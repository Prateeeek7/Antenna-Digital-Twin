import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { S11Plot } from '../visualization/S11Plot';
import { useAntennaStore } from '../../services/state';
import api from '../../services/api';
import { buildDipoleAntennaApiPayload } from '../../utils/dipoleParams';
import './AntennaDesigner.css';

/** Defaults in the ballpark of the openEMS dipole sweep dataset */
const DEFAULT_DIPOLE = {
  dipoleLengthMm: 62,
  wireRadiusMm: 1.0,
  feedGapMm: 1.0,
  f0GHz: 2.4,
  fcGHz: 1.08,
};

export const DipoleDesigner: React.FC = () => {
  const [dipoleLengthMm, setDipoleLengthMm] = useState(DEFAULT_DIPOLE.dipoleLengthMm);
  const [wireRadiusMm, setWireRadiusMm] = useState(DEFAULT_DIPOLE.wireRadiusMm);
  const [feedGapMm, setFeedGapMm] = useState(DEFAULT_DIPOLE.feedGapMm);
  const [f0GHz, setF0GHz] = useState(DEFAULT_DIPOLE.f0GHz);
  const [fcGHz, setFcGHz] = useState(DEFAULT_DIPOLE.fcGHz);

  const [isSimulating, setIsSimulating] = useState(false);
  const [isAutoDesigning, setIsAutoDesigning] = useState(false);
  const [s11Data, setS11Data] = useState<{
    frequency: number[];
    s11Magnitude: number[];
    resonanceFrequencyGHz?: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { setParameters, setSimulationResults } = useAntennaStore();

  const payload = buildDipoleAntennaApiPayload({
    dipoleLengthMm,
    wireRadiusMm,
    feedGapMm,
    f0GHz,
    fcGHz,
  });

  useEffect(() => {
    setParameters(payload);
  }, [dipoleLengthMm, wireRadiusMm, feedGapMm, f0GHz, fcGHz, setParameters]);

  const validate = (): string | null => {
    if (dipoleLengthMm <= 0 || dipoleLengthMm > 500) return 'Dipole length should be between 0 and 500 mm.';
    if (wireRadiusMm <= 0 || wireRadiusMm > 10) return 'Wire radius should be between 0 and 10 mm.';
    if (feedGapMm <= 0 || feedGapMm > 20) return 'Feed gap should be between 0 and 20 mm.';
    if (f0GHz <= 0.1 || f0GHz > 12) return 'Center frequency f₀ should be between 0.1 and 12 GHz.';
    if (fcGHz <= 0 || fcGHz > 5) return 'Excitation bandwidth f_c should be between 0 and 5 GHz.';
    return null;
  };

  const handleRunSurrogate = async () => {
    setError(null);
    const v = validate();
    if (v) {
      setError(v);
      return;
    }
    setIsSimulating(true);
    try {
      const response = await api.post('/em/simulate', payload, {
        params: { solver_name: 'surrogate', antenna_type: 'dipole' },
        timeout: 60000,
      });
      if (response.data?.s11) {
        const freqGHz = response.data.s11.frequency.map((f: number) => f / 1e9);
        const mag = response.data.s11.s11_magnitude;
        const resHz = response.data.metadata?.resonance_frequency;
        setS11Data({
          frequency: freqGHz,
          s11Magnitude: mag,
          resonanceFrequencyGHz: resHz != null ? resHz / 1e9 : undefined,
        });
        setParameters(response.data.antenna_parameters || payload);
        setSimulationResults(response.data);
      } else {
        throw new Error('Invalid response format from simulation');
      }
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError(typeof msg === 'string' ? msg : err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleAutoDesignFromFrequency = async () => {
    setError(null);
    if (f0GHz <= 0.1 || f0GHz > 12) {
      setError('Center frequency f₀ should be between 0.1 and 12 GHz.');
      return;
    }
    setIsAutoDesigning(true);
    try {
      const response = await api.post('/predictions/dipole/design-from-frequency', {
        target_frequency_ghz: f0GHz,
        target_s11_db: -10,
        feed_resistance_ohm: 50,
        n_candidates: 36,
        fc_ratio: 0.45,
      }, { timeout: 120000 });

      const recommendation = response.data?.recommendation as
        | {
            dipole_length_mm: number;
            wire_radius_mm: number;
            feed_gap_mm: number;
            f0_ghz: number;
            fc_ghz: number;
          }
        | undefined;
      const prediction = response.data?.prediction as
        | {
            antenna_parameters?: unknown;
            s11?: { frequency: number[]; s11_magnitude: number[] };
          }
        | undefined;

      if (!recommendation) {
        throw new Error('No recommended dipole design returned by model');
      }

      setDipoleLengthMm(recommendation.dipole_length_mm);
      setWireRadiusMm(recommendation.wire_radius_mm);
      setFeedGapMm(recommendation.feed_gap_mm);
      setF0GHz(recommendation.f0_ghz);
      setFcGHz(recommendation.fc_ghz);

      if (prediction?.s11) {
        setS11Data({
          frequency: prediction.s11.frequency.map((f) => f / 1e9),
          s11Magnitude: prediction.s11.s11_magnitude,
          resonanceFrequencyGHz: response.data?.recommendation?.predicted_resonance_ghz,
        });
      }
      if (prediction?.antenna_parameters) {
        setParameters(prediction.antenna_parameters);
      }
      if (prediction) {
        setSimulationResults(prediction);
      }
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError(typeof msg === 'string' ? msg : err instanceof Error ? err.message : 'Auto design failed');
    } finally {
      setIsAutoDesigning(false);
    }
  };

  return (
    <div className="antenna-designer">
      <div className="antenna-designer-form">
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <div className="section-header">Dipole geometry (center-fed)</div>
        <p className="result-comparison-note" style={{ marginBottom: '12px', maxWidth: '560px' }}>
          Configure a center-fed dipole antenna by adjusting its geometric parameters, where the total length primarily
          determines the resonant frequency, and the wire radius and feed gap influence impedance matching and bandwidth.
          These inputs are mapped into a surrogate model trained on electromagnetic simulations, enabling fast prediction
          and optimization without the need for full-wave simulation. For best results, start with a dipole length
          approximately equal to half the wavelength (λ/2) of your target frequency.
        </p>
        <div className="input-group">
          <Input
            label="Dipole length (end to end)"
            type="number"
            unit="mm"
            value={dipoleLengthMm.toString()}
            onChange={(e) => setDipoleLengthMm(parseFloat(e.target.value) || 0)}
            min="1"
            max="500"
            step="0.1"
          />
          <Input
            label="Wire radius (equivalent)"
            type="number"
            unit="mm"
            value={wireRadiusMm.toString()}
            onChange={(e) => setWireRadiusMm(parseFloat(e.target.value) || 0)}
            min="0.05"
            max="10"
            step="0.01"
          />
          <Input
            label="Feed gap"
            type="number"
            unit="mm"
            value={feedGapMm.toString()}
            onChange={(e) => setFeedGapMm(parseFloat(e.target.value) || 0)}
            min="0.1"
            max="20"
            step="0.05"
          />
        </div>

        <div className="divider" />

        <div className="section-header">Excitation (Gaussian)</div>
        <div className="input-group">
          <Input
            label="Center frequency f₀"
            type="number"
            unit="GHz"
            value={f0GHz.toString()}
            onChange={(e) => setF0GHz(parseFloat(e.target.value) || 0)}
            min="0.1"
            max="12"
            step="0.01"
          />
          <Input
            label="Bandwidth f_c (Gaussian)"
            type="number"
            unit="GHz"
            value={fcGHz.toString()}
            onChange={(e) => setFcGHz(parseFloat(e.target.value) || 0)}
            min="0.05"
            max="5"
            step="0.01"
            title="Matches fc = 0.45×f₀ in the generator when applicable"
          />
        </div>

        <div className="antenna-designer-actions">
          <Button variant="secondary" onClick={handleAutoDesignFromFrequency} disabled={isSimulating || isAutoDesigning}>
            {isAutoDesigning ? 'Searching…' : 'Auto-design from f₀'}
          </Button>
          <Button variant="primary" onClick={handleRunSurrogate} disabled={isSimulating}>
            {isSimulating ? 'Running…' : 'Get result (dipole model)'}
          </Button>
        </div>
      </div>

      <div className="antenna-designer-visualization">
        {s11Data ? (
          <S11Plot frequency={s11Data.frequency} s11Magnitude={s11Data.s11Magnitude} />
        ) : (
          <div className="visualization-placeholder">
            <p>Run dipole surrogate to view S11</p>
          </div>
        )}
      </div>
    </div>
  );
};
