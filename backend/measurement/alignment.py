"""Parameter alignment between measurements and EM simulations."""

from typing import Dict, Any, Optional
import numpy as np

from backend.core.models.schemas import AntennaParameters
from backend.core.exceptions import MeasurementError


class ParameterAligner:
    """Align measurement parameters with known antenna parameters."""
    
    def align(
        self,
        measurement_data: Dict[str, Any],
        known_parameters: AntennaParameters
    ) -> AntennaParameters:
        """
        Align measurement data with known antenna parameters.
        
        This ensures that measurement data is associated with the correct
        antenna geometry and substrate properties.
        
        Args:
            measurement_data: Parsed measurement data
            known_parameters: Known antenna parameters from database/design
            
        Returns:
            Aligned AntennaParameters
        """
        # For now, return known parameters
        # In production, could:
        # - Extract parameters from measurement metadata
        # - Match closest design in database
        # - Validate consistency
        
        # Check if measurement has parameter hints
        measured_params = measurement_data.get("antenna_parameters")
        if measured_params:
            # Validate consistency
            tolerance = 0.01  # 1% tolerance
            
            if abs(measured_params.geometry.length - known_parameters.geometry.length) / known_parameters.geometry.length > tolerance:
                raise MeasurementError(
                    f"Length mismatch: measured {measured_params.geometry.length} vs "
                    f"known {known_parameters.geometry.length}"
                )
            
            # Use measured parameters if within tolerance
            return measured_params
        
        # Use known parameters
        return known_parameters
    
    def find_closest_match(
        self,
        measurement_data: Dict[str, Any],
        candidate_parameters: list[AntennaParameters]
    ) -> Optional[AntennaParameters]:
        """
        Find closest matching antenna parameters from candidates.
        
        Args:
            measurement_data: Parsed measurement data
            candidate_parameters: List of candidate parameter sets
            
        Returns:
            Closest matching AntennaParameters or None
        """
        if not candidate_parameters:
            return None
        
        # Extract measurement hints
        measured_params = measurement_data.get("antenna_parameters")
        if not measured_params:
            return None
        
        # Calculate distances
        distances = []
        for candidate in candidate_parameters:
            dist = self._calculate_parameter_distance(measured_params, candidate)
            distances.append(dist)
        
        # Return closest match
        min_idx = np.argmin(distances)
        return candidate_parameters[min_idx]
    
    def _calculate_parameter_distance(
        self,
        params1: AntennaParameters,
        params2: AntennaParameters
    ) -> float:
        """Calculate normalized distance between parameter sets."""
        g1 = params1.geometry
        g2 = params2.geometry
        s1 = params1.substrate
        s2 = params2.substrate
        
        # Normalized differences
        length_diff = abs(g1.length - g2.length) / max(g1.length, g2.length)
        width_diff = abs(g1.width - g2.width) / max(g1.width, g2.width)
        height_diff = abs(g1.height - g2.height) / max(g1.height, g2.height)
        er_diff = abs(s1.relative_permittivity - s2.relative_permittivity) / max(s1.relative_permittivity, s2.relative_permittivity)
        
        # Weighted sum
        distance = (
            0.3 * length_diff +
            0.3 * width_diff +
            0.2 * height_diff +
            0.2 * er_diff
        )
        
        return distance



















