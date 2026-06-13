import React from 'react';
import { useAntennaStore } from '../../services/state';
import {
  decodeDipolePhysicalFromGeometry,
  type DipolePhysicalInputs,
} from '../../utils/dipoleParams';

function normalizeDipoleDisplay(
  d:
    | DipolePhysicalInputs
    | {
        dipole_length_mm?: number;
        wire_radius_mm?: number;
        feed_gap_mm?: number;
        f0_GHz?: number;
        fc_GHz?: number;
      }
): DipolePhysicalInputs {
  if ('dipoleLengthMm' in d) {
    return d;
  }
  const m = d as {
    dipole_length_mm?: number;
    wire_radius_mm?: number;
    feed_gap_mm?: number;
    f0_GHz?: number;
    fc_GHz?: number;
  };
  return {
    dipoleLengthMm: m.dipole_length_mm ?? 0,
    wireRadiusMm: m.wire_radius_mm ?? 0,
    feedGapMm: m.feed_gap_mm ?? 0,
    f0GHz: m.f0_GHz ?? 0,
    fcGHz: m.fc_GHz ?? 0,
  };
}
import './ParametersPanel.css';

export const ParametersPanel: React.FC = () => {
  const { antennaType, parameters, predictions, simulationResults } = useAntennaStore();

  // Safe defaults with proper structure
  const defaultParams = {
    geometry: { length: 0.03, width: 0.04, height: 0.0016, feed_x: 0.015, feed_y: 0.02 },
    substrate: { substrate_type: 'FR4', relative_permittivity: 4.4, loss_tangent: 0.02 },
  };

  // Prefer last simulation result so panel updates after Design or Designer simulation
  const currentParams = simulationResults?.antenna_parameters || parameters || defaultParams;

  const geometry = currentParams.geometry || defaultParams.geometry;
  const substrate = currentParams.substrate || defaultParams.substrate;

  const dipoleMeta = simulationResults?.metadata?.dipole_physical as
    | {
        dipole_length_mm?: number;
        wire_radius_mm?: number;
        feed_gap_mm?: number;
        f0_GHz?: number;
        fc_GHz?: number;
      }
    | undefined;
  const dipoleDecoded =
    antennaType === 'dipole'
      ? normalizeDipoleDisplay(dipoleMeta ?? decodeDipolePhysicalFromGeometry(geometry))
      : null;

  // Model / solver info: from last run (simulationResults) or predictions
  const isSurrogate = simulationResults?.solver_name === 'surrogate';
  const isOpenEMS = simulationResults?.solver_name && simulationResults.solver_name !== 'surrogate';
  const source = simulationResults || predictions;
  const confidence = source
    ? {
        uncertainty: source.gain_confidence_lower != null && source.gain_confidence_upper != null && source.gain
          ? `±${((source.gain_confidence_upper - source.gain) * 100 / source.gain).toFixed(1)}%`
          : (isOpenEMS ? '—' : '±2.5%'),
        status: 'valid',
        modelName: isSurrogate
          ? source.metadata?.requested_model_name ||
            source.metadata?.model_name ||
            source.model_name ||
            (antennaType === 'dipole' ? 'dipole' : 'default')
          : isOpenEMS
            ? 'OpenEMS'
            : source.model_name || 'N/A',
        modelVersion: source.solver_version || source.model_version || (isOpenEMS ? '—' : '1.0'),
        label: isOpenEMS ? 'Solver' : 'Model',
      }
    : { uncertainty: 'N/A', status: 'pending', modelName: 'N/A', modelVersion: 'N/A', label: 'Model' };

  return (
    <div className="parameters-panel">
      <div className="parameters-panel-header">
        <h3 className="parameters-panel-title">Parameters</h3>
      </div>
      <div className="parameters-panel-content">
        {antennaType === 'dipole' && dipoleDecoded != null ? (
          <>
            <div className="parameters-section">
              <div className="section-header">Dipole (physical)</div>
              <div className="parameters-display">
                <div className="param-row">
                  <span className="param-label">Length:</span>
                  <span className="param-value mono">{dipoleDecoded.dipoleLengthMm.toFixed(2)} mm</span>
                </div>
                <div className="param-row">
                  <span className="param-label">Wire R:</span>
                  <span className="param-value mono">{dipoleDecoded.wireRadiusMm.toFixed(3)} mm</span>
                </div>
                <div className="param-row">
                  <span className="param-label">Feed gap:</span>
                  <span className="param-value mono">{dipoleDecoded.feedGapMm.toFixed(3)} mm</span>
                </div>
                <div className="param-row">
                  <span className="param-label">f₀:</span>
                  <span className="param-value mono">{dipoleDecoded.f0GHz.toFixed(3)} GHz</span>
                </div>
                <div className="param-row">
                  <span className="param-label">f_c:</span>
                  <span className="param-value mono">{dipoleDecoded.fcGHz.toFixed(3)} GHz</span>
                </div>
              </div>
            </div>
            <div className="divider" />
            <div className="parameters-section">
              <div className="section-header">Model encoding</div>
              <p className="parameters-note" style={{ fontSize: 11, color: 'var(--color-text-secondary)', padding: '0 0 8px 0' }}>
                Surrogate uses internal geometry slots for L, 2R, gap, and excitation — same as training.
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="parameters-section">
              <div className="section-header">Geometry (patch)</div>
              <div className="parameters-display">
                <div className="param-row">
                  <span className="param-label">Length:</span>
                  <span className="param-value mono">
                    {(geometry.length * 1000).toFixed(2)} mm
                  </span>
                </div>
                <div className="param-row">
                  <span className="param-label">Width:</span>
                  <span className="param-value mono">
                    {(geometry.width * 1000).toFixed(2)} mm
                  </span>
                </div>
                <div className="param-row">
                  <span className="param-label">Height:</span>
                  <span className="param-value mono">
                    {(geometry.height * 1000).toFixed(2)} mm
                  </span>
                </div>
                <div className="param-row">
                  <span className="param-label">Feed X:</span>
                  <span className="param-value mono">
                    {(geometry.feed_x * 1000).toFixed(2)} mm
                  </span>
                </div>
                <div className="param-row">
                  <span className="param-label">Feed Y:</span>
                  <span className="param-value mono">
                    {(geometry.feed_y * 1000).toFixed(2)} mm
                  </span>
                </div>
              </div>
            </div>
            <div className="divider" />
            <div className="parameters-section">
              <div className="section-header">Substrate</div>
              <div className="parameters-display">
                <div className="param-row">
                  <span className="param-label">Type:</span>
                  <span className="param-value">{substrate.substrate_type ?? defaultParams.substrate.substrate_type}</span>
                </div>
                <div className="param-row">
                  <span className="param-label">εr:</span>
                  <span className="param-value mono">
                    {substrate.relative_permittivity.toFixed(2)}
                  </span>
                </div>
                <div className="param-row">
                  <span className="param-label">tan δ:</span>
                  <span className="param-value mono">
                    {substrate.loss_tangent.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
        <div className="divider" />
        <div className="parameters-section">
          <div className="section-header">Model Info</div>
          <div className="parameters-display">
            <div className="param-row">
              <span className="param-label">{confidence.label}:</span>
              <span className="param-value">{confidence.modelName}</span>
            </div>
            <div className="param-row">
              <span className="param-label">Version:</span>
              <span className="param-value">{confidence.modelVersion === '—' ? '—' : `v${confidence.modelVersion}`}</span>
            </div>
            <div className="param-row">
              <span className="param-label">Uncertainty:</span>
              <span className="param-value mono">{confidence.uncertainty}</span>
            </div>
            <div className="param-row">
              <span className="param-label">Status:</span>
              <span className={`param-value text-${confidence.status === 'valid' ? 'success' : 'secondary'}`}>
                {confidence.status === 'valid' ? (isOpenEMS ? 'Completed' : 'Valid') : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

