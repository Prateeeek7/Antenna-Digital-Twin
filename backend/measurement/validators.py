"""Measurement data validation."""

from typing import Dict, Any, List
import numpy as np

from backend.core.models.schemas import S11Data, RadiationPattern
from backend.core.exceptions import MeasurementError


class MeasurementValidator:
    """Validate measurement data quality."""
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate measurement data.
        
        Args:
            data: Parsed measurement data
            
        Returns:
            Dictionary with validation results:
            - valid: bool
            - quality_score: float (0-1)
            - errors: List[str]
            - warnings: List[str]
        """
        errors = []
        warnings = []
        quality_score = 1.0
        
        # Validate S11 data if present
        if "s11" in data and data["s11"] is not None:
            s11_result = self._validate_s11(data["s11"])
            if not s11_result["valid"]:
                errors.extend(s11_result["errors"])
            warnings.extend(s11_result["warnings"])
            quality_score = min(quality_score, s11_result["quality_score"])
        
        # Validate radiation pattern if present
        if "radiation_pattern" in data and data["radiation_pattern"] is not None:
            pattern_result = self._validate_pattern(data["radiation_pattern"])
            if not pattern_result["valid"]:
                errors.extend(pattern_result["errors"])
            warnings.extend(pattern_result["warnings"])
            quality_score = min(quality_score, pattern_result["quality_score"])
        
        # Validate gain
        if "gain" in data and data["gain"] is not None:
            gain_result = self._validate_gain(data["gain"])
            if not gain_result["valid"]:
                errors.extend(gain_result["errors"])
            quality_score = min(quality_score, gain_result["quality_score"])
        
        return {
            "valid": len(errors) == 0,
            "quality_score": quality_score,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_s11(self, s11: S11Data) -> Dict[str, Any]:
        """Validate S11 data."""
        errors = []
        warnings = []
        quality_score = 1.0
        
        # Check data exists
        if not s11.frequency or not s11.s11_magnitude:
            errors.append("S11 data is empty")
            return {"valid": False, "errors": errors, "warnings": warnings, "quality_score": 0.0}
        
        # Check array lengths match
        if len(s11.frequency) != len(s11.s11_magnitude):
            errors.append("Frequency and S11 magnitude arrays have different lengths")
            quality_score = 0.0
        
        # Check frequency is monotonic
        if len(s11.frequency) > 1:
            freq_diff = np.diff(s11.frequency)
            if np.any(freq_diff <= 0):
                warnings.append("Frequency array is not strictly increasing")
                quality_score *= 0.9
        
        # Check S11 values are reasonable (typically negative dB)
        s11_array = np.array(s11.s11_magnitude)
        if np.any(s11_array > 0):
            warnings.append("Some S11 values are positive (unusual for antenna)")
            quality_score *= 0.95
        
        # Check for outliers
        if len(s11_array) > 10:
            q1, q3 = np.percentile(s11_array, [25, 75])
            iqr = q3 - q1
            outliers = np.sum((s11_array < q1 - 3*iqr) | (s11_array > q3 + 3*iqr))
            if outliers > len(s11_array) * 0.1:  # More than 10% outliers
                warnings.append(f"Many outliers detected in S11 data ({outliers} points)")
                quality_score *= 0.9
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality_score": quality_score
        }
    
    def _validate_pattern(self, pattern: RadiationPattern) -> Dict[str, Any]:
        """Validate radiation pattern data."""
        errors = []
        warnings = []
        quality_score = 1.0
        
        if not pattern.theta or not pattern.phi or not pattern.gain:
            errors.append("Radiation pattern data is incomplete")
            return {"valid": False, "errors": errors, "warnings": warnings, "quality_score": 0.0}
        
        # Check gain matrix dimensions
        if len(pattern.gain) != len(pattern.theta):
            errors.append("Gain matrix rows don't match theta array length")
            quality_score = 0.0
        
        if len(pattern.gain) > 0 and len(pattern.gain[0]) != len(pattern.phi):
            errors.append("Gain matrix columns don't match phi array length")
            quality_score = 0.0
        
        # Check gain values are reasonable
        gain_flat = [g for row in pattern.gain for g in row]
        if gain_flat:
            gain_array = np.array(gain_flat)
            if np.any(gain_array > 20):  # Unusually high gain
                warnings.append("Some gain values are unusually high (>20 dBi)")
                quality_score *= 0.9
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality_score": quality_score
        }
    
    def _validate_gain(self, gain: float) -> Dict[str, Any]:
        """Validate gain value."""
        errors = []
        quality_score = 1.0
        
        if gain < -10 or gain > 20:
            errors.append(f"Gain value {gain} dBi is outside reasonable range")
            quality_score = 0.5
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
            "quality_score": quality_score
        }



















