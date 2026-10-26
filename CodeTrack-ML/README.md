# CodeTrack-AI ML Readiness Predictor

A small Python module for estimating two separate readiness indicators from existing CodeTrack-AI problem history: technical interview preparation and competitive programming preparation.

## Important limitation
Current scores are transparent heuristic baseline scores, not validated predictions of real-world interview or contest outcomes. Current problem history does not contain contest ratings/results, solve times, attempt counts, or verified readiness labels. `train.py` only trains supervised models when you provide defensible labeled examples. Do not train a model to copy the heuristic and call it independently predictive.

## Expected fields
Problem records use Java `ProblemResponse` names: `id,title,platform,difficulty,topic,selectedPattern,verifiedPattern,status,solvedDate,createdAt,updatedAt`. Optional revision records can include `status,scheduledDate,completedAt,problemId`.

## Setup (PowerShell from repository root)
```powershell
python -m pip install -r .\CodeTrack-ML\requirements.txt
```
Use your existing `.venv` first: `.\CodeTrack-ML\.venv\Scripts\Activate.ps1`.

## Run baseline against CSV
```powershell
python .\CodeTrack-ML\src\cli.py --problems .\CodeTrack-ML\data\sample_problems.csv
```

## Run local API
```powershell
python -m uvicorn src.api:app --app-dir .\CodeTrack-ML --reload --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/docs`. `POST /predict/readiness` accepts JSON with `problems` and optional `revisions` arrays. This starter API is for local development. Before production, add service-to-service authentication, request limits, logging and private deployment; never expose private user history publicly.

## Train only with real labels
Provide a CSV with all feature columns and `interview_ready_label`, `competition_ready_label` targets containing defensible 0/1 outcomes. Do not generate labels from the baseline score. Then run:
```powershell
python .\CodeTrack-ML\src\train.py --data .\CodeTrack-ML\data\labeled_training.csv
```
The script requires enough examples per class and reports holdout evaluation.

## Integration plan
1. Run the baseline locally.
2. Spring Boot retrieves the authenticated user's own problem/revision history.
3. Spring Boot calls this Python API privately and returns results to React.
4. Add trained-model inference only after a labeled dataset supports it.

No database schema changes are required for this initial baseline.
