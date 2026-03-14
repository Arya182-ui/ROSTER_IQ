import React from "react";

function renderParagraphs(content) {
  return content
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph, index) => (
      <p key={`${paragraph.slice(0, 24)}-${index}`} className="text-sm leading-7 text-current">
        {paragraph}
      </p>
    ));
}

function AgentTrace({ toolUsed }) {
  const tools = Array.isArray(toolUsed) ? toolUsed : toolUsed ? [toolUsed] : [];
  const visibleTools = tools.filter((tool) => tool && tool !== "conversation");

  if (visibleTools.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {visibleTools.map((tool) => (
        <span key={tool} className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-cyan-200">
          {tool.replaceAll("_", " ")}
        </span>
      ))}
    </div>
  );
}

function SummaryChips({ message }) {
  if (message.role !== "assistant") {
    return null;
  }

  const chips = [];
  const reportSummary = message.report?.summary;

  if (typeof message.count === "number" && message.count > 0) {
    chips.push(`Records: ${message.count}`);
  }

  if (reportSummary) {
    chips.push(`${reportSummary.state || "ALL"} report`);
    chips.push(`${reportSummary.stuck_ros || 0} stuck / ${reportSummary.failed_ros || 0} failed`);
  }

  if (message.stateChange?.change && message.stateChange.change !== "no_history") {
    chips.push(`Trend: ${message.stateChange.change}`);
  }

  if (!chips.length) {
    return null;
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {chips.map((chip) => (
        <span key={chip} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-300">
          {chip}
        </span>
      ))}
    </div>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`rounded-[28px] border px-5 py-4 shadow-xl ${
          isUser
            ? "max-w-md border-cyan-300/20 bg-gradient-to-br from-cyan-400 to-teal-400 text-slate-950"
            : "max-w-4xl border-white/10 bg-slate-900/88 text-slate-100"
        }`}
      >
        <div className="text-[11px] uppercase tracking-[0.22em] opacity-70">{isUser ? "You" : "RosterIQ"}</div>
        <div className="mt-3 space-y-4 whitespace-pre-wrap">{renderParagraphs(message.content)}</div>
        {!isUser ? <SummaryChips message={message} /> : null}
        {!isUser ? <AgentTrace toolUsed={message.toolUsed} /> : null}
        {!isUser && message.sources?.length ? (
          <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Sources</div>
            <div className="mt-3 space-y-2 text-sm text-slate-300">
              {message.sources.map((source) => (
                <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="block truncate text-cyan-300 transition hover:text-cyan-200">
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
