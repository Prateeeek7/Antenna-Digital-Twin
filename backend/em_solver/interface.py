"""Abstract interface for EM solvers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from backend.core.models.schemas import AntennaParameters, EMSimulationResult
from backend.core.exceptions import EMSolverError


class EMSolverInterface(ABC):
    """Abstract base class for EM solver adapters."""
    
    def __init__(self, solver_path: Optional[Path] = None, **kwargs):
        """
        Initialize EM solver.
        
        Args:
            solver_path: Path to solver executable or installation
            **kwargs: Solver-specific configuration
        """
        self.solver_path = solver_path
        self.config = kwargs
        self._validate_setup()
    
    @abstractmethod
    def _validate_setup(self) -> None:
        """Validate that solver is properly configured and available."""
        pass
    
    @abstractmethod
    def get_solver_name(self) -> str:
        """Get solver name."""
        pass
    
    @abstractmethod
    def get_solver_version(self) -> str:
        """Get solver version."""
        pass
    
    @abstractmethod
    def create_simulation_file(
        self,
        parameters: AntennaParameters,
        output_dir: Path,
        **kwargs: Any,
    ) -> Path:
        """
        Create solver-specific simulation file.

        Args:
            parameters: Antenna parameters
            output_dir: Directory for simulation files
            **kwargs: Solver-specific options (e.g. fast for OpenEMS)

        Returns:
            Path to created simulation file
        """
        pass
    
    @abstractmethod
    def run_simulation(
        self,
        simulation_file: Path,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run EM simulation.
        
        Args:
            simulation_file: Path to simulation file
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with simulation metadata (status, execution_time, etc.)
            
        Raises:
            EMSolverError: If simulation fails
        """
        pass
    
    @abstractmethod
    def parse_results(
        self,
        simulation_file: Path,
        results_dir: Path,
        parameters: Optional[AntennaParameters] = None
    ) -> EMSimulationResult:
        """
        Parse solver results into standardized format.
        
        Args:
            simulation_file: Path to original simulation file
            results_dir: Directory containing solver output files
            
        Returns:
            EMSimulationResult with parsed data
            
        Raises:
            EMSolverError: If parsing fails
        """
        pass
    
    def simulate(
        self,
        parameters: AntennaParameters,
        output_dir: Path,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> EMSimulationResult:
        """
        Complete simulation workflow: create file, run, parse results.

        Args:
            parameters: Antenna parameters
            output_dir: Directory for simulation files and results
            timeout: Maximum execution time in seconds
            **kwargs: Solver-specific options (e.g. fast=True for OpenEMS)

        Returns:
            EMSimulationResult with complete simulation data
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save parameters to metadata file for later reconstruction
        import json
        params_file = output_dir / "parameters.json"
        with open(params_file, 'w') as f:
            json.dump(parameters.model_dump(), f, indent=2)

        # Create simulation file (pass through e.g. fast for OpenEMS)
        sim_file = self.create_simulation_file(parameters, output_dir, **kwargs)

        # Run simulation
        sim_metadata = self.run_simulation(sim_file, timeout)
        
        # Parse results (pass parameters for reconstruction)
        result = self.parse_results(sim_file, output_dir, parameters)
        
        # Add execution metadata
        result.simulation_time = sim_metadata.get("execution_time", 0.0)
        result.metadata.update(sim_metadata)
        
        return result

