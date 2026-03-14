import React from "react";
import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { path: "/dashboard", label: "Dashboard", description: "See current health and recommended actions" },
  { path: "/investigations", label: "Investigations", description: "Review history and reopen previous work" },
  { path: "/chat", label: "Agent Chat", description: "Ask questions in plain language" }
];

export default function Sidebar() {
  return (
    <aside className="panel-shell flex h-full flex-col gap-8 p-5 overflow-y-auto custom-scrollbar">
      <div>
        <div className="mb-5 flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/25">
            <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 transition hover:opacity-100" />
            <span className="font-display text-lg font-bold text-white">RQ</span>
          </div>
          <h1 className="font-display text-xl font-bold tracking-tight text-white">
            Roster<span className="text-cyan-400">IQ</span>
          </h1>
        </div>
        <p className="px-1 text-xs font-medium leading-5 text-slate-400">
          AI operations dashboard for provider roster pipelines, market issues, and investigation workflows.
        </p>
      </div>

      <nav className="flex flex-col gap-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `group block rounded-2xl border px-4 py-4 text-left transition ${
                isActive
                  ? "border-cyan-500/30 bg-cyan-500/10"
                  : "border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`text-sm font-semibold ${isActive ? "text-cyan-400" : "text-slate-200 group-hover:text-white"}`}>
                  {item.label}
                </div>
                <div className={`mt-1 text-xs leading-5 ${isActive ? "text-cyan-200/70" : "text-slate-500 group-hover:text-slate-400"}`}>
                  {item.description}
                </div>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-3xl border border-slate-700 bg-gradient-to-br from-slate-900 to-slate-800 p-5 text-white shadow-lg">
        <div className="text-xs uppercase tracking-[0.22em] text-cyan-400 font-semibold">What this app does</div>
        <div className="mt-3 font-display text-lg font-medium">Find problems fast</div>
        <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
          <li className="flex gap-2"><span className="text-cyan-500">•</span> Track failed roster ops</li>
          <li className="flex gap-2"><span className="text-cyan-500">•</span> Explain market drops</li>
          <li className="flex gap-2"><span className="text-cyan-500">•</span> Reuse investigation history</li>
        </ul>
      </div>
    </aside>
  );
}
