import React from "react";
import ChatPanel from "../components/ChatPanel";
import InvestigationHistory from "../components/InvestigationHistory";

export default function InvestigationsPage({ mode, onRerun, queuedQuery, onQueuedQueryConsumed }) {
  const chatPriority = mode === "chat";

  return (
    <div className={`grid gap-6 ${chatPriority ? "xl:grid-cols-[1.4fr_0.9fr]" : "xl:grid-cols-[0.95fr_1.35fr]"}`}>
      <div className={chatPriority ? "order-1" : "order-2 xl:order-1"}>
        <ChatPanel queuedQuery={queuedQuery} onQueuedQueryConsumed={onQueuedQueryConsumed} />
      </div>
      <div className={chatPriority ? "order-2" : "order-1 xl:order-2"}>
        <InvestigationHistory onRerun={onRerun} />
      </div>
    </div>
  );
}
