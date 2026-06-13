/**
 * Encode dipole physical inputs into API AntennaParameters (matches backend/dipole/encoding.py).
 */

export interface DipolePhysicalInputs {
  dipoleLengthMm: number;
  wireRadiusMm: number;
  feedGapMm: number;
  f0GHz: number;
  fcGHz: number;
}

export function decodeDipolePhysicalFromGeometry(geometry: {
  length: number;
  width: number;
  height: number;
  feed_x: number;
  feed_y: number;
}) {
  const L = geometry.length;
  const W = geometry.width;
  const h = geometry.height;
  return {
    dipoleLengthMm: L * 1000,
    wireRadiusMm: (W / 2) * 1000,
    feedGapMm: h * 1000,
    f0GHz: L > 1e-12 ? (geometry.feed_x / L) * 10 : 0,
    fcGHz: W > 1e-12 ? (geometry.feed_y / W) * 5 : 0,
  };
}

export function buildDipoleAntennaApiPayload(inputs: DipolePhysicalInputs) {
  const L = inputs.dipoleLengthMm / 1000;
  const W = Math.max(1e-9, (2 * inputs.wireRadiusMm) / 1000);
  const h = Math.max(1e-9, inputs.feedGapMm / 1000);
  const f0Norm = Math.min(1, Math.max(0, inputs.f0GHz / 10));
  const fcNorm = Math.min(1, Math.max(0, inputs.fcGHz / 5));
  const feed_x = f0Norm * L;
  const feed_y = fcNorm * W;
  const f0Hz = inputs.f0GHz * 1e9;
  const fcHz = Math.max(1e8, inputs.fcGHz * 1e9);
  const fMin = Math.max(1e8, f0Hz - fcHz);
  const fMax = f0Hz + fcHz;

  return {
    geometry: {
      length: L,
      width: W,
      height: h,
      feed_x,
      feed_y,
    },
    substrate: {
      substrate_type: 'FR4',
      relative_permittivity: 1.0006,
      loss_tangent: 0,
      thickness: h,
    },
    feed_type: 'INSET',
    frequency_band: '2.4GHz',
    frequency_range: [fMin, fMax] as [number, number],
  };
}
