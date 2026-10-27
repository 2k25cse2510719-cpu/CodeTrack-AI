import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

path = Path("models/future_rating_v2/personal_baseline_history_details.csv")
df = pd.read_csv(path)

actual = df["rating_change"].to_numpy()
personal = df["pred_personal_average"].to_numpy()
counts = df["historical_contest_count_at_cutoff"].to_numpy()

rows = []

for k in [0, 5, 10, 20, 40, 80, 160]:
    if k == 0:
        pred = personal.copy()
    else:
        pred = (counts / (counts + k)) * personal

    rows.append({
        "k": k,
        "MAE": round(mean_absolute_error(actual, pred), 2),
        "RMSE": round(np.sqrt(mean_squared_error(actual, pred)), 2),
        "R2": round(r2_score(actual, pred), 3),
        "mean_prediction": round(float(pred.mean()), 2),
    })

# Zero-change baseline for reference.
rows.append({
    "k": "zero baseline",
    "MAE": round(mean_absolute_error(actual, np.zeros(len(actual))), 2),
    "RMSE": round(np.sqrt(mean_squared_error(actual, np.zeros(len(actual)))), 2),
    "R2": round(r2_score(actual, np.zeros(len(actual))), 3),
    "mean_prediction": 0.0,
})

results = pd.DataFrame(rows)

print("\nPERSONAL-AVERAGE SHRINKAGE EXPERIMENT")
print("=" * 65)
print(results.to_string(index=False))

out = Path("models/future_rating_v2")
results.to_csv(out / "personal_shrinkage_diagnostic.csv", index=False)

print("\nSaved to:", out / "personal_shrinkage_diagnostic.csv")
