"""What-if scenario analysis."""

from typing import Dict, Any, List, Optional
from backend.core.models.schemas import AntennaParameters, SurrogatePrediction, SubstrateProperties, AntennaGeometry
from backend.ml_models.inference_service import InferenceService


class WhatIfAnalyzer:
    """Perform what-if scenario analysis."""
    
    def __init__(self, inference_service: Optional[InferenceService] = None):
        """
        Initialize analyzer.
        
        Args:
            inference_service: Inference service
        """
        self.inference_service = inference_service or InferenceService()
    
    def analyze_variation(
        self,
        base_parameters: AntennaParameters,
        variation: Dict[str, float],
        model_name: str = "default",
    ) -> Dict[str, SurrogatePrediction]:
        """
        Analyze parameter variation.
        
        Args:
            base_parameters: Base parameters
            variation: Dictionary of parameter variations (e.g., {"length": 1.1} for 10% increase)
            
        Returns:
            Dictionary mapping scenario names to predictions
        """
        results = {}
        
        # Base case
        base_pred = self.inference_service.predict(base_parameters, model_name=model_name)
        results["base"] = base_pred
        
        # Variations
        for param_name, factor in variation.items():
            # Create varied parameters
            varied_params = self._apply_variation(base_parameters, param_name, factor)
            pred = self.inference_service.predict(varied_params, model_name=model_name)
            results[f"{param_name}_{factor}"] = pred
        
        return results
    
    def _apply_variation(
        self,
        parameters: AntennaParameters,
        param_name: str,
        factor: float
    ) -> AntennaParameters:
        """Apply variation to parameter."""
        geom = parameters.geometry
        
        if param_name == "length":
            new_length = geom.length * factor
            return AntennaParameters(
                geometry=AntennaGeometry(
                    length=new_length,
                    width=geom.width,
                    height=geom.height,
                    feed_x=geom.feed_x * factor,
                    feed_y=geom.feed_y
                ),
                substrate=parameters.substrate,
                feed_type=parameters.feed_type,
                frequency_band=parameters.frequency_band,
                frequency_range=parameters.frequency_range
            )
        elif param_name == "width":
            new_width = geom.width * factor
            return AntennaParameters(
                geometry=AntennaGeometry(
                    length=geom.length,
                    width=new_width,
                    height=geom.height,
                    feed_x=geom.feed_x,
                    feed_y=geom.feed_y * factor
                ),
                substrate=parameters.substrate,
                feed_type=parameters.feed_type,
                frequency_band=parameters.frequency_band,
                frequency_range=parameters.frequency_range
            )
        elif param_name == "permittivity":
            new_er = parameters.substrate.relative_permittivity * factor
            return AntennaParameters(
                geometry=parameters.geometry,
                substrate=SubstrateProperties(
                    substrate_type=parameters.substrate.substrate_type,
                    relative_permittivity=new_er,
                    loss_tangent=parameters.substrate.loss_tangent,
                    thickness=parameters.substrate.thickness
                ),
                feed_type=parameters.feed_type,
                frequency_band=parameters.frequency_band,
                frequency_range=parameters.frequency_range
            )
        else:
            return parameters

