"""Sensitivity analysis for parameter ranking."""

from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.stats import pearsonr

from backend.core.models.schemas import AntennaParameters, EMSimulationResult


class SensitivityAnalyzer:
    """Analyze parameter sensitivity for ROM construction."""
    
    def calculate_sobol_indices(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        output_metric: str = "s11_min"
    ) -> Dict[str, float]:
        """
        Calculate Sobol sensitivity indices.
        
        Args:
            parameters: List of parameter sets
            results: Corresponding simulation results
            output_metric: Metric to analyze ("s11_min", "gain", "efficiency")
            
        Returns:
            Dictionary mapping parameter names to Sobol indices
        """
        param_names = ["length", "width", "height", "feed_x", "feed_y", "permittivity"]
        
        # If we have fewer than 2 samples, return equal weights
        if len(parameters) < 2 or len(results) < 2:
            return {name: 1.0 / len(param_names) for name in param_names}
        
        # Extract parameter values
        param_values = np.array([
            [
                p.geometry.length,
                p.geometry.width,
                p.geometry.height,
                p.geometry.feed_x,
                p.geometry.feed_y,
                p.substrate.relative_permittivity
            ]
            for p in parameters
        ])
        
        # Extract output values
        output_values = np.array([
            self._extract_metric(r, output_metric) for r in results
        ])
        
        # Normalize parameters
        param_norm = (param_values - param_values.mean(axis=0)) / (param_values.std(axis=0) + 1e-10)
        output_norm = (output_values - output_values.mean()) / (output_values.std() + 1e-10)
        
        # Calculate first-order Sobol indices (correlation-based approximation)
        sobol_indices = {}
        for i, name in enumerate(param_names):
            corr, _ = pearsonr(param_norm[:, i], output_norm)
            sobol_indices[name] = abs(corr)  # Use absolute correlation as proxy
        
        # Normalize to sum to 1
        total = sum(sobol_indices.values())
        if total > 0:
            sobol_indices = {k: v / total for k, v in sobol_indices.items()}
        
        return sobol_indices
    
    def morris_screening(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        output_metric: str = "s11_min"
    ) -> Dict[str, float]:
        """
        Perform Morris screening (elementary effects method).
        
        Args:
            parameters: List of parameter sets
            results: Corresponding simulation results
            output_metric: Metric to analyze
            
        Returns:
            Dictionary mapping parameter names to Morris indices
        """
        param_names = ["length", "width", "height", "feed_x", "feed_y", "permittivity"]
        
        # If we have fewer than 2 samples, return equal weights
        if len(parameters) < 2 or len(results) < 2:
            return {name: 1.0 / len(param_names) for name in param_names}
        
        # Simplified Morris screening
        # Full implementation would use trajectory-based sampling
        
        param_values = np.array([
            [
                p.geometry.length,
                p.geometry.width,
                p.geometry.height,
                p.geometry.feed_x,
                p.geometry.feed_y,
                p.substrate.relative_permittivity
            ]
            for p in parameters
        ])
        
        output_values = np.array([
            self._extract_metric(r, output_metric) for r in results
        ])
        
        # Calculate elementary effects (simplified)
        morris_indices = {}
        for i, name in enumerate(param_names):
            # Calculate correlation as proxy for elementary effect
            param_std = param_values[:, i].std()
            output_std = output_values.std()
            
            if param_std > 0 and output_std > 0:
                corr, _ = pearsonr(param_values[:, i], output_values)
                morris_indices[name] = abs(corr) * (output_std / param_std)
            else:
                morris_indices[name] = 0.0
        
        # Normalize
        total = sum(morris_indices.values())
        if total > 0:
            morris_indices = {k: v / total for k, v in morris_indices.items()}
        
        return morris_indices
    
    def rank_parameters(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        method: str = "sobol"
    ) -> List[Tuple[str, float]]:
        """
        Rank parameters by sensitivity.
        
        Args:
            parameters: List of parameter sets
            results: Corresponding simulation results
            method: Method ("sobol" or "morris")
            
        Returns:
            List of (parameter_name, sensitivity) tuples, sorted by sensitivity
        """
        if method == "sobol":
            indices = self.calculate_sobol_indices(parameters, results)
        elif method == "morris":
            indices = self.morris_screening(parameters, results)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Sort by sensitivity (descending)
        ranked = sorted(indices.items(), key=lambda x: x[1], reverse=True)
        return ranked
    
    def _extract_metric(
        self,
        result: EMSimulationResult,
        metric: str
    ) -> float:
        """Extract metric value from simulation result."""
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





