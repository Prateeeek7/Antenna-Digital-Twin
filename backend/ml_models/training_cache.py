"""Load training data (OpenEMS CSV) for nearest-neighbor blending at inference."""

import csv
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from backend.core.models.schemas import (
    AntennaParameters,
    AntennaGeometry,
    SubstrateProperties,
    FrequencyBand,
    SubstrateType,
)


def extract_features(parameters: AntennaParameters) -> np.ndarray:
    """Same 7-dim feature order as GP/ensemble: length, width, height, feed_x, feed_y, eps, tan (m/SI)."""
    g = parameters.geometry
    s = parameters.substrate
    return np.array([
        g.length,
        g.width,
        g.height,
        g.feed_x,
        g.feed_y,
        s.relative_permittivity,
        s.loss_tangent,
    ], dtype=np.float64)


def load_training_cache(csv_path: Optional[Path] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load Simulation_Data.csv into (X, y_s11, y_gain, y_eff) using the same conversion as training.
    X is (n, 7) in meters/SI; y_* are (n,) with S11_min_dB, Gain_dBi, Efficiency.
    Rows with non-empty "error" are skipped.
    """
    if csv_path is None:
        csv_path = Path(__file__).resolve().parent.parent / "data" / "Simulation_Data.csv"
    if not csv_path.exists():
        return np.zeros((0, 7)), np.array([]), np.array([]), np.array([])

    X_list = []
    y_s11 = []
    y_gain = []
    y_eff = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
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

            length_m = length_mm / 1000.0
            width_m = width_mm / 1000.0
            height_m = height_mm / 1000.0
            feed_x_m = (length_mm / 2.0 + feed_x_mm) / 1000.0
            feed_x_m = max(0.0, min(length_m, feed_x_m))
            feed_y_m = width_m / 2.0

            geom = AntennaGeometry(
                length=length_m, width=width_m, height=height_m,
                feed_x=feed_x_m, feed_y=feed_y_m,
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
                frequency_range=(2.0e9, 3.0e9),
            )
            x = extract_features(params)
            X_list.append(x)
            y_s11.append(s11_min_db)
            y_gain.append(gain_dbi)
            y_eff.append(efficiency)

    if not X_list:
        return np.zeros((0, 7)), np.array([]), np.array([]), np.array([])
    X = np.array(X_list)
    return X, np.array(y_s11), np.array(y_gain), np.array(y_eff)
