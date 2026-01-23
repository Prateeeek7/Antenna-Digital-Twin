"""EM simulation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from backend.database.base import get_db
from backend.core.models.schemas import AntennaParameters, EMSimulationResult
from backend.core.exceptions import EMSolverError, SolverNotAvailableError
from backend.em_solver.factory import EMSolverFactory
from backend.em_solver.database_service import EMSimulationDatabaseService
from backend.core.config import settings

router = APIRouter(prefix="/em", tags=["EM Simulation"])

db_service = EMSimulationDatabaseService()


@router.post("/simulate", response_model=EMSimulationResult)
async def create_simulation(
    parameters: AntennaParameters,
    solver_name: str = "openems",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Create and run an EM simulation."""
    try:
        # Create solver instance
        solver = EMSolverFactory.create_solver(solver_name)
        
        # Create output directory
        import uuid
        sim_id = str(uuid.uuid4())
        output_dir = settings.EM_SOLVER_RESULTS_DIR / sim_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run simulation
        result = solver.simulate(parameters, output_dir)
        
        # Save to database (background task to avoid blocking)
        def save_to_db():
            try:
                from backend.database.base import SessionLocal
                db_session = SessionLocal()
                try:
                    db_service.save_simulation(result, db_session)
                finally:
                    db_session.close()
            except Exception as e:
                # Log error but don't fail the request
                import logging
                logging.error(f"Failed to save simulation to database: {e}")
        
        background_tasks.add_task(save_to_db)
        
        return result
        
    except SolverNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EMSolverError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


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

