"""Procedure for evaluating whether retries recover outcomes or add overhead."""

from __future__ import annotations

from typing import Any

import pandas as pd

from backend.data_engine.data_engine import get_cached_datasets


def retry_effectiveness_analysis(state: str | None = None) -> dict[str, Any]:
    """Return retry lift and retry overhead metrics by market."""

    datasets = get_cached_datasets()
    roster_df = datasets.roster.copy()
    market_df = datasets.market.copy()

    if state:
        state = state.upper()
        roster_df = roster_df.loc[roster_df["CNT_STATE"].fillna("").eq(state)]
        market_df = market_df.loc[market_df["MARKET"].fillna("").eq(state)]

    retry_df = roster_df.loc[roster_df.get("RUN_NO", 0).fillna(0) > 1].copy()
    retry_df["retry_success"] = (~retry_df.get("IS_FAILED", False).fillna(False).astype(bool)).astype(int)

    retry_summary = {
        "retry_volume": int(len(retry_df)),
        "avg_run_no": round(float(retry_df.get("RUN_NO", pd.Series(dtype="float64")).mean() or 0), 2)
        if not retry_df.empty
        else 0.0,
        "retry_success_rate_pct": round(float(retry_df["retry_success"].mean() * 100), 2)
        if not retry_df.empty
        else 0.0,
    }

    if market_df.empty:
        return {
            "summary": retry_summary | {"count": 0},
            "items": [],
        }

    grouped_market = (
        market_df.groupby(["MARKET", "MONTH"], dropna=False)
        .agg(
            first_iter_success=("FIRST_ITER_SCS_CNT", "sum"),
            first_iter_fail=("FIRST_ITER_FAIL_CNT", "sum"),
            next_iter_success=("NEXT_ITER_SCS_CNT", "sum"),
            next_iter_fail=("NEXT_ITER_FAIL_CNT", "sum"),
            overall_success=("OVERALL_SCS_CNT", "sum"),
            overall_fail=("OVERALL_FAIL_CNT", "sum"),
            scs_percent=("SCS_PERCENT", "mean"),
        )
        .reset_index()
    )

    grouped_market["first_iter_success_rate_pct"] = (
        grouped_market["first_iter_success"]
        / (grouped_market["first_iter_success"] + grouped_market["first_iter_fail"]).replace(0, pd.NA)
        * 100
    ).fillna(0)
    grouped_market["overall_success_rate_pct"] = (
        grouped_market["overall_success"]
        / (grouped_market["overall_success"] + grouped_market["overall_fail"]).replace(0, pd.NA)
        * 100
    ).fillna(0)
    grouped_market["retry_lift_pct"] = (
        grouped_market["overall_success_rate_pct"] - grouped_market["first_iter_success_rate_pct"]
    ).round(2)
    grouped_market["post_retry_failure_share_pct"] = (
        grouped_market["next_iter_fail"]
        / (grouped_market["next_iter_success"] + grouped_market["next_iter_fail"]).replace(0, pd.NA)
        * 100
    ).fillna(0).round(2)

    ranked = grouped_market.sort_values(["retry_lift_pct", "post_retry_failure_share_pct"], ascending=[False, True])
    items = ranked.head(10).astype(object).where(pd.notna(ranked.head(10)), None).to_dict(orient="records")

    return {
        "summary": retry_summary | {"count": int(len(grouped_market))},
        "items": items,
    }
