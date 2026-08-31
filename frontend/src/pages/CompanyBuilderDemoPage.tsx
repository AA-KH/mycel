import React, { useState, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import { DocumentViewer } from "../components/Showcase/Renderers/DocumentViewer";

const API = "http://127.0.0.1:8000";

// ── Types ──────────────────────────────────────────────────────────────────

interface MemberAssignment {
  member_id: string;
  member_name: string;
  member_role: string;
  task_title: string;
  task_description: string;
  expected_output: string;
  status: string;
  team_color: string;
}

interface TeamDelegation {
  team_id: string;
  team_name: string;
  team_color: string;
  manager_name: string;
  manager_role: string;
  objective: string;
  members: MemberAssignment[];
}

interface DelegationGraph {
  graph_id: string;
  workflow_id: string;
  stage: string;
  prompt_summary: string;
  teams: TeamDelegation[];
  total_members_assigned: number;
  total_tasks: number;
}

interface Document {
  doc_id: string;
  stage: string;
  title: string;
  url: string;
}

const STAGE_LABELS: Record<string, string> = {
  COMPANY_INITIALIZATION: "🚀 Company Init",
  REQUIREMENTS_DISCOVERY: "📋 Requirements",
  FEASIBILITY_ANALYSIS: "🔬 Feasibility",
  GROWTH_STRATEGY: "📈 Growth Strategy",
  BRAND_IDENTITY: "🎨 Brand Identity",
  LOGO_CREATION: "✏️ Logo Design",
  POSTER_CREATION: "🖼️ Poster",
  WEBSITE_CREATION: "🌐 Website",
  PITCH_DECK_CREATION: "📊 Pitch Deck",
  QUALITY_VALIDATION: "✅ Quality Check",
};

const STAGE_ORDER = [
  "COMPANY_INITIALIZATION",
  "REQUIREMENTS_DISCOVERY",
  "FEASIBILITY_ANALYSIS",
  "GROWTH_STRATEGY",
  "BRAND_IDENTITY",
  "LOGO_CREATION",
  "POSTER_CREATION",
  "WEBSITE_CREATION",
  "PITCH_DECK_CREATION",
];

// ── Sub-components ─────────────────────────────────────────────────────────

function MemberCard({ member }: { member: MemberAssignment }) {
  return (
    <div
      style={{
        background: "#ffffff",
        border: `2px solid ${member.team_color}44`,
        borderLeft: `4px solid ${member.team_color}`,
        borderRadius: "12px",
        padding: "14px",
        transition: "transform 0.15s, box-shadow 0.15s",
      }}
      className="hover:shadow-lg hover:-translate-y-0.5"
    >
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            background: `linear-gradient(135deg, ${member.team_color}, ${member.team_color}88)`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontWeight: 700,
            fontSize: 16,
            flexShrink: 0,
          }}
        >
          {member.member_name[0]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between flex-wrap gap-1">
            <div>
              <span className="font-semibold text-gray-900 text-sm">{member.member_name}</span>
              <span className="text-gray-400 text-xs ml-2">· {member.member_role}</span>
            </div>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{
                background: `${member.team_color}18`,
                color: member.team_color,
                border: `1px solid ${member.team_color}44`,
              }}
            >
              {member.status}
            </span>
          </div>
          <div className="mt-2 text-xs font-semibold text-gray-700">📋 {member.task_title}</div>
          <div className="mt-1 text-xs text-gray-500 leading-relaxed">{member.task_description}</div>
          <div className="mt-2 text-xs font-medium" style={{ color: member.team_color }}>
            📦 {member.expected_output}
          </div>
        </div>
      </div>
    </div>
  );
}

