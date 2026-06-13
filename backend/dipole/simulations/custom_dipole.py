# -*- coding: utf-8 -*-
"""
Custom dipole antenna parameter generation for digital twin dataset.

- Wide practical ranges for real-life dipole design exploration
- 12 batches x 100 runs (1200 total) by default
- Appends all rows into one CSV file
- Saves full JSON metadata/results
"""

import os
import csv
import json
import shutil
import numpy as np

from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0

# =============================================================================
# BATCH CONFIG
# =============================================================================

# Fast mode keeps 1000 runs but reduces per-run simulation cost.
FAST_MODE = True

n_batches = 10
n_simulations_per_batch = 100
n_simulations = n_batches * n_simulations_per_batch
random_seed = 42

# Wide practical ranges around common sub-GHz to 3 GHz dipoles
param_ranges = {
    'Dipole_Length_mm': (12.0, 220.0),   # total length
    'Wire_Radius_mm': (0.2, 2.5),        # wire thickness proxy
    'Feed_Gap_mm': (0.5, 3.0),           # feed split gap
    'f0_GHz': (0.8, 10.0),                # center frequency
}

# Fixed simulation controls
fc_ratio = 0.45        # bandwidth = fc_ratio * f0
feed_R = 50
n_freq_points = 151 if FAST_MODE else 301
SimBox = np.array([500, 500, 500])      # mm (used when FAST_MODE is False)

# Paths
results_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results'))
results_csv = os.path.join(results_dir, 'Old_custom_dipole_results.csv')
results_json = os.path.join(results_dir, 'Old_custom_dipole_results.json')
base_sim_path = os.path.join(results_dir, 'custom_dipole_batch')


def to_serializable(obj):
    if obj is None:
        return None
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        return None if not np.isfinite(value) else value
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_serializable(v) for v in obj]
    return obj


def sample_params(rng):
    params = {}

    # Sample center frequency first, then derive physically consistent geometry.
    f0_lo, f0_hi = param_ranges['f0_GHz']
    f0_ghz = float(rng.uniform(f0_lo, f0_hi)) if f0_lo != f0_hi else float(f0_lo)
    params['f0_GHz'] = f0_ghz

    # Free-space wavelength in mm.
    lambda0_mm = 300.0 / f0_ghz

    # Keep total dipole length near resonant region for sampled f0.
    # This avoids extremely large/high-frequency mismatches that blow up FDTD size.
    l_lo_abs, l_hi_abs = param_ranges['Dipole_Length_mm']
    l_lo = max(l_lo_abs, 0.35 * lambda0_mm)
    l_hi = min(l_hi_abs, 0.60 * lambda0_mm)
    if l_lo > l_hi:
        l_mid = 0.47 * lambda0_mm
        l_lo = l_hi = float(np.clip(l_mid, l_lo_abs, l_hi_abs))
    params['Dipole_Length_mm'] = float(rng.uniform(l_lo, l_hi)) if l_lo != l_hi else float(l_lo)

    # Wire radius as a small fraction of wavelength, clamped to requested global range.
    r_lo_abs, r_hi_abs = param_ranges['Wire_Radius_mm']
    r_lo = max(r_lo_abs, 0.002 * lambda0_mm)
    r_hi = min(r_hi_abs, 0.010 * lambda0_mm)
    if r_lo > r_hi:
        r_mid = 0.004 * lambda0_mm
        r_lo = r_hi = float(np.clip(r_mid, r_lo_abs, r_hi_abs))
    params['Wire_Radius_mm'] = float(rng.uniform(r_lo, r_hi)) if r_lo != r_hi else float(r_lo)

    # Feed gap remains from configured practical range.
    g_lo, g_hi = param_ranges['Feed_Gap_mm']
    params['Feed_Gap_mm'] = float(rng.uniform(g_lo, g_hi)) if g_lo != g_hi else float(g_lo)

    return params


