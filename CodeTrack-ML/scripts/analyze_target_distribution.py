import numpy as np
import pandas as pd
from pathlib import Path

df = pd.read_csv("data/processed/v3/historical_features.csv")

cutoffs = np.sort(df["cutoff_timestamp"].unique())
test_start = cutoffs[int(len(cutoffs) * 0.8)]

train = df[
    (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()

test = df[df["cutoff_timestamp"] >= test_start].copy()

print("\nTARGET DISTRIBUTION ANALYSIS")
print("=" * 65)

for name, data in [("TRAIN", train), ("TEST", test)]:
    changes = data["rating_change"]
    print(f"\n{name}: {len(data)} samples, {data['handle'].nunique()} users")
    print(f"Mean:   {changes.mean():.2f}")
    print(f"Median: {changes.median():.2f}")
    print(f"Std:    {changes.std():.2f}")
    print(f"Min:    {changes.min():.2f}")
    print(f"Max:    {changes.max():.2f}")
    print(f"Increase: {(changes > 0).sum()} ({(changes > 0).mean()*100:.1f}%)")
    print(f"Decrease: {(changes < 0).sum()} ({(changes < 0).mean()*100:.1f}%)")
    print(f"No change: {(changes == 0).sum()}")

print("\nRATING CHANGE BY BASELINE RATING")
print("=" * 65)

bins = [-np.inf, 1200, 1600, 2100, 2400, np.inf]
labels = ["<1200", "1200-1599", "1600-2099", "2100-2399", "2400+"]

for name, data in [("TRAIN", train), ("TEST", test)]:
    data = data.copy()
    data["rating_band"] = pd.cut(
        data["baseline_rating"], bins=bins, labels=labels, right=False
    )
    summary = data.groupby("rating_band", observed=False)["rating_change"].agg(
        ["count", "mean", "median", "std"]
    ).round(2)
    print(f"\n{name}:")
    print(summary.to_string())

print("\nTEST PERIOD: USERS WITH LARGEST TOTAL RATING CHANGES")
print("=" * 65)

user_stats = test.groupby("handle").agg(
    samples=("rating_change", "size"),
    mean_change=("rating_change", "mean"),
    total_change=("rating_change", "sum"),
    mean_baseline=("baseline_rating", "mean"),
).sort_values("total_change")

print("\nLargest total decreases:")
print(user_stats.head(10).round(2).to_string())

print("\nLargest total increases:")
print(user_stats.tail(10).sort_values("total_change", ascending=False).round(2).to_string())

out = Path("models/future_rating_v3")
out.mkdir(parents=True, exist_ok=True)
user_stats.to_csv(out / "test_user_change_summary.csv")

print("\nSaved user summary to:", out / "test_user_change_summary.csv")
