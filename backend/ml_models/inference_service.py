"""Fast inference service for surrogate models."""

import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import numpy as np

from backend.core.models.schemas import AntennaParameters, SurrogatePrediction, S11Data
from backend.ml_models.ensemble import EnsemblePredictor
from backend.ml_models.accuracy_predictor import AccuracyPredictor
from backend.ml_models.training_pipeline import TrainingPipeline
from backend.ml_models.training_cache import load_training_cache, extract_features
from backend.core.config import settings
from backend.core.exceptions import ModelError, ModelNotFoundError


class InferenceService:
    """Fast inference service for surrogate model predictions."""
    
    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize inference service.
        
        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir or settings.ML_MODEL_DIR
        self.models: Dict[str, EnsemblePredictor] = {}
        self.accuracy_predictors: Dict[str, AccuracyPredictor] = {}
        self.training_pipeline = TrainingPipeline(self.model_dir)
        self._training_cache: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = None
    
    def load_model(self, model_name: str, metric: str = "s11_min") -> None:
        """
        Load model into memory.
        
        Args:
            model_name: Model name
            metric: Target metric
        """
        model_path = self.model_dir / f"{model_name}_{metric}.pkl"
        
        if not model_path.exists():
            raise ModelNotFoundError(f"Model not found: {model_path}")
        
        model = self.training_pipeline.load_model(model_path)
        key = f"{model_name}_{metric}"
        self.models[key] = model
    
    def predict(
        self,
        parameters: AntennaParameters,
        model_name: str = "default",
        metric: str = "s11_min",
        confidence: float = 0.95
    ) -> SurrogatePrediction:
        """
        Get prediction from surrogate model.
        
        Args:
            parameters: Input parameters
            model_name: Model name
            metric: Target metric
            confidence: Confidence level
            
        Returns:
            SurrogatePrediction with uncertainty
        """
        key = f"{model_name}_{metric}"
        
        # Load model if not in memory
        if key not in self.models:
            self.load_model(model_name, metric)
        
        model = self.models[key]
        
        # Get prediction
        import time
        start_time = time.time()
        
        prediction = model.predict_full(
            parameters,
            frequency_range=parameters.frequency_range
        )
        
        prediction.prediction_time = time.time() - start_time

        # Twin-model: accuracy predictor recommends when to run full EM
        acc_key = f"{model_name}_{metric}"
        if acc_key not in self.accuracy_predictors:
            loaded = self.training_pipeline.load_accuracy_predictor(model_name, metric)
            if loaded is not None:
                self.accuracy_predictors[acc_key] = loaded
        acc_predictor = self.accuracy_predictors.get(acc_key)
        threshold = getattr(settings, "EM_ACCURACY_THRESHOLD_MAE", 1.0)
        if acc_predictor is not None and acc_predictor.trained:
            predicted_mae = acc_predictor.predict_mae(parameters)
            recommendation = predicted_mae > threshold
            prediction.recommend_em_run = recommendation
            prediction.predicted_mae = predicted_mae
        else:
            prediction.recommend_em_run = None
            prediction.predicted_mae = None
        
        return prediction

    def _get_training_cache(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Load and cache (X, y_s11, y_gain, y_eff) from Simulation_Data.csv."""
        if self._training_cache is None:
            self._training_cache = load_training_cache()
        return self._training_cache

    def _blend_with_nearest(
        self,
        parameters: AntennaParameters,
        s11_pred: SurrogatePrediction,
        gain_mean: float,
        gain_lo: float,
        gain_hi: float,
        eff_mean: float,
        eff_lo: float,
        eff_hi: float,
        key_s11: str,
    ) -> Tuple[S11Data, List[float], List[float], float, float, float, float, float, float]:
        """
        If the design is close to a training row, blend model output toward that row's OpenEMS values
        so model and OpenEMS results are closer. Returns (s11, s11_lower, s11_upper, gain_mean, ...).
        """
        out_s11 = s11_pred.s11
        out_s11_lower = s11_pred.s11_confidence_lower or s11_pred.s11.s11_magnitude
        out_s11_upper = s11_pred.s11_confidence_upper or s11_pred.s11.s11_magnitude
        out_gain_mean, out_gain_lo, out_gain_hi = gain_mean, gain_lo, gain_hi
        out_eff_mean, out_eff_lo, out_eff_hi = eff_mean, eff_lo, eff_hi

        if not getattr(settings, "NN_BLEND_ENABLED", True):
            return out_s11, out_s11_lower, out_s11_upper, out_gain_mean, out_gain_lo, out_gain_hi, out_eff_mean, out_eff_lo, out_eff_hi

        X, y_s11, y_gain, y_eff = self._get_training_cache()
        if X.shape[0] == 0:
            return out_s11, out_s11_lower, out_s11_upper, out_gain_mean, out_gain_lo, out_gain_hi, out_eff_mean, out_eff_lo, out_eff_hi

        ensemble = self.models.get(key_s11)
        if ensemble is None or not getattr(ensemble, "gp_model", None):
            return out_s11, out_s11_lower, out_s11_upper, out_gain_mean, out_gain_lo, out_gain_hi, out_eff_mean, out_eff_lo, out_eff_hi
        scaler_x = getattr(ensemble.gp_model, "scaler_x", None)
        if scaler_x is None:
            return out_s11, out_s11_lower, out_s11_upper, out_gain_mean, out_gain_lo, out_gain_hi, out_eff_mean, out_eff_lo, out_eff_hi

        x = extract_features(parameters).reshape(1, -1)
        x_scaled = scaler_x.transform(x)
        X_scaled = scaler_x.transform(X)
        distances = np.linalg.norm(X_scaled - x_scaled, axis=1)
        i = int(np.argmin(distances))
        d = float(distances[i])
        threshold = getattr(settings, "NN_BLEND_DISTANCE_THRESHOLD", 2.0)
        weight_max = getattr(settings, "NN_BLEND_WEIGHT_MAX", 0.5)
        if d >= threshold:
            return out_s11, out_s11_lower, out_s11_upper, out_gain_mean, out_gain_lo, out_gain_hi, out_eff_mean, out_eff_lo, out_eff_hi

        alpha = weight_max * max(0.0, 1.0 - d / threshold)
        model_s11_min = min(s11_pred.s11.s11_magnitude)
        blended_s11_min = (1.0 - alpha) * model_s11_min + alpha * float(y_s11[i])
        shift = blended_s11_min - model_s11_min
        new_s11 = [max(-60.0, min(0.0, m + shift)) for m in s11_pred.s11.s11_magnitude]
        new_s11_lower = [max(-60.0, min(0.0, m + shift)) for m in (out_s11_lower or new_s11)]
        new_s11_upper = [max(-60.0, min(0.0, m + shift)) for m in (out_s11_upper or new_s11)]
        out_s11 = S11Data(
            frequency=s11_pred.s11.frequency,
            s11_magnitude=new_s11,
            s11_phase=s11_pred.s11.s11_phase,
        )
        out_s11_lower = new_s11_lower
        out_s11_upper = new_s11_upper
        out_gain_mean = (1.0 - alpha) * gain_mean + alpha * float(y_gain[i])
        out_gain_mean = max(0.0, min(30.0, out_gain_mean))
        out_gain_lo = out_gain_mean - (gain_mean - gain_lo)
        out_gain_hi = out_gain_mean + (gain_hi - gain_mean)
        out_eff_mean = (1.0 - alpha) * eff_mean + alpha * float(y_eff[i])
        out_eff_mean = max(0.0, min(1.0, out_eff_mean))
        out_eff_lo = max(0.0, out_eff_mean - (eff_mean - eff_lo))
        out_eff_hi = min(1.0, out_eff_mean + (eff_hi - eff_mean))
        return out_s11, out_s11_lower, out_s11_upper, out_gain_mean, out_gain_lo, out_gain_hi, out_eff_mean, out_eff_lo, out_eff_hi

    def predict_for_simulation(
        self,
        parameters: AntennaParameters,
        model_name: str = "default",
        confidence: float = 0.95,
    ) -> SurrogatePrediction:
        """
        Full prediction for simulation result: use s11_min, gain, and efficiency
        models so gain/efficiency are not wrongly filled with s11 (dB) values.
        If gain or efficiency model is missing, uses sensible fallbacks.
        """
        start_time = time.time()

        # S11 curve from s11_min model (required)
        key_s11 = f"{model_name}_s11_min"
        if key_s11 not in self.models:
            self.load_model(model_name, "s11_min")
        s11_pred = self.models[key_s11].predict_full(
            parameters, frequency_range=parameters.frequency_range
        )

        # Gain from gain model if available, else fallback (dBi)
        gain_mean, gain_lo, gain_hi = 6.0, 5.0, 7.0
        gain_path = self.model_dir / f"{model_name}_gain.pkl"
        if gain_path.exists():
            key_g = f"{model_name}_gain"
            if key_g not in self.models:
                self.load_model(model_name, "gain")
            gain_mean, gain_lo, gain_hi = self.models[key_g].predict(parameters, confidence=confidence)
            gain_mean = max(0.0, min(30.0, float(gain_mean)))

        # Efficiency from efficiency model if available, else fallback [0, 1]
        eff_mean, eff_lo, eff_hi = 0.85, 0.75, 0.95
        eff_path = self.model_dir / f"{model_name}_efficiency.pkl"
        if eff_path.exists():
            key_e = f"{model_name}_efficiency"
            if key_e not in self.models:
                self.load_model(model_name, "efficiency")
            eff_mean, eff_lo, eff_hi = self.models[key_e].predict(parameters, confidence=confidence)
            eff_mean = max(0.0, min(1.0, float(eff_mean)))
            eff_lo = max(0.0, min(1.0, float(eff_lo)))
            eff_hi = max(0.0, min(1.0, float(eff_hi)))

        # Optional: blend toward nearest OpenEMS training row so model and OpenEMS match better
        s11_data = s11_pred.s11
        s11_lower = s11_pred.s11_confidence_lower
        s11_upper = s11_pred.s11_confidence_upper
        if getattr(settings, "NN_BLEND_ENABLED", True):
            s11_data, s11_lower, s11_upper, gain_mean, gain_lo, gain_hi, eff_mean, eff_lo, eff_hi = (
                self._blend_with_nearest(
                    parameters, s11_pred, gain_mean, gain_lo, gain_hi, eff_mean, eff_lo, eff_hi,
                    key_s11,
                )
            )

        prediction = SurrogatePrediction(
            antenna_parameters=parameters,
            s11=s11_data,
            s11_confidence_lower=s11_lower,
            s11_confidence_upper=s11_upper,
            gain=float(gain_mean),
            gain_confidence_lower=float(gain_lo),
            gain_confidence_upper=float(gain_hi),
            efficiency=float(eff_mean),
            efficiency_confidence_lower=float(eff_lo),
            efficiency_confidence_upper=float(eff_hi),
            model_name=s11_pred.model_name,
            model_version=s11_pred.model_version,
            prediction_time=time.time() - start_time,
        )
        # Accuracy predictor from s11_min
        acc_key = f"{model_name}_s11_min"
        if acc_key not in self.accuracy_predictors:
            loaded = self.training_pipeline.load_accuracy_predictor(model_name, "s11_min")
            if loaded is not None:
                self.accuracy_predictors[acc_key] = loaded
        acc_predictor = self.accuracy_predictors.get(acc_key)
        threshold = getattr(settings, "EM_ACCURACY_THRESHOLD_MAE", 1.0)
        if acc_predictor is not None and acc_predictor.trained:
            prediction.predicted_mae = acc_predictor.predict_mae(parameters)
            prediction.recommend_em_run = (prediction.predicted_mae or 0) > threshold
        else:
            prediction.recommend_em_run = None
            prediction.predicted_mae = None
        return prediction

    def predict_batch(
        self,
        parameters_list: list[AntennaParameters],
        model_name: str = "default",
        metric: str = "s11_min"
    ) -> list[SurrogatePrediction]:
        """
        Batch prediction.
        
        Args:
            parameters_list: List of input parameters
            model_name: Model name
            metric: Target metric
            
        Returns:
            List of predictions
        """
        return [
            self.predict(p, model_name, metric)
            for p in parameters_list
        ]



















