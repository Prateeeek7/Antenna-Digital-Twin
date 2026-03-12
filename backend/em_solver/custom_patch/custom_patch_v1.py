# -*- coding: utf-8 -*-
"""
 Customizable Microstrip Patch Antenna - Single or Batch Simulation

 Single run: Set n_simulations=1 (or use single-run mode).
 Batch run: Set n_simulations (e.g., 100, 200) and parameter ranges.
            Random values are sampled from each range for each run.
            Results saved to JSON file.

 Target: 2.4 GHz microstrip patch antenna

 (c) Based on openEMS Simple Patch Antenna tutorial
"""

import os
import json
import csv
import shutil
import numpy as np
from pylab import *

from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0, EPS0

# =============================================================================
# BATCH SIMULATION CONFIG
# =============================================================================

# Batches: 12 batches x 100 simulations = 1200 total; each batch writes to same CSV then frees disk
n_batches = 12
n_simulations_per_batch = 100
n_simulations = n_batches * n_simulations_per_batch  # 1200 total

# Random seed for reproducibility (None = random each run)
random_seed = 42

# Parameter RANGES (min, max) - random value sampled uniformly in [min, max]
# Set both equal for fixed value
param_ranges = {
    'Length': (30.0, 35.0),        # mm (patch length, resonant dim) - 2.2-2.6 GHz
    'Width': (26.0, 31.0),         # mm (patch width, W/L ~ 0.85-0.9)
    'Height': (1.2, 2.0),          # mm (substrate thickness)
    'Feed_X_mm': (-7.0, -3.0),     # mm (x-offset from center, same as simple_patch)
    'substrate_epsR': (3.8, 4.6),  # permittivity (FR4 range)
    'substrate_loss_tan': (0.0, 0.02),  # loss tangent
}

# Fixed parameters (not varied)
f0 = 2.4e9           # target frequency (Hz)
fc = 0.5e9           # excitation bandwidth (Hz)
feed_R = 50          # Ohm
SimBox = np.array([200, 200, 150])  # mm
n_freq_points = 201
substrate_cells = 4

# Output
results_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results'))
results_json = os.path.join(results_dir, 'Old_custom_patch_results.json')
results_csv = os.path.join(results_dir, 'Old_custom_patch_results.csv')

# Batch mode: skip interactive plots (set True for faster batch)
batch_no_plots = True

# =============================================================================
# Helper: convert to JSON-serializable
# =============================================================================

def to_serializable(obj):
    if obj is None:
        return None
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        return None if not np.isfinite(v) else v
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)) and len(obj) > 0:
        return [to_serializable(x) for x in obj]
    return obj

# =============================================================================
# Run one simulation with given parameters
# =============================================================================

