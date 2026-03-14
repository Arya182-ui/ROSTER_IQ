"""Core dataset loading and analysis helpers for RosterIQ.

The module uses pandas-backed CSV loading today, but the loader boundary is kept
explicit so the backend can move to DuckDB without changing the public analysis
functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import numpy as np
import pandas as pd


ROSTER_FILENAME = "roster_processing_details.csv"
MARKET_FILENAME = "aggregated_operational_metrics.csv"


@dataclass(frozen=True)
class DatasetBundle:
    """Container for the two source datasets used by the application."""

    roster: pd.DataFrame
    market: pd.DataFrame


class PandasDataLoader:
    """Simple CSV loader abstraction for future backend replacement."""

    def read_frame(self, path: Path) -> pd.DataFrame:
        """Read a CSV file into a pandas DataFrame."""

        return pd.read_csv(path)



def _project_root() -> Path:
    """Return the repository root for the RosterIQ project."""

    return Path(__file__).resolve().parents[2]



def _default_data_roots() -> list[Path]:
    """Return candidate directories that may contain the source datasets."""

    project_root = _project_root()
    workspace_root = project_root.parent
    return [
        project_root / "data",
        workspace_root / "Dataset",
        workspace_root / "data",
        workspace_root,
    ]



def _resolve_dataset_path(filename: str, explicit_path: Optional[str | Path] = None) -> Path:
    """Resolve a dataset file from either an explicit path or known roots."""

    if explicit_path is not None:
        candidate = Path(explicit_path).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Dataset not found: {candidate}")

    for root in _default_data_roots():
        candidate = root / filename
        if candidate.exists():
            return candidate

    search_locations = ", ".join(str(path) for path in _default_data_roots())
    raise FileNotFoundError(f"Could not locate {filename}. Checked: {search_locations}")



def _coerce_datetime_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Convert timestamp-like columns to pandas datetime values in place."""

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df



def _coerce_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Convert numeric-like columns to numeric dtype in place."""

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df



def _normalize_boolean_flag(series: pd.Series) -> pd.Series:
    """Normalize common flag representations to booleans."""

    mapping = {
        "1": True,
        "0": False,
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "y": True,
        "n": False,
    }
    normalized = series.astype(str).str.strip().str.lower().map(mapping)
    return normalized.fillna(series)



def _prepare_roster_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply schema normalization to the roster-processing dataset."""

    df = df.copy()

    datetime_columns = [
        "FILE_RECEIVED_DT",
        "PRE_PROCESSING_START_DT",
        "PRE_PROCESSING_END_DT",
        "MAPPING_APPRVD_AT",
        "ISF_GEN_START_DT",
        "ISF_GEN_END_DT",
        "DART_GEN_START_DT",
        "DART_GEN_END_DT",
        "RELEASED_TO_DART_UI_DT",
        "DART_UI_VALIDATION_START_DT",
        "DART_UI_VALIDATION_END_DT",
        "SPS_LOAD_START_DT",
        "SPS_LOAD_END_DT",
        "LATEST_OBJECT_RUN_DT",
        "CREAT_DT",
        "LAST_UPDT_DT",
    ]
    numeric_columns = [
        "RUN_NO",
        "PRE_PROCESSING_DURATION",
        "MAPPING_APROVAL_DURATION",
        "ISF_GEN_DURATION",
        "DART_GEN_DURATION",
        "DART_REVIEW_DURATION",
        "DART_UI_VALIDATION_DURATION",
        "SPS_LOAD_DURATION",
        "AVG_DART_GENERATION_DURATION",
        "AVG_DART_UI_VLDTN_DURATION",
        "AVG_SPS_LOAD_DURATION",
        "AVG_ISF_GENERATION_DURATION",
        "TOT_REC_CNT",
        "SCS_REC_CNT",
        "FAIL_REC_CNT",
        "SKIP_REC_CNT",
        "REJ_REC_CNT",
        "SCS_PCT",
    ]

    df = _coerce_datetime_columns(df, datetime_columns)
    df = _coerce_numeric_columns(df, numeric_columns)

    for flag in ("IS_STUCK", "IS_FAILED"):
        if flag in df.columns:
            df[flag] = _normalize_boolean_flag(df[flag]).astype("boolean")

    return df



