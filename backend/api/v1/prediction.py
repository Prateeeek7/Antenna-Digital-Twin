"""Surrogate model prediction API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
import numpy as np
from backend.database.base import get_db
from backend.core.models.schemas import AntennaParameters, SurrogatePrediction
from backend.ml_models.inference_service import InferenceService
from backend.core.exceptions import ModelError, ModelNotFoundError
from backend.dipole.encoding import dipole_physical_to_parameters, decode_dipole_physical_from_parameters

router = APIRouter(prefix="/predictions", tags=["Predictions"])

inference_service = InferenceService()


class DipoleInverseDesignRequest(BaseModel):
    """Request for inverse dipole design from target frequency."""
    target_frequency_ghz: float = Field(..., gt=0.1, le=12.0)
    target_s11_db: float = Field(default=-10.0, ge=-60.0, le=-3.0)
    feed_resistance_ohm: float = Field(default=50.0, gt=1.0, le=200.0)
    n_candidates: int = Field(default=36, ge=8, le=120)
    random_seed: int = Field(default=42)
    fc_ratio: float = Field(default=0.45, gt=0.05, le=0.9)


class DipoleCandidateSummary(BaseModel):
    dipole_length_mm: float
    wire_radius_mm: float
    feed_gap_mm: float
    f0_ghz: float
    fc_ghz: float
    predicted_resonance_ghz: float
    predicted_s11_min_db: float
    objective_score: float


class DipoleInverseDesignResponse(BaseModel):
    recommendation: DipoleCandidateSummary
    top_candidates: List[DipoleCandidateSummary]
    prediction: SurrogatePrediction
    dipole_physical: dict
    feed_resistance_ohm: float


@router.post("/predict", response_model=SurrogatePrediction)
async def create_prediction(
    parameters: AntennaParameters,
    model_name: Optional[str] = None,
    antenna_type: Optional[str] = None,
    metric: str = "s11_min",
    confidence: float = 0.95,
    db: Session = Depends(get_db)
):
    """Get prediction from surrogate model."""
    try:
        selected_model = inference_service.resolve_model_name(antenna_type, model_name)
        prediction = inference_service.predict(
            parameters,
            model_name=selected_model,
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


@router.post("/dipole/design-from-frequency", response_model=DipoleInverseDesignResponse)
async def design_dipole_from_frequency(
    request: DipoleInverseDesignRequest,
    db: Session = Depends(get_db),
):
    """Infer dipole geometry from target frequency using trained surrogate model."""
    try:
        rng = np.random.default_rng(request.random_seed)
        target_f0 = float(request.target_frequency_ghz)
        fc_ghz = max(0.1, float(request.fc_ratio) * target_f0)
        lambda_mm = 300.0 / target_f0

        # Keep search physically near resonant region used by the dataset builder.
        length_lo = max(12.0, 0.35 * lambda_mm)
        length_hi = min(220.0, 0.60 * lambda_mm)
        if length_lo > length_hi:
            l_mid = float(np.clip(0.47 * lambda_mm, 12.0, 220.0))
            length_lo = l_mid
            length_hi = l_mid

        radius_lo = max(0.2, 0.002 * lambda_mm)
        radius_hi = min(2.5, 0.010 * lambda_mm)
        if radius_lo > radius_hi:
            r_mid = float(np.clip(0.004 * lambda_mm, 0.2, 2.5))
            radius_lo = r_mid
            radius_hi = r_mid

        gap_lo, gap_hi = 0.5, 3.0
        f_min = max(0.1, target_f0 - fc_ghz)
        f_max = min(12.0, target_f0 + fc_ghz)

        candidates: List[tuple] = []
        for _ in range(request.n_candidates):
            dipole_length_mm = float(rng.uniform(length_lo, length_hi)) if length_lo != length_hi else float(length_lo)
            wire_radius_mm = float(rng.uniform(radius_lo, radius_hi)) if radius_lo != radius_hi else float(radius_lo)
            feed_gap_mm = float(rng.uniform(gap_lo, gap_hi))

            params = dipole_physical_to_parameters(
                dipole_length_mm=dipole_length_mm,
                wire_radius_mm=wire_radius_mm,
                feed_gap_mm=feed_gap_mm,
                f0_ghz=target_f0,
                fc_ghz=fc_ghz,
            )
            params.frequency_range = (f_min * 1e9, f_max * 1e9)

            pred = inference_service.predict_for_simulation(
                params,
                model_name="dipole",
                confidence=0.95,
            )

            if not pred.s11 or not pred.s11.frequency or not pred.s11.s11_magnitude:
                continue

            s11_values = pred.s11.s11_magnitude
            idx_min = int(np.argmin(s11_values))
            f_res_ghz = float(pred.s11.frequency[idx_min] / 1e9)
            s11_min_db = float(s11_values[idx_min])

            freq_term = abs(f_res_ghz - target_f0) / max(target_f0, 1e-9)
            s11_penalty = max(0.0, request.target_s11_db - s11_min_db)
            score = freq_term + 0.03 * s11_penalty

            summary = DipoleCandidateSummary(
                dipole_length_mm=dipole_length_mm,
                wire_radius_mm=wire_radius_mm,
                feed_gap_mm=feed_gap_mm,
                f0_ghz=target_f0,
                fc_ghz=fc_ghz,
                predicted_resonance_ghz=f_res_ghz,
                predicted_s11_min_db=s11_min_db,
                objective_score=float(score),
            )
            candidates.append((float(score), summary, pred))

        if not candidates:
            raise HTTPException(status_code=500, detail="Unable to evaluate candidate dipole designs")

        candidates.sort(key=lambda x: x[0])
        best_score, best_summary, best_pred = candidates[0]
        _ = best_score  # explicit local binding for readability

        top = [entry[1] for entry in candidates[:5]]
        dipole_physical = decode_dipole_physical_from_parameters(best_pred.antenna_parameters)

        return DipoleInverseDesignResponse(
            recommendation=best_summary,
            top_candidates=top,
            prediction=best_pred,
            dipole_physical=dipole_physical,
            feed_resistance_ohm=request.feed_resistance_ohm,
        )
    except HTTPException:
        raise
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ModelError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dipole inverse design error: {str(e)}")