def run_simulation(params, sim_idx, sim_path, verbose=True, show_plots=False, fast=False):
    """Run a single FDTD simulation with given params. Returns dict of results.

    fast: If True, use fewer time steps and coarser mesh for quicker runs (~1–2 min);
          default False gives higher accuracy (~3–5 min).
    Optional params: f_min, f_max (Hz) to set frequency sweep; otherwise uses 2.4 GHz band.
    """
    unit = 1e-3
    Length = params['Length']
    Width = params['Width']
    Height = params['Height']
    feed_pos_x = params['Feed_X_mm']   # mm (x-offset from center)
    feed_pos_y = params.get('Feed_Y_mm', 0.0)  # mm (y-offset from center; 0 = center)
    substrate_epsR = params['substrate_epsR']
    substrate_loss_tan = params['substrate_loss_tan']

    # Frequency range: use request range if provided, else default 2.4 GHz band
    f_min_hz = params.get('f_min')
    f_max_hz = params.get('f_max')
    if f_min_hz is not None and f_max_hz is not None and f_max_hz > f_min_hz:
        f0 = (f_min_hz + f_max_hz) / 2.0
        fc = (f_max_hz - f_min_hz) / 2.0
    else:
        f0 = 2.4e9
        fc = 0.5e9

    patch_length = Length
    patch_width = Width
    substrate_thickness = Height
    substrate_kappa = substrate_loss_tan * 2*np.pi*f0 * EPS0*substrate_epsR
    substrate_width = max(Width + 20, 60)
    substrate_length = max(Length + 20, 60)

    # FDTD setup (fast = fewer steps, relaxed convergence, coarser mesh)
    nr_ts = 12000 if fast else 30000
    end_criteria = 1e-3 if fast else 1e-4
    cells_per_wl = 14 if fast else 20
    n_freq = 101 if fast else n_freq_points

    FDTD = openEMS(NrTS=nr_ts, EndCriteria=end_criteria)
    FDTD.SetGaussExcite(f0, fc)
    FDTD.SetBoundaryCond(['MUR', 'MUR', 'MUR', 'MUR', 'MUR', 'MUR'])

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(unit)
    mesh_res = C0/(f0+fc)/unit/cells_per_wl

    mesh.AddLine('x', [-SimBox[0]/2, SimBox[0]/2])
    mesh.AddLine('y', [-SimBox[1]/2, SimBox[1]/2])
    mesh.AddLine('z', [-SimBox[2]/3, SimBox[2]*2/3])

    patch = CSX.AddMetal('patch')
    start = [-patch_width/2, -patch_length/2, substrate_thickness]
    stop = [patch_width/2, patch_length/2, substrate_thickness]
    patch.AddBox(priority=10, start=start, stop=stop)
    FDTD.AddEdges2Grid(dirs='xy', properties=patch, metal_edge_res=mesh_res/2)

    substrate = CSX.AddMaterial('substrate', epsilon=substrate_epsR, kappa=substrate_kappa)
    start = [-substrate_width/2, -substrate_length/2, 0]
    stop = [substrate_width/2, substrate_length/2, substrate_thickness]
    substrate.AddBox(priority=0, start=start, stop=stop)
    mesh.AddLine('z', np.linspace(0, substrate_thickness, substrate_cells+1))

    gnd = CSX.AddMetal('gnd')
    start[2] = 0
    stop[2] = 0
    gnd.AddBox(start, stop, priority=10)
    FDTD.AddEdges2Grid(dirs='xy', properties=gnd)

    start = [feed_pos_x, feed_pos_y, 0]
    stop = [feed_pos_x, feed_pos_y, substrate_thickness]
    port = FDTD.AddLumpedPort(1, feed_R, start, stop, 'z', 1.0, priority=5, edges2grid='xy')
    mesh.SmoothMeshLines('all', mesh_res, 1.4)
    nf2ff = FDTD.CreateNF2FFBox()

    # Run FDTD
    os.makedirs(sim_path, exist_ok=True)
    FDTD.Run(sim_path, cleanup=True)

    # Post-process: sweep over [f_min, f_max]
    f_sweep_min = max(0.5e9, f0 - fc)
    f_sweep_max = f0 + fc
    freq = np.linspace(f_sweep_min, f_sweep_max, n_freq)
    port.CalcPort(sim_path, freq)
    s11 = port.uf_ref/port.uf_inc
    s11_dB = 20.0*np.log10(np.abs(s11))

    idx_min = np.argmin(s11_dB)
    f_res = float(freq[idx_min])
    s11_min_val = float(s11_dB[idx_min])
    s11_max_val = float(np.max(s11_dB))
    s11_min_overall = float(np.min(s11_dB))

    # Gain & efficiency: same formulas as dataset generator (batch script)
    # efficiency = Prad / P_acc at resonance; gain_dBi = 10*log10(efficiency * Dmax)
    theta = np.arange(-180.0, 180.0, 2.0)
    phi = [0., 90.]
    nf2ff_res = nf2ff.CalcNF2FF(sim_path, f_res, theta, phi, center=[0, 0, unit])

    Dmax = np.atleast_1d(nf2ff_res.Dmax)[0]
    Prad = np.atleast_1d(nf2ff_res.Prad)[0]
    # P_acc is per-frequency; use resonance index (same as dataset generator)
    P_acc_arr = np.atleast_1d(port.P_acc)
    P_acc = float(P_acc_arr.flat[idx_min]) if P_acc_arr.size > idx_min else 0.0
    efficiency = float(np.clip(Prad / P_acc if P_acc > 0 else 0, 0, 1))
    gain_dBi = float(10.0 * np.log10(efficiency * Dmax)) if (efficiency * Dmax) > 0 else float(-np.inf)

    results = {
        'input': {
            'Length': Length, 'Width': Width, 'Height': Height,
            'Feed_X_mm': feed_pos_x,
            'substrate_epsR': substrate_epsR, 'substrate_loss_tan': substrate_loss_tan,
        },
        'output': {
            'Gain_dBi': gain_dBi if np.isfinite(gain_dBi) else None, 'Efficiency': efficiency,
            'S11_min_dB': s11_min_overall, 'S11_max_dB': s11_max_val,
            'Resonance_Frequency_GHz': f_res/1e9,
            'Min_S11_dB': s11_min_val, 'Min_S11_freq_GHz': f_res/1e9,
            'Simulation_Method': 'FDTD', 'S11_points': n_freq,
            'frequency': freq.tolist(),
            's11_magnitude': s11_dB.tolist(),
        }
    }

    if show_plots:
        figure()
        plot(freq/1e9, s11_dB, 'k-', linewidth=2, label=r'$S_{11}$')
        grid(); legend(); ylabel('S-Parameter (dB)'); xlabel('Frequency (GHz)')
        title('Reflection Coefficient')

        figure()
        E_norm = 20.0*np.log10(nf2ff_res.E_norm[0]/np.max(nf2ff_res.E_norm[0])) + 10.0*np.log10(nf2ff_res.Dmax[0])
        plot(theta, np.squeeze(E_norm[:, 0]), 'k-', linewidth=2, label='E-plane')
        plot(theta, np.squeeze(E_norm[:, 1]), 'r--', linewidth=2, label='H-plane')
        grid(); legend(); ylabel('Directivity (dBi)'); xlabel('Theta (deg)')
        title('Far-Field at {:.3f} GHz'.format(f_res/1e9))

        Zin = port.uf_tot/port.if_tot
        figure()
        plot(freq/1e9, np.real(Zin), 'k-', linewidth=2, label=r'$\Re\{Z_{in}\}$')
        plot(freq/1e9, np.imag(Zin), 'r--', linewidth=2, label=r'$\Im\{Z_{in}\}$')
        grid(); legend(); ylabel('Zin (Ohm)'); xlabel('Frequency (GHz)')
        show()

    return results

