"""Main measurement ingestion service."""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from backend.core.models.schemas import MeasurementData, AntennaParameters, S11Data
from backend.measurement.parsers.vna_parser import VNAParser
from backend.measurement.parsers.chamber_parser import ChamberParser
from backend.measurement.validators import MeasurementValidator
from backend.measurement.alignment import ParameterAligner
from backend.core.exceptions import MeasurementError


class MeasurementIngestionService:
    """Service for ingesting measurement data."""
    
    def __init__(self):
        """Initialize ingestion service."""
        self.vna_parser = VNAParser()
        self.chamber_parser = ChamberParser()
        self.validator = MeasurementValidator()
        self.aligner = ParameterAligner()
    
    def ingest_from_file(
        self,
        file_path: Path,
        file_type: str = "auto",
        antenna_instance_id: Optional[str] = None,
        antenna_parameters: Optional[AntennaParameters] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MeasurementData:
        """
        Ingest measurement data from file.
        
        Args:
            file_path: Path to measurement file
            file_type: File type ("vna", "chamber", "auto" for detection)
            antenna_instance_id: Antenna instance identifier
            antenna_parameters: Known antenna parameters (for alignment)
            metadata: Additional metadata (temperature, humidity, etc.)
            
        Returns:
            MeasurementData object
            
        Raises:
            MeasurementError: If ingestion fails
        """
        if not file_path.exists():
            raise MeasurementError(f"File not found: {file_path}")
        
        # Auto-detect file type if needed
        if file_type == "auto":
            file_type = self._detect_file_type(file_path)
        
        # Parse file based on type
        if file_type == "vna":
            parsed_data = self.vna_parser.parse(file_path)
        elif file_type == "chamber":
            parsed_data = self.chamber_parser.parse(file_path)
        else:
            raise MeasurementError(f"Unsupported file type: {file_type}")
        
        # Validate data
        validation_result = self.validator.validate(parsed_data)
        if not validation_result["valid"]:
            raise MeasurementError(
                f"Validation failed: {validation_result.get('errors', [])}"
            )
        
        # Align parameters if provided
        if antenna_parameters is None and antenna_instance_id:
            # Try to load parameters from database
            # For now, use parsed parameters or defaults
            antenna_parameters = parsed_data.get("antenna_parameters")
        
        if antenna_parameters:
            aligned_params = self.aligner.align(
                parsed_data,
                antenna_parameters
            )
        else:
            aligned_params = parsed_data.get("antenna_parameters")
        
        # Extract metadata
        temp = metadata.get("temperature") if metadata else None
        humidity = metadata.get("humidity") if metadata else None
        operator = metadata.get("operator") if metadata else None
        equipment_id = metadata.get("equipment_id") if metadata else None
        
        # Create measurement data object
        measurement = MeasurementData(
            measurement_id=str(uuid.uuid4()),
            antenna_instance_id=antenna_instance_id or "unknown",
            antenna_parameters=aligned_params or self._create_default_parameters(),
            s11=parsed_data.get("s11"),
            gain=parsed_data.get("gain"),
            efficiency=parsed_data.get("efficiency"),
            radiation_pattern=parsed_data.get("radiation_pattern"),
            temperature=temp,
            humidity=humidity,
            operator=operator,
            equipment_id=equipment_id,
            timestamp=parsed_data.get("timestamp", datetime.utcnow()),
            quality_score=validation_result.get("quality_score", 1.0),
            metadata=metadata or {}
        )
        
        return measurement
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Auto-detect file type from extension and content."""
        suffix = file_path.suffix.lower()
        
        # Check extension
        if suffix in [".s1p", ".s2p", ".snp", ".csv", ".txt"]:
            # Try to detect VNA format
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline().strip()
                    if "frequency" in first_line.lower() or "s11" in first_line.lower():
                        return "vna"
            except Exception:
                pass
        
        # Default to VNA for common formats
        if suffix in [".s1p", ".s2p", ".snp"]:
            return "vna"
        
        # Try to read and detect
        try:
            with open(file_path, 'r') as f:
                content = f.read(1000).lower()
                if "chamber" in content or "pattern" in content:
                    return "chamber"
                if "s11" in content or "reflection" in content:
                    return "vna"
        except Exception:
            pass
        
        # Default
        return "vna"
    
    def _create_default_parameters(self) -> AntennaParameters:
        """Create default antenna parameters as fallback."""
        from backend.core.models.schemas import (
            AntennaGeometry,
            SubstrateProperties,
            SubstrateType,
            FeedType,
            FrequencyBand
        )
        
        return AntennaParameters(
            geometry=AntennaGeometry(
                length=0.03,
                width=0.04,
                height=0.0016,
                feed_x=0.015,
                feed_y=0.02
            ),
            substrate=SubstrateProperties(
                substrate_type=SubstrateType.FR4,
                relative_permittivity=4.4,
                loss_tangent=0.02,
                thickness=0.0016
            ),
            feed_type=FeedType.INSET,
            frequency_band=FrequencyBand.BAND_24GHZ,
            frequency_range=(2.0e9, 3.0e9)
        )



















