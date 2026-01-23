"""Geometry deformer combining all mechanical effects."""

from typing import Optional
from backend.core.models.schemas import AntennaParameters, AntennaGeometry
from backend.mechanical.bending_model import BendingModel
from backend.mechanical.stress_model import StressModel
from backend.mechanical.thermal_expansion import ThermalExpansionModel


class GeometryDeformer:
    """Combine all mechanical deformations."""
    
    def __init__(self):
        """Initialize deformer."""
        self.bending_model = BendingModel()
        self.stress_model = StressModel()
        self.thermal_model = ThermalExpansionModel()
    
    def deform_geometry(
        self,
        parameters: AntennaParameters,
        bending_radius: Optional[float] = None,
        bending_axis: str = "x",
        stress_x: float = 0.0,
        stress_y: float = 0.0,
        temperature: Optional[float] = None
    ) -> AntennaParameters:
        """
        Apply all mechanical deformations.
        
        Args:
            parameters: Original parameters
            bending_radius: Bending radius (m)
            bending_axis: Bending axis
            stress_x: Stress in x-direction (Pa)
            stress_y: Stress in y-direction (Pa)
            temperature: Temperature (Celsius)
            
        Returns:
            Deformed AntennaParameters
        """
        geom = parameters.geometry
        
        # Apply bending
        if bending_radius is not None:
            geom = self.bending_model.calculate_bending_deformation(
                parameters, bending_radius, bending_axis
            )
            # Update parameters for next step
            parameters = AntennaParameters(
                geometry=geom,
                substrate=parameters.substrate,
                feed_type=parameters.feed_type,
                frequency_band=parameters.frequency_band,
                frequency_range=parameters.frequency_range
            )
        
        # Apply stress
        if stress_x != 0.0 or stress_y != 0.0:
            geom = self.stress_model.calculate_stress_deformation(
                parameters, stress_x, stress_y
            )
            parameters = AntennaParameters(
                geometry=geom,
                substrate=parameters.substrate,
                feed_type=parameters.feed_type,
                frequency_band=parameters.frequency_band,
                frequency_range=parameters.frequency_range
            )
        
        # Apply thermal expansion
        if temperature is not None:
            geom = self.thermal_model.calculate_thermal_deformation(
                parameters, temperature
            )
            parameters = AntennaParameters(
                geometry=geom,
                substrate=parameters.substrate,
                feed_type=parameters.feed_type,
                frequency_band=parameters.frequency_band,
                frequency_range=parameters.frequency_range
            )
        
        return parameters



















