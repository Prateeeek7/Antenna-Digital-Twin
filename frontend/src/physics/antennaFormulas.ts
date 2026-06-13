/**
 * Classical closed-form antenna relations (free-space / textbook approximations).
 * For design guidance — not a substitute for full EM simulation.
 */

export const C0 = 2.99792458e8;

/** Reflection coefficient and |S11| (dB) for a load Z = R + jX vs reference Z0 (real). */
export function s11FromImpedance(Zr: number, Zi: number, Z0: number) {
  const denom = (Zr + Z0) ** 2 + Zi ** 2;
  if (denom <= 0 || !Number.isFinite(denom)) {
    return { gammaMag: NaN, s11Db: NaN };
  }
  const gr = ((Zr - Z0) * (Zr + Z0) + Zi * Zi) / denom;
  const gi = (2 * Zi * Z0) / denom;
  const gammaMag = Math.sqrt(gr * gr + gi * gi);
  const s11Db = 20 * Math.log10(Math.max(gammaMag, 1e-30));
  return { gammaMag, s11Db };
}

/** Half-wave dipole: thin-wire length scaling (end effect). k ≈ 0.95 typical. */
export function dipoleHalfWaveLengthM(fHz: number, velocityFactor = 0.95) {
  if (fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  return (velocityFactor * lambda) / 2;
}

export function dipoleFreqFromHalfWaveLength(lengthM: number, velocityFactor = 0.95) {
  if (lengthM <= 0) return NaN;
  return (C0 * velocityFactor) / (2 * lengthM);
}

/** Thin λ/2 dipole resonant resistance (free space), ~73 Ω. */
export const DIPOLE_RIN_HALF_WAVE = 73.13;

/** Quarter-wave monopole over perfect ground image theory: R_in ≈ half of dipole. */
export const MONOPOLE_RIN_QUARTER_WAVE = DIPOLE_RIN_HALF_WAVE / 2;

/** Small loop: radiation resistance R_rad ≈ 320 π⁴ (A/λ²)² (A = loop area, SI). */
export function smallLoopRadiationResistance(areaM2: number, fHz: number) {
  if (areaM2 <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  const aOverL = areaM2 / (lambda * lambda);
  return 320 * Math.PI ** 4 * aOverL ** 2;
}

/** Circular loop circumference for first resonance (order-of-magnitude, thin wire in air). */
export function circularLoopFirstResonanceCircumferenceM(fHz: number) {
  if (fHz <= 0) return NaN;
  return C0 / fHz;
}

/** Pyramidal / conical horn: aperture gain G ≈ 4π ε_ap A / λ² (linear). */
export function hornGainLinear(apertureAreaM2: number, fHz: number, apertureEfficiency = 0.55) {
  if (apertureAreaM2 <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  return (4 * Math.PI * apertureEfficiency * apertureAreaM2) / (lambda * lambda);
}

export function hornGainDbi(apertureAreaM2: number, fHz: number, apertureEfficiency = 0.55) {
  const g = hornGainLinear(apertureAreaM2, fHz, apertureEfficiency);
  if (!Number.isFinite(g) || g <= 0) return NaN;
  return 10 * Math.log10(g);
}

/** Parabolic reflector (same aperture formula). */
export function parabolicGainDbi(diameterM: number, fHz: number, apertureEfficiency = 0.55) {
  if (diameterM <= 0 || fHz <= 0) return NaN;
  const a = (Math.PI * diameterM * diameterM) / 4;
  return hornGainDbi(a, fHz, apertureEfficiency);
}

/** Axial-mode helix (Kraus): circumference ≈ λ, pitch α ≈ 12–14°, N turns. */
export function helixAxialCircumferenceM(fHz: number) {
  if (fHz <= 0) return NaN;
  return C0 / fHz;
}

/** Kraus: directivity D ≈ 15 (C/λ)² N (S/λ), S = axial spacing between turns. */
export function helixAxialGainEstimate(
  nTurns: number,
  pitchDeg: number,
  circumferenceM: number,
  fHz: number
) {
  if (nTurns <= 0 || fHz <= 0 || circumferenceM <= 0) return NaN;
  const lambda = C0 / fHz;
  const p = (pitchDeg * Math.PI) / 180;
  const spacingM = circumferenceM * Math.tan(p);
  const cL = circumferenceM / lambda;
  const sL = spacingM / lambda;
  const d0 = 15 * cL * cL * nTurns * sL;
  if (d0 <= 0) return NaN;
  return 10 * Math.log10(d0);
}

/** Half-wave slot in infinite ground: length ≈ λ/2 (first resonance, air side). */
export function slotHalfWaveLengthM(fHz: number) {
  if (fHz <= 0) return NaN;
  return C0 / (2 * fHz);
}

/**
 * Booker's relation (complementary antennas): Z_slot Z_dipole ≈ η₀²/4 in free space.
 * η₀ ≈ 377 Ω → if thin half-wave dipole Z_d ≈ 73 Ω, then Z_slot ≈ 377²/(4·73).
 */
export function bookerComplementarySlotZinApprox(dipoleZReal = DIPOLE_RIN_HALF_WAVE) {
  const eta = 377;
  return (eta * eta) / (4 * Math.max(dipoleZReal, 1e-9));
}
