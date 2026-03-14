import React from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function RetryAnalysisChart({ data = [] }) {
  return (
    <section className="panel-shell p-5">
      <div className="mb-5">
        <h3 className="panel-title">Retry Effectiveness</h3>
        <p className="panel-subtitle mt-2">Compare success rates between first-pass and retry attempts.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 16, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
            <XAxis dataKey="stage" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ backgroundColor: "#020617", border: "1px solid rgba(148,163,184,0.15)", borderRadius: 18 }} />
            <Bar dataKey="success" radius={[12, 12, 0, 0]} fill="#38bdf8" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
