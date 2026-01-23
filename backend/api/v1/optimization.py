"""Optimization engine API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.database.base import get_db
from backend.core.models.schemas import AntennaParameters
from backend.optimization.geometry_tuner import GeometryOptimizer
from backend.optimization.whatif_analyzer import WhatIfAnalyzer
from backend.core.exceptions import OptimizationError

router = APIRouter(prefix="/optimization", tags=["Optimization"])

geometry_optimizer = GeometryOptimizer()
whatif_analyzer = WhatIfAnalyzer()


class WhatIfRequest(BaseModel):
    """What-if analysis request."""
    parameters: AntennaParameters
    variation: Dict[str, float] = {}


@router.post("/optimize", response_model=AntennaParameters)
async def optimize_geometry(
    initial_parameters: AntennaParameters,
    objective: str = "minimize_s11",
    target_s11: float = -10.0,
    db: Session = Depends(get_db)
):
    """Optimize antenna geometry for given objective."""
    try:
        if objective == "minimize_s11":
            optimized = geometry_optimizer.optimize_s11(initial_parameters, target_s11=target_s11)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown objective: {objective}")
        
        return optimized
    except OptimizationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@router.post("/what-if")
async def what_if_analysis(
    request: WhatIfRequest,
    db: Session = Depends(get_db)
):
    """Perform what-if scenario analysis."""
    try:
        results = whatif_analyzer.analyze_variation(request.parameters, request.variation)
        
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

