import React from "react";

function confidenceTone(score) {
  if (score >= 0.8) {
    return "text-emerald-300 border-emerald-400/20 bg-emerald-400/10";
  }
  if (score >= 0.55) {
    return "text-amber-200 border-amber-400/20 bg-amber-400/10";
  }
  return "text-rose-200 border-rose-400/20 bg-rose-400/10";
}

export default function RootCausePanel({ stateCode, data = {} }) {
  const confidenceScore = data.confidence_score ?? 0;

  return (
    <section className="panel-shell p-6">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="status-pill border-sky-400/20 bg-sky-400/10 text-sky-200">Root Cause Analysis</div>
          <h3 className="mt-4 font-display text-2xl font-semibold text-white">{data.market || stateCode} market investigation</h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            Review market decline signals, the primary organization driving failures, and the stage most likely to explain the regression.
          </p>
        </div>
        <div className={`rounded-2xl border px-4 py-3 text-right ${confidenceTone(confidenceScore)}`}>
          <div className="text-xs uppercase tracking-[0.18em]">Confidence</div>
          <div className="mt-2 text-2xl font-semibold">{Math.round(confidenceScore * 100)}%</div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Market</div>
          <div className="mt-2 text-lg font-semibold text-white">{data.market || stateCode}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Success Rate Drop</div>
          <div className="mt-2 text-lg font-semibold text-white">{data.success_rate_drop ?? 0}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Primary Organization</div>
          <div className="mt-2 text-lg font-semibold text-white">{data.primary_org || "Unknown"}</div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Likely Stage Issue</div>
          <div className="mt-2 text-lg font-semibold text-white">{data.likely_stage_issue || "Unknown"}</div>
        </div>
      </div>

      <div className="mt-5 rounded-3xl border border-white/10 bg-slate-950/50 p-5">
        <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Investigation narrative</div>
        <p className="mt-3 text-sm leading-7 text-slate-200">{data.explanation || "No explanation available."}</p>
      </div>
    </section>
  );
}
