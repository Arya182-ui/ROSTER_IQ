import React, { useEffect, useMemo, useRef, useState } from "react";
import { askAgent } from "../api/api";
import { APP_CONFIG } from "../config";
import ChatMessage from "./ChatMessage";

const DEFAULT_MESSAGES = [
  {
    id: "welcome",
    role: "assistant",
    content: "Ask about stuck pipelines, market regressions, compliance context, or request a structured operational report.",
    toolUsed: []
  }
];

export default function ChatPanel({ queuedQuery, onQueuedQueryConsumed }) {
  const [messages, setMessages] = useState(DEFAULT_MESSAGES);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);


  async function runQuery(query) {
    const trimmed = query.trim();
    if (!trimmed || loading) {
      return;
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed
    };
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await askAgent(trimmed);
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.analysis || "No analysis returned.",
          toolUsed: response.tool_used,
          count: response.count,
          report: response.report,
          sources: response.sources || [],
          stateChange: response.state_change,
          data: response.data || []
        }
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: error.message || "The investigation request failed.",
          toolUsed: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (queuedQuery) {
      runQuery(queuedQuery);
      onQueuedQueryConsumed?.();
    }
  }, [queuedQuery]);

  const quickPrompts = useMemo(() => APP_CONFIG.quickPrompts, []);

  return (
    <section className="panel-shell flex h-[600px] flex-col overflow-hidden lg:h-full lg:min-h-[650px]">
      <div className="border-b border-white/10 px-6 py-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="panel-title">AI Investigation Chat</h3>
            <p className="panel-subtitle mt-1">Run agent investigations and review tool-assisted responses.</p>
          </div>
          {loading && <div className="status-pill border-teal-500/30 bg-teal-500/10 text-teal-300">Analysis Active</div>}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => runQuery(prompt)}
              className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-medium text-slate-300 transition hover:border-teal-500/30 hover:bg-teal-500/10 hover:text-white"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {loading ? (
          <div className="flex justify-start">
            <div className="rounded-3xl border border-white/10 bg-slate-900/80 px-5 py-4 text-sm text-slate-300">
              <div className="flex items-center gap-3">
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-teal-400" />
                RosterIQ is assembling the investigation.
              </div>
            </div>
          </div>
        ) : null}
        <div ref={endRef} />
      </div>

      <form
        className="border-t border-white/10 px-6 py-5"
        onSubmit={(event) => {
          event.preventDefault();
          runQuery(input);
        }}
      >
        <div className="flex flex-col gap-3 lg:flex-row">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            rows={3}
            placeholder="Ask RosterIQ to triage stuck pipelines, explain a market drop, or build an operational report..."
            className="min-h-[110px] flex-1 rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-teal-400/50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-500 px-5 py-4 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50 lg:w-40"
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </section>
  );
}
