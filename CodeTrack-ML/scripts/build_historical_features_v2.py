import pandas as pd
import numpy as np
from pathlib import Path

CONTEST_FILE = Path("data/codeforces/contest_history.csv")
TARGET_FILE = Path("data/processed/v2/future_rating_dataset.csv")
OUTPUT_FILE = Path("data/processed/v2/historical_features.csv")

SECONDS_PER_DAY = 86400

contests = pd.read_csv(CONTEST_FILE)
targets = pd.read_csv(TARGET_FILE)

contests["ratingUpdateTimeSeconds"] = pd.to_numeric(
    contests["ratingUpdateTimeSeconds"], errors="coerce"
)
contests["newRating"] = pd.to_numeric(
    contests["newRating"], errors="coerce"
)
contests["oldRating"] = pd.to_numeric(
    contests["oldRating"], errors="coerce"
)
contests["rank"] = pd.to_numeric(contests["rank"], errors="coerce")

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
    group = group.sort_values("ratingUpdateTimeSeconds").reset_index(drop=True)
    times = group["ratingUpdateTimeSeconds"].to_numpy(dtype=np.int64)

    user_targets = targets[targets["handle"] == handle]

    for target in user_targets.itertuples(index=False):
        cutoff = int(target.cutoff_timestamp)
        end_idx = np.searchsorted(times, cutoff, side="right")

        if end_idx == 0:
            continue

        history = group.iloc[:end_idx]
        ratings = history["newRating"].to_numpy(dtype=float)
        changes = (
            history["newRating"] - history["oldRating"]
        )
        valid_changes = changes[
            history["oldRating"].notna()
            & (history["oldRating"] > 0)
        ].dropna()

        last_time = int(times[end_idx - 1])
        recent_3 = ratings[-3:]
        recent_5 = ratings[-5:]
        recent_5_changes = (
            history["newRating"] - history["oldRating"]
        ).tail(5).dropna()

        recent_90_count = int(
            (history["ratingUpdateTimeSeconds"]
             >= cutoff - 90 * SECONDS_PER_DAY).sum()
        )
        recent_180_count = int(
            (history["ratingUpdateTimeSeconds"]
             >= cutoff - 180 * SECONDS_PER_DAY).sum()
        )

        rows.append({
            "handle": handle,
            "cutoff_timestamp": cutoff,
            "baseline_rating": float(ratings[-1]),
            "historical_contest_count": len(history),
            "historical_average_rating": float(np.mean(ratings)),
            "historical_max_rating": float(np.max(ratings)),
            "historical_min_rating": float(np.min(ratings)),
            "recent_3_contest_average_rating": float(np.mean(recent_3)),
            "recent_5_contest_average_rating": float(np.mean(recent_5)),
            "recent_5_contest_rating_trend": (
                float(recent_5[-1] - recent_5[0])
                if len(recent_5) >= 2 else 0.0
            ),
            "average_contest_rating_change": (
                float(valid_changes.mean()) if len(valid_changes) else 0.0
            ),
            "rating_change_std": (
                float(valid_changes.std(ddof=0))
                if len(valid_changes) >= 2 else 0.0
            ),
            "historical_average_rank": (
                float(history["rank"].mean())
                if history["rank"].notna().any() else 0.0
            ),
            "days_since_last_contest": (
                cutoff - last_time
            ) / SECONDS_PER_DAY,
            "contests_last_90_days": recent_90_count,
            "contests_last_180_days": recent_180_count,
            "future_rating": float(target.future_rating),
            "rating_change": float(target.rating_change),
            "target_timestamp": int(target.target_timestamp),
            "days_to_target": float(target.days_to_target),
        })

features = pd.DataFrame(rows)

if features.empty:
    raise ValueError("No historical feature rows were generated.")

features = features.sort_values(
    ["handle", "cutoff_timestamp"]
).reset_index(drop=True)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
features.to_csv(OUTPUT_FILE, index=False)

print("V2 HISTORICAL FEATURES")
print("-" * 40)
print("Shape:", features.shape)
print("Users:", features["handle"].nunique())
print("Missing values:", int(features.isnull().sum().sum()))
print("Duplicate handle/cutoff pairs:",
      int(features.duplicated(["handle", "cutoff_timestamp"]).sum()))
print("\nFeature columns:")
for column in features.columns:
    print(" -", column)
print("\nSaved to:", OUTPUT_FILE)
