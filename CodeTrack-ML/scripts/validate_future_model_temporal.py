import pandas as pd
import numpy as np

from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_FILE = "data/processed/historical_features.csv"

df = pd.read_csv(DATA_FILE)
df["cutoff_timestamp"] = pd.to_numeric(
    df["cutoff_timestamp"], errors="coerce"
)
df["target_timestamp"] = pd.to_numeric(
    df["target_timestamp"], errors="coerce"
)

df = df.dropna(
    subset=["handle", "cutoff_timestamp", "target_timestamp", "rating_change"]
).copy()

# Use only features known at the prediction cutoff.
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

target = "rating_change"

# Use the final 20% of unique cutoff dates as the temporal test period.
unique_cutoffs = np.sort(df["cutoff_timestamp"].unique())
split_position = int(len(unique_cutoffs) * 0.80)
split_cutoff = unique_cutoffs[split_position]

# Purge training samples whose future target occurs on or after
# the start of the test period.
train = df[
    (df["cutoff_timestamp"] < split_cutoff)
    & (df["target_timestamp"] < split_cutoff)
].copy()

test = df[df["cutoff_timestamp"] >= split_cutoff].copy()

if train.empty or test.empty:
    raise ValueError("Training or test data is empty; cannot evaluate.")

X_train = train[features].replace([np.inf, -np.inf], np.nan)
y_train = train[target]
X_test = test[features].replace([np.inf, -np.inf], np.nan)
y_test = test[target]

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

baseline_predictions = np.zeros(len(y_test))

print("CHRONOLOGICAL VALIDATION")
print("-" * 45)
print("Test begins at cutoff timestamp:", int(split_cutoff))
print("Training rows:", len(train))
print("Testing rows:", len(test))
print("Training users:", train["handle"].nunique())
print("Testing users:", test["handle"].nunique())
print("Training targets before test period:",
      bool((train["target_timestamp"] < split_cutoff).all()))

for name, predicted in [
    ("ZERO-CHANGE BASELINE", baseline_predictions),
    ("RANDOM FOREST", predictions),
]:
    print(f"\n{name}")
    print("MAE:", round(mean_absolute_error(y_test, predicted), 2))
    print(
        "RMSE:",
        round(np.sqrt(mean_squared_error(y_test, predicted)), 2),
    )
    print("R²:", round(r2_score(y_test, predicted), 3))

print("\nNote: repeated users may appear in both periods.")
print("This test measures performance on later snapshots,")
print("not necessarily on entirely unseen users.")
