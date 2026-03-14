"""Keyword-based tool-selection logic for the initial RosterIQ agent."""

from __future__ import annotations



def decide_tool(user_query: str) -> str:
    """Route a natural-language query to an analytics tool name."""

    normalized_query = user_query.strip().lower()

    if "state rejection" in normalized_query or (
        "state" in normalized_query and "rejection" in normalized_query
    ):
        return "state_rejections"
    if "market success" in normalized_query or (
        "market" in normalized_query and "success" in normalized_query
    ):
        return "market_success"
    if "retry" in normalized_query:
        return "retry_analysis"
    if "duration" in normalized_query:
        return "duration_anomalies"
    if "stuck" in normalized_query:
        return "stuck_ros"
    if "failed" in normalized_query or "failure" in normalized_query:
        return "failed_ros"
    if "rejection" in normalized_query or "reject" in normalized_query:
        return "org_rejections"
    return "stuck_ros"
