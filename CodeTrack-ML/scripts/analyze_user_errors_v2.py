import pandas as pd
import numpy as np

path = "models/future_rating_v2/test_predictions.csv"
df = pd.read_csv(path)

pred_col = "pred_random_forest"
df["abs_error"] = (df[pred_col] - df["rating_change"]).abs()

user_stats = df.groupby("handle").agg(
    samples=("rating_change", "size"),
    actual_mean=("rating_change", "mean"),
    predicted_mean=(pred_col, "mean"),
    mae=("abs_error", "mean"),
    total_absolute_error=("abs_error", "sum")
).sort_values("total_absolute_error", ascending=False)

print("USER-LEVEL ERROR ANALYSIS")
print("=" * 65)
print("Unique test users:", df["handle"].nunique())
print("Users with multiple test samples:", int((user_stats["samples"] > 1).sum()))
print("\nTOP 15 USERS BY TOTAL ABSOLUTE ERROR")
print(user_stats.head(15).round(2).to_string())

print("\nERROR CONCENTRATION")
total_error = df["abs_error"].sum()
for n in [1, 3, 5, 10]:
    contribution = user_stats.head(n)["total_absolute_error"].sum()
    print(f"Top {n} users account for {contribution / total_error * 100:.1f}% of total absolute error")

print("\nPER-USER BASELINE COMPARISON")
# Use the user's historical average rating change as a simple
# personalized baseline, excluding first-rating records (oldRating <= 0).
# This requires historical contest-level data and will be computed next.
print("Next: compare against each user's past-only average rating change.")
