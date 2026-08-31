import React, { useState } from "react";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

interface Props {
  onClose: () => void;
  token: string | null;
}

export default function UploadDataModal({ onClose, token }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setStatus("uploading");
    setMessage("Uploading and indexing...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${baseUrl}/api/v1/real_estate/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setStatus("success");
        setMessage(data.message || "File uploaded and ingestion started.");
        setTimeout(() => onClose(), 2200);
      } else {
        setStatus("error");
        setMessage(data.detail || "Upload failed.");
      }
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || "Network error.");
    }
  };

  const statusColor = status === "success" ? "#a3be8c" : status === "error" ? "#bf616a" : "#ebcb8b";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.75)" }}>
      <div
        className="w-full max-w-md flex flex-col overflow-hidden"
        style={{
          background: "#12161f",
          boxShadow:
            "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.55)",
          imageRendering: "pixelated",
        }}
      >
        {/* Header */}
        <div
          className="px-6 py-4 flex items-center justify-between"
          style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
        >
          <div>
            <div className="text-[9px] font-bold tracking-widest text-[#f28a1f]" style={{ fontFamily: PIXEL }}>
              📂 UPLOAD PROPERTY DATA
            </div>
            <div className="text-[16px] text-[#7f8ca5] mt-1" style={{ fontFamily: TERM }}>
              Excel (.xlsx / .xls) files only
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center text-[10px] font-bold transition-transform active:translate-y-0.5"
            style={{
              fontFamily: PIXEL,
              background: "#3a1418",
              color: "#ffd7d8",
              boxShadow: "0 0 0 2px #e5484d, inset -2px -2px 0 rgba(0,0,0,0.4)",
            }}
          >
            X
          </button>
        </div>

        {/* Drop zone */}
        <div className="px-6 py-6">
          <div
            className="relative flex flex-col items-center justify-center py-10 gap-3 cursor-pointer transition-colors"
            style={{
              border: file ? "3px solid #a3be8c" : "3px dashed #3a4356",
              background: file ? "#1a2e1a" : "#0d1117",
            }}
            onClick={() => document.getElementById("re-file-upload")?.click()}
          >
            <input
              type="file"
              id="re-file-upload"
              className="hidden"
              accept=".xlsx,.xls"
              onChange={(e) => {
                setFile(e.target.files?.[0] || null);
                setStatus("idle");
                setMessage("");
              }}
            />
            <span className="text-4xl">{file ? "📄" : "📊"}</span>
            {file ? (
              <div className="text-center">
                <div className="text-[18px] font-bold text-[#a3be8c]" style={{ fontFamily: TERM }}>
                  {file.name}
                </div>
                <div className="text-[13px] text-[#4e5a70]" style={{ fontFamily: TERM }}>
                  {(file.size / 1024).toFixed(1)} KB — ready to upload
                </div>
              </div>
            ) : (
              <div className="text-center">
                <div className="text-[18px] text-[#4e5a70]" style={{ fontFamily: TERM }}>
                  Click to select properties.xlsx
                </div>
                <div className="text-[7px] text-[#3a4356] tracking-widest mt-1" style={{ fontFamily: PIXEL }}>
                  OR DRAG & DROP
                </div>
              </div>
            )}
          </div>

          {/* Status message */}
          {status !== "idle" && (
            <div
              className="mt-4 px-4 py-3 flex items-center gap-3"
              style={{
                background: status === "success" ? "#1a2e1a" : status === "error" ? "#2e1a1a" : "#1b2230",
                borderLeft: `3px solid ${statusColor}`,
              }}
            >
              {status === "uploading" && (
                <span className="text-[18px] animate-spin inline-block" style={{ fontFamily: TERM }}>↻</span>
              )}
              <span className="text-[16px]" style={{ fontFamily: TERM, color: statusColor }}>
                {message}
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div
          className="px-6 py-4 flex justify-end gap-3"
          style={{ borderTop: "3px solid #3a4356", background: "#0b0e15" }}
        >
          <button
            onClick={onClose}
            className="px-5 py-2 text-[8px] tracking-widest transition-transform active:translate-y-0.5"
            style={{
              fontFamily: PIXEL,
              background: "#1b2230",
              color: "#7f8ca5",
              boxShadow: "0 0 0 2px #3a4356, 0 3px 0 2px #12161f",
            }}
          >
            CANCEL
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || status === "uploading"}
            className="px-5 py-2 text-[8px] tracking-widest transition-transform active:translate-y-0.5 disabled:opacity-40"
            style={{
              fontFamily: PIXEL,
              background: "#f28a1f",
              color: "#241303",
              boxShadow:
                "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.25), 0 3px 0 2px #12161f",
            }}
          >
            {status === "uploading" ? "UPLOADING..." : "UPLOAD ▶"}
          </button>
        </div>
      </div>
    </div>
  );
}
