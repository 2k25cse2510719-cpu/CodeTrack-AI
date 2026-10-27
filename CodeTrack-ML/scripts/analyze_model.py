from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "processed" / "ml_dataset.csv"
MODEL_PATH = ROOT / "models" / "baseline_rating_model.joblib"

def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    df = pd.read_csv(DATASET_PATH)
    model = joblib.load(MODEL_PATH)
    features = df.drop(columns=["target_rating"]).columns.tolist()
    forest = model.named_steps["randomforestregressor"]

    importance = pd.DataFrame({
        "feature": features,
        "importance": forest.feature_importances_,
    }).sort_values("importance", ascending=False)

    print("=" * 55)
    print("CODETRACK-AI FEATURE IMPORTANCE")
    print("=" * 55)
    print(importance.to_string(index=False, formatters={"importance": "{:.4f}".format}))
    print("\nImportance shows model reliance, not causation.")
    print("This does not establish future-rating prediction accuracy.")

if __name__ == "__main__":
    main()
