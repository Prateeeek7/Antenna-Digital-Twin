import React, { useMemo, useState } from 'react';
import { FormulaMarkdown } from '../components/common/FormulaMarkdown';
import { RectangularCalculator } from '../components/calculator/RectangularCalculator';
import { UnitInput, LengthInput } from '../components/calculator/UnitInput';
import { ResultsTable, type ResultRow } from '../components/calculator/ResultsTable';
import type { FrequencyUnit, LengthUnit } from '../lib/units';
import {
  FREQUENCY_UNITS,
  LENGTH_UNITS,
  frequencyToSI,
  lengthToSI,
  siToFrequency,
  siToLength,
} from '../lib/units';
import type { PhysicsLeaf } from './catalog';
import {
  C0,
  DIPOLE_RIN_HALF_WAVE,
  MONOPOLE_RIN_QUARTER_WAVE,
  bookerComplementarySlotZinApprox,
  circularLoopFirstResonanceCircumferenceM,
  dipoleFreqFromHalfWaveLength,
  dipoleHalfWaveLengthM,
  helixAxialGainEstimate,
  hornGainDbi,
  parabolicGainDbi,
  s11FromImpedance,
  slotHalfWaveLengthM,
  smallLoopRadiationResistance,
} from './antennaFormulas';
import {
  FOLDED_DIPOLE_RIN_APPROX,
  annularMeanRadiusFromFreqM,
  arrayGainBroadsideDbi,
  biconicalSlantQuarterWaveM,
  circularPatchRadiusResonanceM,
  cornerReflectorGainDbi,
  disconeApproxLowFreqHz,
  dipoleHalfWaveLengthM as dipoleHalfWaveLen,
  endfireDirectivityEstimateDbi,
  ferriteLoopEffectiveArea,
  freeSpacePathLossDb,
  friisReceivedPowerDbm,
  invertedVTotalWireLengthM,
  lpdaBandwidthRatioFromTau,
  mimoCorrelationRoughFromIsolation,
  monopoleElectricalHeightRatio,
  normalModeHelixRradRough,
  rhombicGainRoughDbi,
  shortDipoleRadiationResistanceOhm,
  slotLengthInMediumM,
  circularSlotMeanCircumferenceM,
  spiralFreqBandFromRadiiM,
  triangularPatchSideM,
  yagiGainEmpiricalDbi,
  fractalKochPathMultiplier,
  fractalRoughLowFreqHz,
  KOCH_FRACTAL_DIMENSION,
  maxwellGarnettEpsilonEff,
  lcResonanceFromNHpF,
} from './extendedFormulas';

function InfoPanel({ title, body }: { title: string; body: string }) {
  return (
    <section className="physics-subsection physics-info-panel">
      <h3>{title}</h3>
      <FormulaMarkdown className="physics-formula-note">{body}</FormulaMarkdown>
    </section>
  );
}

function FractalAntennaPanel() {
  const [preset, setPreset] = useState<'koch' | 'custom'>('koch');
  const [n, setN] = useState(2);
  const [customPerIter, setCustomPerIter] = useState(1.2);
  const [outer, setOuter] = useState(40);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('mm');
  const [vf, setVf] = useState(0.95);

  const pathMult = useMemo(() => {
    if (preset === 'koch') return fractalKochPathMultiplier(n);
    return customPerIter ** n;
  }, [preset, n, customPerIter]);

  const rows = useMemo((): ResultRow[] => {
    const Lm = lengthToSI(outer, lenUnit);
    if (!Number.isFinite(pathMult) || pathMult <= 0 || Lm <= 0) return [];
    const fRef = fractalRoughLowFreqHz(Lm, 1, vf);
    const fRough = fractalRoughLowFreqHz(Lm, pathMult, vf);
    if (!Number.isFinite(fRough) || fRough <= 0) return [];
    const lambda = C0 / fRough;
    const base: ResultRow[] = [
      { symbol: 'P', label: 'Path elongation (wire / outer span)', value: pathMult.toFixed(4), unit: '—' },
      {
        symbol: 'f_ref',
        label: 'Half-wave scale of outer span (straight)',
        value: siToFrequency(fRef, 'GHz'),
        unit: 'GHz',
      },
      {
        symbol: 'f_low*',
        label: 'Rough low band (÷P); verify in EM solver',
        value: siToFrequency(fRough, 'GHz'),
        unit: 'GHz',
      },
      { symbol: 'λ*', label: 'λ at f_low*', value: siToLength(lambda, lenUnit), unit: lenUnit },
    ];
    if (preset === 'koch') {
      base.splice(1, 0, {
        symbol: 'D_f',
        label: 'Koch curve dimension ln4/ln3',
        value: KOCH_FRACTAL_DIMENSION.toFixed(4),
        unit: '—',
      });
    }
    return base;
  }, [pathMult, outer, lenUnit, vf, preset]);

  return (
    <section className="physics-subsection">
      <h3>Fractal antenna</h3>
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {
          'Self-similar meanders **lengthen** the path inside a fixed footprint. Order-of-magnitude low end: $f \\approx \\dfrac{c v_f}{2 L_{\\mathrm{out}} P}$ with $P$ the path factor vs a straight trace along $L_{\\mathrm{out}}$.'
        }
      </FormulaMarkdown>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Curve model</span>
            <div className="input-row">
              <select value={preset} onChange={(e) => setPreset(e.target.value as 'koch' | 'custom')}>
                <option value="koch">Triadic Koch (×4/3 per iter)</option>
                <option value="custom">Custom × per iteration</option>
              </select>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Iterations n</span>
            <div className="input-row">
              <input type="number" min={0} step={1} value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 0)} />
            </div>
          </label>
        </div>
        {preset === 'custom' && (
          <div className="unit-input">
            <label>
              <span className="label-text">Length × per iteration</span>
              <div className="input-row">
                <input
                  type="number"
                  step={0.01}
                  min={1}
                  value={customPerIter}
                  onChange={(e) => setCustomPerIter(parseFloat(e.target.value) || 1)}
                />
              </div>
            </label>
          </div>
        )}
        <LengthInput label="Outer span L_out" value={outer} unit={lenUnit} onValueChange={setOuter} onUnitChange={setLenUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">Velocity factor v_f</span>
            <div className="input-row">
              <input type="number" step={0.01} value={vf} onChange={(e) => setVf(parseFloat(e.target.value) || 0.9)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Fractal scaling (first-order)" rows={rows} />}
    </section>
  );
}