# =============================================================================
# Sample random parameters from ranges
# =============================================================================

def sample_params(rng):
    params = {}
    for key, (lo, hi) in param_ranges.items():
        if lo == hi:
            params[key] = lo
        else:
            params[key] = float(rng.uniform(lo, hi))
    return params

# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    rng = np.random.default_rng(random_seed)
    all_results = []  # accumulated for final JSON only
    base_path = os.path.normpath(os.path.join(results_dir, 'custom_patch_batch'))
    os.makedirs(results_dir, exist_ok=True)

    csv_columns = [
        'run_id', 'Length', 'Width', 'Height', 'Feed_X_mm', 'substrate_epsR', 'substrate_loss_tan',
        'Gain_dBi', 'Efficiency', 'S11_min_dB', 'S11_max_dB', 'Resonance_Frequency_GHz',
        'Min_S11_dB', 'Min_S11_freq_GHz', 'Simulation_Method', 'S11_points', 'error'
    ]
    def csv_value(v):
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return ''
        return v

    print('='*60)
    print('Microstrip Patch Antenna Batch Simulation')
    print('Target: {:.1f} GHz | Batches: {} x {} = {} runs | CSV: {}'.format(
        f0/1e9, n_batches, n_simulations_per_batch, n_simulations, results_csv))
    print('='*60)

    for batch_idx in range(n_batches):
        batch_path = os.path.join(base_path, 'batch_{:02d}'.format(batch_idx + 1))
        batch_results = []
        run_id_offset = batch_idx * n_simulations_per_batch

        print('\n--- Batch {}/{} (runs {}–{}) ---'.format(
            batch_idx + 1, n_batches, run_id_offset + 1, run_id_offset + n_simulations_per_batch))

        for i in range(n_simulations_per_batch):
            global_run_id = run_id_offset + i + 1
            params = sample_params(rng)
            sim_path = os.path.join(batch_path, 'run_{:04d}'.format(i + 1))

            print('\n[{}/{}] Run {}: L={:.2f}, W={:.2f}, H={:.2f}, eps_r={:.2f}'.format(
                global_run_id, n_simulations, global_run_id,
                params['Length'], params['Width'], params['Height'], params['substrate_epsR']))

            try:
                show_plots = (n_simulations == 1) and not batch_no_plots
                res = run_simulation(params, global_run_id, sim_path, verbose=(n_simulations <= 5), show_plots=show_plots)
                res['run_id'] = global_run_id
                res['sim_path'] = sim_path
                batch_results.append(to_serializable(res))
                all_results.append(batch_results[-1])
                out = res['output']
                g = out['Gain_dBi']
                g_str = '{:.2f}'.format(g) if g is not None and np.isfinite(g) else 'N/A'
                print('  -> Gain: {} dBi, eff: {:.1%}, f_res: {:.3f} GHz, S11_min: {:.1f} dB'.format(
                    g_str, out['Efficiency'],
                    out['Resonance_Frequency_GHz'], out['S11_min_dB']))
                if n_simulations == 1:
                    print('\nINPUT PARAMETERS:')
                    for k, v in res['input'].items():
                        print('  {}: {:.4f}'.format(k, v))
                    print('SIMULATION RESULTS:')
                    for k, v in out.items():
                        if isinstance(v, float):
                            print('  {}: {:.4f}'.format(k, v))
                        else:
                            print('  {}: {}'.format(k, v))
            except Exception as e:
                print('  -> FAILED: {}'.format(e))
                rec = {'run_id': global_run_id, 'error': str(e), 'input': to_serializable(params)}
                batch_results.append(rec)
                all_results.append(rec)

        # Append this batch to the same CSV (header only on first batch)
        write_header = (batch_idx == 0)
        with open(results_csv, 'a' if batch_idx > 0 else 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns, extrasaction='ignore')
            if write_header:
                writer.writeheader()
            for res in batch_results:
                row = {'run_id': res.get('run_id', '')}
                if 'error' in res:
                    row['error'] = res['error']
                    inp = res.get('input', {})
                    for k in ['Length', 'Width', 'Height', 'Feed_X_mm', 'substrate_epsR', 'substrate_loss_tan']:
                        row[k] = csv_value(inp.get(k))
                    for k in ['Gain_dBi', 'Efficiency', 'S11_min_dB', 'S11_max_dB', 'Resonance_Frequency_GHz',
                              'Min_S11_dB', 'Min_S11_freq_GHz', 'Simulation_Method', 'S11_points']:
                        row[k] = ''
                else:
                    row['error'] = ''
                    row.update({k: csv_value(v) for k, v in res.get('input', {}).items()})
                    row.update({k: csv_value(v) for k, v in res.get('output', {}).items()})
                writer.writerow(row)

        # Free disk: remove this batch's run directory
        if os.path.isdir(batch_path):
            try:
                shutil.rmtree(batch_path)
                print('  Cleared batch dir: {}'.format(batch_path))
            except OSError as e:
                print('  Warning: could not remove {}: {}'.format(batch_path, e))

    # Save full JSON at the end (optional; same data as CSV)
    with open(results_json, 'w') as f:
        json.dump({
            'n_simulations': n_simulations,
            'n_batches': n_batches,
            'n_simulations_per_batch': n_simulations_per_batch,
            'target_freq_GHz': f0/1e9,
            'param_ranges': param_ranges,
            'results': all_results,
        }, f, indent=2)

    print('\n' + '='*60)
    print('Done. All {} runs in {} batches saved to: {}'.format(n_simulations, n_batches, results_csv))
    print('JSON: {}'.format(results_json))
    print('='*60)

