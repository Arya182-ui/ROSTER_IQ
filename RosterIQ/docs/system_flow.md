# RosterIQ System Flow

## 1. User Query Flow

1. A user opens the React dashboard and either views analytics panels or submits a natural-language question.
2. The dashboard sends API requests to the FastAPI backend.
3. Standard analytics requests go directly to backend analytics services.
4. Natural-language requests go to `POST /ask`, which triggers the RosterIQ agent workflow.

## 2. Tool Selection

1. The agent receives the user query.
2. It checks recent investigation history from Firebase episodic memory.
3. It applies lightweight reasoning rules to decide the next action: `stuck_ros`, `failed_ros`, `org_rejections`, `state_rejections`, `market_success`, `retry_analysis`, `duration_anomalies`, `web_search`, or `root_cause_analysis`.
4. If the query references regulations, compliance, or provider organizations, the agent can branch to Tavily web search.
5. If the query asks why a market is dropping or what caused failures, the agent branches to root-cause analysis.

## 3. Data Analysis

1. Tool wrappers call the data engine.
2. The data engine loads the roster-processing dataset and market-operations dataset.
3. It normalizes dates, flags, durations, and available proxy metrics.
4. The selected tool returns structured JSON that the agent can explain or the frontend can render.

## 4. Root Cause Investigation

1. The root-cause analyzer isolates a target market or state.
2. It checks recent market success performance from aggregated operational metrics.
3. It compares the latest month to the previous month to detect decline.
4. It identifies organizations in that state with the highest failure or rejection proxy rates.
5. It checks duration anomalies to find likely stage bottlenecks.
6. It returns a concise explanation describing the probable operational cause.

## 5. Visualization Rendering

1. The dashboard calls chart-focused analytics endpoints.
2. The backend transforms raw operational data into chart-ready structures.
3. Recharts components render pipeline health distribution, market success trend, record quality breakdown, retry effectiveness, and the root-cause panel.
4. The result is a combined analytical and conversational experience for operations teams.