function TeamNode({ team }: { team: TeamDelegation }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="flex flex-col items-center">
      {/* Manager Node */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="cursor-pointer select-none"
        style={{
          background: `linear-gradient(135deg, ${team.team_color}22, ${team.team_color}08)`,
          border: `2px solid ${team.team_color}`,
          borderRadius: "16px",
          padding: "14px 20px",
          minWidth: 200,
          textAlign: "center",
          boxShadow: `0 4px 20px ${team.team_color}33`,
          transition: "transform 0.15s",
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            background: team.team_color,
            margin: "0 auto 8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontWeight: 700,
            fontSize: 16,
            boxShadow: `0 0 16px ${team.team_color}66`,
          }}
        >
          {team.team_name.slice(0, 2)}
        </div>
        <div className="text-xs font-bold text-gray-800">{team.team_name} TEAM</div>
        <div className="text-xs text-gray-500 mt-0.5">{team.manager_name}</div>
        <div className="text-xs text-gray-400">{team.manager_role}</div>
        <div className="mt-2 text-xs" style={{ color: team.team_color }}>
          {expanded ? "▲ collapse" : "▼ expand"}
        </div>
      </div>

      {/* Vertical line down */}
      {expanded && team.members.length > 0 && (
        <>
          <div
            style={{
              width: 2,
              height: 24,
              background: `linear-gradient(${team.team_color}, ${team.team_color}44)`,
            }}
          />

          {/* Member cards */}
          <div className="flex flex-col gap-3 w-full max-w-sm">
            {team.members.map((m, i) => (
              <div key={m.member_id} className="flex flex-col items-center">
                {i > 0 && (
                  <div
                    style={{
                      width: 2,
                      height: 16,
                      background: `${team.team_color}66`,
                    }}
                  />
                )}
                <MemberCard member={m} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function DelegationView({ graph }: { graph: DelegationGraph }) {
  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 className="text-base font-bold text-gray-900">
            🏢 Work Delegation — {STAGE_LABELS[graph.stage] || graph.stage}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5 italic">"{graph.prompt_summary}"</p>
        </div>
        <div className="flex gap-2">
          <Stat label="Teams" value={graph.teams.length} color="#5e81f4" />
          <Stat label="Members" value={graph.total_members_assigned} color="#2ec4b6" />
          <Stat label="Tasks" value={graph.total_tasks} color="#f4a261" />
        </div>
      </div>

      {/* Node Tree */}
      <div className="overflow-x-auto">
        <div className="flex gap-6 pb-4" style={{ minWidth: "max-content" }}>
          {graph.teams.map((team) => (
            <TeamNode key={team.team_id} team={team} />
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      className="flex flex-col items-center px-3 py-1.5 rounded-lg"
      style={{ background: `${color}14`, border: `1px solid ${color}33` }}
    >
      <span className="text-lg font-bold" style={{ color }}>
        {value}
      </span>
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  );
}

function PipelineTracker({ stages, currentStage, completedStages }: {
  stages: string[];
  currentStage: string;
  completedStages: string[];
}) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {stages.map((s, i) => {
        const isDone = completedStages.includes(s);
        const isActive = s === currentStage;
        return (
          <React.Fragment key={s}>
            <div
              className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
              style={{
                background: isDone ? "#22c55e18" : isActive ? "#5e81f418" : "#f1f5f9",
                color: isDone ? "#16a34a" : isActive ? "#5e81f4" : "#94a3b8",
                border: isActive ? "1.5px solid #5e81f4" : "1.5px solid transparent",
              }}
            >
              {isDone ? "✓" : isActive ? "⟳" : "○"} {STAGE_LABELS[s]?.split(" ").slice(1).join(" ") || s}
            </div>
            {i < stages.length - 1 && (
              <div
                style={{
                  width: 16,
                  height: 1.5,
                  background: isDone ? "#22c55e" : "#e2e8f0",
                }}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function CompanyBuilderDemoPage() {
  const { token } = useAuth();

  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [companyName, setCompanyName] = useState("Acme Corp");
  const [currentStage, setCurrentStage] = useState("COMPANY_INITIALIZATION");
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isIniting, setIsIniting] = useState(false);
  const [delegationHistory, setDelegationHistory] = useState<DelegationGraph[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [latestGraph, setLatestGraph] = useState<DelegationGraph | null>(null);
  const [log, setLog] = useState<string[]>([]);

  const addLog = (msg: string) => setLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 49)]);

  const handleInit = useCallback(async () => {
    setIsIniting(true);
    addLog("Initializing Company Workspace...");
    try {
      const res = await fetch(`${API}/api/company-builder/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ company_name: companyName }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setWorkflowId(data.workflow_id);
      setCurrentStage(data.state.current_stage);
      addLog(`✅ Workspace created. Workflow ID: ${data.workflow_id}`);
      addLog(`🔄 Current stage: ${data.state.current_stage}`);
    } catch (e: any) {
      addLog(`❌ Init failed: ${e.message}`);
    } finally {
      setIsIniting(false);
    }
  }, [token, companyName]);

  const handleSubmitPrompt = useCallback(async () => {
    if (!workflowId || !prompt.trim()) return;
    setIsLoading(true);
    addLog(`📤 Submitting prompt for stage: ${currentStage}`);
    try {
      const res = await fetch(`${API}/api/company-builder/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ workflow_id: workflowId, prompt, company_name: companyName }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();

      // Update delegation
      if (data.delegation_graph) {
        setLatestGraph(data.delegation_graph);
        setDelegationHistory((prev) => [data.delegation_graph, ...prev]);
        addLog(`🏢 Delegated to ${data.delegation_graph.teams.length} teams, ${data.delegation_graph.total_tasks} tasks`);
      }

      // Register document
      if (data.document_id) {
        const docUrl = `${API}/api/company-builder/document/${workflowId}/${data.stage}`;
        setDocuments((prev) => [
          { doc_id: data.document_id, stage: data.stage, title: `${STAGE_LABELS[data.stage] || data.stage} Report`, url: docUrl },
          ...prev.filter((d) => d.stage !== data.stage),
        ]);
        addLog(`📄 Document generated for ${data.stage}`);
      }

      // Advance stage
      setCompletedStages((prev) => [...prev, currentStage]);
      const nextIdx = STAGE_ORDER.indexOf(currentStage) + 1;
      if (nextIdx < STAGE_ORDER.length) {
        setCurrentStage(STAGE_ORDER[nextIdx]);
        addLog(`⏭️ Advanced to next stage: ${STAGE_ORDER[nextIdx]}`);
      }

      setPrompt("");
    } catch (e: any) {
      addLog(`❌ Prompt failed: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [workflowId, prompt, currentStage, token, companyName]);

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        textarea:focus, input:focus { outline: none; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }
        .glass-light { background: rgba(255,255,255,0.95); border: 1px solid rgba(0,0,0,0.08); }
        .scroll-thin::-webkit-scrollbar { width: 4px; height: 4px; }
        .scroll-thin::-webkit-scrollbar-track { background: transparent; }
        .scroll-thin::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
      `}</style>

      {/* ── Header ── */}
      <div className="glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                background: "linear-gradient(135deg, #5e81f4, #8b5cf6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 20,
                boxShadow: "0 0 20px #5e81f466",
              }}
            >
              🏗️
            </div>
            <div>
              <div className="text-white font-bold text-lg leading-tight">Mycel Company Builder</div>
              <div className="text-white/50 text-xs">Autonomous AI-powered company creation pipeline</div>
            </div>
          </div>
          {workflowId && (
            <div
              className="text-xs font-mono px-3 py-1.5 rounded-full"
              style={{ background: "rgba(94,129,244,0.2)", color: "#a5b4fc", border: "1px solid rgba(94,129,244,0.3)" }}
            >
              WF: {workflowId}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-6">

        {/* ── Pipeline Tracker ── */}
        <div className="glass rounded-2xl p-4">
          <div className="text-white/50 text-xs font-semibold mb-3 uppercase tracking-widest">Pipeline Progress</div>
          <PipelineTracker stages={STAGE_ORDER} currentStage={currentStage} completedStages={completedStages} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ── LEFT: Init + Prompt ── */}
          <div className="flex flex-col gap-4">

            {/* Company Setup */}
            {!workflowId ? (
              <div className="glass rounded-2xl p-5">
                <h2 className="text-white font-bold text-sm mb-4">🚀 Initialize Company</h2>
                <label className="text-white/60 text-xs mb-1.5 block">Company Name</label>
                <input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full rounded-xl px-3 py-2.5 text-sm text-gray-900 mb-4"
                  style={{ background: "rgba(255,255,255,0.9)", border: "none" }}
                  placeholder="e.g. LuxeHaven Real Estate"
                />
                <button
                  onClick={handleInit}
                  disabled={isIniting}
                  className="w-full py-3 rounded-xl font-bold text-sm text-white transition-all"
                  style={{
                    background: isIniting
                      ? "rgba(94,129,244,0.4)"
                      : "linear-gradient(135deg, #5e81f4, #8b5cf6)",
                    cursor: isIniting ? "not-allowed" : "pointer",
                    border: "none",
                    boxShadow: isIniting ? "none" : "0 4px 20px rgba(94,129,244,0.4)",
                  }}
                >
                  {isIniting ? "Initializing..." : "Initialize Workspace"}
                </button>
              </div>
            ) : (
              <div className="glass rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-1">
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} />
                  <span className="text-white font-bold text-sm">{companyName}</span>
                </div>
                <div className="text-white/40 text-xs">Workspace active · {completedStages.length} stages complete</div>
              </div>
            )}

            {/* Prompt Input */}
            {workflowId && (
              <div className="glass rounded-2xl p-5">
                <div className="text-white/60 text-xs font-semibold mb-1 uppercase tracking-widest">
                  Current Stage
                </div>
                <div className="text-white font-bold text-sm mb-4">
                  {STAGE_LABELS[currentStage] || currentStage}
                </div>
                <label className="text-white/60 text-xs mb-1.5 block">Your Instructions</label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={5}
                  placeholder={`Describe what you want for ${STAGE_LABELS[currentStage] || currentStage}...`}
                  className="w-full rounded-xl px-3 py-2.5 text-sm text-gray-900 resize-none mb-4 scroll-thin"
                  style={{ background: "rgba(255,255,255,0.9)", border: "none", lineHeight: 1.6 }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.metaKey) handleSubmitPrompt();
                  }}
                />
                <button
                  onClick={handleSubmitPrompt}
                  disabled={isLoading || !prompt.trim()}
                  className="w-full py-3 rounded-xl font-bold text-sm text-white transition-all"
                  style={{
                    background:
                      isLoading || !prompt.trim()
                        ? "rgba(94,129,244,0.3)"
                        : "linear-gradient(135deg, #5e81f4, #8b5cf6)",
                    cursor: isLoading || !prompt.trim() ? "not-allowed" : "pointer",
                    border: "none",
                    boxShadow: isLoading ? "none" : "0 4px 20px rgba(94,129,244,0.4)",
                  }}
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="animate-spin">⟳</span> Delegating Work...
                    </span>
                  ) : (
                    "Submit & Delegate ⌘↵"
                  )}
                </button>
              </div>
            )}

            {/* Documents */}
            {documents.length > 0 && (
              <div className="glass rounded-2xl p-5">
                <h3 className="text-white font-bold text-xs uppercase tracking-widest mb-3">📄 Generated Outputs</h3>
                <div className="flex flex-col gap-2">
                  {documents.map((doc) => (
                    <button
                      key={doc.doc_id}
                      onClick={() => setSelectedDoc(doc)}
                      className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all w-full text-left cursor-pointer"
                      style={{
                        background: "rgba(94,129,244,0.15)",
                        color: "#a5b4fc",
                        border: "1px solid rgba(94,129,244,0.3)",
                      }}
                    >
                      <span>📋</span>
                      <span className="flex-1 truncate">{doc.title}</span>
                      <span className="text-xs opacity-60">View →</span>
                    </button>
                  ))}
                </div>
                <div className="text-white/40 text-xs mt-3">Use browser Print → Save as PDF</div>
              </div>
            )}
          </div>

          {/* ── CENTER + RIGHT: Delegation Graph ── */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            {latestGraph ? (
              <div className="glass-light rounded-2xl p-5 overflow-auto scroll-thin" style={{ maxHeight: "70vh" }}>
                <DelegationView graph={latestGraph} />
              </div>
            ) : (
              <div
                className="glass rounded-2xl flex flex-col items-center justify-center text-center"
                style={{ minHeight: 300 }}
              >
                <div className="text-5xl mb-4">🏗️</div>
                <div className="text-white/70 font-semibold text-base">No work delegated yet</div>
                <div className="text-white/40 text-sm mt-2 max-w-xs">
                  Initialize your company workspace and submit your first prompt to see the
                  Manager → Team delegation tree here.
                </div>
              </div>
            )}

            {/* Activity log */}
            <div className="glass rounded-2xl p-4">
              <div className="text-white/40 text-xs font-semibold uppercase tracking-widest mb-2">⚡ Activity Log</div>
              <div className="flex flex-col gap-1 max-h-32 overflow-y-auto scroll-thin">
                {log.length === 0 && (
                  <div className="text-white/30 text-xs">No activity yet...</div>
                )}
                {log.map((l, i) => (
                  <div key={i} className="text-xs font-mono" style={{ color: i === 0 ? "#a5b4fc" : "rgba(255,255,255,0.4)" }}>
                    {l}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* History */}
        {delegationHistory.length > 1 && (
          <div className="glass rounded-2xl p-5">
            <h3 className="text-white font-bold text-xs uppercase tracking-widest mb-4">📜 Delegation History</h3>
            <div className="flex flex-col gap-4">
              {delegationHistory.slice(1).map((g) => (
                <div key={g.graph_id} className="glass-light rounded-xl p-4 opacity-80">
                  <DelegationView graph={g} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Document Viewer Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white w-full max-w-5xl h-[85vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden relative border border-gray-200">
            <div className="flex items-center justify-between p-4 border-b bg-gray-50">
              <h2 className="text-lg font-bold text-gray-800">{selectedDoc.title}</h2>
              <button 
                onClick={() => setSelectedDoc(null)}
                className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500 transition-colors cursor-pointer font-bold text-xl"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 bg-gray-100 p-0 overflow-auto relative">
              <DocumentViewer 
                url={selectedDoc.url} 
                fileType={selectedDoc.stage === 'PITCH_DECK_CREATION' ? 'ppt' : 'pdf'} 
                filename={selectedDoc.title} 
              />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
