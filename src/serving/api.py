"""
FastAPI serving layer — 2 endpoints for production model serving.
Run: uv run uvicorn src.serving.api:app --reload
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="ml-launchpad",
    description="AutoML model serving API",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ScoreRequest(BaseModel):
    features: dict


class ScoreResponse(BaseModel):
    prediction: str | float
    probability: float | None = None


_predictor = None


def _load_model():
    global _predictor
    model_path = Path("outputs/models/autogluon_model")
    if not model_path.exists():
        return None
    try:
        from autogluon.tabular import TabularPredictor
        _predictor = TabularPredictor.load(str(model_path))
        return _predictor
    except Exception:
        return None


@app.get("/health", response_model=HealthResponse)
def health():
    global _predictor
    if _predictor is None:
        _load_model()
    return HealthResponse(
        status="ok",
        model_loaded=_predictor is not None,
    )


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    global _predictor
    if _predictor is None:
        _load_model()
    if _predictor is None:
        raise HTTPException(
            status_code=503,
            detail="No model loaded. Run /model and /promote first.",
        )

    import pandas as pd
    df = pd.DataFrame([req.features])

    try:
        pred = _predictor.predict(df)
        prediction = pred.iloc[0]

        proba = None
        try:
            prob_df = _predictor.predict_proba(df)
            proba = float(prob_df.max(axis=1).iloc[0])
        except Exception:
            pass

        return ScoreResponse(
            prediction=prediction,
            probability=proba,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
