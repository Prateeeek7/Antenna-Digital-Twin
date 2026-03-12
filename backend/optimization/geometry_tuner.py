"""Geometry optimization."""

from typing import Dict, Any, Optional, Callable, List, Tuple, Literal
import numpy as np
from scipy.optimize import minimize

from backend.core.models.schemas import AntennaParameters, AntennaGeometry, SubstrateProperties
from backend.ml_models.inference_service import InferenceService
from backend.optimization.spectrum_loss import spectrum_loss
from backend.optimization.cross_entropy import cross_entropy_optimize


class GeometryOptimizer:
    """Optimize antenna geometry for target objectives."""
    
    def __init__(self, inference_service: Optional[InferenceService] = None):
        """
        Initialize optimizer.
        
        Args:
            inference_service: Inference service for predictions
        """
        self.inference_service = inference_service or InferenceService()
    
    def optimize_s11(
        self,
        initial_parameters: AntennaParameters,
        target_s11: float = -10.0,
        bounds: Optional[Dict[str, tuple]] = None
    ) -> AntennaParameters:
        """
        Optimize geometry for target S11.
        
        Args:
            initial_parameters: Initial parameters
            target_s11: Target S11 (dB)
            bounds: Parameter bounds
            
        Returns:
            Optimized parameters
        """
        # Default bounds
        if bounds is None:
            bounds = {
                "length": (initial_parameters.geometry.length * 0.8, initial_parameters.geometry.length * 1.2),
                "width": (initial_parameters.geometry.width * 0.8, initial_parameters.geometry.width * 1.2),
                "feed_x": (initial_parameters.geometry.feed_x * 0.5, initial_parameters.geometry.feed_x * 1.5),
                "feed_y": (initial_parameters.geometry.feed_y * 0.5, initial_parameters.geometry.feed_y * 1.5)
            }
        
        # Objective function
        def objective(x):
            # Create parameters from x
            params = AntennaParameters(
                geometry=AntennaGeometry(
                    length=x[0],
                    width=x[1],
                    height=initial_parameters.geometry.height,
                    feed_x=x[2],
                    feed_y=x[3]
                ),
                substrate=initial_parameters.substrate,
                feed_type=initial_parameters.feed_type,
                frequency_band=initial_parameters.frequency_band,
                frequency_range=initial_parameters.frequency_range
            )
            
            # Get prediction
            pred = self.inference_service.predict(params)
            s11_min = min(pred.s11.s11_magnitude) if pred.s11.s11_magnitude else 0.0
            
            # Minimize difference from target
            return abs(s11_min - target_s11)
        
        # Initial guess
        x0 = [
            initial_parameters.geometry.length,
            initial_parameters.geometry.width,
            initial_parameters.geometry.feed_x,
            initial_parameters.geometry.feed_y
        ]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            bounds=[
                bounds["length"],
                bounds["width"],
                bounds["feed_x"],
                bounds["feed_y"]
            ]
        )
        
        # Create optimized parameters
        return AntennaParameters(
            geometry=AntennaGeometry(
                length=result.x[0],
                width=result.x[1],
                height=initial_parameters.geometry.height,
                feed_x=result.x[2],
                feed_y=result.x[3]
            ),
            substrate=initial_parameters.substrate,
            feed_type=initial_parameters.feed_type,
            frequency_band=initial_parameters.frequency_band,
            frequency_range=initial_parameters.frequency_range
        )

    def optimize_s11_spectrum(
        self,
        initial_parameters: AntennaParameters,
        target_frequency_hz: List[float],
        target_s11_magnitude_db: List[float],
        bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        optimizer: Literal["lbfgs", "cem"] = "lbfgs",
        quantile: float = 0.9,
        n_samples: int = 30,
        elite_frac: float = 0.15,
        n_iterations: int = 15,
    ) -> Tuple[AntennaParameters, Optional[List[float]]]:
        """
        Optimize geometry so predicted S11 spectrum matches a target curve (UCE-style).

        Args:
            initial_parameters: Initial antenna parameters.
            target_frequency_hz: Target frequency points (Hz).
            target_s11_magnitude_db: Target S11 magnitude in dB (same length as target_frequency_hz).
            bounds: Parameter bounds (length, width, feed_x, feed_y). If None, use ±20% around initial.
            optimizer: "lbfgs" (gradient-based) or "cem" (Cross-Entropy Method).
            quantile: Quantile for spectrum loss (0 < quantile <= 1).
            n_samples: CEM samples per iteration (only if optimizer="cem").
            elite_frac: CEM elite fraction (only if optimizer="cem").
            n_iterations: CEM iterations (only if optimizer="cem").

        Returns:
            (optimized_parameters, loss_history). loss_history is None for L-BFGS-B.
        """
        if bounds is None:
            g = initial_parameters.geometry
            bounds = {
                "length": (g.length * 0.8, g.length * 1.2),
                "width": (g.width * 0.8, g.width * 1.2),
                "feed_x": (g.feed_x * 0.5, g.feed_x * 1.5),
                "feed_y": (g.feed_y * 0.5, g.feed_y * 1.5),
            }
        bounds_list = [
            bounds["length"],
            bounds["width"],
            bounds["feed_x"],
            bounds["feed_y"],
        ]

        def objective(x: np.ndarray) -> float:
            params = AntennaParameters(
                geometry=AntennaGeometry(
                    length=float(x[0]),
                    width=float(x[1]),
                    height=initial_parameters.geometry.height,
                    feed_x=float(x[2]),
                    feed_y=float(x[3]),
                ),
                substrate=initial_parameters.substrate,
                feed_type=initial_parameters.feed_type,
                frequency_band=initial_parameters.frequency_band,
                frequency_range=initial_parameters.frequency_range,
            )
            pred = self.inference_service.predict(params)
            return spectrum_loss(
                pred.s11.frequency,
                pred.s11.s11_magnitude,
                target_frequency_hz,
                target_s11_magnitude_db,
                quantile=quantile,
            )

        x0 = np.array([
            initial_parameters.geometry.length,
            initial_parameters.geometry.width,
            initial_parameters.geometry.feed_x,
            initial_parameters.geometry.feed_y,
        ])

        if optimizer == "cem":
            best_x, _, loss_history = cross_entropy_optimize(
                objective,
                bounds_list,
                n_samples=n_samples,
                elite_frac=elite_frac,
                n_iterations=n_iterations,
                mu_init=x0,
            )
        else:
            result = minimize(
                objective,
                x0,
                method="L-BFGS-B",
                bounds=bounds_list,
            )
            best_x = result.x
            loss_history = None

        optimized = AntennaParameters(
            geometry=AntennaGeometry(
                length=float(best_x[0]),
                width=float(best_x[1]),
                height=initial_parameters.geometry.height,
                feed_x=float(best_x[2]),
                feed_y=float(best_x[3]),
            ),
            substrate=initial_parameters.substrate,
            feed_type=initial_parameters.feed_type,
            frequency_band=initial_parameters.frequency_band,
            frequency_range=initial_parameters.frequency_range,
        )
        return optimized, loss_history



















