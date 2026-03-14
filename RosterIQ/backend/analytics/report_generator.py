"""Structured operational reporting for pipeline health investigations."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import (
    get_cached_datasets,
    get_failed_ros,
    get_market_success_rates,
    get_retry_operations,
    get_stage_duration_anomalies,
    get_stuck_ros,
)
from backend.procedures.market_health_report import market_health_report


STAGE_HEALTH_MAP = {
    "PRE_PROCESSING": "PRE_PROCESSING_HEALTH",
    "MAPPING_APROVAL": "MAPPING_APROVAL_HEALTH",
    "ISF_GEN": "ISF_GEN_HEALTH",
    "DART_GEN": "DART_GEN_HEALTH",
    "DART_REVIEW": "DART_REVIEW_HEALTH",
    "DART_UI_VALIDATION": "DART_UI_VALIDATION_HEALTH",
    "SPS_LOAD": "SPS_LOAD_HEALTH",
}


def _filter_roster_df(state: str | None = None, org: str | None = None) -> pd.DataFrame:
    """Return a filtered roster dataframe for the requested scope."""

    roster_df = get_cached_datasets().roster.copy()
    if state:
        roster_df = roster_df.loc[roster_df["CNT_STATE"].fillna("").eq(state.upper())]
    if org:
        roster_df = roster_df.loc[
            roster_df["ORG_NM"].fillna("").str.contains(org, case=False, regex=False)
        ]
    return roster_df.reset_index(drop=True)


def _filter_market_df(state: str | None = None) -> pd.DataFrame:
    """Return a filtered market dataframe for the requested state scope."""

    market_df = get_cached_datasets().market.copy()
    if state:
        market_df = market_df.loc[market_df["MARKET"].fillna("").eq(state.upper())]
    return market_df.reset_index(drop=True)


def _normalize_health(value: Any) -> str:
    """Normalize raw health values to Green, Yellow, Red, or Unknown."""

    if value is None or pd.isna(value):
        return "Unknown"
    text = str(value).strip().title()
    if text in {"Green", "Yellow", "Red"}:
        return text.upper()
    return "Unknown"


def _issue_health(row: pd.Series) -> str:
    """Resolve a health flag for an anomalous roster row."""

    mapped_column = STAGE_HEALTH_MAP.get(str(row.get("stage_name", "")))
    if mapped_column and mapped_column in row.index:
        resolved = _normalize_health(row.get(mapped_column))
        if resolved != "Unknown":
            return resolved

    ratio = float(row.get("anomaly_ratio", 0) or 0)
    if ratio >= 3:
        return "RED"
    if ratio >= 2:
        return "YELLOW"
    return "GREEN"


def _market_trend_label(success_rates: list[float]) -> str:
    """Return a simple qualitative trend label for recent success rates."""

    if len(success_rates) < 2:
        return "stable"
    if success_rates[-1] > success_rates[-2]:
        return "improving"
    if success_rates[-1] < success_rates[-2]:
        return "declining"
    return "stable"


def _market_context(state: str | None, market_df: pd.DataFrame) -> dict[str, Any]:
    """Return summarized market success context for the requested scope."""

    if market_df.empty:
        return {
            "market": state.upper() if state else "ALL",
            "success_rate": 0.0,
            "trend": "stable",
        }

    if state:
        scoped_market = get_market_success_rates(market_df).sort_values("MONTH")
        success_rates = scoped_market["SCS_PERCENT"].fillna(0).astype(float).tolist()
        latest_rate = float(success_rates[-1]) if success_rates else 0.0
        return {
            "market": state.upper(),
            "success_rate": round(latest_rate, 2),
            "trend": _market_trend_label(success_rates),
        }

    grouped = (
        market_df.groupby("MONTH", dropna=False)
        .agg(overall_success=("OVERALL_SCS_CNT", "sum"), overall_fail=("OVERALL_FAIL_CNT", "sum"))
        .reset_index()
        .sort_values("MONTH")
    )
    grouped["success_rate"] = (
        grouped["overall_success"]
        / (grouped["overall_success"] + grouped["overall_fail"]).replace(0, pd.NA)
        * 100
    ).fillna(0)
    success_rates = grouped["success_rate"].astype(float).tolist()
    latest_rate = float(success_rates[-1]) if success_rates else 0.0
    return {
        "market": "ALL",
        "success_rate": round(latest_rate, 2),
        "trend": _market_trend_label(success_rates),
    }


def _retry_effectiveness(roster_df: pd.DataFrame) -> dict[str, Any]:
    """Summarize retry outcomes for the requested roster scope."""

    retry_df = get_retry_operations(roster_df)
    if retry_df.empty:
        return {
            "retry_volume": 0,
            "retry_success_rate": 0.0,
            "trend": "insufficient_data",
        }

    failed_retries = retry_df["IS_FAILED"].fillna(False).astype(bool)
    retry_volume = int(len(retry_df))
    retry_success_rate = round(((~failed_retries).sum() / retry_volume) * 100, 2)
    trend = "effective" if retry_success_rate >= 80 else "needs_attention"
    return {
        "retry_volume": retry_volume,
        "retry_success_rate": retry_success_rate,
        "trend": trend,
    }


def _top_problem_orgs(roster_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return the top organizations contributing to failures within scope."""

    failed_df = get_failed_ros(roster_df)
    if failed_df.empty:
        return []

    grouped = (
        failed_df.groupby("ORG_NM", dropna=False)
        .size()
        .reset_index(name="failure_count")
        .sort_values(["failure_count", "ORG_NM"], ascending=[False, True])
        .head(5)
    )
    return [
        {"org": str(row["ORG_NM"] or "Unknown"), "failure_count": int(row["failure_count"])}
        for _, row in grouped.iterrows()
    ]


