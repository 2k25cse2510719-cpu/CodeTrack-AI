"""Chronological evaluation of the corrected V1 future-rating-change model.

Run from the CodeTrack-ML directory:
    python .\scripts\evaluate_future_v1_chronological.py

This evaluator does not overwrite the existing V1 or V2 artifacts.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline

DATA_FILE = Path("data/processed/historical_features.csv")
OUTPUT_DIR = Path("models/future_rating_v1_chronological")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# The 10 verified, cutoff-time features from the corrected V1 model.
FEATURES = [
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
TARGET = "rating_change"
REQUIRED = ["handle", "cutoff_timestamp", "target_timestamp", TARGET, *FEATURES]

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Could not find {DATA_FILE}. Run this script from the CodeTrack-ML directory."
    )

df = pd.read_csv(DATA_FILE)
missing = sorted(set(REQUIRED) - set(df.columns))
if missing:
    raise ValueError(f"Dataset is missing required columns: {missing}")

for col in ["cutoff_timestamp", "target_timestamp", TARGET, *FEATURES]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["handle", "cutoff_timestamp", "target_timestamp", TARGET]).copy()
df[FEATURES] = df[FEATURES].replace([np.inf, -np.inf], np.nan)

# Hold out the latest 20% of unique cutoff timestamps. Purge training rows
# whose target is on/after the first test cutoff to prevent temporal overlap.
cutoffs = np.sort(df["cutoff_timestamp"].unique())
if len(cutoffs) < 2:
    raise ValueError("Not enough unique cutoff timestamps for a chronological split.")
test_start = cutoffs[int(len(cutoffs) * 0.80)]

train = df[
    (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()
test = df[df["cutoff_timestamp"] >= test_start].copy()
if train.empty or test.empty:
    raise ValueError("Chronological split produced an empty train or test set.")
if not (train["target_timestamp"].max() < test_start):
    raise AssertionError("Temporal purge failed: a training target reaches the test period.")

X_train = train[FEATURES]
y_train = train[TARGET]
X_test = test[FEATURES]
y_test = test[TARGET]

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
rf_predictions = model.predict(X_test)
baseline_predictions = np.zeros(len(test), dtype=float)


def score(y_true, y_pred):
    return {
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "R2": round(float(r2_score(y_true, y_pred)), 3),
    }

results = {
    "experiment": "Corrected V1 chronological evaluation",
    "target": TARGET,
    "features": FEATURES,
    "split": {
        "strategy": "latest 20% of unique cutoff timestamps; purge train targets reaching test period",
        "test_start_timestamp": int(test_start),
        "unique_cutoff_timestamps": int(len(cutoffs)),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_users": int(train["handle"].nunique()),
        "test_users": int(test["handle"].nunique()),
        "latest_train_target_before_test": bool(train["target_timestamp"].max() < test_start),
    },
    "target_distribution": {
        "train_mean_change": round(float(y_train.mean()), 2),
        "test_mean_change": round(float(y_test.mean()), 2),
        "test_median_change": round(float(y_test.median()), 2),
    },
    "models": {
        "Zero-change baseline": score(y_test, baseline_predictions),
        "Corrected V1 Random Forest": score(y_test, rf_predictions),
    },
    "notes": [
        "This is a chronological evaluation, not directly comparable to the original random user-held-out V1 score.",
        "The zero-change baseline is evaluated on exactly the same V1 test rows.",
        "No hyperparameter search is performed; existing V1/V2 artifacts are not modified.",
    ],
}

predictions = test[
    ["handle", "cutoff_timestamp", "target_timestamp", "baseline_rating", "future_rating", TARGET]
].copy()
predictions["pred_zero_change_baseline"] = baseline_predictions
predictions["pred_corrected_v1_random_forest"] = rf_predictions
predictions.to_csv(OUTPUT_DIR / "test_predictions.csv", index=False)
with (OUTPUT_DIR / "metrics.json").open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("CORRECTED V1 CHRONOLOGICAL EVALUATION")
print("=" * 48)
print(json.dumps(results, indent=2))
print(f"\nSaved metrics: {OUTPUT_DIR / 'metrics.json'}")
print(f"Saved predictions: {OUTPUT_DIR / 'test_predictions.csv'}")
