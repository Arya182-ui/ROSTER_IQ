# RosterIQ Architecture Diagram

```mermaid
graph TD
    User[User / Ops Analyst] --> ReactDashboard[React Dashboard]
    ReactDashboard --> FastAPI[FastAPI Backend]
    FastAPI --> Agent[AI Agent Core]
    FastAPI --> Analytics[Visualization Analytics Service]

    Agent --> Tools[Tools Layer]
    Agent --> SemanticMemory[Semantic Memory JSON]
    Agent --> EpisodicMemory[Firebase Episodic Memory]
    Agent --> WebSearch[Web Search Tool - Tavily]
    Agent --> RootCause[Root Cause Analyzer]

    Tools --> DataEngine[Data Engine]
    RootCause --> DataEngine
    Analytics --> DataEngine

    DataEngine --> RosterCSV[roster_processing_details.csv]
    DataEngine --> MarketCSV[aggregated_operational_metrics.csv]
```

## Data Flow Summary

`React Dashboard` sends analytics and agent requests to the `FastAPI Backend`.

For natural-language questions, FastAPI hands the request to the `AI Agent Core`, which selects tools, looks up semantic definitions, checks episodic memory, optionally calls `Tavily` for external context, and can invoke the `Root Cause Analyzer`.

For charts and operational views, FastAPI uses the `Visualization Analytics Service`, which reads processed data from the `Data Engine`.

The `Data Engine` loads and normalizes the two CSV datasets and serves both the analytics layer and the agent tool layer.
