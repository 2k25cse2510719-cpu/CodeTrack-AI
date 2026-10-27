import pandas as pd
import numpy as np

from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_FILE = "data/processed/historical_features.csv"

df = pd.read_csv(DATA_FILE)

target = "rating_change"

feature_columns = [
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
X = df[feature_columns].replace([np.inf, -np.inf], np.nan)
y = df[target]
groups = df["handle"]

# Hold out entire users to avoid user overlap between train and test.
splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42,
)

train_idx, test_idx = next(splitter.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

print("TRAINING / TEST SPLIT")
print("-" * 40)
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Training users:", groups.iloc[train_idx].nunique())
print("Testing users:", groups.iloc[test_idx].nunique())
print(
    "User overlap:",
    len(set(groups.iloc[train_idx]) & set(groups.iloc[test_idx]))
)

def evaluate(name, actual, predicted):
    print(f"\n{name}")
    print("MAE:", round(mean_absolute_error(actual, predicted), 2))
    print(
        "RMSE:",
        round(np.sqrt(mean_squared_error(actual, predicted)), 2)
    )
    print("R²:", round(r2_score(actual, predicted), 3))

# Baseline: assume no rating change.
baseline_predictions = np.zeros(len(y_test))
evaluate("PERSISTENCE BASELINE (ZERO CHANGE)", y_test, baseline_predictions)

# Linear Regression
linear_model = make_pipeline(
    SimpleImputer(strategy="median"),
    StandardScaler(),
    LinearRegression(),
)
linear_model.fit(X_train, y_train)
linear_predictions = linear_model.predict(X_test)
evaluate("LINEAR REGRESSION", y_test, linear_predictions)

# Random Forest
forest_model = make_pipeline(
    SimpleImputer(strategy="median"),
    RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
)
forest_model.fit(X_train, y_train)
forest_predictions = forest_model.predict(X_test)
evaluate("RANDOM FOREST", y_test, forest_predictions)

print("\nIMPORTANT")
print("-" * 40)
print("This is a user-held-out evaluation, not a future-time evaluation.")
print("Use the results as an initial benchmark, not proof of future accuracy.")
