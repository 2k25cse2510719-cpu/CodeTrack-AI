import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error

path = Path("models/future_rating_v2/user_balanced_experiment")
df = pd.read_csv(path / "validation_predictions.csv")

models = {
    "Standard RF": "pred_random_forest_standard",
    "User-balanced RF": "pred_random_forest_user_balanced",
    "Personal average": "pred_personal_historical_average",
    "Zero baseline": "pred_zero_change_baseline",
}

# Calculate MAE separately for each user.
records = []

for handle, group in df.groupby("handle"):
    row = {"handle": handle, "samples": len(group)}

    for name, column in models.items():
        row[name] = mean_absolute_error(
            group["rating_change"],
            group[column]
        )

    records.append(row)

per_user = pd.DataFrame(records)

# Each user contributes equally to these aggregate comparisons.
print("\nPER-USER VALIDATION SUMMARY")
print("=" * 75)

for name in models:
    print(
        f"{name:20s} | "
        f"Mean user MAE: {per_user[name].mean():.2f} | "
        f"Median user MAE: {per_user[name].median():.2f}"
    )

standard_wins = (per_user["Standard RF"] < per_user["User-balanced RF"]).sum()
balanced_wins = (per_user["User-balanced RF"] < per_user["Standard RF"]).sum()
ties = (per_user["User-balanced RF"] == per_user["Standard RF"]).sum()

print("\nUSER-BALANCING COMPARISON")
print(f"Users where standard RF has lower MAE: {standard_wins}")
print(f"Users where balanced RF has lower MAE: {balanced_wins}")
print(f"Ties: {ties}")
print(f"Total users: {len(per_user)}")

print("\nBIGGEST IMPROVEMENTS FROM USER BALANCING")
per_user["improvement"] = per_user["Standard RF"] - per_user["User-balanced RF"]
print(
    per_user.sort_values("improvement", ascending=False)
    .head(10)[["handle", "samples", "Standard RF", "User-balanced RF", "improvement"]]
    .round(2).to_string(index=False)
)

print("\nBIGGEST REGRESSIONS FROM USER BALANCING")
print(
    per_user.sort_values("improvement")
    .head(10)[["handle", "samples", "Standard RF", "User-balanced RF", "improvement"]]
    .round(2).to_string(index=False)
)

per_user.to_csv(path / "per_user_validation_metrics.csv", index=False)
print("\nSaved per-user results to:", path / "per_user_validation_metrics.csv")
