# Demo Video Recording Plan (2-3 Minutes)

## 1. Intro (0:00-0:25)

- Problem in one line: provider roster pipeline failures are hard to diagnose fast.
- Solution in one line: RosterIQ combines memory, tools, and visual analytics.

## 2. Architecture Snapshot (0:25-0:45)

- Show architecture diagram briefly.
- Mention three memory types and tool layer.

## 3. Live Demo (0:45-2:20)

1. Ask stuck pipeline query
- Example: Which pipelines are currently stuck?
- Show response + stuck table/chart.

2. Show named procedures
- Call GET /procedures
- Call POST /procedures/triage_stuck_ros/run
- Call POST /procedures/market_health_report/run with state CA

3. Show cross-table report
- Call GET /analytics/pipeline-report?state=CA
- Highlight cross_table_correlation block.

4. Show memory reliability
- Call GET /memory/status
- Explain firebase/local_json fallback.

5. Show purposeful web search
- Ask one regulatory or compliance question
- Show sources influence in response.

## 4. Close (2:20-2:45)

- Summarize impact:
  - faster triage
  - explainable root cause
  - stronger operational decisions

## Recording Quality Checklist

- Full-screen browser visible
- Cursor movements intentional and slow
- Mic clarity check before recording
- No API keys or credentials visible
- Keep total duration under 3 minutes
