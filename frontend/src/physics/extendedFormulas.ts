/**
 * Additional closed-form relations for RF antenna design (textbook / empirical).
 */

import { C0, DIPOLE_RIN_HALF_WAVE, dipoleHalfWaveLengthM } from './antennaFormulas';

export { C0, DIPOLE_RIN_HALF_WAVE } from './antennaFormulas';

/** Short dipole (l ≪ λ): R_rad ≈ 80π²(l/λ)² Ω (Balanis). */
export function shortDipoleRadiationResistanceOhm(lengthM: number, fHz: number) {
  if (lengthM <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  const u = lengthM / lambda;
  return 80 * Math.PI ** 2 * u * u;
}

/** Thin half-wave folded dipole (equal diameters): Z ≈ 4 × thin dipole (~292 Ω). */
export const FOLDED_DIPOLE_RIN_APPROX = 4 * DIPOLE_RIN_HALF_WAVE;

/** Inverted-V: total wire length vs horizontal half-wave; apex half-angle θ from zenith (deg). Rough length scale. */
export function invertedVTotalWireLengthM(fHz: number, vf: number, apexHalfAngleDeg: number) {
  const Ldip = dipoleHalfWaveLengthM(fHz, vf);
  const th = (apexHalfAngleDeg * Math.PI) / 180;
  const sinT = Math.sin(th);
  if (sinT < 1e-6) return NaN;
  return Ldip / sinT;
}

/** Top-loaded monopole: physical height h < λ/4; estimate required h for resonance with top hat (C loads). h_eff ≈ λ/(4β) with β=2π/λ — use user h and show h/λ. */
export function monopoleElectricalHeightRatio(heightM: number, fHz: number) {
  if (heightM <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  return heightM / lambda;
}

/** Circular microstrip patch dominant TM₁₁ — radius a ≈ X₁₁ c / (2π f √(ε_eff)), X₁₁ = 1.841. */
export function circularPatchRadiusResonanceM(fHz: number, erEff: number) {
  if (fHz <= 0 || erEff < 1) return NaN;
  const X11 = 1.841;
  return (X11 * C0) / (2 * Math.PI * fHz * Math.sqrt(erEff));
}

/** Equilateral triangular patch (first mode, order-of): side s ≈ c/(3 f √(ε_eff)). */
export function triangularPatchSideM(fHz: number, erEff: number) {
  if (fHz <= 0 || erEff < 1) return NaN;
  return C0 / (3 * fHz * Math.sqrt(erEff));
}

/** Annular ring patch mean radius r_mean, narrow ring: rough TM₁₁ scale ~ circular with a ≈ r_mean. */
export function annularMeanRadiusFromFreqM(fHz: number, erEff: number) {
  return circularPatchRadiusResonanceM(fHz, erEff);
}

/** Yagi-Uda: very rough gain (dBi) from number of elements N (driver + reflector + directors). */
export function yagiGainEmpiricalDbi(numElements: number) {
  if (numElements < 2) return NaN;
  const n = numElements - 1;
  return 5.5 + 2.8 * Math.log10(Math.max(n, 1));
}

/** Uniform linear array broadside: peak array factor = N; gain boost vs single element ~10 log₁₀(N) (pattern only). */
export function arrayGainBroadsideDbi(numElements: number, elementGainDbi = 2.15) {
  if (numElements < 1) return NaN;
  return elementGainDbi + 10 * Math.log10(numElements);
}

/** End-fire (ordinary): spacing d=λ/4, progressive phase −90°; directivity scales ~ N (order). */
export function endfireDirectivityEstimateDbi(numElements: number) {
  if (numElements < 1) return NaN;
  return 10 * Math.log10(2 * numElements);
}

/** LPDA: bandwidth ratio B = f_max/f_min related to scale factor τ (crude): B ≈ 1/τ. */
export function lpdaBandwidthRatioFromTau(tau: number) {
  if (tau <= 0 || tau >= 1) return NaN;
  return 1 / tau;
}

/** Normal-mode helix (small): radiation resistance ~ loop + dipole mix; very rough R ≈ 20 (βA)² for electrically small. */
export function normalModeHelixRradRough(turnAreaM2: number, nTurns: number, fHz: number) {
  if (turnAreaM2 <= 0 || fHz <= 0 || nTurns <= 0) return NaN;
  const beta = (2 * Math.PI * fHz) / C0;
  const A = nTurns * turnAreaM2;
  return 20 * (beta * A) ** 2;
}

/** Archimedean spiral: lowest frequency ~ c/(2π R_max), highest ~ c/(2π R_min) (transmission-line model, order). */
export function spiralFreqBandFromRadiiM(rMinM: number, rMaxM: number) {
  if (rMinM <= 0 || rMaxM <= rMinM) return { fLowHz: NaN, fHighHz: NaN };
  const fLow = C0 / (2 * Math.PI * rMaxM);
  const fHigh = C0 / (2 * Math.PI * rMinM);
  return { fLowHz: fLow, fHighHz: fHigh };
}

/** Rhombic: leg length L, elevation; main lobe gain very rough ~ 10 log₁₀(4 L/λ) for large L. */
export function rhombicGainRoughDbi(legLengthM: number, fHz: number) {
  if (legLengthM <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  const g = 4 * (legLengthM / lambda);
  if (g <= 0) return NaN;
  return 10 * Math.log10(g);
}

/** Corner reflector (90°): aperture A, rough on-axis gain similar to aperture antenna. */
export function cornerReflectorGainDbi(apertureWidthM: number, apertureHeightM: number, fHz: number, eta = 0.5) {
  const a = apertureWidthM * apertureHeightM;
  if (a <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  const d0 = (4 * Math.PI * eta * a) / (lambda * lambda);
  return 10 * Math.log10(Math.max(d0, 1e-9));
}

/** Dielectric lens on-axis gain from aperture (same as horn). */
export { hornGainDbi as lensGainDbi } from './antennaFormulas';

/** Free-space path loss: PL = 20 log₁₀(4π d / λ). */
export function freeSpacePathLossDb(distanceM: number, fHz: number) {
  if (distanceM <= 0 || fHz <= 0) return NaN;
  const lambda = C0 / fHz;
  const x = (4 * Math.PI * distanceM) / lambda;
  return 20 * Math.log10(Math.max(x, 1e-30));
}

/** Friis (dB): P_r/P_t = G_t + G_r - PL + 20log₁₀(λ/(4π)) ... use received power ratio in dB with gains and PL. */
export function friisReceivedPowerDbm(
  ptDbm: number,
  gtDbi: number,
  grDbi: number,
  distanceM: number,
  fHz: number
) {
  const pl = freeSpacePathLossDb(distanceM, fHz);
  if (!Number.isFinite(pl)) return NaN;
  return ptDbm + gtDbi + grDbi - pl;
}

/** Discone: rough lower band edge ~ c/(4 h) with h = vertical cone height (many variants). */
export function disconeApproxLowFreqHz(coneHeightM: number) {
  if (coneHeightM <= 0) return NaN;
  return C0 / (4 * coneHeightM);
}

/** Biconical: lowest resonance order ~ λ/4 along slant height L_s. */
export function biconicalSlantQuarterWaveM(fHz: number) {
  if (fHz <= 0) return NaN;
  return C0 / (4 * fHz);
}

/** MIMO 2×2: envelope correlation from S-params magnitude (very rough upper bound |S21|²). */
export function mimoCorrelationRoughFromIsolation(s21Mag: number) {
  return s21Mag * s21Mag;
}

/** Ferrite loop: effective area scales ~ μ_eff; R_rad same small-loop with A_eff = μ_eff * A. */
export function ferriteLoopEffectiveArea(areaM2: number, muEff: number) {
  return areaM2 * Math.max(muEff, 1);
}

/** Slot on dielectric: resonant length ~ λ0/(2√(ε_eff)) for half-wave slot. */
export function slotLengthInMediumM(fHz: number, erEff: number) {
  if (fHz <= 0 || erEff < 1) return NaN;
  return C0 / (2 * fHz * Math.sqrt(erEff));
}

/** Circular slot first mode scale: circumference ~ λ. */
export function circularSlotMeanCircumferenceM(fHz: number) {
  if (fHz <= 0) return NaN;
  return C0 / fHz;
}

/** Triadic Koch curve: total polyline length vs initial segment after n iterations (×4/3 per iter). */
export function fractalKochPathMultiplier(n: number) {
  if (n < 0 || !Number.isFinite(n)) return NaN;
  return (4 / 3) ** n;
}

/** Hausdorff dimension of the triadic Koch curve: ln 4 / ln 3. */
export const KOCH_FRACTAL_DIMENSION = Math.log(4) / Math.log(3);

/**
 * Rough lowest resonance scale when a meandering path is P times longer than outer span L
 * (same footprint): f ≈ (c v_f)/(2 L P). Order-of-magnitude only.
 */
export function fractalRoughLowFreqHz(outerSpanM: number, pathMultiplier: number, velocityFactor = 1) {
  if (outerSpanM <= 0 || pathMultiplier <= 0) return NaN;
  const fRef = (C0 * velocityFactor) / (2 * outerSpanM);
  return fRef / pathMultiplier;
}

/** Maxwell–Garnett: spherical inclusions ε_i in host ε_h, volume fraction F ∈ [0,1]. */
export function maxwellGarnettEpsilonEff(epsHost: number, epsInc: number, volumeFraction: number) {
  const F = Math.max(0, Math.min(1, volumeFraction));
  const eh = epsHost;
  const ei = epsInc;
  const denom = ei + 2 * eh - F * (ei - eh);
  if (Math.abs(denom) < 1e-12) return NaN;
  const num = ei + 2 * eh + 2 * F * (ei - eh);
  return eh * (num / denom);
}

/** LC resonance (Hz) from L (H) and C (F). */
export function lcResonanceHz(L: number, C: number) {
  if (L <= 0 || C <= 0) return NaN;
  return 1 / (2 * Math.PI * Math.sqrt(L * C));
}

/** LC resonance from L in nH and C in pF → Hz. */
export function lcResonanceFromNHpF(LnH: number, CpF: number) {
  return lcResonanceHz(LnH * 1e-9, CpF * 1e-12);
}

/** Re-export dipole helpers for panels. */
export { dipoleHalfWaveLengthM, dipoleFreqFromHalfWaveLength } from './antennaFormulas';
