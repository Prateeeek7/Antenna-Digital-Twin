"""EM simulation API endpoints."""

import asyncio
import logging
import math
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pathlib import Path
from backend.database.base import get_db

logger = logging.getLogger(__name__)
from backend.core.models.schemas import AntennaParameters, EMSimulationResult, DesignRequest
from backend.core.exceptions import EMSolverError, SolverNotAvailableError, ModelError, ModelNotFoundError
from backend.em_solver.factory import EMSolverFactory
from backend.em_solver.database_service import EMSimulationDatabaseService
from backend.core.config import settings
from backend.dipole.encoding import decode_dipole_physical_from_parameters

router = APIRouter(prefix="/em", tags=["EM Simulation"])


def _sanitize_for_json(obj: Any) -> Any:
    """Replace nan/inf with JSON-safe values so json.dumps does not raise."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0  # default for scalars; lists may get None below
        return obj
    return obj

db_service = EMSimulationDatabaseService()


@router.post("/simulate", response_model=EMSimulationResult)
async def create_simulation(
    parameters: AntennaParameters,
    solver_name: str = "surrogate",
    antenna_type: Optional[str] = None,
    model_name: Optional[str] = None,
    fast: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Create and run an EM simulation.

    Default solver is \"surrogate\" (trained ML model, fast). Use \"openems\" for
    full physics simulation (OpenEMS), or \"openems_octave\" for Octave/OpenEMS.
    For OpenEMS, set fast=True for quicker runs (~1–2 min) with slightly lower accuracy.
    """
    try:
        sim_id = str(uuid.uuid4())

        if solver_name in ("surrogate", "model"):
            # Use trained surrogate model (fast; no OpenEMS)
            from backend.ml_models.inference_service import InferenceService

            inference = InferenceService()
            selected_model = inference.resolve_model_name(antenna_type, model_name)
            # Use s11_min + gain + efficiency models so efficiency is not s11 (dB)
            prediction = await asyncio.to_thread(
                inference.predict_for_simulation,
                parameters,
                model_name=selected_model,
                confidence=0.95,
            )
            efficiency = max(0.0, min(1.0, float(prediction.efficiency)))
            gain = max(0.0, min(30.0, float(prediction.gain)))
            at = (antenna_type or "microstrip").strip().lower()
            meta = {
                "model_name": prediction.model_name,
                "requested_model_name": selected_model,
                "antenna_type": at,
                "recommend_em_run": prediction.recommend_em_run,
                "predicted_mae": prediction.predicted_mae,
            }
            if at == "dipole":
                meta["dipole_physical"] = decode_dipole_physical_from_parameters(prediction.antenna_parameters)
            if prediction.s11 and prediction.s11.frequency and prediction.s11.s11_magnitude:
                mag = prediction.s11.s11_magnitude
                idx_min = min(range(len(mag)), key=lambda i: mag[i])
                meta["resonance_frequency"] = float(prediction.s11.frequency[idx_min])
            result = EMSimulationResult(
                simulation_id=sim_id,
                antenna_parameters=prediction.antenna_parameters,
                s11=prediction.s11,
                gain=gain,
                efficiency=efficiency,
                radiation_pattern=None,
                solver_name="surrogate",
                solver_version=prediction.model_version,
                simulation_time=prediction.prediction_time,
                timestamp=datetime.utcnow(),
                metadata=meta,
            )
            payload = _sanitize_for_json(result.model_dump(mode="json"))
            return JSONResponse(content=payload, status_code=200)

        # Physics-based solver (OpenEMS, etc.) — microstrip/patch path only
        at = (antenna_type or "microstrip").strip().lower()
        if at == "dipole":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Full EM (OpenEMS) in this app is wired for microstrip patch antennas only. "
                    "For dipole, use surrogate (fast model) trained on dipole FDTD data."
                ),
            )

        logger.info("OpenEMS simulation started (solver=%s, fast=%s)", solver_name, fast)
        solver = EMSolverFactory.create_solver(solver_name)
        results_root = Path(settings.EM_SOLVER_RESULTS_DIR).resolve()
        output_dir = results_root / sim_id
        output_dir.mkdir(parents=True, exist_ok=True)
        result = await asyncio.to_thread(solver.simulate, parameters, output_dir, fast=fast)
        logger.info("OpenEMS simulation completed in %.1fs", result.simulation_time or 0)

        def save_to_db():
            try:
                from backend.database.base import get_new_session
                db_session = get_new_session()
                try:
                    db_service.save_simulation(result, db_session)
                finally:
                    db_session.close()
            except Exception as e:
                import logging
                logging.error(f"Failed to save simulation to database: {e}")

        background_tasks.add_task(save_to_db)
        payload = _sanitize_for_json(result.model_dump(mode="json"))
        return JSONResponse(content=payload, status_code=200)

    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SolverNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EMSolverError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/design", response_model=EMSimulationResult)
