"""Model drift detection."""

from typing import List, Dict, Any
import numpy as np
from datetime import datetime, timedelta

from backend.core.models.schemas import MeasurementData, SurrogatePrediction


class DriftDetector:
    """Detect model drift from measurements."""
    
    def __init__(self, threshold: float = 0.1):
        """
        Initialize drift detector.
        
        Args:
            threshold: Drift detection threshold (relative error)
        """
        self.threshold = threshold
        self.history = []
    
    def detect_drift(
        self,
        predictions: List[SurrogatePrediction],
        measurements: List[MeasurementData]
    ) -> Dict[str, Any]:
        """
        Detect model drift.
        
        Args:
            predictions: Model predictions
            measurements: Corresponding measurements
            
        Returns:
            Dictionary with drift detection results
        """
        if len(predictions) != len(measurements):
            return {"drift_detected": False, "error": "Mismatched lengths"}
        
        errors = []
        for pred, meas in zip(predictions, measurements):
            if meas.s11 and pred.s11:
                pred_s11 = min(pred.s11.s11_magnitude) if pred.s11.s11_magnitude else 0.0
                meas_s11 = min(meas.s11.s11_magnitude) if meas.s11.s11_magnitude else 0.0
                
                if meas_s11 != 0:
                    rel_error = abs(pred_s11 - meas_s11) / abs(meas_s11)
                    errors.append(rel_error)
        
        if not errors:
            return {"drift_detected": False, "mean_error": 0.0}
        
        mean_error = np.mean(errors)
        drift_detected = mean_error > self.threshold
        
        return {
            "drift_detected": drift_detected,
            "mean_error": float(mean_error),
            "threshold": self.threshold,
            "sample_count": len(errors)
        }



















