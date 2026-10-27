import json
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path("data/processed/v3/historical_features.csv")
OUT = Path("models/future_rating_v3")
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)
df["cutoff_timestamp"] = pd.to_numeric(df["cutoff_timestamp"])
df["target_timestamp"] = pd.to_numeric(df["target_timestamp"])

cutoffs = np.sort(df["cutoff_timestamp"].unique())
test_start = cutoffs[int(len(cutoffs) * 0.8)]

train = df[
    (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()

test = df[df["cutoff_timestamp"] >= test_start].copy()

features = [
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
    "recent_5_change_mean",
    "recent_5_change_std",
    "recent_10_change_mean",
    "recent_10_change_std",
    "recent_10_rating_range",
    "peak_drawdown",
]

X_train = train[features]
y_train = train["rating_change"]
X_test = test[features]
y_test = test["rating_change"]

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

predictions = {"Zero-change baseline": np.zeros(len(test))}

for name, model in models.items():
    model.fit(X_train, y_train)
    predictions[name] = model.predict(X_test)

def score(y, pred):
    return {
        "MAE": round(float(mean_absolute_error(y, pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y, pred))), 2),
        "R2": round(float(r2_score(y, pred)), 3),
    }

results = {
    "train_rows": int(len(train)),
    "test_rows": int(len(test)),
    "train_users": int(train["handle"].nunique()),
    "test_users": int(test["handle"].nunique()),
    "latest_train_target_before_test": bool(
        train["target_timestamp"].max() < test_start
    ),
    "models": {
        name: score(y_test, pred)
        for name, pred in predictions.items()
    },
}

print("V3 RATING-CHANGE EVALUATION")
print("=" * 50)
print(json.dumps(results, indent=2))

output = test[
    ["handle", "cutoff_timestamp", "baseline_rating", "future_rating", "rating_change"]
].copy()

for name, pred in predictions.items():
    output["pred_" + name.lower().replace(" ", "_").replace("-", "_")] = pred

output.to_csv(OUT / "test_predictions.csv", index=False)

with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nSaved to:", OUT)