async def design_antenna(
    body: DesignRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    Design a rectangular microstrip patch for the given resonance frequency and
    substrate. Returns design parameters and verified results; the run is saved.
    """
    try:
        from backend.em_solver.patch_design import design_from_frequency

        parameters = design_from_frequency(
            resonance_frequency_hz=body.resonance_frequency_hz,
            relative_permittivity=body.relative_permittivity,
            loss_tangent=body.loss_tangent,
            thickness_m=body.thickness_m,
        )
        sim_id = str(uuid.uuid4())
        results_root = Path(settings.EM_SOLVER_RESULTS_DIR).resolve()
        output_dir = results_root / sim_id
        output_dir.mkdir(parents=True, exist_ok=True)

        result = None
        try:
            solver = EMSolverFactory.create_solver("openems")
            result = await asyncio.to_thread(solver.simulate, parameters, output_dir, fast=True)
        except SolverNotAvailableError:
            from backend.ml_models.inference_service import InferenceService
            inference = InferenceService()
            prediction = await asyncio.to_thread(
                inference.predict_for_simulation, parameters, model_name="default", confidence=0.95
            )
            efficiency = max(0.0, min(1.0, float(prediction.efficiency)))
            gain = max(0.0, min(30.0, float(prediction.gain)))
            meta = {"model_name": prediction.model_name, "resonance_frequency": body.resonance_frequency_hz}
            if prediction.s11 and prediction.s11.frequency and prediction.s11.s11_magnitude:
                mag = prediction.s11.s11_magnitude
                idx = min(range(len(mag)), key=lambda i: mag[i])
                meta["actual_resonance_hz"] = float(prediction.s11.frequency[idx])
            result = EMSimulationResult(
                simulation_id=sim_id,
                antenna_parameters=parameters,
                s11=prediction.s11,
                gain=gain,
                efficiency=efficiency,
                radiation_pattern=None,
                solver_name="surrogate",
                solver_version=prediction.model_version,
                simulation_time=prediction.prediction_time,
                timestamp=datetime.utcnow(),
                metadata=meta,
            )
        if result is None:
            raise HTTPException(status_code=503, detail="Solver not available")
        result.simulation_id = sim_id
        if result.metadata is None:
            result.metadata = {}
        result.metadata["resonance_frequency"] = body.resonance_frequency_hz
        if result.s11 and result.s11.frequency and result.s11.s11_magnitude:
            mag = result.s11.s11_magnitude
            idx = min(range(len(mag)), key=lambda i: mag[i])
            result.metadata["actual_resonance_hz"] = float(result.s11.frequency[idx])

        def save_to_db():
            try:
                from backend.database.base import get_new_session
                db_session = get_new_session()
                try:
                    db_service.save_simulation(result, db_session)
                finally:
                    db_session.close()
            except Exception as e:
                logging.error("Failed to save design simulation: %s", e)

        background_tasks.add_task(save_to_db)
        payload = _sanitize_for_json(result.model_dump(mode="json"))
        return JSONResponse(content=payload, status_code=200)
    except SolverNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EMSolverError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Design failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulations", response_model=List[EMSimulationResult])
async def list_simulations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List EM simulations."""
    # TODO: Implement in Phase 1
    raise HTTPException(status_code=501, detail="Not implemented yet - Phase 1")


@router.get("/simulations/{simulation_id}", response_model=EMSimulationResult)
async def get_simulation(
    simulation_id: str,
    db: Session = Depends(get_db)
):
    """Get EM simulation by ID."""
    # TODO: Implement in Phase 1
    raise HTTPException(status_code=501, detail="Not implemented yet - Phase 1")