def _recommended_actions(
    anomalies_df: pd.DataFrame,
    failed_df: pd.DataFrame,
    retry_summary: dict[str, Any],
    top_problem_orgs: list[dict[str, Any]],
) -> list[str]:
    """Return prioritized recommended actions based on report signals."""

    actions: list[str] = []

    if not anomalies_df.empty:
        dominant_stage = str(anomalies_df["stage_name"].value_counts().idxmax())
        actions.append(f"Investigate {dominant_stage} delays")

    failure_statuses = failed_df.get("FAILURE_STATUS") if "FAILURE_STATUS" in failed_df.columns else None
    if failure_statuses is not None and failure_statuses.fillna("").str.contains(
        "validation|format|schema|reject", case=False, regex=True
    ).any():
        actions.append("Validate provider roster submission format")

    if retry_summary["retry_volume"] > 0 and retry_summary["retry_success_rate"] < 80:
        actions.append("Review retry handling for repeated operational failures")

    if top_problem_orgs:
        actions.append(f"Prioritize remediation with {top_problem_orgs[0]['org']}")

    if not actions:
        actions.append("Continue monitoring pipeline health for new anomalies")

    return actions[:4]


def generate_pipeline_health_report(
    state: str | None = None,
    org: str | None = None,
) -> dict[str, Any]:
    """Generate a structured operational report for the requested scope."""

    roster_df = _filter_roster_df(state=state, org=org)
    market_df = _filter_market_df(state=state)

    stuck_df = get_stuck_ros(roster_df)
    failed_df = get_failed_ros(roster_df)
    anomalies_df = get_stage_duration_anomalies(roster_df)
    retry_summary = _retry_effectiveness(roster_df)
    top_problem_orgs = _top_problem_orgs(roster_df)
    cross_table = market_health_report(state=state)

    issue_source = anomalies_df.copy()
    if not issue_source.empty:
        issue_source = issue_source.merge(
            roster_df[[column for column in ["RO_ID", *STAGE_HEALTH_MAP.values()] if column in roster_df.columns]],
            on="RO_ID",
            how="left",
        )

    pipeline_issues = []
    for _, row in issue_source.head(10).iterrows():
        pipeline_issues.append(
            {
                "ro_id": str(row.get("RO_ID", "")),
                "stage": str(row.get("stage_name", row.get("LATEST_STAGE_NM", "Unknown"))),
                "duration_deviation": round(float(row.get("anomaly_ratio", 0) or 0), 2),
                "health": _issue_health(row),
            }
        )

    return {
        "summary": {
            "state": state.upper() if state else "ALL",
            "organization": org,
            "total_ros": int(len(roster_df)),
            "stuck_ros": int(len(stuck_df)),
            "failed_ros": int(len(failed_df)),
        },
        "pipeline_issues": pipeline_issues,
        "market_context": _market_context(state=state, market_df=market_df),
        "cross_table_correlation": {
            "summary": cross_table.get("summary", {}),
            "top_rows": cross_table.get("items", [])[:5],
        },
        "retry_effectiveness": retry_summary,
        "top_problem_orgs": top_problem_orgs,
        "recommended_actions": _recommended_actions(
            anomalies_df=anomalies_df,
            failed_df=failed_df,
            retry_summary=retry_summary,
            top_problem_orgs=top_problem_orgs,
        ),
    }
