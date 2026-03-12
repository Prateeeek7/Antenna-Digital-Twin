"""Factory for creating EM solver instances."""

from pathlib import Path
from typing import Optional
from backend.em_solver.interface import EMSolverInterface
from backend.em_solver.adapters.custom_patch_adapter import CustomPatchAdapter
from backend.em_solver.adapters.openems_adapter import OpenEMSAdapter
from backend.em_solver.adapters.hfss_adapter import HFSSAdapter
from backend.em_solver.adapters.cst_adapter import CSTAdapter
from backend.core.exceptions import SolverNotAvailableError

# Try to import Meep adapter (optional dependency)
try:
    from backend.em_solver.adapters.meep_adapter import MeepAdapter
    MEEP_AVAILABLE = True
except ImportError:
    MEEP_AVAILABLE = False
    MeepAdapter = None


class EMSolverFactory:
    """Factory for creating EM solver adapters."""

    # Default "openems" uses custom_patch_v1 (openEMS Python) for accurate EM data.
    # "openems_octave" keeps the legacy Octave/OpenEMS adapter.
    _solvers = {
        "openems": CustomPatchAdapter,
        "openems_octave": OpenEMSAdapter,
        "custom_patch": CustomPatchAdapter,
        "hfss": HFSSAdapter,
        "cst": CSTAdapter,
    }

    # Add Meep if available
    if MEEP_AVAILABLE and MeepAdapter:
        _solvers["meep"] = MeepAdapter
    
    @classmethod
    def create_solver(
        cls,
        solver_name: str,
        solver_path: Optional[Path] = None,
        **kwargs
    ) -> EMSolverInterface:
        """
        Create EM solver instance.
        
        Args:
            solver_name: Name of solver ("openems", "hfss", "cst")
            solver_path: Optional path to solver executable
            **kwargs: Solver-specific configuration
            
        Returns:
            EMSolverInterface instance
            
        Raises:
            SolverNotAvailableError: If solver not supported or not available
        """
        solver_name_lower = solver_name.lower()
        
        if solver_name_lower not in cls._solvers:
            available = ", ".join(cls._solvers.keys())
            raise SolverNotAvailableError(
                f"Unknown solver: {solver_name}. Available: {available}"
            )
        
        solver_class = cls._solvers[solver_name_lower]
        
        try:
            return solver_class(solver_path=solver_path, **kwargs)
        except SolverNotAvailableError as e:
            # For "openems": if Python bindings (CustomPatch) fail, try Octave/OpenEMS
            if solver_name_lower == "openems" and solver_class is CustomPatchAdapter:
                try:
                    return OpenEMSAdapter(solver_path=solver_path, **kwargs)
                except Exception:
                    pass
            raise SolverNotAvailableError(
                f"Failed to create {solver_name} solver: {str(e)}"
            )
        except Exception as e:
            raise SolverNotAvailableError(
                f"Failed to create {solver_name} solver: {str(e)}"
            )
    
    @classmethod
    def list_available_solvers(cls) -> list[str]:
        """List available solver names."""
        return list(cls._solvers.keys())
    
    @classmethod
    def register_solver(
        cls,
        name: str,
        solver_class: type[EMSolverInterface]
    ) -> None:
        """
        Register a custom solver adapter.
        
        Args:
            name: Solver name
            solver_class: Solver adapter class
        """
        cls._solvers[name.lower()] = solver_class









