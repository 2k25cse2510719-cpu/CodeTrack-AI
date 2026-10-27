import pandas as pd
import numpy as np

from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

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
test["predicted_change"] = model.predict(X_test)
test["actual_change"] = y_test
test["absolute_error"] = (
    test["predicted_change"] - test["actual_change"]
).abs()

print("TEMPORAL ERROR ANALYSIS")
print("-" * 40)
print("Test rows:", len(test))
print("Actual mean change:", round(test["actual_change"].mean(), 2))
print("Predicted mean change:", round(test["predicted_change"].mean(), 2))
print("Actual median change:", round(test["actual_change"].median(), 2))
print("Predicted median change:", round(test["predicted_change"].median(), 2))
print("MAE:", round(mean_absolute_error(
    test["actual_change"], test["predicted_change"]
), 2))

test["rating_band"] = pd.cut(
    test["baseline_rating"],
    bins=[-np.inf, 1200, 1600, 2100, 2400, np.inf],
    labels=["Below 1200", "1200-1599", "1600-2099",
            "2100-2399", "2400+"],
    right=False,
)

print("\nERROR BY BASELINE RATING")
print(
    test.groupby("rating_band", observed=False)
    .agg(
        samples=("actual_change", "size"),
        mean_actual=("actual_change", "mean"),
        mean_predicted=("predicted_change", "mean"),
        mae=("absolute_error", "mean"),
    )
    .round(2)
    .to_string()
)

print("\nFIRST 10 PREDICTIONS")
print(
    test[
        ["handle", "baseline_rating", "actual_change",
         "predicted_change", "absolute_error"]
    ].head(10).round(2).to_string(index=False)
)
