import React from "react";
import ChatPanel from "../components/ChatPanel";

const CAPABILITY_CARDS = [
  {
    title: "Why this workspace exists",
    body: "Agent Chat is for live triage. You ask naturally, the backend picks the right analysis path, and you get one answer instead of clicking through tools."
  },
  {
    title: "Best use cases",
    body: "Stuck pipelines, failure spikes, market regressions, retry patterns, state-level summaries, and operational report generation."
  },
  {
    title: "Response style",
    body: "Shorter answers, direct findings first, and data-backed follow-up only when it helps the decision."
  }
];

const STARTER_GUIDES = [
  "Which pipelines are stuck in CA right now?",
  "Summarize failed roster operations in NY.",
  "Generate an operational report for CA.",
  "What changed since the last CA investigation?"
];

export default function AgentChatPage({ queuedQuery, onQueuedQueryConsumed, onOpenInvestigations }) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_360px]">
      <div className="space-y-6">
        <section className="panel-shell overflow-hidden border-cyan-400/10 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.18),transparent_38%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(8,15,30,0.92))] p-6">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-2xl">
              <div className="status-pill border-cyan-400/20 bg-cyan-400/10 text-cyan-200">Live AI Workspace</div>
              <h3 className="mt-4 font-display text-3xl font-semibold tracking-tight text-white">Ask one question, get one operational answer</h3>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                This is the live copilot. Use it when you want interpretation, routing, and next-step guidance without opening individual analytics panels.
              </p>
            </div>
            <button
              type="button"
              onClick={onOpenInvestigations}
              className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-slate-200 transition hover:border-cyan-400/30 hover:bg-cyan-400/10 hover:text-white"
            >
              Open saved investigations
            </button>
          </div>
        </section>

        <ChatPanel queuedQuery={queuedQuery} onQueuedQueryConsumed={onQueuedQueryConsumed} />
      </div>

      <aside className="space-y-6">
        {CAPABILITY_CARDS.map((card) => (
          <section key={card.title} className="panel-shell p-5">
            <div className="section-caption text-cyan-300">Agent note</div>
            <h4 className="mt-3 font-display text-xl font-semibold text-white">{card.title}</h4>
            <p className="mt-3 text-sm leading-7 text-slate-300">{card.body}</p>
          </section>
        ))}

        <section className="panel-shell p-5">
          <div className="section-caption text-emerald-300">Good prompts</div>
          <div className="mt-4 space-y-3">
            {STARTER_GUIDES.map((prompt) => (
              <div key={prompt} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-slate-200">
                {prompt}
              </div>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}
