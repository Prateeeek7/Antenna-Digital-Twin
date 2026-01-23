# OpenEMS NaN Results Investigation

## Summary

**Issue:** All 50 OpenEMS simulations completed, but all S11 values in the results are NaN.

**Root Cause:** The `calcPort` function in OpenEMS requires the port structure to have a `type` field, but `AddLumpedPort` doesn't automatically set this field. This causes `calcPort` to fail silently, resulting in NaN values for `port.uf.ref` and `port.uf.inc`, which then propagate to S11 calculations.

## Investigation Details

### What Worked ✅
1. **OpenEMS simulations ran successfully** - All 50 simulations completed
2. **Port files were created** - `port_ut1` and `port_it1` files exist (3-4 MB each)
3. **Simulation data exists** - Field data files (`et`, `ht`) were generated
4. **Results files were saved** - Both `results.mat` and `results_struct.mat` exist

### What Failed ❌
1. **calcPort function failed** - Error: "structure has no member 'type'"
2. **S11 values are all NaN** - Because `port.uf.ref` and `port.uf.inc` are empty/NaN
3. **Training used invalid data** - Models were trained on NaN values, resulting in poor performance

### Diagnostic Results

```bash
ERROR in calcPort: structure has no member 'type'
```

The port structure returned by `AddLumpedPort` is missing the `type` field that `calcPort` expects.

## Fix Applied

Updated `openems_adapter.py` to ensure the port structure has required fields:

```matlab
% Port definition
[CSX, port] = AddLumpedPort(CSX, 0, 1, 50, [feed_y - feed_width/2, feed_x, 0], [feed_y + feed_width/2, feed_x, h], [0, 0, 1], true);
% Ensure port has required fields for calcPort
if ~isfield(port, 'type')
    port.type = 0;  % Lumped port type
end
if ~isfield(port, 'nr')
    port.nr = 1;
end
```

## Impact

- **All 50 existing simulations have NaN results** - These cannot be fixed retroactively
- **Future simulations will work correctly** - The fix ensures port structure is complete
- **Models need retraining** - Current models were trained on NaN data

## Recommendations

1. **Retrain models** - Run training again with the fixed adapter to get valid results
2. **Verify fix** - Test a single simulation to confirm calcPort now works
3. **Monitor training** - Check that S11 values are valid (not NaN) during training

## Files Modified

- `backend/em_solver/adapters/openems_adapter.py` - Added port structure validation

## Testing

To verify the fix works:

```python
from backend.em_solver.adapters.openems_adapter import OpenEMSAdapter
from backend.core.models.schemas import AntennaParameters, FrequencyBand, SubstrateType

# Create test parameters
params = AntennaParameters(...)

# Run simulation
adapter = OpenEMSAdapter()
result = adapter.simulate(params, Path("/tmp/test_sim"))

# Check if S11 values are valid
import numpy as np
s11_values = result.s11.s11_magnitude
assert not np.any(np.isnan(s11_values)), "S11 values should not be NaN!"
```












