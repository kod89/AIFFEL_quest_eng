from __future__ import annotations

from typing import Any


def recommend_capa(root_causes: list[str], hot_spots: list[dict[str, Any]]) -> dict[str, list[str]]:
    """원인 가설과 패턴 hotspot을 바탕으로 CAPA 초안을 생성합니다."""
    corrective_actions: list[str] = []
    preventive_actions: list[str] = []
    additional_checks: list[str] = []

    hot_spot_dimensions = {spot["dimension"]: spot for spot in hot_spots}

    if "equipment_id" in hot_spot_dimensions:
        target = hot_spot_dimensions["equipment_id"]["target"]
        corrective_actions.append(
            f"`{target}` 장비의 사용 중지 여부를 검토하고, 교정 상태 및 최근 점검 기록을 즉시 확인합니다."
        )
        preventive_actions.append(
            "주요 QC 장비에 대해 이상 발생 이력 기반의 예방 점검 주기를 재설정합니다."
        )

    if "analyst" in hot_spot_dimensions:
        target = hot_spot_dimensions["analyst"]["target"]
        corrective_actions.append(
            f"`{target}` 수행 건의 raw data와 계산 로그를 재확인하고, 필요 시 동등성 확인 재시험을 실시합니다."
        )
        preventive_actions.append(
            "시험자 간 SOP 해석 차이를 줄이기 위해 핵심 시험 항목 중심의 재교육과 실습 평가를 수행합니다."
        )

    if "raw_material_lot" in hot_spot_dimensions:
        target = hot_spot_dimensions["raw_material_lot"]["target"]
        corrective_actions.append(
            f"`{target}` 관련 원료의 입고 시험, 사용 이력, 공급처 변경 여부를 QA와 함께 재검토합니다."
        )
        preventive_actions.append(
            "원료 lot 변경 시 영향 평가 체크리스트를 운영해 QC 이상 발생 가능성을 사전에 점검합니다."
        )

    if any("배치" in hypothesis for hypothesis in root_causes):
        additional_checks.append("해당 배치 retain sample 보유 여부를 확인하고, 필요 시 재시험 또는 재평가를 검토합니다.")

    if any("시험법" in hypothesis or "시험 항목" in hypothesis for hypothesis in root_causes):
        additional_checks.append("시험법 적합성, 시스템 적합성 결과, reference standard 상태를 함께 확인합니다.")

    if not corrective_actions:
        corrective_actions.append("이상 건에 대해 원데이터, 시험기록서, 계산 시트를 우선 재검토합니다.")

    if not preventive_actions:
        preventive_actions.append("이상 패턴 재발 방지를 위해 월 단위 추세 모니터링과 리뷰 루틴을 설정합니다.")

    if not additional_checks:
        additional_checks.append("관련 deviation, change control, CAPA 이력과의 연관성을 QA 기준으로 추가 검토합니다.")

    return {
        "corrective_actions": corrective_actions,
        "preventive_actions": preventive_actions,
        "additional_checks": additional_checks,
    }