def _prepare_market_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply schema normalization to the market-operations dataset."""

    df = df.copy()
    df = _coerce_datetime_columns(df, ["CREAT_DT", "LAST_UPDT_DT"])
    df = _coerce_numeric_columns(
        df,
        [
            "FIRST_ITER_SCS_CNT",
            "FIRST_ITER_FAIL_CNT",
            "NEXT_ITER_SCS_CNT",
            "NEXT_ITER_FAIL_CNT",
            "OVERALL_SCS_CNT",
            "OVERALL_FAIL_CNT",
            "SCS_PERCENT",
            "IS_ACTIVE",
        ],
    )

    if "MONTH" in df.columns:
        parsed_month = pd.to_datetime(df["MONTH"], format="%m-%Y", errors="coerce")
        df["MONTH"] = parsed_month.dt.to_period("M").dt.to_timestamp()

    if "IS_ACTIVE" in df.columns:
        df["IS_ACTIVE"] = _normalize_boolean_flag(df["IS_ACTIVE"]).astype("boolean")

    return df



def load_datasets(
    roster_path: Optional[str | Path] = None,
    market_path: Optional[str | Path] = None,
    loader: Optional[Callable[[Path], pd.DataFrame]] = None,
) -> DatasetBundle:
    """Load both RosterIQ datasets and return them as a bundle."""

    read_frame = loader or PandasDataLoader().read_frame
    roster_df = _prepare_roster_dataframe(
        read_frame(_resolve_dataset_path(ROSTER_FILENAME, roster_path))
    )
    market_df = _prepare_market_dataframe(
        read_frame(_resolve_dataset_path(MARKET_FILENAME, market_path))
    )
    return DatasetBundle(roster=roster_df, market=market_df)


@lru_cache(maxsize=1)
def get_cached_datasets() -> DatasetBundle:
    """Load the default datasets once per process for API usage."""

    return load_datasets()



def _resolve_roster_df(roster_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Return the provided roster dataframe or the cached default bundle."""

    return roster_df if roster_df is not None else get_cached_datasets().roster



