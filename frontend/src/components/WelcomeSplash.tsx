import React, { useState, useEffect, useCallback } from "react";

interface Props {
  onDismiss: () => void;
}

export default function WelcomeSplash({ onDismiss }: Props) {
  const [phase, setPhase] = useState<"typing" | "hold" | "fadeout" | "gone">("typing");
  const [displayedText, setDisplayedText] = useState("");

  const TAGLINE = "An Autonomous AI Company";
  const TYPING_SPEED = 70; // ms per character
  const HOLD_DURATION = 2000; // ms to hold after typing
  const FADE_DURATION = 600; // ms for fade out

  // Check if already seen this session
  useEffect(() => {
    if (sessionStorage.getItem("mycel_splash_seen")) {
      setPhase("gone");
      onDismiss();
    }
  }, [onDismiss]);

  // Typing animation
  useEffect(() => {
    if (phase !== "typing") return;

    if (displayedText.length < TAGLINE.length) {
      const timer = setTimeout(() => {
        setDisplayedText(TAGLINE.slice(0, displayedText.length + 1));
      }, TYPING_SPEED);
      return () => clearTimeout(timer);
    } else {
      // Done typing → hold
      setPhase("hold");
    }
  }, [phase, displayedText]);

  // Hold then fade
  useEffect(() => {
    if (phase !== "hold") return;
    const timer = setTimeout(() => setPhase("fadeout"), HOLD_DURATION);
    return () => clearTimeout(timer);
  }, [phase]);

  // Fade out then gone
  useEffect(() => {
    if (phase !== "fadeout") return;
    const timer = setTimeout(() => {
      setPhase("gone");
      sessionStorage.setItem("mycel_splash_seen", "true");
      onDismiss();
    }, FADE_DURATION);
    return () => clearTimeout(timer);
  }, [phase, onDismiss]);

  // Click/key to skip
  const handleSkip = useCallback(() => {
    if (phase === "gone") return;
    setPhase("gone");
    sessionStorage.setItem("mycel_splash_seen", "true");
    onDismiss();
  }, [phase, onDismiss]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.key === "Enter" || e.key === " ") handleSkip();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSkip]);

  if (phase === "gone") return null;

  return (
    <div
      onClick={handleSkip}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "#1a1d24",
        cursor: "pointer",
        opacity: phase === "fadeout" ? 0 : 1,
        transition: `opacity ${FADE_DURATION}ms ease-out`,
        fontFamily: "'Courier New', monospace",
        imageRendering: "pixelated" as any,
      }}
    >
      {/* Pixel border frame */}
      <div
        style={{
          border: "4px solid #4c566a",
          borderRadius: 4,
          padding: "48px 64px",
          background: "rgba(46, 52, 64, 0.6)",
          boxShadow: "0 0 60px rgba(94, 129, 172, 0.15), 8px 8px 0 rgba(0,0,0,0.4)",
          textAlign: "center",
          maxWidth: 520,
        }}
      >
        {/* Logo */}
        <div
          style={{
            fontSize: 48,
            marginBottom: 8,
            animation: "pulse 2s ease-in-out infinite",
          }}
        >
          🏢
        </div>

        {/* Title */}
        <h1
          style={{
            fontSize: 32,
            fontWeight: "bold",
            color: "#eceff4",
            letterSpacing: "6px",
            margin: "0 0 16px 0",
            textShadow: "0 0 20px rgba(136,192,208,0.3)",
          }}
        >
          MYCEL
        </h1>

        {/* Typing tagline */}
        <div
          style={{
            fontSize: 14,
            color: "#88c0d0",
            letterSpacing: "2px",
            minHeight: 20,
          }}
        >
          {displayedText}
          <span
            style={{
              opacity: phase === "typing" ? 1 : 0,
              animation: "blink 0.6s infinite",
              color: "#5e81ac",
            }}
          >
            ▌
          </span>
        </div>

        {/* Scanline effect */}
        <div
          style={{
            fontSize: 9,
            color: "#6b7994",
            marginTop: 32,
            letterSpacing: "1px",
          }}
        >
          PRESS ANY KEY TO ENTER
        </div>
      </div>

      {/* Inline keyframes */}
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
}
