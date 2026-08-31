import React, { useState, useEffect, useRef } from "react";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 8px 8px 0 6px rgba(0,0,0,0.4)",
  imageRendering: "pixelated",
};

interface Message {
  speaker: string;
  text: string;
  lang: string;
  time: string;
}

interface Props {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isProcessing: boolean;
}

export default function LiveConversationPanel({ messages, onSendMessage, isProcessing }: Props) {
  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (inputText.trim() && !isProcessing) {
      onSendMessage(inputText);
      setInputText("");
    }
  };

  return (
    <div style={pixelPanel} className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        className="shrink-0 px-4 py-3 flex items-center gap-3"
        style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
      >
        <span
          className="w-2.5 h-2.5 inline-block animate-chat-blink"
          style={{ background: "#bf616a", boxShadow: "0 0 5px #bf616a" }}
        />
        <span className="text-[9px] font-bold tracking-widest text-[#f28a1f]" style={{ fontFamily: PIXEL }}>
          LIVE CONVERSATION
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
            <span className="text-3xl opacity-30">💬</span>
            <span className="text-[18px] text-[#4e5a70]" style={{ fontFamily: TERM }}>
              Conversation has not started
            </span>
            <span className="text-[7px] text-[#3a4356] tracking-widest" style={{ fontFamily: PIXEL }}>
              TYPE BELOW TO BEGIN
            </span>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isUser = msg.speaker === "Kaushal";
            return (
              <div key={idx} className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
                {/* Meta */}
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="text-[7px] font-bold tracking-widest"
                    style={{ fontFamily: PIXEL, color: isUser ? "#f28a1f" : "#88c0d0" }}
                  >
                    {msg.speaker.toUpperCase()}
                  </span>
                  <span
                    className="px-1.5 py-0.5 text-[8px]"
                    style={{ fontFamily: TERM, background: "#232a38", color: "#7f8ca5" }}
                  >
                    {msg.lang.toUpperCase()}
                  </span>
                  <span className="text-[14px] text-[#4e5a70]" style={{ fontFamily: TERM }}>
                    {msg.time}
                  </span>
                </div>
                {/* Bubble */}
                <div
                  className="px-3 py-2 max-w-[82%] text-[15px] leading-snug"
                  style={{
                    fontFamily: TERM,
                    background: isUser ? "#f28a1f" : "#1b2230",
                    color: isUser ? "#241303" : "#c8d2e4",
                    boxShadow: isUser
                      ? "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.25), 3px 3px 0 2px rgba(0,0,0,0.3)"
                      : "0 0 0 2px #3a4356, 3px 3px 0 2px rgba(0,0,0,0.3)",
                  }}
                >
                  {msg.text}
                </div>
              </div>
            );
          })
        )}
        {isProcessing && (
          <div className="flex items-center gap-2">
            <span className="text-[18px] animate-spin inline-block" style={{ fontFamily: TERM }}>↻</span>
            <span className="text-[15px] text-[#ebcb8b]" style={{ fontFamily: TERM }}>
              AI is processing...
            </span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input bar */}
      <div
        className="shrink-0 px-3 py-3 flex items-center gap-2"
        style={{ borderTop: "3px solid #3a4356", background: "#0b0e15" }}
      >
        {/* Mic */}
        <button
          onClick={() => setIsListening(!isListening)}
          className="w-9 h-9 flex items-center justify-center shrink-0 text-base transition-transform active:translate-y-0.5"
          style={{
            background: isListening ? "#bf616a" : "#232a38",
            boxShadow: isListening
              ? "0 0 0 2px #bf616a, 0 0 8px #bf616a55"
              : "0 0 0 2px #3a4356",
          }}
          title="Toggle voice"
        >
          🎙️
        </button>

        {/* Text input */}
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={isListening ? "Listening..." : "Ask about properties..."}
          disabled={isProcessing}
          className="flex-1 px-3 py-2 text-[14px] text-[#eceff4] placeholder-[#4e5a70] focus:outline-none"
          style={{
            fontFamily: TERM,
            background: "#1b2230",
            border: "2px solid #3a4356",
          }}
        />

        {/* Send */}
        <button
          onClick={handleSend}
          disabled={isProcessing || !inputText.trim()}
          className="px-4 py-2 text-[8px] tracking-widest transition-transform active:translate-y-0.5 disabled:opacity-40"
          style={{
            fontFamily: PIXEL,
            background: "#f28a1f",
            color: "#241303",
            boxShadow:
              "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.25), 0 3px 0 2px #12161f",
          }}
        >
          SEND ▶
        </button>
      </div>

      <style>{`
        @keyframes chat-blink { 0%,60%{opacity:1} 61%,100%{opacity:0.2} }
        .animate-chat-blink { animation: chat-blink 1.2s steps(1) infinite; }
      `}</style>
    </div>
  );
}
