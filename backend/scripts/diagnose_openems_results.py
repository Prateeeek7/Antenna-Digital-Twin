#!/usr/bin/env python3
"""Diagnose why OpenEMS results are NaN."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import tempfile
import scipy.io
import numpy as np

# Test with one simulation
sim_dir = Path('data/em_results/training_20251223_212251/sim_0000_ebca94ed')
sim_data_dir = sim_dir / 'data/em_results/training_20251223_212251/sim_0000_ebca94ed'

print("🔍 Diagnosing OpenEMS Results")
print("=" * 60)

# Check if port files exist
port_files = list(sim_data_dir.glob('port_*'))
print(f"\n✅ Port files found: {len(port_files)}")
for f in port_files:
    print(f"   {f.name}: {f.stat().st_size / 1024 / 1024:.2f} MB")

# Try to manually run calcPort in Octave
print("\n🧪 Testing calcPort manually...")

test_script = f"""
addpath('/Users/pratikkumar/openems/share/openEMS/matlab');
addpath('/Users/pratikkumar/openems/share/CSXCAD/matlab');
physical_constants;

% Load the simulation directory
Sim_Path = '{sim_data_dir}';
freq = linspace(2e9, 3e9, 201);

% Try to create a port structure and call calcPort
% First, check if port files exist
if exist([Sim_Path '/port_ut1'], 'file') && exist([Sim_Path '/port_it1'], 'file')
    fprintf('Port files found\\n');
    
    % Create a minimal port structure
    port = struct();
    port.nr = 1;
    
    try
        % Try calcPort
        port = calcPort(port, Sim_Path, freq, 'RefImpedance', 50);
        
        % Check if we got valid data
        if isfield(port, 'uf') && isfield(port.uf, 'ref') && isfield(port.uf, 'inc')
            ref = port.uf.ref;
            inc = port.uf.inc;
            
            fprintf('calcPort succeeded\\n');
            fprintf('ref size: %s\\n', mat2str(size(ref)));
            fprintf('inc size: %s\\n', mat2str(size(inc)));
            
            if length(ref) > 0 && length(inc) > 0
                s11 = ref ./ inc;
                s11_db = 20*log10(abs(s11));
                fprintf('S11 sample (first 5):\\n');
                fprintf('  %s\\n', mat2str(s11_db(1:min(5, length(s11_db)))));
                
                % Check for NaN
                nan_count = sum(isnan(s11_db));
                fprintf('NaN count: %d / %d\\n', nan_count, length(s11_db));
            else
                fprintf('ERROR: ref or inc is empty\\n');
            end
        else
            fprintf('ERROR: port.uf structure missing\\n');
        end
    catch err
        fprintf('ERROR in calcPort: %s\\n', err.message);
        fprintf('Stack trace:\\n');
        for i = 1:length(err.stack)
            fprintf('  %s\\n', err.stack(i).name);
        end
    end
else
    fprintf('ERROR: Port files not found\\n');
end
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.m', delete=False) as f:
    f.write(test_script)
    test_file = f.name

try:
    result = subprocess.run(
        ['octave', '--no-gui', test_file],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print("\n📊 Octave Output:")
    print(result.stdout)
    
    if result.stderr:
        print("\n⚠️  Octave Errors:")
        print(result.stderr)
        
except Exception as e:
    print(f"\n❌ Error running test: {e}")

finally:
    Path(test_file).unlink()












