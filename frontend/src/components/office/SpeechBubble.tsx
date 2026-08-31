import { useEffect, useState } from "react";

interface Props {
  text: string;
  visible: boolean;
  /** Bubble auto-hides after this many ms. 0 = never. */
  autoHideMs?: number;
}

/**
 * Pixel-art speech bubble with crisp text rendering and shadow.
 */
export default function SpeechBubble({
  text,
  visible,
  autoHideMs = 6000,
}: Props) {
  const [show, setShow] = useState(visible);

  useEffect(() => {
    if (visible && text) {
      setShow(true);
      if (autoHideMs > 0) {
        const timer = setTimeout(() => setShow(false), autoHideMs);
        return () => clearTimeout(timer);
      }
    } else {
      setShow(false);
    }
  }, [visible, text, autoHideMs]);

  if (!show || !text) return null;

  const truncated = text.length > 50 ? text.slice(0, 47) + "..." : text;

  return (
    <div
      className="absolute pointer-events-none select-none"
      style={{
        bottom: "100%",
        left: "50%",
        transform: "translateX(-50%)",
        marginBottom: 8,
        zIndex: 50,
      }}
    >
      <div
        className="relative px-2 py-1 rounded-md text-[8px] leading-tight text-center whitespace-nowrap shadow-lg"
        style={{
          backgroundColor: "#ffffff",
          color: "#0f172a",
          border: "1px solid #94a3b8",
          fontFamily: "'Courier New', monospace",
          fontWeight: 700,
          boxShadow: "0 4px 10px rgba(0,0,0,0.4)",
        }}
      >
        {truncated}
        {/* Triangle pointer */}
        <div
          className="absolute"
          style={{
            top: "100%",
            left: "50%",
            transform: "translateX(-50%)",
            width: 0,
            height: 0,
            borderLeft: "4px solid transparent",
            borderRight: "4px solid transparent",
            borderTop: "5px solid #ffffff",
          }}
        />
      </div>
    </div>
  );
}
