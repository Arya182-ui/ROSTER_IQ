# RosterIQ Hackathon Demo Script

## Introduction - 30 Seconds

"Healthcare provider roster pipelines are operationally critical, but they are hard to diagnose. Teams often deal with failed files, stuck stages, rejection spikes, and declining market performance across multiple dashboards and manual investigation steps.

RosterIQ solves that by acting as an AI operations intelligence agent. It analyzes roster pipeline data, remembers prior investigations, uses domain knowledge, searches external context when needed, and surfaces likely root causes through both natural-language answers and visual dashboards."

## Live Demonstration - 2 Minutes

### Demo 1: Stuck Pipelines

"First, I’ll ask RosterIQ: `Which pipelines are currently stuck?`

The agent routes that question to the stuck pipeline analytics tool, retrieves the relevant roster operations, and returns a concise explanation. At the same time, the dashboard shows the stuck pipeline table and stage-level health distribution, so the team can immediately see where the bottlenecks are."

Then call `GET /procedures` and `POST /procedures/triage_stuck_ros/run` to show a named procedural workflow running directly.

### Demo 2: Root Cause Analysis

"Next, I’ll ask: `Why is CA market success dropping?`

Here the agent switches into root-cause mode. It checks the market success trend, identifies organizations in California with the highest issue rates, reviews stage anomalies, and generates a likely explanation. The root-cause panel highlights the market, the size of the drop, the most impacted organization, the likely pipeline stage, and a plain-English explanation."

Then call `GET /analytics/pipeline-report?state=CA` and highlight `cross_table_correlation` to prove same-state and same-month market/pipeline linkage.

### Demo 3: Visual Analytics

"Finally, I’ll show the analytics layer.

The pipeline health chart shows which stages are healthy versus degraded.
The market success trend shows how market performance changes over time.
The retry effectiveness chart shows whether retries are actually recovering throughput.
Together, these visuals turn raw operational data into fast, decision-ready insight."

### Demo 4: Memory Reliability

"Now I’ll call `GET /memory/status`.

This shows whether episodic memory is using Firebase or local JSON fallback. If Firebase is unavailable, investigations still persist locally so sessions remain resilient instead of failing silently."

### Demo 5: Purposeful Web Search Uses

Use 3 targeted questions:

1. `What recent CMS updates could explain Medicaid rejection spikes in VA?`
2. `What does Complete Validation Failure usually indicate in provider roster compliance?`
3. `What policy changes could affect Medicaid FFS roster submissions in KS?`

"For each query, show returned sources and explain how external context is incorporated into recommendations."

## Conclusion - 30 Seconds

"RosterIQ stands out for three reasons:

First, it is a memory-driven agent, so it can build continuity across investigations.
Second, it performs automated root-cause analysis instead of just listing metrics.
Third, it combines AI reasoning with clear visual operational insight.

The result is a system that helps healthcare operations teams diagnose issues faster and act with more confidence."
