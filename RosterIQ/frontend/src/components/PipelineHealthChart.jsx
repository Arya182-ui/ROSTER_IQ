import React, { useMemo } from "react";

const STAGE_ORDER = [
  "INGESTION",
  "PRE_PROCESSING",
  "MAPPING_APPROVAL",
  "ISF_GENERATION",
  "DART_GENERATION",
  "DART_REVIEW",
  "DART_UI_VALIDATION",
  "SPS_LOAD",
  "RESOLVED"
];

function stageFromRow(row) {
  return row.LATEST_STAGE_NM || row.stage || "UNKNOWN";
}

function cellTone(value, maxValue) {
  if (!value) {
    return "bg-slate-900/40 text-slate-600 border-transparent";
  }
  const intensity = maxValue > 0 ? value / maxValue : 0;
  if (intensity >= 0.75) {
    return "bg-rose-500 text-white border-rose-400/50 shadow-[0_0_15px_-3px_rgba(244,63,94,0.4)]";
  }
  if (intensity >= 0.35) {
    return "bg-amber-500/80 text-white border-amber-400/50 shadow-[0_0_15px_-3px_rgba(245,158,11,0.3)]";
  }
  return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
}

export default function PipelineHealthChart({ stageHealth = [], failedRos = [], focusState = "ALL" }) {
  const matrix = useMemo(() => {
    const scopedFailures = failedRos.filter((row) => !focusState || focusState === "ALL" || row.CNT_STATE === focusState);
    const topOrgs = Array.from(
      scopedFailures.reduce((acc, row) => {
        const key = row.ORG_NM || "Unknown";
        acc.set(key, (acc.get(key) || 0) + 1);
        return acc;
      }, new Map())
    )
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([org]) => org);

    const stages = STAGE_ORDER.filter((stage) => stageHealth.some((item) => item.stage === stage));
    const stageList = stages.length ? stages : STAGE_ORDER.slice(0, 7);
    const heatmap = stageList.map((stage) => {
      const row = { stage };
      topOrgs.forEach((org) => {
        row[org] = scopedFailures.filter((item) => (item.ORG_NM || "Unknown") === org && stageFromRow(item) === stage).length;
      });
      return row;
    });

    const maxValue = heatmap.reduce((max, row) => {
      const rowMax = topOrgs.reduce((valueMax, org) => Math.max(valueMax, row[org] || 0), 0);
      return Math.max(max, rowMax);
    }, 0);

    return { topOrgs, heatmap, maxValue };
  }, [failedRos, focusState, stageHealth]);

  return (
    <section className="panel-shell p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 p-32 bg-blue-500/5 blur-[80px] rounded-full pointer-events-none" />
      
      <div className="relative mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="panel-title">Pipeline Health Matrix</h3>
          <p className="panel-subtitle mt-1">Cross-reference failure stages with top organizations.</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium text-slate-400 bg-white/5 rounded-full px-3 py-1">
          <span>Less</span>
          <div className="flex gap-0.5">
             <div className="w-2 h-2 rounded-sm bg-emerald-500/20" />
             <div className="w-2 h-2 rounded-sm bg-amber-500/50" />
             <div className="w-2 h-2 rounded-sm bg-rose-500" />
          </div>
          <span>More Failures</span>
        </div>
      </div>

      {/* Desktop Grid View */}
      <div className="hidden md:block overflow-x-auto pb-2">
        <div className="min-w-[700px]">
          <div className="grid grid-cols-[160px_repeat(6,minmax(100px,1fr))] gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            <div className="px-2">Stage</div>
            {matrix.topOrgs.map((org) => (
              <div key={org} className="truncate px-2 text-center" title={org}>{org}</div>
            ))}
          </div>
          <div className="space-y-1.5">
            {matrix.heatmap.map((row) => (
              <div key={row.stage} className="grid grid-cols-[160px_repeat(6,minmax(100px,1fr))] gap-2 group hover:bg-white/[0.02] rounded-xl transition-colors duration-150">
                <div className="flex items-center rounded-lg px-3 py-2 text-xs font-medium text-slate-300 group-hover:text-white transition-colors">
                  {row.stage}
                </div>
                {matrix.topOrgs.map((org) => (
                  <div 
                    key={`${row.stage}-${org}`} 
                    className={`
                      relative flex items-center justify-center rounded-lg border px-2 py-2 text-sm font-bold transition-all duration-200
                      ${cellTone(row[org], matrix.maxValue)}
                      ${row[org] > 0 ? "hover:scale-105 hover:z-10 cursor-default" : ""}
                    `}
                    title={`${row[org]} failures in ${org}`}
                  >
                    {row[org] > 0 ? row[org] : <span className="w-1 h-1 rounded-full bg-slate-700" />}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mobile Stack View */}
      <div className="md:hidden space-y-3">
        {matrix.heatmap.map((row) => {
          const activeOrgs = matrix.topOrgs.filter(org => row[org] > 0);
          if (activeOrgs.length === 0) return null;
          
          return (
            <div key={row.stage} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-center">
              <div className="text-sm font-semibold text-slate-300 mb-3 pb-2 border-b border-white/5">{row.stage}</div>
              <div className="grid grid-cols-2 gap-3">
                {activeOrgs.map(org => {
                   const tone = cellTone(row[org], matrix.maxValue);
                   return (
                     <div key={org} className={`rounded-xl px-3 py-2 border ${tone}`}> 
                       <div className="text-[10px] uppercase opacity-80 mb-1 truncate">{org}</div>
                       <div className="text-lg font-bold leading-none">{row[org]}</div>
                     </div>
                   );
                })}
              </div>
            </div>
          );
        })}
        {!matrix.heatmap.some(row => matrix.topOrgs.some(org => row[org] > 0)) && (
           <div className="text-center py-8 text-slate-500 text-sm">No failures detected in top organizations.</div>
        )}
      </div>
    </section>
  );
}
