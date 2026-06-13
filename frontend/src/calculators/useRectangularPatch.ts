import { useCallback, useState } from 'react';
import {
  type FrequencyUnit,
  type LengthUnit,
  frequencyToSI,
  lengthToSI,
  siToFrequency,
  siToLength,
} from '../lib/units';

const C0 = 2.99792458e8;

export type RectMode = 'frequency' | 'dimensions';

export interface RectangularPatchState {
  mode: RectMode;
  frequency: number;
  frequencyUnit: FrequencyUnit;
  width: number;
  length: number;
  height: number;
  heightUnit: LengthUnit;
  epsilonR: number;
  feedXOffset: number | null;
  feedYOffset: number | null;
}

export interface RectangularPatchResult {
  W: number;
  L: number;
  L_eff: number;
  RinAtEdge: number;
  y0_50ohm: number | null;
  G1: number;
  G12: number;
  directivityDBi: number;
}

const initialState: RectangularPatchState = {
  mode: 'frequency',
  frequency: 2.45,
  frequencyUnit: 'GHz',
  width: 30,
  length: 28,
  height: 1.6,
  heightUnit: 'mm',
  epsilonR: 4.4,
  feedXOffset: null,
  feedYOffset: null,
};

function epsEff(er: number, W: number, h: number): number {
  if (W <= 0 || h <= 0) return (er + 1) / 2;
  return (er + 1) / 2 + ((er - 1) / 2) * Math.pow(1 + (12 * h) / W, -0.5);
}

function deltaL(eeff: number, W: number, h: number): number {
  if (h <= 0 || W <= 0 || Math.abs(eeff - 0.258) < 1e-9 || Math.abs(W / h + 0.8) < 1e-9) return 0;
  return (
    0.412 *
    h *
    (((eeff + 0.3) * (W / h + 0.264)) / ((eeff - 0.258) * (W / h + 0.8)))
  );
}

function computeDerived(W: number, L: number, h: number, er: number): RectangularPatchResult {
  const eeff = epsEff(er, W, h);
  const dL = deltaL(eeff, W, h);
  const L_eff = L + 2 * dL;
  const fr = C0 / (2 * L_eff * Math.sqrt(eeff));
  const lambda0 = C0 / fr;
  const k0 = (2 * Math.PI) / lambda0;

  const RinAtEdge = 90 * ((er * er) / Math.max(er - 1, 1e-9)) * (L / W);

  let y0_50ohm: number | null = null;
  if (RinAtEdge > 50) {
    const cosv = Math.sqrt(50 / RinAtEdge);
    if (cosv >= -1 && cosv <= 1) {
      y0_50ohm = (L / Math.PI) * Math.acos(cosv);
    }
  }

  const G1 = (W / (120 * Math.PI * lambda0)) * (1 - Math.pow(k0 * h, 2) / 24);
  const G12 = G1 * 0.12 * Math.abs(Math.sin(k0 * L));

  const A = W * L;
  const D0 = (4 * Math.PI * A) / (lambda0 * lambda0);
  const directivityDBi = 10 * Math.log10(Math.max(D0, 1e-9));

  return {
    W,
    L,
    L_eff,
    RinAtEdge,
    y0_50ohm,
    G1,
    G12,
    directivityDBi,
  };
}

export function useRectangularPatch() {
  const [state, setState] = useState<RectangularPatchState>(initialState);
  const [result, setResult] = useState<RectangularPatchResult | null>(null);
  const [computedFrHz, setComputedFrHz] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const updateState = useCallback(<K extends keyof RectangularPatchState>(
    key: K,
    value: RectangularPatchState[K]
  ) => {
    setState((prev) => ({ ...prev, [key]: value }));
  }, []);

  const getLengthInUnit = useCallback(
    (meters: number, unit: LengthUnit) => siToLength(meters, unit),
    []
  );

  const getFrequencyInUnit = useCallback(
    (hz: number, unit: FrequencyUnit) => siToFrequency(hz, unit),
    []
  );

  const calculate = useCallback(() => {
    setError(null);
    const er = state.epsilonR;
    const h = lengthToSI(state.height, state.heightUnit);
    if (h <= 0 || er <= 1) {
      setError('Substrate height and εr must be valid.');
      setResult(null);
      setComputedFrHz(null);
      return;
    }

    try {
      if (state.mode === 'frequency') {
        const fr = frequencyToSI(state.frequency, state.frequencyUnit);
        if (fr <= 0) {
          setError('Resonant frequency must be positive.');
          setResult(null);
          setComputedFrHz(null);
          return;
        }
        const W = (C0 / (2 * fr)) * Math.sqrt(2 / (er + 1));
        const eeff = epsEff(er, W, h);
        const dL = deltaL(eeff, W, h);
        const L = C0 / (2 * fr * Math.sqrt(eeff)) - 2 * dL;
        if (L <= 0 || W <= 0) {
          setError('Could not compute positive patch dimensions for these inputs.');
          setResult(null);
          setComputedFrHz(null);
          return;
        }
        setComputedFrHz(null);
        setResult(computeDerived(W, L, h, er));
      } else {
        const W = lengthToSI(state.width, state.heightUnit);
        const L = lengthToSI(state.length, state.heightUnit);
        if (W <= 0 || L <= 0) {
          setError('Patch width and length must be positive.');
          setResult(null);
          setComputedFrHz(null);
          return;
        }
        const eeff = epsEff(er, W, h);
        const dL = deltaL(eeff, W, h);
        const L_eff = L + 2 * dL;
        const fr = C0 / (2 * L_eff * Math.sqrt(eeff));
        setComputedFrHz(fr);
        setResult(computeDerived(W, L, h, er));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed.');
      setResult(null);
      setComputedFrHz(null);
    }
  }, [state]);

  return {
    state,
    updateState,
    result,
    computedFrHz,
    error,
    calculate,
    getLengthInUnit,
    getFrequencyInUnit,
  };
}
