import React, { useEffect, useMemo, useState } from "react";
import { getInvestigationHistory } from "../api/api";

function formatTimestamp(value) {
  if (!value) {
    return "Unknown time";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

function summarizeResult(item) {
  const summary = item.result_summary || {};

  if (summary.context_summary) {
    return summary.context_summary;
  }

  if (summary.state && (summary.stuck_ros != null || summary.failed_ros != null)) {
    return `${summary.state}: ${summary.stuck_ros || 0} stuck and ${summary.failed_ros || 0} failed in the saved snapshot.`;
  }

  if (summary.market && summary.likely_stage_issue) {
    return `${summary.market}: likely issue concentrated in ${summary.likely_stage_issue}.`;
  }

  if (summary.dominant_stage) {
    return `Dominant stage captured in memory: ${summary.dominant_stage}.`;
  }

  if (summary.text) {
    return summary.text;
  }

  return "Saved operational snapshot ready to rerun in chat.";
}

function buildMetrics(items) {
  const distinctTools = new Set(items.map((item) => item.tool_used || item.query_type).filter(Boolean));
  const states = new Set(items.map((item) => item.state || item.result_summary?.state).filter(Boolean));

  return [
    { label: "Saved runs", value: items.length },
    { label: "Tool types", value: distinctTools.size },
    { label: "States covered", value: states.size }
  ];
}

export default function InvestigationHistory({ onRerun, variant = "panel", refreshKey, limit }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const requestLimit = limit || (variant === "full" ? 20 : 10);

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        setError("");
        const response = await getInvestigationHistory(requestLimit);
        setItems(response.items || []);
      } catch (requestError) {
        setError(requestError.message || "Failed to load investigation history.");
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, [refreshKey, requestLimit]);

  const metrics = useMemo(() => buildMetrics(items), [items]);
  const isFull = variant === "full";

  return (
    <section className="panel-shell p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className={`section-caption ${isFull ? "text-amber-200" : "text-slate-400"}`}>History timeline</div>
          <h3 className="mt-2 panel-title text-2xl">Investigation History</h3>
          <p className="panel-subtitle mt-2 max-w-3xl">
            Recent episodic memory entries saved from earlier agent investigations. Reopen any of them in chat for a fresh answer.
          </p>
        </div>
        {loading ? <div className="status-pill border-amber-400/20 bg-amber-400/10 text-amber-200">Loading</div> : null}
      </div>

      {isFull ? (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-3xl border border-white/10 bg-white/[0.04] px-5 py-4">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{metric.label}</div>
              <div className="mt-3 font-display text-3xl font-semibold text-white">{metric.value}</div>
            </div>
          ))}
        </div>
      ) : null}

      {error ? <div className="mt-5 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <div className={`mt-6 ${isFull ? "grid gap-4 xl:grid-cols-2" : "space-y-3"}`}>
        {!loading && items.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-8 text-sm leading-7 text-slate-400">
            No saved investigations are available yet. Run a few questions in Agent Chat and this page will start filling with reusable history.
          </div>
        ) : null}

        {items.map((item) => {
          const summaryText = summarizeResult(item);
          const stateTag = item.state || item.result_summary?.state || item.result_summary?.market;

          return (
            <article
              key={item.id}
              className="rounded-3xl border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] px-5 py-5 transition hover:border-cyan-400/20 hover:bg-white/[0.05]"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <h4 className="font-medium leading-7 text-white">{item.query}</h4>
                  <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">{formatTimestamp(item.created_at)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-300">
                    {(item.tool_used || item.query_type || "history").replaceAll("_", " ")}
                  </span>
                  {stateTag ? (
                    <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-amber-100">
                      {stateTag}
                    </span>
                  ) : null}
                </div>
              </div>

              <p className="mt-4 text-sm leading-7 text-slate-300">{summaryText}</p>

              {onRerun ? (
                <button
                  type="button"
                  onClick={() => onRerun(item.query)}
                  className="mt-5 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100 transition hover:border-cyan-300/30 hover:bg-cyan-400/15 hover:text-white"
                >
                  Rerun in chat
                </button>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
