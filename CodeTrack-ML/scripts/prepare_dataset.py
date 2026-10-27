from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed" / "user_features.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "ml_dataset.csv"

EXCLUDED_COLUMNS = {
    "handle", "rating", "maxRating", "rank", "maxRank",
    "first_contest_rating", "latest_contest_rating", "rating_change",
}

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input dataset not found: {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    if df.empty:
        raise ValueError("The input dataset is empty.")
    if "rating" not in df.columns:
        raise ValueError("The source dataset must contain a rating column.")

    feature_columns = [
        c for c in df.select_dtypes(include="number").columns
        if c not in EXCLUDED_COLUMNS
    ]
    if not feature_columns:
        raise ValueError("No numeric input features available.")

    prepared = df[feature_columns].copy()
    prepared["target_rating"] = pd.to_numeric(df["rating"], errors="coerce")

    if prepared.isna().any().any():
        missing = prepared.isna().sum()
        raise ValueError("Missing values found:\n" + missing[missing > 0].to_string())

    numeric = prepared.select_dtypes(include="number")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("Infinite or non-finite values found.")
    if (prepared["target_rating"] < 0).any():
        raise ValueError("Negative target ratings found.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(OUTPUT_PATH, index=False)

    print("=" * 55)
    print("CODETRACK-AI DATASET PREPARATION")
    print("=" * 55)
    print("Dataset preparation complete.")
    print(f"Rows: {len(prepared)}")
    print(f"Input features: {len(feature_columns)}")
    print(f"Total columns: {len(prepared.columns)}")
    print(f"Output: {OUTPUT_PATH}")
    print("\nInput features:")
    for c in feature_columns:
        print(f"  - {c}")
    print("\nTarget: target_rating (provisional; not trained yet)")
    print(f"Target range: {prepared['target_rating'].min():.0f} - {prepared['target_rating'].max():.0f}")
    print("\nPASS: no missing values")
    print("PASS: all numeric values finite")
    print("PASS: target ratings non-negative")
    print("Original user_features.csv was not modified.")

if __name__ == "__main__":
    main()
