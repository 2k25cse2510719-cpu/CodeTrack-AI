import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_FILE = Path("data/processed/historical_features.csv")
OUTPUT_DIR = Path("models/future_rating_v1_clean")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

features = [
    "baseline_rating",
    "historical_contest_count",
    "historical_average_rating",
    "historical_max_rating",
    "historical_min_rating",
    "recent_5_contest_average_rating",
    "recent_5_contest_rating_trend",
    "average_contest_rating_change",
    "historical_average_rank",
    "days_since_last_contest",
]

X = df[features].replace([np.inf, -np.inf], np.nan)
y = df["rating_change"]
groups = df["handle"]

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42,
)
train_idx, test_idx = next(splitter.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

model = make_pipeline(
    SimpleImputer(strategy="median"),
    RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

metrics = {
    "model": "RandomForestRegressor",
    "target": "rating_change",
    "test_strategy": "GroupShuffleSplit by handle",
    "train_rows": int(len(train_idx)),
    "test_rows": int(len(test_idx)),
    "train_users": int(groups.iloc[train_idx].nunique()),
    "test_users": int(groups.iloc[test_idx].nunique()),
    "mae": float(mean_absolute_error(y_test, predictions)),
    "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
    "r2": float(r2_score(y_test, predictions)),
    "features": features,
}

joblib.dump(model, OUTPUT_DIR / "model.joblib")

with open(OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=4)

print("Saved initial future-rating experiment.")
print("Model:", OUTPUT_DIR / "model.joblib")
print("Metrics:", OUTPUT_DIR / "metrics.json")
print("MAE:", round(metrics["mae"], 2))
print("RMSE:", round(metrics["rmse"], 2))
print("R²:", round(metrics["r2"], 3))
print("\nReminder: this is an initial user-held-out evaluation.")
