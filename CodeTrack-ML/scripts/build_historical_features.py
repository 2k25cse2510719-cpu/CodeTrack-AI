import pandas as pd
import numpy as np
from pathlib import Path

CONTEST_FILE = Path("data/codeforces/contest_history.csv")
SNAPSHOT_FILE = Path("data/processed/future_rating_dataset.csv")
OUTPUT_FILE = Path("data/processed/historical_features.csv")

SECONDS_PER_DAY = 86400

contests = pd.read_csv(CONTEST_FILE)
snapshots = pd.read_csv(SNAPSHOT_FILE)

contests["ratingUpdateTimeSeconds"] = pd.to_numeric(
    contests["ratingUpdateTimeSeconds"], errors="coerce"
)
contests["newRating"] = pd.to_numeric(
    contests["newRating"], errors="coerce"
)
contests["oldRating"] = pd.to_numeric(
    contests["oldRating"], errors="coerce"
)
contests["rank"] = pd.to_numeric(
    contests["rank"], errors="coerce"
)

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "newRating"]
).copy()

contests = contests.sort_values(
    ["handle", "ratingUpdateTimeSeconds"]
)

rows = []

for snapshot in snapshots.itertuples(index=False):
    handle = snapshot.handle
    cutoff = int(snapshot.cutoff_timestamp)

    history = contests[
        (contests["handle"] == handle)
        & (contests["ratingUpdateTimeSeconds"] <= cutoff)
    ].copy()

    if history.empty:
        continue

    history = history.sort_values("ratingUpdateTimeSeconds")
    ratings = history["newRating"].astype(float)

    recent = history.tail(5)
    rating_changes = (
        history["newRating"].astype(float)
        - history["oldRating"].astype(float)
    ).dropna()

    # All features below use contest records at or before cutoff.
    row = {
        "handle": handle,
        "cutoff_timestamp": cutoff,
        "baseline_rating": float(ratings.iloc[-1]),
        "historical_contest_count": len(history),
        "historical_average_rating": float(ratings.mean()),
        "historical_max_rating": float(ratings.max()),
        "historical_min_rating": float(ratings.min()),
        "recent_5_contest_average_rating": float(
            recent["newRating"].mean()
        ),
        "recent_5_contest_rating_change": float(
            recent["newRating"].iloc[-1]
            - recent["newRating"].iloc[0]
        ),
        "average_contest_rating_change": (
            float(rating_changes.mean())
            if not rating_changes.empty else 0.0
        ),
        "historical_average_rank": (
            float(history["rank"].mean())
            if history["rank"].notna().any() else np.nan
        ),
        "days_since_last_contest": (
            cutoff - int(history["ratingUpdateTimeSeconds"].iloc[-1])
        ) / SECONDS_PER_DAY,
    }

    # Attach the target columns from the existing snapshot dataset.
    row["future_rating"] = float(snapshot.future_rating)
    row["rating_change"] = float(snapshot.rating_change)
    row["target_timestamp"] = int(snapshot.target_timestamp)
    row["days_to_target"] = float(snapshot.days_to_target)

    rows.append(row)

result = pd.DataFrame(rows)

if result.empty:
    raise ValueError("No historical feature rows were created.")

result = result.sort_values(
    ["handle", "cutoff_timestamp"]
).reset_index(drop=True)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT_FILE, index=False)

print("HISTORICAL FEATURE DATASET CREATED")
print("-" * 40)
print("Rows:", len(result))
print("Users:", result["handle"].nunique())
print("Columns:", len(result.columns))
print("Missing values:")
print(result.isnull().sum().to_string())
print("\nPreview:")
print(result.head(5).to_string(index=False))
print("\nSaved to:", OUTPUT_FILE)
