import numpy as np
import pandas as pd
from pathlib import Path

FEATURE_PATH = Path("data/processed/v2/historical_features.csv")
CONTEST_PATH = Path("data/codeforces/contest_history.csv")

features = pd.read_csv(FEATURE_PATH)
contests = pd.read_csv(CONTEST_PATH)

numeric_cols = [
    "ratingUpdateTimeSeconds", "oldRating", "newRating", "rank"
]
for col in numeric_cols:
    contests[col] = pd.to_numeric(contests[col], errors="coerce")

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "newRating", "rank"]
).copy()

# Use ordinary rated contests for rating-change statistics.
rated = contests[contests["oldRating"] > 0].copy()
rated["contest_change"] = rated["newRating"] - rated["oldRating"]
rated = rated.sort_values(["handle", "ratingUpdateTimeSeconds"])

# Rebuild historical features independently for every cutoff.
checks = []

for row in features.itertuples(index=False):
    history = contests[
        (contests["handle"] == row.handle)
        & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
    ].sort_values("ratingUpdateTimeSeconds")

    rated_history = rated[
        (rated["handle"] == row.handle)
        & (rated["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
    ].sort_values("ratingUpdateTimeSeconds")

    if history.empty:
        continue

    ratings = history["newRating"]
    changes = rated_history["contest_change"]
    ranks = history["rank"]

    recent3 = ratings.tail(3).mean()
    recent5 = ratings.tail(5).mean()

    # Ordinary least-squares trend over the last five ratings.
    recent5_values = ratings.tail(5).to_numpy()
    trend5 = (
    float(recent5_values[-1] - recent5_values[0])
    if len(recent5_values) >= 2 else 0.0
)

    last_time = history["ratingUpdateTimeSeconds"].max()

    expected = {
        "baseline_rating": ratings.iloc[-1],
        "historical_contest_count": len(history),
        "historical_average_rating": ratings.mean(),
        "historical_max_rating": ratings.max(),
        "historical_min_rating": ratings.min(),
        "recent_3_contest_average_rating": recent3,
        "recent_5_contest_average_rating": recent5,
        "recent_5_contest_rating_trend": trend5,
        "average_contest_rating_change": changes.mean(),
        "rating_change_std": changes.std(ddof=0) if len(changes) >= 2 else 0.0,
        "historical_average_rank": ranks.mean(),
        "days_since_last_contest": (
            row.cutoff_timestamp - last_time
        ) / 86400,
        "contests_last_90_days": (
            history["ratingUpdateTimeSeconds"]
            >= row.cutoff_timestamp - 90 * 86400
        ).sum(),
        "contests_last_180_days": (
            history["ratingUpdateTimeSeconds"]
            >= row.cutoff_timestamp - 180 * 86400
        ).sum(),
    }

    for col, expected_value in expected.items():
        actual_value = getattr(row, col)
        checks.append({
            "handle": row.handle,
            "cutoff_timestamp": row.cutoff_timestamp,
            "feature": col,
            "actual": actual_value,
            "recomputed": expected_value,
            "difference": abs(actual_value - expected_value)
                if pd.notna(actual_value) and pd.notna(expected_value)
                else np.nan,
        })

result = pd.DataFrame(checks)
result.to_csv(
    "models/future_rating_v2/feature_audit_details.csv",
    index=False
)

summary = result.groupby("feature").agg(
    checked=("difference", "count"),
    max_abs_difference=("difference", "max"),
    mean_abs_difference=("difference", "mean"),
).sort_values("max_abs_difference", ascending=False)

print("\nINDEPENDENT HISTORICAL FEATURE AUDIT")
print("=" * 75)
print(summary.round(6).to_string())

print("\nTotal feature comparisons:", len(result))
print("Missing comparisons:", int(result["difference"].isna().sum()))
print("Comparisons differing by more than 0.01:",
      int((result["difference"] > 0.01).sum()))
print("\nSaved detailed results to models/future_rating_v2/feature_audit_details.csv")
print(
    "\nNOTE: This is an independent reconstruction using the stated formulas. "
    "If the original builder used different conventions, differences need "
    "investigation rather than automatically being classified as leakage."
)
