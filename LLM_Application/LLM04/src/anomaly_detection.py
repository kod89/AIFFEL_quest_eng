from __future__ import annotations

import numpy as np
import pandas as pd


def _calculate_group_zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - series.mean()) / std


def _calculate_group_iqr_bounds(series: pd.Series) -> tuple[float, float]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return float("-inf"), float("inf")
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return lower, upper


def detect_anomalies(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Spec 기준 OOS와 통계적 이상치를 함께 계산합니다."""
    analyzed = df.copy()

    analyzed["oos_flag"] = (analyzed["value"] < analyzed["spec_min"]) | (
        analyzed["value"] > analyzed["spec_max"]
    )
    analyzed["deviation_from_center"] = analyzed["value"] - analyzed["spec_mid"]

    analyzed["z_score"] = analyzed.groupby("test_item")["value"].transform(_calculate_group_zscore)

    iqr_bounds = (
        analyzed.groupby("test_item")["value"]
        .apply(_calculate_group_iqr_bounds)
        .to_dict()
    )
    analyzed["iqr_lower"] = analyzed["test_item"].map(lambda item: iqr_bounds[item][0])
    analyzed["iqr_upper"] = analyzed["test_item"].map(lambda item: iqr_bounds[item][1])
    analyzed["iqr_outlier"] = (analyzed["value"] < analyzed["iqr_lower"]) | (
        analyzed["value"] > analyzed["iqr_upper"]
    )
    analyzed["zscore_outlier"] = analyzed["z_score"].abs() >= 2.0
    analyzed["stat_outlier"] = analyzed["iqr_outlier"] | analyzed["zscore_outlier"]
    analyzed["severity_score"] = (
        analyzed["oos_flag"].astype(int) * 3
        + analyzed["stat_outlier"].astype(int) * 2
        + analyzed["z_score"].abs().clip(upper=5).fillna(0)
    )

    analyzed["anomaly_label"] = np.select(
        [
            analyzed["oos_flag"] & analyzed["stat_outlier"],
            analyzed["oos_flag"],
            analyzed["stat_outlier"],
        ],
        [
            "OOS + Statistical Outlier",
            "OOS",
            "Statistical Outlier",
        ],
        default="Normal",
    )

    anomaly_table = analyzed[analyzed["anomaly_label"] != "Normal"].copy()
    anomaly_table = anomaly_table.sort_values(
        ["severity_score", "date"], ascending=[False, True]
    ).reset_index(drop=True)

    summary = {
        "total_records": int(len(analyzed)),
        "oos_count": int(analyzed["oos_flag"].sum()),
        "stat_outlier_count": int(analyzed["stat_outlier"].sum()),
        "anomaly_count": int((analyzed["anomaly_label"] != "Normal").sum()),
        "products_affected": int(analyzed.loc[analyzed["anomaly_label"] != "Normal", "product_name"].nunique()),
    }

    return analyzed, {"summary": summary, "anomaly_table": anomaly_table}
