"""Automated training pipeline for surrogate models."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import pickle
from datetime import datetime

from backend.core.models.schemas import AntennaParameters, EMSimulationResult, SurrogatePrediction


def _apply_gpytorch_pickle_shims() -> None:
    """Patch gpytorch modules so pickles from older versions can be loaded."""
    _noop = lambda: None
    try:
        import gpytorch.means.constant_mean as m
        if not hasattr(m, "_ensure_updated_strategy_flag_set"):
            m._ensure_updated_strategy_flag_set = _noop
        if hasattr(m, "ConstantMean") and not hasattr(m.ConstantMean, "_ensure_updated_strategy_flag_set"):
            m.ConstantMean._ensure_updated_strategy_flag_set = _noop
        # Some gpytorch versions expose only raw_constant; old pickles expect .constant
        if hasattr(m, "ConstantMean"):
            cls = m.ConstantMean
            if not hasattr(cls, "constant"):
                if hasattr(cls, "_constant_param") and hasattr(cls, "_constant_closure"):
                    constant_prop = property(
                        lambda self: cls._constant_param(self, self),
                        lambda self, v: cls._constant_closure(self, self, v),
                    )
                else:
                    import torch as _torch

                    def _get_constant(self):
                        r = getattr(self, "raw_constant", None)
                        if r is not None:
                            return r
                        # ConstantMean.forward() uses self.constant.unsqueeze(-1).expand(...); never return None
                        return _torch.tensor(0.0)

                    def _set_constant(self, value):
                        if hasattr(self, "raw_constant"):
                            import torch
                            if not isinstance(value, torch.Tensor):
                                value = torch.as_tensor(value)
                            self.raw_constant.data = value

                    constant_prop = property(_get_constant, _set_constant)
                cls.constant = constant_prop
    except Exception:
        pass
    try:
        import gpytorch.means as means_mod
        if not hasattr(means_mod, "_ensure_updated_strategy_flag_set"):
            means_mod._ensure_updated_strategy_flag_set = _noop
    except Exception:
        pass
from backend.ml_models.ensemble import EnsemblePredictor
from backend.ml_models.accuracy_predictor import AccuracyPredictor
from backend.core.config import settings
from backend.core.exceptions import ModelError


class TrainingPipeline:
    """Automated training pipeline for surrogate models."""
    
    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize training pipeline.
        
        Args:
            model_dir: Directory for saving models
        """
        self.model_dir = model_dir or settings.ML_MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _model_subdir(self, model_name: str) -> Path:
        """Return canonical subdirectory for a model family."""
        name = (model_name or "default").lower()
        if name.startswith("dipole"):
            sub = "dipole"
        elif name.startswith("default") or name.startswith("microstrip"):
            sub = "microstrip"
        else:
            sub = "custom"
        out = self.model_dir / sub
        out.mkdir(parents=True, exist_ok=True)
        return out

    def _resolve_model_path(self, model_name: str, metric: str) -> Path:
        """
        Resolve model path with backward-compatible fallback.
        Preferred: backend/models/<family>/<model_name>_<metric>.pkl
        Legacy:    backend/models/<model_name>_<metric>.pkl
        """
        preferred = self._model_subdir(model_name) / f"{model_name}_{metric}.pkl"
        if preferred.exists():
            return preferred
        legacy = self.model_dir / f"{model_name}_{metric}.pkl"
        return legacy
    
    def train_ensemble(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        model_name: str = "default",
        target_metrics: List[str] = ["s11_min", "gain", "efficiency"]
    ) -> Dict[str, EnsemblePredictor]:
        """
        Train ensemble models for multiple metrics.
        
        Args:
            parameters: Training parameters
            results: Training results
            model_name: Model name for saving
            target_metrics: List of metrics to train
            
        Returns:
            Dictionary mapping metric names to trained models
        """
        models = {}
        
        for metric in target_metrics:
            # Create and train ensemble
            ensemble = EnsemblePredictor()
            ensemble.fit(parameters, results, target=metric)
            
            # Save model
            model_path = self._model_subdir(model_name) / f"{model_name}_{metric}.pkl"
            self._save_model(ensemble, model_path, metric)
            
            models[metric] = ensemble
        
        return models
    
    def _save_model(
        self,
        model: EnsemblePredictor,
        model_path: Path,
        metric: str
    ) -> None:
        """Save trained model."""
        model_data = {
            "model": model,
            "metric": metric,
            "trained_at": datetime.utcnow().isoformat(),
            "model_type": "ensemble"
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(
        self,
        model_path: Path
    ) -> EnsemblePredictor:
        """Load trained model."""
        if not model_path.exists():
            raise ModelError(f"Model not found: {model_path}")
        
        # Compatibility shim: older gpytorch pickles reference attributes that were
        # moved/renamed in newer versions (e.g. _ensure_updated_strategy_flag_set).
        _apply_gpytorch_pickle_shims()
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        return model_data["model"]
    
    def evaluate_model(
        self,
        model: EnsemblePredictor,
        test_parameters: List[AntennaParameters],
        test_results: List[EMSimulationResult],
        metric: str = "s11_min"
    ) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            model: Trained model
            test_parameters: Test parameters
            test_results: Test results
            metric: Metric to evaluate
            
        Returns:
            Dictionary with evaluation metrics
        """
        predictions = []
        true_values = []
        
        for params, result in zip(test_parameters, test_results):
            pred_mean, _, _ = model.predict(params)
            predictions.append(pred_mean)
            
            # Extract true value
            if metric == "s11_min":
                if result.s11 and result.s11.s11_magnitude:
                    true_values.append(min(result.s11.s11_magnitude))
                else:
                    true_values.append(0.0)
            elif metric == "gain":
                true_values.append(result.gain)
            elif metric == "efficiency":
                true_values.append(result.efficiency)
        
        # Calculate metrics
        import numpy as np
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        mse = mean_squared_error(true_values, predictions)
        mae = mean_absolute_error(true_values, predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(true_values, predictions)
        
        return {
            "mse": float(mse),
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2)
        }

    def train_accuracy_predictor(
        self,
        parameters: List[AntennaParameters],
        em_results: List[EMSimulationResult],
        model_name: str = "default",
        metric: str = "s11_min",
        device: Optional[str] = None,
    ) -> AccuracyPredictor:
        """
        Train the accuracy predictor (second model) from EM vs surrogate errors.

        Requires the surrogate model for model_name/metric to already be trained.
        Uses it to get predictions, then trains accuracy predictor on (params, |EM - pred|).

        Returns:
            Trained AccuracyPredictor (also saved to model_dir).
        """
        model_path = self._resolve_model_path(model_name, metric)
        if not model_path.exists():
            raise ModelError(f"Surrogate model not found: {model_path}. Train surrogate first.")
        ensemble = self.load_model(model_path)
        surrogate_predictions = [
            ensemble.predict_full(p, frequency_range=p.frequency_range)
            for p in parameters
        ]
        device = device or settings.ML_DEVICE
        predictor = AccuracyPredictor(device=device)
        predictor.fit(
            parameters=parameters,
            em_results=em_results,
            surrogate_predictions=surrogate_predictions,
            metric=metric,
        )
        acc_path = model_path.with_name(f"{model_name}_{metric}_accuracy.pkl")
        with open(acc_path, "wb") as f:
            pickle.dump(
                {
                    "predictor": predictor,
                    "metric": metric,
                    "trained_at": datetime.utcnow().isoformat(),
                    "model_type": "accuracy_predictor",
                },
                f,
            )
        return predictor

    def load_accuracy_predictor(
        self,
        model_name: str = "default",
        metric: str = "s11_min",
    ) -> Optional[AccuracyPredictor]:
        """Load accuracy predictor if it exists."""
        model_path = self._resolve_model_path(model_name, metric)
        acc_path = model_path.with_name(f"{model_name}_{metric}_accuracy.pkl")
        if not acc_path.exists():
            return None
        _apply_gpytorch_pickle_shims()
        with open(acc_path, "rb") as f:
            data = pickle.load(f)
        return data.get("predictor")






