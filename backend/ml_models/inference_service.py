"""Fast inference service for surrogate models."""

from typing import Optional, Dict, Any
from pathlib import Path

from backend.core.models.schemas import AntennaParameters, SurrogatePrediction
from backend.ml_models.ensemble import EnsemblePredictor
from backend.ml_models.training_pipeline import TrainingPipeline
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
        self.training_pipeline = TrainingPipeline(self.model_dir)
    
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



















