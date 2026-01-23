#!/usr/bin/env python3
"""
Generate a comprehensive log file for all simulation data.
Includes input parameters, results, and statistics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_simulation_data(training_dir: Path) -> List[Dict[str, Any]]:
    """Load all simulation data from training directory."""
    simulations = []
    
    # Find all simulation directories
    sim_dirs = sorted([d for d in training_dir.iterdir() if d.is_dir() and d.name.startswith('sim_')])
    
    for sim_dir in sim_dirs:
        params_file = sim_dir / "parameters.json"
        results_file = sim_dir / "results.json"
        
        # Try to find results.json in nested structure
        if not results_file.exists():
            nested_results = list(sim_dir.rglob("results.json"))
            if nested_results:
                results_file = nested_results[0]
        
        if params_file.exists() and results_file.exists():
            try:
                with open(params_file, 'r') as f:
                    params = json.load(f)
                
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                simulations.append({
                    'sim_id': sim_dir.name,
                    'parameters': params,
                    'results': results
                })
            except Exception as e:
                print(f"Warning: Could not load {sim_dir.name}: {e}", file=sys.stderr)
    
    return simulations

def calculate_statistics(simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive statistics."""
    gains = []
    efficiencies = []
    s11_mins = []
    s11_maxs = []
    resonance_freqs = []
    
    # Geometry parameters
    lengths = []
    widths = []
    heights = []
    feed_xs = []
    feed_ys = []
    permittivities = []
    loss_tangents = []
    
    for sim in simulations:
        results = sim['results']
        params = sim['parameters']
        
        # Extract results
        if 'gain' in results:
            gains.append(results['gain'])
        if 'efficiency' in results:
            efficiencies.append(results['efficiency'])
        if 's11_magnitude' in results and results['s11_magnitude']:
            s11_mags = results['s11_magnitude']
            s11_mins.append(min(s11_mags))
            s11_maxs.append(max(s11_mags))
        if 'resonance_frequency' in results:
            resonance_freqs.append(results['resonance_frequency'] / 1e9)  # Convert to GHz
        
        # Extract parameters
        if 'geometry' in params:
            geom = params['geometry']
            lengths.append(geom.get('length', 0) * 1000)  # Convert to mm
            widths.append(geom.get('width', 0) * 1000)  # Convert to mm
            heights.append(geom.get('height', 0) * 1000)  # Convert to mm
            feed_xs.append(geom.get('feed_x', 0))
            feed_ys.append(geom.get('feed_y', 0))
        
        if 'substrate' in params:
            sub = params['substrate']
            permittivities.append(sub.get('relative_permittivity', 0))
            loss_tangents.append(sub.get('loss_tangent', 0))
    
    stats = {}
    
    if gains:
        stats['gain'] = {
            'count': len(gains),
            'min': float(np.min(gains)),
            'max': float(np.max(gains)),
            'mean': float(np.mean(gains)),
            'median': float(np.median(gains)),
            'std': float(np.std(gains)),
            'q25': float(np.percentile(gains, 25)),
            'q75': float(np.percentile(gains, 75))
        }
    
    if efficiencies:
        stats['efficiency'] = {
            'count': len(efficiencies),
            'min': float(np.min(efficiencies)),
            'max': float(np.max(efficiencies)),
            'mean': float(np.mean(efficiencies)),
            'median': float(np.median(efficiencies)),
            'std': float(np.std(efficiencies)),
            'q25': float(np.percentile(efficiencies, 25)),
            'q75': float(np.percentile(efficiencies, 75))
        }
    
    if s11_mins:
        stats['s11_min'] = {
            'count': len(s11_mins),
            'min': float(np.min(s11_mins)),
            'max': float(np.max(s11_mins)),
            'mean': float(np.mean(s11_mins)),
            'median': float(np.median(s11_mins)),
            'std': float(np.std(s11_mins)),
            'q25': float(np.percentile(s11_mins, 25)),
            'q75': float(np.percentile(s11_mins, 75))
        }
    
    if resonance_freqs:
        stats['resonance_frequency'] = {
            'count': len(resonance_freqs),
            'min': float(np.min(resonance_freqs)),
            'max': float(np.max(resonance_freqs)),
            'mean': float(np.mean(resonance_freqs)),
            'median': float(np.median(resonance_freqs)),
            'std': float(np.std(resonance_freqs)),
            'q25': float(np.percentile(resonance_freqs, 25)),
            'q75': float(np.percentile(resonance_freqs, 75))
        }
    
    # Parameter statistics
    if lengths:
        stats['length'] = {
            'min': float(np.min(lengths)),
            'max': float(np.max(lengths)),
            'mean': float(np.mean(lengths)),
            'std': float(np.std(lengths))
        }
    
    if widths:
        stats['width'] = {
            'min': float(np.min(widths)),
            'max': float(np.max(widths)),
            'mean': float(np.mean(widths)),
            'std': float(np.std(widths))
        }
    
    if heights:
        stats['height'] = {
            'min': float(np.min(heights)),
            'max': float(np.max(heights)),
            'mean': float(np.mean(heights)),
            'std': float(np.std(heights))
        }
    
    if permittivities:
        stats['permittivity'] = {
            'min': float(np.min(permittivities)),
            'max': float(np.max(permittivities)),
            'mean': float(np.mean(permittivities)),
            'std': float(np.std(permittivities))
        }
    
    return stats

