"""EM solver adapter using custom_patch_v1 (openEMS Python) for accurate single/batch simulation."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from backend.em_solver.interface import EMSolverInterface
from backend.core.models.schemas import AntennaParameters, EMSimulationResult, S11Data
from backend.core.exceptions import EMSolverError, SolverNotAvailableError
from backend.core.config import settings


def _project_root() -> Path:
    """Project root (parent of backend)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def _params_to_custom_patch(parameters: AntennaParameters) -> Dict[str, float]:
    """Convert AntennaParameters to custom_patch_v1 params (mm, Feed_X/Y_mm offset from center)."""
    g = parameters.geometry
    s = parameters.substrate
    length_mm = g.length * 1000.0
    width_mm = g.width * 1000.0
    height_mm = g.height * 1000.0
    feed_x_mm = (g.feed_x * 1000.0) - (length_mm / 2.0)  # absolute (m) -> offset from center (mm)
    feed_y_mm = (g.feed_y * 1000.0) - (width_mm / 2.0)   # same for y so Model and OpenEMS match
    return {
        "Length": length_mm,
        "Width": width_mm,
        "Height": height_mm,
        "Feed_X_mm": feed_x_mm,
        "Feed_Y_mm": feed_y_mm,
        "substrate_epsR": s.relative_permittivity,
        "substrate_loss_tan": s.loss_tangent,
    }


