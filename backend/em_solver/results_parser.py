"""Solver-agnostic result extraction and standardization."""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.core.models.schemas import (
    EMSimulationResult,
    S11Data,
    RadiationPattern,
    AntennaParameters
)
from backend.core.exceptions import EMSolverError


class ResultsParser:
    """Parse and standardize EM simulation results."""
    
    @staticmethod
    def parse_s11_from_file(file_path: Path) -> S11Data:
        """
        Parse S11 data from various file formats.
        
        Args:
            file_path: Path to S11 data file (CSV, JSON, MAT, etc.)
            
        Returns:
            S11Data object
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".json":
            return ResultsParser._parse_s11_json(file_path)
        elif suffix == ".csv":
            return ResultsParser._parse_s11_csv(file_path)
        elif suffix == ".mat":
            return ResultsParser._parse_s11_mat(file_path)
        else:
            raise EMSolverError(f"Unsupported file format: {suffix}")
    
    @staticmethod
    def _parse_s11_json(file_path: Path) -> S11Data:
        """Parse S11 from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return S11Data(
            frequency=data.get("frequency", []),
            s11_magnitude=data.get("s11_magnitude", []),
            s11_phase=data.get("s11_phase")
        )
    
    @staticmethod
    def _parse_s11_csv(file_path: Path) -> S11Data:
        """Parse S11 from CSV file."""
        import csv
        
        frequency = []
        s11_magnitude = []
        s11_phase = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'frequency' in row:
                    frequency.append(float(row['frequency']))
                if 's11_magnitude' in row or 's11_db' in row:
                    key = 's11_magnitude' if 's11_magnitude' in row else 's11_db'
                    s11_magnitude.append(float(row[key]))
                if 's11_phase' in row:
                    s11_phase.append(float(row['s11_phase']))
        
        return S11Data(
            frequency=frequency,
            s11_magnitude=s11_magnitude,
            s11_phase=s11_phase if s11_phase else None
        )
    
    @staticmethod
    def _parse_s11_mat(file_path: Path) -> S11Data:
        """Parse S11 from MATLAB .mat file."""
        try:
            import scipy.io
            mat_data = scipy.io.loadmat(
                str(file_path),
                struct_as_record=False,
                squeeze_me=True
            )
            
            # Try common variable names
            freq = mat_data.get('freq', mat_data.get('frequency', []))
            s11 = mat_data.get('s11', mat_data.get('s11_db', []))
            phase = mat_data.get('s11_phase', None)
            
            return S11Data(
                frequency=list(freq) if hasattr(freq, '__iter__') else [freq],
                s11_magnitude=list(s11) if hasattr(s11, '__iter__') else [s11],
                s11_phase=list(phase) if phase is not None and hasattr(phase, '__iter__') else None
            )
        except ImportError:
            raise EMSolverError("scipy.io required for .mat file parsing")
        except Exception as e:
            raise EMSolverError(f"Failed to parse .mat file: {str(e)}")
    
    @staticmethod
    def parse_radiation_pattern_from_file(file_path: Path) -> RadiationPattern:
        """
        Parse radiation pattern from file.
        
        Args:
            file_path: Path to pattern data file
            
        Returns:
            RadiationPattern object
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".json":
            return ResultsParser._parse_pattern_json(file_path)
        elif suffix == ".csv":
            return ResultsParser._parse_pattern_csv(file_path)
        else:
            raise EMSolverError(f"Unsupported pattern file format: {suffix}")
    
    @staticmethod
    def _parse_pattern_json(file_path: Path) -> RadiationPattern:
        """Parse radiation pattern from JSON."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return RadiationPattern(
            theta=data.get("theta", []),
            phi=data.get("phi", []),
            gain=data.get("gain", []),
            e_plane=data.get("e_plane"),
            h_plane=data.get("h_plane")
        )
    
    @staticmethod
    def _parse_pattern_csv(file_path: Path) -> RadiationPattern:
        """Parse radiation pattern from CSV."""
        import csv
        import numpy as np
        
        theta_vals = set()
        phi_vals = set()
        gain_data = {}
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                theta = float(row.get('theta', 0))
                phi = float(row.get('phi', 0))
                gain = float(row.get('gain', 0))
                
                theta_vals.add(theta)
                phi_vals.add(phi)
                gain_data[(theta, phi)] = gain
        
        # Convert to sorted lists and matrix
        theta_list = sorted(theta_vals)
        phi_list = sorted(phi_vals)
        
        gain_matrix = [
            [gain_data.get((t, p), 0.0) for p in phi_list]
            for t in theta_list
        ]
        
        # Extract E-plane (phi=0) and H-plane (theta=90)
        e_plane = [gain_data.get((t, 0), 0.0) for t in theta_list] if 0 in phi_vals else None
        h_plane = [gain_data.get((90, p), 0.0) for p in phi_list] if 90 in theta_vals else None
        
        return RadiationPattern(
            theta=theta_list,
            phi=phi_list,
            gain=gain_matrix,
            e_plane=e_plane,
            h_plane=h_plane
        )
    
    @staticmethod
    def save_results_to_json(
        result: EMSimulationResult,
        output_path: Path
    ) -> None:
        """Save simulation result to JSON file."""
        data = {
            "simulation_id": result.simulation_id,
            "antenna_parameters": result.antenna_parameters.model_dump(),
            "s11": {
                "frequency": result.s11.frequency,
                "s11_magnitude": result.s11.s11_magnitude,
                "s11_phase": result.s11.s11_phase
            },
            "gain": result.gain,
            "efficiency": result.efficiency,
            "solver_name": result.solver_name,
            "solver_version": result.solver_version,
            "simulation_time": result.simulation_time,
            "timestamp": result.timestamp.isoformat(),
            "metadata": result.metadata
        }
        
        if result.radiation_pattern:
            data["radiation_pattern"] = {
                "theta": result.radiation_pattern.theta,
                "phi": result.radiation_pattern.phi,
                "gain": result.radiation_pattern.gain,
                "e_plane": result.radiation_pattern.e_plane,
                "h_plane": result.radiation_pattern.h_plane
            }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)



















