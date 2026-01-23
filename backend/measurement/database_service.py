"""Database service for measurement persistence."""

from typing import Optional
from pathlib import Path
from datetime import datetime
import json
import uuid
from sqlalchemy.orm import Session

from backend.database.models import Measurement, AntennaInstance
from backend.core.models.schemas import MeasurementData, S11Data
from backend.core.config import settings
from backend.core.exceptions import MeasurementError


class MeasurementDatabaseService:
    """Service for persisting measurements to database."""
    
    def __init__(self):
        """Initialize database service."""
        self.measurements_dir = settings.EM_SOLVER_RESULTS_DIR.parent / "measurements"
        self.measurements_dir.mkdir(parents=True, exist_ok=True)
    
    def save_measurement(
        self,
        measurement: MeasurementData,
        db: Session,
        antenna_instance_id: Optional[str] = None
    ) -> Measurement:
        """
        Save measurement to database.
        
        Args:
            measurement: MeasurementData to save
            db: Database session
            antenna_instance_id: Antenna instance ID (if not in measurement)
            
        Returns:
            Database Measurement record
        """
        # Get or validate antenna instance
        instance_id = measurement.antenna_instance_id or antenna_instance_id
        if not instance_id:
            raise MeasurementError("antenna_instance_id is required")
        
        # Verify antenna instance exists
        antenna_instance = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == instance_id
        ).first()
        
        if not antenna_instance:
            raise MeasurementError(f"Antenna instance '{instance_id}' not found")
        
        # Save S11 data to file
        s11_data_path = None
        if measurement.s11:
            s11_data_path = self._save_s11_data(measurement.measurement_id, measurement.s11)
        
        # Save radiation pattern if available
        radiation_pattern_path = None
        if measurement.radiation_pattern:
            radiation_pattern_path = self._save_radiation_pattern(
                measurement.measurement_id,
                measurement.radiation_pattern
            )
        
        # Create database record
        db_measurement = Measurement(
            measurement_id=measurement.measurement_id,
            antenna_instance_id=antenna_instance.id,  # Use database ID, not instance_id
            s11_data_path=str(s11_data_path) if s11_data_path else None,
            gain=measurement.gain,
            efficiency=measurement.efficiency,
            radiation_pattern_path=str(radiation_pattern_path) if radiation_pattern_path else None,
            temperature=measurement.temperature,
            humidity=measurement.humidity,
            operator=measurement.operator,
            equipment_id=measurement.equipment_id,
            quality_score=measurement.quality_score,
            measured_at=measurement.timestamp,
            meas_metadata=measurement.metadata,
        )
        
        db.add(db_measurement)
        db.commit()
        db.refresh(db_measurement)
        
        return db_measurement
    
    def _save_s11_data(self, measurement_id: str, s11: S11Data) -> Path:
        """Save S11 data to JSON file."""
        file_path = self.measurements_dir / f"{measurement_id}_s11.json"
        
        data = {
            "frequency": s11.frequency,
            "s11_magnitude": s11.s11_magnitude,
            "s11_phase": s11.s11_phase,
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return file_path
    
    def _save_radiation_pattern(self, measurement_id: str, pattern) -> Path:
        """Save radiation pattern to JSON file."""
        file_path = self.measurements_dir / f"{measurement_id}_pattern.json"
        
        data = {
            "theta": pattern.theta,
            "phi": pattern.phi,
            "gain": pattern.gain,
            "e_plane": pattern.e_plane,
            "h_plane": pattern.h_plane,
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return file_path
    
    def get_measurement(self, measurement_id: str, db: Session) -> Optional[Measurement]:
        """Get measurement from database."""
        return db.query(Measurement).filter(
            Measurement.measurement_id == measurement_id
        ).first()
    
    def list_measurements(
        self,
        antenna_instance_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = None
    ) -> list[Measurement]:
        """List measurements from database."""
        query = db.query(Measurement)
        
        if antenna_instance_id:
            # Find antenna instance by instance_id
            antenna_instance = db.query(AntennaInstance).filter(
                AntennaInstance.instance_id == antenna_instance_id
            ).first()
            
            if antenna_instance:
                query = query.filter(Measurement.antenna_instance_id == antenna_instance.id)
        
        return query.order_by(Measurement.measured_at.desc()).offset(skip).limit(limit).all()
