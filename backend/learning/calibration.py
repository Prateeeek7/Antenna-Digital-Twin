"""Calibration workflow for physical-digital alignment."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database.models import AntennaInstance, Measurement
from backend.core.models.schemas import AntennaParameters, MeasurementData, SurrogatePrediction
from backend.ml_models.inference_service import InferenceService
from backend.learning.bayesian_update import BayesianUpdater
from backend.core.exceptions import MeasurementError


class CalibrationService:
    """Service for calibrating digital twin with physical measurements."""
    
    def __init__(self):
        """Initialize calibration service."""
        self.inference_service = InferenceService()
        self.bayesian_updater = BayesianUpdater()
    
    def calibrate_instance(
        self,
        antenna_instance_id: str,
        measurement: MeasurementData,
        db: Session
    ) -> Dict[str, Any]:
        """
        Calibrate antenna instance using measurement data.
        
        Args:
            antenna_instance_id: Antenna instance ID
            measurement: Measurement data
            db: Database session
            
        Returns:
            Calibration results with discrepancy analysis
        """
        # Get antenna instance
        antenna_instance = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == antenna_instance_id
        ).first()
        
        if not antenna_instance:
            raise MeasurementError(f"Antenna instance '{antenna_instance_id}' not found")
        
        # Convert to AntennaParameters
        from backend.api.v1.antenna_instance import db_to_antenna_params
        antenna_params = db_to_antenna_params(antenna_instance)
        
        # Get model prediction
        prediction = self.inference_service.predict(antenna_params)
        
        # Compare prediction with measurement
        discrepancy = self._calculate_discrepancy(prediction, measurement)
        
        # Perform Bayesian update
        bayesian_result = self.bayesian_updater.update_model(prediction, measurement)
        
        # Calculate calibration confidence
        calibration_confidence = self._calculate_calibration_confidence(discrepancy)
        
        return {
            "antenna_instance_id": antenna_instance_id,
            "measurement_id": measurement.measurement_id,
            "discrepancy": discrepancy,
            "bayesian_update": bayesian_result,
            "calibration_confidence": calibration_confidence,
            "calibration_status": "calibrated" if calibration_confidence > 0.8 else "needs_recalibration",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _calculate_discrepancy(
        self,
        prediction: SurrogatePrediction,
        measurement: MeasurementData
    ) -> Dict[str, Any]:
        """Calculate discrepancy between prediction and measurement."""
        discrepancy = {}
        
        # S11 discrepancy
        if prediction.s11 and measurement.s11:
            pred_s11_min = min(prediction.s11.s11_magnitude) if prediction.s11.s11_magnitude else None
            meas_s11_min = min(measurement.s11.s11_magnitude) if measurement.s11.s11_magnitude else None
            
            if pred_s11_min is not None and meas_s11_min is not None:
                discrepancy["s11_min"] = {
                    "predicted": pred_s11_min,
                    "measured": meas_s11_min,
                    "difference": abs(pred_s11_min - meas_s11_min),
                    "relative_error": abs(pred_s11_min - meas_s11_min) / abs(meas_s11_min) if meas_s11_min != 0 else None,
                }
        
        # Gain discrepancy
        if prediction.gain is not None and measurement.gain is not None:
            discrepancy["gain"] = {
                "predicted": prediction.gain,
                "measured": measurement.gain,
                "difference": abs(prediction.gain - measurement.gain),
                "relative_error": abs(prediction.gain - measurement.gain) / abs(measurement.gain) if measurement.gain != 0 else None,
            }
        
        # Efficiency discrepancy
        if prediction.efficiency is not None and measurement.efficiency is not None:
            discrepancy["efficiency"] = {
                "predicted": prediction.efficiency,
                "measured": measurement.efficiency,
                "difference": abs(prediction.efficiency - measurement.efficiency),
                "relative_error": abs(prediction.efficiency - measurement.efficiency) / measurement.efficiency if measurement.efficiency != 0 else None,
            }
        
        return discrepancy
    
    def _calculate_calibration_confidence(self, discrepancy: Dict[str, Any]) -> float:
        """Calculate calibration confidence from discrepancy."""
        if not discrepancy:
            return 0.0
        
        errors = []
        
        # Collect relative errors
        for metric, data in discrepancy.items():
            if "relative_error" in data and data["relative_error"] is not None:
                errors.append(data["relative_error"])
        
        if not errors:
            return 0.5  # Default if no errors calculated
        
        # Calculate confidence: lower error = higher confidence
        mean_error = sum(errors) / len(errors)
        
        # Confidence decreases with error
        # 0% error = 1.0 confidence, 10% error = 0.5 confidence, 20%+ error = 0.0 confidence
        confidence = max(0.0, min(1.0, 1.0 - (mean_error * 10)))
        
        return confidence
    
    def get_calibration_history(
        self,
        antenna_instance_id: str,
        db: Session,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """Get calibration history for an antenna instance."""
        # Get recent measurements
        antenna_instance = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == antenna_instance_id
        ).first()
        
        if not antenna_instance:
            return []
        
        measurements = db.query(Measurement).filter(
            Measurement.antenna_instance_id == antenna_instance.id
        ).order_by(Measurement.measured_at.desc()).limit(limit).all()
        
        history = []
        for measurement in measurements:
            # Convert to MeasurementData (simplified)
            # In production, would load full S11 data
            history.append({
                "measurement_id": measurement.measurement_id,
                "measured_at": measurement.measured_at.isoformat() if measurement.measured_at else None,
                "gain": measurement.gain,
                "efficiency": measurement.efficiency,
                "quality_score": measurement.quality_score,
            })
        
        return history
