import { useState, useEffect, useCallback, useRef } from "react";
import type { WalletCard } from "../types/agent";
import { useRealtime } from "../providers/RealtimeProvider";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = import.meta.env.VITE_WS_URL || API_BASE.replace("http", "ws") + "/api/realtime/sessions";

export function useWalletCards() {
  const [cards, setCards] = useState<WalletCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const { subscribe, unsubscribe } = useRealtime();

  // ── Fetch initial cards ────────────────────────────────────────
  const fetchCards = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/wallet/cards`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCards(data.cards || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch wallet cards");
    } finally {
      setLoading(false);
    }
  }, []);

  // ── WebSocket subscription for real-time updates ────────────────
  useEffect(() => {
    fetchCards();
  }, [fetchCards]);

  useEffect(() => {
    const handleMessage = (data: any) => {
      try {
        if (data.event === "hr_assignment") {
          // New agent assigned — add a wallet card
          const newCard: WalletCard = {
            id: data.wallet_card_id || `wc_${Date.now()}`,
            task_id: data.task_id || "",
            agent_id: data.session_id || "",
            agent_role: data.role || "",
            agent_name: data.employee_name || data.role || "Agent",
            task_title: data.summary || "",
            team: data.team || "",
            issued_by: "hr_agent",
            issued_at: data.last_heartbeat_at || new Date().toISOString(),
            status: "assigned",
            completed_summary: null,
          };
          setCards((prev) => [newCard, ...prev]);
        }

        if (data.event === "task_complete") {
          // Agent completed task — update card status
          setCards((prev) =>
            prev.map((card) =>
              card.agent_id === data.session_id
                ? {
                    ...card,
                    status: "done" as const,
                    completed_summary: data.summary || "Task completed",
                  }
                : card
            )
          );
        }

        if (data.event === "agent_status_change" || data.event === "status_update") {
          // Agent status changed — update card to in_progress if working
          if (data.status === "working") {
            setCards((prev) =>
              prev.map((card) =>
                card.agent_id === data.session_id && card.status === "assigned"
                  ? { ...card, status: "in_progress" as const }
                  : card
              )
            );
          }
        }
      } catch {
        // Ignore parse errors
      }
    };

    subscribe(handleMessage);
    return () => unsubscribe(handleMessage);
  }, [subscribe, unsubscribe]);

  return { cards, loading, error, refetch: fetchCards };
}
