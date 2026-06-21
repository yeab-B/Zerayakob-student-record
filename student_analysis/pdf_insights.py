from __future__ import annotations

import re
from collections import defaultdict

import pandas as pd
import pdfplumber

POSITIVE_KEYWORDS = ["excellent", "good", "great", "improved", "active", "participates", "well done"]
NEGATIVE_KEYWORDS = ["poor", "struggling", "weak", "late", "missing", "absent", "low"]
BEHAVIOR_KEYWORDS = ["behavior", "discipline", "attitude", "respect", "focus", "classroom"]
IMPROVEMENT_KEYWORDS = ["improve", "needs", "should", "recommend", "practice", "support"]


def extract_text_from_pdfs(uploaded_pdfs) -> list[str]:
    texts: list[str] = []
    for pdf in uploaded_pdfs:
        with pdfplumber.open(pdf) as document:
            pages = [page.extract_text() or "" for page in document.pages]
            texts.append("\n".join(pages))
    return texts


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if part and part.strip()]


def _bucket_sentence(sentence: str) -> dict[str, bool]:
    lower = sentence.lower()
    return {
        "positive": any(word in lower for word in POSITIVE_KEYWORDS),
        "negative": any(word in lower for word in NEGATIVE_KEYWORDS),
        "behavior": any(word in lower for word in BEHAVIOR_KEYWORDS),
        "improvement": any(word in lower for word in IMPROVEMENT_KEYWORDS),
    }


def analyze_pdf_texts(texts: list[str], student_names: list[str] | None = None) -> dict[str, object]:
    categorized = {
        "positive_comments": [],
        "negative_comments": [],
        "behavior_notes": [],
        "improvement_suggestions": [],
    }
    per_student_notes: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0})
    student_names = student_names or []

    for text in texts:
        for sentence in _split_sentences(text):
            flags = _bucket_sentence(sentence)
            if flags["positive"]:
                categorized["positive_comments"].append(sentence)
            if flags["negative"]:
                categorized["negative_comments"].append(sentence)
            if flags["behavior"]:
                categorized["behavior_notes"].append(sentence)
            if flags["improvement"]:
                categorized["improvement_suggestions"].append(sentence)

            sentence_lower = sentence.lower()
            for student in student_names:
                if student and student.lower() in sentence_lower:
                    if flags["positive"]:
                        per_student_notes[student]["positive"] += 1
                    if flags["negative"]:
                        per_student_notes[student]["negative"] += 1

    return {
        **categorized,
        "student_comment_scores": pd.DataFrame(
            [
                {"student_name": name, "positive_comments": data["positive"], "negative_comments": data["negative"]}
                for name, data in per_student_notes.items()
            ]
        ),
    }
