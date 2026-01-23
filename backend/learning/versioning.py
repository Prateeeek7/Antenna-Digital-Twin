"""Model versioning and lineage tracking."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from backend.core.config import settings


class ModelVersioning:
    """Manage model versions and lineage."""
    
    def __init__(self, version_dir: Optional[Path] = None):
        """
        Initialize versioning.
        
        Args:
            version_dir: Directory for version metadata
        """
        self.version_dir = version_dir or settings.ML_MODEL_DIR / "versions"
        self.version_dir.mkdir(parents=True, exist_ok=True)
    
    def create_version(
        self,
        model_name: str,
        parent_version: Optional[str] = None,
        training_data_ids: Optional[List[str]] = None,
        measurement_ids: Optional[List[str]] = None,
        update_type: str = "initial"
    ) -> str:
        """
        Create new model version.
        
        Args:
            model_name: Model name
            parent_version: Parent version ID
            training_data_ids: Training data IDs
            measurement_ids: Measurement IDs used
            update_type: Update type ("initial", "retrain", "bayesian_update")
            
        Returns:
            Version ID
        """
        version_id = f"{model_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        version_data = {
            "version_id": version_id,
            "model_name": model_name,
            "parent_version": parent_version,
            "training_data_ids": training_data_ids or [],
            "measurement_ids": measurement_ids or [],
            "update_type": update_type,
            "created_at": datetime.utcnow().isoformat()
        }
        
        version_file = self.version_dir / f"{version_id}.json"
        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        
        return version_id
    
    def get_lineage(self, version_id: str) -> List[Dict[str, Any]]:
        """
        Get model lineage.
        
        Args:
            version_id: Version ID
            
        Returns:
            List of version data in lineage
        """
        lineage = []
        current_version = version_id
        
        while current_version:
            version_file = self.version_dir / f"{current_version}.json"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                lineage.append(version_data)
                current_version = version_data.get("parent_version")
            else:
                break
        
        return lineage



















