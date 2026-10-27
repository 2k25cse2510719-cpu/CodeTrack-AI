from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "processed" / "user_features.csv"
TARGET_COLUMNS = {"rating", "maxRating", "rank", "maxRank"}

def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET}")
    df = pd.read_csv(DATASET)

    print("=" * 60)
    print("CODETRACK-AI FEATURE AUDIT")
    print("=" * 60)
    print(f"\nDataset shape: {df.shape}")
    print(f"Unique users: {df['handle'].nunique()}")

    print("\nPotential target/profile columns:")
    for column in sorted(TARGET_COLUMNS):
        if column in df.columns:
            print(f"  {column}: {df[column].nunique()} unique values")

    excluded = {"handle"} | TARGET_COLUMNS
    features = [
        c for c in df.select_dtypes(include="number").columns
        if c not in excluded
    ]
    print("\nCandidate numeric input features:")
    for column in features:
        print(f"  {column}")
    print(f"\nCandidate feature count: {len(features)}")
    print("\nLeakage/interpretation warnings:")
    print("- first_contest_rating, latest_contest_rating, and rating_change")
    print("  encode rating history and require careful treatment.")
    print("- Activity features cover only collected submissions (up to 1,000/user).")
    if len(df) < 500:
        print("- Small pilot dataset: performance estimates will be uncertain.")
    print("\nAudit complete. No files were modified.")

if __name__ == "__main__":
    main()
