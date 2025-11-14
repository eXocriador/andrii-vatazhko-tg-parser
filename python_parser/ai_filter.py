"""Zero-shot classifier that labels Telegram posts."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from transformers import pipeline

CANDIDATE_LABELS = ["fundraising", "report", "other"]
MODEL_NAME = "facebook/bart-large-mnli"


@lru_cache(maxsize=1)
def _build_classifier():
    return pipeline("zero-shot-classification", model=MODEL_NAME)


def classify(text: str) -> str:
    """Return fundraising/report/other for the given text."""
    if not text.strip():
        return "other"
    classifier = _build_classifier()
    result = classifier(text, candidate_labels=CANDIDATE_LABELS, multi_label=False)
    top_label = result["labels"][0]
    return top_label.lower()
