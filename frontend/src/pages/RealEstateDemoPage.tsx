import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useRealEstateDemo } from "../hooks/useRealEstateDemo";

import LiveConversationPanel from "../components/real-estate/LiveConversationPanel";
import ActiveEmployeePanel from "../components/real-estate/ActiveEmployeePanel";
import ActivityTimelinePanel from "../components/real-estate/ActivityTimelinePanel";
import PropertyAnalysisPanel from "../components/real-estate/PropertyAnalysisPanel";
import CustomerProfilePanel from "../components/real-estate/CustomerProfilePanel";
import UploadDataModal from "../components/real-estate/UploadDataModal";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

export default function RealEstateDemoPage() {
  const { token } = useAuth();
  const [showUploadModal, setShowUploadModal] = useState(false);

  const {
    messages,
    timelineEvents,
    activeEmployee,
    currentStage,
    properties,
    customer,
    isProcessing,
    sendMessage,
  } = useRealEstateDemo();

  return (
    <main
      className="relative h-screen overflow-hidden select-none"
      style={{
        background: "linear-gradient(180deg, #4da3e8 0%, #58aeef 45%, #3f8fd6 100%)",
      }}
    >
      {/* ── Blueprint grid ── */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.10) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      {/* ── Scanlines ── */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-[0.07]"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
          backgroundSize: "100% 3px",
        }}
      />
      {/* ── City skyline ── */}
      <div
        aria-hidden="true"
        className="absolute bottom-0 left-0 right-0 h-[28vh] pointer-events-none opacity-30"
        style={{
          background: "#1d4e7e",
          clipPath:
            "polygon(0 62%, 4% 62%, 4% 38%, 9% 38%, 9% 55%, 14% 55%, 14% 22%, 16% 22%, 16% 14%, 18% 14%, 18% 22%, 20% 22%, 20% 58%, 26% 58%, 26% 34%, 31% 34%, 31% 64%, 37% 64%, 37% 44%, 42% 44%, 42% 70%, 50% 70%, 50% 30%, 54% 30%, 54% 18%, 56% 18%, 56% 30%, 60% 30%, 60% 60%, 66% 60%, 66% 40%, 72% 40%, 72% 66%, 78% 66%, 78% 26%, 82% 26%, 82% 50%, 88% 50%, 88% 36%, 93% 36%, 93% 58%, 100% 58%, 100% 100%, 0 100%)",
        }}
      />

      {/* ── Content ── */}
      <div className="relative z-10 h-full flex flex-col p-3 gap-3">

        {/* ─── Header bar ─── */}
        <div
          className="shrink-0 flex items-center justify-between px-5 py-3"
          style={{
            background: "#0b0e15",
            boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #0b0e15",
          }}
        >
          <div className="flex items-center gap-4">
            <span className="text-2xl">🏢</span>
            <div>
              <div
                className="text-[10px] md:text-[11px] font-bold tracking-wider text-[#f28a1f] flex items-center gap-2"
                style={{ fontFamily: PIXEL }}
              >
                <span className="text-[#c8d2e4]">{"─▶ "}</span>
                MYCEL REAL ESTATE
              </div>
              <div className="text-[17px] text-[#7f8ca5] mt-0.5" style={{ fontFamily: TERM }}>
                AI-powered property intelligence · live routing
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live pulse */}
            <div className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 inline-block animate-re-pulse"
                style={{ background: "#bf616a", boxShadow: "0 0 6px #bf616a" }}
              />
              <span className="text-[7px] tracking-widest text-[#bf616a]" style={{ fontFamily: PIXEL }}>
                LIVE
              </span>
            </div>

            {/* Upload button */}
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-[8px] tracking-widest transition-transform active:translate-y-0.5"
              style={{
                fontFamily: PIXEL,
                background: "#f28a1f",
                color: "#241303",
                boxShadow:
                  "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.3), inset 2px 2px 0 rgba(255,255,255,0.3), 0 3px 0 2px #12161f",
              }}
            >
              📂 UPLOAD DATA
            </button>
          </div>
        </div>

        {/* ─── Main 3-column grid ─── */}
        <div className="flex-1 min-h-0 grid grid-cols-12 gap-3">

          {/* LEFT: Conversation + Timeline */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-3 min-h-0">
            <div className="flex-1 min-h-0">
              <LiveConversationPanel
                messages={messages}
                onSendMessage={sendMessage}
                isProcessing={isProcessing}
              />
            </div>
            <div className="h-[30%] min-h-[160px]">
              <ActivityTimelinePanel events={timelineEvents} />
            </div>
          </div>

          {/* MIDDLE: Active Work + Properties */}
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-3 min-h-0">
            <div className="h-[38%] min-h-[200px]">
              <ActiveEmployeePanel activeEmployee={activeEmployee} currentStage={currentStage} />
            </div>
            <div className="flex-1 min-h-0">
              <PropertyAnalysisPanel properties={properties} />
            </div>
          </div>

          {/* RIGHT: Customer Profile */}
          <div className="col-span-12 lg:col-span-3 min-h-0">
            <CustomerProfilePanel customer={customer} />
          </div>
        </div>

        {/* ─── Footer ─── */}
        <div
          className="shrink-0 px-5 py-2 flex items-center justify-between"
          style={{
            background: "#0b0e15",
            boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #0b0e15",
          }}
        >
          <span className="text-[7px] tracking-widest text-[#4e5a70]" style={{ fontFamily: PIXEL }}>
            MYCEL · REAL ESTATE MODULE · v1.0
          </span>
          <span className="text-[16px] text-[#4e5a70] flex items-center gap-2" style={{ fontFamily: TERM }}>
            <span className="w-2 h-2 inline-block" style={{ background: "#f28a1f", boxShadow: "0 0 4px #f28a1f" }} />
            ALL SYSTEMS OPERATIONAL
          </span>
        </div>
      </div>

      {/* Upload modal */}
      {showUploadModal && (
        <UploadDataModal token={token} onClose={() => setShowUploadModal(false)} />
      )}

      <style>{`
        @keyframes re-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.25; }
        }
        .animate-re-pulse { animation: re-pulse 1.4s steps(1) infinite; }
      `}</style>
    </main>
  );
}
