"""Error bounds and uncertainty quantification for ROM."""

from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats

from backend.core.models.schemas import EMSimulationResult


class ErrorBoundsCalculator:
    """Calculate error bounds for ROM predictions."""
    
    def calculate_prediction_intervals(
        self,
        true_values: np.ndarray,
        predicted_values: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate prediction intervals.
        
        Args:
            true_values: True/observed values
            predicted_values: Predicted values
            confidence: Confidence level (0-1)
            
        Returns:
            Tuple of (lower_bound, upper_bound) arrays
        """
        errors = true_values - predicted_values
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        
        # Calculate confidence interval
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        lower = predicted_values - mean_error - z_score * std_error
        upper = predicted_values - mean_error + z_score * std_error
        
        return lower, upper
    
    def calculate_per_metric_bounds(
        self,
        true_results: List[EMSimulationResult],
        predicted_results: List[EMSimulationResult],
        metric: str = "s11_min"
    ) -> Dict[str, Any]:
        """
        Calculate error bounds per metric.
        
        Args:
            true_results: True simulation results
            predicted_results: Predicted results
            metric: Metric name ("s11_min", "gain", "efficiency")
            
        Returns:
            Dictionary with error statistics
        """
        true_values = np.array([
            self._extract_metric(r, metric) for r in true_results
        ])
        pred_values = np.array([
            self._extract_metric(r, metric) for r in predicted_results
        ])
        
        errors = true_values - pred_values
        abs_errors = np.abs(errors)
        rel_errors = abs_errors / (np.abs(true_values) + 1e-10)
        
        return {
            "mean_absolute_error": float(np.mean(abs_errors)),
            "mean_relative_error": float(np.mean(rel_errors)),
            "rmse": float(np.sqrt(np.mean(errors**2))),
            "max_error": float(np.max(abs_errors)),
            "percentile_95": float(np.percentile(abs_errors, 95)),
            "percentile_99": float(np.percentile(abs_errors, 99))
        }
    
    def calculate_uncertainty_growth(
        self,
        distance_from_training: np.ndarray,
        base_uncertainty: float = 0.05
    ) -> np.ndarray:
        """
        Calculate uncertainty growth with distance from training data.
        
        Args:
            distance_from_training: Distance array
            base_uncertainty: Base uncertainty at training points
            
        Returns:
            Uncertainty values
        """
        # Exponential growth model
        growth_rate = 0.1
        uncertainty = base_uncertainty * (1 + growth_rate * distance_from_training)
        
        return uncertainty
    
    def _extract_metric(
        self,
        result: EMSimulationResult,
        metric: str
    ) -> float:
        """Extract metric value from result."""
        if metric == "s11_min":
            if result.s11 and result.s11.s11_magnitude:
                return float(min(result.s11.s11_magnitude))
            return 0.0
        elif metric == "gain":
            return result.gain
        elif metric == "efficiency":
            return result.efficiency
        else:
            raise ValueError(f"Unknown metric: {metric}")



















