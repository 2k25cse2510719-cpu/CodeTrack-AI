import json
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

DATA = Path("data/processed/v2/historical_features.csv")
OUT_DIR = Path("models/future_rating_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)
df["cutoff_timestamp"] = pd.to_numeric(df["cutoff_timestamp"])
df["target_timestamp"] = pd.to_numeric(df["target_timestamp"])

# Chronological holdout: latest 20% of unique cutoff dates.
cutoffs = np.sort(df["cutoff_timestamp"].unique())
split_idx = int(len(cutoffs) * 0.8)
test_start = cutoffs[split_idx]

test = df[df["cutoff_timestamp"] >= test_start].copy()

# Purge training samples whose future target reaches the test period.
train = df[
    (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()

feature_cols = [
    "baseline_rating",
    "historical_contest_count",
    "historical_average_rating",
    "historical_max_rating",
    "historical_min_rating",
    "recent_3_contest_average_rating",
    "recent_5_contest_average_rating",
    "recent_5_contest_rating_trend",
    "average_contest_rating_change",
    "rating_change_std",
    "historical_average_rank",
    "days_since_last_contest",
    "contests_last_90_days",
    "contests_last_180_days",
]

target_col = "rating_change"

X_train = train[feature_cols]
y_train = train[target_col]
X_test = test[feature_cols]
y_test = test[target_col]

if len(train) == 0 or len(test) == 0:
    raise ValueError("Train/test split is empty.")

models = {
    "Linear Regression": make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LinearRegression()
    ),
    "Random Forest": make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestRegressor(
            n_estimators=400,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1
        )
    ),
}

predictions = {
    "Zero-change baseline": np.zeros(len(test))
}

for name, model in models.items():
    model.fit(X_train, y_train)
    predictions[name] = model.predict(X_test)

def metrics(y_true, y_pred):
    return {
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "R2": round(float(r2_score(y_true, y_pred)), 3),
    }

results = {
    "split": {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_users": int(train["handle"].nunique()),
        "test_users": int(test["handle"].nunique()),
        "test_start_timestamp": int(test_start),
        "latest_train_target_before_test": bool(
            train["target_timestamp"].max() < test_start
        ),
    },
    "target_distribution": {
        "train_mean_change": round(float(y_train.mean()), 2),
        "test_mean_change": round(float(y_test.mean()), 2),
        "test_median_change": round(float(y_test.median()), 2),
    },
    "models": {
        name: metrics(y_test, pred)
        for name, pred in predictions.items()
    },
}

print("V2 CHRONOLOGICAL EVALUATION")
print("=" * 50)
print(json.dumps(results, indent=2))

# Save test predictions for error analysis.
pred_df = test[
    ["handle", "cutoff_timestamp", "baseline_rating", "future_rating", "rating_change"]
].copy()

for name, pred in predictions.items():
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    pred_df[f"pred_{safe_name}"] = pred

pred_df.to_csv(OUT_DIR / "test_predictions.csv", index=False)

with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nSaved predictions and metrics to:", OUT_DIR)
