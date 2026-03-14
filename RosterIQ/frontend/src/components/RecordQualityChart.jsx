import React from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#10b981", "#38bdf8", "#f59e0b", "#f43f5e"];

export default function RecordQualityChart({ data = {} }) {
  const chartData = [
    { name: "Success", value: data.success || 65 },
    { name: "Fail", value: data.fail || 15 },
    { name: "Skip", value: data.skip || 10 },
    { name: "Reject", value: data.reject || 10 }
  ];

  const total = chartData.reduce((acc, cur) => acc + cur.value, 0);

  return (
    <section className="panel-shell p-6 bg-slate-950/40">
      <div className="mb-4">
        <h3 className="panel-title">Record Quality</h3>
        <p className="panel-subtitle mt-1">Outcome distribution across {total}% sample.</p>
      </div>

      <div className="relative h-64 flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie 
              data={chartData} 
              dataKey="value" 
              nameKey="name" 
              innerRadius={60} 
              outerRadius={80} 
              paddingAngle={5}
              cornerRadius={6}
              stroke="none"
            >
              {chartData.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "rgba(15, 23, 42, 0.9)", 
                border: "1px solid rgba(255,255,255,0.1)", 
                borderRadius: "12px",
                fontSize: "12px",
                fontWeight: 600
              }} 
              itemStyle={{ color: "#e2e8f0" }}
            />
          </PieChart>
        </ResponsiveContainer>
        
        {/* Center Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="text-3xl font-display font-bold text-white tracking-tight">
            {chartData[0].value}%
          </div>
          <div className="text-[10px] font-semibold text-emerald-400 uppercase tracking-widest">Success</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        {chartData.map((item, index) => (
          <div key={item.name} className="flex items-center justify-between rounded-xl bg-white/[0.03] px-3 py-2 text-xs transition hover:bg-white/[0.06]">
            <div className="flex items-center gap-2 text-slate-300">
              <span className="h-2 w-2 rounded-full shadow-[0_0_8px_current]" style={{ backgroundColor: COLORS[index % COLORS.length], color: COLORS[index % COLORS.length] }} />
              {item.name}
            </div>
            <div className="font-semibold text-white">{item.value}%</div>
          </div>
        ))}
      </div>
    </section>
  );
}
