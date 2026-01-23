"""Mounting stress model."""

from typing import Tuple
import numpy as np

from backend.core.models.schemas import AntennaParameters, AntennaGeometry


class StressModel:
    """Model mounting stress effects on antenna."""
    
    def __init__(self):
        """Initialize stress model."""
        pass
    
    def calculate_stress_deformation(
        self,
        parameters: AntennaParameters,
        stress_x: float = 0.0,
        stress_y: float = 0.0
    ) -> AntennaGeometry:
        """
        Calculate deformation due to mounting stress.
        
        Args:
            parameters: Original parameters
            stress_x: Stress in x-direction (Pa)
            stress_y: Stress in y-direction (Pa)
            
        Returns:
            Deformed AntennaGeometry
        """
        geom = parameters.geometry
        
        # Simple linear stress-strain model
        E = 2.4e9  # Young's modulus for FR-4 (Pa)
        nu = 0.22  # Poisson's ratio
        
        # Calculate strains
        strain_x = stress_x / E
        strain_y = stress_y / E
        
        # Apply Poisson effect
        effective_strain_x = strain_x - nu * strain_y
        effective_strain_y = strain_y - nu * strain_x
        
        # Deform geometry
        length_deformed = geom.length * (1 + effective_strain_x)
        width_deformed = geom.width * (1 + effective_strain_y)
        
        # Feed positions scale
        feed_x_deformed = geom.feed_x * (length_deformed / geom.length)
        feed_y_deformed = geom.feed_y * (width_deformed / geom.width)
        
        return AntennaGeometry(
            length=max(0.001, length_deformed),
            width=max(0.001, width_deformed),
            height=geom.height,
            feed_x=feed_x_deformed,
            feed_y=feed_y_deformed
        )



















