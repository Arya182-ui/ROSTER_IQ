import React, { useMemo, useState } from "react";

function healthTone(level) {
  if (level === "RED") {
    return "text-rose-200 bg-rose-500/15";
  }
  if (level === "YELLOW") {
    return "text-amber-200 bg-amber-400/15";
  }
  return "text-emerald-200 bg-emerald-400/15";
}

export default function StuckROTable({ rows = [], anomalies = [], focusState = "ALL" }) {
  const [sortDirection, setSortDirection] = useState("desc");

  const sortedRows = useMemo(() => {
    const anomalyMap = anomalies.reduce((acc, item) => {
      acc[item.RO_ID] = item;
      return acc;
    }, {});

    const scopedRows = rows
      .filter((row) => !focusState || focusState === "ALL" || row.CNT_STATE === focusState)
      .map((row) => {
        const anomaly = anomalyMap[row.RO_ID];
        const duration = anomaly?.duration_value || 0;
        const health = anomaly?.anomaly_ratio >= 3 ? "RED" : anomaly ? "YELLOW" : "GREEN";
        return {
          ...row,
          duration,
          health
        };
      });

    return scopedRows.sort((a, b) => {
      const modifier = sortDirection === "desc" ? -1 : 1;
      return modifier * ((a.duration || 0) - (b.duration || 0));
    });
  }, [rows, anomalies, focusState, sortDirection]);

  return (
    <section className="panel-shell p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h3 className="panel-title">Stuck RO Tracker</h3>
          <p className="panel-subtitle mt-2">Monitor stuck roster operations and sort them by anomalous duration.</p>
        </div>
        <button
          type="button"
          onClick={() => setSortDirection((current) => (current === "desc" ? "asc" : "desc"))}
          className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-300 transition hover:text-white"
        >
          Duration {sortDirection === "desc" ? "?" : "?"}
        </button>
      </div>

      <div className="overflow-x-auto hidden md:block">
        <table className="min-w-full table-auto border-separate border-spacing-y-2 text-left text-sm text-slate-300">
          <thead>
            <tr className="text-xs uppercase tracking-[0.18em] text-slate-500">
              <th className="px-4 py-2">RO_ID</th>
              <th className="px-4 py-2">ORG_NM</th>
              <th className="px-4 py-2">State</th>
              <th className="px-4 py-2">Latest Stage</th>
              <th className="px-4 py-2">Duration</th>
              <th className="px-4 py-2">Health</th>
            </tr>
          </thead>
          <tbody>
            {sortedRows.length === 0 ? (
              <tr>
                <td colSpan={6} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-6 text-center text-slate-400">
                  No stuck roster operations for this scope.
                </td>
              </tr>
            ) : (
              sortedRows.map((row) => (
                <tr key={row.RO_ID} className="rounded-2xl border border-white/10 bg-white/[0.03]">
                  <td className="rounded-l-2xl px-4 py-4 font-medium text-white">{row.RO_ID}</td>
                  <td className="px-4 py-4">{row.ORG_NM}</td>
                  <td className="px-4 py-4">{row.CNT_STATE}</td>
                  <td className="px-4 py-4">{row.LATEST_STAGE_NM}</td>
                  <td className="px-4 py-4">{row.duration ? row.duration.toFixed(1) + "h" : "-"}</td>
                  <td className="rounded-r-2xl px-4 py-4">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${healthTone(row.health)}`}>
                      {row.health}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="md:hidden space-y-3">
        {sortedRows.length === 0 ? (
           <div className="text-center py-8 text-slate-500 text-sm">No stuck roster operations.</div>
        ) : sortedRows.map((row) => (
           <div key={row.RO_ID} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm">
              <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
                 <div className="font-semibold text-white truncate max-w-[60%]">{row.RO_ID}</div>
                 <div className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wide ${healthTone(row.health)}`}>
                   {row.health}
                 </div>
              </div>
              <div className="grid grid-cols-2 gap-y-3 gap-x-2">
                 <div>
                   <div className="text-[10px] uppercase text-slate-500 tracking-wider mb-1">Org</div>
                   <div className="text-slate-300 truncate">{row.ORG_NM}</div>
                 </div>
                 <div>
                   <div className="text-[10px] uppercase text-slate-500 tracking-wider mb-1">Stage</div>
                   <div className="text-slate-300 truncate">{row.LATEST_STAGE_NM}</div>
                 </div>
                 <div>
                   <div className="text-[10px] uppercase text-slate-500 tracking-wider mb-1">State</div>
                   <div className="text-slate-300">{row.CNT_STATE}</div>
                 </div>
                 <div>
                   <div className="text-[10px] uppercase text-slate-500 tracking-wider mb-1">Duration</div>
                   <div className="text-slate-300 font-mono">{row.duration ? row.duration.toFixed(1) + "h" : "-"}</div>
                 </div>
              </div>
           </div>
        ))}
      </div>
    </section>
  );
}
