import pandas as pd

df = pd.read_csv("data/processed/v2/historical_features.csv")

cutoffs = sorted(df["cutoff_timestamp"].unique())
validation_start = cutoffs[int(len(cutoffs) * 0.60)]
test_start = cutoffs[int(len(cutoffs) * 0.80)]

splits = {
    "TRAIN": df[
        (df["cutoff_timestamp"] < validation_start)
        & (df["target_timestamp"] < validation_start)
    ],
    "VALIDATION": df[
        (df["cutoff_timestamp"] >= validation_start)
        & (df["cutoff_timestamp"] < test_start)
        & (df["target_timestamp"] < test_start)
    ],
    "TEST": df[df["cutoff_timestamp"] >= test_start],
}

for name, data in splits.items():
    print(f"\n{name}")
    print("=" * 65)

    user_stats = data.groupby("handle").agg(
        samples=("rating_change", "size"),
        total_change=("rating_change", "sum"),
        mean_change=("rating_change", "mean"),
        total_absolute_change=("rating_change", lambda x: x.abs().sum()),
    ).sort_values("samples", ascending=False)

    total_abs = user_stats["total_absolute_change"].sum()

    print(f"Total rows: {len(data)}")
    print(f"Unique users: {data['handle'].nunique()}")
    print(f"Top 5 users' share of samples: "
          f"{user_stats.head(5)['samples'].sum() / len(data) * 100:.2f}%")
    print(f"Top 5 users' share of absolute changes: "
          f"{user_stats.head(5)['total_absolute_change'].sum() / total_abs * 100:.2f}%")

    print("\nTop 10 users by sample count:")
    print(user_stats.head(10).round(2).to_string())
