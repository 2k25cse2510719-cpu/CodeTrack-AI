# CodeTrack-AI ML scripts bundle

This bundle contains the helper scripts created during the dataset validation and baseline-model workflow.

## Where to put it

Copy the contents of the `scripts` folder into:

`CodeTrack-ML/scripts/`

These scripts expect the existing project layout:
- `CodeTrack-ML/data/codeforces/`
- `CodeTrack-ML/data/processed/user_features.csv`
- `CodeTrack-ML/models/`

## Script order

1. `validate_dataset.py` — checks the engineered dataset.
2. `inspect_features.py` — prints candidate features and caveats.
3. `prepare_dataset.py` — creates `data/processed/ml_dataset.csv`.
4. `train_baseline.py` — trains a baseline current-rating regression experiment.
5. `analyze_model.py` — prints Random Forest feature importance.
6. `evaluate_model.py` — runs 5-fold cross-validation.

Run each script from the CodeTrack-AI repository root, for example:

```powershell
& ".\\CodeTrack-ML\\.venv\\Scripts\\python.exe" ".\\CodeTrack-ML\\scripts\\validate_dataset.py"
```

## Important limitations

- The dataset currently contains only 100 users.
- Activity features use up to 1,000 recent submissions per user.
- The current target is current Codeforces rating, not future rating change.
- Scores are exploratory and are not proof of future performance.
- Keep the existing collector and feature-building scripts; this bundle does not replace them.
