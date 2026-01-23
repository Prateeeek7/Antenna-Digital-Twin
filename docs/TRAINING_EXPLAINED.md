# Training Data Generation Explained

## Two Modes of Operation

### 1. Mock Data Mode (`--mock` flag)
**What it does:**
- Uses analytical formulas to approximate antenna behavior
- Generates data in seconds
- No EM solver required

**When to use:**
- Testing the training pipeline
- Quick iteration on model architecture
- Development and debugging

**Limitations:**
- Not physically accurate
- Simplified models
- Models trained on mock data won't work well in production

### 2. Real EM Simulation Mode (no `--mock` flag)
**What it does:**
- Runs actual EM simulations (OpenEMS/HFSS/CST)
- Generates physically accurate data
- Takes hours (5-10 min per simulation)

**When to use:**
- Production model training
- Research and validation
- When physical accuracy matters

## Why Mock Data is Fast

Mock data uses **analytical approximations**:
- Transmission line model for S11
- Simple formulas for gain/efficiency
- No numerical EM solving

Real EM simulations:
- Solve Maxwell's equations numerically
- Mesh the geometry
- Iterate to convergence
- Much more computationally expensive

## Current Training Results

Your models (`mock_100_samples_*.pkl`) were trained on:
- ✅ 100 parameter sets (good coverage)
- ⚠️ Mock/analytical data (not physically accurate)
- ✅ Models trained successfully
- ⚠️ Will need retraining with real EM data for production

## Next Steps

### Option 1: Use Mock Models for Testing
- Good for: UI testing, API testing, workflow validation
- Models work but predictions are approximate

### Option 2: Train with Real EM Data
```bash
# Install OpenEMS first, then:
python3 backend/scripts/train_surrogate_model.py \
  --samples 50 \
  --solver openems \
  --frequency 2.4ghz \
  --model-name production_v1
```
- Takes 4-8 hours for 50 samples
- Physically accurate
- Production-ready models

### Option 3: Hybrid Approach
1. Start with mock data (fast iteration)
2. Validate pipeline works
3. Train final model with real EM data (overnight)

## Performance Comparison

| Mode | Time (100 samples) | Accuracy | Use Case |
|------|-------------------|----------|----------|
| Mock | ~30 seconds | Low | Testing |
| OpenEMS | 8-16 hours | High | Production |
| HFSS | 20-40 hours | Very High | Research |

## Recommendation

For now, the mock models are perfect for:
- ✅ Testing the frontend
- ✅ Validating the API
- ✅ Demonstrating the system
- ✅ Development workflow

When ready for production:
- Train with real EM data (OpenEMS recommended)
- Use 50-100 samples minimum
- Run overnight or on a server


















