import { useAuth } from "../contexts/AuthContext";
import { useCallback, useEffect, useState } from "react";

import Button from "@components/ui/Button";
import type { ApiKeyItem } from "../types/agent";

const MONO = "'Courier New', monospace";
const KEY_PREFIX_TAG = "avo_";

export default function ApiKeyManager() {
  const { token, user } = useAuth();
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [keyName, setKeyName] = useState("Default");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchKeys = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/data/keys`);
      if (!response.ok) throw new Error("Failed to fetch keys");
      const data = await response.json();
      setKeys(data);
    } catch (err) {
      console.error("Failed to fetch API keys:", err);
      setError(`Load failed: ${err instanceof Error ? err.message : err}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/data/keys`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: keyName, user_id: user?.id }),
      });
      if (!response.ok) throw new Error("Failed to create key");
      const data = await response.json();
      setNewKey(data.api_key);
      setKeyName("Default");
      await fetchKeys();
    } catch (err) {
      console.error("Failed to create API key:", err);
      setError(`Creation failed: ${err instanceof Error ? err.message : err}`);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId: string) => {
    // Simplified for migration: just delete instead of revoke
    handleDelete(keyId);
  };

  const handleDelete = async (keyId: string) => {
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/data/keys/${keyId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      await fetchKeys();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-4" style={{ fontFamily: MONO }}>
      {/* ── Create ── */}
      <div className="flex gap-3">
        <input
          type="text"
          value={keyName}
          onChange={(e) => setKeyName(e.target.value)}
          placeholder="Key name"
          className="flex-1 px-3 py-2 text-xs text-[#eceff4] focus:outline-none placeholder-[#6b7994]"
          style={{
            background: "#3b4252",
            border: "3px solid #4c566a",
            borderRadius: 2,
            fontFamily: MONO,
          }}
        />
        <Button
          variant="primary"
          size="md"
          onClick={handleCreate}
          loading={creating}
        >
          🔑 Generate
        </Button>
      </div>

      {/* ── Error ── */}
      {error && (
        <div
          className="p-3 text-[11px] text-[#bf616a]"
          style={{
            background: "rgba(191, 97, 106, 0.15)",
            border: "3px solid #bf616a",
            borderRadius: 2,
          }}
        >
          ❌ {error}
        </div>
      )}

      {/* ── New key flash ── */}
      {newKey && (
        <div
          className="p-4"
          style={{
            background: "rgba(163, 190, 140, 0.2)",
            border: "3px solid #a3be8c",
            borderRadius: 2,
            boxShadow: "4px 4px 0 rgba(0,0,0,0.3)",
          }}
        >
          <p className="text-[11px] font-bold text-[#a3be8c] mb-2">
            ✅ New Key generated! Please copy it now, it won't be shown again.
          </p>
          <div className="flex items-center gap-2">
            <code
              className="flex-1 text-[10px] px-3 py-2 break-all text-[#a3be8c]"
              style={{
                background: "#2e3440",
                border: "2px solid #4c566a",
                borderRadius: 2,
              }}
            >
              {newKey}
            </code>
            <Button
              variant={copied ? "secondary" : "primary"}
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(newKey);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
            >
              {copied ? "✓ OK" : "📋 Copy"}
            </Button>
          </div>
        </div>
      )}

      {/* ── Key list ── */}
      {loading ? (
        <p className="text-[11px] text-[#6b7994]">⏳ Loading...</p>
      ) : keys.length === 0 ? (
        <p className="text-[11px] text-[#6b7994]">🔒 No keys created yet.</p>
      ) : (
        <div className="space-y-2">
          {keys.map((key) => (
            <div
              key={key.id}
              className="flex items-center justify-between p-3"
              style={{
                background: "rgba(59, 66, 82, 0.7)",
                border: "3px solid #4c566a",
                borderRadius: 2,
                opacity: 1,
              }}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="font-bold text-background">{key.name}</span>
                </div>
                <div className="text-[9px] text-[#6b7994] mt-1">
                  📅 {new Date(key.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(key.id)}
                >
                  🗑️ Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
