"""Thermal expansion model."""

from typing import Tuple
import numpy as np

from backend.core.models.schemas import AntennaParameters, AntennaGeometry


class ThermalExpansionModel:
    """Model thermal expansion effects."""
    
    def __init__(self, cte: float = 16e-6):
        """
        Initialize thermal expansion model.
        
        Args:
            cte: Coefficient of thermal expansion (1/K) for FR-4
        """
        self.cte = cte
    
    def calculate_thermal_deformation(
        self,
        parameters: AntennaParameters,
        temperature: float,
        reference_temperature: float = 25.0
    ) -> AntennaGeometry:
        """
        Calculate deformation due to thermal expansion.
        
        Args:
            parameters: Original parameters
            temperature: Current temperature (Celsius)
            reference_temperature: Reference temperature (Celsius)
            
        Returns:
            Deformed AntennaGeometry
        """
        geom = parameters.geometry
        
        # Calculate temperature change
        delta_T = temperature - reference_temperature
        
        # Calculate expansion factor
        expansion_factor = 1 + self.cte * delta_T
        
        # Apply to all dimensions
        length_deformed = geom.length * expansion_factor
        width_deformed = geom.width * expansion_factor
        height_deformed = geom.height * expansion_factor
        
        # Feed positions scale
        feed_x_deformed = geom.feed_x * expansion_factor
        feed_y_deformed = geom.feed_y * expansion_factor
        
        return AntennaGeometry(
            length=max(0.001, length_deformed),
            width=max(0.001, width_deformed),
            height=max(0.0001, height_deformed),
            feed_x=feed_x_deformed,
            feed_y=feed_y_deformed
        )



















