import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PREDICTIONS = Path("models/future_rating_v2/test_predictions.csv")
CONTESTS = Path("data/codeforces/contest_history.csv")

df = pd.read_csv(PREDICTIONS)
contests = pd.read_csv(CONTESTS)

contests["ratingUpdateTimeSeconds"] = pd.to_numeric(
    contests["ratingUpdateTimeSeconds"], errors="coerce"
)
contests["oldRating"] = pd.to_numeric(
    contests["oldRating"], errors="coerce"
)
contests["newRating"] = pd.to_numeric(
    contests["newRating"], errors="coerce"
)

contests = contests.dropna(
    subset=["handle", "ratingUpdateTimeSeconds", "oldRating", "newRating"]
)

# Exclude initial ratings and calculate actual contest-to-contest changes.
contests = contests[contests["oldRating"] > 0].copy()
contests["contest_change"] = (
    contests["newRating"] - contests["oldRating"]
)

contests = contests.sort_values(
    ["handle", "ratingUpdateTimeSeconds"]
)

predictions = []

for row in df.itertuples(index=False):
    history = contests[
        (contests["handle"] == row.handle)
        & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
    ]

    # If there is no prior valid contest change, predict zero.
    prediction = (
        float(history["contest_change"].mean())
        if not history.empty else 0.0
    )
    predictions.append(prediction)

df["pred_personal_average"] = predictions

def report(name, pred):
    print(
        f"{name:25s} "
        f"MAE={mean_absolute_error(df['rating_change'], pred):7.2f}  "
        f"RMSE={np.sqrt(mean_squared_error(df['rating_change'], pred)):7.2f}  "
        f"R2={r2_score(df['rating_change'], pred):7.3f}"
    )

print("PERSONALIZED BASELINE COMPARISON")
print("=" * 65)
print("Samples:", len(df))
report("Zero-change baseline", np.zeros(len(df)))
report("Random Forest", df["pred_random_forest"])
report("Personal historical average", df["pred_personal_average"])

print("\nAverage personalized prediction:",
      round(df["pred_personal_average"].mean(), 2))
print("Actual average change:",
      round(df["rating_change"].mean(), 2))

df.to_csv(
    "models/future_rating_v2/personal_baseline_predictions.csv",
    index=False
)
print("\nSaved personalized baseline predictions.")
