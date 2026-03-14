import React from "react";

export default function PipelineReportPanel({ report = {}, focusState }) {
  const summary = report.summary || {};
  const issues = report.pipeline_issues || [];
  const topProblemOrgs = report.top_problem_orgs || [];
  const recommendedActions = report.recommended_actions || [];

  return (
    <section className="panel-shell p-6">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="status-pill border-teal-400/20 bg-teal-400/10 text-teal-200">Pipeline Report</div>
          <h3 className="mt-4 font-display text-2xl font-semibold text-white">Operational report for {summary.state || focusState || "ALL"}</h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            Structured summary of pipeline health, top issue clusters, and the next actions your team should take.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Total ROs</div>
            <div className="mt-2 text-xl font-semibold text-white">{summary.total_ros ?? 0}</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Stuck</div>
            <div className="mt-2 text-xl font-semibold text-amber-300">{summary.stuck_ros ?? 0}</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Failed</div>
            <div className="mt-2 text-xl font-semibold text-rose-300">{summary.failed_ros ?? 0}</div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <div className="rounded-3xl border border-white/10 bg-slate-950/40 p-5">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Pipeline Issues</div>
          <div className="mt-4 space-y-3">
            {issues.length === 0 ? (
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-slate-400">No pipeline issues detected for this scope.</div>
            ) : (
              issues.map((issue) => (
                <div key={`${issue.ro_id}-${issue.stage}`} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="font-medium text-white">{issue.ro_id}</div>
                      <div className="mt-1 text-sm text-slate-400">{issue.stage}</div>
                    </div>
                    <div className={`rounded-full px-3 py-1 text-xs font-semibold ${issue.health === "RED" ? "bg-rose-500/15 text-rose-200" : "bg-amber-400/15 text-amber-200"}`}>
                      {issue.health}
                    </div>
                  </div>
                  <div className="mt-3 text-sm text-slate-300">Duration deviation: {issue.duration_deviation}</div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-3xl border border-white/10 bg-slate-950/40 p-5">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Top Problem Organizations</div>
            <div className="mt-4 space-y-3">
              {topProblemOrgs.length === 0 ? (
                <div className="text-sm text-slate-400">No concentrated failure clusters detected.</div>
              ) : (
                topProblemOrgs.map((org) => (
                  <div key={org.org} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
                    <div className="text-sm text-white">{org.org}</div>
                    <div className="text-sm font-semibold text-rose-300">{org.failure_count}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-slate-950/40 p-5">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Recommended Actions</div>
            <div className="mt-4 space-y-3">
              {recommendedActions.map((action) => (
                <div key={action} className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-slate-200">
                  {action}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
