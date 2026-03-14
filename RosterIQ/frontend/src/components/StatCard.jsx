import React from "react";

export default function StatCard({ label, value, subValue, trend, tone = "text-white", icon }) {
  const isPositive = trend === "up";
  const isNegative = trend === "down";

  return (
    <div className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] px-6 py-5 backdrop-blur-sm transition hover:border-white/20 hover:bg-white/[0.05]">
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br from-white/5 to-transparent blur-2xl transition group-hover:from-white/10" />
      
      <div className="relative flex justify-between items-start">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</div>
          <div className={`mt-3 font-display text-3xl font-bold tracking-tight ${tone}`}>
            {value}
          </div>
        </div>
        {icon && (
          <div className={`flex h-10 w-10 items-center justify-center rounded-2xl border border-white/5 bg-white/5 ${tone}`}>
            {icon}
          </div>
        )}
      </div>

      {subValue && (
        <div className="mt-4 flex items-center gap-2 text-sm font-medium">
          {isPositive && (
            <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
              Trending up
            </span>
          )}
          {isNegative && (
            <span className="flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-xs text-rose-400">
              Needs attention
            </span>
          )}
          <span className="text-slate-400">{subValue}</span>
        </div>
      )}
    </div>
  );
}
