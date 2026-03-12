"""Microstrip rectangular patch antenna design from target resonance and substrate."""

import math
from backend.core.models.schemas import (
    AntennaParameters,
    AntennaGeometry,
    SubstrateProperties,
    SubstrateType,
    FeedType,
    FrequencyBand,
)


def design_from_frequency(
    resonance_frequency_hz: float,
    relative_permittivity: float,
    loss_tangent: float,
    thickness_m: float,
) -> AntennaParameters:
    """
    Compute patch dimensions and feed position for a rectangular microstrip patch
    at the given resonance frequency and substrate. Uses standard design formulas;
    dimensions are then validated by running the physics-based solver.

    Args:
        resonance_frequency_hz: Target resonance frequency (Hz).
        relative_permittivity: Substrate relative permittivity (εr).
        loss_tangent: Substrate loss tangent (tan δ).
        thickness_m: Substrate thickness (m).

    Returns:
        AntennaParameters with geometry and substrate for the design.
    """
    c0 = 2.99792458e8  # m/s
    f0 = float(resonance_frequency_hz)
    er = float(relative_permittivity)
    h = float(thickness_m)

    # Patch width (radiation efficiency)
    w = (c0 / (2 * f0)) * math.sqrt(2.0 / (er + 1.0))

    # Effective permittivity
    if w > 0 and h > 0:
        eeff = (er + 1) / 2.0 + (er - 1) / 2.0 * 1.0 / math.sqrt(1.0 + 12.0 * h / w)
    else:
        eeff = (er + 1) / 2.0

    # Extension length (fringing)
    if h > 0 and (eeff - 0.258) != 0 and (w / h + 0.8) != 0:
        dL = 0.412 * h * ((eeff + 0.3) * (w / h + 0.264)) / ((eeff - 0.258) * (w / h + 0.8))
    else:
        dL = 0.0

    # Patch length (resonance)
    l = (c0 / (2 * f0 * math.sqrt(eeff))) - 2.0 * dL

    # Feed position: center along width; inset from center along length (offset in mm typical -7 to -3)
    feed_x_abs = l / 2.0 + (-5.0e-3)  # -5 mm from center → absolute position
    feed_y_abs = w / 2.0
    feed_x_abs = max(1e-4, min(l - 1e-4, feed_x_abs))
    feed_y_abs = max(1e-4, min(w - 1e-4, feed_y_abs))

    # Frequency band and range from f0
    band = FrequencyBand.BAND_24GHZ if f0 < 3e9 else FrequencyBand.BAND_35GHZ
    f_min = f0 * 0.85
    f_max = f0 * 1.15
    frequency_range = (f_min, f_max)

    geom = AntennaGeometry(
        length=l,
        width=w,
        height=h,
        feed_x=feed_x_abs,
        feed_y=feed_y_abs,
    )
    sub = SubstrateProperties(
        substrate_type=SubstrateType.FR4,
        relative_permittivity=er,
        loss_tangent=loss_tangent,
        thickness=h,
    )
    return AntennaParameters(
        geometry=geom,
        substrate=sub,
        feed_type=FeedType.INSET,
        frequency_band=band,
        frequency_range=frequency_range,
    )
