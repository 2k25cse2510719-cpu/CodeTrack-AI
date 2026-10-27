from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "codeforces"
OUTPUT_DIR = ROOT / "data" / "processed"

SUBMISSIONS_FILE = RAW_DIR / "submissions.csv"
CONTESTS_FILE = RAW_DIR / "contest_history.csv"
USERS_FILE = RAW_DIR / "users.csv"
OUTPUT_FILE = OUTPUT_DIR / "user_features_rebuilt_test.csv"


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    return pd.read_csv(path)


def problem_key(df):
    contest = df.get("contestId", pd.Series(index=df.index, dtype="object"))
    index = df.get("problemIndex", pd.Series(index=df.index, dtype="object"))
    name = df.get("problemName", pd.Series(index=df.index, dtype="object"))

    key = contest.astype("string") + "_" + index.astype("string")
    missing = contest.isna() | index.isna()
    key.loc[missing] = name.loc[missing].astype("string")
    return key


def build_features():
    submissions = read_csv(SUBMISSIONS_FILE)
    contests = read_csv(CONTESTS_FILE)
    users = read_csv(USERS_FILE)

    required_user_column = "handle"
    for label, frame in [
        ("submissions", submissions),
        ("contest history", contests),
        ("users", users),
    ]:
        if required_user_column not in frame.columns:
            raise ValueError(
                f"{label} CSV is missing required column 'handle'. "
                f"Found: {frame.columns.tolist()}"
            )

    submissions["verdict"] = (
        submissions["verdict"].astype("string").str.upper()
        if "verdict" in submissions.columns
        else pd.Series("", index=submissions.index, dtype="string")
    )

    submissions["_problem_key"] = problem_key(submissions)

    accepted = submissions["verdict"].eq("OK")
    wrong_answer = submissions["verdict"].eq("WRONG_ANSWER")
    tle = submissions["verdict"].eq("TIME_LIMIT_EXCEEDED")

    submissions["_accepted"] = accepted
    submissions["_wrong_answer"] = wrong_answer
    submissions["_tle"] = tle

    grouped = submissions.groupby("handle", dropna=False)

    features = grouped.agg(
        total_submissions=("verdict", "size"),
        accepted_submissions=("_accepted", "sum"),
        wrong_answers=("_wrong_answer", "sum"),
        time_limit_exceeded=("_tle", "sum"),
        distinct_problems_attempted=("_problem_key", "nunique"),
    )

    solved = (
        submissions.loc[accepted]
        .groupby("handle")["_problem_key"]
        .nunique()
        .rename("distinct_problems_solved")
    )
    features = features.join(solved, how="left")

    if "problemRating" in submissions.columns:
        submissions["problemRating"] = pd.to_numeric(
            submissions["problemRating"], errors="coerce"
        )
        rated_submissions = submissions.dropna(subset=["problemRating"])
        problem_stats = rated_submissions.groupby("handle")["problemRating"].agg(
            average_problem_rating="mean",
            maximum_problem_rating="max",
        )
        features = features.join(problem_stats, how="left")
    else:
        features["average_problem_rating"] = np.nan
        features["maximum_problem_rating"] = np.nan

    denominator = features["total_submissions"].replace(0, np.nan)
    features["acceptance_rate"] = features["accepted_submissions"] / denominator
    features["wrong_answer_rate"] = features["wrong_answers"] / denominator
    features["tle_rate"] = features["time_limit_exceeded"] / denominator

    if "rank" in contests.columns:
        contests["rank"] = pd.to_numeric(contests["rank"], errors="coerce")
        contest_stats = contests.groupby("handle").agg(
            contest_count=("rank", "size"),
            average_contest_rank=("rank", "mean"),
        )
    else:
        contest_stats = contests.groupby("handle").size().to_frame("contest_count")
        contest_stats["average_contest_rank"] = np.nan

    features = features.join(contest_stats, how="left")

    if "newRating" in contests.columns:
        contests["newRating"] = pd.to_numeric(contests["newRating"], errors="coerce")
        time_col = "ratingUpdateTimeSeconds"
        if time_col in contests.columns:
            contests = contests.sort_values(time_col, kind="stable")
        elif "contestId" in contests.columns:
            contests = contests.sort_values("contestId", kind="stable")

        valid_ratings = contests.dropna(subset=["newRating"])
        first = valid_ratings.groupby("handle")["newRating"].first()
        latest = valid_ratings.groupby("handle")["newRating"].last()

        features["first_contest_rating"] = first
        features["latest_contest_rating"] = latest
        features["rating_change"] = latest - first
    else:
        features["first_contest_rating"] = np.nan
        features["latest_contest_rating"] = np.nan
        features["rating_change"] = np.nan

    profile_columns = [
        column
        for column in ["handle", "rating", "maxRating", "rank", "maxRank"]
        if column in users.columns
    ]
    profiles = users[profile_columns].drop_duplicates("handle").set_index("handle")
    features = features.join(profiles, how="outer")

    count_columns = [
        "total_submissions",
        "accepted_submissions",
        "wrong_answers",
        "time_limit_exceeded",
        "distinct_problems_attempted",
        "distinct_problems_solved",
        "contest_count",
    ]
    for column in count_columns:
        if column not in features:
            features[column] = 0
        features[column] = features[column].fillna(0).astype("int64")

    for column in [
        "average_problem_rating",
        "maximum_problem_rating",
        "acceptance_rate",
        "wrong_answer_rate",
        "tle_rate",
        "average_contest_rank",
        "first_contest_rating",
        "latest_contest_rating",
        "rating_change",
        "rating",
        "maxRating",
    ]:
        if column not in features:
            features[column] = np.nan

    features = features.reset_index()
    features = features[
        [
            "handle",
            "total_submissions",
            "accepted_submissions",
            "wrong_answers",
            "time_limit_exceeded",
            "distinct_problems_attempted",
            "average_problem_rating",
            "maximum_problem_rating",
            "distinct_problems_solved",
            "acceptance_rate",
            "wrong_answer_rate",
            "tle_rate",
            "contest_count",
            "average_contest_rank",
            "first_contest_rating",
            "latest_contest_rating",
            "rating_change",
            "rating",
            "maxRating",
            "rank",
            "maxRank",
        ]
    ].sort_values("handle", kind="stable")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved: {OUTPUT_FILE}")
    print(f"Shape: {features.shape}")
    print(f"Missing values: {int(features.isna().sum().sum())}")
    print("Feature columns:", features.columns.tolist())


if __name__ == "__main__":
    build_features()
