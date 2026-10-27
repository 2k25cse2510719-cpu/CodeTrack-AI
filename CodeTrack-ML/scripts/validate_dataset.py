from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "processed" / "user_features.csv"

def main():
    print("=" * 55)
    print("CODETRACK-AI DATASET VALIDATION")
    print("=" * 55)

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    missing = df.isna().sum()
    missing = missing[missing > 0]
    print("\nMissing values:")
    print(missing.to_string() if not missing.empty else "PASS: No missing values.")

    id_candidates = ["user_id", "handle", "username"]
    id_column = next((c for c in id_candidates if c in df.columns), None)
    if id_column:
        print(f"\nIdentifier column: {id_column}")
        print(f"Missing identifiers: {df[id_column].isna().sum()}")
        print(f"Duplicate identifiers: {df[id_column].duplicated().sum()}")
    else:
        print("\nWARNING: No recognized user identifier column found.")

    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        print("WARNING: No numeric columns found.")
    else:
        finite = np.isfinite(numeric.to_numpy()).all()
        print(f"\nFinite numeric values: {'PASS' if finite else 'FAIL'}")
        constants = [c for c in numeric if numeric[c].nunique(dropna=False) <= 1]
        print("Constant numeric columns:", ", ".join(constants) if constants else "None")

    print("\nColumn types:")
    print(df.dtypes.to_string())
    print("\nNumeric summary:")
    print(numeric.describe().round(2).to_string())

    checks = {
        "Dataset is not empty": not df.empty,
        "No missing values": not df.isna().any().any(),
        "No duplicate rows": not df.duplicated().any(),
        "No infinite numeric values": numeric.empty or np.isfinite(numeric.to_numpy()).all(),
    }
    print("\nValidation summary:")
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

if __name__ == "__main__":
    main()