function MetamaterialEbgPanel() {
  const [eh, setEh] = useState(2.2);
  const [ei, setEi] = useState(10);
  const [fv, setFv] = useState(0.2);
  const [LnH, setLnH] = useState(2.5);
  const [CpF, setCpF] = useState(0.5);

  const eeff = useMemo(() => maxwellGarnettEpsilonEff(eh, ei, fv), [eh, ei, fv]);
  const fLcHz = useMemo(() => lcResonanceFromNHpF(LnH, CpF), [LnH, CpF]);

  const rowsMg: ResultRow[] =
    Number.isFinite(eeff) && eeff > 0
      ? [{ symbol: 'ε_eff', label: 'Maxwell–Garnett (spherical inclusions)', value: eeff.toFixed(4), unit: '—' }]
      : [];

  const rowsLc: ResultRow[] =
    Number.isFinite(fLcHz) && fLcHz > 0
      ? [
          { symbol: 'f_0', label: 'Lumped LC resonance', value: siToFrequency(fLcHz, 'GHz'), unit: 'GHz' },
          { symbol: 'λ_0', label: 'λ at f_0', value: siToLength(C0 / fLcHz, 'mm'), unit: 'mm' },
        ]
      : [];

  return (
    <section className="physics-subsection">
      <h3>Metamaterial / EBG</h3>
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {
          '**Mixture:** Maxwell–Garnett for spheres in a host ($\\varepsilon_h$, $\\varepsilon_i$, volume fraction $F$). **Resonant element:** split-ring / ZOR-style lumped $LC$ gives $f_0 = 1/(2\\pi\\sqrt{LC})$. Bloch/FEM still needed for real dispersion.'
        }
      </FormulaMarkdown>
      <h4 className="physics-subpanel-heading">Effective permittivity (quasi-static)</h4>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">ε_h (host)</span>
            <div className="input-row">
              <input type="number" step={0.1} value={eh} onChange={(e) => setEh(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">ε_i (inclusion)</span>
            <div className="input-row">
              <input type="number" step={0.1} value={ei} onChange={(e) => setEi(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Volume fraction F</span>
            <div className="input-row">
              <input type="number" step={0.05} min={0} max={1} value={fv} onChange={(e) => setFv(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
      </div>
      {rowsMg.length > 0 && <ResultsTable title="Maxwell–Garnett" rows={rowsMg} />}

      <h4 className="physics-subpanel-heading">Lumped LC (SRR / ZOR scale)</h4>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">L</span>
            <div className="input-row">
              <input type="number" step={0.1} value={LnH} onChange={(e) => setLnH(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">nH</span>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">C</span>
            <div className="input-row">
              <input type="number" step={0.05} value={CpF} onChange={(e) => setCpF(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">pF</span>
            </div>
          </label>
        </div>
      </div>
      {rowsLc.length > 0 && <ResultsTable title="LC resonance" rows={rowsLc} />}
    </section>
  );
}

export const PhysicsPanelRouter: React.FC<{ leaf: PhysicsLeaf }> = ({ leaf }) => (
  <>
    <div className="physics-breadcrumb">
      <span className="physics-bc-cat">{leaf.categoryLabel}</span>
      <span className="physics-bc-sep">›</span>
      <span>{leaf.typeLabel}</span>
      <span className="physics-bc-sep">›</span>
      <span className="physics-bc-leaf">{leaf.subtypeLabel}</span>
    </div>
    {leaf.note && (
      <FormulaMarkdown className="physics-formula-note physics-leaf-note" inlineParagraph>
        {leaf.note}
      </FormulaMarkdown>
    )}
    <PanelBody panelId={leaf.panelId} />
  </>
);

const PanelBody: React.FC<{ panelId: string }> = ({ panelId }) => {
  switch (panelId) {
    case 'dipole-half-wave':
      return <DipoleHalfWavePanel />;
    case 'dipole-folded':
      return <DipoleFoldedPanel />;
    case 'dipole-short':
      return <DipoleShortPanel />;
    case 'dipole-inverted-v':
      return <DipoleInvertedVPanel />;
    case 'monopole-quarter':
    case 'monopole-ground-plane':
    case 'monopole-ifa':
    case 'monopole-pifa':
    case 'monopole-top-loaded':
    case 'monopole-umbrella':
      return <MonopoleVariantPanel variant={panelId} />;
    case 'loop-small':
      return <LoopSmallPanel />;
    case 'loop-large':
      return <LoopLargePanel />;
    case 'loop-ferrite':
      return <LoopFerritePanel />;
    case 'loop-shielded':
      return <LoopShieldedPanel />;
    case 'long-wire':
      return <LongWirePanel />;
    case 'beverage':
      return <BeveragePanel />;
    case 'horn-aperture':
      return <HornPanel />;
    case 'slot-rectangular':
      return <SlotRectPanel />;
    case 'slot-circular':
      return <SlotCircularPanel />;
    case 'slot-ring':
      return <SlotRingPanel />;
    case 'slot-waveguide':
      return <SlotWaveguidePanel />;
    case 'parabolic-reflector':
      return <ParabolicPanel />;
    case 'corner-reflector':
      return <CornerReflectorPanel />;
    case 'reflectarray-info':
      return (
        <InfoPanel
          title="Reflectarray"
          body="Phase-shifting elements on a flat surface approximate a parabolic phase front. Per-element reflection phase comes from patch size, delay lines, or tunable devices. Use array synthesis ($\\mathrm{AF} \\times$ element pattern) plus full-wave cell models for bandwidth and loss."
        />
      );
    case 'yagi-uda':
      return <YagiPanel folded={false} />;
    case 'yagi-folded':
      return <YagiPanel folded />;
    case 'lpda':
      return <LpdaPanel />;
    case 'phased-array':
      return <PhasedArrayPanel />;
    case 'collinear-array':
      return <CollinearPanel />;
    case 'broadside-array':
      return <BroadsidePanel />;
    case 'endfire-array':
      return <EndfirePanel />;
    case 'ms-patch-rectangular':
      return <RectangularCalculator />;
    case 'ms-patch-circular':
      return <CircularPatchPanel />;
    case 'ms-patch-triangular':
      return <TriangularPatchPanel />;
    case 'ms-patch-annular':
      return <AnnularPatchPanel />;
    case 'printed-dipole':
      return <PrintedDipolePanel />;
    case 'printed-slot':
      return <PrintedSlotPanel />;
    case 'fractal-info':
      return <FractalAntennaPanel />;
    case 'metamaterial-info':
      return <MetamaterialEbgPanel />;
    case 'helix-normal':
      return <HelixNormalPanel />;
    case 'helix-axial':
      return <HelicalAxialPanel />;
    case 'spiral-archimedean':
      return <SpiralArchimedeanPanel />;
    case 'spiral-log':
      return <SpiralLogPanel />;
    case 'v-antenna':
      return <VAntennaPanel />;
    case 'rhombic':
      return <RhombicPanel />;
    case 'lens-aperture':
      return <LensPanel />;
    case 'fi-log-periodic':
      return <FiLpPanel />;
    case 'fi-spiral':
      return <FiSpiralPanel />;
    case 'fi-sinuous':
      return (
        <InfoPanel
          title="Sinuous antenna"
          body="Multi-arm sinuous slot/dipole for dual-linear polarization over octave-scale bandwidth. Arm geometry and cavity depth set impedance and pattern — use full-wave optimization; combine with Friis / path-loss tools for system level."
        />
      );
    case 'discone':
      return <DisconePanel />;
    case 'biconical':
      return <BiconicalPanel />;
    case 'turnstile':
      return <TurnstilePanel />;
    case 'rf-link-budget':
      return <RfLinkBudgetPanel />;
    case 'mimo-correlation':
      return <MimoPanel />;
    case 'z-to-s11':
      return <S11Panel />;
    case 'rf-path-friis':
      return <PathFriisPanel />;
    default:
      return (
        <InfoPanel title="Panel" body={`Unknown panel: \`${panelId}\``} />
      );
  }
};

/* ——— Dipole family ——— */

function DipoleHalfWavePanel() {
  const [mode, setMode] = useState<'f2l' | 'l2f'>('f2l');
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [len, setLen] = useState(58);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('mm');
  const [vf, setVf] = useState(0.95);
  const [z0, setZ0] = useState(50);

  const rows = useMemo((): ResultRow[] => {
    const fHz = mode === 'f2l' ? frequencyToSI(f, fUnit) : dipoleFreqFromHalfWaveLength(lengthToSI(len, lenUnit), vf);
    const lengthM = mode === 'f2l' ? dipoleHalfWaveLengthM(frequencyToSI(f, fUnit), vf) : lengthToSI(len, lenUnit);
    if (!Number.isFinite(fHz) || fHz <= 0 || !Number.isFinite(lengthM) || lengthM <= 0) return [];
    const lambda = C0 / fHz;
    const { s11Db, gammaMag } = s11FromImpedance(DIPOLE_RIN_HALF_WAVE, 0, z0);
    return [
      { symbol: 'f_r', label: 'Resonance (half-wave)', value: siToFrequency(fHz, fUnit), unit: fUnit },
      { symbol: 'L', label: 'Total length (λ/2)', value: siToLength(lengthM, lenUnit), unit: lenUnit },
      { symbol: 'λ₀', label: 'Wavelength', value: siToLength(lambda, lenUnit), unit: lenUnit },
      { symbol: 'R_in', label: 'Thin dipole R (approx.)', value: DIPOLE_RIN_HALF_WAVE.toFixed(3), unit: 'Ω' },
      { symbol: '|Γ|', label: '|Γ| vs Z₀', value: gammaMag.toFixed(4), unit: '—' },
      { symbol: 'S11', label: '|S11|', value: s11Db.toFixed(3), unit: 'dB' },
    ];
  }, [mode, f, fUnit, len, lenUnit, vf, z0]);

  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`$L \\approx v_f \\lambda / 2$; $R_{\\mathrm{in}} \\approx 73\\,\\Omega$. Bandwidth ~ few % (thin wire); wider with fat elements or matching.`}
      </FormulaMarkdown>
      <div className="mode-toggle">
        <label className="mode-label">
          <input type="radio" checked={mode === 'f2l'} onChange={() => setMode('f2l')} />
          <span>f → L</span>
        </label>
        <label className="mode-label">
          <input type="radio" checked={mode === 'l2f'} onChange={() => setMode('l2f')} />
          <span>L → f</span>
        </label>
      </div>
      <div className="input-panel physics-input-grid">
        {mode === 'f2l' ? (
          <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        ) : (
          <LengthInput label="Total L (λ/2)" value={len} unit={lenUnit} onValueChange={setLen} onUnitChange={setLenUnit} />
        )}
        <div className="unit-input">
          <label>
            <span className="label-text">v_f</span>
            <div className="input-row">
              <input type="number" step={0.01} value={vf} onChange={(e) => setVf(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Z₀</span>
            <div className="input-row">
              <input type="number" step={1} value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 50)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Results" rows={rows} />}
    </section>
  );
}

function DipoleFoldedPanel() {
  const [z0, setZ0] = useState(75);
  const { s11Db, gammaMag } = useMemo(() => s11FromImpedance(FOLDED_DIPOLE_RIN_APPROX, 0, z0), [z0]);
  const rows: ResultRow[] = [
    { symbol: 'R_in', label: 'Approx. R at resonance (4× thin dipole)', value: FOLDED_DIPOLE_RIN_APPROX.toFixed(2), unit: 'Ω' },
    { symbol: '|Γ|', label: 'vs Z₀', value: gammaMag.toFixed(4), unit: '—' },
    { symbol: 'S11', label: '|S11|', value: s11Db.toFixed(3), unit: 'dB' },
  ];
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`Use half-wave dipole tab for length; folded raises impedance for twin-lead / 300 $\\Omega$ systems ($Z \\approx 4 Z_{\\mathrm{dip}}$).`}
      </FormulaMarkdown>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Z₀</span>
            <div className="input-row">
              <input type="number" value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 75)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
      </div>
      <ResultsTable title="Impedance match (folded dipole)" rows={rows} />
    </section>
  );
}

function DipoleShortPanel() {
  const [lenMm, setLenMm] = useState(50);
  const [f, setF] = useState(300);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const [z0, setZ0] = useState(50);
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    const l = lenMm * 1e-3;
    if (fHz <= 0 || l <= 0) return [];
    const R = shortDipoleRadiationResistanceOhm(l, fHz);
    const lambda = C0 / fHz;
    const { s11Db, gammaMag } = s11FromImpedance(R, 0, z0);
    return [
      { symbol: 'l/λ', label: 'Electrical length', value: (l / lambda).toFixed(5), unit: '—' },
      { symbol: 'R_rad', label: 'Radiation resistance', value: R.toExponential(4), unit: 'Ω' },
      { symbol: '|Γ|', label: 'vs Z₀ (X ignored)', value: gammaMag.toFixed(4), unit: '—' },
      { symbol: 'S11', label: '|S11| (R only)', value: s11Db.toFixed(3), unit: 'dB' },
    ];
  }, [lenMm, f, fUnit, z0]);

  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Strip length l</span>
            <div className="input-row">
              <input type="number" value={lenMm} onChange={(e) => setLenMm(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">mm</span>
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">Z₀</span>
            <div className="input-row">
              <input type="number" value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 50)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Short dipole (R_rad only)" rows={rows} />}
    </section>
  );
}

function DipoleInvertedVPanel() {
  const [f, setF] = useState(14.2);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const [vf, setVf] = useState(0.95);
  const [apex, setApex] = useState(45);
  const lenUnit: LengthUnit = 'm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const Lh = dipoleHalfWaveLen(fHz, vf);
    const Lw = invertedVTotalWireLengthM(fHz, vf, apex);
    const lambda = C0 / fHz;
    return [
      { symbol: 'L_h', label: 'Equivalent horizontal λ/2 span', value: siToLength(Lh, lenUnit), unit: lenUnit },
      { symbol: 'L_w', label: 'Total wire (2 sloped legs)', value: siToLength(Lw, lenUnit), unit: lenUnit },
      { symbol: 'λ₀', label: 'Wavelength', value: siToLength(lambda, lenUnit), unit: lenUnit },
    ];
  }, [f, fUnit, vf, apex]);

  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">v_f</span>
            <div className="input-row">
              <input type="number" step={0.01} value={vf} onChange={(e) => setVf(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Apex half-angle from zenith</span>
            <div className="input-row">
              <input type="number" value={apex} onChange={(e) => setApex(parseFloat(e.target.value) || 45)} />
              <span className="physics-suffix">°</span>
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Inverted-V wire length" rows={rows} />}
    </section>
  );
}

/* ——— Monopole variants ——— */

function MonopoleVariantPanel({ variant }: { variant: string }) {
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [vf, setVf] = useState(0.95);
  const [z0, setZ0] = useState(50);
  const [hMm, setHMm] = useState(30);
  const lenUnit: LengthUnit = 'mm';

  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const lambda = C0 / fHz;
    const Lq = (vf * lambda) / 4;
    const { s11Db } = s11FromImpedance(MONOPOLE_RIN_QUARTER_WAVE, 0, z0);
    const base: ResultRow[] = [
      { symbol: 'L_λ/4', label: 'Quarter-wave height', value: siToLength(Lq, lenUnit), unit: lenUnit },
      { symbol: 'λ₀', label: 'Wavelength', value: siToLength(lambda, lenUnit), unit: lenUnit },
      { symbol: 'R_in', label: 'R (PEC ground, approx.)', value: MONOPOLE_RIN_QUARTER_WAVE.toFixed(3), unit: 'Ω' },
      { symbol: 'S11', label: '|S11| vs Z₀', value: s11Db.toFixed(3), unit: 'dB' },
    ];
    if (variant === 'monopole-top-loaded' || variant === 'monopole-umbrella' || variant === 'monopole-ifa' || variant === 'monopole-pifa') {
      const h = hMm * 1e-3;
      const ratio = monopoleElectricalHeightRatio(h, fHz);
      base.push({
        symbol: 'h/λ',
        label: 'Physical height / λ (your structure)',
        value: ratio.toFixed(4),
        unit: '—',
      });
    }
    if (variant === 'monopole-ground-plane') {
      base.push({
        symbol: 'L_rad',
        label: 'Radial length (each, first order)',
        value: siToLength(Lq, lenUnit),
        unit: lenUnit,
      });
    }
    return base;
  }, [f, fUnit, vf, z0, variant, hMm]);

  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} unitOptions={FREQUENCY_UNITS} />
        <div className="unit-input">
          <label>
            <span className="label-text">v_f</span>
            <div className="input-row">
              <input type="number" step={0.01} value={vf} onChange={(e) => setVf(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Z₀</span>
            <div className="input-row">
              <input type="number" value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 50)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
        {(variant === 'monopole-top-loaded' ||
          variant === 'monopole-umbrella' ||
          variant === 'monopole-ifa' ||
          variant === 'monopole-pifa') && (
          <div className="unit-input">
            <label>
              <span className="label-text">Physical height h</span>
              <div className="input-row">
                <input type="number" value={hMm} onChange={(e) => setHMm(parseFloat(e.target.value) || 0)} />
                <span className="physics-suffix">mm</span>
              </div>
            </label>
          </div>
        )}
      </div>
      {rows.length > 0 && <ResultsTable title="Monopole metrics" rows={rows} />}
    </section>
  );
}