class CustomPatchAdapter(EMSolverInterface):
    """Adapter for custom_patch_v1 (openEMS Python) – accurate single/batch EM simulation."""

    def __init__(self, solver_path: Optional[Path] = None, **kwargs):
        self._python = kwargs.get("python_path", sys.executable)
        super().__init__(solver_path, **kwargs)

    def _validate_setup(self) -> None:
        # Check we can run Python and project has custom_patch
        root = _project_root()
        custom_module = root / "backend" / "em_solver" / "custom_patch" / "custom_patch_v1.py"
        if not custom_module.exists():
            raise SolverNotAvailableError(
                f"custom_patch_v1 not found at {custom_module}. "
                "Ensure backend/em_solver/custom_patch/ is present."
            )
        try:
            root_str = root.as_posix()
            r = subprocess.run(
                [self._python, "-c", "import sys; sys.path.insert(0, r'" + root_str + "'); from backend.em_solver.custom_patch.custom_patch_v1 import run_simulation; print('ok')"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=root_str,
            )
            if r.returncode != 0 or "ok" not in (r.stdout or ""):
                stderr = (r.stderr or r.stdout or "").strip()
                if "CSXCAD" in stderr or "openEMS" in stderr or "ModuleNotFoundError" in stderr:
                    raise SolverNotAvailableError(
                        "OpenEMS Python bindings not installed (missing CSXCAD/openEMS). "
                        "Install: build CSXCAD and openEMS Python from openEMS-Project source "
                        "(see https://docs.openems.de/python/install.html), or use solver "
                        "'openems_octave' if you have the OpenEMS binary and Octave. "
                        f"Details: {stderr[:500]}"
                    )
                raise SolverNotAvailableError(
                    "custom_patch_v1 import failed. Install openEMS Python (CSXCAD, openEMS). "
                    f"stderr: {stderr[:500]}"
                )
        except subprocess.TimeoutExpired:
            raise SolverNotAvailableError("custom_patch_v1 import timed out.")
        except Exception as e:
            raise SolverNotAvailableError(f"custom_patch_v1 check failed: {e}")

    def get_solver_name(self) -> str:
        return "CustomPatch (openEMS Python)"

    def get_solver_version(self) -> str:
        return "1.0"

    def create_simulation_file(
        self,
        parameters: AntennaParameters,
        output_dir: Path,
        **kwargs: Any,
    ) -> Path:
        """Write runner script that calls custom_patch_v1.run_simulation and writes results.json."""
        root = _project_root()
        output_dir = Path(output_dir)
        runner = output_dir / "run_custom_patch.py"
        params = _params_to_custom_patch(parameters)
        f_min, f_max = parameters.frequency_range
        params["f_min"] = float(f_min)
        params["f_max"] = float(f_max)
        root_str = root.as_posix()
        out_dir_str = output_dir.as_posix()
        fast = kwargs.get("fast", False)

        script = f'''# -*- coding: utf-8 -*-
# Generated runner: run custom_patch_v1 and write results.json
import sys
import json
from pathlib import Path

root = Path(r"{root_str}")
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

try:
    from backend.em_solver.custom_patch.custom_patch_v1 import run_simulation
except Exception as e:
    print("Import error:", e, file=sys.stderr)
    sys.exit(1)

out_dir = Path(r"{out_dir_str}")
sim_path = str(out_dir)
params = {json.dumps(params)}
fast_mode = {str(fast)}

try:
    res = run_simulation(params, 0, sim_path, verbose=False, show_plots=False, fast=fast_mode)
except Exception as e:
    print("Simulation error:", e, file=sys.stderr)
    sys.exit(2)

out = res["output"]
# Gain_dBi from OpenEMS (same formula as dataset generator: 10*log10(efficiency*Dmax))
gain = out.get("Gain_dBi")
if gain is None or (isinstance(gain, float) and (gain != gain or gain <= -1e6)):
    gain = 6.6  # fallback only when OpenEMS returns invalid (nan/-inf)
eff = float(out.get("Efficiency", 0.85))

# Full S11 curve from OpenEMS (Hz and dB) when available
freq_list = out.get("frequency")
s11_mag_list = out.get("s11_magnitude")
if freq_list is not None and s11_mag_list is not None and len(freq_list) == len(s11_mag_list):
    frequency = [float(x) for x in freq_list]
    s11_magnitude = [float(x) for x in s11_mag_list]
else:
    f_res_ghz = out.get("Resonance_Frequency_GHz", 2.45)
    f_res = f_res_ghz * 1e9
    s11_min = out.get("S11_min_dB", -15.0)
    f_min, f_max = {f_min}, {f_max}
    frequency = [f_min, f_res, f_max]
    s11_magnitude = [s11_min + 5, s11_min, s11_min + 5]

results = {{
    "frequency": frequency,
    "s11_magnitude": s11_magnitude,
    "s11_phase": None,
    "gain": float(gain),
    "efficiency": eff,
    "resonance_frequency": float(out.get("Resonance_Frequency_GHz", 2.45)) * 1e9,
}}
with open(out_dir / "results.json", "w") as f:
    json.dump(results, f, indent=2)
'''
        runner.write_text(script, encoding="utf-8")
        return runner

    def run_simulation(
        self,
        simulation_file: Path,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute the runner script with Python. Run from project root so openEMS can find libs."""
        simulation_file = Path(simulation_file).resolve()
        output_dir = simulation_file.parent
        root = _project_root()
        timeout = timeout or settings.EM_SOLVER_TIMEOUT
        start = datetime.utcnow()
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([str(root), env.get("PYTHONPATH", "")])
        openems_bin = root / "backend" / "opt" / "openEMS" / "bin"
        if openems_bin.is_dir():
            env["PATH"] = os.pathsep.join([str(openems_bin), env.get("PATH", "")])
        try:
            r = subprocess.run(
                [self._python, "-u", str(simulation_file)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            elapsed = (datetime.utcnow() - start).total_seconds()
            if r.returncode != 0:
                out_snip = (r.stdout or "")[-1500:]
                err_snip = (r.stderr or "")[-1500:]
                raise EMSolverError(
                    f"OpenEMS simulation failed (exit {r.returncode}). "
                    f"stdout: {out_snip!r} stderr: {err_snip!r}"
                )
            results_file = output_dir / "results.json"
            if not results_file.exists():
                out_snip = (r.stdout or "")[-1500:]
                err_snip = (r.stderr or "")[-1500:]
                raise EMSolverError(
                    "OpenEMS run finished but results.json was not created. "
                    f"stdout: {out_snip!r} stderr: {err_snip!r}"
                )
            return {
                "status": "completed",
                "execution_time": elapsed,
                "solver": self.get_solver_name(),
                "stdout": r.stdout or "",
                "stderr": r.stderr or "",
            }
        except subprocess.TimeoutExpired as e:
            raise EMSolverError(
                f"OpenEMS simulation exceeded timeout of {timeout} seconds. "
                "Try enabling fast mode in the UI or increase EM_SOLVER_TIMEOUT."
            ) from e

    def parse_results(
        self,
        simulation_file: Path,
        results_dir: Path,
        parameters: Optional[AntennaParameters] = None,
    ) -> EMSimulationResult:
        """Load results.json and return EMSimulationResult."""
        if parameters is None:
            params_file = results_dir / "parameters.json"
            if not params_file.exists():
                raise EMSolverError("parameters not provided and parameters.json not found")
            with open(params_file) as f:
                data = json.load(f)
            parameters = AntennaParameters(**data)

        results_file = results_dir / "results.json"
        if not results_file.exists():
            raise EMSolverError("results.json not found")

        with open(results_file) as f:
            data = json.load(f)

        freq = data.get("frequency", [2.0e9, 2.45e9, 3.0e9])
        s11_mag = data.get("s11_magnitude", [-10.0, -15.0, -10.0])
        s11_phase = data.get("s11_phase")
        gain = float(data.get("gain", 6.6))
        efficiency = float(data.get("efficiency", 0.85))
        res_freq = data.get("resonance_frequency")

        metadata = {"source": "custom_patch_v1"}
        if res_freq is not None:
            metadata["resonance_frequency"] = float(res_freq)

        return EMSimulationResult(
            simulation_id=str(uuid.uuid4()),
            antenna_parameters=parameters,
            s11=S11Data(frequency=freq, s11_magnitude=s11_mag, s11_phase=s11_phase),
            gain=gain,
            efficiency=efficiency,
            solver_name=self.get_solver_name(),
            solver_version=self.get_solver_version(),
            simulation_time=0.0,
            timestamp=datetime.utcnow(),
            metadata=metadata,
        )
