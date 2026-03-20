from __future__ import annotations

from typing import Any


def generate_llm_response(prompt: str, context: dict[str, Any] | None = None) -> str:
    """향후 OpenAI/Gemini 연동을 위한 확장 포인트입니다."""
    _ = context
    return (
        "현재 버전은 외부 LLM 없이 규칙 기반으로 동작합니다. "
        "추후 이 함수에 OpenAI 또는 Gemini API 호출 로직을 연결하면 됩니다."
    )