/* ——— Loops ——— */

function LoopSmallPanel() {
  const [area, setArea] = useState(0.01);
  const [areaUnit, setAreaUnit] = useState<'m²' | 'cm²'>('m²');
  const [f, setF] = useState(100);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    const areaM2 = areaUnit === 'm²' ? area : area * 1e-4;
    if (fHz <= 0 || areaM2 <= 0) return [];
    const Rrad = smallLoopRadiationResistance(areaM2, fHz);
    const C1 = circularLoopFirstResonanceCircumferenceM(fHz);
    const lambda = C0 / fHz;
    return [
      { symbol: 'R_rad', label: 'Radiation resistance', value: Rrad.toExponential(4), unit: 'Ω' },
      { symbol: 'C~λ', label: 'First resonance scale (circumference)', value: C1.toFixed(4), unit: 'm' },
      { symbol: 'λ₀', label: 'Wavelength', value: lambda.toFixed(4), unit: 'm' },
    ];
  }, [area, areaUnit, f, fUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Area A</span>
            <div className="input-row">
              <input type="number" step="any" value={area} onChange={(e) => setArea(parseFloat(e.target.value) || 0)} />
              <select value={areaUnit} onChange={(e) => setAreaUnit(e.target.value as 'm²' | 'cm²')}>
                <option value="m²">m²</option>
                <option value="cm²">cm²</option>
              </select>
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Small loop" rows={rows} />}
    </section>
  );
}

