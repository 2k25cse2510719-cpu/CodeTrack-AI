import pandas as pd
import numpy as np

from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

df = pd.read_csv("data/processed/historical_features.csv")
df = df.sort_values("cutoff_timestamp").copy()

features = [
    "baseline_rating",
    "historical_contest_count",
    "historical_average_rating",
    "historical_max_rating",
    "historical_min_rating",
    "recent_5_contest_average_rating",
    "recent_5_contest_rating_trend",
    "average_contest_rating_change",
    "historical_average_rank",
    "days_since_last_contest",
]

unique_cutoffs = np.sort(df["cutoff_timestamp"].unique())
split_cutoff = unique_cutoffs[int(len(unique_cutoffs) * 0.80)]

train = df[
    (df["cutoff_timestamp"] < split_cutoff)
    & (df["target_timestamp"] < split_cutoff)
].copy()

test = df[df["cutoff_timestamp"] >= split_cutoff].copy()

X_train = train[features].replace([np.inf, -np.inf], np.nan)
X_test = test[features].replace([np.inf, -np.inf], np.nan)
y_train = train["rating_change"]
y_test = test["rating_change"]

model = make_pipeline(
    SimpleImputer(strategy="median"),
    RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

baselines = {
    "Zero-change baseline": np.zeros(len(test)),
    "Training-mean baseline": np.full(len(test), y_train.mean()),
    "Training-median baseline": np.full(len(test), y_train.median()),
    "Random Forest": predictions,
}

print("BASELINE COMPARISON")
print("-" * 45)

for name, pred in baselines.items():
    print(
        f"{name:24s} "
        f"MAE={mean_absolute_error(y_test, pred):7.2f} "
        f"RMSE={np.sqrt(mean_squared_error(y_test, pred)):7.2f}"
    )

test = test.copy()
test["prediction"] = predictions
test["absolute_error"] = (test["prediction"] - y_test).abs()

print("\nERROR BY ACTUAL CHANGE DIRECTION")
print("-" * 45)

test["actual_direction"] = np.where(
    test["rating_change"] > 0,
    "Rating increased",
    np.where(test["rating_change"] < 0, "Rating decreased", "No change"),
)

print(
    test.groupby("actual_direction", observed=False).agg(
        samples=("rating_change", "size"),
        mean_actual=("rating_change", "mean"),
        mean_predicted=("prediction", "mean"),
        mae=("absolute_error", "mean"),
    ).round(2).to_string()
)

print("\nTraining target mean:", round(y_train.mean(), 2))
print("Training target median:", round(y_train.median(), 2))
