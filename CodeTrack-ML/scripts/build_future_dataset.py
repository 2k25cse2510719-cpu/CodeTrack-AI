
import pandas as pd
import numpy as np
from pathlib import Path

DATA_FILE = Path("data/codeforces/contest_history.csv")
OUTPUT_FILE = Path("data/processed/future_rating_dataset.csv")

MIN_TARGET_DAYS = 75
MAX_TARGET_DAYS = 105
CUTOFF_INTERVAL_DAYS = 30
SECONDS_PER_DAY = 86400

# Load contest history
df = pd.read_csv(DATA_FILE)

df["ratingUpdateTimeSeconds"] = pd.to_numeric(
    df["ratingUpdateTimeSeconds"], errors="coerce"
)
df["newRating"] = pd.to_numeric(
    df["newRating"], errors="coerce"
)

df = df.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "newRating"]
).copy()

df["ratingUpdateTimeSeconds"] = (
    df["ratingUpdateTimeSeconds"].astype("int64")
)

# Sort records chronologically and handle duplicate timestamps
df = df.sort_values(
    ["handle", "ratingUpdateTimeSeconds"]
).drop_duplicates(
    subset=["handle", "ratingUpdateTimeSeconds"],
    keep="last"
)

rows = []

for handle, group in df.groupby("handle"):
    times = group["ratingUpdateTimeSeconds"].to_numpy()
    ratings = group["newRating"].to_numpy()

    if len(group) < 2:
        continue

    # Create historical cutoffs every 30 days
    cutoffs = np.arange(
        times[0],
        times[-1] - MIN_TARGET_DAYS * SECONDS_PER_DAY,
        CUTOFF_INTERVAL_DAYS * SECONDS_PER_DAY,
    )

    for cutoff in cutoffs:
        # Get the latest known rating at the cutoff
        before_idx = (
            np.searchsorted(times, cutoff, side="right") - 1
        )

        if before_idx < 0:
            continue

        # Find future ratings between 75 and 105 days later
        start_idx = np.searchsorted(
            times,
            cutoff + MIN_TARGET_DAYS * SECONDS_PER_DAY,
            side="left",
        )

        end_idx = np.searchsorted(
            times,
            cutoff + MAX_TARGET_DAYS * SECONDS_PER_DAY,
            side="right",
        )

        if start_idx >= end_idx:
            continue

        # Use the first rating recorded inside the target window
        target_idx = start_idx

        baseline_rating = float(ratings[before_idx])
        future_rating = float(ratings[target_idx])

        rows.append({
            "handle": handle,
            "cutoff_timestamp": int(cutoff),
            "baseline_rating": baseline_rating,
            "future_rating": future_rating,
            "rating_change": future_rating - baseline_rating,
            "days_to_target": (
                times[target_idx] - cutoff
            ) / SECONDS_PER_DAY,
            "target_timestamp": int(times[target_idx]),
        })

# Build and save the dataset
future_df = pd.DataFrame(rows)

if future_df.empty:
    raise ValueError(
        "No future-rating examples were created. "
        "Check the input data and target window."
    )

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
future_df.to_csv(OUTPUT_FILE, index=False)

# Display results
print("Future-rating dataset created successfully!")
print("Total rows:", len(future_df))
print("Unique users:", future_df["handle"].nunique())
print(
    "Average rating change:",
    round(future_df["rating_change"].mean(), 2),
)
print(
    "Median rating change:",
    round(future_df["rating_change"].median(), 2),
)
print("\nTarget days:")
print(future_df["days_to_target"].describe().round(1).to_string())
print("\nSaved to:", OUTPUT_FILE)
