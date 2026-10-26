
"""Local development API. Production integration must be private/authenticated."""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.features import build_features
from src.readiness import score_readiness

app = FastAPI(title="CodeTrack-AI Readiness API", version="0.1.0")


class ReadinessRequest(BaseModel):
    problems: list[dict[str, Any]] = Field(default_factory=list)
    revisions: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict/readiness")
def readiness(payload: ReadinessRequest) -> dict[str, Any]:
    features = build_features(payload.problems, payload.revisions)
    return {
        "features": features,
        "readiness": score_readiness(features),
    }
