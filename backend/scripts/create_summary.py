#!/usr/bin/env python3
"""Create summary JSON file for training results."""

import json
import scipy.io
from pathlib import Path
import numpy as np
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_summary(training_dir_path: str):
    """Create summary JSON for training results."""
    training_dir = Path(training_dir_path)
    sim_dirs = sorted([d for d in training_dir.iterdir() if d.is_dir() and d.name.startswith('sim_')])

    print(f"Processing {len(sim_dirs)} simulations...")

    summary = {
        "training_run": training_dir.name,
        "total_simulations": len(sim_dirs),
        "generated_at": datetime.now().isoformat(),
        "simulations": []
    }

    for idx, sim_dir in enumerate(sim_dirs):
        sim_data = {
            "simulation_id": sim_dir.name,
            "parameters": None,
            "results": None,
            "status": "unknown"
        }
        
        # Read parameters
        params_file = sim_dir / 'parameters.json'
        if params_file.exists():
            with open(params_file) as f:
                sim_data["parameters"] = json.load(f)
        
        # Try to find and parse results.mat
        results_mat_files = list(sim_dir.rglob('results.mat'))
        if results_mat_files:
            try:
                mat_file = results_mat_files[0]
                mat_data = scipy.io.loadmat(str(mat_file))
                
                # Extract data
                freq = mat_data.get('freq', np.array([]))
                s11_db = mat_data.get('s11_db', np.array([]))
                s11 = mat_data.get('s11', np.array([]))
                
                if len(freq) > 0:
                    freq_flat = freq.flatten() if freq.ndim > 1 else freq
                    s11_db_flat = s11_db.flatten() if s11_db.ndim > 1 else s11_db
                    s11_flat = s11.flatten() if s11.ndim > 1 else s11
                    
                    # Check for valid data
                    valid_freq = freq_flat[~np.isnan(freq_flat)]
                    valid_s11_db = s11_db_flat[~np.isnan(s11_db_flat)] if len(s11_db_flat) > 0 else np.array([])
                    valid_s11 = s11_flat[~np.isnan(s11_flat)] if len(s11_flat) > 0 else np.array([])
                    
                    # Try to calculate dB from complex s11 if s11_db is invalid
                    if len(valid_s11_db) == 0 and len(valid_s11) > 0:
                        valid_s11_db = 20 * np.log10(np.abs(valid_s11))
                    
                    sim_data["results"] = {
                        "frequency_range": {
                            "min": float(np.min(valid_freq)) if len(valid_freq) > 0 else None,
                            "max": float(np.max(valid_freq)) if len(valid_freq) > 0 else None,
                            "points": int(len(freq_flat))
                        },
                        "s11": {
                            "min_db": float(np.min(valid_s11_db)) if len(valid_s11_db) > 0 else None,
                            "max_db": float(np.max(valid_s11_db)) if len(valid_s11_db) > 0 else None,
                            "mean_db": float(np.mean(valid_s11_db)) if len(valid_s11_db) > 0 else None,
                            "at_2_4ghz": None,
                            "valid_data_points": len(valid_s11_db)
                        },
                        "data_points": len(freq_flat),
                        "has_valid_data": len(valid_s11_db) > 0
                    }
                    
                    # Find S11 at 2.4 GHz if available
                    if len(valid_freq) > 0 and len(valid_s11_db) > 0:
                        target_freq = 2.4e9
                        if np.min(valid_freq) <= target_freq <= np.max(valid_freq):
                            idx = np.argmin(np.abs(valid_freq - target_freq))
                            sim_data["results"]["s11"]["at_2_4ghz"] = float(valid_s11_db[idx])
                    
                    if len(valid_s11_db) > 0:
                        sim_data["status"] = "success"
                    else:
                        sim_data["status"] = "no_valid_data"
                        sim_data["results"]["error"] = "All S11 values are NaN"
                else:
                    sim_data["status"] = "empty_results"
                    sim_data["results"] = {"error": "No data in results.mat"}
            except Exception as e:
                sim_data["status"] = "parse_error"
                sim_data["results"] = {"error": str(e)}
        else:
            sim_data["status"] = "no_results_file"
        
        summary["simulations"].append(sim_data)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(sim_dirs)}...")

    # Calculate statistics
    successful = [s for s in summary["simulations"] if s["status"] == "success"]
    summary["statistics"] = {
        "successful": len(successful),
        "failed": len(summary["simulations"]) - len(successful),
        "success_rate": f"{100*len(successful)/len(sim_dirs):.1f}%"
    }

    if successful:
        s11_mins = [s["results"]["s11"]["min_db"] for s in successful 
                   if s["results"] and s["results"].get("s11") and s["results"]["s11"].get("min_db") is not None]
        if s11_mins:
            summary["statistics"]["s11_min"] = {
                "min": float(np.min(s11_mins)),
                "max": float(np.max(s11_mins)),
                "mean": float(np.mean(s11_mins)),
                "std": float(np.std(s11_mins))
            }
        else:
            summary["statistics"]["s11_min"] = {
                "note": "No valid S11 data found in any simulation results"
            }

    # Save summary
    output_file = training_dir / 'summary.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Summary created: {output_file}")
    print(f"   Total simulations: {summary['total_simulations']}")
    print(f"   Successful: {summary['statistics']['successful']}")
    print(f"   Failed: {summary['statistics']['failed']}")
    print(f"   Success rate: {summary['statistics']['success_rate']}")

    if successful and s11_mins:
        print(f"\n📊 S11 Statistics (dB):")
        print(f"   Min: {summary['statistics']['s11_min']['min']:.2f} dB")
        print(f"   Max: {summary['statistics']['s11_min']['max']:.2f} dB")
        print(f"   Mean: {summary['statistics']['s11_min']['mean']:.2f} dB")
        print(f"   Std: {summary['statistics']['s11_min']['std']:.2f} dB")
    
    return output_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        training_dir = sys.argv[1]
    else:
        training_dir = "data/em_results/training_20251223_212251"
    
    create_summary(training_dir)

