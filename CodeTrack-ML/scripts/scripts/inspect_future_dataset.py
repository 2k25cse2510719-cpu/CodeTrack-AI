
import pandas as pd
from pathlib import Path

DATA_FILE = Path("data/processed/future_rating_dataset.csv")

df = pd.read_csv(DATA_FILE)

print("FUTURE-RATING DATASET INSPECTION")
print("-" * 40)

print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Unique users:", df["handle"].nunique())

print("\nMissing values:")
print(df.isnull().sum().to_string())

print("\nDuplicate rows:", df.duplicated().sum())

print("\nBaseline rating statistics:")
print(df["baseline_rating"].describe().round(2).to_string())

print("\nFuture rating statistics:")
print(df["future_rating"].describe().round(2).to_string())

print("\nRating change statistics:")
print(df["rating_change"].describe().round(2).to_string())

print("\nExamples:")
print(df.head(10).to_string(index=False))
