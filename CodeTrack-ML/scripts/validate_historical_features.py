import pandas as pd

path = "data/processed/historical_features.csv"
df = pd.read_csv(path)

# Rename the trend feature for clarity
df = df.rename(columns={
    "recent_5_contest_rating_change": "recent_5_contest_rating_trend"
})

# Rebuild the average rating-change feature from the historical
# contest records, excluding initial ratings with oldRating == 0.
contests = pd.read_csv("data/codeforces/contest_history.csv")

contests["ratingUpdateTimeSeconds"] = pd.to_numeric(
    contests["ratingUpdateTimeSeconds"], errors="coerce"
)
contests["oldRating"] = pd.to_numeric(
    contests["oldRating"], errors="coerce"
)
contests["newRating"] = pd.to_numeric(
    contests["newRating"], errors="coerce"
)

contests = contests.dropna(subset=[
    "handle", "ratingUpdateTimeSeconds", "oldRating", "newRating"
])

contests = contests[contests["oldRating"] > 0].copy()

values = []

for row in df.itertuples(index=False):
    history = contests[
        (contests["handle"] == row.handle)
        & (contests["ratingUpdateTimeSeconds"] <= row.cutoff_timestamp)
    ]

    if history.empty:
        values.append(0.0)
    else:
        changes = history["newRating"] - history["oldRating"]
        values.append(float(changes.mean()))

df["average_contest_rating_change"] = values

df.to_csv(path, index=False)

print("Historical features corrected and saved.")
print("Rows:", len(df))
print("Users:", df["handle"].nunique())
print("Missing values:", int(df.isnull().sum().sum()))
print("\nUpdated columns:")
print(df.columns.tolist())
print("\nRating-change feature:")
print(df["average_contest_rating_change"].describe().round(2).to_string())
print("\nSaved to:", path)
