import React from "react";
import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { path: "/dashboard", label: "Dashboard", description: "Live health, KPIs, and recommended actions" },
  { path: "/investigations", label: "Investigations", description: "Saved runs, history, and reruns" },
  { path: "/chat", label: "Agent Chat", description: "Live AI triage workspace" }
];

export default function Sidebar() {
  return (
    <aside className="panel-shell custom-scrollbar flex h-full flex-col gap-8 overflow-y-auto p-5">
      <div>
        <div className="mb-5 flex items-center gap-3">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-400 via-sky-500 to-blue-600 shadow-lg shadow-cyan-500/25">
            <span className="font-display text-lg font-bold text-white">RQ</span>
          </div>
          <h1 className="font-display text-xl font-bold tracking-tight text-white">
            Roster<span className="text-cyan-300">IQ</span>
          </h1>
        </div>
        <p className="px-1 text-sm leading-7 text-slate-400">
          Operations intelligence for provider roster pipelines, market signals, and repeatable investigations.
        </p>
      </div>

      <nav className="flex flex-col gap-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `group block rounded-3xl border px-4 py-4 text-left transition ${
                isActive
                  ? "border-cyan-400/30 bg-cyan-400/10 shadow-lg shadow-cyan-500/5"
                  : "border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`text-sm font-semibold ${isActive ? "text-cyan-200" : "text-slate-200 group-hover:text-white"}`}>
                  {item.label}
                </div>
                <div className={`mt-1 text-xs leading-6 ${isActive ? "text-cyan-100/70" : "text-slate-500 group-hover:text-slate-400"}`}>
                  {item.description}
                </div>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(45,212,191,0.18),transparent_38%),linear-gradient(180deg,rgba(15,23,42,0.96),rgba(9,14,27,0.96))] p-5 text-white shadow-xl shadow-slate-950/30">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-300">Why two workspaces</div>
        <div className="mt-3 font-display text-lg font-medium">Live chat plus saved memory</div>
        <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
          <div>Agent Chat answers a question now.</div>
          <div>Investigations stores what was already analyzed.</div>
          <div>Dashboard stays focused on the live operating picture.</div>
        </div>
      </div>
    </aside>
  );
}
