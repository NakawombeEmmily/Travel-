from __future__ import annotations

import re

from app.models.feedback import Sentiment

_POSITIVE_WORDS = {
    "great",
    "excellent",
    "amazing",
    "good",
    "happy",
    "satisfied",
    "perfect",
    "love",
    "loved",
    "helpful",
    "fast",
    "friendly",
    "wonderful",
    "thanks",
    "thank",
    "best",
    "smooth",
    "recommend",
}

_NEGATIVE_WORDS = {
    "bad",
    "terrible",
    "awful",
    "poor",
    "slow",
    "rude",
    "disappointed",
    "disappointing",
    "worst",
    "hate",
    "hated",
    "expensive",
    "delay",
    "delayed",
    "problem",
    "problems",
    "issue",
    "issues",
    "unhappy",
    "refund",
    "late",
    "never",
}

_WORD_RE = re.compile(r"[a-z]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def calculate_sentiment(rating: int, comment: str | None) -> str:
    """Derive sentiment from a rating (1-5) and optional free-text comment.

    Rating drives the base sentiment; conflicting comment signals downgrade the
    result to ``mixed``.
    """
    tokens = _tokens(comment or "")
    has_positive = bool(tokens & _POSITIVE_WORDS)
    has_negative = bool(tokens & _NEGATIVE_WORDS)

    if rating >= 4:
        base = Sentiment.positive
    elif rating <= 2:
        base = Sentiment.negative
    else:
        base = Sentiment.neutral

    if has_positive and has_negative:
        return Sentiment.mixed.value
    if base == Sentiment.positive and has_negative:
        return Sentiment.mixed.value
    if base == Sentiment.negative and has_positive:
        return Sentiment.mixed.value
    return base.value
