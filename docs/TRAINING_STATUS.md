# Training Status

## Current Training Run

Training with OpenEMS has been started in the background.

### Configuration
- **Samples**: 1 (test run)
- **Solver**: OpenEMS
- **Frequency Band**: 2.4 GHz
- **Status**: Running in background

### Monitoring Progress

To check the training progress:

```bash
# View the log file
tail -f /tmp/training_test.log

# Or check the results directory
ls -lht "/Users/pratikkumar/Desktop/Antenna Digital Twin/backend/data/em_results/" | head -10
```

### Expected Duration

**Important**: Real EM simulations take significantly longer than mock data:
- **Single simulation**: 5-30 minutes (depending on mesh size and complexity)
- **100 simulations**: Several hours to days

For production training with 100 samples, expect:
- **Minimum**: 8-10 hours
- **Typical**: 1-2 days
- **Maximum**: Several days (if simulations are complex)

### Running Full Training

Once you've verified the test run works, start full training:

```bash
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin/backend"
export PATH="$HOME/openems/bin:$PATH"
PYTHONPATH=/Users/pratikkumar/Desktop/Antenna\ Digital\ Twin python3 scripts/train_surrogate_model.py --samples 100 --solver openems --frequency 2.4ghz
```

**Recommendation**: Run this in a `screen` or `tmux` session so it can continue if you disconnect:

```bash
# Using screen
screen -S training
# Then run the training command
# Press Ctrl+A then D to detach
# Reattach with: screen -r training

# Using tmux
tmux new -s training
# Then run the training command
# Press Ctrl+B then D to detach
# Reattach with: tmux attach -t training
```

### Troubleshooting

If simulations fail:
1. Check Octave is working: `octave --version`
2. Check OpenEMS is in PATH: `which openEMS`
3. Check simulation logs in: `backend/data/em_results/training_*/sim_*/`

### Results Location

- **Simulation results**: `backend/data/em_results/training_YYYYMMDD_HHMMSS/`
- **Trained models**: `backend/data/ml_models/`
- **Training logs**: `/tmp/training_test.log` (or check terminal output)
















