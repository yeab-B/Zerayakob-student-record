from __future__ import annotations

from io import BytesIO
from typing import Iterable

import numpy as np
import pandas as pd


STUDENT_NAME_ALIASES = ["student", "name", "learner", "pupil"]
ATTENDANCE_ALIASES = ["attendance", "present", "presence", "attended"]


def read_csv_file(uploaded_file) -> pd.DataFrame:
    """Read uploaded CSV file using safe fallback strategies."""
    content = uploaded_file.getvalue()
    parsers = [
        {"encoding": "utf-8", "engine": "python"},
        {"encoding": "latin-1", "engine": "python"},
    ]

    for parser in parsers:
        try:
            frame = pd.read_csv(BytesIO(content), **parser)
            frame["source_file"] = uploaded_file.name
            return frame
        except Exception:
            continue

    return pd.DataFrame({"source_file": [uploaded_file.name]})


def merge_csv_files(uploaded_files: Iterable) -> pd.DataFrame:
    frames = [read_csv_file(file) for file in uploaded_files]
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True, sort=False)
    return clean_missing_values(merged)


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    cleaned = df.copy()
    for col in cleaned.columns:
        if pd.api.types.is_numeric_dtype(cleaned[col]):
            cleaned[col] = cleaned[col].fillna(cleaned[col].median() if cleaned[col].notna().any() else 0)
        else:
            cleaned[col] = cleaned[col].fillna("Unknown")
    return cleaned


def _find_student_column(df: pd.DataFrame) -> str | None:
    lowered = {col.lower(): col for col in df.columns}
    for alias in STUDENT_NAME_ALIASES:
        for key, original in lowered.items():
            if alias in key:
                return original
    return None


def _find_attendance_column(df: pd.DataFrame) -> str | None:
    lowered = {col.lower(): col for col in df.columns}
    for alias in ATTENDANCE_ALIASES:
        for key, original in lowered.items():
            if alias in key:
                return original
    return None


def _score_columns(df: pd.DataFrame, student_col: str | None, attendance_col: str | None) -> list[str]:
    excluded = {student_col, attendance_col, "source_file", "rank", "performance_tag"}
    numeric_cols = [
        col
        for col in df.columns
        if col not in excluded and pd.api.types.is_numeric_dtype(df[col])
    ]
    return numeric_cols


def compute_metrics(df: pd.DataFrame) -> dict[str, pd.DataFrame | pd.Series | float | int]:
    if df.empty:
        return {
            "student_table": pd.DataFrame(),
            "subject_performance": pd.DataFrame(),
            "top_students": pd.DataFrame(),
            "weak_students": pd.DataFrame(),
            "average_score": 0.0,
            "total_students": 0,
        }

    working = df.copy()
    student_col = _find_student_column(working)
    if student_col is None:
        working["student_name"] = np.arange(1, len(working) + 1).astype(str)
        student_col = "student_name"

    attendance_col = _find_attendance_column(working)
    if attendance_col:
        working[attendance_col] = pd.to_numeric(working[attendance_col], errors="coerce").fillna(0)
    else:
        working["attendance_rate"] = 100.0
        attendance_col = "attendance_rate"

    score_cols = _score_columns(working, student_col, attendance_col)
    if score_cols:
        for col in score_cols:
            working[col] = pd.to_numeric(working[col], errors="coerce")
        working["average_score"] = working[score_cols].mean(axis=1).fillna(0)
    else:
        working["average_score"] = 0.0

    student_table = (
        working.groupby(student_col, as_index=False)
        .agg(
            average_score=("average_score", "mean"),
            attendance_rate=(attendance_col, "mean"),
        )
        .rename(columns={student_col: "student_name"})
    )

    student_table["rank"] = student_table["average_score"].rank(method="dense", ascending=False).astype(int)

    student_table["performance_tag"] = np.where(
        student_table["average_score"] >= 75,
        "Strong",
        np.where(student_table["average_score"] < 50, "Weak", "Average"),
    )

    subject_performance = (
        working[score_cols].mean().reset_index(name="average_score").rename(columns={"index": "subject"})
        if score_cols
        else pd.DataFrame(columns=["subject", "average_score"])
    )

    top_students = student_table.sort_values("average_score", ascending=False).head(10)
    weak_students = student_table[student_table["performance_tag"] == "Weak"].sort_values("average_score")

    return {
        "student_table": student_table.sort_values("rank"),
        "subject_performance": subject_performance.sort_values("average_score", ascending=False),
        "top_students": top_students,
        "weak_students": weak_students,
        "average_score": float(student_table["average_score"].mean() if not student_table.empty else 0),
        "total_students": int(student_table["student_name"].nunique()),
    }
