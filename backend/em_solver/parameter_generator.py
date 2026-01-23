"""Parameter generator for Design of Experiments (DoE)."""

import numpy as np
from typing import List, Dict, Any
from backend.core.models.schemas import AntennaParameters, AntennaGeometry, SubstrateProperties, SubstrateType, FeedType, FrequencyBand


class ParameterGenerator:
    """Generate parameter sets for Design of Experiments."""
    
    def __init__(
        self,
        frequency_band: FrequencyBand = FrequencyBand.BAND_24GHZ,
        substrate_type: SubstrateType = SubstrateType.FR4
    ):
        """
        Initialize parameter generator.
        
        Args:
            frequency_band: Target frequency band
            substrate_type: Substrate material type
        """
        self.frequency_band = frequency_band
        self.substrate_type = substrate_type
        
        # Set parameter bounds based on frequency band
        if frequency_band == FrequencyBand.BAND_24GHZ:
            self.f0 = 2.4e9
            self.f_range = (2.0e9, 3.0e9)
            # Typical dimensions for 2.4 GHz patch (in meters)
            self.length_bounds = (0.025, 0.035)  # ~λ/4
            self.width_bounds = (0.030, 0.045)
        elif frequency_band == FrequencyBand.BAND_35GHZ:
            self.f0 = 3.5e9
            self.f_range = (3.0e9, 4.0e9)
            self.length_bounds = (0.018, 0.025)
            self.width_bounds = (0.022, 0.032)
        else:
            raise ValueError(f"Unsupported frequency band: {frequency_band}")
        
        # Common bounds
        self.height_bounds = (0.0008, 0.0032)  # 0.8mm to 3.2mm
        self.feed_x_bounds = (0.0, 1.0)  # Fraction of length
        self.feed_y_bounds = (0.0, 1.0)  # Fraction of width
    
    def generate_latin_hypercube(
        self,
        n_samples: int,
        seed: int = None
    ) -> List[AntennaParameters]:
        """
        Generate parameter sets using Latin Hypercube Sampling (LHS).
        
        Args:
            n_samples: Number of samples to generate
            seed: Random seed for reproducibility
            
        Returns:
            List of AntennaParameters
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Generate LHS samples in [0, 1]^5
        from scipy.stats import qmc
        sampler = qmc.LatinHypercube(d=5, seed=seed)
        samples = sampler.random(n=n_samples)
        
        parameters = []
        for sample in samples:
            # Map [0, 1] to parameter ranges
            length = np.interp(sample[0], [0, 1], self.length_bounds)
            width = np.interp(sample[1], [0, 1], self.width_bounds)
            height = np.interp(sample[2], [0, 1], self.height_bounds)
            feed_x_frac = sample[3]  # Fraction of length
            feed_y_frac = sample[4]  # Fraction of width
            
            # Calculate actual feed positions
            feed_x = length * feed_x_frac * 0.5  # Center feed in inset
            feed_y = width * feed_y_frac * 0.5
            
            # Ensure feed is within bounds
            feed_x = np.clip(feed_x, 0.001, length * 0.4)
            feed_y = np.clip(feed_y, 0.001, width * 0.4)
            
            # Get substrate properties
            if self.substrate_type == SubstrateType.FR4:
                er = 4.4
                tan_d = 0.02
            elif self.substrate_type == SubstrateType.ROGERS_RO4003:
                er = 3.38
                tan_d = 0.0027
            elif self.substrate_type == SubstrateType.ROGERS_RO4350:
                er = 3.48
                tan_d = 0.0037
            else:
                er = 4.4
                tan_d = 0.02
            
            params = AntennaParameters(
                geometry=AntennaGeometry(
                    length=float(length),
                    width=float(width),
                    height=float(height),
                    feed_x=float(feed_x),
                    feed_y=float(feed_y)
                ),
                substrate=SubstrateProperties(
                    substrate_type=self.substrate_type,
                    relative_permittivity=er,
                    loss_tangent=tan_d,
                    thickness=float(height)
                ),
                feed_type=FeedType.INSET,
                frequency_band=self.frequency_band,
                frequency_range=self.f_range
            )
            parameters.append(params)
        
        return parameters
    
    def generate_sobol_sequence(
        self,
        n_samples: int,
        seed: int = None
    ) -> List[AntennaParameters]:
        """
        Generate parameter sets using Sobol sequence (quasi-random).
        
        Args:
            n_samples: Number of samples to generate
            seed: Random seed for reproducibility
            
        Returns:
            List of AntennaParameters
        """
        from scipy.stats import qmc
        sampler = qmc.Sobol(d=5, seed=seed, scramble=True)
        samples = sampler.random(n=n_samples)
        
        parameters = []
        for sample in samples:
            length = np.interp(sample[0], [0, 1], self.length_bounds)
            width = np.interp(sample[1], [0, 1], self.width_bounds)
            height = np.interp(sample[2], [0, 1], self.height_bounds)
            feed_x_frac = sample[3]
            feed_y_frac = sample[4]
            
            feed_x = length * feed_x_frac * 0.5
            feed_y = width * feed_y_frac * 0.5
            feed_x = np.clip(feed_x, 0.001, length * 0.4)
            feed_y = np.clip(feed_y, 0.001, width * 0.4)
            
            if self.substrate_type == SubstrateType.FR4:
                er = 4.4
                tan_d = 0.02
            else:
                er = 4.4
                tan_d = 0.02
            
            params = AntennaParameters(
                geometry=AntennaGeometry(
                    length=float(length),
                    width=float(width),
                    height=float(height),
                    feed_x=float(feed_x),
                    feed_y=float(feed_y)
                ),
                substrate=SubstrateProperties(
                    substrate_type=self.substrate_type,
                    relative_permittivity=er,
                    loss_tangent=tan_d,
                    thickness=float(height)
                ),
                feed_type=FeedType.INSET,
                frequency_band=self.frequency_band,
                frequency_range=self.f_range
            )
            parameters.append(params)
        
        return parameters
    
    def generate_grid(
        self,
        n_per_dimension: int = 5
    ) -> List[AntennaParameters]:
        """
        Generate parameter sets using regular grid (full factorial).
        
        Args:
            n_per_dimension: Number of points per dimension
            
        Returns:
            List of AntennaParameters
        """
        # Create grid for length, width, height
        length_vals = np.linspace(*self.length_bounds, n_per_dimension)
        width_vals = np.linspace(*self.width_bounds, n_per_dimension)
        height_vals = np.linspace(*self.height_bounds, 3)  # Fewer height values
        
        parameters = []
        for length in length_vals:
            for width in width_vals:
                for height in height_vals:
                    # Center feed
                    feed_x = length * 0.25
                    feed_y = width * 0.25
                    
                    if self.substrate_type == SubstrateType.FR4:
                        er = 4.4
                        tan_d = 0.02
                    else:
                        er = 4.4
                        tan_d = 0.02
                    
                    params = AntennaParameters(
                        geometry=AntennaGeometry(
                            length=float(length),
                            width=float(width),
                            height=float(height),
                            feed_x=float(feed_x),
                            feed_y=float(feed_y)
                        ),
                        substrate=SubstrateProperties(
                            substrate_type=self.substrate_type,
                            relative_permittivity=er,
                            loss_tangent=tan_d,
                            thickness=float(height)
                        ),
                        feed_type=FeedType.INSET,
                        frequency_band=self.frequency_band,
                        frequency_range=self.f_range
                    )
                    parameters.append(params)
        
        return parameters



















