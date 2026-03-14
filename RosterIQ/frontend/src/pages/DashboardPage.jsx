import React, { useEffect, useMemo, useReducer } from "react";
import {
  getDurationAnomalies,
  getFailedRos,
  getHealth,
  getMarketTrend,
  getPipelineHealth,
  getPipelineReport,
  getRecordQuality,
  getRetryAnalysis,
  getRootCause,
  getStuckRos
} from "../api/api";
import { APP_CONFIG } from "../config";
import AnalyticsDashboard from "../components/AnalyticsDashboard";
import PipelineReportPanel from "../components/PipelineReportPanel";
import RootCausePanel from "../components/RootCausePanel";
import StatCard from "../components/StatCard";
import StuckROTable from "../components/StuckROTable";

const initialState = {
  loading: true,
  focusedLoading: true,
  error: "",
  focusState: APP_CONFIG.defaultState || "CA",
  data: {
    health: null,
    pipelineHealth: [],
    marketTrend: [],
    recordQuality: {},
    retryAnalysis: [],
    stuckRos: [],
    failedRos: [],
    durationAnomalies: []
  },
  focusedData: {
    rootCause: {},
    pipelineReport: {}
  }
};

function dashboardReducer(state, action) {
  switch (action.type) {
    case "INIT_START":
      return { ...state, loading: true, error: "" };
    case "INIT_SUCCESS":
      return { ...state, loading: false, focusedLoading: false, data: action.payload };
    case "INIT_FAILURE":
      return { ...state, loading: false, error: action.payload };
    case "SET_FOCUS":
      return { ...state, focusState: action.payload };
    case "FOCUS_START":
      return { ...state, focusedLoading: true };
    case "FOCUS_SUCCESS":
      return { ...state, focusedLoading: false, focusedData: action.payload };
    case "FOCUS_FAILURE":
      // We don't block the whole dashboard for focused data failures
      console.error(action.payload);
      return { ...state, focusedLoading: false };
    default:
      return state;
  }
}

function truncateText(text, maxLength = 78) {
  if (!text) {
    return "";
  }
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
}

function SkeletonBlock({ className = "" }) {
  return <div className={`animate-pulse rounded-2xl border border-white/10 bg-white/[0.04] ${className}`} aria-hidden="true" />;
}

