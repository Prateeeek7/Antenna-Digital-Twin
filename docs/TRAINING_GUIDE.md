# Surrogate Model Training Guide

This guide explains how to train surrogate models for the Antenna Digital Twin system.

## Overview

The surrogate model training process:
1. **Generate Parameter Sets** - Design of Experiments (DoE) using Latin Hypercube Sampling
2. **Run EM Simulations** - Generate ground truth data (or use mock data)
3. **Train Models** - Train Gaussian Process and Neural Network surrogates
4. **Evaluate** - Validate model performance

## Prerequisites

### Option 1: With EM Solver (OpenEMS)
- OpenEMS installed and in PATH
- Octave installed (for OpenEMS scripts)
- Python dependencies installed

### Option 2: Mock Data (No EM Solver)
- Python dependencies only
- Uses analytical approximations for training

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Train with Mock Data (Recommended for Testing)

```bash
python scripts/train_surrogate_model.py --samples 100 --mock --model-name test_model
```

This will:
- Generate 100 parameter sets
- Create mock S11, gain, and efficiency data
- Train surrogate models
- Save models to `models/` directory

### 3. Train with EM Solver (OpenEMS)

```bash
python scripts/train_surrogate_model.py \
  --samples 50 \
  --solver openems \
  --frequency 2.4ghz \
  --model-name production_v1
```

**Note:** This requires OpenEMS and can take hours depending on sample count.

## Training Script Options

```bash
python scripts/train_surrogate_model.py --help
```

### Arguments

- `--samples N`: Number of training samples (default: 100)
  - More samples = better accuracy but longer training
  - Recommended: 50-200 for initial training
  
- `--solver NAME`: EM solver to use (default: "openems")
  - Options: "openems", "hfss", "cst"
  - Use "mock" or `--mock` flag for no solver
  
- `--frequency BAND`: Frequency band (default: "2.4ghz")
  - Options: "2.4ghz", "3.5ghz"
  
- `--model-name NAME`: Model identifier (default: "default")
  - Used for saving/loading models
  
- `--seed N`: Random seed (default: 42)
  - For reproducibility
  
- `--mock`: Use mock data instead of EM solver
  - Faster, good for testing

## Training Workflow

### Step 1: Generate Training Data

The script generates parameter sets using Latin Hypercube Sampling (LHS) to ensure good coverage of the design space.

**Parameter ranges (2.4 GHz):**
- Length: 25-35 mm
- Width: 30-45 mm
- Height: 0.8-3.2 mm
- Feed positions: Varied
- Substrate: FR-4 (εr=4.4, tan δ=0.02)

### Step 2: Run Simulations

For each parameter set:
- Create EM simulation file
- Run simulation (OpenEMS/HFSS/CST)
- Extract S11, gain, efficiency
- Store results

**Time estimate:**
- OpenEMS: ~5-10 minutes per simulation
- 100 samples: ~8-16 hours total
- Mock data: ~1 second per sample

### Step 3: Train Models

Trains three models:
1. **S11 Min Model** - Predicts minimum S11 value
2. **Gain Model** - Predicts peak gain
3. **Efficiency Model** - Predicts radiation efficiency

Each model uses:
- **Gaussian Process** - For uncertainty quantification
- **Neural Network** - For fast inference
- **Ensemble** - Combines both for best performance

### Step 4: Evaluation

Models are evaluated on a held-out test set (20% of data):
- **RMSE** - Root Mean Squared Error
- **MAE** - Mean Absolute Error
- **R²** - Coefficient of determination

## Example Training Sessions

### Quick Test (5 minutes)
```bash
python scripts/train_surrogate_model.py --samples 20 --mock --model-name quick_test
```

### Production Model (8-16 hours)
```bash
python scripts/train_surrogate_model.py \
  --samples 100 \
  --solver openems \
  --frequency 2.4ghz \
  --model-name production_2.4ghz_v1 \
  --seed 42
```

### Large Dataset (24+ hours)
```bash
python scripts/train_surrogate_model.py \
  --samples 200 \
  --solver openems \
  --frequency 2.4ghz \
  --model-name production_2.4ghz_v2
```

## Training via API

You can also start training via the API:

```bash
curl -X POST "http://localhost:8000/api/v1/training/start" \
  -H "Content-Type: application/json" \
  -d '{
    "n_samples": 50,
    "solver_name": "openems",
    "frequency_band": "2.4GHz",
    "model_name": "api_trained",
    "use_mock": false
  }'
```

Training runs in the background. Check status:
```bash
curl http://localhost:8000/api/v1/training/status
```

## Model Output

Trained models are saved to:
```
backend/models/
├── {model_name}_s11_min.pkl
├── {model_name}_gain.pkl
└── {model_name}_efficiency.pkl
```

Each model file contains:
- Trained ensemble (GP + Neural Network)
- Training metadata
- Performance metrics

## Using Trained Models

Models are automatically loaded by the inference service:

```python
from backend.ml_models.inference_service import InferenceService

service = InferenceService()
service.load_model("production_v1", "s11_min")
prediction = service.predict(antenna_parameters)
```

## Performance Targets

Good model performance:
- **S11 RMSE**: < 1.0 dB
- **Gain RMSE**: < 0.5 dBi
- **Efficiency RMSE**: < 0.05 (5%)
- **R² Score**: > 0.90

## Troubleshooting

### OpenEMS Not Found
```bash
# Install OpenEMS or use --mock flag
python scripts/train_surrogate_model.py --mock
```

### Out of Memory
- Reduce `--samples` count
- Use smaller batch size in training

### Slow Training
- Use `--mock` for faster iteration
- Reduce sample count for initial testing
- Use parallel workers (configured in batch_runner)

## Next Steps

After training:
1. Validate models on test data
2. Deploy models to production
3. Monitor prediction accuracy
4. Retrain when drift is detected

## Advanced: Custom Training

For custom training, modify `scripts/train_surrogate_model.py`:
- Change DoE method (Sobol, grid, etc.)
- Adjust model hyperparameters
- Add custom metrics
- Implement custom validation