def format_simulation_entry(sim: Dict[str, Any], index: int) -> str:
    """Format a single simulation entry."""
    params = sim['parameters']
    results = sim['results']
    
    # Extract geometry
    geom = params.get('geometry', {})
    length = geom.get('length', 0) * 1000  # mm
    width = geom.get('width', 0) * 1000  # mm
    height = geom.get('height', 0) * 1000  # mm
    feed_x = geom.get('feed_x', 0)
    feed_y = geom.get('feed_y', 0)
    
    # Extract substrate
    sub = params.get('substrate', {})
    permittivity = sub.get('relative_permittivity', 0)
    loss_tangent = sub.get('loss_tangent', 0)
    
    # Extract results
    gain = results.get('gain', 0)
    efficiency = results.get('efficiency', 0)
    s11_mags = results.get('s11_magnitude', [])
    s11_min = min(s11_mags) if s11_mags else 0
    s11_max = max(s11_mags) if s11_mags else 0
    resonance_freq = results.get('resonance_frequency', 0) / 1e9  # GHz
    method = results.get('simulation_method', 'unknown')
    
    entry = f"""
{'='*80}
CASE #{index+1:04d} - {sim['sim_id']}
{'='*80}

INPUT PARAMETERS:
  Geometry:
    Length:     {length:8.4f} mm
    Width:      {width:8.4f} mm
    Height:     {height:8.4f} mm
    Feed X:     {feed_x:8.4f} (fraction of length)
    Feed Y:     {feed_y:8.4f} (fraction of width)
  
  Substrate:
    Permittivity (εr):  {permittivity:8.4f}
    Loss Tangent:      {loss_tangent:8.6f}

SIMULATION RESULTS:
  Gain:                 {gain:8.4f} dBi
  Efficiency:           {efficiency:8.4f} ({efficiency*100:6.2f}%)
  S11_min:              {s11_min:8.2f} dB
  S11_max:              {s11_max:8.2f} dB
  Resonance Frequency:   {resonance_freq:8.4f} GHz
  Simulation Method:     {method}
  
  S11 Frequency Range:  {len(s11_mags)} points"""
    
    if s11_mags and 'frequency' in results:
        freq_at_min = results['frequency'][s11_mags.index(min(s11_mags))] / 1e9
        entry += f"\n    Min S11: {s11_min:.2f} dB at {freq_at_min:.4f} GHz"
    else:
        entry += "\n    Min S11: N/A"
    
    entry += "\n"
    
    return entry
    
    return entry

