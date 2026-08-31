import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';

type RealtimeMessage = any;
type MessageListener = (data: RealtimeMessage) => void;

interface RealtimeContextType {
  subscribe: (listener: MessageListener) => void;
  unsubscribe: (listener: MessageListener) => void;
  isConnected: boolean;
}

const RealtimeContext = createContext<RealtimeContextType | null>(null);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  // Using a Set directly allows constant time add/remove
  const listenersRef = useRef<Set<MessageListener>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);
  
  const subscribe = useCallback((listener: MessageListener) => {
    listenersRef.current.add(listener);
  }, []);

  const unsubscribe = useCallback((listener: MessageListener) => {
    listenersRef.current.delete(listener);
  }, []);

  useEffect(() => {
    let isMounted = true;
    let reconnectTimeout: number;

    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return;

      const wsUrl = (import.meta.env.VITE_WS_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace("http", "ws")) + "/api/realtime/sessions";
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isMounted) setIsConnected(true);
        console.log("[RealtimeProvider] WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          listenersRef.current.forEach(listener => {
            try {
              listener(data);
            } catch (err) {
              console.error("[RealtimeProvider] listener error:", err);
            }
          });
        } catch (err) {
          console.error("[RealtimeProvider] parse error:", err);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          setIsConnected(false);
          wsRef.current = null;
          console.log("[RealtimeProvider] WebSocket closed. Reconnecting...");
          // Reconnect with simple backoff
          reconnectTimeout = window.setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error("[RealtimeProvider] ws error:", err);
      };
    };

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        // Prevent onclose from triggering reconnect during unmount
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return (
    <RealtimeContext.Provider value={{ subscribe, unsubscribe, isConnected }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}