def run_simulation(params, sim_path):
    unit = 1e-3
    dipole_length = params['Dipole_Length_mm']
    wire_radius = params['Wire_Radius_mm']
    feed_gap = params['Feed_Gap_mm']
    f0 = params['f0_GHz'] * 1e9
    fc = fc_ratio * f0

    half_len = dipole_length / 2.0
    half_gap = feed_gap / 2.0

    fdtd = openEMS(
        NrTS=30000 if FAST_MODE else 45000,
        EndCriteria=3e-4 if FAST_MODE else 1e-4
    )
    fdtd.SetGaussExcite(f0, fc)
    fdtd.SetBoundaryCond(['MUR', 'MUR', 'MUR', 'MUR', 'MUR', 'MUR'])

    csx = ContinuousStructure()
    fdtd.SetCSX(CSX=csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(unit)

    if FAST_MODE:
        # Dynamic box sizing keeps wide parameter coverage while avoiding one
        # oversized domain for every run.
        lambda0_mm = (C0 / f0) * 1e3
        margin = max(0.40 * lambda0_mm, 1.0 * dipole_length) + 20.0
        box_edge = float(np.clip(2.0 * margin, 180.0, 320.0))
        sim_box = np.array([box_edge, box_edge, box_edge], dtype=float)
        mesh_res = C0 / (f0 + fc) / unit / 18
    else:
        sim_box = SimBox.astype(float)
        mesh_res = C0 / (f0 + fc) / unit / 28

    mesh.AddLine('x', [-sim_box[0] / 2, sim_box[0] / 2])
    mesh.AddLine('y', [-sim_box[1] / 2, sim_box[1] / 2])
    mesh.AddLine('z', [-sim_box[2] / 2, sim_box[2] / 2])

    dipole = csx.AddMetal('dipole')
    dipole.AddBox(priority=10,
                  start=[-wire_radius, -wire_radius, -half_len],
                  stop=[wire_radius, wire_radius, -half_gap])
    dipole.AddBox(priority=10,
                  start=[-wire_radius, -wire_radius, half_gap],
                  stop=[wire_radius, wire_radius, half_len])
    fdtd.AddEdges2Grid(dirs='xyz', properties=dipole, metal_edge_res=mesh_res / 2)

    port = fdtd.AddLumpedPort(1, feed_R,
                              [0.0, 0.0, -half_gap],
                              [0.0, 0.0, half_gap],
                              'z', 1.0, priority=5, edges2grid='xy')

    mesh.SmoothMeshLines('all', mesh_res, 1.4)
    nf2ff = fdtd.CreateNF2FFBox()

    os.makedirs(sim_path, exist_ok=True)
    fdtd.Run(sim_path, cleanup=True)

    freq = np.linspace(max(0.2e9, f0 - fc), f0 + fc, n_freq_points)
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

    return {
        'input': {
            'Dipole_Length_mm': dipole_length,
            'Wire_Radius_mm': wire_radius,
            'Feed_Gap_mm': feed_gap,
            'f0_GHz': params['f0_GHz'],
            'fc_GHz': fc / 1e9,
        },
        'output': {
            'Gain_dBi': gain_dBi if np.isfinite(gain_dBi) else None,
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


def csv_value(v):
    if v is None:
        return ''
    if isinstance(v, float) and not np.isfinite(v):
        return ''
    return v


def main():
    rng = np.random.default_rng(random_seed)
    os.makedirs(results_dir, exist_ok=True)

    csv_columns = [
        'run_id',
        'Dipole_Length_mm', 'Wire_Radius_mm', 'Feed_Gap_mm', 'f0_GHz', 'fc_GHz',
        'Gain_dBi', 'Efficiency', 'S11_min_dB', 'S11_max_dB', 'Resonance_Frequency_GHz',
        'Min_S11_dB', 'Min_S11_freq_GHz', 'Simulation_Method', 'S11_points', 'error',
    ]

    all_results = []

    print('=' * 66)
    print('Dipole Antenna Digital Twin Batch Simulation')
    print('FAST_MODE: {}'.format('ON' if FAST_MODE else 'OFF'))
    print('Batches: {} x {} = {} runs | CSV: {}'.format(
        n_batches, n_simulations_per_batch, n_simulations, results_csv))
    print('=' * 66)

    for batch_idx in range(n_batches):
        batch_path = os.path.join(base_sim_path, 'batch_{:02d}'.format(batch_idx + 1))
        run_id_offset = batch_idx * n_simulations_per_batch
        batch_results = []

        print('\n--- Batch {}/{} (runs {}-{}) ---'.format(
            batch_idx + 1, n_batches, run_id_offset + 1, run_id_offset + n_simulations_per_batch))

        for i in range(n_simulations_per_batch):
            run_id = run_id_offset + i + 1
            params = sample_params(rng)
            sim_path = os.path.join(batch_path, 'run_{:04d}'.format(i + 1))

            print('[{}/{}] Run {}: L={:.1f}mm, R={:.2f}mm, gap={:.2f}mm, f0={:.2f}GHz'.format(
                run_id, n_simulations, run_id,
                params['Dipole_Length_mm'], params['Wire_Radius_mm'], params['Feed_Gap_mm'], params['f0_GHz']))

            try:
                res = run_simulation(params, sim_path)
                res['run_id'] = run_id
                res['sim_path'] = sim_path
                rec = to_serializable(res)
                batch_results.append(rec)
                all_results.append(rec)

                out = rec['output']
                g = out.get('Gain_dBi')
                g_str = '{:.2f}'.format(g) if isinstance(g, (int, float)) else 'N/A'
                print('  -> Gain {} dBi | Eff {:.1%} | f_res {:.3f} GHz | S11_min {:.1f} dB'.format(
                    g_str, out['Efficiency'], out['Resonance_Frequency_GHz'], out['S11_min_dB']))
            except Exception as exc:
                print('  -> FAILED:', exc)
                rec = {'run_id': run_id, 'error': str(exc), 'input': to_serializable(params)}
                batch_results.append(rec)
                all_results.append(rec)

        # append to one CSV
        write_header = (batch_idx == 0)
        mode = 'w' if write_header else 'a'
        with open(results_csv, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns, extrasaction='ignore')
            if write_header:
                writer.writeheader()

            for rec in batch_results:
                row = {'run_id': rec.get('run_id', '')}
                if 'error' in rec:
                    row['error'] = rec['error']
                    inp = rec.get('input', {})
                    for k in ['Dipole_Length_mm', 'Wire_Radius_mm', 'Feed_Gap_mm', 'f0_GHz', 'fc_GHz']:
                        row[k] = csv_value(inp.get(k))
                    for k in ['Gain_dBi', 'Efficiency', 'S11_min_dB', 'S11_max_dB', 'Resonance_Frequency_GHz',
                              'Min_S11_dB', 'Min_S11_freq_GHz', 'Simulation_Method', 'S11_points']:
                        row[k] = ''
                else:
                    row['error'] = ''
                    row.update({k: csv_value(v) for k, v in rec.get('input', {}).items()})
                    row.update({k: csv_value(v) for k, v in rec.get('output', {}).items()})
                writer.writerow(row)

        # free disk batch-wise
        if os.path.isdir(batch_path):
            try:
                shutil.rmtree(batch_path)
                print('  Cleared batch dir:', batch_path)
            except OSError as exc:
                print('  Warning: failed to remove {}: {}'.format(batch_path, exc))

    with open(results_json, 'w') as f:
        json.dump({
            'n_simulations': n_simulations,
            'n_batches': n_batches,
            'n_simulations_per_batch': n_simulations_per_batch,
            'param_ranges': param_ranges,
            'results': all_results,
        }, f, indent=2)

    print('\n' + '=' * 66)
    print('Done. {} dipole simulations saved.'.format(n_simulations))
    print('CSV :', results_csv)
    print('JSON:', results_json)
    print('=' * 66)


if __name__ == '__main__':
    main()
