
from datetime import date

from src.features import build_features
from src.readiness import score_readiness


def test_features_and_scores():
    problems = [
        {
            "title": "A",
            "status": "SOLVED",
            "difficulty": "Easy",
            "topic": "Arrays",
            "selectedPattern": "Hashing",
            "verifiedPattern": "Hashing",
            "solvedDate": "2026-10-24",
        },
        {
            "title": "B",
            "status": "IN_PROGRESS",
            "difficulty": "Medium",
            "topic": "Trees",
        },
        {
            "title": "C",
            "status": "SOLVED",
            "difficulty": "Hard",
            "topic": "Trees",
            "selectedPattern": "DFS",
            "solvedDate": "2026-10-23",
        },
    ]

    features = build_features(problems, today=date(2026, 10, 25))

    assert features["total_problems"] == 3
    assert features["solved_count"] == 2
    assert features["easy_solved"] == 1
    assert features["hard_solved"] == 1
    assert features["topic_count"] == 2

    result = score_readiness(features)

    assert 0 <= result["interview"]["score"] <= 100
    assert 0 <= result["competition"]["score"] <= 100
    assert result["score_type"] == "heuristic_baseline_not_validated_prediction"


def test_empty_history():
    features = build_features([])

    assert features["total_problems"] == 0

    result = score_readiness(features)

    assert result["interview"]["score"] == 0
    assert result["competition"]["score"] == 0


def test_future_solved_dates_do_not_count_as_recent_activity():
    problems = [
        {
            "title": "Past problem",
            "status": "SOLVED",
            "difficulty": "Medium",
            "solvedDate": "2026-10-24",
        },
        {
            "title": "Future problem",
            "status": "SOLVED",
            "difficulty": "Medium",
            "solvedDate": "2026-10-27",
        },
    ]

    features = build_features(
        problems,
        today=date(2026, 10, 25),
    )

    assert features["solved_last_7_days"] == 1
    assert features["solved_last_30_days"] == 1

def test_missing_solved_dates_do_not_count_as_recent_activity():
    problems = [
        {
            "title": "Missing date",
            "status": "SOLVED",
            "difficulty": "Easy",
        },
        {
            "title": "Invalid date",
            "status": "SOLVED",
            "difficulty": "Medium",
            "solvedDate": "not-a-date",
        },
    ]

    features = build_features(
        problems,
        today=date(2026, 10, 25),
    )

    assert features["solved_count"] == 2
    assert features["solved_last_7_days"] == 0
    assert features["solved_last_30_days"] == 0
    assert features["has_solved_date_rate"] == 0.0


def test_solved_date_rate_counts_only_valid_dates():
    problems = [
        {
            "title": "Valid date",
            "status": "SOLVED",
            "difficulty": "Easy",
            "solvedDate": "2026-10-24",
        },
        {
            "title": "Missing date",
            "status": "SOLVED",
            "difficulty": "Medium",
        },
    ]

    features = build_features(
        problems,
        today=date(2026, 10, 25),
    )

    assert features["has_solved_date_rate"] == 0.5
    assert features["solved_last_7_days"] == 1


def test_revision_completion_improves_readiness_scores():
    base_features = {
        "solved_count": 20,
        "medium_solved": 10,
        "hard_solved": 2,
        "topic_count": 5,
        "pattern_count": 3,
        "solved_last_30_days": 5,
        "solved_last_7_days": 2,
        "revision_total": 3,
        "revision_completed": 0,
        "revision_completion_rate": 0.0,
        "has_solved_date_rate": 1.0,
    }

    incomplete = score_readiness(base_features)

    completed_features = {
        **base_features,
        "revision_completed": 3,
        "revision_completion_rate": 1.0,
    }
    completed = score_readiness(completed_features)

    assert completed["interview"]["score"] > incomplete["interview"]["score"]
    assert completed["competition"]["score"] > incomplete["competition"]["score"]


def test_readiness_explanations_have_correct_spacing():
    result = score_readiness({
        "solved_count": 2,
        "medium_solved": 2,
        "topic_count": 1,
        "revision_total": 3,
        "revision_completed": 1,
        "revision_completion_rate": 1 / 3,
    })

    interview_gaps = result["interview"]["areas_to_improve"]
    competition_gaps = result["competition"]["areas_to_improve"]

    assert "Broaden practice across DSA topics" in interview_gaps
    assert "Build more medium-problem experience" in interview_gaps
    assert all("Broadenpractice" not in gap for gap in interview_gaps)
    assert all("Buildmore" not in gap for gap in competition_gaps)
