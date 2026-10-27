import pandas as pd
import numpy as np
from pathlib import Path

CONTEST_FILE = Path("data/codeforces/contest_history.csv")
SNAPSHOT_FILE = Path("data/processed/future_rating_dataset.csv")
OUTPUT_DIR = Path("data/processed/v2")
OUTPUT_FILE = OUTPUT_DIR / "future_rating_dataset.csv"

SECONDS_PER_DAY = 86400
MIN_DAYS = 75
MAX_DAYS = 105
TARGET_DAYS = 90
CUTOFF_INTERVAL_DAYS = 30

contests = pd.read_csv(CONTEST_FILE)
old_snapshots = pd.read_csv(SNAPSHOT_FILE)

contests["ratingUpdateTimeSeconds"] = pd.to_numeric(
    contests["ratingUpdateTimeSeconds"], errors="coerce"
)
contests["newRating"] = pd.to_numeric(
    contests["newRating"], errors="coerce"
)

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "newRating"]
).copy()

contests["ratingUpdateTimeSeconds"] = (
    contests["ratingUpdateTimeSeconds"].astype("int64")
)

contests = contests.sort_values(
    ["handle", "ratingUpdateTimeSeconds"]
).drop_duplicates(
    subset=["handle", "ratingUpdateTimeSeconds"],
    keep="last"
)

rows = []

for handle, group in contests.groupby("handle"):
    times = group["ratingUpdateTimeSeconds"].to_numpy()
    ratings = group["newRating"].to_numpy(dtype=float)

    if len(group) < 2:
        continue

    # Reuse historical cutoffs, not future target selections.
    user_cutoffs = old_snapshots.loc[
        old_snapshots["handle"] == handle, "cutoff_timestamp"
    ].drop_duplicates().to_numpy(dtype=np.int64)

    for cutoff in user_cutoffs:
        baseline_idx = np.searchsorted(times, cutoff, side="right") - 1

        if baseline_idx < 0:
            continue

        min_time = cutoff + MIN_DAYS * SECONDS_PER_DAY
        max_time = cutoff + MAX_DAYS * SECONDS_PER_DAY
        target_time = cutoff + TARGET_DAYS * SECONDS_PER_DAY

        start_idx = np.searchsorted(times, min_time, side="left")
        end_idx = np.searchsorted(times, max_time, side="right")

        if start_idx >= end_idx:
            continue

        # Select the observation closest to day 90.
        candidates = np.arange(start_idx, end_idx)
        target_idx = candidates[
            np.argmin(np.abs(times[candidates] - target_time))
        ]

        baseline_rating = float(ratings[baseline_idx])
        future_rating = float(ratings[target_idx])

        rows.append({
            "handle": handle,
            "cutoff_timestamp": int(cutoff),
            "baseline_rating": baseline_rating,
            "future_rating": future_rating,
            "rating_change": future_rating - baseline_rating,
            "target_timestamp": int(times[target_idx]),
            "days_to_target": (
                times[target_idx] - cutoff
            ) / SECONDS_PER_DAY,
        })

result = pd.DataFrame(rows)

if result.empty:
    raise ValueError("No valid future-rating samples were generated.")

result = result.sort_values(
    ["handle", "cutoff_timestamp"]
).reset_index(drop=True)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT_FILE, index=False)

print("V2 FUTURE-RATING TARGET DATASET")
print("-" * 40)
print("Rows:", len(result))
print("Users:", result["handle"].nunique())
print("Missing values:", int(result.isnull().sum().sum()))
print("Duplicate rows:", int(result.duplicated().sum()))
print("\nDays to target:")
print(result["days_to_target"].describe().round(2).to_string())
print("\nRating change:")
print(result["rating_change"].describe().round(2).to_string())
print("\nSaved to:", OUTPUT_FILE)
