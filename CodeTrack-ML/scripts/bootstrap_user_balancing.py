import numpy as np
import pandas as pd
from pathlib import Path

path = Path("models/future_rating_v2/user_balanced_experiment")
df = pd.read_csv(path / "validation_predictions.csv")

standard_col = "pred_random_forest_standard"
balanced_col = "pred_random_forest_user_balanced"

# Calculate each user's mean absolute error for both models.
per_user = df.groupby("handle").apply(
    lambda g: pd.Series({
        "standard_mae": np.mean(
            np.abs(g["rating_change"] - g[standard_col])
        ),
        "balanced_mae": np.mean(
            np.abs(g["rating_change"] - g[balanced_col])
        ),
        "samples": len(g),
    }),
    include_groups=False,
).reset_index()

# Positive improvement means user balancing reduced MAE.
per_user["improvement"] = (
    per_user["standard_mae"] - per_user["balanced_mae"]
)

# Bootstrap users, not individual rows, so repeated observations
# from the same user stay together.
rng = np.random.default_rng(42)
n_users = len(per_user)
n_bootstrap = 10000

improvements = per_user["improvement"].to_numpy()
bootstrap_means = np.empty(n_bootstrap)

for i in range(n_bootstrap):
    sampled = rng.integers(0, n_users, size=n_users)
    bootstrap_means[i] = improvements[sampled].mean()

mean_improvement = improvements.mean()
lower, upper = np.percentile(bootstrap_means, [2.5, 97.5])

print("\nPAIRED USER-LEVEL BOOTSTRAP")
print("=" * 55)
print(f"Users: {n_users}")
print(f"Validation rows: {len(df)}")
print(f"Mean standard per-user MAE: {per_user['standard_mae'].mean():.2f}")
print(f"Mean balanced per-user MAE: {per_user['balanced_mae'].mean():.2f}")
print(f"Mean improvement: {mean_improvement:.2f} rating points")
print(f"95% bootstrap interval: [{lower:.2f}, {upper:.2f}]")
print(f"Users improved: {(improvements > 0).sum()}")
print(f"Users worsened: {(improvements < 0).sum()}")
print(f"Ties: {(improvements == 0).sum()}")

per_user.to_csv(path / "bootstrap_per_user_errors.csv", index=False)

print("\nInterpretation:")
if lower > 0:
    print("The interval is above zero: evidence of an average improvement across users.")
elif upper < 0:
    print("The interval is below zero: evidence that user balancing worsened average per-user MAE.")
else:
    print("The interval includes zero: the improvement is uncertain at this level.")
print("This interval reflects variation across the observed validation users,")
print("not uncertainty from collecting a new dataset or a fresh time period.")
