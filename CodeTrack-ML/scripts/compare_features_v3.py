import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df = pd.read_csv("data/processed/v3/historical_features.csv")

cutoffs = np.sort(df["cutoff_timestamp"].unique())
test_start = cutoffs[int(len(cutoffs) * 0.8)]

train = df[
    (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()
test = df[df["cutoff_timestamp"] >= test_start].copy()

old_features = [
    "baseline_rating", "historical_contest_count",
    "historical_average_rating", "historical_max_rating",
    "historical_min_rating", "recent_3_contest_average_rating",
    "recent_5_contest_average_rating", "recent_5_contest_rating_trend",
    "average_contest_rating_change", "rating_change_std",
    "historical_average_rank", "days_since_last_contest",
    "contests_last_90_days", "contests_last_180_days",
]

new_features = [
    "recent_5_change_mean", "recent_5_change_std",
    "recent_10_change_mean", "recent_10_change_std",
    "recent_10_rating_range", "peak_drawdown",
]

y_train = train["rating_change"]
y_test = test["rating_change"]
results = []
importance = None

for name, cols in [
    ("V2 features only", old_features),
    ("V3 features only", old_features + new_features),
]:
    model = RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
    model.fit(train[cols], y_train)
    pred = model.predict(test[cols])

    results.append({
        "model": name,
        "features": len(cols),
        "MAE": round(mean_absolute_error(y_test, pred), 2),
        "RMSE": round(np.sqrt(mean_squared_error(y_test, pred)), 2),
        "R2": round(r2_score(y_test, pred), 3),
    })

    if name == "V3 features only":
        importance = pd.DataFrame({
            "feature": cols,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)

out = Path("models/future_rating_v3")
out.mkdir(parents=True, exist_ok=True)
importance.to_csv(out / "feature_importance.csv", index=False)

print("\nFEATURE COMPARISON")
print("=" * 55)
print(pd.DataFrame(results).to_string(index=False))
print("\nTOP 10 V3 FEATURES")
print(importance.head(10).to_string(index=False))
print("\nSaved feature importance to:", out / "feature_importance.csv")
