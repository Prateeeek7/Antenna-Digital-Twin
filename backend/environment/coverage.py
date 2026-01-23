"""Coverage probability calculation."""

from typing import List, Tuple, Dict, Any
import numpy as np

from backend.core.models.schemas import RadiationPattern
from backend.environment.propagation import PropagationModel


class CoverageCalculator:
    """Calculate coverage probability maps."""
    
    def __init__(self):
        """Initialize coverage calculator."""
        self.propagation_model = PropagationModel()
    
    def calculate_coverage(
        self,
        pattern: RadiationPattern,
        distance: float,
        frequency: float,
        environment: str = "free_space",
        threshold_gain: float = -80.0
    ) -> Dict[str, Any]:
        """
        Calculate coverage probability.
        
        Args:
            pattern: Radiation pattern
            distance: Distance (m)
            frequency: Frequency (Hz)
            environment: Environment type
            threshold_gain: Minimum gain threshold (dB)
            
        Returns:
            Dictionary with coverage statistics
        """
        # Calculate path loss
        path_loss = self.propagation_model.path_loss(distance, frequency, environment)
        
        # Extract gain values
        if pattern.gain:
            gains_flat = [g for row in pattern.gain for g in row]
            if gains_flat:
                max_gain = max(gains_flat)
                min_gain = min(gains_flat)
                mean_gain = np.mean(gains_flat)
                
                # Calculate coverage (gain - path_loss > threshold)
                effective_gain = max_gain - path_loss
                coverage_probability = 1.0 if effective_gain > threshold_gain else 0.0
                
                return {
                    "coverage_probability": float(coverage_probability),
                    "effective_gain": float(effective_gain),
                    "path_loss": float(path_loss),
                    "max_gain": float(max_gain),
                    "mean_gain": float(mean_gain)
                }
        
        return {
            "coverage_probability": 0.0,
            "effective_gain": -100.0,
            "path_loss": float(path_loss)
        }



















