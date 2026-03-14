import React from "react";
import InvestigationHistory from "../components/InvestigationHistory";

const DIFFERENCE_POINTS = [
  "Agent Chat is for a live question and a fresh answer.",
  "Investigations stores what was already asked, what route was used, and what should be rerun.",
  "Use this page to reopen prior work instead of asking the same question from scratch."
];

const MEMORY_POINTS = [
  "Original user query",
  "Agent route or investigation type",
  "Compact result summary for later comparison"
];

export default function InvestigationsPage({ onOpenChat, onRerun }) {
  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_360px]">
        <div className="panel-shell overflow-hidden border-amber-400/10 bg-[radial-gradient(circle_at_top_right,rgba(251,191,36,0.16),transparent_36%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(9,14,27,0.92))] p-6">
          <div className="status-pill border-amber-400/20 bg-amber-400/10 text-amber-200">Saved workflow memory</div>
          <h3 className="mt-4 font-display text-3xl font-semibold tracking-tight text-white">Reopen previous investigations instead of repeating them</h3>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
            This page is the history layer. It exists to track what the agent already analyzed, what changed since then, and which query should be rerun in chat.
          </p>
          <div className="mt-5 space-y-3 text-sm text-slate-200">
            {DIFFERENCE_POINTS.map((point) => (
              <div key={point} className="flex items-start gap-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-amber-300" />
                <span>{point}</span>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={onOpenChat}
            className="mt-6 rounded-2xl bg-gradient-to-r from-amber-300 to-orange-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110"
          >
            Go to live chat
          </button>
        </div>

        <section className="panel-shell p-5">
          <div className="section-caption text-amber-200">What gets stored</div>
          <div className="mt-4 space-y-3">
            {MEMORY_POINTS.map((point) => (
              <div key={point} className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-200">
                {point}
              </div>
            ))}
          </div>
        </section>
      </section>

      <InvestigationHistory variant="full" onRerun={onRerun} limit={20} />
    </div>
  );
}
