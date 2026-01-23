"""Measurement ingestion API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import tempfile
from backend.database.base import get_db
from backend.core.models.schemas import MeasurementData
from backend.measurement.ingestion import MeasurementIngestionService
from backend.measurement.database_service import MeasurementDatabaseService
from backend.measurement.storage import MeasurementStorage
from backend.core.exceptions import MeasurementError

router = APIRouter(prefix="/measurements", tags=["Measurements"])

ingestion_service = MeasurementIngestionService()
db_service = MeasurementDatabaseService()

# Initialize time-series storage (optional, fails gracefully if InfluxDB not available)
try:
    ts_storage = MeasurementStorage()
    TS_STORAGE_AVAILABLE = True
except Exception:
    TS_STORAGE_AVAILABLE = False
    ts_storage = None


@router.post("/ingest", response_model=MeasurementData)
async def ingest_measurement(
    file: UploadFile = File(...),
    file_type: Optional[str] = Form("auto"),
    antenna_instance_id: Optional[str] = Form(None),
    temperature: Optional[float] = Form(None),
    humidity: Optional[float] = Form(None),
    operator: Optional[str] = Form(None),
    equipment_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Ingest measurement data from file (VNA, chamber, etc.) and persist to database."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Prepare metadata
            metadata = {}
            if temperature is not None:
                metadata["temperature"] = temperature
            if humidity is not None:
                metadata["humidity"] = humidity
            if operator:
                metadata["operator"] = operator
            if equipment_id:
                metadata["equipment_id"] = equipment_id
            
            # Ingest measurement
            measurement = ingestion_service.ingest_from_file(
                tmp_path,
                file_type=file_type,
                antenna_instance_id=antenna_instance_id,
                metadata=metadata if metadata else None
            )
            
            # Persist to database
            db_measurement = db_service.save_measurement(
                measurement,
                db,
                antenna_instance_id=antenna_instance_id
            )
            
            # Store in time-series database (background task)
            if TS_STORAGE_AVAILABLE and ts_storage:
                background_tasks.add_task(ts_storage.store_measurement, measurement)
            
            # Trigger automated Bayesian update (background task)
            background_tasks.add_task(_trigger_bayesian_update, measurement.antenna_instance_id, measurement.measurement_id)
            
            return measurement
            
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)
            
    except MeasurementError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


def _trigger_bayesian_update(antenna_instance_id: str, measurement_id: str):
    """Background task to trigger Bayesian update."""
    try:
        from backend.learning.automated_updater import AutomatedBayesianUpdater
        updater = AutomatedBayesianUpdater()
        updater.process_new_measurement(antenna_instance_id, measurement_id)
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logging.error(f"Failed to trigger Bayesian update: {e}")


@router.get("/", response_model=List[dict])
async def list_measurements(
    antenna_instance_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List measurements."""
    try:
        measurements = db_service.list_measurements(
            antenna_instance_id=antenna_instance_id,
            skip=skip,
            limit=limit,
            db=db
        )
        
        return [
            {
                "id": m.id,
                "measurement_id": m.measurement_id,
                "antenna_instance_id": m.antenna_instance.instance_id if m.antenna_instance else None,
                "gain": m.gain,
                "efficiency": m.efficiency,
                "temperature": m.temperature,
                "humidity": m.humidity,
                "quality_score": m.quality_score,
                "measured_at": m.measured_at.isoformat() if m.measured_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "metadata": m.meas_metadata,
            }
            for m in measurements
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list measurements: {str(e)}")


@router.get("/{measurement_id}")
async def get_measurement(
    measurement_id: str,
    db: Session = Depends(get_db)
):
    """Get measurement by ID."""
    try:
        measurement = db_service.get_measurement(measurement_id, db)
        
        if not measurement:
            raise HTTPException(status_code=404, detail=f"Measurement '{measurement_id}' not found")
        
        # Load S11 data if available
        s11_data = None
        if measurement.s11_data_path and Path(measurement.s11_data_path).exists():
            import json
            with open(measurement.s11_data_path, 'r') as f:
                s11_json = json.load(f)
                s11_data = {
                    "frequency": s11_json.get("frequency", []),
                    "s11_magnitude": s11_json.get("s11_magnitude", []),
                    "s11_phase": s11_json.get("s11_phase"),
                }
        
        return {
            "id": measurement.id,
            "measurement_id": measurement.measurement_id,
            "antenna_instance_id": measurement.antenna_instance.instance_id if measurement.antenna_instance else None,
            "s11": s11_data,
            "gain": measurement.gain,
            "efficiency": measurement.efficiency,
            "temperature": measurement.temperature,
            "humidity": measurement.humidity,
            "operator": measurement.operator,
            "equipment_id": measurement.equipment_id,
            "quality_score": measurement.quality_score,
            "measured_at": measurement.measured_at.isoformat() if measurement.measured_at else None,
            "created_at": measurement.created_at.isoformat() if measurement.created_at else None,
            "metadata": measurement.meas_metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get measurement: {str(e)}")

