import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

path = Path("models/future_rating_v2/personal_baseline_predictions.csv")
df = pd.read_csv(path)

actual = df["rating_change"].to_numpy()
rf = df["pred_random_forest"].to_numpy()
personal = df["pred_personal_average"].to_numpy()
zero = df["pred_zero_change_baseline"].to_numpy()

predictions = {
    "Zero-change baseline": zero,
    "Random Forest": rf,
    "Personal historical average": personal,
    "50/50 ensemble": 0.5 * rf + 0.5 * personal,
}

rows = []

for name, pred in predictions.items():
    rows.append({
        "model": name,
        "MAE": round(mean_absolute_error(actual, pred), 2),
        "RMSE": round(np.sqrt(mean_squared_error(actual, pred)), 2),
        "R2": round(r2_score(actual, pred), 3),
        "mean_prediction": round(float(np.mean(pred)), 2),
    })

results = pd.DataFrame(rows).sort_values("MAE")

print("\nSAME-TEST-SET MODEL COMPARISON")
print("=" * 65)
print(f"Samples: {len(df)}")
print(results.to_string(index=False))

out = Path("models/future_rating_v2")
results.to_csv(out / "ensemble_comparison.csv", index=False)

print("\nSaved to:", out / "ensemble_comparison.csv")
