"""
UCE-style spectrum loss for S11 curve matching.

Piecewise loss: L1/squared for small residuals, mixed (residual^2 + c^2)/(2c) for large,
with c = quantile of absolute residuals. See Al-Zawqari et al. (2024) UCE Antenna.
"""

from typing import List, Union
import numpy as np


def spectrum_loss(
    pred_freq: Union[List[float], np.ndarray],
    pred_s11_db: Union[List[float], np.ndarray],
    target_freq: Union[List[float], np.ndarray],
    target_s11_db: Union[List[float], np.ndarray],
    quantile: float = 0.9,
) -> float:
    """
    Compute scalar loss between predicted and target S11 spectra (in dB).

    Predictions are interpolated onto target frequency points. Uses UCE-style
    piecewise loss: squared for |residual| <= c, (r^2 + c^2)/(2c) for |r| > c,
    with c = quantile of |residuals|.

    Args:
        pred_freq: Predicted frequency points (Hz).
        pred_s11_db: Predicted S11 magnitude in dB (same length as pred_freq).
        target_freq: Target frequency points (Hz).
        target_s11_db: Target S11 magnitude in dB (same length as target_freq).
        quantile: Quantile for threshold c (0 < quantile <= 1). Default 0.9.

    Returns:
        Scalar loss (non-negative).
    """
    pred_f = np.asarray(pred_freq, dtype=float)
    pred_db = np.asarray(pred_s11_db, dtype=float)
    tgt_f = np.asarray(target_freq, dtype=float)
    tgt_db = np.asarray(target_s11_db, dtype=float)

    if pred_f.size == 0 or tgt_f.size == 0:
        return 0.0

    # Interpolate predicted S11 onto target frequency grid
    pred_db_on_target = np.interp(tgt_f, pred_f, pred_db)
    residual = tgt_db - pred_db_on_target

    # Clamp residual magnitude to avoid extreme outliers dominating
    abs_res = np.abs(residual)
    if abs_res.size == 0:
        return 0.0

    c = float(np.quantile(abs_res, min(quantile, 1.0)))
    c = max(c, 1e-9)  # avoid division by zero

    # Piecewise: |r| <= c -> |r|; |r| > c -> (r^2 + c^2) / (2*c)
    squared_part = np.where(abs_res <= c, abs_res, (residual ** 2 + c ** 2) / (2 * c))
    return float(np.sum(squared_part))
