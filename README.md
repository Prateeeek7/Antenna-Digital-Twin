# Antenna Digital Twin

A comprehensive digital twin platform for single-band microstrip patch antennas, enabling real-time prediction, optimization, and closed-loop learning from measurements.

## Overview

The Antenna Digital Twin is a production-ready system that combines electromagnetic (EM) simulations, machine learning surrogates, and measurement data to create an accurate digital representation of microstrip patch antennas. The system provides:

- **Fast Predictions**: ML-based surrogate models for instant antenna performance predictions
- **Uncertainty Quantification**: Confidence intervals for all predictions
- **Closed-Loop Learning**: Automatic model updates from physical measurements
- **Optimization**: Geometry tuning for target performance metrics
- **3D Visualization**: Unity-based virtual twin integration

## Features

### Core Capabilities

- **EM Simulation Integration**: Support for multiple solvers (Meep FDTD, OpenEMS, HFSS, CST)
- **Surrogate Models**: Gaussian Process and Neural Network ensembles for fast inference
- **Measurement Ingestion**: Automatic parsing of VNA and chamber measurement data
- **Mechanical Modeling**: Bending, stress, and thermal expansion effects
- **Environmental Effects**: Orientation, proximity, and propagation modeling
- **Optimization Engine**: Geometry tuning for target S11, gain, and efficiency
- **Validation Layer**: EM-surrogate validation and KPI tracking

### Key Highlights

- ✅ **1000+ Training Samples**: Trained on real Meep FDTD simulations
- ✅ **Realistic Predictions**: Gain range 2.3-7.6 dBi, efficiency 49-95%
- ✅ **Production Ready**: Docker Compose setup with PostgreSQL, InfluxDB, MinIO
- ✅ **RESTful API**: FastAPI-based backend with WebSocket support
- ✅ **Modern Frontend**: React + TypeScript with engineering-grade UI

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Docker and Docker Compose (for services)
- Conda (for Meep FDTD solver)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Antenna Digital Twin"
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Meep FDTD solver** (optional, for real EM simulations)
```bash
conda create -n meep-env -c conda-forge pymeep
conda activate meep-env
```

4. **Start services with Docker Compose**
```bash
docker-compose up -d
```

5. **Install frontend dependencies**
```bash
cd frontend
npm install
```

### Running the Application

1. **Start the backend**
```bash
cd backend
python main.py
```
Backend API will be available at `http://localhost:8000`

2. **Start the frontend** (in a new terminal)
```bash
cd frontend
npm run dev
```
Frontend will be available at `http://localhost:3000`

3. **Access the API documentation**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
Antenna Digital Twin/
├── backend/                 # Python backend
│   ├── api/v1/             # REST API endpoints
│   ├── core/                # Configuration and models
│   ├── database/            # Database models and migrations
│   ├── em_solver/          # EM solver adapters
│   │   └── adapters/       # Meep, OpenEMS, HFSS, CST
│   ├── measurement/        # Measurement ingestion
│   ├── rom/                # Reduced-order modeling
│   ├── ml_models/         # Surrogate ML models
│   ├── mechanical/        # Mechanical twin
│   ├── environment/       # Environmental modeling
│   ├── learning/           # Closed-loop learning
│   ├── optimization/       # Optimization engine
│   ├── validation/        # Validation layer
│   ├── models/             # Trained model files (.pkl)
│   ├── data/               # Training data and results
│   └── scripts/            # Utility scripts
├── frontend/               # React + TypeScript frontend
│   └── src/
│       ├── components/     # UI components
│       ├── services/       # API clients
│       └── styles/         # Theme and styles
├── unity/                  # Unity 3D visualization
├── docs/                   # Documentation
├── docker-compose.yml      # Service orchestration
└── requirements.txt        # Python dependencies
```

## Training Surrogate Models

The system includes pre-trained models, but you can retrain with your own data:

### Using Meep FDTD (Recommended)

```bash
cd backend
python scripts/train_surrogate_model.py --samples 1000 --solver meep --frequency 2.4ghz
```

### Training Options

- `--samples`: Number of training samples (default: 100)
- `--solver`: EM solver to use (`meep`, `openems`)
- `--frequency`: Frequency band (`2.4ghz`, `3.5ghz`)
- `--model-name`: Model name for saving (default: `default`)

### Current Models

The system includes models trained on 1000 Meep FDTD simulations:
- **Gain Model**: Predicts antenna gain (2.3-7.6 dBi range)
- **Efficiency Model**: Predicts radiation efficiency (49-95% range)
- **S11_min Model**: Predicts minimum reflection coefficient (-40 to -1 dB)

## API Usage

### Predict Antenna Performance

```python
import requests

