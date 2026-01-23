#!/usr/bin/env python3
"""
Training script for surrogate model.
Generates EM simulation data and trains surrogate models.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.em_solver.factory import EMSolverFactory
from backend.em_solver.parameter_generator import ParameterGenerator
from backend.em_solver.batch_runner import BatchRunner
from backend.rom.doe_generator import DOEGenerator
from backend.rom.sensitivity_analysis import SensitivityAnalyzer
from backend.ml_models.training_pipeline import TrainingPipeline
from backend.core.models.schemas import FrequencyBand, SubstrateType
from backend.core.config import settings
import json
from datetime import datetime


def generate_training_data(
    n_samples: int = 100,
    solver_name: str = "openems",
    frequency_band: FrequencyBand = FrequencyBand.BAND_24GHZ,
    seed: int = 42
):
    """
    Generate training data using EM simulations.
    
    Args:
        n_samples: Number of parameter sets to simulate
        solver_name: EM solver to use
        frequency_band: Target frequency band
        seed: Random seed for reproducibility
    """
    print(f"Generating {n_samples} training samples...")
    
    # Create parameter generator
    param_gen = ParameterGenerator(
        frequency_band=frequency_band,
        substrate_type=SubstrateType.FR4
    )
    
    # Create DoE generator
    doe_gen = DOEGenerator(param_gen)
    
    # Generate parameter sets using Latin Hypercube Sampling
    print("Generating parameter sets using LHS...")
    parameters = doe_gen.generate_lhs(n_samples, seed=seed)
    
    print(f"Generated {len(parameters)} parameter sets")
    
    # Create EM solver
    try:
        solver = EMSolverFactory.create_solver(solver_name)
        print(f"Using solver: {solver.get_solver_name()} v{solver.get_solver_version()}")
        print("Running real EM simulations (this will take time)...")
    except Exception as e:
        print(f"Warning: Could not create {solver_name} solver: {e}")
        print("Falling back to mock data generation...")
        print("Note: For production models, install OpenEMS or use --mock flag explicitly")
        return generate_mock_training_data(parameters, frequency_band)
    
    # Create batch runner - run in parallel (3 workers) for faster training
    # Note: --no-gui flag prevents Octave GUI windows
    batch_runner = BatchRunner(solver, max_workers=3)
    
    # Run simulations
    output_dir = settings.EM_SOLVER_RESULTS_DIR / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Running EM simulations (this may take a while)...")
    print(f"Results will be saved to: {output_dir}")
    
    def progress_callback(completed, total, result):
        if completed % 10 == 0 or completed == total:
            print(f"Progress: {completed}/{total} ({100*completed/total:.1f}%)")
    
    try:
        results = batch_runner.run_batch(
            parameters,
            output_dir,
            progress_callback=progress_callback
        )
        print(f"Completed {len(results)} simulations")
        return parameters, results
    except Exception as e:
        print(f"Error during simulation: {e}")
        print("Falling back to mock data...")
        return generate_mock_training_data(parameters, frequency_band)


def generate_mock_training_data(parameters, frequency_band):
    """
    Generate mock training data using improved analytical models.
    
    This creates more realistic data that approximates what OpenEMS would produce,
    but is much faster. For production, use real EM simulations.
    """
    print("Generating mock training data (analytical approximations)...")
    from backend.core.models.schemas import EMSimulationResult, S11Data
    import numpy as np
    import uuid
    
    results = []
    f_min, f_max = (2.0e9, 3.0e9) if frequency_band == FrequencyBand.BAND_24GHZ else (3.0e9, 4.0e9)
    f0 = (f_min + f_max) / 2
    c = 3e8  # Speed of light
    
    for i, params in enumerate(parameters):
        if (i + 1) % 20 == 0:
            print(f"  Generated {i + 1}/{len(parameters)} samples...")
        
        # Generate frequency array
        freq = np.linspace(f_min, f_max, 201)
        
        # Improved analytical model for microstrip patch antenna
        geom = params.geometry
        er = params.substrate.relative_permittivity
        h = geom.height
        
        # Effective permittivity (Hammerstad & Jensen)
        er_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * h / geom.width) ** (-0.5)
        
        # Approximate resonant frequency (transmission line model)
        # fr ≈ c / (2 * L * sqrt(er_eff))
        fr_approx = c / (2 * geom.length * np.sqrt(er_eff))
        
        # S11 calculation using simple transmission line model
        s11_mag = []
        for f in freq:
            # Normalized frequency
            fn = f / fr_approx
            
            # Simple impedance model
            # Zin ≈ Z0 * (L/W) * sqrt(er_eff) with feed position effect
            feed_factor = 1.0 + 0.1 * (params.geometry.feed_x / params.geometry.length - 0.25)
            
            # Reflection coefficient approximation
            # Better model: S11 depends on frequency detuning
            detuning = abs(fn - 1.0)
            if detuning < 0.1:
                # Near resonance
                s11_db = -15 - detuning * 50
            else:
                # Far from resonance
                s11_db = -5 - detuning * 10
            
            # Add some variation based on geometry
            s11_db += 2 * (geom.width / geom.length - 1.0)  # Aspect ratio effect
            s11_db = max(-30, min(-3, s11_db))  # Clamp to reasonable range
            
            s11_mag.append(s11_db)
        
        # Gain calculation (simplified patch antenna formula)
        # Directivity ≈ 4π * (L*W) / λ²
        lambda0 = c / f0
        directivity_db = 10 * np.log10(4 * np.pi * (geom.length * geom.width) / (lambda0 ** 2))
        gain = directivity_db * 0.85  # Assume 85% efficiency
        gain += np.random.normal(0, 0.2)  # Small variation
        
        # Efficiency (depends on substrate loss)
        tan_d = params.substrate.loss_tangent
        efficiency = 0.90 - tan_d * 10  # Rough estimate
        efficiency = max(0.7, min(0.95, efficiency + np.random.normal(0, 0.03)))
        
        result = EMSimulationResult(
            simulation_id=str(uuid.uuid4()),
            antenna_parameters=params,
            s11=S11Data(
                frequency=freq.tolist(),
                s11_magnitude=s11_mag,
                s11_phase=None
            ),
            gain=float(gain),
            efficiency=float(efficiency),
            solver_name="Mock (Analytical)",
            solver_version="1.0",
            simulation_time=0.0,
            metadata={"note": "Analytical approximation - use EM solver for production"}
        )
        results.append(result)
    
    print(f"Generated {len(results)} mock simulation results")
    return parameters, results


def train_models(parameters, results, model_name: str = "default"):
    """
    Train surrogate models on simulation data.
    
    Args:
        parameters: List of antenna parameters
        results: List of EM simulation results
        model_name: Name for the trained model
    """
    print(f"\nTraining surrogate models (model: {model_name})...")
    
    # Check if we have any successful results
    if not results or len(results) == 0:
        raise ValueError("No successful simulation results. Cannot train models. Check simulation logs for errors.")
    
    if len(results) < len(parameters):
        print(f"Warning: Only {len(results)}/{len(parameters)} simulations succeeded. Proceeding with available data.")
        # Align parameters with successful results
        parameters = parameters[:len(results)]
    
    # Perform sensitivity analysis
    print("Performing sensitivity analysis...")
    sensitivity_analyzer = SensitivityAnalyzer()
    
    if len(parameters) < 2:
        print(f"Warning: Only {len(parameters)} sample(s) available. Sensitivity analysis requires at least 2 samples.")
        print("Using equal weights for all parameters.")
        ranked = [("length", 1.0/6), ("width", 1.0/6), ("height", 1.0/6), 
                  ("feed_x", 1.0/6), ("feed_y", 1.0/6), ("permittivity", 1.0/6)]
    else:
        ranked = sensitivity_analyzer.rank_parameters(parameters, results, method="sobol")
    
    print("\nParameter Sensitivity Ranking:")
    for param, sensitivity in ranked:
        print(f"  {param}: {sensitivity:.3f}")
    
    # Train models
    training_pipeline = TrainingPipeline()
    
    target_metrics = ["s11_min", "gain", "efficiency"]
    
    print(f"\nTraining models for metrics: {', '.join(target_metrics)}")
    models = training_pipeline.train_ensemble(
        parameters,
        results,
        model_name=model_name,
        target_metrics=target_metrics
    )
    
    print(f"\nTrained {len(models)} models:")
    for metric, model in models.items():
        print(f"  - {metric}")
    
    # Evaluate models
    print("\nEvaluating models...")
    # Use last 20% for validation
    split_idx = int(len(parameters) * 0.8)
    test_params = parameters[split_idx:]
    test_results = results[split_idx:]
    
    for metric, model in models.items():
        metrics = training_pipeline.evaluate_model(
            model,
            test_params,
            test_results,
            metric=metric
        )
        print(f"\n{metric} Model Performance:")
        print(f"  RMSE: {metrics['rmse']:.4f}")
        print(f"  MAE: {metrics['mae']:.4f}")
        print(f"  R²: {metrics['r2']:.4f}")
    
    return models


def main():
    """Main training workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train surrogate model for antenna digital twin")
    parser.add_argument("--samples", type=int, default=100, help="Number of training samples")
    parser.add_argument("--solver", type=str, default="openems", help="EM solver name")
    parser.add_argument("--frequency", type=str, default="2.4ghz", choices=["2.4ghz", "3.5ghz"])
    parser.add_argument("--model-name", type=str, default="default", help="Model name")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no EM solver required)")
    
    args = parser.parse_args()
    
    frequency_band = FrequencyBand.BAND_24GHZ if args.frequency == "2.4ghz" else FrequencyBand.BAND_35GHZ
    
    print("=" * 60)
    print("Antenna Digital Twin - Surrogate Model Training")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Samples: {args.samples}")
    print(f"  Solver: {args.solver}")
    print(f"  Frequency Band: {args.frequency}")
    print(f"  Model Name: {args.model_name}")
    print(f"  Seed: {args.seed}")
    print(f"  Mock Data: {args.mock}")
    print("=" * 60)
    
    # Generate training data
    if args.mock:
        param_gen = ParameterGenerator(frequency_band=frequency_band)
        doe_gen = DOEGenerator(param_gen)
        parameters = doe_gen.generate_lhs(args.samples, seed=args.seed)
        parameters, results = generate_mock_training_data(parameters, frequency_band)
    else:
        parameters, results = generate_training_data(
            n_samples=args.samples,
            solver_name=args.solver,
            frequency_band=frequency_band,
            seed=args.seed
        )
    
    # Train models
    models = train_models(parameters, results, model_name=args.model_name)
    
    print("\n" + "=" * 60)
    print("Training completed successfully!")
    print(f"Models saved to: {settings.ML_MODEL_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

