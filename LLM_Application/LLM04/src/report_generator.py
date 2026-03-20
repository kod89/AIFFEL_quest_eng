from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _register_font() -> str:
    """가능하면 한글 지원 폰트를 사용하고, 없으면 기본 폰트로 대체합니다."""
    font_candidates = [
        "/mnt/c/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]

    for font_path in font_candidates:
        if Path(font_path).exists():
            pdfmetrics.registerFont(TTFont("QCReportFont", font_path))
            return "QCReportFont"
    return "Helvetica"


def _build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "QCTitle",
            parent=sample["Title"],
            fontName=font_name,
            fontSize=18,
            leading=24,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#12344D"),
            spaceAfter=10,
        ),
        "heading": ParagraphStyle(
            "QCHeading",
            parent=sample["Heading2"],
            fontName=font_name,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#12344D"),
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "QCBody",
            parent=sample["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "QCSmall",
            parent=sample["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#4A5568"),
        ),
    }


def _safe_text(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _summary_table(summary: dict[str, Any], font_name: str) -> Table:
    rows = [
        ["Metric", "Value"],
        ["Total Records", summary["total_records"]],
        ["OOS", summary["oos_count"]],
        ["Statistical Outliers", summary["stat_outlier_count"]],
        ["Total Anomalies", summary["anomaly_count"]],
        ["Affected Products", summary["products_affected"]],
    ]
    table = Table(rows, colWidths=[75 * mm, 35 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E7F3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#12344D")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C6D1")),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ]
        )
    )
    return table


def _dataframe_table(df: pd.DataFrame, font_name: str, max_rows: int = 8) -> Table:
    if df.empty:
        df = pd.DataFrame([{"message": "No data"}])

    trimmed = df.head(max_rows).copy()
    for column in trimmed.columns:
        trimmed[column] = trimmed[column].astype(str)

    rows = [list(trimmed.columns)] + trimmed.values.tolist()
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("LEADING", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E7F3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#12344D")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFCFE")]),
            ]
        )
    )
    return table


def generate_report(
    summary: dict[str, Any],
    anomaly_table: pd.DataFrame,
    pattern_result: dict[str, Any],
    root_causes: list[str],
    capa: dict[str, list[str]],
    output_dir: str | Path = "reports",
) -> str:
    """분석 결과를 PDF 보고서로 저장합니다."""
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"qc_capa_report_{timestamp}.pdf"

    font_name = _register_font()
    styles = _build_styles(font_name)

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    anomaly_view = anomaly_table[
        [
            "date",
            "product_name",
            "batch_no",
            "test_item",
            "value",
            "analyst",
            "equipment_id",
            "anomaly_label",
        ]
    ].copy()
    if not anomaly_view.empty and pd.api.types.is_datetime64_any_dtype(anomaly_view["date"]):
        anomaly_view["date"] = anomaly_view["date"].dt.strftime("%Y-%m-%d")

    equipment_table = pattern_result["pattern_tables"]["equipment_id"][
        ["equipment_id", "total_runs", "anomaly_count", "oos_count", "anomaly_rate", "risk_score"]
    ].copy()
    analyst_table = pattern_result["pattern_tables"]["analyst"][
        ["analyst", "total_runs", "anomaly_count", "oos_count", "anomaly_rate", "risk_score"]
    ].copy()

    story = [
        Paragraph("QC Anomaly Analysis + CAPA Recommendation Report", styles["title"]),
        Paragraph(
            _safe_text(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
            styles["small"],
        ),
        Spacer(1, 6),
        Paragraph(
            "This report summarizes detection results, repeated abnormal patterns, root-cause hypotheses, and CAPA recommendations for QC review.",
            styles["body"],
        ),
        Spacer(1, 8),
        Paragraph("1. Detection Summary", styles["heading"]),
        _summary_table(summary, font_name),
        Spacer(1, 10),
        Paragraph("2. Key Anomalies", styles["heading"]),
        _dataframe_table(anomaly_view, font_name),
        Spacer(1, 10),
        Paragraph("3. Pattern Highlights - Equipment", styles["heading"]),
        _dataframe_table(equipment_table, font_name, max_rows=6),
        Spacer(1, 8),
        Paragraph("4. Pattern Highlights - Analyst", styles["heading"]),
        _dataframe_table(analyst_table, font_name, max_rows=6),
        Spacer(1, 10),
        Paragraph("5. Root Cause Hypotheses", styles["heading"]),
    ]

    for hypothesis in root_causes:
        story.append(Paragraph(f"- {_safe_text(hypothesis)}", styles["body"]))

    story.extend(
        [
            Spacer(1, 10),
            Paragraph("6. CAPA Recommendations", styles["heading"]),
            Paragraph("Corrective Actions", styles["body"]),
        ]
    )
    for item in capa["corrective_actions"]:
        story.append(Paragraph(f"- {_safe_text(item)}", styles["body"]))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Preventive Actions", styles["body"]))
    for item in capa["preventive_actions"]:
        story.append(Paragraph(f"- {_safe_text(item)}", styles["body"]))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Additional Checks", styles["body"]))
    for item in capa["additional_checks"]:
        story.append(Paragraph(f"- {_safe_text(item)}", styles["body"]))

    doc.build(story)
    return str(report_path)
