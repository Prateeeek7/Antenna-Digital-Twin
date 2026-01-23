"""Geometry optimization."""

from typing import Dict, Any, Optional, Callable
import numpy as np
from scipy.optimize import minimize, differential_evolution

from backend.core.models.schemas import AntennaParameters, AntennaGeometry, SubstrateProperties
from backend.ml_models.inference_service import InferenceService


class GeometryOptimizer:
    """Optimize antenna geometry for target objectives."""
    
    def __init__(self, inference_service: Optional[InferenceService] = None):
        """
        Initialize optimizer.
        
        Args:
            inference_service: Inference service for predictions
        """
        self.inference_service = inference_service or InferenceService()
    
    def optimize_s11(
        self,
        initial_parameters: AntennaParameters,
        target_s11: float = -10.0,
        bounds: Optional[Dict[str, tuple]] = None
    ) -> AntennaParameters:
        """
        Optimize geometry for target S11.
        
        Args:
            initial_parameters: Initial parameters
            target_s11: Target S11 (dB)
            bounds: Parameter bounds
            
        Returns:
            Optimized parameters
        """
        # Default bounds
        if bounds is None:
            bounds = {
                "length": (initial_parameters.geometry.length * 0.8, initial_parameters.geometry.length * 1.2),
                "width": (initial_parameters.geometry.width * 0.8, initial_parameters.geometry.width * 1.2),
                "feed_x": (initial_parameters.geometry.feed_x * 0.5, initial_parameters.geometry.feed_x * 1.5),
                "feed_y": (initial_parameters.geometry.feed_y * 0.5, initial_parameters.geometry.feed_y * 1.5)
            }
        
        # Objective function
        def objective(x):
            # Create parameters from x
            params = AntennaParameters(
                geometry=AntennaGeometry(
                    length=x[0],
                    width=x[1],
                    height=initial_parameters.geometry.height,
                    feed_x=x[2],
                    feed_y=x[3]
                ),
                substrate=initial_parameters.substrate,
                feed_type=initial_parameters.feed_type,
                frequency_band=initial_parameters.frequency_band,
                frequency_range=initial_parameters.frequency_range
            )
            
            # Get prediction
            pred = self.inference_service.predict(params)
            s11_min = min(pred.s11.s11_magnitude) if pred.s11.s11_magnitude else 0.0
            
            # Minimize difference from target
            return abs(s11_min - target_s11)
        
        # Initial guess
        x0 = [
            initial_parameters.geometry.length,
            initial_parameters.geometry.width,
            initial_parameters.geometry.feed_x,
            initial_parameters.geometry.feed_y
        ]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            bounds=[
                bounds["length"],
                bounds["width"],
                bounds["feed_x"],
                bounds["feed_y"]
            ]
        )
        
        # Create optimized parameters
        return AntennaParameters(
            geometry=AntennaGeometry(
                length=result.x[0],
                width=result.x[1],
                height=initial_parameters.geometry.height,
                feed_x=result.x[2],
                feed_y=result.x[3]
            ),
            substrate=initial_parameters.substrate,
            feed_type=initial_parameters.feed_type,
            frequency_band=initial_parameters.frequency_band,
            frequency_range=initial_parameters.frequency_range
        )



















