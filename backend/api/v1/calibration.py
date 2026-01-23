"""Calibration workflow API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.base import get_db
from backend.learning.calibration import CalibrationService
from backend.core.exceptions import MeasurementError

router = APIRouter(prefix="/calibration", tags=["Calibration"])

calibration_service = CalibrationService()


@router.post("/calibrate/{antenna_instance_id}")
async def calibrate_antenna_instance(
    antenna_instance_id: str,
    measurement_id: str,
    db: Session = Depends(get_db)
):
    """Calibrate antenna instance using measurement data."""
    try:
        # Get measurement from database
        from backend.database.models import Measurement
        from backend.measurement.database_service import MeasurementDatabaseService
        
        measurement_db = db.query(Measurement).filter(
            Measurement.measurement_id == measurement_id
        ).first()
        
        if not measurement_db:
            raise HTTPException(status_code=404, detail=f"Measurement '{measurement_id}' not found")
        
        # Convert to MeasurementData
        db_service = MeasurementDatabaseService()
        from backend.learning.automated_updater import AutomatedBayesianUpdater
        updater = AutomatedBayesianUpdater()
        measurement = updater._db_to_measurement_data(measurement_db)
        
        # Perform calibration
        result = calibration_service.calibrate_instance(
            antenna_instance_id,
            measurement,
            db
        )
        
        return result
        
    except MeasurementError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration error: {str(e)}")


@router.get("/history/{antenna_instance_id}")
async def get_calibration_history(
    antenna_instance_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get calibration history for an antenna instance."""
    try:
        history = calibration_service.get_calibration_history(
            antenna_instance_id,
            db,
            limit=limit
        )
        
        return {
            "antenna_instance_id": antenna_instance_id,
            "history": history,
            "count": len(history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get calibration history: {str(e)}")
