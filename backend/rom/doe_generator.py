"""Design of Experiments (DoE) generator for ROM."""

from typing import List, Dict, Any
import numpy as np
from scipy.stats import qmc

from backend.core.models.schemas import AntennaParameters
from backend.em_solver.parameter_generator import ParameterGenerator


class DOEGenerator:
    """Generate Design of Experiments for ROM construction."""
    
    def __init__(self, parameter_generator: ParameterGenerator):
        """
        Initialize DoE generator.
        
        Args:
            parameter_generator: ParameterGenerator instance
        """
        self.param_gen = parameter_generator
    
    def generate_lhs(
        self,
        n_samples: int,
        seed: int = None
    ) -> List[AntennaParameters]:
        """
        Generate Latin Hypercube Sampling (LHS) design.
        
        Args:
            n_samples: Number of samples
            seed: Random seed
            
        Returns:
            List of parameter sets
        """
        return self.param_gen.generate_latin_hypercube(n_samples, seed)
    
    def generate_sobol(
        self,
        n_samples: int,
        seed: int = None
    ) -> List[AntennaParameters]:
        """
        Generate Sobol sequence design.
        
        Args:
            n_samples: Number of samples
            seed: Random seed
            
        Returns:
            List of parameter sets
        """
        return self.param_gen.generate_sobol_sequence(n_samples, seed)
    
    def generate_optimal_lhs(
        self,
        n_samples: int,
        iterations: int = 100,
        seed: int = None
    ) -> List[AntennaParameters]:
        """
        Generate optimized LHS (maximizes minimum distance).
        
        Args:
            n_samples: Number of samples
            iterations: Number of optimization iterations
            seed: Random seed
            
        Returns:
            List of parameter sets
        """
        # Generate multiple LHS designs and select best
        best_design = None
        best_min_dist = 0
        
        for _ in range(iterations):
            design = self.param_gen.generate_latin_hypercube(n_samples, seed)
            
            # Calculate minimum distance between points
            # (simplified - would use actual parameter space distance)
            min_dist = self._calculate_min_distance(design)
            
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_design = design
        
        return best_design or self.param_gen.generate_latin_hypercube(n_samples, seed)
    
    def _calculate_min_distance(self, parameters: List[AntennaParameters]) -> float:
        """Calculate minimum distance between parameter sets."""
        if len(parameters) < 2:
            return 0.0
        
        # Extract parameter vectors
        param_vectors = []
        for p in parameters:
            vec = [
                p.geometry.length,
                p.geometry.width,
                p.geometry.height,
                p.geometry.feed_x,
                p.geometry.feed_y,
                p.substrate.relative_permittivity
            ]
            param_vectors.append(vec)
        
        param_array = np.array(param_vectors)
        
        # Normalize
        param_array = (param_array - param_array.min(axis=0)) / (param_array.max(axis=0) - param_array.min(axis=0) + 1e-10)
        
        # Calculate pairwise distances
        from scipy.spatial.distance import pdist
        distances = pdist(param_array)
        
        return float(np.min(distances))



















