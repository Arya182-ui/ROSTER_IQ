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
      return { ...state, loading: false, data: action.payload };
    case "INIT_FAILURE":
      return { ...state, loading: false, error: action.payload };
    case "SET_FOCUS":
      return { ...state, focusState: action.payload };
    case "FOCUS_SUCCESS":
      return { ...state, focusedData: action.payload };
    case "FOCUS_FAILURE":
      // We don't block the whole dashboard for focused data failures
      console.error(action.payload);
      return state;
    default:
      return state;
  }
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse px-2">
      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <div className="rounded-3xl border border-white/5 bg-slate-900/50 h-48"></div>
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4 xl:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-2xl border border-white/5 bg-slate-900/50 h-32"></div>
          ))}
        </div>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
         <div className="rounded-3xl border border-white/5 bg-slate-900/50 h-96"></div>
         <div className="rounded-3xl border border-white/5 bg-slate-900/50 h-96"></div>
      </div>
    </div>
  );
}

export default function DashboardPage({ onOpenChat }) {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);
  const { loading, error, focusState, data, focusedData } = state;

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
                <div className="text-xs uppercase tracking-[0.18em] text-slate-500 mb-2">Focus state</div>
                <select
                  value={focusState}
                  onChange={(e) => dispatch({ type: "SET_FOCUS", payload: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-teal-500 focus:outline-none appearance-none cursor-pointer hover:bg-slate-800"
                >
                  {stateOptions.map((state) => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={onOpenChat}
                className="rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-500 px-6 py-4 text-sm font-semibold text-slate-950 transition hover:brightness-110 shadow-lg shadow-teal-500/20"
              >
                Ask agent about {focusState}
              </button>
            </div>
          </div>
        </div>

        <div className="grid gap-4 grid-cols-2 md:grid-cols-4 xl:grid-cols-2">
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

      <AnalyticsDashboard
        pipelineHealth={data.pipelineHealth}
        marketTrend={data.marketTrend}
        retryAnalysis={data.retryAnalysis}
        recordQuality={data.recordQuality}
        failedRos={data.failedRos}
        focusState={focusState}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <RootCausePanel stateCode={focusState} data={focusedData.rootCause} />
        <PipelineReportPanel report={focusedData.pipelineReport} focusState={focusState} />
      </div>

      <StuckROTable rows={data.stuckRos} anomalies={data.durationAnomalies} focusState={focusState} />
    </div>
  );
}
