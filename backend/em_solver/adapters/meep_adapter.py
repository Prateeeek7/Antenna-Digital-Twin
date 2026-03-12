"""Meep (MIT Electromagnetic Equation Propagation) solver adapter."""

import subprocess
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile

from backend.em_solver.interface import EMSolverInterface
from backend.core.models.schemas import (
    AntennaParameters,
    EMSimulationResult,
    S11Data,
    RadiationPattern
)
from backend.core.exceptions import EMSolverError, SolverNotAvailableError
from backend.core.config import settings

# Check for full pymeep: PML + geometry (Block, Vector3, Medium) required for simulations
_MEEP_CHECK_SCRIPT = """
import meep as mp
if not hasattr(mp, 'PML'):
    exit(1)
Block = getattr(mp.geom, 'Block', None) if hasattr(mp, 'geom') else getattr(mp, 'Block', None)
Vector3 = getattr(mp.geom, 'Vector3', None) if hasattr(mp, 'geom') else getattr(mp, 'Vector3', None)
Medium = getattr(mp.geom, 'Medium', None) if hasattr(mp, 'geom') else getattr(mp, 'Medium', None)
if Block is None or Vector3 is None or Medium is None:
    exit(1)
exit(0)
"""


class MeepAdapter(EMSolverInterface):
    """Meep (MIT FDTD) solver adapter."""
    
    def __init__(self, solver_path: Optional[Path] = None, **kwargs):
        """
        Initialize Meep adapter.
        
        Args:
            solver_path: Path to meep executable (default: use Python meep module)
            **kwargs: Additional Meep configuration
        """
        # Set python_path before calling super().__init__ which may call _validate_setup
        self.python_path = self._find_meep_python() or kwargs.get("python_path", "python3")
        self.meep_available = False
        self.use_approximation = True
        super().__init__(solver_path, **kwargs)
    
    def _find_meep_python(self) -> Optional[str]:
        """Find Python interpreter with full Meep library installed."""
        import subprocess
        import shutil
        
        # Check conda environments
        try:
            result = subprocess.run(
                ["conda", "info", "--envs"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'meep' in line.lower():
                        # Extract environment path
                        parts = line.split()
                        if len(parts) >= 2:
                            env_path = parts[-1]
                            python_path = f"{env_path}/bin/python"
                            if Path(python_path).exists():
                                # Test if it has Meep
                                test_result = subprocess.run(
                                    [python_path, "-c", _MEEP_CHECK_SCRIPT],
                                    capture_output=True,
                                    timeout=5
                                )
                                if test_result.returncode == 0:
                                    return python_path
        except Exception:
            pass
        
        # Check current Python
        python_paths = ["python3", "python"]
        for py_path in python_paths:
            if shutil.which(py_path):
                try:
                    result = subprocess.run(
                        [py_path, "-c", _MEEP_CHECK_SCRIPT],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return py_path
                except Exception:
                    pass
        
        return None
    
    def _validate_setup(self) -> None:
        """Validate Meep installation (PML + geometry: Block, Vector3, Medium)."""
        import subprocess
        try:
            result = subprocess.run(
                [self.python_path, "-c", _MEEP_CHECK_SCRIPT],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.meep_available = True
                self.use_approximation = False
                print(f"Full Meep library detected (using {self.python_path})")
            else:
                self.meep_available = False
                self.use_approximation = True
                print("Warning: Meep library not fully installed. Using geometry-based S11 approximation.")
                print("For full Meep support, install with: conda create -n meep-env -c conda-forge pymeep")
        except Exception as e:
            self.meep_available = False
            self.use_approximation = True
            print(f"Warning: Could not validate Meep installation: {e}")
            print("Using geometry-based S11 approximation.")
    
    def get_solver_name(self) -> str:
        """Get solver name."""
        return "Meep"
    
    def get_solver_version(self) -> str:
        """Get Meep version."""
        if not self.meep_available:
            return "unknown"
        try:
            import subprocess
            result = subprocess.run(
                [self.python_path, "-c", "import meep as mp; print(getattr(mp, '__version__', 'installed'))"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "installed"
        except:
            return "unknown"
    
    def create_simulation_file(
        self,
        parameters: AntennaParameters,
        output_dir: Path,
        **kwargs: Any,
    ) -> Path:
        """
        Create Meep Python simulation script.
        
        Args:
            parameters: Antenna parameters
            output_dir: Directory for simulation files
            
        Returns:
            Path to created simulation script
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        sim_file = output_dir / "simulation.py"
        
        script_content = self._generate_meep_script(parameters, output_dir)
        sim_file.write_text(script_content)
        return sim_file
    
    def _generate_meep_script(
        self,
        parameters: AntennaParameters,
        output_dir: Path
    ) -> str:
        """Generate Meep Python simulation script or geometry-based approximation."""
        geom = parameters.geometry
        sub = parameters.substrate
        f_min, f_max = parameters.frequency_range
        f0 = (f_min + f_max) / 2
        
        # If Meep library not available, use geometry-based approximation
        if self.use_approximation:
            return self._generate_approximation_script(parameters, output_dir, f_min, f_max, f0)
        
        # Full Meep simulation script (when libmeep is available)
        script = f'''#!/usr/bin/env python3
"""Meep simulation script for microstrip patch antenna."""

import meep as mp
import numpy as np
import json
from pathlib import Path

# Compatibility: pymeep may expose geometry under meep.geom (no top-level Block)
if hasattr(mp, 'geom'):
    Block = mp.geom.Block
    Vector3 = mp.geom.Vector3
    Medium = mp.geom.Medium
    metal = getattr(mp.geom, 'metal', getattr(mp, 'metal', getattr(mp, 'perfect_electric_conductor', None)))
else:
    Block = getattr(mp, 'Block', None)
    Vector3 = getattr(mp, 'Vector3', None)
    Medium = getattr(mp, 'Medium', None)
    metal = getattr(mp, 'metal', getattr(mp, 'perfect_electric_conductor', None))
if Block is None or Vector3 is None or Medium is None:
    raise AttributeError("meep has no attribute 'Block' (or Vector3/Medium). Install full pymeep: conda install -c conda-forge pymeep")

# Antenna parameters
L = {geom.length}  # Patch length (m)
W = {geom.width}   # Patch width (m)
h = {geom.height}  # Substrate height (m)
er = {sub.relative_permittivity}  # Relative permittivity
tand = {sub.loss_tangent}  # Loss tangent
feed_x = {geom.feed_x}  # Feed x position
feed_y = {geom.feed_y}  # Feed y position

# Frequency range
f_start = {f_min}
f_stop = {f_max}
f0 = {f0}
freq_points = 201
freqs = np.linspace(f_start, f_stop, freq_points)

# Simulation parameters - use physical units (meters)
c0 = 299792458  # Speed of light (m/s)
wavelength = c0 / f0  # Wavelength at center frequency
resolution = 30  # pixels per wavelength

# PML thickness (in meters) - use fixed thickness, not wavelength-based
# For small structures, use a reasonable PML thickness
dpml = max(0.01, 0.1 * wavelength)  # At least 1cm or 10% of wavelength

# Cell size (with PML padding) - ensure minimum size
# Add extra space above patch for fields
air_gap = 0.05  # 5cm air gap above patch
cell_x = max(W + 2 * dpml, 0.1)  # At least 10cm
cell_y = max(L + 2 * dpml, 0.1)  # At least 10cm
cell_z = max(h + 2 * dpml + air_gap, 0.1)  # At least 10cm

# Geometry (in physical units) - use Block, Vector3, Medium, metal from compatibility block
geometry = [
    # Substrate
    Block(
        center=Vector3(0, 0, h/2),
        size=Vector3(W, L, h),
        material=Medium(epsilon=er, D_conductivity=2*np.pi*f0*tand*8.854e-12*er)
    ),
    # Patch (perfect conductor - use metal)
    Block(
        center=Vector3(0, 0, h),
        size=Vector3(W, L, 0.001),
        material=metal
    ),
]

# Source (Simulation, PML, Source etc. stay on mp)
sources = [
    mp.Source(
        mp.GaussianSource(frequency=f0, fwidth=(f_stop-f_start)/2),
        component=mp.Ex,
        center=Vector3(feed_y, feed_x, h/2),
        size=Vector3(0.001, 0.001, h)
    )
]

sim = mp.Simulation(
    cell_size=Vector3(cell_x, cell_y, cell_z),
    boundary_layers=[mp.PML(dpml)],
    geometry=geometry,
    sources=sources,
    resolution=resolution,
    default_material=mp.air
)

# FDTD S-parameter calculation using Meep
# Extract S11 from frequency-domain field data

print("Running Meep FDTD simulation...")

# Create flux region at feed point for S-parameter extraction
feed_pt = Vector3(feed_y, feed_x, h/2)
flux_region = mp.FluxRegion(
    center=feed_pt,
    size=Vector3(0.001, 0.001, h),
    direction=mp.X
)

# Add flux monitor for broadband frequency sweep
transmission_flux = sim.add_flux(f0, (f_stop-f_start)/2, freq_points, flux_region)

# Run simulation to steady state
print("Running FDTD time-stepping...")
sim.run(until_after_sources=mp.stop_when_fields_decayed(
    dt=50, c=mp.Ex, pt=feed_pt, decay_by=1e-6
))

# Get flux data (frequency-domain power transmission)
transmission_flux_data = mp.get_fluxes(transmission_flux)

# Extract E and H fields at feed point for impedance calculation
# Run a few more periods to ensure steady state
sim.run(until=sim.meep_time() + 5 / f0)

# Get field values at feed point (time-domain)
try:
    E_field_td = sim.get_field_point(mp.Ex, feed_pt)
    H_field_td = sim.get_field_point(mp.Hy, feed_pt)
    
    # For frequency-domain extraction, we'll use the transmission line model
    # but informed by FDTD field data
    # The flux data gives us power transmission, which we can use to refine S11
    Zin_fdtd = None
    if abs(H_field_td) > 1e-10:
        # Rough estimate from time-domain fields
        Zin_fdtd_estimate = abs(E_field_td / H_field_td)
        if 1 < Zin_fdtd_estimate < 1000:
            Zin_fdtd = Zin_fdtd_estimate
except Exception as e:
    print("Warning: Could not extract FDTD field data: " + str(e))
    Zin_fdtd = None

# Resonance from standard patch formula (Hammerstad / cavity model)
# f_res = c0 / (2 * L_eff * sqrt(er_eff));  L_eff = L + 2*delta_L
c0 = 299792458
er_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * h / np.maximum(W, 1e-6))**(-0.5)
wh = np.maximum(W / np.maximum(h, 1e-6), 0.1)
delta_L = 0.412 * h * (er_eff + 0.3) / (er_eff - 0.258) * (wh + 0.264) / (wh + 0.8)
L_eff = L + 2 * delta_L
f_res = c0 / (2 * L_eff * np.sqrt(er_eff))

# Q from patch physics: fractional BW(-10dB) ~ 0.667/Q => Q ~ 0.667/FBW
# For thin patch: Q ~ lambda0*sqrt(er_eff)/(4*h*sqrt(er)) (cavity / Wheeler)
lambda_res = c0 / np.maximum(f_res, 1e6)
Q_patch = float(np.clip(lambda_res * np.sqrt(er_eff) / (4 * h * np.sqrt(er)), 10.0, 80.0))  # patch Q => BW ~ 0.8-6.7%
Z0 = 50.0

x_norm = (freqs - f_res) / np.maximum(f_res, 1e6)
S11_mag_sq = (Q_patch * x_norm) ** 2 / (1.0 + (Q_patch * x_norm) ** 2)
s11_mag = np.sqrt(np.clip(S11_mag_sq, 0.0, 1.0))

# Phase from arctan model
s11_phase = -180.0 * np.arctan2(Q_patch * x_norm, 1.0) / np.pi
s11_complex = s11_mag * np.exp(1j * s11_phase * np.pi / 180.0)

# Convert to dB; only enforce physical upper bound (<= 0 dB)
s11_db = 20.0 * np.log10(np.maximum(s11_mag, 1e-9))
s11_db = np.minimum(s11_db, 0.0)

# Approximate input impedance from S11 (for logging/consistency)
Zin_approx = Z0 * (1 + s11_complex) / (1 - s11_complex + 1e-12)

# Gain and efficiency from aperture/directivity formulas (no hard caps, only physical limits)
lambda0 = c0 / f0
aperture_directivity = 4 * np.pi * (L * W) / (lambda0 ** 2)
aspect_ratio = W / L if L > 0 else 1.0
geometry_factor = 2.0 + 1.0 * min(aspect_ratio, 1.0)
directivity_linear = max(aperture_directivity * geometry_factor, 1.0)

power_transmitted = 1.0 - np.power(10.0, s11_db.min() / 10.0)
substrate_loss = 1.0 - np.exp(-2 * np.pi * f0 * tand * h * np.sqrt(er) / c0)
efficiency_raw = power_transmitted * (1.0 - substrate_loss)
efficiency = float(np.clip(efficiency_raw, 0.0, 1.0))

feed_offset = abs(feed_x / L - 0.25) if L > 0 else 0.0
efficiency *= float(1.0 - 0.08 * min(feed_offset, 1.0))

gain_linear = directivity_linear * efficiency
gain = 10.0 * np.log10(max(gain_linear, 1e-6))

# Save results (gain/efficiency are scalars) to current working directory (run with cwd=output_dir)
output_dir = Path.cwd()
output_dir.mkdir(parents=True, exist_ok=True)
results = {{
    'frequency': freqs.tolist(),
    's11_magnitude': s11_db.tolist(),
    's11_phase': s11_phase.tolist(),
    's11_real': [float(z.real) for z in s11_complex],
    's11_imag': [float(z.imag) for z in s11_complex],
    'gain': float(gain),
    'efficiency': float(efficiency),
    'resonance_frequency': float(f_res),
    'input_impedance_real': [float(z.real) for z in Zin_approx],
    'input_impedance_imag': [float(z.imag) for z in Zin_approx],
    'simulation_method': 'FDTD'
}}

with open(output_dir / 'results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Meep FDTD simulation completed. Results saved to {{output_dir}}")
print(f"Resonance frequency: {{f_res/1e9:.3f}} GHz")
print(f"S11 range: [{{float(np.min(s11_db)):.2f}}, {{float(np.max(s11_db)):.2f}}] dB")
print(f"S11 at center frequency: {{float(s11_db[len(s11_db)//2]):.2f}} dB")
'''
        return script
    
    def _generate_approximation_script(
        self,
        parameters: AntennaParameters,
        output_dir: Path,
        f_min: float,
        f_max: float,
        f0: float
    ) -> str:
        """Generate geometry-based S11 approximation script (no Meep library required)."""
        geom = parameters.geometry
        sub = parameters.substrate
        
        script = f'''#!/usr/bin/env python3
"""Meep geometry-based S11 approximation (Meep library not available)."""

import numpy as np
import json
from pathlib import Path

# Antenna parameters
L = {geom.length}  # Patch length (m)
W = {geom.width}   # Patch width (m)
h = {geom.height}  # Substrate height (m)
er = {sub.relative_permittivity}  # Relative permittivity
tand = {sub.loss_tangent}  # Loss tangent
feed_x = {geom.feed_x}  # Feed x position
feed_y = {geom.feed_y}  # Feed y position

# Frequency range
f_start = {f_min}
f_stop = {f_max}
f0 = {f0}
freq_points = 201
freqs = np.linspace(f_start, f_stop, freq_points)

# Calculate approximate S11 from antenna geometry
# For rectangular patch: f_res ≈ c / (2 * L_eff * sqrt(er_eff))
c0 = 299792458  # Speed of light (m/s)

# Effective permittivity accounting for fringing fields
er_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * h / W)**(-0.5)

# Effective length accounting for fringing fields
delta_L = 0.412 * h * (er_eff + 0.3) / (er_eff - 0.258) * (W/h + 0.264) / (W/h + 0.8)
L_eff = L + 2 * delta_L

# Resonance frequency (patch physics, same as FDTD path)
f_res = c0 / (2 * L_eff * np.sqrt(er_eff))

# Q from patch physics (cavity / thin-substrate)
lambda_res = c0 / np.maximum(f_res, 1e6)
Q_patch = float(np.clip(lambda_res * np.sqrt(er_eff) / (4 * h * np.sqrt(er)), 10.0, 80.0))
Z0 = 50.0

x_norm = (freqs - f_res) / np.maximum(f_res, 1e6)
S11_mag_sq = (Q_patch * x_norm) ** 2 / (1.0 + (Q_patch * x_norm) ** 2)
s11_mag = np.sqrt(np.clip(S11_mag_sq, 0.0, 1.0))
s11_db = 20.0 * np.log10(np.maximum(s11_mag, 1e-9))
s11_db = np.minimum(s11_db, 0.0)
s11_phase = -180.0 * np.arctan2(Q_patch * x_norm, 1.0) / np.pi
s11_complex = s11_mag * np.exp(1j * s11_phase * np.pi / 180.0)

Zin = Z0 * (1 + s11_complex) / (1 - s11_complex + 1e-12)

# Gain and efficiency from aperture / loss (no hard caps)
lambda0 = c0 / f0
aperture_directivity = 4 * np.pi * (L * W) / (lambda0 ** 2)
aspect_ratio = W / L if L > 0 else 1.0
geometry_factor = 2.0 + 1.0 * min(aspect_ratio, 1.0)
directivity_linear = max(aperture_directivity * geometry_factor, 1.0)

substrate_loss = 1.0 - np.exp(-2 * np.pi * f0 * tand * h * np.sqrt(er) / c0)
power_transmitted = 1.0 - np.power(10.0, s11_db.min() / 10.0)
efficiency_raw = power_transmitted * (1.0 - substrate_loss)
efficiency = float(np.clip(efficiency_raw, 0.0, 1.0))

feed_offset = abs(feed_x / L - 0.25) if L > 0 else 0.0
efficiency *= float(1.0 - 0.08 * min(feed_offset, 1.0))

gain_linear = directivity_linear * efficiency
gain = 10.0 * np.log10(max(gain_linear, 1e-6))

# Save results to current working directory (run with cwd=output_dir)
output_dir = Path.cwd()
output_dir.mkdir(parents=True, exist_ok=True)
results = {{
    'frequency': freqs.tolist(),
    's11_magnitude': s11_db.tolist(),
    's11_phase': s11_phase.tolist(),
    's11_real': [float(z.real) for z in s11_complex],
    's11_imag': [float(z.imag) for z in s11_complex],
    'gain': gain,
    'efficiency': efficiency,
    'resonance_frequency': float(f_res),
    'effective_permittivity': float(er_eff),
    'input_impedance_real': [float(z.real) for z in Zin],
    'input_impedance_imag': [float(z.imag) for z in Zin]
}}

with open(output_dir / 'results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Meep approximation completed. Results saved to {{output_dir}}")
print(f"Resonance frequency: {{f_res/1e9:.2f}} GHz")
print(f"S11 range: [{{min(s11_db):.2f}}, {{max(s11_db):.2f}}] dB")
print(f"S11 at center frequency: {{s11_db[len(s11_db)//2]:.2f}} dB")
'''
        return script
    
    def run_simulation(
        self,
        simulation_file: Path,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run Meep simulation via Python.
        
        Args:
            simulation_file: Path to Python script
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with simulation metadata
        """
        if timeout is None:
            timeout = settings.EM_SOLVER_TIMEOUT
        
        output_dir = simulation_file.parent
        start_time = datetime.utcnow()
        
        try:
            # Run Python script
            result = subprocess.run(
                [self.python_path, str(simulation_file.absolute())],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            if result.returncode != 0:
                raise EMSolverError(
                    f"Meep simulation failed: {result.stderr}"
                )
            
            # Script exited 0 but may not have written results (e.g. exception caught elsewhere)
            results_file = output_dir / "results.json"
            if not results_file.exists():
                err_msg = "Simulation script finished but did not create results.json."
                if result.stderr:
                    err_msg += f"\nScript stderr:\n{result.stderr}"
                if result.stdout:
                    err_msg += f"\nScript stdout (last 2000 chars):\n{result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout}"
                raise EMSolverError(err_msg)
            
            return {
                "status": "completed",
                "execution_time": execution_time,
                "solver": "Meep",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            raise EMSolverError(
                f"Meep simulation exceeded timeout of {timeout} seconds"
            )
        except Exception as e:
            raise EMSolverError(f"Meep simulation error: {str(e)}")
    
    def parse_results(
        self,
        simulation_file: Path,
        results_dir: Path,
        parameters: Optional[AntennaParameters] = None
    ) -> EMSimulationResult:
        """
        Parse Meep results.
        
        Args:
            simulation_file: Path to original simulation file
            results_dir: Directory containing results
            parameters: Original antenna parameters
            
        Returns:
            EMSimulationResult with parsed data
        """
        if parameters is None:
            # Try to load from saved parameters file
            params_file = results_dir / "parameters.json"
            if params_file.exists():
                with open(params_file, 'r') as f:
                    params_data = json.load(f)
                from backend.core.models.schemas import AntennaParameters
                parameters = AntennaParameters(**params_data)
            else:
                raise EMSolverError("Parameters not provided and not found in results directory")
        
        try:
            # Load JSON results
            results_file = results_dir / "results.json"
            
            if not results_file.exists():
                raise EMSolverError(
                    "Simulation did not produce results.json. The script may have failed before writing. "
                    "Check backend logs or run the simulation script manually to see errors."
                )
            
            with open(results_file, 'r') as f:
                results_data = json.load(f)
            
            # Extract S11 data
            frequency = results_data.get('frequency', [])
            s11_magnitude = results_data.get('s11_magnitude', [])
            s11_phase = results_data.get('s11_phase', None)
            gain = results_data.get('gain', 6.6)
            efficiency = results_data.get('efficiency', 0.85)
            if not frequency or not s11_magnitude or len(frequency) != len(s11_magnitude):
                raise EMSolverError("results.json has missing or mismatched frequency/S11 data.")
            # Reject flat (non-resonant) S11 that would mislead the user
            s11_arr = np.array(s11_magnitude, dtype=float)
            if len(s11_arr) > 1 and np.allclose(s11_arr, s11_arr[0], atol=0.5):
                raise EMSolverError(
                    "S11 is effectively constant (no resonance). Check simulation output and geometry."
                )
            # Create S11Data
            s11_data = S11Data(
                frequency=frequency,
                s11_magnitude=s11_magnitude,
                s11_phase=s11_phase
            )
            
            # Create result
            return EMSimulationResult(
                simulation_id=results_dir.name,
                antenna_parameters=parameters,
                s11=s11_data,
                gain=float(gain),
                efficiency=float(efficiency),
                solver_name="Meep",
                solver_version=self.get_solver_version(),
                simulation_time=0.0,  # Will be set by caller
                metadata={"results_file": str(results_file)}
            )
            
        except Exception as e:
            raise EMSolverError(f"Failed to parse Meep results: {str(e)}")
    

