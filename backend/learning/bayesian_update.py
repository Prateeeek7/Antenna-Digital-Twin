"""Bayesian model updating from measurements."""

from typing import List, Dict, Any
import numpy as np

from backend.core.models.schemas import AntennaParameters, MeasurementData, SurrogatePrediction


class BayesianUpdater:
    """Update surrogate models using Bayesian inference."""
    
    def update_model(
        self,
        model_prediction: SurrogatePrediction,
        measurement: MeasurementData,
        prior_variance: float = 1.0
    ) -> Dict[str, Any]:
        """
        Update model prediction using measurement (Bayesian update).
        
        Args:
            model_prediction: Model prediction
            measurement: New measurement
            prior_variance: Prior uncertainty variance
            
        Returns:
            Dictionary with updated predictions and uncertainty
        """
        # Simplified Bayesian update
        # Full implementation would use proper Bayesian inference
        
        if measurement.s11 and model_prediction.s11:
            # Update S11 prediction
            measured_s11 = min(measurement.s11.s11_magnitude) if measurement.s11.s11_magnitude else None
            predicted_s11 = min(model_prediction.s11.s11_magnitude) if model_prediction.s11.s11_magnitude else None
            
            if measured_s11 is not None and predicted_s11 is not None:
                # Weighted average (simplified)
                measurement_weight = 0.7
                model_weight = 0.3
                
                updated_s11 = measurement_weight * measured_s11 + model_weight * predicted_s11
                updated_variance = prior_variance * 0.5  # Reduced uncertainty
                
                return {
                    "updated_s11": float(updated_s11),
                    "updated_variance": float(updated_variance),
                    "update_weight": float(measurement_weight)
                }
        
        return {
            "updated_s11": None,
            "updated_variance": prior_variance,
            "update_weight": 0.0
        }



















