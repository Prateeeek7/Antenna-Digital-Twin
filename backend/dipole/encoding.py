"""Map dipole physical parameters to AntennaParameters (same encoding as dipole surrogate training)."""

from __future__ import annotations

from backend.core.models.schemas import (
    AntennaParameters,
    AntennaGeometry,
    SubstrateProperties,
    SubstrateType,
    FeedType,
    FrequencyBand,
)


def dipole_physical_to_parameters(
    dipole_length_mm: float,
    wire_radius_mm: float,
    feed_gap_mm: float,
    f0_ghz: float,
    fc_ghz: float,
) -> AntennaParameters:
    """
    Encode dipole geometry into the surrogate feature vector used at training time.

    Mapping (matches backend/scripts/train_surrogate_model.py dipole JSON loader):
      length  <- total dipole length (m)
      width   <- 2 * wire radius (m)
      height  <- feed gap (m)
      feed_x  <- (f0_GHz/10 clamped to [0,1]) * length
      feed_y  <- (fc_GHz/5 clamped to [0,1]) * width
    """
    length_m = float(dipole_length_mm) / 1000.0
    width_m = max(1e-9, (2.0 * float(wire_radius_mm)) / 1000.0)
    height_m = max(1e-9, float(feed_gap_mm)) / 1000.0

    f0_norm = max(0.0, min(1.0, float(f0_ghz) / 10.0))
    fc_norm = max(0.0, min(1.0, float(fc_ghz) / 5.0))
    feed_x_m = f0_norm * length_m
    feed_y_m = fc_norm * width_m

    f0_hz = float(f0_ghz) * 1e9
    fc_hz = max(1e8, float(fc_ghz) * 1e9)
    f_min = max(1e8, f0_hz - fc_hz)
    f_max = f0_hz + fc_hz

    geom = AntennaGeometry(
        length=length_m,
        width=width_m,
        height=height_m,
        feed_x=feed_x_m,
        feed_y=feed_y_m,
    )
    substrate = SubstrateProperties(
        substrate_type=SubstrateType.FR4,
        relative_permittivity=1.0006,
        loss_tangent=0.0,
        thickness=height_m,
    )
    return AntennaParameters(
        geometry=geom,
        substrate=substrate,
        feed_type=FeedType.INSET,
        frequency_band=FrequencyBand.BAND_24GHZ,
        frequency_range=(f_min, f_max),
    )


def decode_dipole_physical_from_parameters(params: AntennaParameters) -> dict:
    """Inverse of dipole_physical_to_parameters for UI / metadata display."""
    g = params.geometry
    L = g.length
    W = g.width
    h = g.height
    f0_ghz = (g.feed_x / L) * 10.0 if L > 1e-12 else 0.0
    fc_ghz = (g.feed_y / W) * 5.0 if W > 1e-12 else 0.0
    return {
        "dipole_length_mm": L * 1000.0,
        "wire_radius_mm": (W / 2.0) * 1000.0,
        "feed_gap_mm": h * 1000.0,
        "f0_GHz": f0_ghz,
        "fc_GHz": fc_ghz,
    }
