import React, { useMemo, useState, useEffect, useRef } from "react";
import type {
  OrchestrationState,
  OrchestrationStep,
  OrchestrationEmployee,
} from "../types/agent";
import {
  ORCHESTRATION_PHASE_LABELS,
  ORCHESTRATION_PHASE_COLORS,
} from "../types/agent";
import { getAgentAvatar } from "../config/agent-avatars";
import { TEAM_REGISTRY } from "../config/agent-roles";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

// ── Components ──────────────────────────────────────────────────

function PersonnelCard({
  employee,
  showMatch = false,
  highlight = false,
  label = "",
}: {
  employee: OrchestrationEmployee;
  showMatch?: boolean;
  highlight?: boolean;
  label?: string;
}) {
  const teamColor = TEAM_REGISTRY[employee.team_name]?.color || "#7f8ca5";
  const avatar = getAgentAvatar(employee.employee_id) || "/placeholder.svg";

  return (
    <article
      className="group flex flex-col transition-transform duration-150"
      style={{
        background: "#1b2230",
        boxShadow: highlight
          ? `0 0 0 3px ${teamColor}, 0 0 12px ${teamColor}80`
          : `0 0 0 3px #3a4356`,
        width: "100%",
        maxWidth: 240,
        margin: "0 auto",
      }}
    >
      <div
        className="relative overflow-hidden flex items-center justify-center"
        style={{
          background: "#0b0e15",
          borderBottom: `3px solid ${teamColor}`,
          height: 120,
        }}
      >
        <img
          src={avatar}
          alt={employee.employee_name}
          className="w-full h-full object-cover transition-transform duration-200"
          style={{ imageRendering: "pixelated", opacity: highlight ? 1 : 0.8 }}
          loading="lazy"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 pointer-events-none opacity-[0.08]"
          style={{
            backgroundImage: "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
            backgroundSize: "100% 3px",
          }}
        />
        {label && (
          <span
            className="absolute bottom-2 left-1/2 -translate-x-1/2 px-2 py-1 text-[10px] leading-none whitespace-nowrap"
            style={{
              fontFamily: PIXEL,
              background: "rgba(11,14,21,0.9)",
              color: highlight ? "#79d97c" : "#e8edf4",
              boxShadow: `0 0 0 2px ${highlight ? "#79d97c" : "#3a4356"}`,
            }}
          >
            {label}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-1 px-3 py-2">
        <h3
          className="text-[9px] leading-relaxed text-[#e8edf4] truncate"
          style={{ fontFamily: PIXEL }}
        >
          {employee.employee_name.toUpperCase()}
        </h3>
        <p className="text-[16px] leading-tight truncate" style={{ color: teamColor }}>
          {employee.employee_role}
        </p>
        <div className="flex items-center justify-between mt-1">
          <span
            className="px-1.5 py-0.5 text-[8px] tracking-widest truncate"
            style={{
              fontFamily: PIXEL,
              background: `${teamColor}22`,
              color: teamColor,
              boxShadow: `0 0 0 1px ${teamColor}55`,
            }}
          >
            {employee.team_name.toUpperCase()}
          </span>
        </div>
        {showMatch && employee.match_score !== undefined && (
          <div className="mt-1 text-[14px] text-[#79d97c]" style={{ fontFamily: TERM }}>
            MATCH: {(employee.match_score * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </article>
  );
}

// ── FLIP Overlay ──────────────────────────────────────────────────

function FlyingCardOverlay({
  flyingCard,
}: {
  flyingCard: {
    employee: OrchestrationEmployee;
    sourceRect: DOMRect;
    targetRect: DOMRect;
  };
}) {
  const [style, setStyle] = useState<React.CSSProperties>({
    transform: "translate(0px, 0px)",
    opacity: 1,
  });

  useEffect(() => {
    // Initial paint at source
    const tid = requestAnimationFrame(() => {
      // Next frame: transition to target
      requestAnimationFrame(() => {
        const deltaX = flyingCard.targetRect.left - flyingCard.sourceRect.left;
        const deltaY = flyingCard.targetRect.top - flyingCard.sourceRect.top;
        setStyle({
          transform: `translate(${deltaX}px, ${deltaY}px)`,
          opacity: 1,
        });
      });
    });
    return () => cancelAnimationFrame(tid);
  }, [flyingCard]);

  return (
    <div
      style={{
        position: "fixed",
        top: flyingCard.sourceRect.top,
        left: flyingCard.sourceRect.left,
        width: flyingCard.sourceRect.width,
        height: flyingCard.sourceRect.height,
        zIndex: 9999,
        pointerEvents: "none",
        transition: "transform 1.6s cubic-bezier(0.34, 1.56, 0.64, 1)",
        ...style,
      }}
    >
      <PersonnelCard
        employee={flyingCard.employee}
        highlight={true}
        label={`ASSIGNING → ${flyingCard.employee.team_name.toUpperCase()}`}
      />
    </div>
  );
}

// ── Main Panel ────────────────────────────────────────────────────

interface Props {
  orchestration: OrchestrationState;
  isOpen: boolean;
  onClose: () => void;
}

export default function OrchestrationPanel({
  orchestration,
  isOpen,
  onClose,
}: Props) {
  const steps = orchestration.steps;
  const candidateRef = useRef<HTMLDivElement>(null);
  const teamRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const lastProcessedEventIndex = useRef<number>(-1);
  const [flyingCard, setFlyingCard] = useState<{
    employee: OrchestrationEmployee;
    sourceRect: DOMRect;
    targetRect: DOMRect;
    eventId: string;
  } | null>(null);
  const [hiddenCandidates, setHiddenCandidates] = useState<Set<string>>(new Set());

  // Animation trigger logic
  useEffect(() => {
    if (steps.length === 0) return;

    // Detect bulk load (e.g. refresh history)
    if (steps.length - lastProcessedEventIndex.current > 1) {
      lastProcessedEventIndex.current = steps.length - 1;
      return;
    }

    // Detect live single event
    const latestStep = steps[steps.length - 1];
    if (
      latestStep.phase === "MEMBER_SELECTED" &&
      latestStep.payload.employee_id
    ) {
      const emp = orchestration.selected_employees[latestStep.payload.employee_id];
      if (emp) {
        requestAnimationFrame(() => {
          const sourceEl = candidateRef.current;
          const targetEl = teamRefs.current[emp.employee_id];

          if (sourceEl && targetEl) {
            setFlyingCard({
              employee: emp,
              sourceRect: sourceEl.getBoundingClientRect(),
              targetRect: targetEl.getBoundingClientRect(),
              eventId: latestStep.event_id,
            });

            setTimeout(() => {
              // Hide candidate from source area permanently after transition
              setHiddenCandidates((prev) => new Set(prev).add(emp.employee_id));
              setFlyingCard((prev) =>
                prev?.eventId === latestStep.event_id ? null : prev
              );
            }, 1700); // Wait for transition to complete
          }
        });
      }
    }

    lastProcessedEventIndex.current = steps.length - 1;
  }, [steps, orchestration.selected_employees]);

  // Derive current candidate from the latest MEMBER_SELECTION_STARTED or MEMBER_SELECTED event
  const currentCandidateEvent = useMemo(() => {
    for (let i = steps.length - 1; i >= 0; i--) {
      if (
        steps[i].phase === "MEMBER_SELECTION_STARTED" ||
        steps[i].phase === "MEMBER_SELECTED"
      ) {
        if (orchestration.is_workforce_assembled) return null;
        return steps[i];
      }
    }
    return null;
  }, [steps, orchestration.is_workforce_assembled]);

  const currentCandidateEmp = currentCandidateEvent?.payload.employee_id
    ? orchestration.selected_employees[currentCandidateEvent.payload.employee_id]
    : null;

  if (!isOpen) return null;

  return (
    <>
      <style>{`
        @keyframes hr-slideIn {
          from { transform: translateX(-100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes pop-in {
          0% { transform: scale(0.9); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>

      {flyingCard && <FlyingCardOverlay flyingCard={flyingCard} />}

      <div
        className="flex flex-col h-full overflow-hidden"
        style={{
          ...pixelPanel,
          animation: "hr-slideIn 0.3s ease-out",
          width: 380,
          maxHeight: "100%",
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-3 py-2 shrink-0"
          style={{
            borderBottom: "3px solid #3a4356",
            background: "#0e1219",
          }}
        >
          <div className="flex items-center gap-2">
            <span style={{ fontSize: 14 }}>🧠</span>
            <span
              style={{
                fontFamily: PIXEL,
                fontSize: 9,
                color: "#e8edf4",
                letterSpacing: "0.5px",
              }}
            >
              HR COMMAND CENTER
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              fontFamily: PIXEL,
              fontSize: 8,
              color: "#5a6270",
              background: "none",
              border: "1px solid #3a4356",
              padding: "3px 8px",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        <div
          className="flex-1 overflow-y-auto"
          style={{ scrollbarWidth: "thin", scrollbarColor: "#3a4356 #12161f" }}
        >
          {/* TASK SECTION */}
          {orchestration.task_id && (
            <div className="p-3 border-b-2" style={{ borderColor: "#232a38" }}>
              <div
                style={{
                  fontFamily: PIXEL,
                  fontSize: 8,
                  color: "#7f8ca5",
                  marginBottom: 6,
                }}
              >
                TASK
              </div>
              <div
                style={{
                  fontFamily: TERM,
                  fontSize: 16,
                  color: "#e8edf4",
                  lineHeight: 1.3,
                }}
              >
                {steps[0]?.payload.detail?.replace("Task received: ", "") ||
                  "Unknown Task"}
              </div>
              <div
                className="mt-2 flex items-center justify-between"
                style={{ fontFamily: TERM, fontSize: 14 }}
              >
                <span style={{ color: "#5a6270" }}>
                  ID: {orchestration.task_id.slice(0, 8)}
                </span>
                <span
                  style={{
                    color: orchestration.is_workforce_assembled
                      ? "#79d97c"
                      : "#ffd93d",
                  }}
                >
                  {orchestration.is_workforce_assembled
                    ? "✓ WORKFORCE ASSEMBLED"
                    : "● ASSEMBLING WORKFORCE"}
                </span>
              </div>
            </div>
          )}

          {/* REQUIRED CAPABILITIES */}
          {(() => {
            const capStep = steps.find(
              (s) => s.phase === "CAPABILITY_IDENTIFIED"
            );
            if (!capStep || !capStep.payload.capabilities?.length) return null;
            return (
              <div
                className="p-3 border-b-2"
                style={{ borderColor: "#232a38" }}
              >
                <div
                  style={{
                    fontFamily: PIXEL,
                    fontSize: 8,
                    color: "#7f8ca5",
                    marginBottom: 6,
                  }}
                >
                  REQUIRED CAPABILITIES
                </div>
                <div className="flex flex-wrap gap-1">
                  {capStep.payload.capabilities.map((cap) => (
                    <span
                      key={cap}
                      style={{
                        fontFamily: TERM,
                        fontSize: 14,
                        color: "#ffd93d",
                        background: "#ffd93d15",
                        padding: "2px 6px",
                        border: "1px solid #ffd93d30",
                      }}
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* CURRENT CANDIDATE */}
          {!orchestration.is_workforce_assembled && (
            <div
              className="p-3 border-b-2"
              style={{ borderColor: "#232a38", minHeight: 180 }}
            >
              <div
                style={{
                  fontFamily: PIXEL,
                  fontSize: 8,
                  color: "#7f8ca5",
                  marginBottom: 8,
                }}
              >
                CURRENT CANDIDATE
              </div>
              {currentCandidateEvent ? (
                <div
                  className="flex justify-center"
                  style={{ animation: "pop-in 0.3s ease-out" }}
                >
                  {currentCandidateEmp &&
                  !hiddenCandidates.has(currentCandidateEmp.employee_id) ? (
                    <div
                      ref={candidateRef}
                      style={{
                        opacity: flyingCard ? 0 : 1,
                        width: "100%",
                      }}
                    >
                      <PersonnelCard
                        employee={currentCandidateEmp}
                        showMatch={true}
                        highlight={true}
                        label="✓ SELECTED BY HR"
                      />
                    </div>
                  ) : (
                    <div
                      className="w-full flex flex-col items-center justify-center p-6"
                      style={{
                        background: "#1b2230",
                        border: "3px dashed #3a4356",
                      }}
                    >
                      <span
                        className="animate-pulse text-center"
                        style={{
                          fontFamily: TERM,
                          fontSize: 18,
                          color: "#b197fc",
                        }}
                      >
                        {currentCandidateEmp
                          ? "WAITING FOR NEXT CANDIDATE..."
                          : "HR SELECTING MEMBER..."}
                      </span>
                      {!currentCandidateEmp && (
                        <span
                          style={{
                            fontFamily: TERM,
                            fontSize: 14,
                            color: "#7f8ca5",
                            marginTop: 4,
                          }}
                        >
                          {currentCandidateEvent.payload.team_name}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div
                  style={{
                    fontFamily: TERM,
                    fontSize: 16,
                    color: "#5a6270",
                    textAlign: "center",
                    padding: 20,
                  }}
                >
                  Waiting for HR...
                </div>
              )}
            </div>
          )}

          {/* SELECTED TEAMS */}
          <div className="p-3 border-b-2" style={{ borderColor: "#232a38" }}>
            <div
              style={{
                fontFamily: PIXEL,
                fontSize: 8,
                color: "#7f8ca5",
                marginBottom: 12,
              }}
            >
              SELECTED TEAMS
            </div>

            <div className="flex flex-col gap-4">
              {orchestration.selected_teams.map((teamName) => {
                const teamMembers = Object.values(
                  orchestration.selected_employees
                ).filter((e) => e.team_name === teamName);
                const isTeamAssembled = steps.some(
                  (s) =>
                    s.phase === "TEAM_ASSEMBLED" &&
                    s.payload.team_name === teamName
                );
                const color = TEAM_REGISTRY[teamName]?.color || "#7f8ca5";

                return (
                  <div
                    key={teamName}
                    style={{
                      border: `2px solid ${color}40`,
                      background: "#12161f",
                    }}
                  >
                    <div
                      className="flex items-center justify-between p-2"
                      style={{
                        background: `${color}20`,
                        borderBottom: `2px solid ${color}40`,
                      }}
                    >
                      <span
                        style={{ fontFamily: PIXEL, fontSize: 9, color }}
                      >
                        {teamName.toUpperCase()}
                      </span>
                      <span
                        style={{
                          fontFamily: TERM,
                          fontSize: 16,
                          color: "#e8edf4",
                        }}
                      >
                        {teamMembers.length}
                      </span>
                    </div>
                    <div className="p-3 grid grid-cols-2 gap-2">
                      {teamMembers.map((emp) => {
                        const isFlying =
                          flyingCard?.employee.employee_id === emp.employee_id;
                        return (
                          <div
                            key={emp.employee_id}
                            ref={(el) => {
                              teamRefs.current[emp.employee_id] = el;
                            }}
                            style={{ position: "relative" }}
                          >
                            <div style={{ opacity: isFlying ? 0 : 1 }}>
                              <PersonnelCard employee={emp} />
                              {emp.status && emp.status !== "hired" && (
                                <div
                                  className="mt-1 text-center truncate"
                                  style={{
                                    fontFamily: TERM,
                                    fontSize: 12,
                                    color: "#a0aab5",
                                  }}
                                >
                                  {emp.status.toUpperCase()}
                                </div>
                              )}
                            </div>
                            {/* DROP TARGET OVERLAY */}
                            {isFlying && (
                              <div className="absolute inset-0 flex flex-col items-center justify-center p-2 border-2 border-dashed border-[#3a4356]">
                                <span
                                  className="animate-pulse text-center"
                                  style={{
                                    fontFamily: TERM,
                                    fontSize: 14,
                                    color: "#7f8ca5",
                                  }}
                                >
                                  [ DROP TARGET ]
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                      {!isTeamAssembled &&
                        currentCandidateEvent?.payload.team_name === teamName &&
                        (!currentCandidateEmp ||
                          hiddenCandidates.has(
                            currentCandidateEmp.employee_id
                          )) && (
                          <div
                            className="flex items-center justify-center p-2"
                            style={{
                              border: "2px dashed #3a4356",
                              height: 120,
                            }}
                          >
                            <span
                              className="animate-pulse text-center"
                              style={{
                                fontFamily: TERM,
                                fontSize: 14,
                                color: "#7f8ca5",
                              }}
                            >
                              Selecting...
                            </span>
                          </div>
                        )}
                    </div>
                    {isTeamAssembled && (
                      <div
                        className="p-1 text-center"
                        style={{
                          background: `${color}10`,
                          borderTop: `1px solid ${color}20`,
                          fontFamily: TERM,
                          fontSize: 14,
                          color,
                        }}
                      >
                        ✓ TEAM ASSEMBLED
                      </div>
                    )}
                  </div>
                );
              })}
              {orchestration.selected_teams.length === 0 && (
                <div
                  style={{
                    fontFamily: TERM,
                    fontSize: 16,
                    color: "#5a6270",
                    textAlign: "center",
                    padding: 20,
                  }}
                >
                  No teams selected yet.
                </div>
              )}
            </div>
          </div>

          {/* LIVE EVENT HISTORY */}
          <div className="p-3">
            <div
              style={{
                fontFamily: PIXEL,
                fontSize: 8,
                color: "#7f8ca5",
                marginBottom: 12,
              }}
            >
              LIVE EVENT HISTORY
            </div>
            <div className="flex flex-col gap-2">
              {[...steps].reverse().map((step, i) => {
                const time = step.timestamp
                  ? new Date(step.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })
                  : "";
                const color =
                  ORCHESTRATION_PHASE_COLORS[step.phase] || "#e8edf4";
                const label =
                  ORCHESTRATION_PHASE_LABELS[step.phase] || step.phase;

                return (
                  <div
                    key={`${step.event_id}-${i}`}
                    className="flex items-start gap-2 mb-1.5"
                    style={{ opacity: i === 0 ? 1 : 0.65 }}
                  >
                    <span
                      style={{
                        fontFamily: TERM,
                        fontSize: 14,
                        color: "#5a6270",
                        minWidth: "65px",
                      }}
                    >
                      {time}
                    </span>
                    <span style={{ fontFamily: TERM, fontSize: 16, color, lineHeight: 1.2 }}>
                      {label}
                      {step.payload.team_name
                        ? ` · ${step.payload.team_name.toUpperCase()}`
                        : ""}
                      {step.payload.employee_name
                        ? ` · ${step.payload.employee_name.toUpperCase()}`
                        : ""}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
