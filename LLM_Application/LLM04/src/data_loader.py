from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = [
    "date",
    "product_name",
    "batch_no",
    "test_item",
    "value",
    "spec_min",
    "spec_max",
    "analyst",
    "equipment_id",
    "raw_material_lot",
]


def validate_columns(df: pd.DataFrame, required_columns: Iterable[str] = REQUIRED_COLUMNS) -> None:
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "필수 컬럼이 누락되었습니다: " + ", ".join(missing_columns)
        )


def load_qc_data(file_obj: str | Path | object | None) -> pd.DataFrame:
    """업로드 파일 또는 파일 경로에서 QC 데이터를 읽습니다."""
    if file_obj is None:
        raise ValueError("업로드된 파일이 없습니다. CSV 파일을 선택하거나 샘플 데이터를 불러오세요.")

    if isinstance(file_obj, Path):
        file_source = str(file_obj)
    elif isinstance(file_obj, str):
        file_source = file_obj
    else:
        file_source = getattr(file_obj, "name", file_obj)
    df = pd.read_csv(file_source)

    if df.empty:
        raise ValueError("CSV 파일이 비어 있습니다. 데이터가 포함된 파일을 업로드해주세요.")

    validate_columns(df)
    return df


def load_sample_data(sample_path: str | Path = "sample_data/sample_qc_data.csv") -> pd.DataFrame:
    sample_file = Path(sample_path)
    if not sample_file.exists():
        raise FileNotFoundError(f"샘플 데이터 파일을 찾을 수 없습니다: {sample_file}")
    return load_qc_data(sample_file)
