from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr
import pandas as pd

from src.anomaly_detection import detect_anomalies
from src.capa_recommender import recommend_capa
from src.data_loader import load_qc_data, load_sample_data
from src.pattern_analysis import analyze_patterns
from src.preprocess import preprocess_qc_data
from src.report_generator import generate_report
from src.root_cause import generate_root_cause_hypotheses


REPORT_COLUMNS = [
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
    "anomaly_label",
]


def _assess_risk_level(summary: dict[str, Any]) -> tuple[str, str]:
    anomaly_rate = summary["anomaly_count"] / max(summary["total_records"], 1)
    if summary["oos_count"] >= 5 or anomaly_rate >= 0.3:
        return "High", "즉시 원인 조사와 배치 영향도 검토가 필요한 수준입니다."
    if summary["oos_count"] >= 2 or anomaly_rate >= 0.15:
        return "Medium", "반복 패턴 기반 우선 점검과 추가 모니터링이 필요한 수준입니다."
    return "Low", "현재는 제한적 이상 수준이지만 추세 모니터링은 유지해야 합니다."


def _format_summary_cards(summary: dict[str, Any]) -> str:
    risk_level, risk_message = _assess_risk_level(summary)
    card_template = """
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """
    cards = [
        card_template.format(label="Total Records", value=summary["total_records"]),
        card_template.format(label="OOS", value=summary["oos_count"]),
        card_template.format(label="Statistical Outliers", value=summary["stat_outlier_count"]),
        card_template.format(label="Affected Products", value=summary["products_affected"]),
    ]
    return f"""
    <div class="summary-shell">
        <div class="summary-banner">
            <div>
                <div class="summary-title">QC Risk Brief</div>
                <div class="summary-subtitle">{risk_message}</div>
            </div>
            <div class="risk-pill risk-{risk_level.lower()}">{risk_level} Risk</div>
        </div>
        <div class="metric-grid">
            {''.join(cards)}
        </div>
    </div>
    """.strip()


def _format_agent_brief(
    summary: dict[str, Any],
    hot_spots: list[dict[str, Any]],
    root_causes: list[str],
    capa: dict[str, list[str]],
) -> str:
    risk_level, risk_message = _assess_risk_level(summary)
    top_spot = hot_spots[0] if hot_spots else None
    lead_signal = (
        f"`{top_spot['dimension']}` 기준 `{top_spot['target']}`에서 반복 이상이 가장 두드러졌습니다."
        if top_spot
        else "현재 데이터에서 뚜렷한 단일 hotspot은 제한적입니다."
    )
    first_action = capa["corrective_actions"][0] if capa["corrective_actions"] else "원데이터 재검토를 우선 수행합니다."
    leading_hypothesis = root_causes[0] if root_causes else "추가 데이터 확보 후 원인 가설 정교화가 필요합니다."
    return f"""
### Analysis Briefing
- **Risk Level:** {risk_level}
- **Executive Interpretation:** {risk_message}
- **Primary Signal:** {lead_signal}
- **Leading Hypothesis:** {leading_hypothesis}
- **Recommended First Action:** {first_action}
""".strip()


def _format_root_causes(root_causes: list[str]) -> str:
    return "\n".join([f"- {item}" for item in root_causes])


def _format_capa(capa: dict[str, list[str]]) -> str:
    lines = ["### Corrective Actions"]
    lines.extend([f"- {item}" for item in capa["corrective_actions"]])
    lines.extend(["", "### Preventive Actions"])
    lines.extend([f"- {item}" for item in capa["preventive_actions"]])
    lines.extend(["", "### Additional Checks"])
    lines.extend([f"- {item}" for item in capa["additional_checks"]])
    return "\n".join(lines)


def _format_agent_status() -> str:
    return """
### Workflow Steps
1. Detection: spec 이탈과 통계 이상치를 함께 식별합니다.
2. Root Cause: 반복 패턴을 바탕으로 우선 확인 포인트를 정리합니다.
3. CAPA: 시정조치, 예방조치, 추가 확인사항을 제안합니다.
4. Report: PDF 보고서를 생성해 다운로드할 수 있습니다.
""".strip()


def _empty_outputs(error_message: str) -> tuple[str, pd.DataFrame, pd.DataFrame, str, str, str | None]:
    return error_message, "", pd.DataFrame(), pd.DataFrame(), "", "", None


def run_analysis(file_obj: object | None) -> tuple[str, str, pd.DataFrame, pd.DataFrame, str, str, str | None]:
    try:
        raw_df = load_sample_data() if file_obj is None else load_qc_data(file_obj)
        processed_df = preprocess_qc_data(raw_df)
        analyzed_df, anomaly_result = detect_anomalies(processed_df)
        pattern_result = analyze_patterns(analyzed_df)
        root_causes = generate_root_cause_hypotheses(analyzed_df, pattern_result)
        capa = recommend_capa(root_causes, pattern_result["hot_spots"])
        report_path = generate_report(
            summary=anomaly_result["summary"],
            anomaly_table=anomaly_result["anomaly_table"],
            pattern_result=pattern_result,
            root_causes=root_causes,
            capa=capa,
        )

        hotspot_rows = []
        for spot in pattern_result["hot_spots"]:
            hotspot_rows.append(
                {
                    "dimension": spot["dimension"],
                    "target": spot["target"],
                    "anomaly_count": spot["anomaly_count"],
                    "anomaly_rate": round(spot["anomaly_rate"], 3),
                    "risk_score": round(spot["risk_score"], 3),
                }
            )

        anomaly_table = anomaly_result["anomaly_table"][REPORT_COLUMNS].copy()
        if not anomaly_table.empty:
            anomaly_table["date"] = anomaly_table["date"].dt.strftime("%Y-%m-%d")

        hotspot_df = pd.DataFrame(hotspot_rows)

        return (
            _format_summary_cards(anomaly_result["summary"]),
            _format_agent_brief(
                anomaly_result["summary"],
                pattern_result["hot_spots"],
                root_causes,
                capa,
            ),
            anomaly_table,
            hotspot_df,
            _format_root_causes(root_causes),
            _format_capa(capa),
            report_path,
        )
    except Exception as exc:
        return _empty_outputs(f"분석 중 오류가 발생했습니다: {exc}")


