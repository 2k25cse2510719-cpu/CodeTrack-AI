import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df = pd.read_csv(
    "models/future_rating_v2/personal_baseline_predictions.csv"
)

actual = df["rating_change"].to_numpy()
rf = df["pred_random_forest"].to_numpy()
personal = df["pred_personal_average"].to_numpy()

rows = []

for weight in np.arange(0, 1.01, 0.1):
    pred = weight * rf + (1 - weight) * personal

    rows.append({
        "rf_weight": round(weight, 1),
        "personal_weight": round(1 - weight, 1),
        "MAE": round(np.mean(np.abs(actual - pred)), 2),
        "RMSE": round(np.sqrt(np.mean((actual - pred) ** 2)), 2),
        "R2": round(r2_score(actual, pred), 3),
    })

results = pd.DataFrame(rows).sort_values("MAE")

print("\nENSEMBLE WEIGHT COMPARISON")
print("=" * 60)
print(results.to_string(index=False))

out = Path("models/future_rating_v2")
results.to_csv(out / "ensemble_weight_comparison.csv", index=False)

print("\nSaved to:", out / "ensemble_weight_comparison.csv")
