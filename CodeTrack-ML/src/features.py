"""Feature engineering for CodeTrack-AI problem history."""
from __future__ import annotations
from datetime import date
from typing import Any
import pandas as pd

PROBLEM_COLUMNS = ["id", "title", "platform", "difficulty", "topic", "selectedPattern",
                   "verifiedPattern", "status", "solvedDate", "createdAt", "updatedAt"]
REVISION_COLUMNS = ["status", "scheduledDate", "completedAt", "problemId"]

def _frame(records: list[dict[str, Any]] | None, columns: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(records or [])
    for column in columns:
        if column not in frame.columns:
            frame[column] = None
    return frame

def build_features(problems: list[dict[str, Any]] | None,
                   revisions: list[dict[str, Any]] | None = None,
                   today: date | None = None) -> dict[str, float | int]:
    """Calculate user-level features from ProblemResponse-like records."""
    now = pd.Timestamp(today or date.today())
    p = _frame(problems, PROBLEM_COLUMNS)
    r = _frame(revisions, REVISION_COLUMNS)
    p["status_norm"] = p["status"].fillna("").astype(str).str.strip().str.upper()
    p["difficulty_norm"] = p["difficulty"].fillna("").astype(str).str.strip().str.upper()
    p["topic_norm"] = p["topic"].fillna("").astype(str).str.strip()
    p["pattern_norm"] = p["verifiedPattern"].fillna("").astype(str).str.strip()
    missing_verified = p["pattern_norm"].eq("")
    p.loc[missing_verified, "pattern_norm"] = p.loc[missing_verified, "selectedPattern"].fillna("").astype(str).str.strip()
    p["solved_date"] = pd.to_datetime(p["solvedDate"], errors="coerce")
    solved = p[p["status_norm"].eq("SOLVED")].copy()
    recent_7 = int((solved["solved_date"] >= now - pd.Timedelta(days=6)).sum())
    recent_30 = int((solved["solved_date"] >= now - pd.Timedelta(days=29)).sum())
    def count_difficulty(level: str) -> int:
        return int(solved["difficulty_norm"].eq(level).sum())
    solved_topics = solved.loc[solved["topic_norm"].ne(""), "topic_norm"]
    solved_patterns = solved.loc[solved["pattern_norm"].ne(""), "pattern_norm"]
    r["status_norm"] = r["status"].fillna("").astype(str).str.strip().str.upper()
    revision_total = len(r)
    revision_completed = int(r["status_norm"].eq("COMPLETED").sum())
    total, solved_count = len(p), len(solved)
    platform_series = solved["platform"].dropna().astype(str).str.strip().replace("", pd.NA)
    return {
        "total_problems": int(total),
        "solved_count": int(solved_count),
        "in_progress_count": int(p["status_norm"].eq("IN_PROGRESS").sum()),
        "todo_count": int(p["status_norm"].eq("TODO").sum()),
        "solve_rate": round(solved_count / total, 4) if total else 0.0,
        "easy_solved": count_difficulty("EASY"),
        "medium_solved": count_difficulty("MEDIUM"),
        "hard_solved": count_difficulty("HARD"),
        "topic_count": int(solved_topics.nunique()),
        "pattern_count": int(solved_patterns.nunique()),
        "solved_last_7_days": recent_7,
        "solved_last_30_days": recent_30,
        "platform_count": int(platform_series.nunique()),
        "revision_total": int(revision_total),
        "revision_completed": int(revision_completed),
        "revision_completion_rate": round(revision_completed / revision_total, 4) if revision_total else 0.0,
        "has_solved_date_rate": round(float(solved["solved_date"].notna().mean()), 4) if solved_count else 0.0,
    }
