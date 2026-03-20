from __future__ import annotations

from typing import Any

import pandas as pd


DIMENSION_LABELS = {
    "equipment_id": "장비",
    "analyst": "시험자",
    "batch_no": "배치",
    "raw_material_lot": "원료 lot",
    "test_item": "시험 항목",
}


def _top_issue(table: pd.DataFrame, key_column: str) -> dict[str, Any] | None:
    if table.empty:
        return None
    row = table.iloc[0]
    if int(row["anomaly_count"]) == 0:
        return None
    return {
        "target": str(row[key_column]),
        "anomaly_count": int(row["anomaly_count"]),
        "anomaly_rate": float(row["anomaly_rate"]),
        "oos_count": int(row["oos_count"]),
        "stat_outlier_count": int(row["stat_outlier_count"]),
        "risk_score": float(row["risk_score"]),
    }


def generate_root_cause_hypotheses(
    analyzed_df: pd.DataFrame,
    pattern_result: dict[str, Any],
) -> list[str]:
    """패턴 분석 결과를 기반으로 우선 확인할 원인 가설을 생성합니다."""
    hypotheses: list[str] = []
    pattern_tables = pattern_result["pattern_tables"]

    equipment_issue = _top_issue(pattern_tables["equipment_id"], "equipment_id")
    if equipment_issue and equipment_issue["anomaly_count"] >= 2:
        hypotheses.append(
            f"장비 관점에서 `{equipment_issue['target']}`에서 이상이 반복되었습니다. "
            f"장비 상태, 교정 이력, 최근 유지보수 기록을 우선 확인할 필요가 있습니다."
        )

    analyst_issue = _top_issue(pattern_tables["analyst"], "analyst")
    if analyst_issue and analyst_issue["anomaly_rate"] >= 0.4:
        hypotheses.append(
            f"시험자 관점에서 `{analyst_issue['target']}` 수행 건의 이상 비율이 높습니다. "
            "시험 수행 편차, 시료 전처리 방법, 계산 또는 판독 과정의 일관성 점검이 필요합니다."
        )

    raw_material_issue = _top_issue(pattern_tables["raw_material_lot"], "raw_material_lot")
    if raw_material_issue and raw_material_issue["anomaly_count"] >= 2:
        hypotheses.append(
            f"원료 lot 관점에서 `{raw_material_issue['target']}`와 연계된 이상이 반복되었습니다. "
            "원료 입고 시험 결과, 공급처 변경 여부, lot 간 이력 차이를 우선 검토하는 것이 적절합니다."
        )

    batch_issue = _top_issue(pattern_tables["batch_no"], "batch_no")
    if batch_issue and batch_issue["oos_count"] >= 1:
        hypotheses.append(
            f"특정 배치 `{batch_issue['target']}`에서 OOS가 확인되었습니다. "
            "제조 이력, 공정 편차, 보관 조건, retain sample 재시험 필요성을 함께 검토해야 합니다."
        )

    test_item_issue = _top_issue(pattern_tables["test_item"], "test_item")
    if test_item_issue and test_item_issue["anomaly_count"] >= 2:
        hypotheses.append(
            f"`{test_item_issue['target']}` 항목에서 반복 이상이 관찰됩니다. "
            "해당 시험법의 민감도, 분석 조건, 기준 설정 적절성을 우선 확인하는 것이 좋습니다."
        )

    if analyzed_df["oos_flag"].sum() and not hypotheses:
        hypotheses.append(
            "OOS가 확인되었으나 단일 차원으로 원인이 집중되지는 않았습니다. "
            "시험 수행 기록, 원데이터, 장비 로그를 교차 검토해 복합 요인을 확인해야 합니다."
        )

    if not hypotheses:
        hypotheses.append(
            "현재 데이터에서는 뚜렷한 반복 이상 패턴이 제한적입니다. "
            "추가 배치 데이터와 장기 추세를 확보하면 원인 가설의 신뢰도를 높일 수 있습니다."
        )

    return hypotheses
