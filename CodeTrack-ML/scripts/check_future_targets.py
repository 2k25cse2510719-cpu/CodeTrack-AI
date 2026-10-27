import pandas as pd

snapshots = pd.read_csv("data/processed/future_rating_dataset.csv")
features = pd.read_csv("data/processed/historical_features.csv")

print("TARGET WINDOW CHECK")
print("-" * 40)
print("Target days:")
print(snapshots["days_to_target"].describe().round(2).to_string())

print("\nTarget timestamp consistency:")
expected_days = (
    snapshots["target_timestamp"] - snapshots["cutoff_timestamp"]
) / 86400

print("Maximum days discrepancy:",
      round((expected_days - snapshots["days_to_target"]).abs().max(), 8))

print("\nBASELINE RATING CHECK")
print("-" * 40)

merged = snapshots.merge(
    features[["handle", "cutoff_timestamp", "baseline_rating"]],
    on=["handle", "cutoff_timestamp"],
    how="left",
    suffixes=("_target", "_feature"),
)

mismatch = (
    merged["baseline_rating_target"] - merged["baseline_rating_feature"]
).abs() > 0.001

print("Rows checked:", len(merged))
print("Missing feature baselines:", merged["baseline_rating_feature"].isna().sum())
print("Baseline mismatches:", int(mismatch.sum()))

print("\nRating change consistency:")
difference = (
    snapshots["future_rating"] - snapshots["baseline_rating"]
    - snapshots["rating_change"]
)
print("Inconsistent targets:", int((difference.abs() > 0.001).sum()))
