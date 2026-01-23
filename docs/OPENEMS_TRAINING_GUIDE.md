# OpenEMS Training Guide

## Current Status

OpenEMS has been successfully installed and integrated into the training pipeline. The system is configured to run real EM simulations.

### Recent Fixes Applied

1. ✅ **OpenEMS Installation**: Successfully built and installed from source
2. ✅ **PATH Configuration**: OpenEMS added to system PATH
3. ✅ **Octave Integration**: Octave paths configured for OpenEMS and CSXCAD
4. ✅ **Script Generation**: Fixed f-string formatting for Octave cell arrays
5. ✅ **Material Creation**: Updated to use `AddMaterial` before setting properties
6. 🔄 **Testing**: Currently testing full simulation workflow

## Running Training

### Basic Command

```bash
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin/backend"
export PATH="$HOME/openems/bin:$PATH"
PYTHONPATH=/Users/pratikkumar/Desktop/Antenna\ Digital\ Twin python3 scripts/train_surrogate_model.py --samples 100 --solver openems --frequency 2.4ghz
```

### Options

- `--samples N`: Number of training samples (default: 100)
- `--solver NAME`: EM solver name (default: "openems")
- `--frequency BAND`: Frequency band - "2.4ghz" or "3.5ghz" (default: "2.4ghz")
- `--model-name NAME`: Model name for saving (default: "default")
- `--seed N`: Random seed for reproducibility (default: 42)
- `--mock`: Use mock data instead of real EM simulation (for testing)

### Expected Duration

**Real EM simulations are time-intensive:**

- **Per simulation**: 5-30 minutes (depending on mesh complexity)
- **10 samples**: ~1-5 hours
- **100 samples**: ~8-50 hours (1-2 days typical)

### Running in Background

For long training runs, use `screen` or `tmux`:

```bash
# Using screen
screen -S training
# Run training command
# Detach: Ctrl+A then D
# Reattach: screen -r training

# Using tmux  
tmux new -s training
# Run training command
# Detach: Ctrl+B then D
# Reattach: tmux attach -t training
```

## Monitoring Progress

### Check Logs

```bash
# View latest training log
tail -f /tmp/openems_training_final.log

# Or check simulation results
ls -lht "backend/data/em_results/" | head -10
```

### Check Individual Simulations

```bash
# List simulation directories
ls -la backend/data/em_results/training_*/

# Check a specific simulation
cat backend/data/em_results/training_*/sim_*/simulation.m
```

## Troubleshooting

### OpenEMS Not Found

```bash
# Verify OpenEMS is in PATH
which openEMS
openEMS --version

# If not found, add to PATH
export PATH="$HOME/openems/bin:$PATH"
```

### Octave Errors

```bash
# Verify Octave installation
octave --version

# Test OpenEMS paths
octave --eval "addpath('~/openems/share/openEMS/matlab'); addpath('~/openems/share/CSXCAD/matlab'); physical_constants;"
```

### Simulation Failures

1. Check simulation script syntax:
   ```bash
   cat backend/data/em_results/training_*/sim_*/simulation.m
   ```

2. Check Octave error messages in logs

3. Verify material properties are valid (positive values, reasonable ranges)

### Memory Issues

If simulations fail due to memory:
- Reduce mesh resolution in the script
- Use fewer frequency points
- Process simulations sequentially instead of in parallel

## Results Location

- **Simulation Results**: `backend/data/em_results/training_YYYYMMDD_HHMMSS/`
- **Trained Models**: `backend/data/ml_models/`
- **Training Logs**: Check terminal output or `/tmp/openems_training_*.log`

## Next Steps

Once training completes successfully:

1. Models will be saved to `backend/data/ml_models/`
2. You can use the trained models for fast inference
3. Compare surrogate predictions with real EM simulations
4. Iterate and improve model accuracy with more training data

## Notes

- First simulation may take longer (OpenEMS initialization)
- Each simulation creates its own directory with results
- Failed simulations are logged but don't stop the batch
- Progress is reported every 10 simulations or at completion
















