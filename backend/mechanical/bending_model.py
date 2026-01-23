"""Substrate bending model."""

from typing import Tuple
import numpy as np

from backend.core.models.schemas import AntennaParameters, AntennaGeometry


class BendingModel:
    """Model substrate bending effects on antenna geometry."""
    
    def __init__(self, youngs_modulus: float = 2.4e9, poisson_ratio: float = 0.22):
        """
        Initialize bending model.
        
        Args:
            youngs_modulus: Young's modulus for FR-4 (Pa)
            poisson_ratio: Poisson's ratio for FR-4
        """
        self.E = youngs_modulus
        self.nu = poisson_ratio
    
    def calculate_bending_deformation(
        self,
        parameters: AntennaParameters,
        bending_radius: float,
        bending_axis: str = "x"
    ) -> AntennaGeometry:
        """
        Calculate deformed geometry due to bending.
        
        Args:
            parameters: Original antenna parameters
            bending_radius: Bending radius in meters (positive = convex, negative = concave)
            bending_axis: Bending axis ("x" or "y")
            
        Returns:
            Deformed AntennaGeometry
        """
        geom = parameters.geometry
        
        if bending_radius == 0 or abs(bending_radius) > 1.0:  # No bending or very large radius
            return geom
        
        # Calculate strain
        # For thin substrate, strain = thickness / (2 * radius)
        strain = geom.height / (2 * abs(bending_radius))
        
        # Apply deformation based on axis
        if bending_axis == "x":
            # Bending along x-axis affects length
            length_deformed = geom.length * (1 + strain)
            width_deformed = geom.width * (1 - self.nu * strain)
        else:  # y-axis
            length_deformed = geom.length * (1 - self.nu * strain)
            width_deformed = geom.width * (1 + strain)
        
        # Feed positions scale proportionally
        feed_x_deformed = geom.feed_x * (length_deformed / geom.length)
        feed_y_deformed = geom.feed_y * (width_deformed / geom.width)
        
        return AntennaGeometry(
            length=max(0.001, length_deformed),  # Prevent negative
            width=max(0.001, width_deformed),
            height=geom.height,  # Thickness unchanged
            feed_x=feed_x_deformed,
            feed_y=feed_y_deformed
        )



















