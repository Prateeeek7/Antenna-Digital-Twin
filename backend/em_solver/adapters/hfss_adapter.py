"""ANSYS HFSS solver adapter (placeholder for future implementation)."""

from pathlib import Path
from typing import Dict, Any, Optional

from backend.em_solver.interface import EMSolverInterface
from backend.core.models.schemas import AntennaParameters, EMSimulationResult
from backend.core.exceptions import SolverNotAvailableError


class HFSSAdapter(EMSolverInterface):
    """ANSYS HFSS adapter (not yet implemented)."""
    
    def __init__(self, solver_path: Optional[Path] = None, **kwargs):
        """Initialize HFSS adapter."""
        super().__init__(solver_path, **kwargs)
    
    def _validate_setup(self) -> None:
        """Validate HFSS installation."""
        raise SolverNotAvailableError(
            "HFSS adapter not yet implemented. Use OpenEMS for now."
        )
    
    def get_solver_name(self) -> str:
        """Get solver name."""
        return "ANSYS HFSS"
    
    def get_solver_version(self) -> str:
        """Get solver version."""
        return "unknown"
    
    def create_simulation_file(
        self,
        parameters: AntennaParameters,
        output_dir: Path
    ) -> Path:
        """Create HFSS simulation file."""
        raise NotImplementedError("HFSS adapter not yet implemented")
    
    def run_simulation(
        self,
        simulation_file: Path,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run HFSS simulation."""
        raise NotImplementedError("HFSS adapter not yet implemented")
    
    def parse_results(
        self,
        simulation_file: Path,
        results_dir: Path,
        parameters: Optional[AntennaParameters] = None
    ) -> EMSimulationResult:
        """Parse HFSS results."""
        raise NotImplementedError("HFSS adapter not yet implemented")

