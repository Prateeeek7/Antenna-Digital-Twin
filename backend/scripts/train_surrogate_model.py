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
from backend.core.models.schemas import (
    FrequencyBand,
    SubstrateType,
    AntennaParameters,
    AntennaGeometry,
    SubstrateProperties,
    EMSimulationResult,
    S11Data,
)
from backend.core.config import settings
import json
import uuid
import csv
from datetime import datetime
from typing import Optional


def load_training_data_from_csv(
    csv_path: Path,
    frequency_range: tuple[float, float] = (2.0e9, 3.0e9),
) -> tuple[list[AntennaParameters], list[EMSimulationResult]]:
    """
    Load training data from Simulation_Data.csv using all design and output columns.

    Design parameters (all used as model inputs):
      Length, Width, Height (mm), Feed_X_mm, substrate_epsR, substrate_loss_tan.
    feed_y is set to Width/2 (center); CSV has no Feed_Y column.
    All lengths in CSV are mm; converted to meters for schemas.

    Output columns used for targets: Gain_dBi, Efficiency, S11_min_dB.
    Other outputs stored in metadata: S11_max_dB, Resonance_Frequency_GHz,
    Min_S11_dB, Min_S11_freq_GHz, run_id, Simulation_Method, S11_points.
    Rows with non-empty "error" are skipped.
    """
    parameters = []
    results = []
    f_min, f_max = frequency_range

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip failed runs if error column is present and non-empty
            if row.get("error", "").strip():
                continue
            try:
                length_mm = float(row["Length"])
                width_mm = float(row["Width"])
                height_mm = float(row["Height"])
                feed_x_mm = float(row["Feed_X_mm"])
                eps_r = float(row["substrate_epsR"])
                loss_tan = float(row["substrate_loss_tan"])
                gain_dbi = float(row["Gain_dBi"])
                efficiency = float(row["Efficiency"])
                s11_min_db = float(row["S11_min_dB"])
            except (KeyError, ValueError):
                continue

            # All 6 design parameters from CSV → geometry + substrate (feed_y = Width/2)
            length_m = length_mm / 1000.0
            width_m = width_mm / 1000.0
            height_m = height_mm / 1000.0
            feed_x_m = (length_mm / 2.0 + feed_x_mm) / 1000.0
            feed_x_m = max(0.0, min(length_m, feed_x_m))
            feed_y_m = width_m / 2.0

            geom = AntennaGeometry(
                length=length_m,
                width=width_m,
                height=height_m,
                feed_x=feed_x_m,
                feed_y=feed_y_m,
            )
            substrate = SubstrateProperties(
                substrate_type=SubstrateType.FR4,
                relative_permittivity=eps_r,
                loss_tangent=loss_tan,
                thickness=height_m,
            )
            params = AntennaParameters(
                geometry=geom,
                substrate=substrate,
                frequency_band=FrequencyBand.BAND_24GHZ,
                frequency_range=(f_min, f_max),
            )
            parameters.append(params)

            # Use all CSV output columns: resonance freq for S11 curve; rest in metadata
            freq_ghz = float(row.get("Resonance_Frequency_GHz", 2.45))
            freq_hz = freq_ghz * 1e9
            s11_data = S11Data(
                frequency=[f_min, freq_hz, f_max],
                s11_magnitude=[s11_min_db + 5, s11_min_db, s11_min_db + 5],
                s11_phase=None,
            )
            metadata = {
                "source": "Simulation_Data.csv",
                "run_id": row.get("run_id", ""),
                "S11_max_dB": _safe_float(row, "S11_max_dB"),
                "Resonance_Frequency_GHz": freq_ghz,
                "Min_S11_dB": _safe_float(row, "Min_S11_dB"),
                "Min_S11_freq_GHz": _safe_float(row, "Min_S11_freq_GHz"),
                "Simulation_Method": row.get("Simulation_Method", ""),
                "S11_points": row.get("S11_points", ""),
            }
            result = EMSimulationResult(
                simulation_id=str(uuid.uuid4()),
                antenna_parameters=params,
                s11=s11_data,
                gain=gain_dbi,
                efficiency=efficiency,
                solver_name="FDTD (CSV)",
                solver_version="1.0",
                simulation_time=0.0,
                metadata=metadata,
            )
            results.append(result)

    return parameters, results


