from __future__ import annotations

import pandas as pd


def preprocess_qc_data(df: pd.DataFrame) -> pd.DataFrame:
    """QC 분석 전에 타입과 결측치를 정리합니다."""
    processed = df.copy()

    # 날짜와 수치형 컬럼을 명시적으로 변환합니다.
    processed["date"] = pd.to_datetime(processed["date"], errors="coerce")

    numeric_columns = ["value", "spec_min", "spec_max"]
    for column in numeric_columns:
        processed[column] = pd.to_numeric(processed[column], errors="coerce")

    text_columns = [
        "product_name",
        "batch_no",
        "test_item",
        "analyst",
        "equipment_id",
        "raw_material_lot",
    ]
    for column in text_columns:
        processed[column] = processed[column].astype(str).str.strip()

    processed = processed.dropna(subset=["date", "value", "spec_min", "spec_max"]).copy()
    if processed.empty:
        raise ValueError("전처리 후 남은 데이터가 없습니다. 날짜/수치 컬럼 형식을 확인해주세요.")

    processed["month"] = processed["date"].dt.to_period("M").astype(str)
    processed["spec_range"] = processed["spec_max"] - processed["spec_min"]
    processed["spec_mid"] = (processed["spec_max"] + processed["spec_min"]) / 2

    return processed.sort_values(["date", "product_name", "batch_no", "test_item"]).reset_index(drop=True)
