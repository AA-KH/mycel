import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRealtime } from "../providers/RealtimeProvider";

// ─────────────────────────────────────────────────────────────────────────────
// Domain types
// ─────────────────────────────────────────────────────────────────────────────

export interface TimelineEvent {
  id: string;
  timestamp: string;
  type: "info" | "success" | "error" | "handoff";
  label: string;
  summary: string;
}

export interface ActiveEmployee {
  team: string | null;
  teamId: string | null;
  member: string | null;
  task: string | null;
  status: "idle" | "running" | "completed" | "error";
  source: string | null;
  capabilities: string[];
  isHandoff: boolean;
  previousTeam: string | null;
}

export interface Property {
  property_id: string;
  title: string;
  price: number;
  location: string;
  city?: string;
  bhk: number;
  area_sqft?: number;
  match_score?: number;
  rental_yield?: number;
  developer?: string;
  availability?: string;
  amenities?: string[];
  image_url?: string;
}

export interface CustomerProfile {
  customer_id: string;
  name: string;
  lead_status: string;
  requirements: {
    budget_max?: number;
    location?: string;
    bhk?: number;
    purpose?: string;
    investment_interest?: boolean;
  };
}

export interface ConversationMessage {
  speaker: string;
  text: string;
  lang: string;
  time: string;
  isAgent?: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace("http", "ws");

// ─────────────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────────────

export function useRealEstateDemo(customerId: string = "kaushal") {
  const { token } = useAuth();
  const [conversationId, setConversationId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [activeEmployee, setActiveEmployee] = useState<ActiveEmployee>({
    team: null,
    teamId: null,
    member: null,
    task: null,
    status: "idle",
    source: null,
    capabilities: [],
    isHandoff: false,
    previousTeam: null,
  });
  const [currentStage, setCurrentStage] = useState<string>("Ready");
  const [currentIntent, setCurrentIntent] = useState<string | null>(null);
  const [language, setLanguage] = useState<string>("en");
  const [properties, setProperties] = useState<Property[]>([]);
  const [customer, setCustomer] = useState<CustomerProfile>({
    customer_id: customerId,
    name: "Kaushal",
    lead_status: "hot",
    requirements: {
      budget_max: 8_000_000,
      location: "Chandigarh",
      bhk: 2,
      purpose: "family",
      investment_interest: true,
    },
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [legalOutput, setLegalOutput] = useState<any>(null);

  const previousTeamRef = useRef<string | null>(null);

  const { subscribe, unsubscribe } = useRealtime();

  // ── Add timeline event ──────────────────────────────────────────────────
  const addEvent = useCallback(
    (type: TimelineEvent["type"], label: string, summary: string) => {
      setTimelineEvents((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          }),
          type,
          label,
          summary,
        },
      ]);
    },
    []
  );

  // WebSocket connection
  useEffect(() => {
    const handleMessage = (data: any) => {
      try {
        // Ensure this event belongs to our conversation
        if (data.conversation_id && data.conversation_id !== conversationId) return;
        
        const p = data.payload || {};

        switch (data.event_type) {
          case "CONVERSATION_STARTED":
            addEvent("info", "Query received", p.query?.slice(0, 80) || "");
            setCurrentStage("Intent Detection");
            break;

          case "LANGUAGE_DETECTED":
            setLanguage(p.language || "en");
            addEvent(
              "info",
              "Language",
              p.language?.toUpperCase() || "Detected"
            );
            break;

          case "INTENT_DETECTED":
            setCurrentIntent(p.intent || null);
            addEvent("success", "Intent", p.intent || "");
            setCurrentStage("Capability Resolution");
            // Update customer requirements from detected requirements
            if (p.requirements && Object.keys(p.requirements).length > 0) {
              setCustomer((prev) => ({
                ...prev,
                requirements: {
                  ...prev.requirements,
                  ...Object.fromEntries(
                    Object.entries(p.requirements).filter(
                      ([, v]) => v !== null && v !== undefined
                    )
                  ),
                },
              }));
            }
            break;

          case "CAPABILITY_RESOLVED":
            addEvent(
              "success",
              "Capabilities",
              (p.capabilities || []).join(", ")
            );
            setCurrentStage("Team Assignment");
            break;

          case "TEAM_SELECTED": {
            const prevTeam = previousTeamRef.current;
            const newTeam = p.team;
            const isHandoff = prevTeam !== null && prevTeam !== newTeam;
            previousTeamRef.current = newTeam;
            setActiveEmployee((prev) => ({
              ...prev,
              team: newTeam,
              teamId: p.team_id || null,
              isHandoff,
              previousTeam: isHandoff ? prevTeam : null,
              status: "running",
            }));
            if (isHandoff) {
              addEvent(
                "handoff",
                "Handoff",
                `${prevTeam} → ${newTeam}: specialized capability required`
              );
            } else {
              addEvent("info", "Team", newTeam);
            }
            break;
          }

          case "MEMBER_SELECTED":
            setActiveEmployee((prev) => ({
              ...prev,
              member: p.member,
            }));
            addEvent("info", "Member", p.member || "");
            setCurrentStage("Task Execution");
            break;

          case "DATA_SOURCE_SELECTED":
            setActiveEmployee((prev) => ({ ...prev, source: p.source }));
            addEvent("info", "Source", p.source || "");
            break;

          case "TASK_CREATED":
            setActiveEmployee((prev) => ({
              ...prev,
              task: p.task,
              status: "running",
            }));
            addEvent("info", "Task created", p.task || "");
            break;

          case "TASK_STARTED":
            setCurrentStage(p.stage || "Executing");
            addEvent("info", "Task started", p.task || "");
            break;

          case "RETRIEVAL_STARTED":
            setCurrentStage(`Querying ${p.source || p.stage || "source"}...`);
            break;

          case "RETRIEVAL_COMPLETED":
            addEvent("success", "Retrieved", `from ${p.source || p.tool_id}`);
            setCurrentStage("Analysis");
            break;

          case "ANALYSIS_STARTED":
            setCurrentStage("Generating response...");
            break;

          case "ANALYSIS_COMPLETED":
            setCurrentStage("Delivering response");
            break;

          case "RESPONSE_GENERATED":
            addEvent("success", "Response ready", "");
            break;

          case "TASK_COMPLETED":
            setActiveEmployee((prev) => ({ ...prev, status: "completed" }));
            setCurrentStage("Completed");
            addEvent("success", "Completed", p.task || "Task done");
            break;

          case "TASK_FAILED":
            setActiveEmployee((prev) => ({ ...prev, status: "error" }));
            setCurrentStage("Failed");
            addEvent(
              "error",
              "Failed",
              p.reason || "Unknown error"
            );
            break;
        }
      } catch (e) {
        console.error("[useRealEstateDemo] WS parse error:", e);
      }
    };

    subscribe(handleMessage);
    return () => unsubscribe(handleMessage);
  }, [conversationId, addEvent, subscribe, unsubscribe]);

  // ── Load customer from backend on mount ─────────────────────────────────
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/real-estate/customers/${customerId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (res.ok) {
          const data = await res.json();
          setCustomer({
            customer_id: data.customer_id,
            name: data.name,
            lead_status: data.lead_status,
            requirements: data.requirements || {},
          });
        }
      } catch {
        // Fallback to defaults if backend not reachable
      }
    };
    load();
  }, [customerId, token]);

  // ── Start conversation ──────────────────────────────────────────────────
  const startConversation = useCallback(async (): Promise<string> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/real-estate/conversations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ customer_id: customerId }),
      });
      if (res.ok) {
        const data = await res.json();
        setConversationId(data.conversation_id);
        return data.conversation_id;
      }
    } catch (e) {
      console.error("[useRealEstateDemo] Failed to create conversation:", e);
    }
    // Fallback: generate client-side
    const id = crypto.randomUUID();
    setConversationId(id);
    return id;
  }, [customerId, token]);

  // ── Send message ────────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isProcessing) return;

      // Ensure we have a conversation
      let convId = conversationId;
      if (!convId) {
        convId = await startConversation();
      }

      // Add user message to UI immediately
      setMessages((prev) => [
        ...prev,
        {
          speaker: customer.name,
          text,
          lang: language,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          isAgent: false,
        },
      ]);

      setIsProcessing(true);
      setCurrentStage("Processing...");
      // Reset state for new query
      setActiveEmployee((prev) => ({
        ...prev,
        status: "running",
      }));

      try {
        const res = await fetch(
          `${API_BASE}/api/v1/real-estate/conversations/${convId}/message`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ customer_id: customerId, text }),
          }
        );

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }

        const data = await res.json();

        // Display agent response
        setMessages((prev) => [
          ...prev,
          {
            speaker: data.member || "Agent",
            text: data.response || "I've processed your request.",
            lang: data.language || "en",
            time: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
            isAgent: true,
          },
        ]);

        // Process tool output
        if (data.tool_output) {
          if (data.intent === "PROPERTY_SEARCH" && data.tool_output.results) {
            setProperties(data.tool_output.results);
          } else if (
            data.intent === "PROPERTY_LEGAL_QUERY"
          ) {
            setLegalOutput(data.tool_output);
            setProperties([]); // Clear property grid for legal queries
          } else if (
            data.intent === "PROPERTY_INVESTMENT_ANALYSIS" &&
            data.tool_output.analysis
          ) {
            // Show analysis as properties with enriched data
            setProperties(
              data.tool_output.analysis.map((a: any) => ({
                ...a,
                match_score: a.investment_score,
              }))
            );
          }
        }
      } catch (err: any) {
        console.error("[useRealEstateDemo] sendMessage error:", err);
        setMessages((prev) => [
          ...prev,
          {
            speaker: "System",
            text: `Error: ${err.message || "Failed to reach backend"}`,
            lang: "en",
            time: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
            isAgent: true,
          },
        ]);
        addEvent("error", "Error", err.message || "Backend unreachable");
      } finally {
        setIsProcessing(false);
      }
    },
    [
      conversationId,
      customerId,
      token,
      language,
      customer.name,
      isProcessing,
      startConversation,
      addEvent,
    ]
  );

  return {
    conversationId,
    messages,
    timelineEvents,
    activeEmployee,
    currentStage,
    currentIntent,
    language,
    properties,
    legalOutput,
    customer,
    isProcessing,
    sendMessage,
    startConversation,
    setConversationId,
  };
}
