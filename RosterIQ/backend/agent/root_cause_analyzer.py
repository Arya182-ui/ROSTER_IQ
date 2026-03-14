"""Root-cause analysis utilities for market performance investigation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import get_cached_datasets, get_stage_duration_anomalies


def _state_roster_proxy_rates(state: str) -> pd.DataFrame:
    """Return organization-level failure and rejection proxy rates for a state."""

    roster_df = get_cached_datasets().roster.copy()
    state_df = roster_df.loc[roster_df["CNT_STATE"].fillna("").eq(state.upper())].copy()
    if state_df.empty:
        return pd.DataFrame(columns=["ORG_NM", "failed_rosters", "rejected_rosters", "total_rosters", "combined_issue_rate"])

    state_df["rejected_proxy"] = (
        state_df["LATEST_STAGE_NM"].fillna("").eq("REJECTED")
        | state_df["FAILURE_STATUS"].fillna("").str.contains("reject", case=False, regex=False)
    ).astype(int)
    state_df["failed_proxy"] = state_df["IS_FAILED"].fillna(False).astype(int)

    grouped = (
        state_df.groupby("ORG_NM", dropna=False)
        .agg(
            failed_rosters=("failed_proxy", "sum"),
            rejected_rosters=("rejected_proxy", "sum"),
            total_rosters=("ORG_NM", "size"),
        )
        .reset_index()
    )
    grouped["combined_issue_rate"] = (
        (grouped["failed_rosters"] + grouped["rejected_rosters"])
        / grouped["total_rosters"].replace(0, pd.NA)
        * 100
    ).fillna(0)
    return grouped.sort_values(["combined_issue_rate", "failed_rosters", "rejected_rosters"], ascending=False)


def _state_stage_issue(state: str) -> str:
    """Return the most prominent anomalous stage for a state."""

    anomalies = get_stage_duration_anomalies()
    if anomalies.empty:
        return "Unknown"
    state_anomalies = anomalies.loc[anomalies["CNT_STATE"].fillna("").eq(state.upper())].copy()
    if state_anomalies.empty:
        return "Unknown"
    stage_counts = (
        state_anomalies.groupby("stage_name")
        .agg(anomaly_count=("stage_name", "size"), max_ratio=("anomaly_ratio", "max"))
        .reset_index()
        .sort_values(["anomaly_count", "max_ratio"], ascending=False)
    )
    return str(stage_counts.iloc[0]["stage_name"])


def _confidence_score(success_rate_drop: float, primary_org: str, likely_stage_issue: str) -> float:
    """Return a lightweight confidence score for the root-cause narrative."""

    score = 0.35
    if success_rate_drop > 0:
        score += 0.2
    if success_rate_drop >= 3:
        score += 0.1
    if primary_org != "Unknown":
        score += 0.2
    if likely_stage_issue != "Unknown":
        score += 0.15
    return round(min(score, 0.95), 2)


def analyze_market_drop(state: str) -> dict[str, Any]:
    """Correlate market decline with file-level issues for a given state."""

    market_df = get_cached_datasets().market.copy()
    state = state.upper()
    state_market = (
        market_df.loc[market_df["MARKET"].fillna("").eq(state)]
        .sort_values("MONTH")
        .reset_index(drop=True)
    )

    if state_market.empty:
        return {
            "market": state,
            "success_rate_drop": 0.0,
            "primary_org": "Unknown",
            "likely_stage_issue": "Unknown",
            "confidence_score": 0.0,
            "explanation": f"No market performance data was found for {state}.",
        }

    latest_rate = float(state_market.iloc[-1]["SCS_PERCENT"])
    previous_rate = float(state_market.iloc[-2]["SCS_PERCENT"]) if len(state_market) > 1 else latest_rate
    success_rate_drop = round(max(previous_rate - latest_rate, 0.0), 2)

    org_rates = _state_roster_proxy_rates(state)
    if org_rates.empty:
        primary_org = "Unknown"
        primary_issue_rate = 0.0
    else:
        primary_org = str(org_rates.iloc[0]["ORG_NM"])
        primary_issue_rate = round(float(org_rates.iloc[0]["combined_issue_rate"]), 2)

    likely_stage_issue = _state_stage_issue(state)
    confidence_score = _confidence_score(success_rate_drop, primary_org, likely_stage_issue)

    if success_rate_drop > 0:
        explanation = (
            f"Market {state} declined by {success_rate_drop} points versus the prior month. "
            f"{primary_org} shows the highest failure or rejection proxy rate in the state at {primary_issue_rate}%. "
            f"The strongest operational anomaly is in {likely_stage_issue}, which likely contributed to the market slowdown."
        )
    else:
        explanation = (
            f"Market {state} does not show a recent success-rate drop, but {primary_org} still has the highest issue proxy rate in the state. "
            f"The most visible anomalous stage is {likely_stage_issue}."
        )

    return {
        "market": state,
        "success_rate_drop": success_rate_drop,
        "primary_org": primary_org,
        "likely_stage_issue": likely_stage_issue,
        "confidence_score": confidence_score,
        "explanation": explanation,
    }
