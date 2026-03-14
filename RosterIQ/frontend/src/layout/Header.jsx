import React from "react";

const PAGE_LABELS = {
  dashboard: "Operations Command",
  investigations: "Saved Investigations",
  chat: "Live AI Copilot"
};

export default function Header({ title, subtitle, activeView }) {
  return (
    <header className="panel-shell overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.12),transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.94),rgba(8,15,30,0.94))] px-6 py-5">
      <div>
        <div className="section-caption mb-2 text-cyan-300">{PAGE_LABELS[activeView] || "RosterIQ"}</div>
        <h2 className="font-display text-3xl font-semibold tracking-tight text-white">{title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300">{subtitle}</p>
      </div>
    </header>
  );
}
