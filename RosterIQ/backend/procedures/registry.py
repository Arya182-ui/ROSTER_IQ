"""Registry and selector for named diagnostic procedures."""

from __future__ import annotations

from typing import Any, Callable

from backend.procedures.market_health_report import market_health_report
from backend.procedures.quality_drift_watch import quality_drift_watch
from backend.procedures.retry_effectiveness_analysis import retry_effectiveness_analysis
from backend.procedures.triage_stuck_ros import triage_stuck_ros


ProcedureCallable = Callable[..., dict[str, Any]]


PROCEDURE_REGISTRY: dict[str, ProcedureCallable] = {
    "triage_stuck_ros": triage_stuck_ros,
    "market_health_report": market_health_report,
    "retry_effectiveness_analysis": retry_effectiveness_analysis,
    "quality_drift_watch": quality_drift_watch,
}


PROCEDURE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "triage_stuck_ros": ("triage", "stuck", "escalation", "priority"),
    "market_health_report": ("market health", "correlate", "state report", "market report"),
    "retry_effectiveness_analysis": ("retry", "reprocess", "retry lift", "retry effectiveness"),
    "quality_drift_watch": ("drift", "trend", "declining", "worsening", "anomaly trend"),
}


def select_procedure_for_query(query: str) -> str | None:
    """Return the first matching procedure name for a natural-language query."""

    normalized = (query or "").strip().lower()
    if not normalized:
        return None

    for procedure_name, keywords in PROCEDURE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return procedure_name
    return None


def run_procedure(name: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a named procedure and return a standard payload shape."""

    procedure = PROCEDURE_REGISTRY[name]
    result = procedure(**kwargs)
    items = result.get("items", []) if isinstance(result, dict) else []
    summary = result.get("summary", {}) if isinstance(result, dict) else {}
    return {
        "tool_name": name,
        "count": int(len(items)),
        "data": items,
        "procedure_summary": summary,
    }
