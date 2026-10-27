import numpy as np
import pandas as pd
from pathlib import Path

PREDICTIONS = Path(
    "models/future_rating_v2/personal_baseline_predictions.csv"
)
CONTESTS = Path("data/codeforces/contest_history.csv")
OUT = Path("models/future_rating_v2")

df = pd.read_csv(PREDICTIONS)
contests = pd.read_csv(CONTESTS)

for col in ["ratingUpdateTimeSeconds", "oldRating", "newRating"]:
    contests[col] = pd.to_numeric(contests[col], errors="coerce")

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "oldRating", "newRating"]
).copy()

# Count only ordinary, rated contest-to-contest changes.
contests = contests[contests["oldRating"] > 0].copy()
contests["contest_change"] = contests["newRating"] - contests["oldRating"]
contests = contests.sort_values(["handle", "ratingUpdateTimeSeconds"])

history_counts = []
history_means = []

for row in df.itertuples(index=False):
    history = contests[
        (contests["handle"] == row.handle)
        & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
    ]

    history_counts.append(len(history))
    history_means.append(
        float(history["contest_change"].mean()) if len(history) else 0.0
    )

df["historical_contest_count_at_cutoff"] = history_counts
df["recomputed_personal_average"] = history_means

# Verify the recomputation matches the saved predictions.
diff = (
    df["recomputed_personal_average"] - df["pred_personal_average"]
).abs()

print("\nPERSONAL BASELINE HISTORY ANALYSIS")
print("=" * 65)
print("Test samples:", len(df))
print("Prediction mismatch count (tolerance 1e-6):", int((diff > 1e-6).sum()))

# Group by how much history was available at the prediction cutoff.
bins = [-1, 0, 5, 10, 20, 50, np.inf]
labels = [
    "0 contests", "1-5", "6-10", "11-20", "21-50", "51+"
]
df["history_group"] = pd.cut(
    df["historical_contest_count_at_cutoff"],
    bins=bins,
    labels=labels
)

rows = []

for group, part in df.groupby("history_group", observed=False):
    if len(part) == 0:
        continue

    actual = part["rating_change"].to_numpy()
    personal = part["pred_personal_average"].to_numpy()
    zero = np.zeros(len(part))

    rows.append({
        "history_group": str(group),
        "samples": len(part),
        "users": part["handle"].nunique(),
        "mean_history_count": round(
            part["historical_contest_count_at_cutoff"].mean(), 1
        ),
        "actual_mean_change": round(float(actual.mean()), 2),
        "personal_MAE": round(float(np.mean(np.abs(actual - personal))), 2),
        "zero_MAE": round(float(np.mean(np.abs(actual - zero))), 2),
    })

summary = pd.DataFrame(rows)

print("\nERROR BY HISTORICAL CONTEST COUNT")
print("=" * 85)
print(summary.to_string(index=False))

summary.to_csv(OUT / "personal_baseline_history_analysis.csv", index=False)

df.to_csv(OUT / "personal_baseline_history_details.csv", index=False)

print("\nSaved summary to:", OUT / "personal_baseline_history_analysis.csv")
print("Saved details to:", OUT / "personal_baseline_history_details.csv")
