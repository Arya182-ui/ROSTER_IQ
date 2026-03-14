import React, { useEffect, useState } from "react";
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

export default function InvestigationHistory({ onRerun }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        const response = await getInvestigationHistory();
        setItems(response.items || []);
      } catch (requestError) {
        setError(requestError.message || "Failed to load investigation history.");
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, []);

  return (
    <section className="panel-shell p-6">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="panel-title">Investigation History</h3>
          <p className="panel-subtitle mt-2">Recent episodic memory entries saved from previous agent investigations.</p>
        </div>
        {loading ? <div className="status-pill border-amber-400/20 bg-amber-400/10 text-amber-200">Loading</div> : null}
      </div>

      {error ? <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <div className="space-y-3">
        {!loading && items.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-6 text-sm text-slate-400">
            No episodic investigation history is available yet.
          </div>
        ) : null}

        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onRerun?.(item.query)}
            className="w-full rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4 text-left transition hover:border-teal-400/30 hover:bg-white/[0.05]"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-medium text-white">{item.query}</div>
                <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">{formatTimestamp(item.created_at)}</div>
              </div>
              <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                {item.tool_used || item.query_type || "history"}
              </span>
            </div>
            <div className="mt-3 text-sm leading-6 text-slate-300">
              {item.result_summary?.context_summary || item.result_summary?.dominant_stage || item.result_summary?.text || "Click to rerun this investigation."}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
