import { useState, useEffect, useCallback, useMemo } from "react";
import { ProjectWorkspace, ProjectOutput } from "./Showcase/ProjectWorkspace";

/** Renders markdown text as clean HTML — no raw ### or ** visible */
function MarkdownRenderer({ content, className }: { content: string; className?: string }) {
  const html = useMemo(() => {
    if (!content) return "";
    let md = content
      // strip leading/trailing whitespace
      .trim()
      // headings
      .replace(/^######\s+(.+)$/gm, "<h6 style='font-size:13px;font-weight:700;color:#1a1a2e;margin:16px 0 6px'>$1</h6>")
      .replace(/^#####\s+(.+)$/gm, "<h5 style='font-size:14px;font-weight:700;color:#1a1a2e;margin:16px 0 6px'>$1</h5>")
      .replace(/^####\s+(.+)$/gm, "<h4 style='font-size:15px;font-weight:700;color:#1a1a2e;margin:18px 0 8px'>$1</h4>")
      .replace(/^###\s+(.+)$/gm, "<h3 style='font-size:17px;font-weight:700;color:#1a1a2e;margin:20px 0 10px;padding-bottom:4px;border-bottom:2px solid #e5e7eb'>$1</h3>")
      .replace(/^##\s+(.+)$/gm, "<h2 style='font-size:20px;font-weight:700;color:#111827;margin:24px 0 12px;padding-bottom:6px;border-bottom:2px solid #d1d5db'>$1</h2>")
      .replace(/^#\s+(.+)$/gm, "<h1 style='font-size:24px;font-weight:800;color:#111827;margin:0 0 16px;padding-bottom:8px;border-bottom:3px solid #6366f1'>$1</h1>")
      // bold + italic
      .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
      .replace(/\*\*(.+?)\*\*/g, "<strong style='color:#111827'>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // inline code
      .replace(/`(.+?)`/g, "<code style='background:#f1f5f9;color:#6366f1;padding:2px 6px;border-radius:4px;font-size:13px;font-family:monospace'>$1</code>")
      // horizontal rule
      .replace(/^---+$/gm, "<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0'/>")
      // tables: |col|col|
      .replace(/^\|(.+)\|$/gm, (line) => {
        if (line.replace(/[|\s-]/g, '').length === 0) return ''; // separator row
        const cells = line.split('|').filter(c => c.trim() !== '');
        const isHeader = false;
        const tds = cells.map(c => `<td style='padding:8px 14px;border:1px solid #e5e7eb;font-size:14px;color:#374151'>${c.trim()}</td>`).join('');
        return `<tr>${tds}</tr>`;
      })
      // wrap consecutive <tr> in <table>
      .replace(/(<tr>.*?<\/tr>\n?)+/gs, (block) =>
        `<table style='width:100%;border-collapse:collapse;margin:16px 0;font-size:14px'><tbody>${block}</tbody></table>`
      )
      // unordered lists
      .replace(/^[*\-]\s+(.+)$/gm, "<li style='margin:4px 0;color:#374151;font-size:15px;line-height:1.6'>$1</li>")
      .replace(/(<li[^>]*>.*<\/li>\n?)+/gs, (block) =>
        `<ul style='padding-left:20px;margin:8px 0 16px'>${block}</ul>`
      )
      // ordered lists
      .replace(/^\d+\.\s+(.+)$/gm, "<li style='margin:4px 0;color:#374151;font-size:15px;line-height:1.6'>$1</li>")
      // blockquote
      .replace(/^>\s+(.+)$/gm, "<blockquote style='border-left:4px solid #6366f1;padding:8px 16px;margin:12px 0;background:#f8f9ff;color:#4b5563;font-style:italic'>$1</blockquote>")
      // double newlines -> paragraph breaks
      .replace(/\n\n/g, "</p><p style='margin:0 0 12px;color:#374151;font-size:15px;line-height:1.75'>")
      // single newlines
      .replace(/\n/g, "<br/>");
    return `<div style='font-family:Inter,system-ui,sans-serif;color:#374151;line-height:1.75'><p style='margin:0 0 12px;color:#374151;font-size:15px;line-height:1.75'>${md}</p></div>`;
  }, [content]);
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

interface TeamResult {
  team: string;
  subtask: string;
  result: string;
  completed_at?: string;
}

interface TaskLog {
  task_id: string;
  project_task: string;
  submitted_at: string;
  status: "queued" | "in_progress" | "complete" | "failed";
  total_duration_seconds?: number;
  final_report?: string;
  team_results?: TeamResult[];
  manager_plan?: { project: string; overview: string };
}

const STATUS_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  queued: { bg: "#f2b01f", color: "#241303", label: "QUEUED" },
  in_progress: { bg: "#6aa9ff", color: "#0c1c38", label: "WORKING" },
  complete: { bg: "#79d97c", color: "#0e2a12", label: "COMPLETE" },
  failed: { bg: "#e5484d", color: "#ffd7d8", label: "FAILED" },
};

const STATUS_ICONS: Record<string, string> = {
  queued: "⏳",
  in_progress: "⚡",
  complete: "✅",
  failed: "❌",
};

/**
 * Extracts pure HTML code from markdown code fences or raw text
 */
function extractHtml(raw: string): string | null {
  if (!raw) return null;

  let content = raw;

  // 1. If it has a markdown fence, extract the content inside it first
  const fenceMatch = content.match(/```(?:html|htm|xml)?\s*([\s\S]*?)(?:```|$)/i);
  if (fenceMatch && fenceMatch[1]) {
    content = fenceMatch[1].trim();
  }

  // 2. Strip any garbage BEFORE the actual HTML document starts
  const docStart = content.match(/(<!DOCTYPE html[\s\S]*)/i);
  if (docStart && docStart[1]) {
    return docStart[1].trim();
  }

  const htmlStart = content.match(/(<html[\s\S]*)/i);
  if (htmlStart && htmlStart[1]) {
    return htmlStart[1].trim();
  }

  const divStart = content.match(/(<div[\s\S]*)/i);
  if (divStart && divStart[1] && (divStart[1].includes("className") || divStart[1].includes("class="))) {
    return divStart[1].trim();
  }

  return null;
}

/* ── Tab configuration for deliverables modal ── */
const TAB_CONFIG: Record<string, { color: string; emoji: string; label: string }> = {
  website: { color: "#79d97c", emoji: "🌐", label: "WEBSITE" },
  ppt: { color: "#f2b01f", emoji: "📊", label: "PPT" },
  image: { color: "#f472b6", emoji: "🖼️", label: "IMAGE" },
  report: { color: "#a78bfa", emoji: "📄", label: "REPORT" },
  showcase: { color: "#f2b01f", emoji: "✨", label: "SHOWCASE" },
};

export default function TaskPanel() {
  const [open, setOpen] = useState(false);
  const [taskInput, setTaskInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [tasks, setTasks] = useState<TaskLog[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskLog | null>(null);
  const [activeTab, setActiveTab] = useState<string>("showcase");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [iframeKey, setIframeKey] = useState(0);
  const [subtaskBreakdown, setSubtaskBreakdown] = useState<Array<{team: string; task: string}>>([]);

  const showToast = (msg: string) => {
    setToast(msg);
    // Don't auto-dismiss if it's an error message
    if (!msg.includes("❌")) {
      setTimeout(() => setToast(null), 4000);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    showToast("📋 Copied to clipboard!");
    setTimeout(() => setCopiedKey(null), 2500);
  };

  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`💾 Downloaded ${filename}!`);
  };

  const openPreviewInNewTab = (htmlContent: string) => {
    const newWindow = window.open();
    if (newWindow) {
      newWindow.document.write(htmlContent);
      newWindow.document.close();
    }
  };

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/tasks/`);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch {}
  }, []);

  useEffect(() => {
    if (!open) return;
    fetchTasks();
    const interval = setInterval(fetchTasks, 4000);
    return () => clearInterval(interval);
  }, [open, fetchTasks]);

  useEffect(() => {
    if (!selectedTask || selectedTask.status === "complete") return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/tasks/${selectedTask.task_id}`);
        const data = await res.json();
        setSelectedTask(data);
      } catch {}
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedTask?.task_id, selectedTask?.status]);

  const handleSubmit = async () => {
    if (!taskInput.trim() || taskInput.trim().length < 5) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/tasks/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: taskInput.trim(), submitted_by: "kaushal" }),
      });
      if (!res.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await res.json();
      showToast("🚀 Task assigned to Manager! Watch the office come alive.");
      setTaskInput("");
      // Capture subtask breakdown if returned by orchestrator
      if (data.subtasks && Array.isArray(data.subtasks)) {
        setSubtaskBreakdown(data.subtasks);
      }
      fetchTasks();
      if (data.task_id) {
        setSelectedTask({
          task_id: data.task_id,
          project_task: taskInput.trim(),
          submitted_at: new Date().toISOString(),
          status: "queued",
          team_results: [],
        });
        setActiveTab("coder");
      }
    } catch (e) {
      showToast("❌ groq and gemini ip is block in this network , try with another network");
    } finally {
      setSubmitting(false);
    }
  };

  // Scan ALL team results for HTML (not just 'coder') — Manager LLM may assign any team name
  const allResults = selectedTask?.team_results?.map((r) => r.result || "") || [];
  const allResultsJoined = allResults.join("\n");
  const coderResult = selectedTask?.team_results?.find((r) => r.team === "coder")?.result || allResultsJoined;
  const previewHtml = useMemo(() => {
    // 1. Contract-based detection first
    for (const r of selectedTask?.team_results || []) {
      if (r.preview_type === 'LIVE_WEBSITE' || r.modality === 'WEBSITE') {
        const extracted = extractHtml(r.result || "");
        if (extracted) return extracted;
      }
    }
    // 2. Fallback heuristic detection
    for (const r of selectedTask?.team_results || []) {
      const extracted = extractHtml(r.result || "");
      if (extracted) return extracted;
    }
    return null;
  }, [selectedTask?.team_results]);

  const availableTabs = useMemo(() => {
    if (!selectedTask) return [];
    const tabs: string[] = [];
    const finalReport = selectedTask.final_report || "";
    
    // WEBSITE: Check explicit contract or heuristic fallback
    const hasWebsiteContract = selectedTask.team_results?.some(r => r.preview_type === 'LIVE_WEBSITE' || r.modality === 'WEBSITE');
    
    if (previewHtml || hasWebsiteContract) {
      tabs.push("website");
    }
    
    // PPT: Check finalReport or any team result for pptx links
    const pptPattern = /\[.*?\]\((.*?\.(pptx|pdf))\)/i;
    const pptKeywords = /presentation|powerpoint|pptx|slide deck/i;
    if (finalReport.match(pptPattern) || allResultsJoined.match(pptPattern) || allResultsJoined.match(pptKeywords)) {
      tabs.push("ppt");
    }
    
    // IMAGE: Check finalReport for embedded images (not website screenshots)
    const imgPattern = /!\[.*?\]\((https?:\/\/.*?)\)/i;
    const imgKeywords = /image generated|poster created|graphic created/i;
    if ((finalReport.match(imgPattern) || allResultsJoined.match(imgKeywords)) && !previewHtml) {
      tabs.push("image");
    }

    // REPORT: Always show if task complete or there's a final_report
    if (finalReport || selectedTask.status === "complete") {
      tabs.push("report");
    }

    // SHOWCASE: show as fallback
    if (tabs.length === 0 || (!previewHtml && !tabs.includes("ppt"))) {
      tabs.push("showcase");
    }

    return Array.from(new Set(tabs));
  }, [selectedTask, previewHtml, allResultsJoined]);

  useEffect(() => {
    if (availableTabs.includes("website")) {
      setActiveTab("website");
    } else if (availableTabs.includes("ppt")) {
      setActiveTab("ppt");
    } else if (availableTabs.includes("showcase")) {
      setActiveTab("showcase");
    }
  }, [availableTabs.join(",")]);

  const showcaseOutput = useMemo<ProjectOutput | null>(() => {
    if (!selectedTask || !selectedTask.final_report) return null;
    
    // Check for PPT or PDF artifact
    const pptMatch = selectedTask.final_report.match(/\[.*?\]\((.*?\.(pptx|pdf))\)/i);
    if (pptMatch) {
      const url = pptMatch[1];
      const isPdf = url.toLowerCase().endsWith('.pdf');
      return {
        id: selectedTask.task_id,
        type: isPdf ? 'pdf' : 'ppt',
        title: selectedTask.manager_plan?.project || selectedTask.project_task,
        url: url,
      };
    }
    
    // Check for Website (raw HTML)
    const htmlMatch = previewHtml;
    if (htmlMatch) {
      return {
        id: selectedTask.task_id,
        type: 'code',
        title: selectedTask.manager_plan?.project || selectedTask.project_task,
        content: htmlMatch,
        metadata: { isWebProject: true, language: 'html' }
      };
    }
    
    return null;
  }, [selectedTask, previewHtml]);

  const workingIntent = useMemo(() => {
    if (!selectedTask) return "your request";
    
    const taskInput = (selectedTask.project_task || "").toLowerCase();
    const planText = selectedTask.manager_plan ? JSON.stringify(selectedTask.manager_plan).toLowerCase() : "";
    const combined = taskInput + " " + planText;
    
    if (combined.includes("website") || combined.includes("landing page") || combined.includes("html") || combined.includes("react")) {
      return "a Website";
    }
    if (combined.includes("ppt") || combined.includes("presentation") || combined.includes("powerpoint") || combined.includes("slide")) {
      return "a Presentation";
    }
    if (combined.includes("image") || combined.includes("poster") || combined.includes("logo") || combined.includes("graphic")) {
      return "an Image";
    }
    return "a Report";
  }, [selectedTask]);

  return (
    <>
      {/* Toast notification */}
      {toast && (
        <div
          style={{
            position: "fixed",
            top: 20,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 9999,
          }}
        >
          <div
            className="px-5 py-3 relative pr-10"
            style={{
              ...pixelPanel,
              boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 8px 8px 0 6px rgba(0,0,0,0.5)",
            }}
          >
            <span
              className="text-[9px] tracking-widest text-[#7fd4ff]"
              style={{ fontFamily: PIXEL }}
            >
              {toast}
            </span>
            <button
              onClick={() => setToast(null)}
              className="absolute right-2 top-2 text-[#e5484d] hover:text-white cursor-pointer"
              style={{ fontFamily: PIXEL, fontSize: "10px" }}
              aria-label="Close"
            >
              [X]
            </button>
          </div>
        </div>
      )}

      {/* ── Floating Action Button ── */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-19 right-4 md:bottom-21 md:right-5 z-1000 cursor-pointer transition-transform active:translate-y-0.5"
        style={{
          fontFamily: PIXEL,
          fontSize: "9px",
          letterSpacing: "0.1em",
          padding: "11px 15px",
          background: open ? "#3a1418" : "#e77d1d",
          color: open ? "#ffd7d8" : "#241303",
          boxShadow: open
            ? "0 0 0 2px #e5484d, 0 0 0 4px #0b0e15, inset -2px -2px 0 rgba(0,0,0,0.4), inset 2px 2px 0 rgba(255,255,255,0.12)"
            : "0 0 0 2px #f2a55d, 0 0 0 4px #0b0e15, inset -2px -2px 0 rgba(0,0,0,0.22), inset 2px 2px 0 rgba(255,255,255,0.28)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        {open ? "X CLOSE" : "📋 ASSIGN TASK"}
      </button>

      {/* ── Right Drawer: Task Center & Project List ── */}
      {open && (
        <div
          className="fixed bottom-19 right-6 z-999 flex flex-col overflow-hidden"
          style={{
            ...pixelPanel,
            width: 420,
            maxHeight: "calc(100vh - 130px)",
            fontFamily: TERM,
            color: "#e8edf4",
          }}
        >
          {/* Header */}
          <div
            className="px-5 py-4 shrink-0 flex items-center justify-between gap-3"
            style={{ borderBottom: "3px solid #3a4356", background: "#1b2230" }}
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">🏢</span>
              <div className="flex flex-col gap-1">
                <span
                  className="text-[11px] md:text-[13px] tracking-wider text-[#f2b01f]"
                  style={{ fontFamily: PIXEL }}
                >
                  <span className="text-[#c8d2e4]">{"\u2500\u25B6 "}</span>
                  TASK CENTER
                </span>
                <span className="text-[17px] text-[#aeb9cf]">
                  Assign projects & get full code deliverables
                </span>
              </div>
            </div>
            
            {/* Knowledge Upload Button */}
            <div className="relative shrink-0">
              <input
                type="file"
                id="knowledge-upload"
                accept=".pdf,.txt,.xlsx,.xls,.csv"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  
                  const formData = new FormData();
                  formData.append("file", file);
                  
                  showToast("📚 Uploading knowledge...");
                  try {
                    const res = await fetch(`${API_URL}/api/v1/real-estate/knowledge/upload`, {
                      method: "POST",
                      body: formData,
                    });
                    const data = await res.json();
                    if (res.ok && data.status === "success") {
                      showToast(`✅ Knowledge learned! (${data.chunks_added} chunks)`);
                    } else {
                      showToast("❌ Failed to learn knowledge");
                    }
                  } catch (e) {
                    showToast("❌ Upload error");
                  }
                  e.target.value = ""; // reset
                }}
              />
              <label
                htmlFor="knowledge-upload"
                className="cursor-pointer transition-transform active:translate-y-0.5"
                style={{
                  fontFamily: PIXEL,
                  fontSize: "8px",
                  padding: "8px 12px",
                  background: "#79d97c",
                  color: "#0e2a12",
                  boxShadow: "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)",
                  display: "inline-block"
                }}
              >
                📚 UPLOAD DOC
              </label>
            </div>
          </div>

          {/* Prompt Input Box */}
          <div
            className="px-5 py-4 shrink-0"
            style={{ borderBottom: "3px solid #3a4356" }}
          >
            <label
              className="block mb-2 text-[9px] tracking-widest text-[#c8d2e4]"
              style={{ fontFamily: PIXEL }}
              htmlFor="task-input"
            >
              PROJECT BRIEF
            </label>
            <textarea
              id="task-input"
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSubmit();
              }}
              placeholder="Assign a task to the team...&#10;e.g. 'Build a coffee shop landing page with hero, menu, and reservation form'"
              rows={3}
              className="w-full px-3 py-2.5 focus:outline-none placeholder:text-[#4e5a70]"
              style={{
                fontFamily: TERM,
                fontSize: "18px",
                lineHeight: 1.4,
                background: "#0b0e15",
                color: "#e8edf4",
                border: "none",
                boxShadow: "0 0 0 2px #3a4356, inset 3px 3px 0 rgba(0,0,0,0.6)",
                caretColor: "#f28a1f",
                resize: "none",
                boxSizing: "border-box",
              }}
            />
            <div className="flex justify-between items-center mt-3">
              <span
                className="text-[8px] tracking-widest text-[#4e5a70]"
                style={{ fontFamily: PIXEL }}
              >
                CTRL+ENTER
              </span>
              <button
                onClick={handleSubmit}
                disabled={submitting || taskInput.trim().length < 5}
                className="cursor-pointer transition-transform active:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  fontFamily: PIXEL,
                  fontSize: "9px",
                  letterSpacing: "0.1em",
                  padding: "10px 18px",
                  background:
                    submitting || taskInput.trim().length < 5
                      ? "#3a4356"
                      : "#f28a1f",
                  color:
                    submitting || taskInput.trim().length < 5
                      ? "#7f8ca5"
                      : "#241303",
                  boxShadow:
                    submitting || taskInput.trim().length < 5
                      ? "none"
                      : "0 0 0 3px #12161f, inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.35), 0 4px 0 3px #12161f",
                }}
              >
                {submitting ? "SENDING..." : "🚀 SEND TO TEAM"}
              </button>
            </div>
          </div>

          {/* Subtask Breakdown (shown after submit) */}
          {subtaskBreakdown.length > 0 && (
            <div
              className="px-5 py-3 shrink-0"
              style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
            >
              <div className="flex items-center justify-between mb-3">
                <span
                  className="px-3 py-1.5 text-[8px] tracking-widest"
                  style={{
                    fontFamily: PIXEL,
                    background: "#a78bfa",
                    color: "#12161f",
                    boxShadow:
                      "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)",
                  }}
                >
                  📋 PLAN ({subtaskBreakdown.length})
                </span>
                <button
                  onClick={() => setSubtaskBreakdown([])}
                  className="w-7 h-7 flex items-center justify-center text-[10px] text-[#7f8ca5] hover:text-[#c8d2e4] cursor-pointer"
                  style={{ fontFamily: PIXEL }}
                >
                  X
                </button>
              </div>
              {subtaskBreakdown.map((st, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 py-2"
                  style={{
                    borderTop: i > 0 ? "1px solid #232a38" : "none",
                  }}
                >
                  <span
                    className="text-[8px] px-2 py-1 tracking-widest shrink-0 mt-0.5"
                    style={{
                      fontFamily: PIXEL,
                      background: "#88c0d022",
                      color: "#88c0d0",
                      boxShadow: "0 0 0 1px #88c0d044",
                    }}
                  >
                    {st.team.toUpperCase()}
                  </span>
                  <span className="text-[17px] text-[#aeb9cf] leading-snug">
                    {st.task}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Recent Tasks List */}
          <div className="overflow-y-auto flex-1" style={{ maxHeight: "360px" }}>
            <div
              className="px-5 py-3 sticky top-0 z-10 flex items-center gap-3"
              style={{
                borderBottom: "3px solid #3a4356",
                background: "#1b2230",
              }}
            >
              <span
                className="text-[9px] tracking-widest text-[#c8d2e4]"
                style={{ fontFamily: PIXEL }}
              >
                PROJECT LOGS ({tasks.length})
              </span>
              <span className="flex-1 h-0.5 bg-[#3a4356]" />
            </div>
            {tasks.length === 0 && (
              <div className="text-center py-10 px-5">
                <p
                  className="text-[9px] tracking-widest text-[#7f8ca5]"
                  style={{ fontFamily: PIXEL }}
                >
                  NO TASKS YET
                </p>
                <p className="text-[19px] text-[#4e5a70] mt-3 leading-relaxed">
                  Type a project above and your team will build it! 🚀
                </p>
              </div>
            )}
             {tasks.map((task) => {
              const statusConf = STATUS_STYLES[task.status] || STATUS_STYLES.queued;
              return (
                <div
                  key={task.task_id}
                  onClick={() => {
                    setSelectedTask(task);
                    setActiveTab(task.status === "complete" ? "showcase" : "coder");
                  }}
                  className="px-5 py-4 cursor-pointer transition-colors hover:bg-[#1b2230]"
                  style={{
                    borderBottom: "1px solid #232a38",
                    background: selectedTask?.task_id === task.task_id ? "#1b2230" : "transparent",
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className="text-[8px] px-2.5 py-1 tracking-widest"
                      style={{ fontFamily: PIXEL, background: statusConf.bg, color: statusConf.color, boxShadow: "inset -2px -2px 0 rgba(0,0,0,0.2), inset 2px 2px 0 rgba(255,255,255,0.25)" }}
                    >
                      {STATUS_ICONS[task.status]} {statusConf.label}
                    </span>
                    {task.total_duration_seconds && (
                      <span className="text-[15px] text-[#4e5a70]">⏱ {task.total_duration_seconds}s</span>
                    )}
                  </div>
                  <div className="text-[18px] text-[#e8edf4] truncate leading-snug">
                    {task.project_task}
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-[15px] text-[#4e5a70]">
                      {new Date(task.submitted_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <div className="flex items-center gap-2">
                      {task.status === "complete" && task.final_report && (
                        <span
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTask(task);
                            setActiveTab("showcase");
                          }}
                          className="text-[8px] tracking-widest px-2 py-1 cursor-pointer"
                          style={{ fontFamily: PIXEL, background: "#6366f122", color: "#a5b4fc", border: "1px solid #6366f144" }}
                        >
                          👁 PREVIEW
                        </span>
                      )}
                      <span className="text-[8px] tracking-widest text-[#6aa9ff]" style={{ fontFamily: PIXEL }}>
                        OPEN ▶
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────
          CENTERED FULL-SIZE DELIVERABLES & LIVE PREVIEW MODAL
      ────────────────────────────────────────────────────────── */}
      {selectedTask && (
        <div
          className="fixed inset-0 z-1050 flex items-center justify-center p-4 md:p-8"
          style={{
            background: "rgba(4, 10, 22, 0.72)",
            backdropFilter: "blur(3px)",
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedTask(null);
          }}
        >
          <div
            className="w-full max-w-275 flex flex-col"
            style={{
              ...pixelPanel,
              height: "88vh",
              maxHeight: "850px",
              fontFamily: TERM,
              color: "#e8edf4",
            }}
          >
            {/* Modal Header */}
            <div
              className="px-5 md:px-8 py-5 flex items-center justify-between gap-4 shrink-0"
              style={{ borderBottom: "3px solid #3a4356", background: "#1b2230" }}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-base">📦</span>
                  <span
                    className="text-[11px] md:text-[13px] tracking-wider text-[#f2b01f] truncate"
                    style={{ fontFamily: PIXEL }}
                  >
                    {selectedTask.manager_plan?.project || "DELIVERABLES"}
                  </span>
                  {(() => {
                    const sc = STATUS_STYLES[selectedTask.status] || STATUS_STYLES.queued;
                    return (
                      <span
                        className="text-[8px] px-2.5 py-1 tracking-widest shrink-0"
                        style={{
                          fontFamily: PIXEL,
                          background: sc.bg,
                          color: sc.color,
                          boxShadow:
                            "inset -2px -2px 0 rgba(0,0,0,0.2), inset 2px 2px 0 rgba(255,255,255,0.25)",
                        }}
                      >
                        {sc.label}
                      </span>
                    );
                  })()}
                </div>
                <div className="text-[20px] text-[#aeb9cf] truncate">
                  {selectedTask.project_task}
                </div>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                aria-label="Close deliverables"
                className="shrink-0 w-11 h-11 flex items-center justify-center text-[14px] text-[#ffd7d8] cursor-pointer transition-transform active:translate-y-0.5"
                style={{
                  fontFamily: PIXEL,
                  background: "#3a1418",
                  boxShadow:
                    "0 0 0 3px #e5484d, inset -3px -3px 0 rgba(0,0,0,0.4), inset 3px 3px 0 rgba(255,255,255,0.12)",
                }}
              >
                X
              </button>
            </div>

            {/* Navigation Tabs */}
            <div
              className="flex shrink-0 overflow-x-auto"
              style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
              role="tablist"
            >
              {availableTabs.map((tab) => {
                const tc = TAB_CONFIG[tab] || { color: "#ffffff", emoji: "📄", label: tab.toUpperCase() };
                const active = activeTab === tab;
                return (
                  <button
                    key={tab}
                    role="tab"
                    aria-selected={active}
                    onClick={() => setActiveTab(tab)}
                    className="flex items-center gap-2 px-4 md:px-5 py-4 text-[9px] md:text-[10px] tracking-widest whitespace-nowrap cursor-pointer transition-colors"
                    style={{
                      fontFamily: PIXEL,
                      background: active ? tc.color : "transparent",
                      color: active ? "#12161f" : "#7f8ca5",
                      borderRight: "3px solid #232a38",
                      boxShadow: active
                        ? "inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.3)"
                        : "none",
                    }}
                  >
                    <span>{tc.emoji}</span>
                    {tc.label}
                  </button>
                );
              })}
            </div>

            {/* Tab Content Display */}
            <div className="overflow-y-auto flex-1 p-5 md:p-6" style={{ background: "#12161f" }}>
              {/* LIVE PREVIEW IFRAME */}
              {/* SHOWCASE & ARTIFACT TABS */}
              {activeTab === "showcase" || activeTab === "ppt" || activeTab === "image" ? (
                <div style={{ background: '#ffffff', borderRadius: 12, padding: showcaseOutput ? '0' : '32px 36px', minHeight: 400 }}>
                  {showcaseOutput ? (
                     <ProjectWorkspace output={showcaseOutput} />
                  ) : selectedTask.status === 'complete' ? (
                    <div style={{ color: '#6b7280', fontSize: 15, fontFamily: 'sans-serif', textAlign: 'center', paddingTop: 60 }}>No visual artifact generated yet.</div>
                  ) : (
                    <div style={{ textAlign: 'center', paddingTop: 60 }}>
                      <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
                      <div style={{ color: '#6b7280', fontSize: 15, fontFamily: 'sans-serif' }}>Team is generating {workingIntent}...</div>
                    </div>
                  )}
                </div>
              ) : activeTab === "report" ? (
                <div style={{ background: '#ffffff', borderRadius: 12, padding: '32px 36px', minHeight: 400 }}>
                  {selectedTask.final_report ? (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottom: '2px solid #f1f5f9' }}>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: '#6366f1', marginBottom: 6, fontFamily: 'sans-serif' }}>MYCEL AI · AUTONOMOUS OUTPUT</div>
                          <div style={{ fontSize: 22, fontWeight: 800, color: '#111827', fontFamily: 'Inter, sans-serif' }}>{selectedTask.manager_plan?.project || selectedTask.project_task}</div>
                        </div>
                        <button
                          onClick={() => {
                            const w = window.open();
                            if (w) {
                              w.document.write(`<!DOCTYPE html><html><head><meta charset='utf-8'><title>Report</title><style>body{font-family:Inter,sans-serif;max-width:860px;margin:40px auto;padding:0 24px;color:#374151;line-height:1.75}h1,h2,h3{color:#111827}table{border-collapse:collapse;width:100%}td,th{border:1px solid #e5e7eb;padding:8px 14px}@media print{button{display:none}}</style></head><body>${(document.querySelector('[data-report-content]') as any)?.innerHTML || ''}<br><button onclick='window.print()' style='background:#6366f1;color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:14px;cursor:pointer;margin-top:24px'>Print / Save as PDF</button></body></html>`);
                              w.document.close();
                            }
                          }}
                          style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', border: 'none', borderRadius: 10, padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'sans-serif', display: 'flex', alignItems: 'center', gap: 6 }}
                        >🖨️ Save as PDF</button>
                      </div>
                      <div data-report-content>
                        <MarkdownRenderer content={selectedTask.final_report} />
                      </div>
                    </>
                  ) : selectedTask.status === 'complete' ? (
                    <div style={{ color: '#6b7280', fontSize: 15, fontFamily: 'sans-serif', textAlign: 'center', paddingTop: 60 }}>No report generated yet.</div>
                  ) : (
                    <div style={{ textAlign: 'center', paddingTop: 60 }}>
                      <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
                      <div style={{ color: '#6b7280', fontSize: 15, fontFamily: 'sans-serif' }}>Team is generating {workingIntent}...</div>
                    </div>
                  )}
                </div>
              ) : activeTab === "website" && previewHtml ? (
                <div className="flex flex-col h-full gap-3">
                  {/* Browser Mockup Header */}
                  <div
                    className="flex items-center justify-between px-4 py-3 shrink-0"
                    style={{
                      background: "#1b2230",
                      boxShadow: "0 0 0 3px #3a4356",
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex gap-2">
                        <span className="w-3 h-3 inline-block" style={{ background: "#e5484d" }} />
                        <span className="w-3 h-3 inline-block" style={{ background: "#f2b01f" }} />
                        <span className="w-3 h-3 inline-block" style={{ background: "#79d97c" }} />
                      </div>
                      <span
                        className="px-3 py-1 text-[16px] text-[#7f8ca5]"
                        style={{
                          background: "#0b0e15",
                          boxShadow: "0 0 0 2px #3a4356",
                          fontFamily: TERM,
                        }}
                      >
                        <span style={{ color: "#79d97c" }}>🔒</span> https://mycel.ai/preview
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => setIframeKey((k) => k + 1)}
                        className="px-3 py-1.5 text-[8px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5"
                        style={{
                          fontFamily: PIXEL,
                          background: "#3a4356",
                          color: "#c8d2e4",
                          boxShadow:
                            "inset -2px -2px 0 rgba(0,0,0,0.3), inset 2px 2px 0 rgba(255,255,255,0.15)",
                        }}
                        title="Reload Preview"
                      >
                        🔄 RELOAD
                      </button>
                      <button
                        onClick={() => openPreviewInNewTab(previewHtml)}
                        className="px-3 py-1.5 text-[8px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5"
                        style={{
                          fontFamily: PIXEL,
                          background: "#6aa9ff",
                          color: "#0c1c38",
                          boxShadow:
                            "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)",
                        }}
                      >
                        🚀 FULL TAB
                      </button>
                      <button
                        onClick={() => downloadFile(previewHtml, "index.html")}
                        className="px-3 py-1.5 text-[8px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5"
                        style={{
                          fontFamily: PIXEL,
                          background: "#79d97c",
                          color: "#0e2a12",
                          boxShadow:
                            "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)",
                        }}
                      >
                        💾 DOWNLOAD
                      </button>
                    </div>
                  </div>

                  {/* Rendered HTML iframe */}
                  <div
                    className="flex-1"
                    style={{
                      minHeight: "460px",
                      overflow: "hidden",
                      boxShadow: "0 0 0 3px #3a4356",
                      background: "#ffffff",
                    }}
                  >
                    <iframe
                      key={iframeKey}
                      srcDoc={previewHtml}
                      title="Live Landing Page Preview"
                      sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                      style={{
                        width: "100%",
                        height: "100%",
                        minHeight: "460px",
                        border: "none",
                        display: "block",
                        backgroundColor: "#ffffff",
                      }}
                    />
                  </div>
                </div>
              ) : (
                (() => {
                  const teamResult = selectedTask.team_results?.find((r) => r.team === activeTab);
                  const content =
                    activeTab === "report"
                      ? selectedTask.final_report || "Final report is generating..."
                      : teamResult?.result ||
                        (selectedTask.status === "in_progress"
                          ? "⏳ Agent is currently working on this subtask..."
                          : "No output recorded for this team.");

                  const isHtml = content.includes("<!DOCTYPE html>") || content.includes("<html");
                  const fileExt = isHtml ? "html" : activeTab === "report" ? "md" : "py";
                  const isMarkdownLike = !isHtml && (content.includes('##') || content.includes('**') || content.includes('\n-'));

                  return (
                    <div>
                      <div className="flex flex-wrap justify-between items-center mb-4 pb-4" style={{ borderBottom: "3px solid #3a4356" }}>
                        <div>
                          {teamResult?.subtask && (
                            <div className="text-[18px] text-[#aeb9cf]">Subtask: <span className="text-[#e8edf4]">{teamResult.subtask}</span></div>
                          )}
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          {isHtml && (
                            <button onClick={() => { const e = extractHtml(content); if (e) openPreviewInNewTab(e); }} className="px-3 py-2 text-[8px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5" style={{ fontFamily: PIXEL, background: "#79d97c", color: "#0e2a12", boxShadow: "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)" }}>🌐 PREVIEW</button>
                          )}
                          <button onClick={() => copyToClipboard(content, activeTab)} className="px-3 py-2 text-[8px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5" style={{ fontFamily: PIXEL, background: copiedKey === activeTab ? "#79d97c" : "#3a4356", color: copiedKey === activeTab ? "#0e2a12" : "#c8d2e4", boxShadow: "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.15)" }}>📋 {copiedKey === activeTab ? "COPIED!" : "COPY"}</button>
                          <button onClick={() => downloadFile(content, `${activeTab}_${selectedTask.task_id.slice(0, 6)}.${fileExt}`)} className="px-3 py-2 text-[8px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5" style={{ fontFamily: PIXEL, background: "#6aa9ff", color: "#0c1c38", boxShadow: "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)" }}>💾 {fileExt.toUpperCase()}</button>
                        </div>
                      </div>
                      {isMarkdownLike ? (
                        <div style={{ background: '#fff', borderRadius: 8, padding: '24px 28px' }}>
                          <MarkdownRenderer content={content} />
                        </div>
                      ) : (
                        <pre className="px-5 py-4" style={{ background: "#0b0e15", boxShadow: "0 0 0 3px #3a4356, inset 3px 3px 0 rgba(0,0,0,0.4)", color: "#e2e8f0", fontSize: 14, lineHeight: 1.7, overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word", fontFamily: "'Fira Code', " + TERM }}>{content}</pre>
                      )}
                    </div>
                  );
                })()
              )}
            </div>
          </div>
        </div>
      )}

      <style>{`
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #0b0e15; }
        ::-webkit-scrollbar-thumb { background: #3a4356; }
        ::-webkit-scrollbar-thumb:hover { background: #4e5a70; }
      `}</style>
    </>
  );
}
