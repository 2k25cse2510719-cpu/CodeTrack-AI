import numpy as np
import pandas as pd
from pathlib import Path

CONTEST_FILE = Path("data/codeforces/contest_history.csv")
TARGET_FILE = Path("data/processed/v2/future_rating_dataset.csv")
OUTPUT_FILE = Path("models/future_rating_v2/target_audit_details.csv")

SECONDS_PER_DAY = 86400
MIN_DAYS = 75
MAX_DAYS = 105
TARGET_DAYS = 90

contests = pd.read_csv(CONTEST_FILE)
targets = pd.read_csv(TARGET_FILE)

for col in ["ratingUpdateTimeSeconds", "newRating"]:
    contests[col] = pd.to_numeric(contests[col], errors="coerce")

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

groups = {
    handle: group.sort_values("ratingUpdateTimeSeconds")
    for handle, group in contests.groupby("handle")
}

checks = []

for row in targets.itertuples(index=False):
    group = groups.get(row.handle)

    if group is None:
        checks.append({
            "handle": row.handle,
            "cutoff_timestamp": row.cutoff_timestamp,
            "status": "USER_NOT_FOUND",
        })
        continue

    times = group["ratingUpdateTimeSeconds"].to_numpy()
    ratings = group["newRating"].to_numpy(dtype=float)

    baseline_idx = np.searchsorted(
        times, row.cutoff_timestamp, side="right"
    ) - 1

    min_time = row.cutoff_timestamp + MIN_DAYS * SECONDS_PER_DAY
    max_time = row.cutoff_timestamp + MAX_DAYS * SECONDS_PER_DAY
    target_time = row.cutoff_timestamp + TARGET_DAYS * SECONDS_PER_DAY

    start_idx = np.searchsorted(times, min_time, side="left")
    end_idx = np.searchsorted(times, max_time, side="right")

    if baseline_idx < 0 or start_idx >= end_idx:
        checks.append({
            "handle": row.handle,
            "cutoff_timestamp": row.cutoff_timestamp,
            "status": "NO_VALID_BASELINE_OR_TARGET",
        })
        continue

    candidates = np.arange(start_idx, end_idx)
    target_idx = candidates[
        np.argmin(np.abs(times[candidates] - target_time))
    ]

    expected_baseline = float(ratings[baseline_idx])
    expected_future = float(ratings[target_idx])
    expected_timestamp = int(times[target_idx])
    expected_days = (expected_timestamp - row.cutoff_timestamp) / SECONDS_PER_DAY

    checks.append({
        "handle": row.handle,
        "cutoff_timestamp": row.cutoff_timestamp,
        "status": "CHECKED",
        "baseline_match": np.isclose(
            row.baseline_rating, expected_baseline, atol=0.01
        ),
        "future_rating_match": np.isclose(
            row.future_rating, expected_future, atol=0.01
        ),
        "target_timestamp_match": (
            int(row.target_timestamp) == expected_timestamp
        ),
        "rating_change_match": np.isclose(
            row.rating_change,
            expected_future - expected_baseline,
            atol=0.01,
        ),
        "days_to_target_match": np.isclose(
            row.days_to_target, expected_days, atol=1e-8
        ),
        "horizon_valid": MIN_DAYS <= expected_days <= MAX_DAYS,
        "target_strictly_future": expected_timestamp > row.cutoff_timestamp,
        "expected_days_to_target": expected_days,
    })

result = pd.DataFrame(checks)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT_FILE, index=False)

checked = result[result["status"] == "CHECKED"]
check_cols = [
    "baseline_match",
    "future_rating_match",
    "target_timestamp_match",
    "rating_change_match",
    "days_to_target_match",
    "horizon_valid",
    "target_strictly_future",
]

print("\nINDEPENDENT V2 TARGET AUDIT")
print("=" * 60)
print("Saved target rows:", len(targets))
print("Rows independently checked:", len(checked))
print("Rows not checked:", len(result) - len(checked))

for col in check_cols:
    print(f"{col}: {int(checked[col].fillna(False).sum())} / {len(checked)} passed")

print("\nMismatch counts:")
for col in check_cols:
    print(f"{col}: {int((~checked[col].fillna(False)).sum())}")

print("\nDays-to-target summary:")
print(checked["expected_days_to_target"].describe().round(2).to_string())

print("\nDetailed audit saved to:", OUTPUT_FILE)
