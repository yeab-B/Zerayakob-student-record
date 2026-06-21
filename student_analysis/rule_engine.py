from __future__ import annotations

import numpy as np
import pandas as pd


def generate_student_insights(student_table: pd.DataFrame, student_comment_scores: pd.DataFrame) -> pd.DataFrame:
    if student_table.empty:
        return student_table

    working = student_table.copy()
    if student_comment_scores is not None and not student_comment_scores.empty:
        working = working.merge(student_comment_scores, on="student_name", how="left")
    else:
        working["positive_comments"] = 0
        working["negative_comments"] = 0

    working[["positive_comments", "negative_comments"]] = working[
        ["positive_comments", "negative_comments"]
    ].fillna(0)

    at_risk_condition = (working["average_score"] < 50) | (working["attendance_rate"] < 75) | (
        working["negative_comments"] > working["positive_comments"]
    )
    high_performer_condition = (working["average_score"] >= 80) & (working["attendance_rate"] >= 85) & (
        working["negative_comments"] == 0
    )

    working["insight"] = np.select(
        [high_performer_condition, at_risk_condition],
        ["High performer", "At risk student"],
        default="Needs improvement",
    )

    return working.sort_values("rank")
