"""Run baseline on a CSV export of problem history."""
import argparse, json
import pandas as pd
from src.features import build_features
from src.readiness import score_readiness

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problems", required=True, help="CSV containing ProblemResponse-like fields")
    parser.add_argument("--revisions", help="Optional revision-history CSV")
    args = parser.parse_args()
    problem_df = pd.read_csv(args.problems)
    problems = problem_df.where(pd.notna(problem_df), None).to_dict("records")
    revisions = None
    if args.revisions:
        revision_df = pd.read_csv(args.revisions)
        revisions = revision_df.where(pd.notna(revision_df), None).to_dict("records")
    features = build_features(problems, revisions)
    print(json.dumps({"features": features, "readiness": score_readiness(features)}, indent=2))

if __name__ == "__main__":
    main()
