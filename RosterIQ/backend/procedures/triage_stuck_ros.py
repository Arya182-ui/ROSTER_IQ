"""Procedure for ranking stuck roster operations by operational severity."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import get_cached_datasets


HEALTH_COLUMNS = [
    "PRE_PROCESSING_HEALTH",
    "MAPPING_APROVAL_HEALTH",
    "ISF_GEN_HEALTH",
    "DART_GEN_HEALTH",
    "DART_REVIEW_HEALTH",
    "DART_UI_VALIDATION_HEALTH",
    "SPS_LOAD_HEALTH",
]

DURATION_COLUMNS = [
    "PRE_PROCESSING_DURATION",
    "MAPPING_APROVAL_DURATION",
    "ISF_GEN_DURATION",
    "DART_GEN_DURATION",
    "DART_REVIEW_DURATION",
    "DART_UI_VALIDATION_DURATION",
    "SPS_LOAD_DURATION",
]



def triage_stuck_ros() -> dict[str, Any]:
    """Return a severity-ranked view of currently stuck roster operations."""

    roster_df = get_cached_datasets().roster.copy()
    if "IS_STUCK" not in roster_df.columns:
        return {"summary": {"count": 0}, "items": []}

    stuck_df = roster_df.loc[roster_df["IS_STUCK"] == True].copy()
    if stuck_df.empty:
        return {"summary": {"count": 0}, "items": []}

    health_columns = [column for column in HEALTH_COLUMNS if column in stuck_df.columns]
    duration_columns = [column for column in DURATION_COLUMNS if column in stuck_df.columns]

    if health_columns:
        stuck_df["red_flag_count"] = stuck_df[health_columns].apply(
            lambda row: row.astype(str).str.upper().eq("RED").sum(),
            axis=1,
        )
    else:
        stuck_df["red_flag_count"] = 0

    if duration_columns:
        stuck_df["longest_stage_duration"] = stuck_df[duration_columns].max(axis=1, skipna=True).fillna(0)
        stuck_df["longest_stage_name"] = (
            stuck_df[duration_columns]
            .idxmax(axis=1, skipna=True)
            .fillna("UNKNOWN_STAGE")
            .str.replace("_DURATION", "", regex=False)
        )
    else:
        stuck_df["longest_stage_duration"] = 0.0
        stuck_df["longest_stage_name"] = "UNKNOWN_STAGE"

    stuck_df["severity_score"] = (
        stuck_df["red_flag_count"] * 1000 + stuck_df["longest_stage_duration"].fillna(0)
    )
    stuck_df["priority"] = pd.cut(
        stuck_df["red_flag_count"],
        bins=[-1, 0, 1, 99],
        labels=["medium", "high", "critical"],
    ).astype(str)

    output_columns = [
        column
        for column in [
            "RO_ID",
            "ORG_NM",
            "CNT_STATE",
            "LATEST_STAGE_NM",
            "FAILURE_STATUS",
            "red_flag_count",
            "longest_stage_name",
            "longest_stage_duration",
            "severity_score",
            "priority",
            "LATEST_OBJECT_RUN_DT",
        ]
        if column in stuck_df.columns
    ]
    ranked_df = stuck_df[output_columns].sort_values(
        ["severity_score", "red_flag_count", "longest_stage_duration"],
        ascending=[False, False, False],
        na_position="last",
    )

    top_priority = ranked_df.head(10).astype(object).where(pd.notna(ranked_df.head(10)), None)
    return {
        "summary": {
            "count": int(len(ranked_df)),
            "critical_count": int((ranked_df["priority"] == "critical").sum()),
            "high_count": int((ranked_df["priority"] == "high").sum()),
            "medium_count": int((ranked_df["priority"] == "medium").sum()),
        },
        "items": top_priority.to_dict(orient="records"),
    }
