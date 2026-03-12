"""Database service for EM simulation persistence."""

from typing import Optional
from pathlib import Path
from datetime import datetime
import json
from sqlalchemy.orm import Session

from backend.database.models import EMSimulation, AntennaInstance
from backend.core.models.schemas import EMSimulationResult, S11Data
from backend.core.config import settings
from backend.core.exceptions import EMSolverError


class EMSimulationDatabaseService:
    """Service for persisting EM simulations to database."""
    
    def __init__(self):
        """Initialize database service (use absolute path for background tasks)."""
        self.simulations_dir = Path(settings.EM_SOLVER_RESULTS_DIR).resolve()
        self.simulations_dir.mkdir(parents=True, exist_ok=True)
    
    def save_simulation(
        self,
        result: EMSimulationResult,
        db: Session,
        antenna_instance_id: Optional[str] = None
    ) -> EMSimulation:
        """
        Save EM simulation to database.
        
        Args:
            result: EMSimulationResult to save
            db: Database session
            antenna_instance_id: Antenna instance ID (optional, will try to find or create)
            
        Returns:
            Database EMSimulation record
        """
        # Find or create antenna instance
        antenna_instance = None
        if antenna_instance_id:
            antenna_instance = db.query(AntennaInstance).filter(
                AntennaInstance.instance_id == antenna_instance_id
            ).first()
        
        # If not found, try to find by parameters
        if not antenna_instance:
            antenna_instance = self._find_or_create_instance(result.antenna_parameters, db)
        
        # Save S11 data to file
        s11_data_path = self._save_s11_data(result.simulation_id, result.s11)
        
        # Save radiation pattern if available
        radiation_pattern_path = None
        if result.radiation_pattern:
            radiation_pattern_path = self._save_radiation_pattern(
                result.simulation_id,
                result.radiation_pattern
            )
        
        # Create database record
        db_simulation = EMSimulation(
            simulation_id=result.simulation_id,
            antenna_instance_id=antenna_instance.id,
            solver_name=result.solver_name,
            solver_version=result.solver_version,
            s11_data_path=str(s11_data_path),
            gain=result.gain,
            efficiency=result.efficiency,
            radiation_pattern_path=str(radiation_pattern_path) if radiation_pattern_path else None,
            simulation_time=result.simulation_time,
            status="completed",
            completed_at=datetime.utcnow(),
            sim_metadata=result.metadata,
        )
        
        db.add(db_simulation)
        db.commit()
        db.refresh(db_simulation)
        
        return db_simulation
    
    def _find_or_create_instance(self, parameters, db: Session) -> AntennaInstance:
        """Find existing instance or create new one based on parameters."""
        # Try to find existing instance with matching parameters
        instance = db.query(AntennaInstance).filter(
            AntennaInstance.geometry_length == parameters.geometry.length,
            AntennaInstance.geometry_width == parameters.geometry.width,
            AntennaInstance.substrate_permittivity == parameters.substrate.relative_permittivity,
            AntennaInstance.frequency_band == parameters.frequency_band.value,
        ).first()
        
        if instance:
            return instance
        
        # Create new instance
        import uuid
        instance_id = f"ANT-{uuid.uuid4().hex[:8].upper()}"
        
        from backend.api.v1.antenna_instance import antenna_params_to_db
        db_data = antenna_params_to_db(instance_id, parameters)
        instance = AntennaInstance(**db_data)
        
        db.add(instance)
        db.commit()
        db.refresh(instance)
        
        return instance
    
    def _save_s11_data(self, simulation_id: str, s11: S11Data) -> Path:
        """Save S11 data to JSON file."""
        file_path = self.simulations_dir / f"{simulation_id}_s11.json"
        
        data = {
            "frequency": s11.frequency,
            "s11_magnitude": s11.s11_magnitude,
            "s11_phase": s11.s11_phase,
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return file_path
    
    def _save_radiation_pattern(self, simulation_id: str, pattern) -> Path:
        """Save radiation pattern to JSON file."""
        file_path = self.simulations_dir / f"{simulation_id}_pattern.json"
        
        data = {
            "theta": pattern.theta,
            "phi": pattern.phi,
            "gain": pattern.gain,
            "e_plane": pattern.e_plane,
            "h_plane": pattern.h_plane,
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return file_path
