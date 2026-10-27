import pandas as pd
import numpy as np
from pathlib import Path

target_path = Path("data/processed/v2/future_rating_dataset.csv")
feature_path = Path("data/processed/v2/historical_features.csv")
contest_path = Path("data/codeforces/contest_history.csv")

targets = pd.read_csv(target_path)
features = pd.read_csv(feature_path)
contests = pd.read_csv(contest_path)

# Check target and feature rows match
key = ["handle", "cutoff_timestamp"]
merged = features.merge(
    targets,
    on=key,
    how="outer",
    suffixes=("_feature", "_target"),
    indicator=True
)

print("V2 DATA VALIDATION")
print("-" * 45)
print("Target rows:", len(targets))
print("Feature rows:", len(features))
print("Unmatched rows:", int((merged["_merge"] != "both").sum()))

both = merged[merged["_merge"] == "both"]

baseline_mismatches = (
    both["baseline_rating_feature"] != both["baseline_rating_target"]
).sum()

target_mismatches = (
    both["future_rating_feature"] != both["future_rating_target"]
).sum()

change_mismatches = (
    both["rating_change_feature"] != both["rating_change_target"]
).sum()

print("Baseline mismatches:", int(baseline_mismatches))
print("Future-rating mismatches:", int(target_mismatches))
print("Rating-change mismatches:", int(change_mismatches))

print("Missing feature values:", int(features.isna().sum().sum()))
print(
    "Duplicate feature keys:",
    int(features.duplicated(key).sum())
)

print(
    "Target horizon within 75-105 days:",
    bool(features["days_to_target"].between(75, 105).all())
)

# Independently verify each baseline against the last contest
# rating at or before its cutoff.
contests["ratingUpdateTimeSeconds"] = pd.to_numeric(
    contests["ratingUpdateTimeSeconds"], errors="coerce"
)
contests["newRating"] = pd.to_numeric(
    contests["newRating"], errors="coerce"
)

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "newRating"]
)

baseline_errors = 0
checked = 0

for handle, group in contests.groupby("handle"):
    group = group.sort_values("ratingUpdateTimeSeconds")
    user_features = features[features["handle"] == handle]

    times = group["ratingUpdateTimeSeconds"].to_numpy()
    ratings = group["newRating"].to_numpy()

    for row in user_features.itertuples(index=False):
        idx = np.searchsorted(
            times, row.cutoff_timestamp, side="right"
        ) - 1

        if idx < 0:
            baseline_errors += 1
            continue

        checked += 1
        if not np.isclose(
            ratings[idx], row.baseline_rating, atol=0.01
        ):
            baseline_errors += 1

print("Baselines independently checked:", checked)
print("Independent baseline errors:", baseline_errors)

passed = (
    (merged["_merge"] == "both").all()
    and baseline_mismatches == 0
    and target_mismatches == 0
    and change_mismatches == 0
    and features.isna().sum().sum() == 0
    and features.duplicated(key).sum() == 0
    and features["days_to_target"].between(75, 105).all()
    and baseline_errors == 0
)

print("\nVALIDATION RESULT:", "PASS" if passed else "FAIL")

if not passed:
    raise SystemExit("Fix validation failures before model training.")