def _safe_float(row: dict, key: str) -> Optional[float]:
    """Return row[key] as float or None if missing/invalid."""
    try:
        return float(row[key])
    except (KeyError, ValueError, TypeError):
        return None


def cleanup_previous_data():
    """Remove all previous EM results and saved surrogate models."""
    import shutil
    # Clean EM results: both cwd-relative and backend/data/em_results (repo location)
    for em_dir in [
        settings.EM_SOLVER_RESULTS_DIR,
        Path(__file__).resolve().parent.parent / "data" / "em_results",
    ]:
        if em_dir.exists():
            for p in em_dir.iterdir():
                if p.is_file():
                    p.unlink()
                else:
                    shutil.rmtree(p, ignore_errors=True)
            print(f"Cleaned: {em_dir}")
    # Delete all .pkl models (cwd-relative and backend/models)
    for model_dir in [
        settings.ML_MODEL_DIR,
        Path(__file__).resolve().parent.parent / "models",
    ]:
        if model_dir.exists():
            removed = 0
            for p in model_dir.glob("*.pkl"):
                p.unlink()
                removed += 1
            if removed:
                print(f"Removed {removed} previous model(s) from {model_dir}")


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

    # Train accuracy predictor (twin model) on validation split
    if len(test_params) >= 10:
        print("\nTraining accuracy predictor (when to run full EM)...")
        for metric in target_metrics:
            try:
                training_pipeline.train_accuracy_predictor(
                    parameters=test_params,
                    em_results=test_results,
                    model_name=model_name,
                    metric=metric,
                )
                print(f"  Trained accuracy predictor for {metric}")
            except Exception as e:
                print(f"  Skipped accuracy predictor for {metric}: {e}")
    else:
        print("\nSkipping accuracy predictor (need at least 10 validation samples).")
    
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
    parser.add_argument(
        "--csv",
        type=str,
        nargs="?",
        const="backend/data/Simulation_Data.csv",
        default=None,
        metavar="PATH",
        help="Train from CSV file. If PATH omitted, uses backend/data/Simulation_Data.csv. Cleans previous em_results and models.",
    )
    args = parser.parse_args()

    frequency_band = FrequencyBand.BAND_24GHZ if args.frequency == "2.4ghz" else FrequencyBand.BAND_35GHZ
    frequency_range = (2.0e9, 3.0e9) if args.frequency == "2.4ghz" else (3.0e9, 4.0e9)

    print("=" * 60)
    print("Antenna Digital Twin - Surrogate Model Training")
    print("=" * 60)
    if args.csv is not None:
        csv_input = args.csv or "backend/data/Simulation_Data.csv"
        print("Mode: CSV (no EM simulation, no radiation/visualization)")
        print(f"  CSV file: {csv_input}")
        print(f"  Model name: {args.model_name}")
        print("=" * 60)
        # Clean previous data and models
        cleanup_previous_data()
        csv_input = args.csv or "backend/data/Simulation_Data.csv"
        csv_path = Path(csv_input)
        if not csv_path.is_absolute():
            # Resolve relative to project root (parent of backend/)
            root = Path(__file__).resolve().parent.parent.parent
            csv_path = root / csv_input
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        parameters, results = load_training_data_from_csv(csv_path, frequency_range=frequency_range)
        print(f"Loaded {len(parameters)} samples from {csv_path.name}")
        print("  Inputs: Length, Width, Height, Feed_X_mm, substrate_epsR, substrate_loss_tan (feed_y=Width/2)")
        print("  Targets: S11_min_dB, Gain_dBi, Efficiency (+ S11_max, Resonance_Freq, etc. in metadata)")
    else:
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
                seed=args.seed,
            )

    # Train models
    models = train_models(parameters, results, model_name=args.model_name)

    print("\n" + "=" * 60)
    print("Training completed successfully!")
    print(f"Models saved to: {settings.ML_MODEL_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

