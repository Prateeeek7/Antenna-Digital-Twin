"""Model training API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from backend.database.base import get_db
from backend.core.exceptions import ModelError

router = APIRouter(prefix="/training", tags=["Training"])


class TrainingRequest(BaseModel):
    """Training request model."""
    n_samples: int = 100
    solver_name: str = "openems"
    frequency_band: str = "2.4GHz"
    model_name: str = "default"
    seed: int = 42
    use_mock: bool = False


@router.post("/start")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start model training in background.
    
    This will:
    1. Generate parameter sets using DoE
    2. Run EM simulations (or use mock data)
    3. Train surrogate models
    4. Save models to disk
    """
    # Import here to avoid circular imports
    import subprocess
    import sys
    from pathlib import Path
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "train_surrogate_model.py"
    
    if not script_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Training script not found"
        )
    
    # Build command
    cmd = [
        sys.executable,
        str(script_path),
        "--samples", str(request.n_samples),
        "--solver", request.solver_name,
        "--frequency", request.frequency_band.lower().replace("ghz", "ghz"),
        "--model-name", request.model_name,
        "--seed", str(request.seed),
    ]
    
    if request.use_mock:
        cmd.append("--mock")
    
    # Run training in background
    def run_training():
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(script_path.parent.parent)
            )
            if result.returncode != 0:
                print(f"Training error: {result.stderr}")
        except Exception as e:
            print(f"Training exception: {e}")
    
    background_tasks.add_task(run_training)
    
    return {
        "status": "started",
        "message": "Training started in background",
        "config": request.model_dump()
    }


@router.get("/status")
async def get_training_status():
    """Get training status (placeholder)."""
    return {
        "status": "idle",
        "message": "Training status not yet implemented"
    }


















