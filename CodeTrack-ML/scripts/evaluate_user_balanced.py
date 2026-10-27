import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES = [
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

DATA = Path("data/processed/v2/historical_features.csv")
CONTESTS = Path("data/codeforces/contest_history.csv")
OUT = Path("models/future_rating_v2/user_balanced_experiment")
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)
contests = pd.read_csv(CONTESTS)

for col in ["cutoff_timestamp", "target_timestamp"]:
    df[col] = pd.to_numeric(df[col], errors="raise")

for col in ["ratingUpdateTimeSeconds", "oldRating", "newRating"]:
    contests[col] = pd.to_numeric(contests[col], errors="coerce")

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "oldRating", "newRating"]
).copy()
contests = contests[contests["oldRating"] > 0].copy()
contests["contest_change"] = contests["newRating"] - contests["oldRating"]
contests = contests.sort_values(["handle", "ratingUpdateTimeSeconds"])

# Same chronological split and target purging as the existing experiment.
cutoffs = np.sort(df["cutoff_timestamp"].unique())
n = len(cutoffs)
validation_start = cutoffs[int(n * 0.60)]
test_start = cutoffs[int(n * 0.80)]

train = df[
    (df["cutoff_timestamp"] < validation_start)
    & (df["target_timestamp"] < validation_start)
].copy()

validation = df[
    (df["cutoff_timestamp"] >= validation_start)
    & (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()

test = df[df["cutoff_timestamp"] >= test_start].copy()

if min(len(train), len(validation), len(test)) == 0:
    raise ValueError("At least one chronological split is empty.")

def personal_predictions(rows):
    predictions = []
    for row in rows.itertuples(index=False):
        history = contests[
            (contests["handle"] == row.handle)
            & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
        ]["contest_change"]
        predictions.append(float(history.mean()) if len(history) else 0.0)
    return np.asarray(predictions)

def score(y, pred):
    return {
        "MAE": round(float(mean_absolute_error(y, pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y, pred))), 2),
        "R2": round(float(r2_score(y, pred)), 3),
    }

# Each user's total training weight is equal to 1.
# Scaling all weights by the same constant does not change their relative influence.
counts = train.groupby("handle")["handle"].transform("size")
user_weights = 1.0 / counts.to_numpy()

models = {
    "Random Forest (standard)": RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
    "Random Forest (user-balanced)": RandomForestRegressor(
        n_estimators=400,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
}

models["Random Forest (standard)"].fit(
    train[FEATURES], train["rating_change"]
)
models["Random Forest (user-balanced)"].fit(
    train[FEATURES], train["rating_change"], sample_weight=user_weights
)

y_val = validation["rating_change"].to_numpy()
y_test = test["rating_change"].to_numpy()

predictions = {
    "Zero-change baseline": {
        "validation": np.zeros(len(validation)),
        "test": np.zeros(len(test)),
    },
    "Personal historical average": {
        "validation": personal_predictions(validation),
        "test": personal_predictions(test),
    },
}

for name, model in models.items():
    predictions[name] = {
        "validation": model.predict(validation[FEATURES]),
        "test": model.predict(test[FEATURES]),
    }

# Validation metrics guide the next decision; final test metrics are recorded
# for transparency but must not be used to select a model.
rows = []
for name, pred in predictions.items():
    rows.append({
        "model": name,
        **{f"validation_{k}": v for k, v in score(y_val, pred["validation"]).items()},
        **{f"test_{k}": v for k, v in score(y_test, pred["test"]).items()},
    })

results = pd.DataFrame(rows)
results.to_csv(OUT / "comparison_metrics.csv", index=False)

validation_output = validation[
    ["handle", "cutoff_timestamp", "baseline_rating", "rating_change"]
].copy()
for name, pred in predictions.items():
    col = "pred_" + (
        name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "_")
    )
    validation_output[col] = pred["validation"]
validation_output.to_csv(OUT / "validation_predictions.csv", index=False)

test_output = test[
    ["handle", "cutoff_timestamp", "baseline_rating", "rating_change"]
].copy()
for name, pred in predictions.items():
    col = "pred_" + (
        name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "_")
    )
    test_output[col] = pred["test"]
test_output.to_csv(OUT / "test_predictions.csv", index=False)

metadata = {
    "train_rows": len(train),
    "validation_rows": len(validation),
    "test_rows": len(test),
    "train_users": int(train["handle"].nunique()),
    "validation_users": int(validation["handle"].nunique()),
    "test_users": int(test["handle"].nunique()),
    "train_targets_before_validation": bool(
        train["target_timestamp"].max() < validation_start
    ),
    "validation_targets_before_test": bool(
        validation["target_timestamp"].max() < test_start
    ),
    "weighting": "Each training user's sample weights sum to 1.",
    "warning": "Use validation metrics for model choice; test metrics are final holdout diagnostics.",
}
with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print("\nUSER-BALANCED EXPERIMENT")
print("=" * 80)
print(json.dumps(metadata, indent=2))
print("\nMetrics:")
print(results.to_string(index=False))
print("\nSaved results to:", OUT)