function LoopLargePanel() {
  const [f, setF] = useState(50);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const C = circularLoopFirstResonanceCircumferenceM(fHz);
    return [
      { symbol: 'C', label: 'Circumference ~ λ (order)', value: C.toFixed(3), unit: 'm' },
      { symbol: 'λ₀', label: 'Wavelength', value: (C0 / fHz).toFixed(3), unit: 'm' },
    ];
  }, [f, fUnit]);
  return (
    <section className="physics-subsection">
      <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      {rows.length > 0 && <ResultsTable title="Large loop (resonance scale)" rows={rows} />}
    </section>
  );
}

function LoopFerritePanel() {
  const [area, setArea] = useState(0.001);
  const [mu, setMu] = useState(40);
  const [f, setF] = useState(1);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0 || area <= 0) return [];
    const Aeff = ferriteLoopEffectiveArea(area, mu);
    const Rrad = smallLoopRadiationResistance(Aeff, fHz);
    return [
      { symbol: 'A_eff', label: 'Effective area (μ_eff·A)', value: Aeff.toExponential(4), unit: 'm²' },
      { symbol: 'R_rad', label: 'R_rad (scaled)', value: Rrad.toExponential(4), unit: 'Ω' },
    ];
  }, [area, mu, f, fUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Physical area A</span>
            <div className="input-row">
              <input type="number" value={area} onChange={(e) => setArea(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m²</span>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">μ_eff (relative)</span>
            <div className="input-row">
              <input type="number" value={mu} onChange={(e) => setMu(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Ferrite loop (first-order)" rows={rows} />}
    </section>
  );
}

function LoopShieldedPanel() {
  return (
    <InfoPanel
      title="Shielded loop"
      body="Electrostatic shield with gap preserves magnetic flux linkage. Equivalent circuit: loop inductance + shield capacitance; $R_{\\mathrm{rad}}$ still from small-loop formula on effective magnetic moment. Use small-loop calculator with physical loop area inside shield."
    />
  );
}

/* ——— Long wire ——— */

function LongWirePanel() {
  const [f, setF] = useState(7);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const [L, setL] = useState(20);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('m');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    const Lm = lengthToSI(L, lenUnit);
    if (fHz <= 0 || Lm <= 0) return [];
    const lambda = C0 / fHz;
    return [
      { symbol: 'L/λ', label: 'Wire length / wavelength', value: (Lm / lambda).toFixed(3), unit: '—' },
      { symbol: 'λ₀', label: 'Wavelength', value: siToLength(lambda, lenUnit), unit: lenUnit },
    ];
  }, [f, fUnit, L, lenUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <LengthInput label="Wire length L" value={L} unit={lenUnit} onValueChange={setL} onUnitChange={setLenUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Long wire (electrical length)" rows={rows} />}
    </section>
  );
}

function BeveragePanel() {
  const [f, setF] = useState(3.5);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const [L, setL] = useState(200);
  const lenUnit: LengthUnit = 'm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0 || L <= 0) return [];
    const lambda = C0 / fHz;
    return [
      { symbol: 'L/λ', label: 'Beverage length / λ', value: (L / lambda).toFixed(2), unit: '—' },
      { symbol: 'λ₀', label: 'Wavelength', value: lambda.toFixed(2), unit: lenUnit },
    ];
  }, [f, fUnit, L]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">Length L</span>
            <div className="input-row">
              <input type="number" value={L} onChange={(e) => setL(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m</span>
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Beverage (electrical length)" rows={rows} />}
    </section>
  );
}

/* ——— Horn, slot, parabolic, corner ——— */

function HornPanel() {
  const [a, setA] = useState(0.15);
  const [b, setB] = useState(0.11);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('m');
  const [f, setF] = useState(10);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [eta, setEta] = useState(0.55);
  const rows = useMemo((): ResultRow[] => {
    const w = lengthToSI(a, lenUnit);
    const h = lengthToSI(b, lenUnit);
    const fHz = frequencyToSI(f, fUnit);
    if (w <= 0 || h <= 0 || fHz <= 0) return [];
    const ap = w * h;
    const g = hornGainDbi(ap, fHz, eta);
    const lambda = C0 / fHz;
    return [
      { symbol: 'A_ap', label: 'Aperture', value: ap.toFixed(6), unit: 'm²' },
      { symbol: 'λ₀', label: 'λ', value: siToLength(lambda, lenUnit), unit: lenUnit },
      { symbol: 'G', label: 'Gain (dBi)', value: g.toFixed(3), unit: 'dBi' },
    ];
  }, [a, b, lenUnit, f, fUnit, eta]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <LengthInput label="Aperture a" value={a} unit={lenUnit} onValueChange={setA} onUnitChange={setLenUnit} />
        <LengthInput label="Aperture b" value={b} unit={lenUnit} onValueChange={setB} onUnitChange={setLenUnit} />
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_ap</span>
            <div className="input-row">
              <input type="number" step={0.05} value={eta} onChange={(e) => setEta(parseFloat(e.target.value) || 0.55)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Horn / aperture" rows={rows} />}
    </section>
  );
}

function SlotRectPanel() {
  const [f, setF] = useState(10);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [er, setEr] = useState(1);
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const Lair = slotHalfWaveLengthM(fHz);
    const Lmed = slotLengthInMediumM(fHz, Math.max(er, 1));
    const Zs = bookerComplementarySlotZinApprox();
    return [
      { symbol: 'L', label: 'Half-wave slot (air)', value: siToLength(Lair, lenUnit), unit: lenUnit },
      { symbol: 'L_ε', label: 'Half-wave in medium (√ε_eff)', value: siToLength(Lmed, lenUnit), unit: lenUnit },
      { symbol: 'Z_slot', label: 'Booker order (complement ~73 Ω dipole)', value: Zs.toFixed(1), unit: 'Ω' },
    ];
  }, [f, fUnit, er]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_eff (substrate, 1=air)</span>
            <div className="input-row">
              <input type="number" step={0.1} value={er} onChange={(e) => setEr(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Rectangular slot" rows={rows} />}
    </section>
  );
}

function SlotCircularPanel() {
  const [f, setF] = useState(5);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const C = circularSlotMeanCircumferenceM(fHz);
    return [
      { symbol: 'C', label: 'Mean circumference ~ λ (first order)', value: siToLength(C, lenUnit), unit: lenUnit },
      { symbol: 'λ₀', label: 'λ', value: siToLength(C0 / fHz, lenUnit), unit: lenUnit },
    ];
  }, [f, fUnit]);
  return (
    <section className="physics-subsection">
      <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      {rows.length > 0 && <ResultsTable title="Circular slot" rows={rows} />}
    </section>
  );
}

function SlotRingPanel() {
  const [f, setF] = useState(5);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [ereff, setEreff] = useState(3.2);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('mm');

  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const a = circularPatchRadiusResonanceM(fHz, ereff);
    const lambda = C0 / fHz;
    const Cmean = 2 * Math.PI * a;
    return [
      {
        symbol: 'r_m',
        label: 'Mean radius (≈ circular patch TM₁₁ a)',
        value: siToLength(a, lenUnit),
        unit: lenUnit,
      },
      {
        symbol: 'C_m',
        label: 'Mean circumference 2πr_m',
        value: siToLength(Cmean, lenUnit),
        unit: lenUnit,
      },
      { symbol: 'λ₀', label: 'Wavelength', value: siToLength(lambda, lenUnit), unit: lenUnit },
    ];
  }, [f, fUnit, ereff, lenUnit]);

  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`Annular slot modes depend on mean radius $r_m$ and slot width $w$. **First order:** treat $r_m$ like the circular patch radius $a$ for dominant $\\mathrm{TM}_{11}$ (same cavity-style scale).`}
      </FormulaMarkdown>
      <FormulaMarkdown className="physics-formula-note">
        {`$$a = \\frac{1.841\\,c}{2\\pi f \\sqrt{\\varepsilon_{\\mathrm{eff}}}} \\approx r_m$$`}
      </FormulaMarkdown>
      <p className="physics-formula-note">
        Full-wave simulation recommended for slot width, ring gap, and finite ground plane.
      </p>
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_eff</span>
            <div className="input-row">
              <input type="number" step={0.1} value={ereff} onChange={(e) => setEreff(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Result length unit</span>
            <div className="input-row">
              <select value={lenUnit} onChange={(e) => setLenUnit(e.target.value as LengthUnit)}>
                {LENGTH_UNITS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Ring slot (first-order mean radius)" rows={rows} />}
    </section>
  );
}

function SlotWaveguidePanel() {
  const [a, setA] = useState(22.86);
  const [b, setB] = useState(10.16);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('mm');
  const rows = useMemo((): ResultRow[] => {
    const aM = lengthToSI(a, lenUnit);
    if (aM <= 0) return [];
    const fc = C0 / (2 * aM);
    return [
      { symbol: 'f_c', label: 'TE₁₀ cutoff (wide wall a)', value: (fc / 1e9).toFixed(4), unit: 'GHz' },
      { symbol: 'λ_c', label: 'Cutoff wavelength', value: (2 * aM).toFixed(6), unit: 'm' },
    ];
  }, [a, lenUnit]);
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`Slotted waveguide: slot on broad wall cuts surface current; TE$_{10}$ cutoff $f_c = c/(2a)$. Array spacing sets grating lobes ($d/\\lambda$).`}
      </FormulaMarkdown>
      <div className="input-panel physics-input-grid">
        <LengthInput label="Guide wide wall a" value={a} unit={lenUnit} onValueChange={setA} onUnitChange={setLenUnit} />
        <LengthInput label="Narrow wall b" value={b} unit={lenUnit} onValueChange={setB} onUnitChange={setLenUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Rectangular waveguide (TE₁₀)" rows={rows} />}
    </section>
  );
}

