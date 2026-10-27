import pandas as pd

df = pd.read_csv("data/processed/v2/historical_features.csv")

cutoffs = sorted(df["cutoff_timestamp"].unique())
validation_start = cutoffs[int(len(cutoffs) * 0.60)]
test_start = cutoffs[int(len(cutoffs) * 0.80)]

train = df[
    (df["cutoff_timestamp"] < validation_start)
    & (df["target_timestamp"] < validation_start)
].copy()

validation = df[
    (df["cutoff_timestamp"] >= validation_start)
    & (df["cutoff_timestamp"] < test_start)
    & (df["target_timestamp"] < test_start)
].copy()

test = df[df["cutoff_timestamp"] >= test_start].copy()

bins = [0, 1200, 1600, 2100, 2400, float("inf")]
labels = ["Below 1200", "1200-1599", "1600-2099", "2100-2399", "2400+"]

for name, data in [
    ("TRAIN", train),
    ("VALIDATION", validation),
    ("TEST", test),
]:
    data["rating_band"] = pd.cut(
        data["baseline_rating"],
        bins=bins,
        labels=labels,
        right=False,
    )

    print(f"\n{name}")
    print("=" * 75)

    summary = data.groupby("rating_band", observed=False).agg(
        samples=("rating_change", "size"),
        users=("handle", "nunique"),
        mean_rating=("baseline_rating", "mean"),
        mean_change=("rating_change", "mean"),
        median_change=("rating_change", "median"),
        std_change=("rating_change", "std"),
        increase_pct=("rating_change", lambda x: (x > 0).mean() * 100),
        decrease_pct=("rating_change", lambda x: (x < 0).mean() * 100),
    )

    print(summary.round(2).to_string())
