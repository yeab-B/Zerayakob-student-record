from __future__ import annotations

from io import BytesIO

import pandas as pd
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def _draw_lines(pdf: canvas.Canvas, title: str, lines: list[str], y: float, max_lines: int = 8) -> float:
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(0.7 * inch, y, title)
    y -= 0.22 * inch
    pdf.setFont("Helvetica", 10)
    for line in lines[:max_lines]:
        pdf.drawString(0.9 * inch, y, f"- {line[:115]}")
        y -= 0.2 * inch
    return y - 0.1 * inch


def generate_pdf_report(
    student_table: pd.DataFrame,
    at_risk_students: pd.DataFrame,
    pdf_insights: dict[str, object],
    average_score: float,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    y = height - 0.8 * inch

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(0.7 * inch, y, "Kail Academy - Student Performance Report")
    y -= 0.35 * inch

    pdf.setFont("Helvetica", 11)
    pdf.drawString(0.7 * inch, y, f"Total students: {len(student_table)}")
    y -= 0.22 * inch
    pdf.drawString(0.7 * inch, y, f"Class average score: {average_score:.2f}")
    y -= 0.35 * inch

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(0.7 * inch, y, "Student ranking table")
    y -= 0.22 * inch
    pdf.setFont("Helvetica", 10)
    for _, row in student_table.head(20).iterrows():
        pdf.drawString(
            0.9 * inch,
            y,
            f"Rank {int(row['rank'])} - {row['student_name']} | Score: {row['average_score']:.2f} | Attendance: {row['attendance_rate']:.1f}%",
        )
        y -= 0.2 * inch
        if y < 1.2 * inch:
            pdf.showPage()
            y = height - 0.8 * inch

    at_risk_names = at_risk_students["student_name"].astype(str).tolist() if not at_risk_students.empty else ["None"]
    y = _draw_lines(pdf, "At-risk students", at_risk_names, y)
    y = _draw_lines(
        pdf,
        "Insights from teacher PDF reports",
        [*pdf_insights.get("negative_comments", [])[:4], *pdf_insights.get("positive_comments", [])[:4]]
        or ["No PDF insights provided."],
        y,
    )
    y = _draw_lines(
        pdf,
        "Recommendations for improvement",
        [
            "Give targeted support sessions for at-risk students.",
            "Engage families on attendance and homework routines.",
            "Use weekly teacher feedback to track behavior and progress.",
        ],
        y,
    )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