function SkeletonLine({ className = "" }) {
  return <div className={`animate-pulse rounded-full bg-white/[0.06] ${className}`} aria-hidden="true" />;
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300 px-2" aria-busy="true">
      <section className="panel-shell overflow-hidden border-teal-400/10 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.12),transparent_32%),linear-gradient(180deg,rgba(15,23,42,0.94),rgba(8,15,30,0.94))] p-6">
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="status-pill border-teal-400/20 bg-teal-400/10 text-teal-200">Loading live analytics</div>
            <h3 className="mt-4 font-display text-3xl font-semibold tracking-tight text-white">
              Preparing the operations dashboard
            </h3>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
              Fetching pipeline health, failure clusters, anomaly tracking, and state-specific investigations before the charts render.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {["Pipeline health", "Market trend", "Root cause", "Stuck RO tracker"].map((item) => (
                <div
                  key={item}
                  className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium text-slate-300"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-slate-950/45 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="section-caption text-cyan-300">Load status</div>
                <div className="mt-2 text-sm font-medium text-white">Syncing dashboard panels</div>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/10">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-200/30 border-t-cyan-200" />
              </div>
            </div>

            <div className="mt-5 rounded-full border border-white/10 bg-white/[0.04] p-1">
              <div className="h-2.5 w-2/3 animate-pulse rounded-full bg-gradient-to-r from-teal-400 via-cyan-300 to-sky-400" />
            </div>

            <div className="mt-5 space-y-3 text-sm text-slate-300">
              {[
                "Connecting to analytics endpoints",
                "Collecting state-level failure signals",
                "Rendering charts, summaries, and tables"
              ].map((step) => (
                <div key={step} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
                  <div className="h-2 w-2 animate-pulse rounded-full bg-cyan-300 shadow-[0_0_12px_rgba(103,232,249,0.8)]" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {["API Status", "Failures", "Stuck Pipes", "Actions"].map((label) => (
          <div key={label} className="panel-shell p-5">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</div>
            <SkeletonBlock className="mt-4 h-10" />
            <SkeletonLine className="mt-4 h-3 w-24" />
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        {[1, 2, 3, 4].map((panel) => (
          <div key={panel} className="panel-shell p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <SkeletonLine className="h-3 w-40" />
                <SkeletonLine className="mt-3 h-3 w-56" />
              </div>
              <SkeletonBlock className="h-12 w-20" />
            </div>
            <SkeletonBlock className="mt-6 h-72 rounded-[28px]" />
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        {[1, 2].map((panel) => (
          <div key={panel} className="panel-shell p-6">
            <SkeletonLine className="h-3 w-44" />
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {[1, 2, 3, 4].map((card) => (
                <SkeletonBlock key={card} className="h-24" />
              ))}
            </div>
            <SkeletonBlock className="mt-5 h-32 rounded-3xl" />
          </div>
        ))}
      </section>

      <section className="panel-shell p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <SkeletonLine className="h-3 w-36" />
            <SkeletonLine className="mt-3 h-3 w-72" />
          </div>
          <SkeletonBlock className="h-10 w-28 rounded-full" />
        </div>
        <div className="mt-6 space-y-3">
          {[1, 2, 3, 4].map((row) => (
            <div key={row} className="grid gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 md:grid-cols-6">
              {[1, 2, 3, 4, 5, 6].map((cell) => (
                <SkeletonLine key={cell} className="h-4 w-full" />
              ))}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default function DashboardPage({ onOpenChat }) {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);
  const { loading, focusedLoading, error, focusState, data, focusedData } = state;

  useEffect(() => {
    async function loadDashboard() {
      dispatch({ type: "INIT_START" });
      try {
        const [
          health,
          pipelineHealth,
          marketTrend,
          recordQuality,
          retryAnalysis,
          stuckResponse,
          failedResponse,
          durationAnomaliesResponse
        ] = await Promise.all([
          getHealth(),
          getPipelineHealth(),
          getMarketTrend(),
          getRecordQuality(),
          getRetryAnalysis(),
          getStuckRos(),
          getFailedRos(),
          getDurationAnomalies()
        ]);

        dispatch({
          type: "INIT_SUCCESS",
          payload: {
            health,
            pipelineHealth: pipelineHealth || [],
            marketTrend: marketTrend || [],
            recordQuality: recordQuality || {},
            retryAnalysis: retryAnalysis || [],
            stuckRos: stuckResponse.items || [],
            failedRos: failedResponse.items || [],
            durationAnomalies: durationAnomaliesResponse.items || []
          }
        });
      } catch (err) {
        dispatch({ type: "INIT_FAILURE", payload: err.message || "Failed to load dashboard." });
      }
    }

    loadDashboard();
  }, []);

  useEffect(() => {
    async function loadFocused() {
      try {
        dispatch({ type: "FOCUS_START" });
        const [rootCause, pipelineReport] = await Promise.all([
          getRootCause(focusState),
          getPipelineReport(focusState)
        ]);
        dispatch({
          type: "FOCUS_SUCCESS",
          payload: {
            rootCause: rootCause || {},
            pipelineReport: pipelineReport || {}
          }
        });
      } catch (err) {
        dispatch({ type: "FOCUS_FAILURE", payload: err.message || "Failed to load analysis." });
      }
    }
    loadFocused();
  }, [focusState]);

  const stateOptions = useMemo(() => {
    const uniqueStates = new Set([focusState]);
    data.stuckRos.forEach((row) => uniqueStates.add(row.CNT_STATE));
    data.failedRos.forEach((row) => uniqueStates.add(row.CNT_STATE));
    return Array.from(uniqueStates).filter(Boolean).sort();
  }, [data.stuckRos, data.failedRos, focusState]);

  const scopedFailedRos = useMemo(
    () => data.failedRos.filter((row) => row.CNT_STATE === focusState),
    [data.failedRos, focusState]
  );

  const focusInsightCards = useMemo(() => {
    const summary = focusedData.pipelineReport.summary || {};
    const recommendedActions = focusedData.pipelineReport.recommended_actions || [];
    const confidenceScore = Math.round((focusedData.rootCause.confidence_score || 0) * 100);

    return [
      {
        label: "Focus Market",
        value: focusedData.rootCause.market || focusState,
        note: `${summary.total_ros ?? 0} total roster ops in scope`,
        shell: "border-cyan-400/20 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.14),transparent_44%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(8,15,30,0.92))]",
        tone: "text-cyan-200"
      },
      {
        label: "Confidence",
        value: `${confidenceScore}%`,
        note: focusedData.rootCause.likely_stage_issue || "Watching for the most likely stage issue",
        shell: "border-emerald-400/20 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.14),transparent_42%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(8,15,30,0.92))]",
        tone: "text-emerald-200"
      },
      {
        label: "Primary Organization",
        value: focusedData.rootCause.primary_org || "No cluster yet",
        note: `${summary.failed_ros ?? scopedFailedRos.length} failed roster ops currently in view`,
        shell: "border-amber-400/20 bg-[radial-gradient(circle_at_top_right,rgba(251,191,36,0.14),transparent_42%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(8,15,30,0.92))]",
        tone: "text-amber-100"
      },
      {
        label: "Recommended Actions",
        value: `${recommendedActions.length}`,
        note: truncateText(recommendedActions[0] || `${summary.stuck_ros ?? data.stuckRos.length} stuck roster ops need follow-up`),
        shell: "border-fuchsia-400/20 bg-[radial-gradient(circle_at_top_right,rgba(244,114,182,0.14),transparent_42%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(8,15,30,0.92))]",
        tone: "text-fuchsia-100"
      }
    ];
  }, [data.stuckRos.length, focusState, focusedData.pipelineReport, focusedData.rootCause, scopedFailedRos.length]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {error && (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
          {error}
        </div>
      )}

      <section className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <div className="panel-shell p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="status-pill text-teal-300 border-teal-500/30 bg-teal-500/10">Live Operations</div>
              <h3 className="mt-3 font-display text-2xl font-semibold text-white tracking-tight">Pipeline Control Center</h3>
              <p className="mt-1 text-sm text-slate-400">
                Monitor live roster health and investigate anomalies with AI assistance.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
                <div className="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">Focus state</div>
                <select
                  value={focusState}
                  onChange={(e) => dispatch({ type: "SET_FOCUS", payload: e.target.value })}
                  className="w-full cursor-pointer appearance-none rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800 focus:border-teal-500 focus:outline-none"
                >
                  {stateOptions.map((state) => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={onOpenChat}
                className="rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-500 px-6 py-4 text-sm font-semibold text-slate-950 shadow-lg shadow-teal-500/20 transition hover:brightness-110"
              >
                Ask agent about {focusState}
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-2">
          <StatCard
            label="API Status"
            value={data.health?.status || "unknown"}
            tone="text-emerald-400"
            icon={<div className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.6)]" />}
          />
          <StatCard
            label={`${focusState} Failures`}
            value={scopedFailedRos.length}
            subValue="last 7 days"
            trend={scopedFailedRos.length > 5 ? "down" : "up"}
            tone="text-rose-400"
          />
          <StatCard
            label="Stuck Pipes"
            value={data.stuckRos.length}
            subValue="needs action"
            tone="text-amber-400"
          />
          <StatCard
            label="Actions"
            value={focusedData.pipelineReport.recommended_actions?.length || 0}
            tone="text-sky-400"
          />
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {focusInsightCards.map((card) => (
          <div key={card.label} className={`panel-shell overflow-hidden p-5 ${card.shell}`}>
            <div className="section-caption text-slate-400">{card.label}</div>
            <div className={`mt-4 font-display text-2xl font-semibold tracking-tight ${card.tone}`}>{card.value}</div>
            <p className="mt-2 text-sm leading-6 text-slate-300">{card.note}</p>
          </div>
        ))}
      </section>

      {focusedLoading && (
        <section className="panel-shell border-cyan-400/20 bg-cyan-500/10 p-4 text-sm text-cyan-100">
          Updating state-specific root-cause and pipeline report panels for {focusState}...
        </section>
      )}

      <AnalyticsDashboard
        pipelineHealth={data.pipelineHealth}
        marketTrend={data.marketTrend}
        retryAnalysis={data.retryAnalysis}
        recordQuality={data.recordQuality}
        failedRos={data.failedRos}
        focusState={focusState}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        {focusedLoading ? (
          <div className="panel-shell p-6">
            <SkeletonLine className="h-3 w-44" />
            <SkeletonLine className="mt-3 h-3 w-64" />
            <SkeletonBlock className="mt-5 h-56 rounded-3xl" />
          </div>
        ) : (
          <RootCausePanel stateCode={focusState} data={focusedData.rootCause} />
        )}
        {focusedLoading ? (
          <div className="panel-shell p-6">
            <SkeletonLine className="h-3 w-44" />
            <SkeletonLine className="mt-3 h-3 w-64" />
            <SkeletonBlock className="mt-5 h-56 rounded-3xl" />
          </div>
        ) : (
          <PipelineReportPanel report={focusedData.pipelineReport} focusState={focusState} />
        )}
      </div>

      <StuckROTable rows={data.stuckRos} anomalies={data.durationAnomalies} focusState={focusState} />
    </div>
  );
}
