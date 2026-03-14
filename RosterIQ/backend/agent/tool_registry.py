"""Registry of analytics tools available to the RosterIQ agent."""

from __future__ import annotations

from typing import Any, Callable

from backend.tools.analytics_tools import (
    tool_get_duration_anomalies,
    tool_get_failed_ros,
    tool_get_market_success,
    tool_get_org_rejections,
    tool_get_retry_analysis,
    tool_get_state_rejections,
    tool_get_stuck_ros,
)
from backend.tools.web_search_tool import search_web


ToolCallable = Callable[..., dict[str, Any]]


TOOL_REGISTRY: dict[str, ToolCallable] = {
    "stuck_ros": tool_get_stuck_ros,
    "failed_ros": tool_get_failed_ros,
    "org_rejections": tool_get_org_rejections,
    "state_rejections": tool_get_state_rejections,
    "market_success": tool_get_market_success,
    "retry_analysis": tool_get_retry_analysis,
    "duration_anomalies": tool_get_duration_anomalies,
    "web_search": search_web,
}
