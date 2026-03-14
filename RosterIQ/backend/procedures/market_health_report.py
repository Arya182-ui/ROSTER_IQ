"""Procedure for correlating market success with same-period pipeline health."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import get_cached_datasets, get_stage_duration_anomalies


def _month_label(series: pd.Series) -> pd.Series:
    """Return month labels aligned to market CSV format (e.g., Jan-26)."""

    timestamps = pd.to_datetime(series, errors="coerce")
    return timestamps.dt.strftime("%b-%y")


def market_health_report(state: str | None = None) -> dict[str, Any]:
    """Correlate market success with same-state, same-month pipeline outcomes."""

    datasets = get_cached_datasets()
    roster_df = datasets.roster.copy()
    market_df = datasets.market.copy()

    if state:
        normalized_state = state.upper()
        roster_df = roster_df.loc[roster_df["CNT_STATE"].fillna("").eq(normalized_state)]
        market_df = market_df.loc[market_df["MARKET"].fillna("").eq(normalized_state)]
    else:
        normalized_state = "ALL"

    if roster_df.empty or market_df.empty:
        return {
            "summary": {
                "state": normalized_state,
                "count": 0,
                "note": "Insufficient roster or market data for correlation.",
            },
            "items": [],
        }

    roster_df["MONTH"] = _month_label(roster_df.get("LATEST_OBJECT_RUN_DT", pd.Series(dtype="object")))
    roster_df = roster_df.loc[roster_df["MONTH"].notna()].copy()

    if roster_df.empty:
        return {
            "summary": {
                "state": normalized_state,
                "count": 0,
                "note": "Roster data has no valid run timestamps for month-level correlation.",
            },
            "items": [],
        }

    roster_df["stuck_flag"] = roster_df.get("IS_STUCK", False).fillna(False).astype(bool).astype(int)
    roster_df["failed_flag"] = roster_df.get("IS_FAILED", False).fillna(False).astype(bool).astype(int)

    grouped_roster = (
        roster_df.groupby(["CNT_STATE", "MONTH"], dropna=False)
        .agg(
            total_ros=("RO_ID", "size"),
            stuck_ros=("stuck_flag", "sum"),
            failed_ros=("failed_flag", "sum"),
        )
        .reset_index()
        .rename(columns={"CNT_STATE": "MARKET"})
    )
    grouped_roster["stuck_rate_pct"] = (
        grouped_roster["stuck_ros"] / grouped_roster["total_ros"].replace(0, pd.NA) * 100
    ).fillna(0)
    grouped_roster["failed_rate_pct"] = (
        grouped_roster["failed_ros"] / grouped_roster["total_ros"].replace(0, pd.NA) * 100
    ).fillna(0)

    anomalies = get_stage_duration_anomalies(roster_df)
    anomaly_counts = pd.DataFrame(columns=["MARKET", "MONTH", "anomaly_count"])
    if not anomalies.empty:
        anomaly_source = roster_df[["RO_ID", "CNT_STATE", "MONTH"]].dropna(subset=["MONTH"])
        anomalies = anomalies[["RO_ID"]].merge(anomaly_source, on="RO_ID", how="left")
        anomaly_counts = (
            anomalies.groupby(["CNT_STATE", "MONTH"], dropna=False)
            .size()
            .reset_index(name="anomaly_count")
            .rename(columns={"CNT_STATE": "MARKET"})
        )

    market_scope = market_df[["MONTH", "MARKET", "SCS_PERCENT", "OVERALL_SCS_CNT", "OVERALL_FAIL_CNT"]].copy()
    market_scope["MONTH"] = market_scope["MONTH"].astype(str).str.strip()

    correlated = market_scope.merge(grouped_roster, on=["MARKET", "MONTH"], how="left")
    correlated = correlated.merge(anomaly_counts, on=["MARKET", "MONTH"], how="left")
    correlated["anomaly_count"] = correlated["anomaly_count"].fillna(0).astype(int)
    correlated["total_ros"] = correlated["total_ros"].fillna(0).astype(int)
    correlated["stuck_ros"] = correlated["stuck_ros"].fillna(0).astype(int)
    correlated["failed_ros"] = correlated["failed_ros"].fillna(0).astype(int)
    correlated["stuck_rate_pct"] = correlated["stuck_rate_pct"].fillna(0).round(2)
    correlated["failed_rate_pct"] = correlated["failed_rate_pct"].fillna(0).round(2)

    correlated["risk_score"] = (
        (100 - correlated["SCS_PERCENT"].fillna(0).astype(float)).clip(lower=0)
        + correlated["failed_rate_pct"]
        + correlated["stuck_rate_pct"] * 0.5
        + correlated["anomaly_count"]
    ).round(2)

    ranked = correlated.sort_values(["risk_score", "SCS_PERCENT"], ascending=[False, True])
    items = ranked.head(10).astype(object).where(pd.notna(ranked.head(10)), None).to_dict(orient="records")

    return {
        "summary": {
            "state": normalized_state,
            "count": int(len(correlated)),
            "latest_month": str(ranked.iloc[0]["MONTH"]) if not ranked.empty else None,
            "highest_risk_market": str(ranked.iloc[0]["MARKET"]) if not ranked.empty else None,
        },
        "items": items,
    }
