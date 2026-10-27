from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "processed" / "ml_dataset.csv"
MODEL_DIR = ROOT / "models"
MODEL_PATH = MODEL_DIR / "baseline_rating_model.joblib"
TARGET = "target_rating"

def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    if len(df) < 20:
        raise ValueError("Too few users for this exploratory baseline.")

    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    models = {
        "Mean baseline": DummyRegressor(strategy="mean"),
        "Random forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(
                n_estimators=200, random_state=42, min_samples_leaf=3
            ),
        ),
    }

    print("=" * 55)
    print("CODETRACK-AI BASELINE RATING EXPERIMENT")
    print("=" * 55)
    print(f"Users: {len(df)}")
    print(f"Features: {len(X.columns)}")
    print(f"Training users: {len(X_train)}")
    print(f"Test users: {len(X_test)}")
    print("WARNING: predicts current rating, not future progress.")
    print("Results are exploratory because the dataset is small.")

    forest = None
    for name, model in models.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)
        print(f"\n{name}\n  MAE:  {mae:.2f}\n  RMSE: {rmse:.2f}\n  R²:   {r2:.3f}")
        if name == "Random forest":
            forest = model

    if forest is not None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(forest, MODEL_PATH)
        print(f"\nSaved random forest model: {MODEL_PATH}")
    print("\nExperiment complete. Scores are not future-rating accuracy.")

if __name__ == "__main__":
    main()
