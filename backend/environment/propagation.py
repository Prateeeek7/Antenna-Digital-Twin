"""Simple propagation models."""

from typing import Dict, Any
import numpy as np


class PropagationModel:
    """Simple indoor/outdoor propagation models."""
    
    def path_loss(
        self,
        distance: float,
        frequency: float,
        environment: str = "free_space"
    ) -> float:
        """
        Calculate path loss.
        
        Args:
            distance: Distance (m)
            frequency: Frequency (Hz)
            environment: Environment type ("free_space", "indoor", "outdoor")
            
        Returns:
            Path loss (dB)
        """
        c = 3e8  # Speed of light
        wavelength = c / frequency
        
        if environment == "free_space":
            # Free space path loss
            path_loss = 20 * np.log10(4 * np.pi * distance / wavelength)
        elif environment == "indoor":
            # Indoor path loss (simplified)
            path_loss = 20 * np.log10(4 * np.pi * distance / wavelength) + 20  # +20 dB for indoor
        elif environment == "outdoor":
            # Outdoor path loss (simplified)
            path_loss = 20 * np.log10(4 * np.pi * distance / wavelength) + 10  # +10 dB for outdoor
        else:
            path_loss = 20 * np.log10(4 * np.pi * distance / wavelength)
        
        return float(path_loss)



















