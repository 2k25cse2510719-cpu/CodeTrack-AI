import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error

path = Path("models/future_rating_v2/test_predictions.csv")
df = pd.read_csv(path)

pred_col = "pred_random_forest"
df["error"] = df[pred_col] - df["rating_change"]
df["absolute_error"] = df["error"].abs()

df["actual_direction"] = np.select(
    [df["rating_change"] > 0, df["rating_change"] < 0],
    ["Increased", "Decreased"],
    default="Unchanged"
)

df["predicted_direction"] = np.select(
    [df[pred_col] > 0, df[pred_col] < 0],
    ["Increased", "Decreased"],
    default="Unchanged"
)

print("V2 ERROR ANALYSIS")
print("=" * 55)
print("Test samples:", len(df))
print("Overall MAE:", round(df["absolute_error"].mean(), 2))
print(
    "Direction accuracy:",
    round((df["actual_direction"] == df["predicted_direction"]).mean() * 100, 2),
    "%"
)

print("\nERROR BY ACTUAL DIRECTION")
print(
    df.groupby("actual_direction").agg(
        samples=("rating_change", "size"),
        actual_mean=("rating_change", "mean"),
        predicted_mean=(pred_col, "mean"),
        MAE=("absolute_error", "mean")
    ).round(2).to_string()
)

df["rating_band"] = pd.cut(
    df["baseline_rating"],
    bins=[-np.inf, 1199, 1599, 2099, 2399, np.inf],
    labels=["Below 1200", "1200-1599", "1600-2099", "2100-2399", "2400+"]
)

print("\nERROR BY BASELINE RATING")
print(
    df.groupby("rating_band", observed=False).agg(
        samples=("rating_change", "size"),
        actual_mean=("rating_change", "mean"),
        predicted_mean=(pred_col, "mean"),
        MAE=("absolute_error", "mean")
    ).round(2).to_string()
)

print("\nLARGEST PREDICTION ERRORS")
cols = [
    "handle", "baseline_rating", "rating_change",
    pred_col, "error", "absolute_error"
]
print(
    df.nlargest(10, "absolute_error")[cols]
    .round(2).to_string(index=False)
)

print("\nLARGEST DIRECTION MISMATCHES")
wrong = df[df["actual_direction"] != df["predicted_direction"]]
print("Mismatches:", len(wrong))
print(
    wrong.nlargest(10, "absolute_error")[cols]
    .round(2).to_string(index=False)
)
