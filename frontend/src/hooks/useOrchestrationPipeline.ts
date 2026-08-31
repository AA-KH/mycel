import { useCallback, useEffect, useRef, useState } from "react";
import type {
  OrchestrationState,
  OrchestrationStep,
} from "../types/agent";
import { OrchestrationPhase } from "../types/agent";
import { useRealtime } from "../providers/RealtimeProvider";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL =
  import.meta.env.VITE_WS_URL ||
  API_BASE.replace("http", "ws") + "/api/realtime/sessions";

/**
 * Creates a blank OrchestrationState with no active task.
 */
function emptyState(): OrchestrationState {
  return {
    task_id: null,
    current_phase: null,
    steps: [],
    selected_teams: [],
    selected_employees: {},
    is_active: false,
    is_workforce_assembled: false,
    started_at: null,
    completed_at: null,
  };
}

export function useOrchestrationPipeline() {
  const [state, setState] = useState<OrchestrationState>(emptyState);

  const applyEventToState = useCallback((eventStep: OrchestrationStep, prevState: OrchestrationState) => {
    const taskChanged = prevState.task_id !== null && prevState.task_id !== eventStep.task_id;
    const baseState = taskChanged ? emptyState() : prevState;
    
    // Check if event already exists
    if (!taskChanged && baseState.steps.some(s => s.event_id === eventStep.event_id)) {
        return baseState;
    }

    const prevSteps = baseState.steps.map((s) =>
      s.status === "active" ? { ...s, status: "complete" as const } : s
    );

    const newState = {
      ...baseState,
      task_id: eventStep.task_id,
      current_phase: eventStep.phase,
      steps: [...prevSteps, eventStep].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
      started_at: baseState.started_at || eventStep.timestamp,
    };

    if (eventStep.status === "complete" || eventStep.status === "failed") {
        newState.is_active = false;
        newState.completed_at = eventStep.timestamp;
    } else {
        newState.is_active = true;
    }

    // Apply specific Phase 4 reducers based on payload
    const p = eventStep.payload;

    if (eventStep.phase === OrchestrationPhase.TEAM_ASSEMBLED && p.team_name) {
        if (!newState.selected_teams.includes(p.team_name)) {
            newState.selected_teams = [...newState.selected_teams, p.team_name];
        }
    }

    if (eventStep.phase === OrchestrationPhase.WORKFORCE_ASSEMBLED) {
        newState.is_workforce_assembled = true;
    }

    // Identify employee key
    const employeeKey = p.employee_id;
    if (employeeKey) {
        const emp = newState.selected_employees[employeeKey] || {
            employee_id: employeeKey,
            employee_name: p.employee_name || "Agent",
            employee_role: p.employee_role || "Agent",
            team_name: p.team_name || "General",
            status: "hired"
        };

        // Update fields if present
        if (p.employee_name) emp.employee_name = p.employee_name;
        if (p.employee_role) emp.employee_role = p.employee_role;
        if (p.team_name) emp.team_name = p.team_name;
        if (p.session_id) emp.session_id = p.session_id;
        if (p.wallet_card_id) emp.wallet_card_id = p.wallet_card_id;
        if (p.subtask_id) emp.subtask_id = p.subtask_id;
        if (p.match_score) emp.match_score = p.match_score;
        if (p.capabilities) emp.capabilities = p.capabilities;
        if (p.metadata?.subtask_description) emp.subtask_description = p.metadata.subtask_description;

        // Progress status based on phase
        if (eventStep.phase === OrchestrationPhase.MEMBER_SELECTED) {
            if (emp.status !== "assigned" && emp.status !== "moving" && emp.status !== "working" && emp.status !== "completed" && emp.status !== "failed") {
                emp.status = "hired";
            }
        } else if (eventStep.phase === OrchestrationPhase.TASK_ASSIGNED) {
            if (emp.status !== "moving" && emp.status !== "working" && emp.status !== "completed" && emp.status !== "failed") emp.status = "assigned";
        } else if (eventStep.phase === OrchestrationPhase.AGENT_MOVING) {
            if (emp.status !== "working" && emp.status !== "completed" && emp.status !== "failed") emp.status = "moving";
        } else if (eventStep.phase === OrchestrationPhase.AGENT_WORKING || eventStep.phase === OrchestrationPhase.EXECUTION_STARTED) {
            if (emp.status !== "completed" && emp.status !== "failed") emp.status = "working";
        } else if (eventStep.phase === OrchestrationPhase.AGENT_COMPLETED) {
            emp.status = "completed";
        } else if (eventStep.phase === OrchestrationPhase.AGENT_FAILED) {
            emp.status = "failed";
        }

        newState.selected_employees = { ...newState.selected_employees, [employeeKey]: emp };
    }

    return newState;
  }, []);

  // ── Fetch history (for reconnect / replay) ──────────────────────
  const fetchHistory = useCallback(async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${taskId}/orchestration`);
      if (!res.ok) return;
      const data = await res.json();
      const events = data.events || [];
      
      let reconstructedState = emptyState();
      
      for (let i = 0; i < events.length; i++) {
          const e = events[i];
          const phase: OrchestrationPhase = e.phase;
          const isTerminal = phase === "ORCHESTRATION_COMPLETED" || phase === "ORCHESTRATION_FAILED";
          
          const step: OrchestrationStep = {
              event_id: e.event_id || crypto.randomUUID(),
              task_id: e.task_id || taskId,
              event_type: e.event_type || "orchestration_phase",
              actor: e.actor || "system",
              phase,
              phase_index: e.phase_index ?? i,
              timestamp: e.timestamp ?? new Date().toISOString(),
              status: isTerminal ? (phase === "ORCHESTRATION_COMPLETED" ? "complete" : "failed") : (i === events.length - 1 && data.status !== "complete" ? "active" : "complete"),
              payload: {
                  detail: e.payload?.detail || e.detail,
                  team_id: e.payload?.team_id || e.team_id,
                  team_name: e.payload?.team_name || e.team_name,
                  employee_id: e.payload?.employee_id || e.employee_id,
                  employee_name: e.payload?.employee_name || e.employee_name,
                  employee_role: e.payload?.employee_role || e.agent_role,
                  session_id: e.payload?.session_id || e.session_id,
                  wallet_card_id: e.payload?.wallet_card_id || e.wallet_card_id,
                  subtask_id: e.payload?.subtask_id || e.subtask_id,
                  match_score: e.payload?.match_score || e.hiring_score,
                  capabilities: e.payload?.capabilities || e.capabilities,
                  selected_teams: e.payload?.selected_teams || e.selected_teams,
                  metadata: e.payload?.metadata || e.metadata,
                  subtask_index: e.payload?.subtask_index || e.subtask_index,
                  total_subtasks: e.payload?.total_subtasks || e.total_subtasks,
              }
          };
          
          reconstructedState = applyEventToState(step, reconstructedState);
      }
      
      // Override overall active if API says it's active
      if (data.status !== "complete" && data.status !== "failed" && reconstructedState.steps.length > 0) {
          reconstructedState.is_active = true;
          if (reconstructedState.steps.length > 0) {
            reconstructedState.steps[reconstructedState.steps.length - 1].status = "active";
          }
      }
      
      setState(reconstructedState);
    } catch (err) {
      console.error("[useOrchestrationPipeline] Failed to fetch history", err);
    }
  }, [applyEventToState]);

  // ── Auto-reconnect: fetch latest active task's events on mount ──
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/tasks/?limit=1`);
        if (!res.ok) return;
        const data = await res.json();
        const tasks = data.tasks || [];
        const active = tasks.find(
          (t: any) => t.status === "in_progress" || t.status === "queued"
        );
        if (active?.task_id) {
            await fetchHistory(active.task_id);
        }
      } catch {
        // Silent fail — the live WebSocket will populate state on next task
      }
    })();
  }, [fetchHistory]);

  const { subscribe, unsubscribe } = useRealtime();

  // ── WebSocket subscription ──────────────────────────────────────
  useEffect(() => {
    const handleMessage = (data: any) => {
      try {
        // Only process orchestration_phase events
        if (data.event_type !== "orchestration_phase" && data.event !== "orchestration_phase") return;

        const phase: OrchestrationPhase = data.phase;
        const isTerminal = phase === "ORCHESTRATION_COMPLETED" || phase === "ORCHESTRATION_FAILED";

        const newStep: OrchestrationStep = {
          event_id: data.event_id || crypto.randomUUID(),
          task_id: data.task_id || "unknown",
          event_type: data.event_type || "orchestration_phase",
          actor: data.actor || "system",
          phase,
          phase_index: data.phase_index ?? 0,
          timestamp: data.timestamp ?? new Date().toISOString(),
          status: isTerminal ? (phase === "ORCHESTRATION_COMPLETED" ? "complete" : "failed") : "active",
          payload: {
            detail: data.payload?.detail || data.detail,
            team_id: data.payload?.team_id,
            team_name: data.payload?.team_name,
            employee_id: data.payload?.employee_id,
            employee_name: data.payload?.employee_name || data.employee_name,
            employee_role: data.payload?.employee_role || data.agent_role,
            session_id: data.payload?.session_id || data.session_id,
            wallet_card_id: data.payload?.wallet_card_id,
            subtask_id: data.payload?.subtask_id,
            match_score: data.payload?.match_score || data.hiring_score,
            capabilities: data.payload?.capabilities || data.capabilities,
            selected_teams: data.payload?.selected_teams || data.selected_teams,
            metadata: data.payload?.metadata,
            subtask_index: data.payload?.subtask_index || data.subtask_index,
            total_subtasks: data.payload?.total_subtasks || data.total_subtasks,
          }
        };

        setState((prev) => applyEventToState(newStep, prev));
      } catch {
        // Ignore parse errors — other event types flow through here too
      }
    };

    subscribe(handleMessage);
    return () => unsubscribe(handleMessage);
  }, [subscribe, unsubscribe, applyEventToState]);

  // ── Reset ───────────────────────────────────────────────────────
  const reset = useCallback(() => {
    setState(emptyState());
  }, []);

  return { state, fetchHistory, reset };
}
