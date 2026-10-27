from pathlib import Path
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import KFold, cross_validate
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "processed" / "ml_dataset.csv"
TARGET = "target_rating"

def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "Mean baseline": DummyRegressor(strategy="mean"),
        "Random forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(
                n_estimators=200, random_state=42, min_samples_leaf=3
            ),
        ),
    }
    scoring = {
        "mae": "neg_mean_absolute_error",
        "rmse": "neg_root_mean_squared_error",
        "r2": "r2",
    }

    print("=" * 60)
    print("CODETRACK-AI 5-FOLD CROSS-VALIDATION")
    print("=" * 60)
    print(f"Users: {len(df)}")
    print("Predicts current rating, not future progress.")
    for name, model in models.items():
        results = cross_validate(
            model, X, y, cv=cv, scoring=scoring, error_score="raise"
        )
        mae = -results["test_mae"]
        rmse = -results["test_rmse"]
        r2 = results["test_r2"]
        print(f"\n{name}")
        print(f"  MAE:  {mae.mean():.2f} +/- {mae.std():.2f}")
        print(f"  RMSE: {rmse.mean():.2f} +/- {rmse.std():.2f}")
        print(f"  R²:   {r2.mean():.3f} +/- {r2.std():.3f}")
    print("\nEvaluation complete.")

if __name__ == "__main__":
    main()
