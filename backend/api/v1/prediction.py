"""Surrogate model prediction API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.base import get_db
from backend.core.models.schemas import AntennaParameters, SurrogatePrediction
from backend.ml_models.inference_service import InferenceService
from backend.core.exceptions import ModelError, ModelNotFoundError

router = APIRouter(prefix="/predictions", tags=["Predictions"])

inference_service = InferenceService()


@router.post("/predict", response_model=SurrogatePrediction)
async def create_prediction(
    parameters: AntennaParameters,
    model_name: str = "default",
    metric: str = "s11_min",
    confidence: float = 0.95,
    db: Session = Depends(get_db)
):
    """Get prediction from surrogate model."""
    try:
        prediction = inference_service.predict(
            parameters,
            model_name=model_name,
            metric=metric,
            confidence=confidence
        )
        return prediction
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ModelError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

