import React from "react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const value = payload[0].value;
    return (
      <div className="rounded-xl border border-teal-500/30 bg-slate-900/90 px-3 py-2 text-sm shadow-[0_0_20px_rgba(45,212,191,0.15)] backdrop-blur-md">
        <div className="mb-1 text-xs text-slate-400">{label}</div>
        <div className="font-display text-lg font-bold text-teal-400">{value}%</div>
        <div className="text-[10px] text-teal-200/50">Market Success Rate</div>
      </div>
    );
  }
  return null;
}

export default function MarketTrendChart({ data = [] }) {
  const currentRate = data.length > 0 ? data[data.length - 1].success_rate : 0;
  const startRate = data.length > 0 ? data[0].success_rate : 0;
  const growth = currentRate - startRate;

  return (
    <section className="panel-shell p-6 bg-slate-950/40">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h3 className="panel-title">Market Health Trend</h3>
          <p className="panel-subtitle mt-1">Weighted success rate over recent operation cycles.</p>
        </div>
        <div className={`text-right ${growth >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
          <div className="text-2xl font-bold font-display">{currentRate}%</div>
          <div className="text-xs font-medium">
            {growth >= 0 ? "+" : ""}{growth.toFixed(1)}% since start
          </div>
        </div>
      </div>
      
      <div className="h-64 ring-1 ring-white/5 rounded-2xl bg-slate-900/20 p-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="marketTrendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.05)" vertical={false} />
            <XAxis 
              dataKey="month" 
              tick={{ fill: "#64748b", fontSize: 10, fontWeight: 500 }} 
              axisLine={false} 
              tickLine={false}
              tickMargin={10}
            />
            <YAxis 
              domain={[60, 100]} 
              tick={{ fill: "#64748b", fontSize: 10, fontWeight: 500 }} 
              axisLine={false} 
              tickLine={false} 
              orientation="left"
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(45,212,191,0.2)", strokeWidth: 2 }} />
            <ReferenceLine y={95} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.4} />
            <Area 
              type="monotone" 
              dataKey="success_rate" 
              stroke="#2dd4bf" 
              strokeWidth={3} 
              fill="url(#marketTrendFill)" 
              activeDot={{ r: 6, strokeWidth: 0, fill: "#f0fdfa" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
