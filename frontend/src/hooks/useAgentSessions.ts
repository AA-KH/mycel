import { useAuth } from "../contexts/AuthContext";
import { useCallback, useEffect, useState } from "react";
import type { AgentSession } from "../types/agent";
import { useRealtime } from "../providers/RealtimeProvider";

const STALE_THRESHOLD_MS = 12 * 60 * 60 * 1000; // 12 hours

export function useAgentSessions() {
  const { token, logout } = useAuth();
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const filterActive = useCallback((allSessions: AgentSession[]) => {
    const now = Date.now();
    return allSessions.filter((s) => {
      const heartbeat = new Date(s.last_heartbeat_at).getTime();
      return now - heartbeat < STALE_THRESHOLD_MS;
    });
  }, []);

  const { subscribe, unsubscribe } = useRealtime();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/data/sessions`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (response.status === 401) {
          logout();
          return;
        }
        if (!response.ok) throw new Error("Failed to fetch sessions");
        const data = await response.json();
        setSessions(filterActive(data));
        setLoading(false);
      } catch (err: any) {
        setError(err);
        setLoading(false);
      }
    };
    
    if (token) {
      fetchData();
    } else {
      setLoading(false);
    }
  }, [token, logout, filterActive]);

  useEffect(() => {
    const handleMessage = (data: any) => {
      const eventType = data.event;

      // All event types update or insert the session
      if (
        eventType === "status_update" ||
        eventType === "hr_assignment" ||
        eventType === "agent_status_change" ||
        eventType === "task_complete"
      ) {
        setSessions((prev) => {
          const index = prev.findIndex(s => s.session_id === data.session_id);
          const session: AgentSession = {
            id: data.session_id || data.id,
            session_id: data.session_id,
            role: data.role,
            status: data.status,
            break_activity: data.break_activity || null,
            team: data.team || "",
            employee_name: data.employee_name || null,
            summary: data.summary || null,
            link: data.link || null,
            workspace: data.workspace || null,
            started_at: data.started_at || data.last_heartbeat_at,
            last_heartbeat_at: data.last_heartbeat_at,
            current_task_id: data.current_task_id || null,
          };

          if (index >= 0) {
            const newSessions = [...prev];
            newSessions[index] = session;
            return filterActive(newSessions);
          }
          return filterActive([...prev, session]);
        });
      }
    };

    subscribe(handleMessage);
    return () => unsubscribe(handleMessage);
  }, [subscribe, unsubscribe, filterActive]);

  // Re-filter periodically to remove stale sessions
  useEffect(() => {
    const interval = setInterval(() => {
      setSessions((prev) => filterActive(prev));
    }, 30_000);
    return () => clearInterval(interval);
  }, [filterActive]);

  return { sessions, loading, error };
}
