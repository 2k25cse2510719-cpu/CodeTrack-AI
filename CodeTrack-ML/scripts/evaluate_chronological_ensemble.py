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
OUT = Path("models/future_rating_v2/chronological_ensemble")
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

# Ignore initial ratings; use only ordinary contest-to-contest changes.
contests = contests[contests["oldRating"] > 0].copy()
contests["contest_change"] = contests["newRating"] - contests["oldRating"]
contests = contests.sort_values(["handle", "ratingUpdateTimeSeconds"])

# Three chronological periods based on unique cutoff dates.
cutoffs = np.sort(df["cutoff_timestamp"].unique())
n = len(cutoffs)
train_end = cutoffs[int(n * 0.60)]
validation_start = cutoffs[int(n * 0.60)]
validation_end = cutoffs[int(n * 0.80)]
test_start = cutoffs[int(n * 0.80)]

train = df[
    (df["cutoff_timestamp"] < train_end)
    & (df["target_timestamp"] < validation_start)
].copy()

validation = df[
    (df["cutoff_timestamp"] >= validation_start)
    & (df["cutoff_timestamp"] < validation_end)
    & (df["target_timestamp"] < test_start)
].copy()

test = df[df["cutoff_timestamp"] >= test_start].copy()

if min(len(train), len(validation), len(test)) == 0:
    raise ValueError(
        f"Empty split: train={len(train)}, validation={len(validation)}, test={len(test)}"
    )

# Personal average must use contest history available by each cutoff.
def personal_predictions(rows):
    result = []
    for row in rows.itertuples(index=False):
        history = contests[
            (contests["handle"] == row.handle)
            & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
        ]["contest_change"]
        result.append(float(history.mean()) if len(history) else 0.0)
    return np.asarray(result)

personal_val = personal_predictions(validation)
personal_test = personal_predictions(test)

# Fit Random Forest only on the training period.
model = RandomForestRegressor(
    n_estimators=400,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)
model.fit(train[FEATURES], train["rating_change"])

rf_val = model.predict(validation[FEATURES])
rf_test = model.predict(test[FEATURES])

y_val = validation["rating_change"].to_numpy()
y_test = test["rating_change"].to_numpy()

# Select the weight using validation MAE only.
weight_results = []
for weight in np.round(np.arange(0, 1.01, 0.1), 1):
    pred = weight * rf_val + (1 - weight) * personal_val
    weight_results.append({
        "rf_weight": float(weight),
        "personal_weight": round(1 - float(weight), 1),
        "MAE": float(mean_absolute_error(y_val, pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_val, pred))),
    })

weight_df = pd.DataFrame(weight_results).sort_values(
    ["MAE", "RMSE"], ascending=True
)
best_weight = float(weight_df.iloc[0]["rf_weight"])

# Evaluate the selected weight on final test data.
predictions = {
    "Zero-change baseline": np.zeros(len(test)),
    "Random Forest": rf_test,
    "Personal historical average": personal_test,
    "Selected ensemble": (
        best_weight * rf_test + (1 - best_weight) * personal_test
    ),
}

def score(y, pred):
    return {
        "MAE": round(float(mean_absolute_error(y, pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y, pred))), 2),
        "R2": round(float(r2_score(y, pred)), 3),
    }

metrics = {
    "split_rows": {
        "train": int(len(train)),
        "validation": int(len(validation)),
        "test": int(len(test)),
    },
    "split_users": {
        "train": int(train["handle"].nunique()),
        "validation": int(validation["handle"].nunique()),
        "test": int(test["handle"].nunique()),
    },
    "boundaries": {
        "train_end_cutoff": int(train_end),
        "validation_start_cutoff": int(validation_start),
        "validation_end_cutoff": int(validation_end),
        "test_start_cutoff": int(test_start),
        "train_targets_before_validation": bool(
            train["target_timestamp"].max() < validation_start
        ),
        "validation_targets_before_test": bool(
            validation["target_timestamp"].max() < test_start
        ),
    },
    "selected_rf_weight": best_weight,
    "selected_personal_weight": round(1 - best_weight, 1),
    "validation_best_mae": round(float(weight_df.iloc[0]["MAE"]), 2),
    "final_test_metrics": {
        name: score(y_test, pred)
        for name, pred in predictions.items()
    },
}

weight_df.to_csv(OUT / "validation_weight_results.csv", index=False)

output = test[
    ["handle", "cutoff_timestamp", "baseline_rating", "future_rating", "rating_change"]
].copy()
output["pred_random_forest"] = rf_test
output["pred_personal_average"] = personal_test
output["pred_selected_ensemble"] = predictions["Selected ensemble"]
output["pred_zero_change"] = predictions["Zero-change baseline"]
output.to_csv(OUT / "test_predictions.csv", index=False)

with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print("\nCHRONOLOGICAL ENSEMBLE EVALUATION")
print("=" * 60)
print(json.dumps(metrics, indent=2))
print("\nValidation weight search:")
print(weight_df.round(2).to_string(index=False))
print("\nSaved results to:", OUT)
