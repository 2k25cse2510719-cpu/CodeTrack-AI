import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PREDICTIONS = Path("models/future_rating_v2/test_predictions.csv")
CONTESTS = Path("data/codeforces/contest_history.csv")
OUTPUT = Path("models/future_rating_v2/recent_baseline_predictions.csv")

df = pd.read_csv(PREDICTIONS)
contests = pd.read_csv(CONTESTS)

for col in ["ratingUpdateTimeSeconds", "oldRating", "newRating"]:
    contests[col] = pd.to_numeric(contests[col], errors="coerce")

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "oldRating", "newRating"]
)

# Ignore initial ratings because they aren't ordinary contest-to-contest changes.
contests = contests[contests["oldRating"] > 0].copy()
contests["contest_change"] = contests["newRating"] - contests["oldRating"]
contests = contests.sort_values(["handle", "ratingUpdateTimeSeconds"])

# Calculate past-only predictions for each test row.
full_avg, recent5, recent10 = [], [], []

for row in df.itertuples(index=False):
    history = contests[
        (contests["handle"] == row.handle)
        & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
    ]["contest_change"]

    full_avg.append(float(history.mean()) if len(history) else 0.0)
    recent5.append(float(history.tail(5).mean()) if len(history) else 0.0)
    recent10.append(float(history.tail(10).mean()) if len(history) else 0.0)

df["pred_full_historical_average"] = full_avg
df["pred_recent_5_average"] = recent5
df["pred_recent_10_average"] = recent10

y = df["rating_change"]

models = {
    "Zero-change baseline": np.zeros(len(df)),
    "Random Forest": df["pred_random_forest"].to_numpy(),
    "Full historical average": df["pred_full_historical_average"].to_numpy(),
    "Recent 5-contest average": df["pred_recent_5_average"].to_numpy(),
    "Recent 10-contest average": df["pred_recent_10_average"].to_numpy(),
}

print("RECENT-PERFORMANCE BASELINE COMPARISON")
print("=" * 75)
print(f"{'Model':30s} {'MAE':>9s} {'RMSE':>9s} {'R2':>9s}")

results = []

for name, pred in models.items():
    mae = mean_absolute_error(y, pred)
    rmse = np.sqrt(mean_squared_error(y, pred))
    r2 = r2_score(y, pred)

    results.append({
        "model": name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
    })

    print(f"{name:30s} {mae:9.2f} {rmse:9.2f} {r2:9.3f}")

result_df = pd.DataFrame(results).sort_values("MAE")
result_df.to_csv(
    "models/future_rating_v2/recent_baseline_metrics.csv",
    index=False
)
df.to_csv(OUTPUT, index=False)

print("\nBest MAE:", result_df.iloc[0]["model"])
print("Saved metrics to models/future_rating_v2/recent_baseline_metrics.csv")
print("Saved predictions to", OUTPUT)
