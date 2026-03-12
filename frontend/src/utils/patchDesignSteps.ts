/**
 * Frontend replica of patch design formulas (matches backend/em_solver/patch_design.py).
 * Returns steps with LaTeX formulas and values for the Calculation panel.
 */

import type { CalculationDetails } from '../services/state';

const C0 = 2.99792458e8; // m/s

export function getPatchDesignSteps(
  resonanceFrequencyHz: number,
  relativePermittivity: number,
  lossTangent: number,
  thicknessM: number,
  resultGeometry?: { length: number; width: number; height: number; feed_x: number; feed_y: number }
): CalculationDetails {
  const f0 = resonanceFrequencyHz;
  const er = relativePermittivity;
  const h = thicknessM;
  const f0GHz = (f0 / 1e9).toFixed(3);
  const hMm = (h * 1000).toFixed(3);

  const w = (C0 / (2 * f0)) * Math.sqrt(2 / (er + 1));
  const eeff = w > 0 && h > 0
    ? (er + 1) / 2 + ((er - 1) / 2) * 1 / Math.sqrt(1 + 12 * h / w)
    : (er + 1) / 2;
  const dL = h > 0 && (eeff - 0.258) !== 0 && (w / h + 0.8) !== 0
    ? 0.412 * h * ((eeff + 0.3) * (w / h + 0.264)) / ((eeff - 0.258) * (w / h + 0.8))
    : 0;
  const l = (C0 / (2 * f0 * Math.sqrt(eeff))) - 2 * dL;
  let feedX = l / 2 + (-5e-3);
  let feedY = w / 2;
  feedX = Math.max(1e-4, Math.min(l - 1e-4, feedX));
  feedY = Math.max(1e-4, Math.min(w - 1e-4, feedY));

  const wMm = (w * 1000).toFixed(4);
  const lMm = (l * 1000).toFixed(4);
  const feedXMm = (feedX * 1000).toFixed(2);
  const feedYMm = (feedY * 1000).toFixed(2);
  const eeffVal = eeff.toFixed(4);
  const dLMm = (dL * 1000).toFixed(4);

  const steps = [
    {
      name: 'W',
      formula: 'W = \\frac{c_0}{2 f_0} \\sqrt{\\frac{2}{\\varepsilon_r + 1}}',
      value: wMm,
      unit: 'mm',
    },
    {
      name: '\\varepsilon_{\\mathrm{eff}}',
      formula: '\\varepsilon_{\\mathrm{eff}} = \\frac{\\varepsilon_r+1}{2} + \\frac{\\varepsilon_r-1}{2} \\frac{1}{\\sqrt{1+12h/W}}',
      value: eeffVal,
      unit: '—',
    },
    {
      name: '\\Delta L',
      formula: '\\Delta L = 0.412h \\frac{(\\varepsilon_{\\mathrm{eff}}+0.3)(W/h+0.264)}{(\\varepsilon_{\\mathrm{eff}}-0.258)(W/h+0.8)}',
      value: dLMm,
      unit: 'mm',
    },
    {
      name: 'L',
      formula: 'L = \\frac{c_0}{2 f_0 \\sqrt{\\varepsilon_{\\mathrm{eff}}}} - 2\\Delta L',
      value: lMm,
      unit: 'mm',
    },
    {
      name: 'Feed',
      formula: '\\text{feed}_x = L/2 - 5\\,\\mathrm{mm},\\quad \\text{feed}_y = W/2',
      value: `(${feedXMm}, ${feedYMm})`,
      unit: 'mm',
    },
  ];

  const geom = resultGeometry ?? { length: l, width: w, height: h, feed_x: feedX, feed_y: feedY };

  return {
    type: 'design',
    title: 'Patch design from resonance',
    inputs: [
      { label: 'f_0', value: f0GHz, unit: 'GHz' },
      { label: '\\varepsilon_r', value: String(relativePermittivity), unit: '—' },
      { label: '\\tan\\delta', value: String(lossTangent), unit: '—' },
      { label: 'h', value: hMm, unit: 'mm' },
    ],
    steps,
    output: [
      { label: 'L', value: (geom.length * 1000).toFixed(2), unit: 'mm' },
      { label: 'W', value: (geom.width * 1000).toFixed(2), unit: 'mm' },
      { label: 'h', value: (geom.height * 1000).toFixed(2), unit: 'mm' },
      { label: 'Feed (x, y)', value: `(${(geom.feed_x * 1000).toFixed(2)}, ${(geom.feed_y * 1000).toFixed(2)})`, unit: 'mm' },
    ],
  };
}
