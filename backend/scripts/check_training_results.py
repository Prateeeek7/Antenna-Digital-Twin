#!/usr/bin/env python3
"""Check if training results have valid S11 values."""

import scipy.io
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Find the latest training directory
training_dirs = sorted(Path('data/em_results').glob('training_*'))
if training_dirs:
    latest_dir = training_dirs[-1]
    print(f"📁 Latest training directory: {latest_dir.name}")
    
    # Find first simulation
    sim_dirs = sorted([d for d in latest_dir.iterdir() if d.is_dir() and d.name.startswith('sim_')])
    if sim_dirs:
        sim_dir = sim_dirs[0]
        print(f"🔍 Checking: {sim_dir.name}")
        
        # Look for results_struct.mat
        results_files = list(sim_dir.rglob('results_struct.mat'))
        if results_files:
            try:
                mat_data = scipy.io.loadmat(str(results_files[0]), struct_as_record=False, squeeze_me=True)
                if 'results' in mat_data:
                    results = mat_data['results']
                    if hasattr(results, 's11_magnitude'):
                        s11 = results.s11_magnitude
                        valid_count = np.sum(~np.isnan(s11))
                        total_count = len(s11) if hasattr(s11, '__len__') else 1
                        
                        print(f"\n📊 S11 Results:")
                        print(f"   Total data points: {total_count}")
                        print(f"   Valid (non-NaN): {valid_count}")
                        print(f"   NaN count: {total_count - valid_count}")
                        
                        if valid_count > 0:
                            s11_valid = s11[~np.isnan(s11)]
                            print(f"   ✅ SUCCESS! Valid S11 values found!")
                            print(f"   Min S11: {np.min(s11_valid):.2f} dB")
                            print(f"   Max S11: {np.max(s11_valid):.2f} dB")
                            print(f"   Mean S11: {np.mean(s11_valid):.2f} dB")
                        else:
                            print(f"   ❌ Still NaN - fix may not be working")
                    else:
                        print("   ⚠️  No s11_magnitude in results")
                else:
                    print("   ⚠️  No results in mat file")
            except Exception as e:
                print(f"   ❌ Error reading results: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("   ⏳ Simulation still running (no results file yet)")
    else:
        print("   ⏳ No simulations started yet")
else:
    print("   ⏳ No training directory found yet")