function ParabolicPanel() {
  const [d, setD] = useState(1.2);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('m');
  const [f, setF] = useState(12);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [eta, setEta] = useState(0.55);
  const rows = useMemo((): ResultRow[] => {
    const Dm = lengthToSI(d, lenUnit);
    const fHz = frequencyToSI(f, fUnit);
    if (Dm <= 0 || fHz <= 0) return [];
    const g = parabolicGainDbi(Dm, fHz, eta);
    const lambda = C0 / fHz;
    return [
      { symbol: 'D', label: 'Diameter', value: d.toString(), unit: lenUnit },
      { symbol: 'λ₀', label: 'λ', value: siToLength(lambda, lenUnit), unit: lenUnit },
      { symbol: 'G', label: 'Gain (dBi)', value: g.toFixed(3), unit: 'dBi' },
    ];
  }, [d, lenUnit, f, fUnit, eta]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <LengthInput label="D" value={d} unit={lenUnit} onValueChange={setD} onUnitChange={setLenUnit} />
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">η</span>
            <div className="input-row">
              <input type="number" step={0.05} value={eta} onChange={(e) => setEta(parseFloat(e.target.value) || 0.55)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Parabolic reflector" rows={rows} />}
    </section>
  );
}

function CornerReflectorPanel() {
  const [w, setW] = useState(0.5);
  const [h, setH] = useState(0.5);
  const [f, setF] = useState(10);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const lenUnit: LengthUnit = 'm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const g = cornerReflectorGainDbi(w, h, fHz, 0.5);
    return [
      { symbol: 'G', label: 'Rough aperture gain', value: g.toFixed(2), unit: 'dBi' },
      { symbol: 'λ₀', label: 'λ', value: siToLength(C0 / fHz, lenUnit), unit: lenUnit },
    ];
  }, [w, h, f, fUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Aperture width</span>
            <div className="input-row">
              <input type="number" value={w} onChange={(e) => setW(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m</span>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Aperture height</span>
            <div className="input-row">
              <input type="number" value={h} onChange={(e) => setH(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m</span>
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Corner reflector" rows={rows} />}
    </section>
  );
}

/* ——— Arrays ——— */

function YagiPanel({ folded }: { folded: boolean }) {
  const [n, setN] = useState(7);
  const [z0, setZ0] = useState(50);
  const rows = useMemo((): ResultRow[] => {
    const g = yagiGainEmpiricalDbi(n);
    const R = folded ? FOLDED_DIPOLE_RIN_APPROX : DIPOLE_RIN_HALF_WAVE;
    const { s11Db } = s11FromImpedance(R, 0, z0);
    return [
      { symbol: 'N_el', label: 'Elements (driver+reflector+directors)', value: n, unit: '—' },
      { symbol: 'G', label: 'Empirical gain (order)', value: g.toFixed(2), unit: 'dBi' },
      { symbol: 'R_drv', label: 'Driver R (approx.)', value: R.toFixed(1), unit: 'Ω' },
      { symbol: 'S11', label: '|S11| vs Z₀ (rough)', value: s11Db.toFixed(2), unit: 'dB' },
    ];
  }, [n, z0, folded]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Element count</span>
            <div className="input-row">
              <input type="number" step={1} value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 2)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Z₀</span>
            <div className="input-row">
              <input type="number" value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 50)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
      </div>
      <ResultsTable title="Yagi-Uda (empirical)" rows={rows} />
    </section>
  );
}

function LpdaPanel() {
  const [tau, setTau] = useState(0.9);
  const rows = useMemo((): ResultRow[] => {
    const B = lpdaBandwidthRatioFromTau(tau);
    return [{ symbol: 'B', label: 'Bandwidth ratio f_max/f_min (crude)', value: B.toFixed(3), unit: '—' }];
  }, [tau]);
  return (
    <section className="physics-subsection">
      <div className="unit-input">
        <label>
          <span className="label-text">Scale factor τ</span>
          <div className="input-row">
            <input type="number" step={0.01} value={tau} onChange={(e) => setTau(parseFloat(e.target.value) || 0.9)} />
          </div>
        </label>
      </div>
      <ResultsTable title="LPDA" rows={rows} />
    </section>
  );
}

function PhasedArrayPanel() {
  const [n, setN] = useState(8);
  const [dLam, setDLam] = useState(0.5);
  const rows = useMemo((): ResultRow[] => {
    const g = arrayGainBroadsideDbi(n, 2.15);
    return [
      { symbol: 'N', label: 'Elements', value: n, unit: '—' },
      { symbol: 'd/λ', label: 'Spacing', value: dLam.toFixed(3), unit: '—' },
      { symbol: 'G_bs', label: 'Broadside gain vs λ/2 dipole (pattern)', value: g.toFixed(2), unit: 'dBi' },
    ];
  }, [n, dLam]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">N</span>
            <div className="input-row">
              <input type="number" value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 1)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">d/λ</span>
            <div className="input-row">
              <input type="number" step={0.05} value={dLam} onChange={(e) => setDLam(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
      </div>
      <ResultsTable title="Phased / uniform array" rows={rows} />
    </section>
  );
}

function CollinearPanel() {
  const [n, setN] = useState(4);
  const rows = useMemo(() => [{ symbol: 'G', label: 'Gain scale (ideal stack)', value: arrayGainBroadsideDbi(n, 2.15).toFixed(2), unit: 'dBi' }], [n]);
  return (
    <section className="physics-subsection">
      <div className="unit-input">
        <label>
          <span className="label-text">λ/2 sections N</span>
          <div className="input-row">
            <input type="number" value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 1)} />
          </div>
        </label>
      </div>
      <ResultsTable title="Collinear" rows={rows} />
    </section>
  );
}

function BroadsidePanel() {
  const [n, setN] = useState(4);
  const rows = useMemo(() => [{ symbol: 'AF_peak', label: 'Array factor peak ∝ N', value: n.toString(), unit: '—' }], [n]);
  return (
    <section className="physics-subsection">
      <div className="unit-input">
        <label>
          <span className="label-text">N</span>
          <div className="input-row">
            <input type="number" value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 1)} />
          </div>
        </label>
      </div>
      <ResultsTable title="Broadside" rows={rows} />
    </section>
  );
}