def _resolve_market_df(market_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Return the provided market dataframe or the cached default bundle."""

    return market_df if market_df is not None else get_cached_datasets().market



def _clean_output(df: pd.DataFrame, sort_by: Optional[list[str]] = None) -> pd.DataFrame:
    """Apply stable sorting and reset the index on output dataframes."""

    clean_df = df.copy()
    if sort_by:
        active_sort_columns = [column for column in sort_by if column in clean_df.columns]
        if active_sort_columns:
            clean_df = clean_df.sort_values(
                active_sort_columns,
                ascending=[False] * len(active_sort_columns),
                na_position="last",
            )
    return clean_df.reset_index(drop=True)



def _require_columns(df: pd.DataFrame, columns: Iterable[str], context: str) -> None:
    """Raise a descriptive error when the expected dataset schema is missing columns."""

    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f"{context} requires missing columns: {missing}")



def _select_existing_columns(df: pd.DataFrame, requested_columns: list[str]) -> list[str]:
    """Return the subset of requested columns that are present in the dataframe."""

    return [column for column in requested_columns if column in df.columns]



def get_stuck_ros(roster_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Return roster operations currently marked as stuck."""

    roster_df = _resolve_roster_df(roster_df)
    _require_columns(
        roster_df,
        ["RO_ID", "ORG_NM", "CNT_STATE", "RUN_NO", "LATEST_STAGE_NM", "IS_STUCK"],
        "get_stuck_ros",
    )

    columns = _select_existing_columns(
        roster_df,
        [
            "RO_ID",
            "ORG_NM",
            "CNT_STATE",
            "SRC_SYS",
            "LOB",
            "RUN_NO",
            "FILE_STATUS_CD",
            "LATEST_STAGE_NM",
            "FAILURE_STATUS",
            "LATEST_OBJECT_RUN_DT",
        ],
    )
    stuck_df = roster_df.loc[roster_df["IS_STUCK"] == True, columns].copy()
    return _clean_output(stuck_df, sort_by=["LATEST_OBJECT_RUN_DT", "RUN_NO"])



def get_failed_ros(roster_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Return roster operations currently marked as failed."""

    roster_df = _resolve_roster_df(roster_df)
    _require_columns(
        roster_df,
        ["RO_ID", "ORG_NM", "CNT_STATE", "RUN_NO", "IS_FAILED"],
        "get_failed_ros",
    )

    columns = _select_existing_columns(
        roster_df,
        [
            "RO_ID",
            "ORG_NM",
            "CNT_STATE",
            "SRC_SYS",
            "LOB",
            "RUN_NO",
            "FILE_STATUS_CD",
            "LATEST_STAGE_NM",
            "FAILURE_STATUS",
            "LATEST_OBJECT_RUN_DT",
        ],
    )
    failed_df = roster_df.loc[roster_df["IS_FAILED"] == True, columns].copy()
    return _clean_output(failed_df, sort_by=["LATEST_OBJECT_RUN_DT", "RUN_NO"])



def _rate_result(
    grouped: pd.DataFrame,
    entity_column: str,
    numerator_column: str,
    denominator_column: str,
    rate_column: str,
    basis: str,
) -> pd.DataFrame:
    """Calculate a percentage column and return a clean aggregate dataframe."""

    result = grouped.copy()
    result[rate_column] = np.where(
        result[denominator_column] > 0,
        (result[numerator_column] / result[denominator_column]) * 100.0,
        np.nan,
    )
    result["metric_basis"] = basis
    columns = [entity_column, numerator_column, denominator_column, rate_column, "metric_basis"]
    return _clean_output(result[columns], sort_by=[rate_column, numerator_column])



def get_org_rejection_rates(roster_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Aggregate rejection rates by organization.

    When record-level rejection columns are absent, a roster-level failure proxy
    is returned and labeled through the ``metric_basis`` column.
    """

    roster_df = _resolve_roster_df(roster_df)
    _require_columns(roster_df, ["ORG_NM"], "get_org_rejection_rates")

    if {"REJ_REC_CNT", "TOT_REC_CNT"}.issubset(roster_df.columns):
        grouped = (
            roster_df.groupby("ORG_NM", dropna=False)
            .agg(rejected_records=("REJ_REC_CNT", "sum"), total_records=("TOT_REC_CNT", "sum"))
            .reset_index()
        )
        return _rate_result(
            grouped,
            entity_column="ORG_NM",
            numerator_column="rejected_records",
            denominator_column="total_records",
            rate_column="rejection_rate_pct",
            basis="record_rejections",
        )

    _require_columns(roster_df, ["IS_FAILED"], "get_org_rejection_rates")
    grouped = (
        roster_df.assign(is_failed_numeric=roster_df["IS_FAILED"].fillna(False).astype(int))
        .groupby("ORG_NM", dropna=False)
        .agg(failed_rosters=("is_failed_numeric", "sum"), total_rosters=("ORG_NM", "size"))
        .reset_index()
    )
    return _rate_result(
        grouped,
        entity_column="ORG_NM",
        numerator_column="failed_rosters",
        denominator_column="total_rosters",
        rate_column="rejection_rate_pct",
        basis="failed_roster_proxy",
    )



def get_state_rejection_rates(roster_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Aggregate rejection rates by state.

    When record-level rejection columns are absent, a roster-level failure proxy
    is returned and labeled through the ``metric_basis`` column.
    """

    roster_df = _resolve_roster_df(roster_df)
    _require_columns(roster_df, ["CNT_STATE"], "get_state_rejection_rates")

    if {"REJ_REC_CNT", "TOT_REC_CNT"}.issubset(roster_df.columns):
        grouped = (
            roster_df.groupby("CNT_STATE", dropna=False)
            .agg(rejected_records=("REJ_REC_CNT", "sum"), total_records=("TOT_REC_CNT", "sum"))
            .reset_index()
        )
        return _rate_result(
            grouped,
            entity_column="CNT_STATE",
            numerator_column="rejected_records",
            denominator_column="total_records",
            rate_column="rejection_rate_pct",
            basis="record_rejections",
        )

    _require_columns(roster_df, ["IS_FAILED"], "get_state_rejection_rates")
    grouped = (
        roster_df.assign(is_failed_numeric=roster_df["IS_FAILED"].fillna(False).astype(int))
        .groupby("CNT_STATE", dropna=False)
        .agg(failed_rosters=("is_failed_numeric", "sum"), total_rosters=("CNT_STATE", "size"))
        .reset_index()
    )
    return _rate_result(
        grouped,
        entity_column="CNT_STATE",
        numerator_column="failed_rosters",
        denominator_column="total_rosters",
        rate_column="rejection_rate_pct",
        basis="failed_roster_proxy",
    )



def get_market_success_rates(market_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Return market-level success rates suitable for trend analysis."""

    market_df = _resolve_market_df(market_df)
    _require_columns(
        market_df,
        ["MONTH", "MARKET", "CLIENT_ID", "OVERALL_SCS_CNT", "OVERALL_FAIL_CNT", "SCS_PERCENT", "IS_ACTIVE"],
        "get_market_success_rates",
    )

    rates_df = market_df[
        [
            "MONTH",
            "MARKET",
            "CLIENT_ID",
            "OVERALL_SCS_CNT",
            "OVERALL_FAIL_CNT",
            "SCS_PERCENT",
            "IS_ACTIVE",
        ]
    ].copy()
    return _clean_output(rates_df, sort_by=["MONTH", "SCS_PERCENT"])



def get_retry_operations(roster_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Return roster operations that represent retry attempts."""

    roster_df = _resolve_roster_df(roster_df)
    _require_columns(roster_df, ["RO_ID", "ORG_NM", "RUN_NO"], "get_retry_operations")

    columns = _select_existing_columns(
        roster_df,
        [
            "RO_ID",
            "ORG_NM",
            "CNT_STATE",
            "SRC_SYS",
            "LOB",
            "RUN_NO",
            "FILE_STATUS_CD",
            "LATEST_STAGE_NM",
            "IS_FAILED",
            "FAILURE_STATUS",
            "LATEST_OBJECT_RUN_DT",
        ],
    )
    retry_df = roster_df.loc[roster_df["RUN_NO"].fillna(0) > 1, columns].copy()
    retry_df["retry_sequence"] = retry_df["RUN_NO"] - 1
    return _clean_output(retry_df, sort_by=["RUN_NO", "LATEST_OBJECT_RUN_DT"])



def get_stage_duration_anomalies(
    roster_df: Optional[pd.DataFrame] = None,
    threshold_multiplier: float = 2.0,
) -> pd.DataFrame:
    """Identify roster operations whose stage durations exceed historical baselines."""

    roster_df = _resolve_roster_df(roster_df)
    stage_pairs: Dict[str, tuple[str, str]] = {
        "ISF_GEN": ("ISF_GEN_DURATION", "AVG_ISF_GENERATION_DURATION"),
        "DART_GEN": ("DART_GEN_DURATION", "AVG_DART_GENERATION_DURATION"),
        "DART_UI_VALIDATION": ("DART_UI_VALIDATION_DURATION", "AVG_DART_UI_VLDTN_DURATION"),
        "SPS_LOAD": ("SPS_LOAD_DURATION", "AVG_SPS_LOAD_DURATION"),
    }

    available_pairs = {
        stage: pair
        for stage, pair in stage_pairs.items()
        if pair[0] in roster_df.columns and pair[1] in roster_df.columns
    }
    if not available_pairs:
        return pd.DataFrame(
            columns=[
                "RO_ID",
                "ORG_NM",
                "CNT_STATE",
                "stage_name",
                "duration_value",
                "average_duration_value",
                "anomaly_ratio",
                "threshold_multiplier",
                "LATEST_STAGE_NM",
            ]
        )

    anomaly_frames = []
    for stage_name, (duration_column, average_column) in available_pairs.items():
        columns = _select_existing_columns(
            roster_df,
            ["RO_ID", "ORG_NM", "CNT_STATE", "LATEST_STAGE_NM", duration_column, average_column],
        )
        stage_df = roster_df[columns].copy().rename(
            columns={
                duration_column: "duration_value",
                average_column: "average_duration_value",
            }
        )
        stage_df["stage_name"] = stage_name
        valid_average = stage_df["average_duration_value"].fillna(0) > 0
        stage_df["anomaly_ratio"] = np.where(
            valid_average,
            stage_df["duration_value"] / stage_df["average_duration_value"],
            np.nan,
        )
        stage_df["threshold_multiplier"] = threshold_multiplier
        anomaly_frames.append(
            stage_df.loc[valid_average & (stage_df["anomaly_ratio"] >= threshold_multiplier)]
        )

    if not anomaly_frames:
        return pd.DataFrame(
            columns=[
                "RO_ID",
                "ORG_NM",
                "CNT_STATE",
                "LATEST_STAGE_NM",
                "duration_value",
                "average_duration_value",
                "stage_name",
                "anomaly_ratio",
                "threshold_multiplier",
            ]
        )

    anomalies_df = pd.concat(anomaly_frames, ignore_index=True)
    output_columns = [
        "RO_ID",
        "ORG_NM",
        "CNT_STATE",
        "LATEST_STAGE_NM",
        "stage_name",
        "duration_value",
        "average_duration_value",
        "anomaly_ratio",
        "threshold_multiplier",
    ]
    return _clean_output(anomalies_df[output_columns], sort_by=["anomaly_ratio", "duration_value"])
