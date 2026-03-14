import React, { useEffect, useMemo, useRef, useState } from "react";
import { askAgent } from "../api/api";
import { APP_CONFIG } from "../config";
import ChatMessage from "./ChatMessage";

const DEFAULT_MESSAGES = [
  {
    id: "welcome",
    role: "assistant",
    content:
      "Ask a direct operational question and I will route it to the right analysis path. Good examples: 'Which pipelines are stuck in CA?' or 'Generate an operational report for CA.'",
    toolUsed: []
  }
];

export default function ChatPanel({ queuedQuery, onQueuedQueryConsumed, onCompleted }) {
  const [messages, setMessages] = useState(DEFAULT_MESSAGES);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);
  const quickPrompts = useMemo(() => APP_CONFIG.quickPrompts, []);

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
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.analysis || "No analysis returned.",
        toolUsed: response.tool_used,
        count: response.count,
        report: response.report,
        sources: response.sources || [],
        stateChange: response.state_change,
        data: response.data || []
      };

      setMessages((current) => [...current, assistantMessage]);
      onCompleted?.({ query: trimmed, response });
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

  return (
    <section className="panel-shell flex min-h-[760px] flex-col overflow-hidden">
      <div className="border-b border-white/10 px-6 py-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="section-caption text-cyan-300">Live conversation</div>
            <h3 className="mt-2 panel-title text-2xl">Ask the agent in plain language</h3>
            <p className="panel-subtitle mt-2 max-w-2xl">
              RosterIQ handles routing, summary generation, and structured follow-up context so you do not have to open each tool manually.
            </p>
          </div>
          {loading ? <div className="status-pill border-cyan-400/20 bg-cyan-400/10 text-cyan-200">Analyzing</div> : null}
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => runQuery(prompt)}
              className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-left text-sm font-medium text-slate-200 transition hover:border-cyan-400/30 hover:bg-cyan-400/10 hover:text-white"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="custom-scrollbar flex-1 space-y-5 overflow-y-auto px-6 py-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {loading ? (
          <div className="flex justify-start">
            <div className="rounded-3xl border border-cyan-400/10 bg-slate-950/80 px-5 py-4 text-sm text-slate-300 shadow-lg shadow-cyan-500/5">
              <div className="flex items-center gap-3">
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-cyan-400" />
                RosterIQ is reviewing the data and preparing a short answer.
              </div>
            </div>
          </div>
        ) : null}

        <div ref={endRef} />
      </div>

      <form
        className="border-t border-white/10 bg-slate-950/40 px-6 py-5"
        onSubmit={(event) => {
          event.preventDefault();
          runQuery(input);
        }}
      >
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end">
          <div className="flex-1">
            <label className="mb-2 block text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Your question</label>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              rows={4}
              placeholder="Ask about stuck pipelines, failed roster ops, market drops, or request a state report..."
              className="min-h-[128px] w-full rounded-3xl border border-white/10 bg-slate-950/80 px-4 py-4 text-sm leading-7 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400/40"
            />
          </div>
          <div className="flex gap-3 xl:w-[210px] xl:flex-col">
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="flex-1 rounded-3xl bg-gradient-to-br from-cyan-300 to-teal-400 px-5 py-4 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Working..." : "Send to agent"}
            </button>
            <button
              type="button"
              onClick={() => {
                setMessages(DEFAULT_MESSAGES);
                setInput("");
              }}
              className="rounded-3xl border border-white/10 bg-white/[0.03] px-5 py-4 text-sm font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
            >
              Reset chat
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