def load_sample_for_preview() -> pd.DataFrame:
    sample_df = load_sample_data()
    return sample_df.head(15)


with gr.Blocks(title="QC Analysis Workflow") as demo:
    gr.Markdown(
        """
        # QC Analysis Workflow
        QC 시험 데이터에서 이상치를 탐지하고, 반복 패턴 기반 원인 가설과 CAPA를 제안하는 분석 워크플로우 데모입니다.
        """
    )

    with gr.Row(elem_classes=["app-shell"]):
        with gr.Column(scale=1):
            file_input = gr.File(label="QC CSV 업로드", file_types=[".csv"])
            sample_button = gr.Button("샘플 데이터 미리보기", variant="secondary")
            analyze_button = gr.Button("분석 실행", variant="primary")
            agent_status = gr.Markdown(_format_agent_status())
            gr.Markdown("파일을 업로드하지 않고 `분석 실행`을 누르면 기본 샘플 데이터로 분석합니다.")
            sample_preview = gr.Dataframe(
                label="샘플 데이터 Preview",
                interactive=False,
                wrap=True,
            )

        with gr.Column(scale=2):
            summary_output = gr.HTML(label="Summary Cards")
            briefing_output = gr.Markdown(label="Analysis Briefing")
            with gr.Tab("1. Detection"):
                anomaly_output = gr.Dataframe(
                    label="이상치 테이블",
                    interactive=False,
                    wrap=True,
                )
            with gr.Tab("2. Root Cause"):
                hotspot_output = gr.Dataframe(
                    label="반복 이상 패턴",
                    interactive=False,
                    wrap=True,
                )
                root_cause_output = gr.Markdown(label="원인 가설")
            with gr.Tab("3. CAPA"):
                capa_output = gr.Markdown(label="CAPA 추천")
            with gr.Tab("4. Report"):
                report_file = gr.File(label="PDF 리포트 다운로드", interactive=False)

    sample_button.click(fn=load_sample_for_preview, outputs=sample_preview)
    analyze_button.click(
        fn=run_analysis,
        inputs=file_input,
        outputs=[
            summary_output,
            briefing_output,
            anomaly_output,
            hotspot_output,
            root_cause_output,
            capa_output,
            report_file,
        ],
    )


if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue="slate",
            secondary_hue="blue",
            neutral_hue="slate",
        ),
        css="""
        .app-shell {max-width: 1240px; margin: 0 auto;}
        .summary-shell {
            background: linear-gradient(135deg, #f8fbff 0%, #edf4fb 100%);
            border: 1px solid #c9d8e6;
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 14px;
            color: #102a43;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
        }
        .summary-banner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }
        .summary-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #102a43 !important;
        }
        .summary-subtitle {
            font-size: 0.92rem;
            color: #486581 !important;
            margin-top: 4px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }
        .metric-card {
            background: white;
            border: 1px solid #c9d8e6;
            border-radius: 14px;
            padding: 14px;
            color: #102a43 !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
        }
        .metric-label {
            font-size: 0.85rem;
            color: #52606d !important;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 1.55rem;
            font-weight: 700;
            color: #102a43 !important;
        }
        .risk-pill {
            padding: 7px 12px;
            border-radius: 999px;
            font-size: 0.86rem;
            font-weight: 700;
            white-space: nowrap;
            border: 1px solid transparent;
        }
        .risk-high {
            background: #fde8e8;
            color: #9b1c1c !important;
            border-color: #f5c2c7;
        }
        .risk-medium {
            background: #fff3c4;
            color: #8d6e00 !important;
            border-color: #f7d070;
        }
        .risk-low {
            background: #def7ec;
            color: #046c4e !important;
            border-color: #84e1bc;
        }
        .summary-shell * {
            color: inherit;
        }
        .summary-shell .summary-title,
        .summary-shell .summary-subtitle,
        .summary-shell .metric-label,
        .summary-shell .metric-value,
        .summary-shell .risk-pill {
            opacity: 1 !important;
            text-shadow: none !important;
        }
        .summary-shell .metric-card * {
            color: inherit !important;
        }
        .gradio-container .summary-shell p,
        .gradio-container .summary-shell span,
        .gradio-container .summary-shell div {
            color: inherit;
        }
        @media (max-width: 900px) {
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .summary-banner {
                flex-direction: column;
                align-items: flex-start;
            }
        }
        """,
    )
