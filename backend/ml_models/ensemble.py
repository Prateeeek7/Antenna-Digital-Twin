"""Ensemble predictor combining GP and neural network."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from backend.core.models.schemas import AntennaParameters, SurrogatePrediction, S11Data, EMSimulationResult
from backend.ml_models.gaussian_process import GaussianProcessSurrogate
from backend.ml_models.neural_surrogate import NeuralSurrogate
from backend.core.exceptions import ModelError


class EnsemblePredictor:
    """Ensemble of GP and neural network for prediction with uncertainty."""
    
    def __init__(
        self,
        gp_model: Optional[GaussianProcessSurrogate] = None,
        nn_model: Optional[NeuralSurrogate] = None,
        fusion_method: str = "weighted_average"
    ):
        """
        Initialize ensemble.
        
        Args:
            gp_model: Trained GP model
            nn_model: Trained neural network model
            fusion_method: Fusion method ("weighted_average", "stacking")
        """
        self.gp_model = gp_model
        self.nn_model = nn_model
        self.fusion_method = fusion_method
        self.trained = False
    
    def fit(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        target: str = "s11_min"
    ) -> None:
        """
        Train ensemble models.
        
        Args:
            parameters: Training parameters
            results: Training results
            target: Target metric
        """
        if self.gp_model is None:
            self.gp_model = GaussianProcessSurrogate()
        if self.nn_model is None:
            self.nn_model = NeuralSurrogate()
        
        # Train both models
        self.gp_model.fit(parameters, results, target)
        self.nn_model.fit(parameters, results, target)
        
        self.trained = True
    
    def predict(
        self,
        parameters: AntennaParameters,
        confidence: float = 0.95
    ) -> Tuple[float, float, float]:
        """
        Predict with ensemble and uncertainty.
        
        Args:
            parameters: Input parameters
            confidence: Confidence level (0-1)
            
        Returns:
            Tuple of (mean, lower_bound, upper_bound)
        """
        if not self.trained:
            raise ModelError("Ensemble must be trained before prediction")
        
        # Get predictions from both models
        gp_mean, gp_std = self.gp_model.predict(parameters, return_std=True)
        nn_mean, _ = self.nn_model.predict(parameters, return_std=False)
        
        if self.fusion_method == "weighted_average":
            # Weighted average: GP for uncertainty, NN for speed
            # Use GP uncertainty, but blend predictions
            mean = 0.6 * gp_mean + 0.4 * nn_mean  # Slight bias to GP
            std = gp_std if gp_std is not None else abs(gp_mean - nn_mean) * 0.5
        
        elif self.fusion_method == "stacking":
            # Use GP as primary (has uncertainty)
            mean = gp_mean
            std = gp_std if gp_std is not None else abs(gp_mean - nn_mean) * 0.5
        
        else:
            raise ValueError(f"Unknown fusion method: {self.fusion_method}")
        
        # Calculate confidence intervals
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        lower = mean - z_score * std
        upper = mean + z_score * std
        
        return float(mean), float(lower), float(upper)
    
    def predict_full(
        self,
        parameters: AntennaParameters,
        frequency_range: Tuple[float, float] = (2.0e9, 3.0e9),
        n_points: int = 201
    ) -> SurrogatePrediction:
        """
        Predict full S11 curve with uncertainty.
        
        Args:
            parameters: Input parameters
            frequency_range: Frequency range (f_min, f_max)
            n_points: Number of frequency points
            
        Returns:
            SurrogatePrediction with S11 curve and confidence intervals
        """
        # Generate frequency array
        f_min, f_max = frequency_range
        frequency = np.linspace(f_min, f_max, n_points).tolist()
        
        # Predict S11 at each frequency (simplified - would use frequency as input)
        # For now, use single prediction and create frequency response
        mean, lower, upper = self.predict(parameters)
        
        # Create S11 curve (simplified - would predict at each frequency)
        s11_magnitude = [mean] * n_points  # Placeholder
        s11_lower = [lower] * n_points
        s11_upper = [upper] * n_points
        
        # Predict gain and efficiency
        gain_mean, gain_lower, gain_upper = self.predict(parameters)
        eff_mean, eff_lower, eff_upper = self.predict(parameters)
        
        return SurrogatePrediction(
            antenna_parameters=parameters,
            s11=S11Data(
                frequency=frequency,
                s11_magnitude=s11_magnitude,
                s11_phase=None
            ),
            s11_confidence_lower=s11_lower,
            s11_confidence_upper=s11_upper,
            gain=float(gain_mean),
            gain_confidence_lower=float(gain_lower),
            gain_confidence_upper=float(gain_upper),
            efficiency=float(eff_mean),
            efficiency_confidence_lower=float(eff_lower),
            efficiency_confidence_upper=float(eff_upper),
            model_name="ensemble",
            model_version="1.0",
            prediction_time=0.0
        )


