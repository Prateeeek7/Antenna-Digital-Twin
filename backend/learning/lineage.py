"""Data lineage tracking."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from backend.core.config import settings


class LineageTracker:
    """Track data lineage from EM → ROM → Surrogate → Prediction."""
    
    def __init__(self, lineage_dir: Optional[Path] = None):
        """
        Initialize lineage tracker.
        
        Args:
            lineage_dir: Directory for lineage data
        """
        self.lineage_dir = lineage_dir or settings.ML_MODEL_DIR / "lineage"
        self.lineage_dir.mkdir(parents=True, exist_ok=True)
    
    def track_prediction(
        self,
        prediction_id: str,
        em_simulation_ids: List[str],
        measurement_ids: List[str],
        model_version: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        Track prediction lineage.
        
        Args:
            prediction_id: Prediction ID
            em_simulation_ids: EM simulation IDs used
            measurement_ids: Measurement IDs used
            model_version: Model version
            parameters: Input parameters
        """
        lineage_data = {
            "prediction_id": prediction_id,
            "em_simulation_ids": em_simulation_ids,
            "measurement_ids": measurement_ids,
            "model_version": model_version,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        lineage_file = self.lineage_dir / f"{prediction_id}.json"
        with open(lineage_file, 'w') as f:
            json.dump(lineage_data, f, indent=2)