function EndfirePanel() {
  const [n, setN] = useState(6);
  const rows = useMemo(() => [{ symbol: 'G_ef', label: 'End-fire directivity est.', value: endfireDirectivityEstimateDbi(n).toFixed(2), unit: 'dBi' }], [n]);
  return (
    <section className="physics-subsection">
      <div className="unit-input">
        <label>
          <span className="label-text">N</span>
          <div className="input-row">
            <input type="number" value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 1)} />
          </div>
        </label>
      </div>
      <ResultsTable title="End-fire" rows={rows} />
    </section>
  );
}

/* ——— Microstrip variants ——— */

function CircularPatchPanel() {
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [ereff, setEreff] = useState(3.2);
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const a = circularPatchRadiusResonanceM(fHz, ereff);
    return [
      { symbol: 'a', label: 'TM₁₁ radius (order)', value: siToLength(a, lenUnit), unit: lenUnit },
      { symbol: 'D', label: 'Diameter', value: siToLength(2 * a, lenUnit), unit: lenUnit },
    ];
  }, [f, fUnit, ereff]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f_r" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_eff</span>
            <div className="input-row">
              <input type="number" step={0.1} value={ereff} onChange={(e) => setEreff(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Circular patch" rows={rows} />}
    </section>
  );
}

function TriangularPatchPanel() {
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [ereff, setEreff] = useState(3.2);
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const s = triangularPatchSideM(fHz, ereff);
    return [{ symbol: 's', label: 'Equilateral side (order)', value: siToLength(s, lenUnit), unit: lenUnit }];
  }, [f, fUnit, ereff]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f_r" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_eff</span>
            <div className="input-row">
              <input type="number" step={0.1} value={ereff} onChange={(e) => setEreff(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Triangular patch" rows={rows} />}
    </section>
  );
}

function AnnularPatchPanel() {
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [ereff, setEreff] = useState(3.2);
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const rm = annularMeanRadiusFromFreqM(fHz, ereff);
    return [{ symbol: 'r_m', label: 'Mean radius (first order)', value: siToLength(rm, lenUnit), unit: lenUnit }];
  }, [f, fUnit, ereff]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f_r" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_eff</span>
            <div className="input-row">
              <input type="number" step={0.1} value={ereff} onChange={(e) => setEreff(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Annular ring patch" rows={rows} />}
    </section>
  );
}

