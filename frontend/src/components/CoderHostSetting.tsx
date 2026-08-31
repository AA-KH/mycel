import Button from "@components/ui/Button";
import { useEffect, useState } from "react";

const MONO = "'Courier New', monospace";
const STORAGE_KEY = "avo_coder_host";

export function getCoderHost(): string {
  return localStorage.getItem(STORAGE_KEY) || "";
}

export default function CoderHostSetting() {
  const [host, setHost] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setHost(getCoderHost());
  }, []);

  const handleSave = () => {
    // Normalize: remove trailing slash
    const normalized = host.replace(/\/+$/, "");
    localStorage.setItem(STORAGE_KEY, normalized);
    setHost(normalized);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-3" style={{ fontFamily: MONO }}>
      <p className="text-[11px] text-[#8892a6]">
        🌐 Enter your Coder deployment URL. Agents in the office will link directly to their corresponding workspace.
      </p>

      <div className="flex gap-3">
        <input
          type="url"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          placeholder="https://coder.example.com"
          className="flex-1 px-3 py-2 text-xs text-[#eceff4] focus:outline-none placeholder-[#6b7994]"
          style={{
            background: "#3b4252",
            border: "3px solid #4c566a",
            borderRadius: 2,
            fontFamily: MONO,
          }}
        />
        <Button
          variant={saved ? "secondary" : "primary"}
          size="md"
          onClick={handleSave}
        >
          {saved ? "✓ Saved" : "💾 Save"}
        </Button>
      </div>

      {host && (
        <p className="text-[10px] text-[#6b7994]">
          💡 After an Agent reports a workspace, the office will show a link to{" "}
          <code className="text-[#88c0d0]">{host}/@me/workspace</code>
        </p>
      )}
    </div>
  );
}
