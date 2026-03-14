"""FastAPI routes for the RosterIQ backend."""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from backend.agent.agent_core import run_agent
from backend.agent.root_cause_analyzer import analyze_market_drop
from backend.analytics.report_generator import generate_pipeline_health_report
from backend.analytics.visualization_service import (
    get_market_success_trend,
    get_pipeline_health_summary,
    get_record_quality_breakdown,
    get_retry_effectiveness,
)
from backend.data_engine.data_engine import (
    get_failed_ros,
    get_market_success_rates,
    get_org_rejection_rates,
    get_retry_operations,
    get_stage_duration_anomalies,
    get_state_rejection_rates,
    get_stuck_ros,
)
from backend.memory.firebase_memory import get_recent_investigations
from backend.memory.firebase_memory import get_memory_backend_status
from backend.procedures.registry import PROCEDURE_REGISTRY, run_procedure

router = APIRouter()


class AskRequest(BaseModel):
    """Request body for natural-language agent queries."""

    query: str


class ProcedureRunRequest(BaseModel):
    """Request body for running a named diagnostic procedure."""

    state: str | None = None


def _dataframe_payload(df: pd.DataFrame) -> dict[str, Any]:
    """Convert a pandas DataFrame into a JSON-safe API payload."""

    normalized_df = df.astype(object).where(pd.notna(df), None)
    return {
        "count": int(len(normalized_df)),
        "items": jsonable_encoder(normalized_df.to_dict(orient="records")),
    }


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple health status for the backend service."""

    return {"status": "ok", "service": "RosterIQ API"}


@router.get("/stuck-ros")
def read_stuck_ros() -> dict[str, Any]:
    """Return stuck roster operations."""

    return _dataframe_payload(get_stuck_ros())


@router.get("/failed-ros")
def read_failed_ros() -> dict[str, Any]:
    """Return failed roster operations."""

    return _dataframe_payload(get_failed_ros())


@router.get("/org-rejections")
def read_org_rejections() -> dict[str, Any]:
    """Return organization-level rejection metrics."""

    return _dataframe_payload(get_org_rejection_rates())


@router.get("/state-rejections")
def read_state_rejections() -> dict[str, Any]:
    """Return state-level rejection metrics."""

    return _dataframe_payload(get_state_rejection_rates())


@router.get("/market-success")
def read_market_success() -> dict[str, Any]:
    """Return market success-rate data."""

    return _dataframe_payload(get_market_success_rates())


@router.get("/retry-analysis")
def read_retry_analysis() -> dict[str, Any]:
    """Return retry-operation details."""

    return _dataframe_payload(get_retry_operations())


@router.get("/duration-anomalies")
def read_duration_anomalies() -> dict[str, Any]:
    """Return stage duration anomalies."""

    return _dataframe_payload(get_stage_duration_anomalies())


@router.get("/analytics/pipeline-health")
def read_pipeline_health() -> list[dict[str, Any]]:
    """Return chart-ready pipeline health distribution data."""

    return get_pipeline_health_summary()


@router.get("/analytics/record-quality")
def read_record_quality() -> dict[str, float]:
    """Return chart-ready record quality distribution data."""

    return get_record_quality_breakdown()


@router.get("/analytics/market-trend")
def read_market_trend() -> list[dict[str, Any]]:
    """Return chart-ready market success trend data."""

    return get_market_success_trend()


@router.get("/analytics/retry-analysis")
def read_retry_effectiveness() -> list[dict[str, Any]]:
    """Return chart-ready retry effectiveness data."""

    return get_retry_effectiveness()


@router.get("/analytics/root-cause/{state}")
def read_root_cause(state: str) -> dict[str, Any]:
    """Return market root-cause analysis for a given state."""

    return analyze_market_drop(state)


@router.get("/analytics/pipeline-report")
def read_pipeline_report(
    state: str | None = Query(default=None),
    organization: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return a structured operational pipeline report for the requested scope."""

    return generate_pipeline_health_report(state=state, org=organization)


@router.get("/investigations/history")
def read_investigation_history(limit: int = Query(default=12, ge=1, le=50)) -> dict[str, Any]:
    """Return recent episodic investigation history for the frontend."""

    try:
        return {"items": get_recent_investigations(limit=limit)}
    except Exception:
        return {"items": []}


@router.get("/memory/status")
def read_memory_status() -> dict[str, Any]:
    """Return active memory backend health and fallback status."""

    return get_memory_backend_status()


@router.get("/procedures")
def read_procedures() -> dict[str, Any]:
    """Return the available named diagnostic procedures."""

    names = sorted(PROCEDURE_REGISTRY.keys())
    return {"count": len(names), "items": names}


@router.post("/procedures/{name}/run")
def run_named_procedure(name: str, request: ProcedureRunRequest) -> dict[str, Any]:
    """Run a named diagnostic procedure for direct demonstration or debugging."""

    if name not in PROCEDURE_REGISTRY:
        return {
            "tool_name": name,
            "count": 0,
            "data": [],
            "error": "Unknown procedure",
        }

    kwargs: dict[str, Any] = {}
    if request.state and name != "triage_stuck_ros":
        kwargs["state"] = request.state.upper()
    return run_procedure(name=name, **kwargs)


@router.post("/ask")
def ask_agent(request: AskRequest) -> dict[str, Any]:
    """Run the RosterIQ reasoning agent against a natural-language query."""

    agent_result = run_agent(request.query)
    return {
        "analysis": agent_result["analysis"],
        "data": agent_result["data"],
        "tool_used": agent_result["tool_used"],
        "count": agent_result["count"],
        "report": agent_result.get("report"),
        "sources": agent_result.get("sources", []),
        "state_change": agent_result.get("state_change"),
    }
