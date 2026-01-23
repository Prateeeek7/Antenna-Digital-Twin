"""Trust region definition for ROM validity."""

from typing import List, Tuple, Dict, Any
import numpy as np

from backend.core.models.schemas import AntennaParameters


class TrustRegion:
    """Define valid design space (trust region) for ROM."""
    
    def __init__(self):
        """Initialize trust region."""
        self.bounds = {}
        self.center = None
        self.radius = None
    
    def fit(
        self,
        parameters: List[AntennaParameters],
        method: str = "convex_hull"
    ) -> None:
        """
        Fit trust region from parameter samples.
        
        Args:
            parameters: List of parameter sets
            method: Method ("convex_hull", "bounding_box", "ellipsoid")
        """
        if method == "bounding_box":
            self._fit_bounding_box(parameters)
        elif method == "convex_hull":
            self._fit_convex_hull(parameters)
        elif method == "ellipsoid":
            self._fit_ellipsoid(parameters)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _fit_bounding_box(self, parameters: List[AntennaParameters]) -> None:
        """Fit axis-aligned bounding box."""
        param_names = ["length", "width", "height", "feed_x", "feed_y", "permittivity"]
        
        param_vectors = np.array([
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
        
        # Calculate bounds
        self.bounds = {}
        for i, name in enumerate(param_names):
            self.bounds[name] = (
                float(param_vectors[:, i].min()),
                float(param_vectors[:, i].max())
            )
        
        # Calculate center
        center_vector = param_vectors.mean(axis=0)
        self.center = {
            name: float(center_vector[i])
            for i, name in enumerate(param_names)
        }
    
    def _fit_convex_hull(self, parameters: List[AntennaParameters]) -> None:
        """Fit convex hull (simplified to bounding box for now)."""
        # Full convex hull would use scipy.spatial.ConvexHull
        # For now, use bounding box
        self._fit_bounding_box(parameters)
    
    def _fit_ellipsoid(self, parameters: List[AntennaParameters]) -> None:
        """Fit ellipsoid trust region."""
        param_vectors = np.array([
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
        
        # Calculate center and covariance
        self.center_vector = param_vectors.mean(axis=0)
        cov = np.cov(param_vectors.T)
        
        # Store for ellipsoid check
        self.cov = cov
        self.inv_cov = np.linalg.pinv(cov)
        
        # Calculate radius (Mahalanobis distance)
        distances = []
        for vec in param_vectors:
            diff = vec - self.center_vector
            dist = np.sqrt(diff @ self.inv_cov @ diff)
            distances.append(dist)
        
        self.radius = float(np.max(distances)) * 1.1  # 10% margin
    
    def is_inside(
        self,
        parameters: AntennaParameters,
        method: str = "bounding_box"
    ) -> bool:
        """
        Check if parameters are inside trust region.
        
        Args:
            parameters: Parameter set to check
            method: Method used for trust region
            
        Returns:
            True if inside trust region
        """
        if method == "bounding_box":
            return self._check_bounding_box(parameters)
        elif method == "ellipsoid":
            return self._check_ellipsoid(parameters)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _check_bounding_box(self, parameters: AntennaParameters) -> bool:
        """Check if inside bounding box."""
        if not self.bounds:
            return True  # No bounds defined
        
        param_vec = [
            parameters.geometry.length,
            parameters.geometry.width,
            parameters.geometry.height,
            parameters.geometry.feed_x,
            parameters.geometry.feed_y,
            parameters.substrate.relative_permittivity
        ]
        
        param_names = ["length", "width", "height", "feed_x", "feed_y", "permittivity"]
        
        for i, name in enumerate(param_names):
            if name in self.bounds:
                min_val, max_val = self.bounds[name]
                if param_vec[i] < min_val or param_vec[i] > max_val:
                    return False
        
        return True
    
    def _check_ellipsoid(self, parameters: AntennaParameters) -> bool:
        """Check if inside ellipsoid."""
        if not hasattr(self, 'center_vector'):
            return True
        
        param_vec = np.array([
            parameters.geometry.length,
            parameters.geometry.width,
            parameters.geometry.height,
            parameters.geometry.feed_x,
            parameters.geometry.feed_y,
            parameters.substrate.relative_permittivity
        ])
        
        diff = param_vec - self.center_vector
        dist = np.sqrt(diff @ self.inv_cov @ diff)
        
        return dist <= self.radius
    
    def get_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Get parameter bounds."""
        return self.bounds.copy()
    
    def get_center(self) -> Dict[str, float]:
        """Get trust region center."""
        return self.center.copy() if self.center else {}



















