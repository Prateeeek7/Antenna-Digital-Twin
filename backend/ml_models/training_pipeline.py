"""Automated training pipeline for surrogate models."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import pickle
from datetime import datetime

from backend.core.models.schemas import AntennaParameters, EMSimulationResult
from backend.ml_models.ensemble import EnsemblePredictor
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
            model_path = self.model_dir / f"{model_name}_{metric}.pkl"
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



















