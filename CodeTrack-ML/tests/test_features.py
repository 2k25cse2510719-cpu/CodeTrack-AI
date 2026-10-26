from datetime import date
from src.features import build_features
from src.readiness import score_readiness

def test_features_and_scores():
    problems = [
        {"title":"A","status":"SOLVED","difficulty":"Easy","topic":"Arrays","selectedPattern":"Hashing","verifiedPattern":"Hashing","solvedDate":"2026-10-24"},
        {"title":"B","status":"IN_PROGRESS","difficulty":"Medium","topic":"Trees"},
        {"title":"C","status":"SOLVED","difficulty":"Hard","topic":"Trees","selectedPattern":"DFS","solvedDate":"2026-10-23"},
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
