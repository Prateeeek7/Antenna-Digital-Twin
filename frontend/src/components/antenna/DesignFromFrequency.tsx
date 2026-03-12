import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Patch3DView } from '../visualization/Patch3DView';
import api from '../../services/api';
import { useAntennaStore } from '../../services/state';
import { getPatchDesignSteps } from '../../utils/patchDesignSteps';
import './DesignFromFrequency.css';

interface DesignInput {
  resonanceGHz: number;
  permittivity: number;
  lossTangent: number;
  heightMm: number;
}

interface DesignResult {
  simulation_id: string;
  antenna_parameters: {
    geometry: { length: number; width: number; height: number; feed_x: number; feed_y: number };
    substrate: { relative_permittivity: number; loss_tangent: number };
  };
  s11?: { frequency: number[]; s11_magnitude: number[] };
  metadata?: { actual_resonance_hz?: number };
}

const defaultInput: DesignInput = {
  resonanceGHz: 2.45,
  permittivity: 4.4,
  lossTangent: 0.02,
  heightMm: 1.6,
};

export const DesignFromFrequency: React.FC = () => {
  const { setParameters, setSimulationResults, setCalculationDetails } = useAntennaStore();
  const [input, setInput] = useState<DesignInput>(defaultInput);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DesignResult | null>(null);

  const handleDesign = async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.post<DesignResult>('/em/design', {
        resonance_frequency_hz: input.resonanceGHz * 1e9,
        relative_permittivity: input.permittivity,
        loss_tangent: input.lossTangent,
        thickness_m: input.heightMm / 1000,
      }, { timeout: 300000 });
      const data = res.data;
      setResult(data);
      setParameters(data.antenna_parameters);
      setSimulationResults(data);
      const details = getPatchDesignSteps(
        input.resonanceGHz * 1e9,
        input.permittivity,
        input.lossTangent,
        input.heightMm / 1000,
        data.antenna_parameters?.geometry
      );
      setCalculationDetails(details);
    } catch (e: unknown) {
      setError(e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? 'Design failed'
        : 'Design failed');
    } finally {
      setLoading(false);
    }
  };

  const g = result?.antenna_parameters?.geometry;
  const sub = result?.antenna_parameters?.substrate;

  return (
    <div className="design-from-freq">
      <div className="design-from-freq-form">
        <div className="design-from-freq-inputs">
          <label>
            <span>f<sub>0</sub> (GHz)</span>
            <input
              type="number"
              step="0.01"
              min="0.5"
              max="10"
              value={input.resonanceGHz}
              onChange={(e) => setInput((p) => ({ ...p, resonanceGHz: parseFloat(e.target.value) || p.resonanceGHz }))}
            />
          </label>
          <label>
            <span>ε<sub>r</sub></span>
            <input
              type="number"
              step="0.1"
              min="1"
              max="20"
              value={input.permittivity}
              onChange={(e) => setInput((p) => ({ ...p, permittivity: parseFloat(e.target.value) || p.permittivity }))}
            />
          </label>
          <label>
            <span>tan δ</span>
            <input
              type="number"
              step="0.001"
              min="0"
              max="0.1"
              value={input.lossTangent}
              onChange={(e) => setInput((p) => ({ ...p, lossTangent: parseFloat(e.target.value) ?? p.lossTangent }))}
            />
          </label>
          <label>
            <span>h (mm)</span>
            <input
              type="number"
              step="0.1"
              min="0.2"
              max="5"
              value={input.heightMm}
              onChange={(e) => setInput((p) => ({ ...p, heightMm: parseFloat(e.target.value) || p.heightMm }))}
            />
          </label>
        </div>
        <Button variant="primary" onClick={handleDesign} disabled={loading}>
          {loading ? 'Designing…' : 'Design'}
        </Button>
        {error && <div className="design-from-freq-error">{error}</div>}
        {result && g && (
          <div className="design-from-freq-result-card">
            <div className="design-from-freq-result-section">
              <span className="design-from-freq-result-label">Dimensions</span>
              <div className="design-from-freq-result-grid">
                <div><var>L</var> {(g.length * 1000).toFixed(2)} mm</div>
                <div><var>W</var> {(g.width * 1000).toFixed(2)} mm</div>
                <div><var>h</var> {(g.height * 1000).toFixed(2)} mm</div>
              </div>
            </div>
            <div className="design-from-freq-result-section">
              <span className="design-from-freq-result-label">Feed (x, y)</span>
              <div className="design-from-freq-result-value">
                ({(g.feed_x * 1000).toFixed(2)}, {(g.feed_y * 1000).toFixed(2)}) mm
              </div>
            </div>
            {result.metadata?.actual_resonance_hz != null && (
              <div className="design-from-freq-result-section">
                <span className="design-from-freq-result-label">f<sub>res</sub></span>
                <span className="design-from-freq-result-fres">{(result.metadata.actual_resonance_hz / 1e9).toFixed(3)} GHz</span>
              </div>
            )}
            <div className="design-from-freq-result-saved">Saved</div>
          </div>
        )}
      </div>
      <div className="design-from-freq-view">
        {result && g ? (
          <div className="design-from-freq-3d-wrap">
            <p className="design-from-freq-scale">
              Top view · W = {(g.width * 1000).toFixed(2)} mm, L = {(g.length * 1000).toFixed(2)} mm, h = {(g.height * 1000).toFixed(2)} mm · Drag to rotate
            </p>
            <Patch3DView
              length={g.length}
              width={g.width}
              height={g.height}
              feedX={g.feed_x}
              feedY={g.feed_y}
            />
          </div>
        ) : (
          <div className="design-from-freq-placeholder">Enter values and run Design</div>
        )}
      </div>
    </div>
  );
};
