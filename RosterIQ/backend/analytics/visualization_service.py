"""Visualization-ready analytics services for the RosterIQ dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import get_cached_datasets


STAGE_HEALTH_COLUMN_MAP = {
    "INGESTION": "PRE_PROCESSING_HEALTH",
    "PRE_PROCESSING": "PRE_PROCESSING_HEALTH",
    "MAPPING_APPROVAL": "MAPPING_APROVAL_HEALTH",
    "ISF_GENERATION": "ISF_GEN_HEALTH",
    "DART_GENERATION": "DART_GEN_HEALTH",
    "DART_REVIEW": "DART_REVIEW_HEALTH",
    "DART_UI_VALIDATION": "DART_UI_VALIDATION_HEALTH",
    "SPS_LOAD": "SPS_LOAD_HEALTH",
    "RESOLVED": "SPS_LOAD_HEALTH",
}

HEALTH_COLUMNS = [
    "PRE_PROCESSING_HEALTH",
    "MAPPING_APROVAL_HEALTH",
    "ISF_GEN_HEALTH",
    "DART_GEN_HEALTH",
    "DART_REVIEW_HEALTH",
    "DART_UI_VALIDATION_HEALTH",
    "SPS_LOAD_HEALTH",
]



def _datasets():
    """Return the cached source datasets for analytics services."""

    return get_cached_datasets()



def _normalize_health(value: Any) -> str:
    """Normalize health values to Green, Yellow, Red, or Unknown."""

    if value is None or pd.isna(value):
        return "Unknown"
    text = str(value).strip().title()
    if text in {"Green", "Yellow", "Red"}:
        return text
    return "Unknown"



def _worst_health(row: pd.Series) -> str:
    """Return the most severe health flag available on a roster row."""

    severity = {"Red": 3, "Yellow": 2, "Green": 1}
    values = [_normalize_health(row.get(column)) for column in HEALTH_COLUMNS if column in row.index]
    ranked = [value for value in values if value in severity]
    if not ranked:
        return "Unknown"
    return max(ranked, key=lambda item: severity[item])



def get_pipeline_health_summary() -> list[dict[str, Any]]:
    """Return stage-level health counts for stacked bar chart rendering."""

    roster_df = _datasets().roster.copy()
    roster_df["stage"] = roster_df["LATEST_STAGE_NM"].fillna("UNKNOWN_STAGE").astype(str)

    def resolve_stage_health(row: pd.Series) -> str:
        stage_name = row["stage"]
        mapped_column = STAGE_HEALTH_COLUMN_MAP.get(stage_name)
        if mapped_column and mapped_column in row.index:
            normalized = _normalize_health(row.get(mapped_column))
            if normalized != "Unknown":
                return normalized
        return _worst_health(row)

    roster_df["resolved_health"] = roster_df.apply(resolve_stage_health, axis=1)

    grouped = (
        roster_df.groupby(["stage", "resolved_health"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    return [
        {
            "stage": row["stage"],
            "green": int(row.get("Green", 0)),
            "yellow": int(row.get("Yellow", 0)),
            "red": int(row.get("Red", 0)),
        }
        for _, row in grouped.iterrows()
    ]



def get_record_quality_breakdown() -> dict[str, float]:
    """Return percentage distribution for record-quality outcomes.

    If record-count columns are unavailable, the function falls back to roster-
    level proxy categories based on failure flags and stage/status signals.
    """

    roster_df = _datasets().roster.copy()

    if {"TOT_REC_CNT", "SCS_REC_CNT", "FAIL_REC_CNT", "SKIP_REC_CNT", "REJ_REC_CNT"}.issubset(roster_df.columns):
        total = float(roster_df["TOT_REC_CNT"].fillna(0).sum())
        success = float(roster_df["SCS_REC_CNT"].fillna(0).sum())
        fail = float(roster_df["FAIL_REC_CNT"].fillna(0).sum())
        skip = float(roster_df["SKIP_REC_CNT"].fillna(0).sum())
        reject = float(roster_df["REJ_REC_CNT"].fillna(0).sum())
    else:
        total = float(len(roster_df))
        reject_mask = (
            roster_df["LATEST_STAGE_NM"].fillna("").eq("REJECTED")
            | roster_df["FAILURE_STATUS"].fillna("").str.contains("reject", case=False, regex=False)
        )
        fail_mask = roster_df["IS_FAILED"].fillna(False).astype(bool) & ~reject_mask
        success_mask = (
            roster_df["LATEST_STAGE_NM"].fillna("").isin(["RESOLVED", "SPS_LOAD"])
            & ~fail_mask
            & ~reject_mask
        )
        skip_mask = ~(reject_mask | fail_mask | success_mask)

        success = float(success_mask.sum())
        fail = float(fail_mask.sum())
        skip = float(skip_mask.sum())
        reject = float(reject_mask.sum())

    if total <= 0:
        return {"success": 0.0, "fail": 0.0, "skip": 0.0, "reject": 0.0}

    return {
        "success": round((success / total) * 100, 2),
        "fail": round((fail / total) * 100, 2),
        "skip": round((skip / total) * 100, 2),
        "reject": round((reject / total) * 100, 2),
    }



def get_market_success_trend() -> list[dict[str, Any]]:
    """Return a monthly weighted market success-rate time series."""

    market_df = _datasets().market.copy()
    grouped = (
        market_df.groupby("MONTH", dropna=False)
        .agg(
            overall_success=("OVERALL_SCS_CNT", "sum"),
            overall_fail=("OVERALL_FAIL_CNT", "sum"),
        )
        .reset_index()
        .sort_values("MONTH")
    )
    grouped["success_rate"] = (
        grouped["overall_success"]
        / (grouped["overall_success"] + grouped["overall_fail"]).replace(0, pd.NA)
        * 100
    ).fillna(0)
    grouped["month_label"] = pd.to_datetime(grouped["MONTH"]).dt.strftime("%b-%y")

    return [
        {"month": row["month_label"], "success_rate": round(float(row["success_rate"]), 2)}
        for _, row in grouped.iterrows()
    ]



def get_retry_effectiveness() -> list[dict[str, Any]]:
    """Return first-pass versus retry success rates for comparison charts."""

    market_df = _datasets().market.copy()
    first_success = float(market_df["FIRST_ITER_SCS_CNT"].fillna(0).sum())
    first_fail = float(market_df["FIRST_ITER_FAIL_CNT"].fillna(0).sum())
    retry_success = float(market_df["NEXT_ITER_SCS_CNT"].fillna(0).sum())
    retry_fail = float(market_df["NEXT_ITER_FAIL_CNT"].fillna(0).sum())

    first_rate = (first_success / (first_success + first_fail) * 100) if (first_success + first_fail) else 0.0
    retry_rate = (retry_success / (retry_success + retry_fail) * 100) if (retry_success + retry_fail) else 0.0

    return [
        {"stage": "first_pass", "success": round(first_rate, 2)},
        {"stage": "retry", "success": round(retry_rate, 2)},
    ]
