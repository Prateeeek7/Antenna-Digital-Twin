"""Validate surrogate against EM ground truth."""

from typing import List, Dict, Any
import numpy as np

from backend.core.models.schemas import EMSimulationResult, SurrogatePrediction


class EMSurrogateValidator:
    """Validate surrogate predictions against EM simulations."""
    
    def validate(
        self,
        em_results: List[EMSimulationResult],
        surrogate_predictions: List[SurrogatePrediction],
        metric: str = "s11_min"
    ) -> Dict[str, Any]:
        """
        Validate surrogate against EM.
        
        Args:
            em_results: EM simulation results
            surrogate_predictions: Surrogate predictions
            metric: Metric to validate
            
        Returns:
            Validation metrics
        """
        if len(em_results) != len(surrogate_predictions):
            return {"error": "Mismatched lengths"}
        
        em_values = []
        pred_values = []
        
        for em, pred in zip(em_results, surrogate_predictions):
            em_val = self._extract_metric(em, metric)
            pred_val = self._extract_metric(pred, metric)
            
            em_values.append(em_val)
            pred_values.append(pred_val)
        
        # Calculate errors
        errors = np.array(em_values) - np.array(pred_values)
        abs_errors = np.abs(errors)
        rel_errors = abs_errors / (np.abs(em_values) + 1e-10)
        
        return {
            "mean_absolute_error": float(np.mean(abs_errors)),
            "mean_relative_error": float(np.mean(rel_errors)),
            "rmse": float(np.sqrt(np.mean(errors**2))),
            "max_error": float(np.max(abs_errors)),
            "r2_score": float(1 - np.sum(errors**2) / np.sum((np.array(em_values) - np.mean(em_values))**2))
        }
    
    def _extract_metric(self, result, metric: str) -> float:
        """Extract metric from result."""
        if metric == "s11_min":
            if hasattr(result, 's11') and result.s11 and result.s11.s11_magnitude:
                return min(result.s11.s11_magnitude)
        elif metric == "gain":
            return result.gain
        elif metric == "efficiency":
            return result.efficiency
        return 0.0



