def generate_log_file(training_dir: Path, output_file: Path):
    """Generate comprehensive log file."""
    print(f"Loading simulation data from {training_dir}...")
    simulations = load_simulation_data(training_dir)
    print(f"Loaded {len(simulations)} simulations")
    
    if not simulations:
        print("Error: No simulations found!", file=sys.stderr)
        return
    
    # Calculate statistics
    print("Calculating statistics...")
    stats = calculate_statistics(simulations)
    
    # Generate log file
    print(f"Generating log file: {output_file}")
    with open(output_file, 'w') as f:
        # Header
        f.write("="*80 + "\n")
        f.write("ANTENNA DIGITAL TWIN - SIMULATION DATA LOG\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Simulations: {len(simulations)}\n")
        f.write(f"Training Directory: {training_dir}\n")
        f.write("="*80 + "\n\n")
        
        # Individual cases
        f.write("INDIVIDUAL SIMULATION CASES\n")
        f.write("="*80 + "\n")
        for i, sim in enumerate(simulations):
            f.write(format_simulation_entry(sim, i))
        
        # Statistics section
        f.write("\n\n")
        f.write("="*80 + "\n")
        f.write("STATISTICAL SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        # Gain statistics
        if 'gain' in stats:
            g = stats['gain']
            f.write("GAIN (dBi):\n")
            f.write(f"  Count:        {g['count']}\n")
            f.write(f"  Minimum:      {g['min']:8.4f} dBi\n")
            f.write(f"  Maximum:      {g['max']:8.4f} dBi\n")
            f.write(f"  Mean:         {g['mean']:8.4f} dBi\n")
            f.write(f"  Median:       {g['median']:8.4f} dBi\n")
            f.write(f"  Std Dev:      {g['std']:8.4f} dBi\n")
            f.write(f"  25th Percentile: {g['q25']:8.4f} dBi\n")
            f.write(f"  75th Percentile: {g['q75']:8.4f} dBi\n")
            f.write("\n")
        
        # Efficiency statistics
        if 'efficiency' in stats:
            e = stats['efficiency']
            f.write("EFFICIENCY:\n")
            f.write(f"  Count:        {e['count']}\n")
            f.write(f"  Minimum:      {e['min']:8.4f} ({e['min']*100:6.2f}%)\n")
            f.write(f"  Maximum:      {e['max']:8.4f} ({e['max']*100:6.2f}%)\n")
            f.write(f"  Mean:         {e['mean']:8.4f} ({e['mean']*100:6.2f}%)\n")
            f.write(f"  Median:       {e['median']:8.4f} ({e['median']*100:6.2f}%)\n")
            f.write(f"  Std Dev:      {e['std']:8.4f}\n")
            f.write(f"  25th Percentile: {e['q25']:8.4f} ({e['q25']*100:6.2f}%)\n")
            f.write(f"  75th Percentile: {e['q75']:8.4f} ({e['q75']*100:6.2f}%)\n")
            f.write("\n")
        
        # S11 statistics
        if 's11_min' in stats:
            s = stats['s11_min']
            f.write("S11_MIN (dB):\n")
            f.write(f"  Count:        {s['count']}\n")
            f.write(f"  Minimum:      {s['min']:8.2f} dB\n")
            f.write(f"  Maximum:      {s['max']:8.2f} dB\n")
            f.write(f"  Mean:         {s['mean']:8.2f} dB\n")
            f.write(f"  Median:       {s['median']:8.2f} dB\n")
            f.write(f"  Std Dev:      {s['std']:8.2f} dB\n")
            f.write(f"  25th Percentile: {s['q25']:8.2f} dB\n")
            f.write(f"  75th Percentile: {s['q75']:8.2f} dB\n")
            f.write("\n")
        
        # Resonance frequency statistics
        if 'resonance_frequency' in stats:
            rf = stats['resonance_frequency']
            f.write("RESONANCE FREQUENCY (GHz):\n")
            f.write(f"  Count:        {rf['count']}\n")
            f.write(f"  Minimum:      {rf['min']:8.4f} GHz\n")
            f.write(f"  Maximum:      {rf['max']:8.4f} GHz\n")
            f.write(f"  Mean:         {rf['mean']:8.4f} GHz\n")
            f.write(f"  Median:       {rf['median']:8.4f} GHz\n")
            f.write(f"  Std Dev:      {rf['std']:8.4f} GHz\n")
            f.write(f"  25th Percentile: {rf['q25']:8.4f} GHz\n")
            f.write(f"  75th Percentile: {rf['q75']:8.4f} GHz\n")
            f.write("\n")
        
        # Parameter statistics
        f.write("INPUT PARAMETER RANGES:\n")
        if 'length' in stats:
            l = stats['length']
            f.write(f"  Length:       {l['min']:6.2f} - {l['max']:6.2f} mm (mean: {l['mean']:6.2f} ± {l['std']:6.2f})\n")
        if 'width' in stats:
            w = stats['width']
            f.write(f"  Width:        {w['min']:6.2f} - {w['max']:6.2f} mm (mean: {w['mean']:6.2f} ± {w['std']:6.2f})\n")
        if 'height' in stats:
            h = stats['height']
            f.write(f"  Height:       {h['min']:6.2f} - {h['max']:6.2f} mm (mean: {h['mean']:6.2f} ± {h['std']:6.2f})\n")
        if 'permittivity' in stats:
            p = stats['permittivity']
            f.write(f"  Permittivity: {p['min']:6.2f} - {p['max']:6.2f} (mean: {p['mean']:6.2f} ± {p['std']:6.2f})\n")
        
        f.write("\n")
        f.write("="*80 + "\n")
        f.write("END OF LOG\n")
        f.write("="*80 + "\n")
    
    print(f"✅ Log file generated: {output_file}")
    print(f"   Total size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    # Find the most recent training directory
    results_dir = Path("data/em_results")
    training_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('training_')])
    
    if not training_dirs:
        print("Error: No training directories found!", file=sys.stderr)
        sys.exit(1)
    
    # Use the most recent one
    training_dir = training_dirs[-1]
    output_file = Path("data") / f"simulation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    generate_log_file(training_dir, output_file)

