# -*- coding: utf-8 -*-
"""
Simple center-fed dipole antenna simulation (single run).

- openEMS FDTD model in free space
- Outputs S11, resonance frequency, gain and efficiency
- Saves one JSON result file for quick validation
"""

import os
import json
import numpy as np
from pylab import *

from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0

# =============================================================================
# INPUT PARAMETERS - Edit for your design
# =============================================================================

# Geometry (mm)
Dipole_Length = 62.0     # total end-to-end length
Wire_Radius = 1.0        # cylindrical-equivalent radius (implemented as square wire half-size)
Feed_Gap = 1.0           # center gap between dipole arms

# Simulation
f0 = 2.4e9               # center frequency (Hz)
fc = 1.2e9               # excitation bandwidth (Hz)
feed_R = 50              # Ohm
n_freq_points = 401
SimBox = np.array([300, 300, 300])  # mm
post_proc_only = False

# Paths
results_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results'))
sim_path = os.path.join(results_dir, 'simple_dipole')
results_json = os.path.join(results_dir, 'Old_simple_dipole_results.json')


def build_and_run(show_plots=True):
    unit = 1e-3
    half_len = Dipole_Length / 2.0
    half_gap = Feed_Gap / 2.0

    # FDTD setup
    fdtd = openEMS(NrTS=40000, EndCriteria=1e-4)
    fdtd.SetGaussExcite(f0, fc)
    fdtd.SetBoundaryCond(['MUR', 'MUR', 'MUR', 'MUR', 'MUR', 'MUR'])

    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(unit)

    mesh_res = C0 / (f0 + fc) / unit / 25
    mesh.AddLine('x', [-SimBox[0] / 2, SimBox[0] / 2])
    mesh.AddLine('y', [-SimBox[1] / 2, SimBox[1] / 2])
    mesh.AddLine('z', [-SimBox[2] / 2, SimBox[2] / 2])

    # Dipole arms along z-axis (square wire approximation)
    dipole = csx.AddMetal('dipole')
    # Lower arm
    dipole.AddBox(
        priority=10,
        start=[-Wire_Radius, -Wire_Radius, -half_len],
        stop=[Wire_Radius, Wire_Radius, -half_gap],
    )
    # Upper arm
    dipole.AddBox(
        priority=10,
        start=[-Wire_Radius, -Wire_Radius, half_gap],
        stop=[Wire_Radius, Wire_Radius, half_len],
    )
    fdtd.AddEdges2Grid(dirs='xyz', properties=dipole, metal_edge_res=mesh_res / 2)

    # Lumped source at feed gap
    port = fdtd.AddLumpedPort(
        1,
        feed_R,
        [0.0, 0.0, -half_gap],
        [0.0, 0.0, half_gap],
        'z',
        1.0,
        priority=5,
        edges2grid='xy',
    )

    mesh.SmoothMeshLines('all', mesh_res, 1.4)
    nf2ff = fdtd.CreateNF2FFBox()

    if not post_proc_only:
        os.makedirs(sim_path, exist_ok=True)
        fdtd.Run(sim_path, cleanup=True)

    # Post-processing
    freq = np.linspace(max(0.5e9, f0 - fc), f0 + fc, n_freq_points)
    port.CalcPort(sim_path, freq)

    s11 = port.uf_ref / port.uf_inc
    s11_dB = 20.0 * np.log10(np.abs(s11))

    idx_min = int(np.argmin(s11_dB))
    f_res = float(freq[idx_min])
    s11_min = float(np.min(s11_dB))
    s11_max = float(np.max(s11_dB))

    theta = np.arange(-180.0, 180.0, 2.0)
    phi = [0.0, 90.0]
    nf2ff_res = nf2ff.CalcNF2FF(sim_path, f_res, theta, phi, center=[0, 0, 0])

    dmax = float(np.atleast_1d(nf2ff_res.Dmax)[0])
    prad = float(np.atleast_1d(nf2ff_res.Prad)[0])
    p_acc = float(np.atleast_1d(port.P_acc).flat[idx_min])
    efficiency = float(np.clip(prad / p_acc if p_acc > 0 else 0, 0, 1))
    gain_dBi = float(10.0 * np.log10(efficiency * dmax)) if efficiency * dmax > 0 else float('-inf')

    results = {
        'input': {
            'Dipole_Length_mm': Dipole_Length,
            'Wire_Radius_mm': Wire_Radius,
            'Feed_Gap_mm': Feed_Gap,
        },
        'output': {
            'Gain_dBi': gain_dBi,
            'Efficiency': efficiency,
            'S11_min_dB': s11_min,
            'S11_max_dB': s11_max,
            'Resonance_Frequency_GHz': f_res / 1e9,
            'Min_S11_dB': s11_min,
            'Min_S11_freq_GHz': f_res / 1e9,
            'Simulation_Method': 'FDTD',
            'S11_points': n_freq_points,
        },
    }

    os.makedirs(results_dir, exist_ok=True)
    with open(results_json, 'w') as fp:
        json.dump(results, fp, indent=2)

    print('\nSIMPLE DIPOLE RESULTS')
    print('  Gain: {:.2f} dBi'.format(gain_dBi))
    print('  Efficiency: {:.2%}'.format(efficiency))
    print('  f_res: {:.3f} GHz'.format(f_res / 1e9))
    print('  S11_min: {:.2f} dB'.format(s11_min))
    print('  Saved:', results_json)

    if show_plots:
        figure()
        plot(freq / 1e9, s11_dB, 'k-', linewidth=2, label=r'$S_{11}$')
        grid(); legend(); ylabel('S-Parameter (dB)'); xlabel('Frequency (GHz)')
        title('Simple Dipole Reflection Coefficient')
        show()


if __name__ == '__main__':
    build_and_run(show_plots=True)
