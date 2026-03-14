"""Agent-facing wrappers around the core roster analytics functions."""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi.encoders import jsonable_encoder

from backend.data_engine.data_engine import (
    get_failed_ros,
    get_market_success_rates,
    get_org_rejection_rates,
    get_retry_operations,
    get_stage_duration_anomalies,
    get_state_rejection_rates,
    get_stuck_ros,
)



def _dataframe_to_json_payload(tool_name: str, df: pd.DataFrame) -> dict[str, Any]:
    """Convert a dataframe into a JSON-safe structured tool result."""

    normalized_df = df.astype(object).where(pd.notna(df), None)
    return {
        "tool_name": tool_name,
        "count": int(len(normalized_df)),
        "data": jsonable_encoder(normalized_df.to_dict(orient="records")),
    }



def tool_get_stuck_ros() -> dict[str, Any]:
    """Return structured stuck-roster analytics output."""

    return _dataframe_to_json_payload("stuck_ros", get_stuck_ros())



def tool_get_failed_ros() -> dict[str, Any]:
    """Return structured failed-roster analytics output."""

    return _dataframe_to_json_payload("failed_ros", get_failed_ros())



def tool_get_org_rejections() -> dict[str, Any]:
    """Return structured organization rejection analytics output."""

    return _dataframe_to_json_payload("org_rejections", get_org_rejection_rates())



def tool_get_state_rejections() -> dict[str, Any]:
    """Return structured state rejection analytics output."""

    return _dataframe_to_json_payload("state_rejections", get_state_rejection_rates())



def tool_get_market_success() -> dict[str, Any]:
    """Return structured market success analytics output."""

    return _dataframe_to_json_payload("market_success", get_market_success_rates())



def tool_get_retry_analysis() -> dict[str, Any]:
    """Return structured retry analytics output."""

    return _dataframe_to_json_payload("retry_analysis", get_retry_operations())



def tool_get_duration_anomalies() -> dict[str, Any]:
    """Return structured duration anomaly analytics output."""

    return _dataframe_to_json_payload("duration_anomalies", get_stage_duration_anomalies())
