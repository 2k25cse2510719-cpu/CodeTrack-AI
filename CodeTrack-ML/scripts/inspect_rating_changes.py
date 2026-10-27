import pandas as pd

df = pd.read_csv("data/processed/future_rating_dataset.csv")

print("RATING CHANGE DISTRIBUTION")
print("-" * 40)
print(df["rating_change"].describe(
    percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
).round(2).to_string())

print("\nLARGEST ABSOLUTE RATING CHANGES")
print("-" * 40)
cols = [
    "handle",
    "baseline_rating",
    "future_rating",
    "rating_change",
    "days_to_target",
]
print(
    df.assign(
        abs_change=df["rating_change"].abs()
    ).nlargest(15, "abs_change")[cols].to_string(index=False)
)

print("\nSAMPLES PER USER")
print("-" * 40)
counts = df.groupby("handle").size()
print(counts.describe().round(2).to_string())
print("Users with fewer than 5 samples:", (counts < 5).sum())
