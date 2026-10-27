
"""Explainable baseline scores; these are heuristics, not validated ML predictions."""
from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, value)), 1)


def _band(score: float) -> str:
    if score < 35:
        return "Building foundations"
    if score < 60:
        return "Developing"
    if score < 80:
        return "Progressing well"
    return "Strong preparation signals"


def score_readiness(features: dict[str, Any]) -> dict[str, Any]:
    """Return two transparent, rule-based readiness indicators."""
    solved = int(features.get("solved_count", 0))
    medium = int(features.get("medium_solved", 0))
    hard = int(features.get("hard_solved", 0))
    topics = int(features.get("topic_count", 0))
    patterns = int(features.get("pattern_count", 0))
    recent30 = int(features.get("solved_last_30_days", 0))
    recent7 = int(features.get("solved_last_7_days", 0))
    revision_total = int(features.get("revision_total", 0))
    revision_rate = float(features.get("revision_completion_rate", 0.0))

    interview = _clamp(
        min(solved, 100) * 0.25
        + min(medium, 40) * 0.65
        + min(hard, 20) * 0.65
        + min(topics, 12) * 1.5
        + min(patterns, 12) * 0.75
        + min(recent30, 20) * 0.5
        + revision_rate * 10
    )

    competition = _clamp(
        min(solved, 100) * 0.20
        + min(medium, 40) * 0.60
        + min(hard, 25) * 1.2
        + min(topics, 12) * 1.0
        + min(patterns, 12) * 0.75
        + min(recent7, 10) * 1.0
        + revision_rate * 5
    )

    strengths = []
    gaps = []

    if medium >= 10:
        strengths.append("Some medium-level problem-solving experience")
    if hard >= 3:
        strengths.append("Experience with hard problems")
    if topics >= 5:
        strengths.append("Practice spans several topics")
    if recent30 >= 5:
        strengths.append("Recent problem-solving activity")
    if revision_rate >= 0.7 and revision_total >= 3:
        strengths.append("Good completion rate for recorded revisions")

    if medium < 10:
        gaps.append("Build more medium-problem experience")
    if topics < 5:
        gaps.append("Broaden practice across DSA topics")
    if recent30 < 5:
        gaps.append("Increase recent, consistent practice")
    if hard < 3:
        gaps.append("Try more challenging problems over time")
    if float(features.get("has_solved_date_rate", 0)) < 0.8:
        gaps.append("Record solved dates consistently to improve activity estimates")

    return {
        "score_type": "heuristic_baseline_not_validated_prediction",
        "interview": {
            "score": interview,
            "band": _band(interview),
            "strengths": strengths[:4],
            "areas_to_improve": gaps[:4],
        },
        "competition": {
            "score": competition,
            "band": _band(competition),
            "strengths": [
                strength
                for strength in strengths
                if any(
                    keyword in strength.lower()
                    for keyword in ("hard", "topic", "activity")
                )
            ][:4],
            "areas_to_improve": gaps[:4],
        },
        "limitations": [
            "Scores are a rule-based baseline, not a trained or validated ML prediction.",
            "Problem history does not currently measure solve time, attempts, contest ratings, or interview outcomes.",
            "Scores are not probabilities of success.",
        ],
    }



