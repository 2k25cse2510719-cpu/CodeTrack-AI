import numpy as np
import pandas as pd
from pathlib import Path

CONTEST_FILE = Path("data/codeforces/contest_history.csv")
TARGET_FILE = Path("data/processed/v2/future_rating_dataset.csv")
OUTPUT_FILE = Path("data/processed/v3/historical_features.csv")

SECONDS_PER_DAY = 86400

contests = pd.read_csv(CONTEST_FILE)
targets = pd.read_csv(TARGET_FILE)

for col in ["ratingUpdateTimeSeconds", "oldRating", "newRating", "rank"]:
    contests[col] = pd.to_numeric(contests[col], errors="coerce")

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "newRating"]
).copy()

contests = contests.sort_values(
    ["handle", "ratingUpdateTimeSeconds"]
).drop_duplicates(
    subset=["handle", "ratingUpdateTimeSeconds"],
    keep="last"
)

rows = []

for handle, group in contests.groupby("handle"):
    group = group.sort_values("ratingUpdateTimeSeconds").reset_index(drop=True)
    user_targets = targets[targets["handle"] == handle]

    times = group["ratingUpdateTimeSeconds"].to_numpy(dtype=np.int64)
    ratings = group["newRating"].to_numpy(dtype=float)
    old_ratings = group["oldRating"].to_numpy(dtype=float)
    ranks = group["rank"].to_numpy(dtype=float)

    for target in user_targets.itertuples(index=False):
        cutoff = int(target.cutoff_timestamp)
        end_idx = np.searchsorted(times, cutoff, side="right")

        if end_idx == 0:
            continue

        hist_ratings = ratings[:end_idx]
        hist_times = times[:end_idx]
        hist_old = old_ratings[:end_idx]
        hist_ranks = ranks[:end_idx]

        changes = hist_ratings - hist_old
        valid_changes = changes[
            np.isfinite(changes) & np.isfinite(hist_old) & (hist_old > 0)
        ]

        recent5 = changes[-5:]
        recent10 = changes[-10:]

        recent5 = recent5[
            np.isfinite(recent5)
            & np.isfinite(hist_old[-5:])
            & (hist_old[-5:] > 0)
        ]
        recent10 = changes[-10:]
        recent10 = recent10[
            np.isfinite(recent10)
            & np.isfinite(hist_old[-10:])
            & (hist_old[-10:] > 0)
        ]

        recent_ratings10 = hist_ratings[-10:]
        last_time = int(hist_times[-1])

        rows.append({
            "handle": handle,
            "cutoff_timestamp": cutoff,
            "baseline_rating": float(hist_ratings[-1]),
            "historical_contest_count": len(hist_ratings),
            "historical_average_rating": float(np.mean(hist_ratings)),
            "historical_max_rating": float(np.max(hist_ratings)),
            "historical_min_rating": float(np.min(hist_ratings)),
            "recent_3_contest_average_rating": float(np.mean(hist_ratings[-3:])),
            "recent_5_contest_average_rating": float(np.mean(hist_ratings[-5:])),
            "recent_5_contest_rating_trend": (
                float(hist_ratings[-1] - hist_ratings[-5])
                if len(hist_ratings) >= 5 else 0.0
            ),
            "average_contest_rating_change": (
                float(np.mean(valid_changes)) if len(valid_changes) else 0.0
            ),
            "rating_change_std": (
                float(np.std(valid_changes, ddof=0))
                if len(valid_changes) else 0.0
            ),
            "historical_average_rank": (
                float(np.nanmean(hist_ranks))
                if np.isfinite(hist_ranks).any() else 0.0
            ),
            "days_since_last_contest": (
                cutoff - last_time
            ) / SECONDS_PER_DAY,
            "contests_last_90_days": int(
                (hist_times >= cutoff - 90 * SECONDS_PER_DAY).sum()
            ),
            "contests_last_180_days": int(
                (hist_times >= cutoff - 180 * SECONDS_PER_DAY).sum()
            ),
            "recent_5_change_mean": (
                float(np.mean(recent5)) if len(recent5) else 0.0
            ),
            "recent_5_change_std": (
                float(np.std(recent5, ddof=0)) if len(recent5) else 0.0
            ),
            "recent_10_change_mean": (
                float(np.mean(recent10)) if len(recent10) else 0.0
            ),
            "recent_10_change_std": (
                float(np.std(recent10, ddof=0)) if len(recent10) else 0.0
            ),
            "recent_10_rating_range": float(
                np.max(recent_ratings10) - np.min(recent_ratings10)
            ),
            "peak_drawdown": float(hist_ratings[-1] - np.max(hist_ratings)),
            "future_rating": float(target.future_rating),
            "rating_change": float(target.rating_change),
            "target_timestamp": int(target.target_timestamp),
            "days_to_target": float(target.days_to_target),
        })

features = pd.DataFrame(rows)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
features = features.sort_values(
    ["handle", "cutoff_timestamp"]
).reset_index(drop=True)
features.to_csv(OUTPUT_FILE, index=False)

print("V3 HISTORICAL FEATURES")
print("-" * 45)
print("Shape:", features.shape)
print("Users:", features["handle"].nunique())
print("Missing values:", int(features.isna().sum().sum()))
print(
    "Duplicate handle/cutoff pairs:",
    int(features.duplicated(["handle", "cutoff_timestamp"]).sum())
)
print("Saved to:", OUTPUT_FILE)
