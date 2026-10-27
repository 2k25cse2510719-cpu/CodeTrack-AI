import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df = pd.read_csv("data/processed/v3/historical_features.csv")

cutoffs = np.sort(df["cutoff_timestamp"].unique())
test_start = cutoffs[int(len(cutoffs) * 0.8)]

train = df[
    (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()

test = df[df["cutoff_timestamp"] >= test_start].copy()

# Rating bands defined in advance.
bins = [-np.inf, 1200, 1600, 2100, 2400, np.inf]
labels = ["below_1200", "1200_1599", "1600_2099", "2100_2399", "2400_plus"]

train["rating_band"] = pd.cut(
    train["baseline_rating"], bins=bins, labels=labels, right=False
)
test["rating_band"] = pd.cut(
    test["baseline_rating"], bins=bins, labels=labels, right=False
)

global_mean = train["rating_change"].mean()
band_means = train.groupby("rating_band", observed=False)["rating_change"].mean()

predictions = {
    "Zero-change": np.zeros(len(test)),
    "Global training mean": np.full(len(test), global_mean),
    "Rating-band training mean": (
        test["rating_band"].map(band_means).astype(float)
        .fillna(global_mean).to_numpy()
    ),
}

y_test = test["rating_change"].to_numpy()

results = []
for name, pred in predictions.items():
    results.append({
        "model": name,
        "MAE": round(mean_absolute_error(y_test, pred), 2),
        "RMSE": round(np.sqrt(mean_squared_error(y_test, pred)), 2),
        "R2": round(r2_score(y_test, pred), 3),
        "mean_prediction": round(float(np.mean(pred)), 2),
    })

print("\nRATING-BAND BASELINE COMPARISON")
print("=" * 65)
print(f"Training samples: {len(train)}")
print(f"Test samples: {len(test)}")
print(f"Training global mean change: {global_mean:.2f}")
print("\nTraining means by rating band:")
print(band_means.round(2).to_string())
print("\nTest results:")
print(pd.DataFrame(results).to_string(index=False))

out = Path("models/future_rating_v3")
out.mkdir(parents=True, exist_ok=True)

pd.DataFrame(results).to_csv(
    out / "rating_band_baseline_metrics.csv", index=False
)

pred_output = test[
    ["handle", "baseline_rating", "rating_band", "rating_change"]
].copy()

for name, pred in predictions.items():
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    pred_output[f"pred_{safe_name}"] = pred

pred_output.to_csv(
    out / "rating_band_baseline_predictions.csv", index=False
)

print("\nSaved metrics and predictions to:", out)
