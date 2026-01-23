"""Anechoic chamber measurement data parser."""

import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from backend.core.models.schemas import RadiationPattern
from backend.core.exceptions import MeasurementError


class ChamberParser:
    """Parser for anechoic chamber measurement files."""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse chamber measurement file.
        
        Supports:
        - JSON with pattern data
        - CSV with theta, phi, gain columns
        
        Args:
            file_path: Path to chamber file
            
        Returns:
            Dictionary with parsed data
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".json":
            return self._parse_json(file_path)
        elif suffix == ".csv":
            return self._parse_csv(file_path)
        else:
            raise MeasurementError(f"Unsupported chamber file format: {suffix}")
    
    def _parse_json(self, file_path: Path) -> Dict[str, Any]:
        """Parse JSON format."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        pattern = RadiationPattern(
            theta=data.get("theta", []),
            phi=data.get("phi", []),
            gain=data.get("gain", []),
            e_plane=data.get("e_plane"),
            h_plane=data.get("h_plane")
        )
        
        return {
            "radiation_pattern": pattern,
            "gain": data.get("peak_gain"),
            "efficiency": data.get("efficiency"),
            "timestamp": datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()))
        }
    
    def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV format."""
        theta_vals = set()
        phi_vals = set()
        gain_data = {}
        peak_gain = None
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    theta = float(row.get('theta', 0))
                    phi = float(row.get('phi', 0))
                    gain = float(row.get('gain', row.get('gain_dbi', 0)))
                    
                    theta_vals.add(theta)
                    phi_vals.add(phi)
                    gain_data[(theta, phi)] = gain
                    
                    if peak_gain is None or gain > peak_gain:
                        peak_gain = gain
                except (ValueError, KeyError):
                    continue
        
        if not theta_vals or not phi_vals:
            raise MeasurementError(f"No valid data found in {file_path}")
        
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
        
        pattern = RadiationPattern(
            theta=theta_list,
            phi=phi_list,
            gain=gain_matrix,
            e_plane=e_plane,
            h_plane=h_plane
        )
        
        return {
            "radiation_pattern": pattern,
            "gain": peak_gain,
            "timestamp": datetime.utcnow()
        }



















