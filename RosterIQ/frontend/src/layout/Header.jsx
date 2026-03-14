import React from "react";

const PAGE_LABELS = {
  dashboard: "Operations Overview",
  investigations: "Investigation Workspace",
  chat: "Agent Workspace"
};

export default function Header({ title, subtitle, activeView }) {
  return (
    <header className="panel-shell px-6 py-5">
      <div>
        <div className="section-caption text-teal-400 mb-2">{PAGE_LABELS[activeView] || "RosterIQ"}</div>
        <h2 className="font-display text-3xl font-semibold tracking-tight text-white">{title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{subtitle}</p>
      </div>
    </header>
  );
}
