from __future__ import annotations

from typing import Any

import pandas as pd


PATTERN_DIMENSIONS = ["batch_no", "analyst", "equipment_id", "test_item", "raw_material_lot"]


def _build_dimension_summary(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    grouped = (
        df.groupby(dimension, dropna=False)
        .agg(
            total_runs=("anomaly_label", "size"),
            anomaly_count=("anomaly_label", lambda x: (x != "Normal").sum()),
            oos_count=("oos_flag", "sum"),
            stat_outlier_count=("stat_outlier", "sum"),
        )
        .reset_index()
    )
    grouped["anomaly_rate"] = grouped["anomaly_count"] / grouped["total_runs"]
    grouped["risk_score"] = (
        grouped["oos_count"] * 3
        + grouped["stat_outlier_count"] * 2
        + grouped["anomaly_rate"] * 5
    )
    return grouped.sort_values(["risk_score", "anomaly_count"], ascending=[False, False]).reset_index(drop=True)


def analyze_patterns(df: pd.DataFrame) -> dict[str, Any]:
    """반복 이상 패턴을 batch, analyst, equipment 등 차원으로 요약합니다."""
    pattern_tables = {dimension: _build_dimension_summary(df, dimension) for dimension in PATTERN_DIMENSIONS}

    hot_spots = []
    for dimension, table in pattern_tables.items():
        if table.empty:
            continue
        top_row = table.iloc[0]
        if top_row["anomaly_count"] > 0:
            hot_spots.append(
                {
                    "dimension": dimension,
                    "target": str(top_row[dimension]),
                    "anomaly_count": int(top_row["anomaly_count"]),
                    "anomaly_rate": float(top_row["anomaly_rate"]),
                    "risk_score": float(top_row["risk_score"]),
                }
            )

    trend_by_date = (
        df.assign(date_only=df["date"].dt.date)
        .groupby("date_only")
        .agg(
            total_runs=("anomaly_label", "size"),
            anomaly_count=("anomaly_label", lambda x: (x != "Normal").sum()),
        )
        .reset_index()
    )
    trend_by_date["anomaly_rate"] = trend_by_date["anomaly_count"] / trend_by_date["total_runs"]

    return {
        "pattern_tables": pattern_tables,
        "hot_spots": sorted(hot_spots, key=lambda x: x["risk_score"], reverse=True),
        "trend_by_date": trend_by_date,
    }
