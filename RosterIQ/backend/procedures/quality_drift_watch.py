"""Procedure for spotting quality drift in failure and rejection signals over time."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import get_cached_datasets


def _month_label(series: pd.Series) -> pd.Series:
    """Return month labels aligned to market CSV format (e.g., Jan-26)."""

    timestamps = pd.to_datetime(series, errors="coerce")
    return timestamps.dt.strftime("%b-%y")


def quality_drift_watch(state: str | None = None) -> dict[str, Any]:
    """Track month-over-month drift in failed and rejected roster outcomes."""

    roster_df = get_cached_datasets().roster.copy()
    if state:
        state = state.upper()
        roster_df = roster_df.loc[roster_df["CNT_STATE"].fillna("").eq(state)]

    if roster_df.empty:
        return {
            "summary": {"count": 0, "state": state or "ALL"},
            "items": [],
        }

    roster_df["MONTH"] = _month_label(roster_df.get("LATEST_OBJECT_RUN_DT", pd.Series(dtype="object")))
    roster_df = roster_df.loc[roster_df["MONTH"].notna()].copy()
    if roster_df.empty:
        return {
            "summary": {"count": 0, "state": state or "ALL"},
            "items": [],
        }

    roster_df["failed_flag"] = roster_df.get("IS_FAILED", False).fillna(False).astype(bool).astype(int)
    roster_df["rejected_flag"] = (
        roster_df.get("FAILURE_STATUS", "").fillna("").astype(str).str.contains("reject|validation", case=False, regex=True)
    ).astype(int)
    roster_df["stuck_flag"] = roster_df.get("IS_STUCK", False).fillna(False).astype(bool).astype(int)

    grouped = (
        roster_df.groupby(["CNT_STATE", "MONTH"], dropna=False)
        .agg(
            total_ros=("RO_ID", "size"),
            failed_ros=("failed_flag", "sum"),
            rejected_ros=("rejected_flag", "sum"),
            stuck_ros=("stuck_flag", "sum"),
        )
        .reset_index()
    )
    grouped["failed_rate_pct"] = (
        grouped["failed_ros"] / grouped["total_ros"].replace(0, pd.NA) * 100
    ).fillna(0)
    grouped["rejected_rate_pct"] = (
        grouped["rejected_ros"] / grouped["total_ros"].replace(0, pd.NA) * 100
    ).fillna(0)
    grouped["stuck_rate_pct"] = (
        grouped["stuck_ros"] / grouped["total_ros"].replace(0, pd.NA) * 100
    ).fillna(0)

    grouped = grouped.sort_values(["CNT_STATE", "MONTH"])
    grouped["failed_rate_delta"] = grouped.groupby("CNT_STATE")["failed_rate_pct"].diff().fillna(0)
    grouped["rejected_rate_delta"] = grouped.groupby("CNT_STATE")["rejected_rate_pct"].diff().fillna(0)
    grouped["stuck_rate_delta"] = grouped.groupby("CNT_STATE")["stuck_rate_pct"].diff().fillna(0)

    grouped["drift_score"] = (
        grouped["failed_rate_delta"].clip(lower=0) * 1.2
        + grouped["rejected_rate_delta"].clip(lower=0)
        + grouped["stuck_rate_delta"].clip(lower=0) * 0.8
    ).round(2)

    ranked = grouped.sort_values(["drift_score", "failed_rate_delta", "rejected_rate_delta"], ascending=[False, False, False])
    items = ranked.head(10).astype(object).where(pd.notna(ranked.head(10)), None).to_dict(orient="records")

    return {
        "summary": {
            "count": int(len(grouped)),
            "state": state or "ALL",
            "max_drift_score": float(ranked.iloc[0]["drift_score"]) if not ranked.empty else 0.0,
        },
        "items": items,
    }
