"""VNA (Vector Network Analyzer) data parser."""

import csv
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

from backend.core.models.schemas import S11Data
from backend.core.exceptions import MeasurementError


class VNAParser:
    """Parser for VNA measurement files."""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse VNA measurement file.
        
        Supports:
        - Touchstone (.s1p, .s2p, .snp)
        - CSV with frequency, S11 columns
        - Text files with S-parameter data
        
        Args:
            file_path: Path to VNA file
            
        Returns:
            Dictionary with parsed data
        """
        suffix = file_path.suffix.lower()
        
        if suffix in [".s1p", ".s2p", ".snp"]:
            return self._parse_touchstone(file_path)
        elif suffix == ".csv":
            return self._parse_csv(file_path)
        else:
            return self._parse_text(file_path)
    
    def _parse_touchstone(self, file_path: Path) -> Dict[str, Any]:
        """Parse Touchstone format (.s1p, .s2p, etc.)."""
        frequency = []
        s11_real = []
        s11_imag = []
        
        with open(file_path, 'r') as f:
            # Skip header lines (start with ! or #)
            for line in f:
                line = line.strip()
                if not line or line.startswith('!'):
                    continue
                if line.startswith('#'):
                    # Parse format line
                    # Format: # [freq_unit] [S] [param] [format] [R] [n]
                    continue
                
                # Parse data line
                parts = line.split()
                if len(parts) >= 3:
                    freq = float(parts[0])
                    real = float(parts[1])
                    imag = float(parts[2])
                    
                    frequency.append(freq)
                    s11_real.append(real)
                    s11_imag.append(imag)
        
        # Convert to magnitude and phase
        s11_complex = np.array(s11_real) + 1j * np.array(s11_imag)
        s11_magnitude = 20 * np.log10(np.abs(s11_complex))
        s11_phase = np.angle(s11_complex) * 180 / np.pi
        
        return {
            "s11": S11Data(
                frequency=list(frequency),
                s11_magnitude=list(s11_magnitude),
                s11_phase=list(s11_phase)
            ),
            "timestamp": datetime.utcnow()
        }
    
    def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV format."""
        frequency = []
        s11_magnitude = []
        s11_phase = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try various column name variations
                freq_key = None
                mag_key = None
                phase_key = None
                
                for key in row.keys():
                    key_lower = key.lower()
                    if 'freq' in key_lower:
                        freq_key = key
                    elif 's11' in key_lower or 'magnitude' in key_lower or 'mag' in key_lower:
                        mag_key = key
                    elif 'phase' in key_lower:
                        phase_key = key
                
                if freq_key and mag_key:
                    try:
                        freq = float(row[freq_key])
                        mag = float(row[mag_key])
                        phase = float(row[phase_key]) if phase_key and row[phase_key] else None
                        
                        frequency.append(freq)
                        s11_magnitude.append(mag)
                        if phase is not None:
                            s11_phase.append(phase)
                    except (ValueError, KeyError):
                        continue
        
        return {
            "s11": S11Data(
                frequency=frequency,
                s11_magnitude=s11_magnitude,
                s11_phase=s11_phase if s11_phase else None
            ),
            "timestamp": datetime.utcnow()
        }
    
    def _parse_text(self, file_path: Path) -> Dict[str, Any]:
        """Parse generic text format."""
        frequency = []
        s11_magnitude = []
        s11_phase = []
        
        with open(file_path, 'r') as f:
            for line in f:
                # Try to extract numbers
                numbers = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', line)
                if len(numbers) >= 2:
                    try:
                        freq = float(numbers[0])
                        mag = float(numbers[1])
                        phase = float(numbers[2]) if len(numbers) >= 3 else None
                        
                        frequency.append(freq)
                        s11_magnitude.append(mag)
                        if phase is not None:
                            s11_phase.append(phase)
                    except ValueError:
                        continue
        
        if not frequency:
            raise MeasurementError(f"Could not parse data from {file_path}")
        
        return {
            "s11": S11Data(
                frequency=frequency,
                s11_magnitude=s11_magnitude,
                s11_phase=s11_phase if s11_phase else None
            ),
            "timestamp": datetime.utcnow()
        }



















