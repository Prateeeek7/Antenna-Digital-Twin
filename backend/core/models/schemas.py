"""Pydantic schemas for antenna parameters and data models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import numpy as np


class SubstrateType(str, Enum):
    """Supported substrate types."""
    FR4 = "FR4"
    ROGERS_RO4003 = "RO4003"
    ROGERS_RO4350 = "RO4350"
    CUSTOM = "CUSTOM"


class FeedType(str, Enum):
    """Antenna feed types."""
    INSET = "INSET"
    COAXIAL = "COAXIAL"
    MICROSTRIP = "MICROSTRIP"


class FrequencyBand(str, Enum):
    """Supported frequency bands."""
    BAND_24GHZ = "2.4GHz"
    BAND_35GHZ = "3.5GHz"


class AntennaGeometry(BaseModel):
    """Antenna geometry parameters."""
    length: float = Field(..., gt=0, description="Patch length (L) in meters")
    width: float = Field(..., gt=0, description="Patch width (W) in meters")
    height: float = Field(..., gt=0, description="Substrate height (h) in meters")
    feed_x: float = Field(..., ge=0, description="Feed x-position in meters")
    feed_y: float = Field(..., ge=0, description="Feed y-position in meters")
    
    @field_validator('feed_x', 'feed_y')
    @classmethod
    def validate_feed_position(cls, v, info):
        """Validate feed position is within patch bounds."""
        if hasattr(info, 'data'):
            if 'feed_x' in info.data and 'length' in info.data:
                if info.data['feed_x'] > info.data['length']:
                    raise ValueError("feed_x must be less than length")
            if 'feed_y' in info.data and 'width' in info.data:
                if info.data['feed_y'] > info.data['width']:
                    raise ValueError("feed_y must be less than width")
        return v


class SubstrateProperties(BaseModel):
    """Substrate material properties."""
    substrate_type: SubstrateType = Field(default=SubstrateType.FR4)
    relative_permittivity: float = Field(..., gt=1.0, description="εr")
    loss_tangent: float = Field(..., ge=0.0, description="tan δ")
    thickness: float = Field(..., gt=0, description="Substrate thickness in meters")
    
    @field_validator('substrate_type', mode='before')
    @classmethod
    def set_default_properties(cls, v, values):
        """Set default properties based on substrate type."""
        if isinstance(v, str):
            v = SubstrateType(v)
        
        # Set defaults for known substrates
        if v == SubstrateType.FR4:
            if 'relative_permittivity' not in values.data:
                values.data['relative_permittivity'] = 4.4
            if 'loss_tangent' not in values.data:
                values.data['loss_tangent'] = 0.02
        elif v == SubstrateType.ROGERS_RO4003:
            if 'relative_permittivity' not in values.data:
                values.data['relative_permittivity'] = 3.38
            if 'loss_tangent' not in values.data:
                values.data['loss_tangent'] = 0.0027
        elif v == SubstrateType.ROGERS_RO4350:
            if 'relative_permittivity' not in values.data:
                values.data['relative_permittivity'] = 3.48
            if 'loss_tangent' not in values.data:
                values.data['loss_tangent'] = 0.0037
        
        return v


class AntennaParameters(BaseModel):
    """Complete antenna parameter set."""
    geometry: AntennaGeometry
    substrate: SubstrateProperties
    feed_type: FeedType = FeedType.INSET
    frequency_band: FrequencyBand = FrequencyBand.BAND_24GHZ
    frequency_range: tuple[float, float] = Field(
        default=(2.0e9, 3.0e9),
        description="Frequency range in Hz (f_min, f_max)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "geometry": {
                    "length": 0.03,
                    "width": 0.04,
                    "height": 0.0016,
                    "feed_x": 0.015,
                    "feed_y": 0.02
                },
                "substrate": {
                    "substrate_type": "FR4",
                    "relative_permittivity": 4.4,
                    "loss_tangent": 0.02,
                    "thickness": 0.0016
                },
                "feed_type": "INSET",
                "frequency_band": "2.4GHz",
                "frequency_range": [2.0e9, 3.0e9]
            }
        }


class S11Data(BaseModel):
    """S11 (reflection coefficient) data."""
    frequency: List[float] = Field(..., description="Frequency array in Hz")
    s11_magnitude: List[float] = Field(..., description="|S11| in dB")
    s11_phase: Optional[List[float]] = Field(None, description="S11 phase in degrees")
    
    @field_validator('frequency', 's11_magnitude')
    @classmethod
    def validate_arrays_match(cls, v, info):
        """Validate frequency and magnitude arrays have same length."""
        if hasattr(info, 'data'):
            freq = info.data.get('frequency', [])
            mag = info.data.get('s11_magnitude', [])
            if freq and mag and len(freq) != len(mag):
                raise ValueError("frequency and s11_magnitude must have same length")
        return v


class RadiationPattern(BaseModel):
    """Radiation pattern data."""
    theta: List[float] = Field(..., description="Theta angles in degrees")
    phi: List[float] = Field(..., description="Phi angles in degrees")
    gain: List[List[float]] = Field(..., description="Gain matrix [theta][phi] in dBi")
    e_plane: Optional[List[float]] = Field(None, description="E-plane cut")
    h_plane: Optional[List[float]] = Field(None, description="H-plane cut")


class EMSimulationResult(BaseModel):
    """EM simulation results."""
    simulation_id: str
    antenna_parameters: AntennaParameters
    s11: S11Data
    gain: float = Field(..., description="Peak gain in dBi")
    efficiency: float = Field(..., ge=0.0, le=1.0, description="Radiation efficiency")
    radiation_pattern: Optional[RadiationPattern] = None
    solver_name: str
    solver_version: Optional[str] = None
    simulation_time: float = Field(..., description="Simulation time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MeasurementData(BaseModel):
    """Physical measurement data."""
    measurement_id: str
    antenna_instance_id: str
    antenna_parameters: AntennaParameters
    s11: Optional[S11Data] = None
    gain: Optional[float] = None
    efficiency: Optional[float] = None
    radiation_pattern: Optional[RadiationPattern] = None
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Humidity in %")
    operator: Optional[str] = None
    equipment_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data quality score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SurrogatePrediction(BaseModel):
    """Surrogate model prediction with uncertainty."""
    antenna_parameters: AntennaParameters
    s11: S11Data
    s11_confidence_lower: Optional[List[float]] = None
    s11_confidence_upper: Optional[List[float]] = None
    gain: float
    gain_confidence_lower: Optional[float] = None
    gain_confidence_upper: Optional[float] = None
    efficiency: float
    efficiency_confidence_lower: Optional[float] = None
    efficiency_confidence_upper: Optional[float] = None
    model_name: str
    model_version: str
    prediction_time: float = Field(..., description="Prediction time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)



