function PrintedDipolePanel() {
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [vf, setVf] = useState(0.81);
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const L = dipoleHalfWaveLen(fHz, vf);
    return [
      { symbol: 'L', label: 'Printed λ/2 length', value: siToLength(L, lenUnit), unit: lenUnit },
      { symbol: 'λ₀', label: 'λ', value: siToLength(C0 / fHz, lenUnit), unit: lenUnit },
    ];
  }, [f, fUnit, vf]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">v_f (substrate)</span>
            <div className="input-row">
              <input type="number" step={0.01} value={vf} onChange={(e) => setVf(parseFloat(e.target.value) || 0.8)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Printed dipole" rows={rows} />}
    </section>
  );
}

function PrintedSlotPanel() {
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [er, setEr] = useState(4.4);
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const ereff = (er + 1) / 2;
    const L = slotLengthInMediumM(fHz, ereff);
    return [{ symbol: 'L', label: 'Half-wave slot length', value: siToLength(L, lenUnit), unit: lenUnit }];
  }, [f, fUnit, er]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">ε_r (substrate)</span>
            <div className="input-row">
              <input type="number" step={0.1} value={er} onChange={(e) => setEr(parseFloat(e.target.value) || 1)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Printed slot" rows={rows} />}
    </section>
  );
}

/* ——— Travelling ——— */

function HelixNormalPanel() {
  const [A, setA] = useState(0.002);
  const [n, setN] = useState(5);
  const [f, setF] = useState(150);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const R = normalModeHelixRradRough(A, n, fHz);
    return [{ symbol: 'R_rad', label: 'Very rough R_rad', value: R.toExponential(4), unit: 'Ω' }];
  }, [A, n, f, fUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Turn area (one turn)</span>
            <div className="input-row">
              <input type="number" value={A} onChange={(e) => setA(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m²</span>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Turns</span>
            <div className="input-row">
              <input type="number" value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 1)} />
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Normal-mode helix" rows={rows} />}
    </section>
  );
}

function HelicalAxialPanel() {
  const [f, setF] = useState(1.5);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const [n, setN] = useState(12);
  const [pitch, setPitch] = useState(13);
  const [cFrac, setCFrac] = useState(1);
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0 || n <= 0) return [];
    const lambda = C0 / fHz;
    const C = cFrac * lambda;
    const g = helixAxialGainEstimate(n, pitch, C, fHz);
    return [
      { symbol: 'C', label: 'Circumference', value: C.toFixed(6), unit: 'm' },
      { symbol: 'G', label: 'Kraus D (dBi)', value: Number.isFinite(g) ? g.toFixed(3) : '—', unit: 'dBi' },
    ];
  }, [f, fUnit, n, pitch, cFrac]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
        <div className="unit-input">
          <label>
            <span className="label-text">N</span>
            <div className="input-row">
              <input type="number" value={n} onChange={(e) => setN(parseInt(e.target.value, 10) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Pitch °</span>
            <div className="input-row">
              <input type="number" value={pitch} onChange={(e) => setPitch(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">C/λ</span>
            <div className="input-row">
              <input type="number" step={0.01} value={cFrac} onChange={(e) => setCFrac(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Axial helix" rows={rows} />}
    </section>
  );
}

function SpiralArchimedeanPanel() {
  const [rmin, setRmin] = useState(5);
  const [rmax, setRmax] = useState(40);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('mm');
  const rows = useMemo((): ResultRow[] => {
    const a = lengthToSI(rmin, lenUnit);
    const b = lengthToSI(rmax, lenUnit);
    const { fLowHz, fHighHz } = spiralFreqBandFromRadiiM(a, b);
    if (!Number.isFinite(fLowHz)) return [];
    return [
      { symbol: 'f_lo', label: '~Lower band edge', value: siToFrequency(fLowHz, 'GHz'), unit: 'GHz' },
      { symbol: 'f_hi', label: '~Upper band edge', value: siToFrequency(fHighHz, 'GHz'), unit: 'GHz' },
    ];
  }, [rmin, rmax, lenUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <LengthInput label="R_min" value={rmin} unit={lenUnit} onValueChange={setRmin} onUnitChange={setLenUnit} />
        <LengthInput label="R_max" value={rmax} unit={lenUnit} onValueChange={setRmax} onUnitChange={setLenUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Archimedean spiral band" rows={rows} />}
    </section>
  );
}

function SpiralLogPanel() {
  return (
    <InfoPanel
      title="Log spiral"
      body="Self-complementary spiral on infinite ground has impedance $\\approx 188\\,\\Omega$ (free-space $\\eta_0/2$). Finite substrate, cavity, and feed balun dominate practical $S_{11}$. Use Archimedean band tool for order-of-magnitude bandwidth vs arm extent."
    />
  );
}

function VAntennaPanel() {
  const [leg, setLeg] = useState(5);
  const [f, setF] = useState(50);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const [lenUnit, setLenUnit] = useState<LengthUnit>('m');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    const Lm = lengthToSI(leg, lenUnit);
    if (fHz <= 0 || Lm <= 0) return [];
    const lambda = C0 / fHz;
    return [
      { symbol: 'L/λ', label: 'Leg / λ', value: (Lm / lambda).toFixed(3), unit: '—' },
      { symbol: 'λ₀', label: 'λ', value: siToLength(lambda, lenUnit), unit: lenUnit },
    ];
  }, [leg, f, fUnit, lenUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <LengthInput label="Leg length" value={leg} unit={lenUnit} onValueChange={setLeg} onUnitChange={setLenUnit} />
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="V antenna" rows={rows} />}
    </section>
  );
}

function RhombicPanel() {
  const [leg, setLeg] = useState(10);
  const [f, setF] = useState(20);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const [lenUnit, setLenUnit] = useState<LengthUnit>('m');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    const Lm = lengthToSI(leg, lenUnit);
    if (fHz <= 0) return [];
    const g = rhombicGainRoughDbi(Lm, fHz);
    return [
      { symbol: 'G', label: 'Very rough gain', value: g.toFixed(2), unit: 'dBi' },
      { symbol: 'λ₀', label: 'λ', value: siToLength(C0 / fHz, lenUnit), unit: lenUnit },
    ];
  }, [leg, f, fUnit, lenUnit]);
  return (
    <section className="physics-subsection">
      <div className="input-panel physics-input-grid">
        <LengthInput label="Leg length" value={leg} unit={lenUnit} onValueChange={setLeg} onUnitChange={setLenUnit} />
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Rhombic" rows={rows} />}
    </section>
  );
}

function LensPanel() {
  return <HornPanel />;
}

function FiLpPanel() {
  return <LpdaPanel />;
}

function FiSpiralPanel() {
  return <SpiralArchimedeanPanel />;
}

function DisconePanel() {
  const [h, setH] = useState(0.15);
  const [lenUnit, setLenUnit] = useState<LengthUnit>('m');
  const rows = useMemo((): ResultRow[] => {
    const hm = lengthToSI(h, lenUnit);
    const flo = disconeApproxLowFreqHz(hm);
    if (!Number.isFinite(flo)) return [];
    return [{ symbol: 'f_lo', label: 'Rough lower frequency', value: siToFrequency(flo, 'MHz'), unit: 'MHz' }];
  }, [h, lenUnit]);
  return (
    <section className="physics-subsection">
      <LengthInput label="Cone height h" value={h} unit={lenUnit} onValueChange={setH} onUnitChange={setLenUnit} />
      {rows.length > 0 && <ResultsTable title="Discone" rows={rows} />}
    </section>
  );
}

function BiconicalPanel() {
  const [f, setF] = useState(200);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('MHz');
  const lenUnit: LengthUnit = 'mm';
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0) return [];
    const Ls = biconicalSlantQuarterWaveM(fHz);
    return [{ symbol: 'L_s', label: 'Slant height ~ λ/4 @ f', value: siToLength(Ls, lenUnit), unit: lenUnit }];
  }, [f, fUnit, lenUnit]);
  return (
    <section className="physics-subsection">
      <UnitInput label="Design f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      {rows.length > 0 && <ResultsTable title="Biconical" rows={rows} />}
    </section>
  );
}