# Define antenna parameters
params = {
    "geometry": {
        "length": 0.030,  # meters
        "width": 0.040,   # meters
        "height": 0.0016, # meters
        "feed_x": 0.25,   # fraction of length
        "feed_y": 0.5     # fraction of width
    },
    "substrate": {
        "relative_permittivity": 4.4,
        "loss_tangent": 0.02
    },
    "frequency_band": "BAND_24GHZ"
}

# Get predictions
response = requests.post(
    "http://localhost:8000/api/v1/prediction/predict",
    json=params
)
result = response.json()

print(f"Predicted Gain: {result['gain']:.2f} dBi")
print(f"Predicted Efficiency: {result['efficiency']:.2%}")
print(f"Predicted S11_min: {result['s11_min']:.2f} dB")
```

### Run EM Simulation

```python
# Run full EM simulation (slower but more accurate)
response = requests.post(
    "http://localhost:8000/api/v1/em/simulate",
    json=params,
    params={"solver_name": "meep"}
)
simulation_result = response.json()
```

### Optimize Geometry

```python
# Optimize for target S11
optimization_params = {
    "target_metric": "s11_min",
    "target_value": -20.0,  # dB
    "constraints": {
        "length": {"min": 0.025, "max": 0.035},
        "width": {"min": 0.030, "max": 0.045}
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/optimization/optimize",
    json=optimization_params
)
optimized_params = response.json()
```

## Key Components

### EM Solvers

- **Meep FDTD**: Full FDTD simulation (recommended, requires conda)
- **OpenEMS**: Open-source FDTD solver (requires Octave)
- **HFSS**: ANSYS HFSS adapter (placeholder)
- **CST**: CST Studio Suite adapter (placeholder)

### Surrogate Models

- **Gaussian Process (GP)**: Provides uncertainty quantification
- **Neural Network (NN)**: Fast inference for real-time predictions
- **Ensemble**: Combines GP and NN for best accuracy

### Learning Engine

- **Bayesian Updates**: Incorporates measurement data
- **Drift Detection**: Monitors model performance over time
- **Auto-Retraining**: Triggers retraining when needed

## Configuration

Configuration is managed through environment variables or `.env` file:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=antenna_twin

# InfluxDB (time-series)
INFLUXDB_URL=http://localhost:8086

# MinIO/S3 (object storage)
S3_ENDPOINT=localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

## Documentation

- **Scope Definition**: `docs/scope_definition.md`
- **Training Guide**: `docs/TRAINING_GUIDE.md`
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Frontend README**: `frontend/README.md`
- **Unity README**: `unity/README.md`

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Quality

```bash
# Format code
black backend/

# Lint
flake8 backend/
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

## Performance

- **Prediction Speed**: <10ms per prediction (surrogate models)
- **Simulation Speed**: 30-60 seconds per EM simulation (Meep FDTD)
- **Training Time**: ~6-12 hours for 1000 samples (parallel execution)

## Current Status

✅ **Completed Features**:
- EM solver integration (Meep, OpenEMS)
- Surrogate model training (1000 samples)
- REST API with FastAPI
- Frontend UI (React + TypeScript)
- Docker Compose setup
- Measurement ingestion
- Optimization engine
- Closed-loop learning

🚧 **In Progress**:
- Unity 3D visualization integration
- Advanced optimization algorithms
- Multi-solver comparison


**Version**: 1.0.0  
**Last Updated**: January 2026
** - Pratik Kumar**

