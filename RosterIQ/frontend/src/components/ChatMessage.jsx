import React from "react";

function AgentTrace({ toolUsed }) {
  const tools = Array.isArray(toolUsed) ? toolUsed : toolUsed ? [toolUsed] : [];
  if (tools.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/50 p-3">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Agent used</div>
      <ul className="mt-2 space-y-1 text-sm text-slate-200">
        {tools.map((tool) => (
          <li key={tool}>• {tool}</li>
        ))}
      </ul>
    </div>
  );
}

function DataSummary({ message }) {
  if (message.role !== "assistant") {
    return null;
  }

  const reportSummary = message.report?.summary;
  return (
    <div className="mt-4 grid gap-3 md:grid-cols-2">
      {typeof message.count === "number" ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Data summary</div>
          <div className="mt-2">Returned records: {message.count}</div>
        </div>
      ) : null}
      {reportSummary ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Report scope</div>
          <div className="mt-2">
            {reportSummary.state}: {reportSummary.failed_ros} failed / {reportSummary.stuck_ros} stuck
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-3xl rounded-3xl border px-5 py-4 shadow-lg ${
          isUser
            ? "border-teal-400/20 bg-gradient-to-br from-teal-500 to-cyan-500 text-slate-950"
            : "border-white/10 bg-slate-900/80 text-slate-100"
        }`}
      >
        <div className="text-xs uppercase tracking-[0.18em] opacity-70">
          {isUser ? "You" : "RosterIQ Agent"}
        </div>
        <div className="mt-3 whitespace-pre-wrap text-sm leading-7">{message.content}</div>
        <DataSummary message={message} />
        {!isUser ? <AgentTrace toolUsed={message.toolUsed} /> : null}
        {!isUser && message.sources?.length ? (
          <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/50 p-3">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Sources</div>
            <div className="mt-2 space-y-1 text-sm text-slate-300">
              {message.sources.map((source) => (
                <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="block truncate text-teal-300 hover:text-teal-200">
                  {source.title || source.url}
                </a>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
