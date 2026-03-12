"""Automated Bayesian update service."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database.base import get_db
from backend.database.models import Measurement, AntennaInstance
from backend.core.models.schemas import MeasurementData, SurrogatePrediction
from backend.ml_models.inference_service import InferenceService
from backend.learning.bayesian_update import BayesianUpdater
from backend.learning.calibration import CalibrationService
from backend.learning.drift_detection import DriftDetector
from backend.api.v1.antenna_instance import db_to_antenna_params
from backend.core.exceptions import MeasurementError


class AutomatedBayesianUpdater:
    """Automated service for triggering Bayesian updates on new measurements."""
    
    def __init__(self):
        """Initialize automated updater."""
        self.inference_service = InferenceService()
        self.bayesian_updater = BayesianUpdater()
        self.calibration_service = CalibrationService()
        self.drift_detector = DriftDetector()
    
    def process_new_measurement(
        self,
        antenna_instance_id: str,
        measurement_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Process new measurement and trigger Bayesian update.
        
        Args:
            antenna_instance_id: Antenna instance ID
            measurement_id: Measurement ID
            db: Database session (optional, will create if not provided)
            
        Returns:
            Update results
        """
        # Get database session if not provided
        if db is None:
            from backend.database.base import get_new_session
            db = get_new_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get measurement from database
            measurement_db = db.query(Measurement).filter(
                Measurement.measurement_id == measurement_id
            ).first()
            
            if not measurement_db:
                raise MeasurementError(f"Measurement '{measurement_id}' not found")
            
            # Get antenna instance
            antenna_instance = db.query(AntennaInstance).filter(
                AntennaInstance.instance_id == antenna_instance_id
            ).first()
            
            if not antenna_instance:
                raise MeasurementError(f"Antenna instance '{antenna_instance_id}' not found")
            
            # Convert database record to MeasurementData (simplified)
            # In production, would load full S11 data from file
            measurement = self._db_to_measurement_data(measurement_db)
            
            # Get current prediction
            antenna_params = db_to_antenna_params(antenna_instance)
            prediction = self.inference_service.predict(antenna_params)
            
            # Perform calibration
            calibration_result = self.calibration_service.calibrate_instance(
                antenna_instance_id,
                measurement,
                db
            )
            
            # Check for drift
            # Get recent measurements for drift detection
            recent_measurements = db.query(Measurement).filter(
                Measurement.antenna_instance_id == antenna_instance.id
            ).order_by(Measurement.measured_at.desc()).limit(10).all()
            
            drift_result = None
            if len(recent_measurements) >= 3:
                # Convert to list of predictions and measurements for drift detection
                predictions_list = [prediction] * len(recent_measurements)
                measurements_list = [self._db_to_measurement_data(m) for m in recent_measurements]
                
                drift_result = self.drift_detector.detect_drift(
                    predictions_list,
                    measurements_list
                )
            
            # Store update metadata in measurement record
            measurement_db.meas_metadata = {
                **(measurement_db.meas_metadata or {}),
                "bayesian_update": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "calibration_confidence": calibration_result.get("calibration_confidence"),
                    "drift_detected": drift_result.get("drift_detected") if drift_result else False,
                }
            }
            
            db.commit()
            
            return {
                "measurement_id": measurement_id,
                "antenna_instance_id": antenna_instance_id,
                "calibration": calibration_result,
                "drift_detection": drift_result,
                "update_timestamp": datetime.utcnow().isoformat(),
            }
        
        finally:
            if should_close:
                db.close()
    
    def _db_to_measurement_data(self, measurement_db: Measurement) -> MeasurementData:
        """Convert database Measurement to MeasurementData."""
        # Load S11 data if available
        s11_data = None
        if measurement_db.s11_data_path:
            from pathlib import Path
            import json
            
            s11_path = Path(measurement_db.s11_data_path)
            if s11_path.exists():
                with open(s11_path, 'r') as f:
                    s11_json = json.load(f)
                    from backend.core.models.schemas import S11Data
                    s11_data = S11Data(
                        frequency=s11_json.get("frequency", []),
                        s11_magnitude=s11_json.get("s11_magnitude", []),
                        s11_phase=s11_json.get("s11_phase"),
                    )
        
        # Get antenna parameters from instance
        antenna_instance = measurement_db.antenna_instance
        antenna_params = db_to_antenna_params(antenna_instance)
        
        return MeasurementData(
            measurement_id=measurement_db.measurement_id,
            antenna_instance_id=antenna_instance.instance_id,
            antenna_parameters=antenna_params,
            s11=s11_data,
            gain=measurement_db.gain,
            efficiency=measurement_db.efficiency,
            temperature=measurement_db.temperature,
            humidity=measurement_db.humidity,
            operator=measurement_db.operator,
            equipment_id=measurement_db.equipment_id,
            timestamp=measurement_db.measured_at or datetime.utcnow(),
            quality_score=measurement_db.quality_score,
            metadata=measurement_db.meas_metadata or {},
        )
