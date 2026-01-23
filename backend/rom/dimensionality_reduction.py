"""Dimensionality reduction for ROM."""

from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from backend.core.models.schemas import AntennaParameters, EMSimulationResult


class DimensionalityReducer:
    """Reduce dimensionality of parameter space for ROM."""
    
    def __init__(self, n_components: int = 3):
        """
        Initialize reducer.
        
        Args:
            n_components: Number of reduced dimensions
        """
        self.n_components = n_components
        self.pca = PCA(n_components=n_components)
        self.scaler = StandardScaler()
        self.fitted = False
    
    def fit(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult]
    ) -> None:
        """
        Fit dimensionality reduction model.
        
        Args:
            parameters: List of parameter sets
            results: Corresponding simulation results
        """
        # Extract parameter vectors
        param_vectors = np.array([
            [
                p.geometry.length,
                p.geometry.width,
                p.geometry.height,
                p.geometry.feed_x,
                p.geometry.feed_y,
                p.substrate.relative_permittivity,
                p.substrate.loss_tangent
            ]
            for p in parameters
        ])
        
        # Scale and fit PCA
        param_scaled = self.scaler.fit_transform(param_vectors)
        self.pca.fit(param_scaled)
        self.fitted = True
    
    def transform(
        self,
        parameters: List[AntennaParameters]
    ) -> np.ndarray:
        """
        Transform parameters to reduced space.
        
        Args:
            parameters: List of parameter sets
            
        Returns:
            Reduced parameter vectors (n_samples, n_components)
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before transform")
        
        param_vectors = np.array([
            [
                p.geometry.length,
                p.geometry.width,
                p.geometry.height,
                p.geometry.feed_x,
                p.geometry.feed_y,
                p.substrate.relative_permittivity,
                p.substrate.loss_tangent
            ]
            for p in parameters
        ])
        
        param_scaled = self.scaler.transform(param_vectors)
        return self.pca.transform(param_scaled)
    
    def inverse_transform(
        self,
        reduced_vectors: np.ndarray
    ) -> np.ndarray:
        """
        Transform from reduced space back to original space.
        
        Args:
            reduced_vectors: Reduced parameter vectors
            
        Returns:
            Original parameter vectors (approximate)
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before inverse_transform")
        
        param_scaled = self.pca.inverse_transform(reduced_vectors)
        return self.scaler.inverse_transform(param_scaled)
    
    def get_explained_variance(self) -> np.ndarray:
        """Get explained variance ratio for each component."""
        if not self.fitted:
            raise ValueError("Model must be fitted")
        return self.pca.explained_variance_ratio_
    
    def get_components(self) -> np.ndarray:
        """Get principal components."""
        if not self.fitted:
            raise ValueError("Model must be fitted")
        return self.pca.components_



















