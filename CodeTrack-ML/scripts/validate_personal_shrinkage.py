import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA = Path("data/processed/v2/historical_features.csv")
CONTESTS = Path("data/codeforces/contest_history.csv")
OUT = Path("models/future_rating_v2/chronological_shrinkage")
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
    raise ValueError(
        f"Empty split: train={len(train)}, "
        f"validation={len(validation)}, test={len(test)}"
    )

# Compute a personal average using only contests up to each cutoff.
def add_personal_history(rows):
    counts = []
    averages = []

    for row in rows.itertuples(index=False):
        history = contests[
            (contests["handle"] == row.handle)
            & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
        ]["contest_change"]

        counts.append(len(history))
        averages.append(float(history.mean()) if len(history) else 0.0)

    result = rows.copy()
    result["personal_history_count"] = counts
    result["personal_average"] = averages
    return result

validation = add_personal_history(validation)
test = add_personal_history(test)

def evaluate(rows, k):
    actual = rows["rating_change"].to_numpy()
    personal = rows["personal_average"].to_numpy()
    counts = rows["personal_history_count"].to_numpy()

    if k == 0:
        pred = personal.copy()
    else:
        pred = (counts / (counts + k)) * personal

    return {
        "k": k,
        "MAE": round(float(mean_absolute_error(actual, pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(actual, pred))), 2),
        "R2": round(float(r2_score(actual, pred)), 3),
        "mean_prediction": round(float(pred.mean()), 2),
    }

# Select k using validation data only.
validation_results = pd.DataFrame([
    evaluate(validation, k) for k in [0, 5, 10, 20, 40, 80, 160]
]).sort_values(["MAE", "RMSE"])

best_k = int(validation_results.iloc[0]["k"])

# Compare the selected parameter against fixed alternatives on final test.
test_results = pd.DataFrame([
    evaluate(test, k) for k in [0, 5, 10, 20, 40, 80, 160]
])

zero_pred = np.zeros(len(test))
test_results = pd.concat([
    test_results,
    pd.DataFrame([{
        "k": "zero baseline",
        "MAE": round(float(mean_absolute_error(test["rating_change"], zero_pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(test["rating_change"], zero_pred))), 2),
        "R2": round(float(r2_score(test["rating_change"], zero_pred)), 3),
        "mean_prediction": 0.0,
    }])
], ignore_index=True)

chosen_test = test_results[test_results["k"] == best_k].iloc[0].to_dict()

summary = {
    "train_rows": int(len(train)),
    "validation_rows": int(len(validation)),
    "test_rows": int(len(test)),
    "train_targets_before_validation": bool(
        train["target_timestamp"].max() < validation_start
    ),
    "validation_targets_before_test": bool(
        validation["target_timestamp"].max() < test_start
    ),
    "selected_k_from_validation": best_k,
    "validation_best_mae": float(validation_results.iloc[0]["MAE"]),
    "selected_k_test_metrics": chosen_test,
}

validation_results.to_csv(OUT / "validation_results.csv", index=False)
test_results.to_csv(OUT / "test_results.csv", index=False)

with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("\nCHRONOLOGICAL PERSONAL-AVERAGE SHRINKAGE")
print("=" * 65)
print(json.dumps(summary, indent=2))

print("\nValidation results (used to select k):")
print(validation_results.to_string(index=False))

print("\nFinal test results:")
print(test_results.to_string(index=False))

print("\nSaved results to:", OUT)
