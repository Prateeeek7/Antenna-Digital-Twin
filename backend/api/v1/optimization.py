"""Optimization engine API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
from backend.database.base import get_db
from backend.core.models.schemas import AntennaParameters, TargetSpectrum
from backend.optimization.geometry_tuner import GeometryOptimizer
from backend.optimization.whatif_analyzer import WhatIfAnalyzer
from backend.core.exceptions import OptimizationError
from backend.ml_models.inference_service import InferenceService

router = APIRouter(prefix="/optimization", tags=["Optimization"])

geometry_optimizer = GeometryOptimizer()
whatif_analyzer = WhatIfAnalyzer()
_inference = InferenceService()


def _resolved_model(antenna_type: Optional[str], model_name: Optional[str]) -> str:
    return _inference.resolve_model_name(antenna_type, model_name)


class WhatIfRequest(BaseModel):
    """What-if analysis request."""
    parameters: AntennaParameters
    variation: Dict[str, float] = {}


class OptimizeSpectrumRequest(BaseModel):
    """Request for UCE-style full S11 spectrum matching."""
    initial_parameters: AntennaParameters
    target_spectrum: TargetSpectrum
    optimizer: Literal["lbfgs", "cem"] = Field(default="lbfgs", description="Optimizer: lbfgs or cem")
    quantile: float = Field(default=0.9, ge=0.01, le=1.0, description="Spectrum loss quantile")
    n_samples: int = Field(default=30, ge=5, le=200, description="CEM samples per iteration")
    elite_frac: float = Field(default=0.15, gt=0.0, lt=1.0, description="CEM elite fraction")
    n_iterations: int = Field(default=15, ge=1, le=100, description="CEM iterations")


@router.post("/optimize", response_model=AntennaParameters)
async def optimize_geometry(
    initial_parameters: AntennaParameters,
    objective: str = "minimize_s11",
    target_s11: float = -10.0,
    antenna_type: Optional[str] = None,
    model_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Optimize antenna geometry for given objective."""
    try:
        resolved = _resolved_model(antenna_type, model_name)
        if objective == "minimize_s11":
            optimized = geometry_optimizer.optimize_s11(
                initial_parameters, target_s11=target_s11, model_name=resolved
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown objective: {objective}")
        
        return optimized
    except HTTPException:
        raise
    except OptimizationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@router.post("/optimize-spectrum")
async def optimize_spectrum(
    request: OptimizeSpectrumRequest,
    antenna_type: Optional[str] = None,
    model_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Optimize geometry so predicted S11 curve matches target spectrum (UCE-style).
    Supports L-BFGS-B or Cross-Entropy Method (CEM).
    """
    try:
        resolved = _resolved_model(antenna_type, model_name)
        optimized, loss_history = geometry_optimizer.optimize_s11_spectrum(
            initial_parameters=request.initial_parameters,
            target_frequency_hz=request.target_spectrum.frequency_hz,
            target_s11_magnitude_db=request.target_spectrum.s11_magnitude_db,
            optimizer=request.optimizer,
            quantile=request.quantile,
            n_samples=request.n_samples,
            elite_frac=request.elite_frac,
            n_iterations=request.n_iterations,
            model_name=resolved,
        )
        return {
            "optimized_parameters": optimized,
            "loss_history": loss_history,
        }
    except OptimizationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@router.post("/what-if")
async def what_if_analysis(
    request: WhatIfRequest,
    antenna_type: Optional[str] = None,
    model_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Perform what-if scenario analysis."""
    try:
        resolved = _resolved_model(antenna_type, model_name)
        results = whatif_analyzer.analyze_variation(
            request.parameters, request.variation, model_name=resolved
        )
        
        # Extract the first variation result (or base if no variations)
        # Frontend expects a single prediction result
        if request.variation:
            # Get the first variation result
            first_key = list(results.keys())[1] if len(results) > 1 else list(results.keys())[0]
            prediction = results[first_key]
        else:
            prediction = results.get("base", list(results.values())[0] if results else None)
        
        if prediction:
            # Return simplified result for frontend
            s11_min = min(prediction.s11.s11_magnitude) if prediction.s11 and prediction.s11.s11_magnitude else None
            return {
                "s11_min": s11_min,
                "gain": prediction.gain,
                "efficiency": prediction.efficiency,
                "full_prediction": prediction.model_dump()  # Include full data if needed
            }
        else:
            raise HTTPException(status_code=500, detail="No prediction result available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis error: {str(e)}")