function TurnstilePanel() {
  const [z0, setZ0] = useState(50);
  const rows = useMemo(() => {
    const { s11Db } = s11FromImpedance(DIPOLE_RIN_HALF_WAVE, 0, z0);
    return [{ symbol: 'S11', label: 'Single dipole arm vs Z₀ (before hybrid)', value: s11Db.toFixed(2), unit: 'dB' }];
  }, [z0]);
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`Two $\\lambda/2$ dipoles at $90^\\circ$ with quadrature feed → CP; branch-line hybrid or $90^\\circ$ cable.`}
      </FormulaMarkdown>
      <div className="unit-input">
        <label>
          <span className="label-text">Z₀</span>
          <div className="input-row">
            <input type="number" value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 50)} />
            <span className="physics-suffix">Ω</span>
          </div>
        </label>
      </div>
      <ResultsTable title="Turnstile (dipole arm match)" rows={rows} />
    </section>
  );
}

function RfLinkBudgetPanel() {
  const [pt, setPt] = useState(20);
  const [gt, setGt] = useState(3);
  const [gr, setGr] = useState(3);
  const [d, setD] = useState(1000);
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0 || d <= 0) return [];
    const pl = freeSpacePathLossDb(d, fHz);
    const pr = friisReceivedPowerDbm(pt, gt, gr, d, fHz);
    return [
      { symbol: 'PL_fs', label: 'Free-space path loss', value: pl.toFixed(2), unit: 'dB' },
      { symbol: 'P_r', label: 'Received power (dBm)', value: pr.toFixed(2), unit: 'dBm' },
    ];
  }, [pt, gt, gr, d, f, fUnit]);
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`$$P_r\\ \\mathrm{(dBm)} = P_t + G_t + G_r - \\mathrm{FSPL}\\quad\\text{(Friis, LOS)}$$`}
      </FormulaMarkdown>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">P_t (dBm)</span>
            <div className="input-row">
              <input type="number" value={pt} onChange={(e) => setPt(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">G_t (dBi)</span>
            <div className="input-row">
              <input type="number" value={gt} onChange={(e) => setGt(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">G_r (dBi)</span>
            <div className="input-row">
              <input type="number" value={gr} onChange={(e) => setGr(parseFloat(e.target.value) || 0)} />
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Distance</span>
            <div className="input-row">
              <input type="number" value={d} onChange={(e) => setD(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m</span>
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Link budget (Friis, LOS)" rows={rows} />}
    </section>
  );
}

function MimoPanel() {
  const [s21, setS21] = useState(0.1);
  const rho = useMemo(() => mimoCorrelationRoughFromIsolation(s21), [s21]);
  const rows: ResultRow[] = [
    { symbol: '|S21|', label: 'Coupling magnitude (proxy)', value: s21.toFixed(4), unit: '—' },
    { symbol: 'ρ_env²', label: 'Very rough correlation proxy', value: rho.toExponential(3), unit: '—' },
  ];
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`Low correlation needs pattern/space diversity; use full $S$-parameter matrix for real $\\rho_e$ (envelope correlation).`}
      </FormulaMarkdown>
      <div className="unit-input">
        <label>
          <span className="label-text">|S21| between branches</span>
          <div className="input-row">
            <input type="number" step={0.01} value={s21} onChange={(e) => setS21(parseFloat(e.target.value) || 0)} />
          </div>
        </label>
      </div>
      <ResultsTable title="MIMO isolation proxy" rows={rows} />
    </section>
  );
}

function S11Panel() {
  const [zr, setZr] = useState(73);
  const [zi, setZi] = useState(0);
  const [z0, setZ0] = useState(50);
  const rows = useMemo((): ResultRow[] => {
    const { s11Db, gammaMag } = s11FromImpedance(zr, zi, z0);
    if (!Number.isFinite(s11Db)) return [];
    return [
      { symbol: 'Z', label: 'Z', value: `${zr.toFixed(3)}+j${zi.toFixed(3)}`, unit: 'Ω' },
      { symbol: '|Γ|', label: '|Γ|', value: gammaMag.toFixed(6), unit: '—' },
      { symbol: 'S11', label: '|S11|', value: s11Db.toFixed(4), unit: 'dB' },
    ];
  }, [zr, zi, z0]);
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`$\\Gamma = \\dfrac{Z - Z_0}{Z + Z_0}$, $|S_{11}| = 20\\log_{10}|\\Gamma|$ (passive one-port, real $Z_0$).`}
      </FormulaMarkdown>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">Re(Z)</span>
            <div className="input-row">
              <input type="number" value={zr} onChange={(e) => setZr(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Im(Z)</span>
            <div className="input-row">
              <input type="number" value={zi} onChange={(e) => setZi(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
        <div className="unit-input">
          <label>
            <span className="label-text">Z₀</span>
            <div className="input-row">
              <input type="number" value={z0} onChange={(e) => setZ0(parseFloat(e.target.value) || 50)} />
              <span className="physics-suffix">Ω</span>
            </div>
          </label>
        </div>
      </div>
      {rows.length > 0 && <ResultsTable title="Γ / S11" rows={rows} />}
    </section>
  );
}

function PathFriisPanel() {
  const [d, setD] = useState(1000);
  const [f, setF] = useState(2.45);
  const [fUnit, setFUnit] = useState<FrequencyUnit>('GHz');
  const rows = useMemo((): ResultRow[] => {
    const fHz = frequencyToSI(f, fUnit);
    if (fHz <= 0 || d <= 0) return [];
    const pl = freeSpacePathLossDb(d, fHz);
    const lambda = C0 / fHz;
    return [
      { symbol: 'PL', label: 'FSPL', value: pl.toFixed(3), unit: 'dB' },
      { symbol: 'λ₀', label: 'λ', value: lambda.toFixed(4), unit: 'm' },
    ];
  }, [d, f, fUnit]);
  return (
    <section className="physics-subsection">
      <FormulaMarkdown className="physics-formula-note" inlineParagraph>
        {`$$\\mathrm{FSPL} = 20\\log_{10}\\!\\left(\\frac{4\\pi d}{\\lambda}\\right)\\ \\mathrm{dB}$$`}
      </FormulaMarkdown>
      <div className="input-panel physics-input-grid">
        <div className="unit-input">
          <label>
            <span className="label-text">d</span>
            <div className="input-row">
              <input type="number" value={d} onChange={(e) => setD(parseFloat(e.target.value) || 0)} />
              <span className="physics-suffix">m</span>
            </div>
          </label>
        </div>
        <UnitInput label="f" value={f} unit={fUnit} onValueChange={setF} onUnitChange={setFUnit} />
      </div>
      {rows.length > 0 && <ResultsTable title="Free-space path loss" rows={rows} />}
    </section>
  );
}
