import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  generateDecision,
  nextReviewer,
  seedDecisions,
  type DecisionRecord,
  type RiskLevel,
} from "./engine";

const MAX_RECORDS = 120;

export interface ArmorIQMetrics {
  total: number;
  allowed: number;
  denied: number;
  pendingApproval: number;
  review: number;
  allowRate: number;
  p50: number;
  p95: number;
  riskCounts: Record<RiskLevel, number>;
  throughput: number[];
  rpm: number;
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return sorted[idx];
}

export function useArmorIQ() {
  const [decisions, setDecisions] = useState<DecisionRecord[]>(() =>
    seedDecisions(6),
  );
  const [live, setLive] = useState(true);
  const [bootStep, setBootStep] = useState(0);
  const [uptime, setUptime] = useState(0);
  const [throughput, setThroughput] = useState<number[]>(() =>
    Array.from({ length: 44 }, () => Math.round(2 + Math.random() * 7)),
  );
  const bucketRef = useRef(0);

  /* ── handshake / boot sequence ── */
  useEffect(() => {
    const t = window.setInterval(() => {
      setBootStep(s => s + 1);
    }, 260);
    return () => window.clearInterval(t);
  }, []);

  /* ── session uptime ── */
  useEffect(() => {
    const t = window.setInterval(() => setUptime(u => u + 1), 1000);
    return () => window.clearInterval(t);
  }, []);

  /* ── decision stream ── */
  useEffect(() => {
    if (!live) return;
    let timer: number;
    const tick = () => {
      const record = generateDecision();
      bucketRef.current += 1;
      setDecisions(prev => [record, ...prev].slice(0, MAX_RECORDS));
      // Fire every 8–18 seconds — realistic authorization cadence
      timer = window.setTimeout(tick, 8000 + Math.random() * 10000);
    };
    timer = window.setTimeout(tick, 4000);
    return () => window.clearTimeout(timer);
  }, [live]);

  /* ── throughput buckets ── */
  useEffect(() => {
    const t = window.setInterval(() => {
      setThroughput(prev => {
        const next = [...prev.slice(1), bucketRef.current];
        bucketRef.current = 0;
        return next;
      });
    }, 2000);
    return () => window.clearInterval(t);
  }, []);

  const resolveApproval = useCallback(
    (decisionId: string, status: "ALLOW" | "DENY") => {
      setDecisions(prev =>
        prev.map(d =>
          d.decisionId === decisionId
            ? {
                ...d,
                resolution: { by: nextReviewer(), status, ts: Date.now() },
              }
            : d,
        ),
      );
    },
    [],
  );

  const metrics = useMemo<ArmorIQMetrics>(() => {
    const riskCounts: Record<RiskLevel, number> = {
      LOW: 0,
      MEDIUM: 0,
      HIGH: 0,
      CRITICAL: 0,
    };
    let allowed = 0;
    let denied = 0;
    let pendingApproval = 0;
    let review = 0;
    const latencies: number[] = [];

    for (const d of decisions) {
      riskCounts[d.riskLevel] += 1;
      latencies.push(d.latencyMs);
      const effective = d.resolution?.status ?? d.status;
      if (effective === "ALLOW") allowed += 1;
      else if (effective === "DENY") denied += 1;
      else if (effective === "REQUIRE_APPROVAL") pendingApproval += 1;
      else review += 1;
    }

    latencies.sort((a, b) => a - b);
    const total = decisions.length || 1;
    const windowSecs = (throughput.length * 2) / 60;
    const rpm = Math.round(
      throughput.reduce((s, x) => s + x, 0) / Math.max(windowSecs, 0.1),
    );

    return {
      total: decisions.length,
      allowed,
      denied,
      pendingApproval,
      review,
      allowRate: allowed / total,
      p50: percentile(latencies, 50),
      p95: percentile(latencies, 95),
      riskCounts,
      throughput,
      rpm,
    };
  }, [decisions, throughput]);

  const approvals = useMemo(
    () =>
      decisions.filter(
        d => d.status === "REQUIRE_APPROVAL" && !d.resolution,
      ),
    [decisions],
  );

  return {
    decisions,
    approvals,
    metrics,
    live,
    setLive,
    bootStep,
    uptime,
    resolveApproval,
  };
}
