import pandas as pd

files = {
    "features": "data/processed/user_features.csv",
    "contests": "data/codeforces/contest_history.csv",
    "submissions": "data/codeforces/submissions.csv",
}

for name, path in files.items():
    df = pd.read_csv(path)

    print("\n" + "=" * 55)
    print(name.upper())
    print("=" * 55)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head(2).to_string(index=False))
