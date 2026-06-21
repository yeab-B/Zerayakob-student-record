from __future__ import annotations

import streamlit as st

from student_analysis.csv_processing import compute_metrics, merge_csv_files
from student_analysis.pdf_insights import analyze_pdf_texts, extract_text_from_pdfs
from student_analysis.reporting import generate_pdf_report
from student_analysis.rule_engine import generate_student_insights


st.set_page_config(page_title="Kail Academy Student Analysis", layout="wide")
st.title("Kail Academy Student Performance Analysis System")
st.caption("Rule-based insights only (no machine learning training).")

csv_files = st.file_uploader("Upload student CSV files", type=["csv"], accept_multiple_files=True)
pdf_files = st.file_uploader("Upload weekly teacher PDF reports", type=["pdf"], accept_multiple_files=True)

if st.button("Run Analysis", type="primary"):
    if not csv_files:
        st.error("Please upload at least one CSV file.")
        st.stop()

    merged_df = merge_csv_files(csv_files)
    metrics = compute_metrics(merged_df)

    if metrics["student_table"].empty:
        st.warning("No usable student rows were found in uploaded CSV files.")
        st.stop()

    pdf_texts = extract_text_from_pdfs(pdf_files) if pdf_files else []
    pdf_insights = analyze_pdf_texts(
        pdf_texts,
        metrics["student_table"]["student_name"].astype(str).tolist(),
    )

    student_insights = generate_student_insights(
        metrics["student_table"],
        pdf_insights.get("student_comment_scores"),
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total students", metrics["total_students"])
    with col2:
        st.metric("Average score", f"{metrics['average_score']:.2f}")

    st.subheader("Student performance table")
    st.dataframe(student_insights, use_container_width=True)

    st.subheader("Top students")
    st.dataframe(metrics["top_students"], use_container_width=True)

    at_risk_students = student_insights[student_insights["insight"] == "At risk student"]
    st.subheader("Weak / At-risk students")
    st.dataframe(at_risk_students if not at_risk_students.empty else metrics["weak_students"], use_container_width=True)

    st.subheader("Subject-wise performance")
    st.dataframe(metrics["subject_performance"], use_container_width=True)

    st.subheader("Teacher PDF insights")
    st.write("**Positive comments**")
    st.write(pdf_insights.get("positive_comments", [])[:10] or ["None"])
    st.write("**Negative comments**")
    st.write(pdf_insights.get("negative_comments", [])[:10] or ["None"])
    st.write("**Behavior notes**")
    st.write(pdf_insights.get("behavior_notes", [])[:10] or ["None"])
    st.write("**Improvement suggestions**")
    st.write(pdf_insights.get("improvement_suggestions", [])[:10] or ["None"])

    report_bytes = generate_pdf_report(
        student_insights,
        at_risk_students,
        pdf_insights,
        metrics["average_score"],
    )
    st.download_button(
        "Download PDF report",
        report_bytes,
        file_name="kail_academy_student_performance_report.pdf",
        mime="application/pdf",
    )
