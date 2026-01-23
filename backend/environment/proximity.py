"""Proximity effects (hand, housing, etc.)."""

from typing import Optional
import numpy as np

from backend.core.models.schemas import AntennaParameters, S11Data


class ProximityModel:
    """Model proximity effects on antenna performance."""
    
    def calculate_proximity_effect(
        self,
        parameters: AntennaParameters,
        obstacle_distance: float,
        obstacle_permittivity: float = 1.0,
        obstacle_size: Optional[float] = None
    ) -> float:
        """
        Calculate S11 degradation due to proximity.
        
        Args:
            parameters: Antenna parameters
            obstacle_distance: Distance to obstacle (m)
            obstacle_permittivity: Relative permittivity of obstacle
            obstacle_size: Size of obstacle (m)
            
        Returns:
            S11 degradation factor (multiplier)
        """
        # Simple model: degradation increases with proximity
        if obstacle_distance > 0.1:  # > 10 cm
            return 1.0  # No effect
        
        # Exponential decay model
        decay_factor = np.exp(-obstacle_distance / 0.02)  # 2 cm characteristic distance
        degradation = 1.0 + decay_factor * (obstacle_permittivity - 1.0) * 0.1
        
        return float(degradation)



















