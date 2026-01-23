import React from 'react';
import { useAntennaStore } from '../../services/state';
import './ParametersPanel.css';

export const ParametersPanel: React.FC = () => {
  const { parameters, predictions } = useAntennaStore();

  // Safe defaults with proper structure
  const defaultParams = {
    geometry: { length: 0.03, width: 0.04, height: 0.0016, feed_x: 0.015, feed_y: 0.02 },
    substrate: { substrate_type: 'FR4', relative_permittivity: 4.4, loss_tangent: 0.02 },
  };

  const currentParams = parameters || defaultParams;
  
  // Ensure geometry and substrate exist
  const geometry = currentParams.geometry || defaultParams.geometry;
  const substrate = currentParams.substrate || defaultParams.substrate;

  // Extract confidence information from predictions if available
  const confidence = predictions
    ? {
        uncertainty: predictions.gain_confidence_lower && predictions.gain_confidence_upper
          ? `±${((predictions.gain_confidence_upper - predictions.gain) * 100 / predictions.gain).toFixed(1)}%`
          : '±2.5%',
        status: 'valid',
        modelName: predictions.model_name || 'default',
        modelVersion: predictions.model_version || '1.0',
      }
    : { uncertainty: 'N/A', status: 'pending', modelName: 'N/A', modelVersion: 'N/A' };

  return (
    <div className="parameters-panel">
      <div className="parameters-panel-header">
        <h3 className="parameters-panel-title">Parameters</h3>
      </div>
      <div className="parameters-panel-content">
        <div className="parameters-section">
          <div className="section-header">Geometry</div>
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
              <span className="param-value">{substrate.substrate_type}</span>
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
        <div className="divider" />
        <div className="parameters-section">
          <div className="section-header">Model Info</div>
          <div className="parameters-display">
            <div className="param-row">
              <span className="param-label">Model:</span>
              <span className="param-value">{confidence.modelName}</span>
            </div>
            <div className="param-row">
              <span className="param-label">Version:</span>
              <span className="param-value">v{confidence.modelVersion}</span>
            </div>
            <div className="param-row">
              <span className="param-label">Uncertainty:</span>
              <span className="param-value mono">{confidence.uncertainty}</span>
            </div>
            <div className="param-row">
              <span className="param-label">Status:</span>
              <span className={`param-value text-${confidence.status === 'valid' ? 'success' : 'secondary'}`}>
                {confidence.status === 'valid' ? 'Valid' : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

