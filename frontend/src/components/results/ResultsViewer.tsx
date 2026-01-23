import React, { useState, useMemo } from 'react';
import { S11Plot } from '../visualization/S11Plot';
import { Table } from '../common/Table';
import { useAntennaStore } from '../../services/state';
import './ResultsViewer.css';

export const ResultsViewer: React.FC = () => {
  const { simulationResults, predictions } = useAntennaStore();
  const [activeView, setActiveView] = useState<'s11' | 'metrics'>('s11');

  // Use actual data from store, fallback to predictions if available
  const activeData = simulationResults || predictions;

  const s11Data = useMemo(() => {
    if (activeData?.s11) {
      return {
        frequency: activeData.s11.frequency.map((f: number) => f / 1e9), // Hz to GHz
        s11Magnitude: activeData.s11.s11_magnitude,
        // Confidence intervals are S11 magnitude values (dB), not frequencies
        confidenceLower: activeData.s11_confidence_lower,
        confidenceUpper: activeData.s11_confidence_upper,
      };
    }
    return null;
  }, [activeData]);

  const metricsData = useMemo(() => {
    if (!activeData) return [];

    const metrics = [];
    
    // S11 Min
    if (activeData.s11?.s11_magnitude) {
      const s11Min = Math.min(...activeData.s11.s11_magnitude);
      metrics.push({
        metric: 'S11 Min',
        value: s11Min.toFixed(2),
        unit: 'dB',
        status: s11Min < -10 ? 'success' : s11Min < -6 ? 'warning' : 'error',
      });
    }

    // Gain with confidence intervals if available
    if (activeData.gain !== undefined) {
      let gainValue = activeData.gain.toFixed(2);
      if (activeData.gain_confidence_lower !== undefined && activeData.gain_confidence_upper !== undefined) {
        gainValue += ` [${activeData.gain_confidence_lower.toFixed(2)}, ${activeData.gain_confidence_upper.toFixed(2)}]`;
      }
      metrics.push({
        metric: 'Peak Gain',
        value: gainValue,
        unit: 'dBi',
        status: activeData.gain > 5 ? 'success' : activeData.gain > 3 ? 'warning' : 'error',
      });
    }

    // Efficiency with confidence intervals if available
    if (activeData.efficiency !== undefined) {
      const efficiencyPercent = activeData.efficiency * 100;
      let efficiencyValue = efficiencyPercent.toFixed(1);
      if (activeData.efficiency_confidence_lower !== undefined && activeData.efficiency_confidence_upper !== undefined) {
        const lower = (activeData.efficiency_confidence_lower * 100).toFixed(1);
        const upper = (activeData.efficiency_confidence_upper * 100).toFixed(1);
        efficiencyValue += ` [${lower}, ${upper}]`;
      }
      metrics.push({
        metric: 'Efficiency',
        value: efficiencyValue,
        unit: '%',
        status: efficiencyPercent > 80 ? 'success' : efficiencyPercent > 60 ? 'warning' : 'error',
      });
    }

    // Bandwidth (-10dB)
    if (activeData.s11?.frequency && activeData.s11?.s11_magnitude) {
      const below10dB = activeData.s11.frequency.filter((_: any, i: number) => 
        activeData.s11.s11_magnitude[i] < -10
      );
      if (below10dB.length > 1) {
        const bandwidth = (below10dB[below10dB.length - 1] - below10dB[0]) / 1e6; // Hz to MHz
        metrics.push({
          metric: 'Bandwidth (-10dB)',
          value: bandwidth.toFixed(0),
          unit: 'MHz',
          status: bandwidth > 100 ? 'success' : bandwidth > 50 ? 'warning' : 'error',
        });
      }
    }

    // Resonant Frequency
    if (activeData.s11?.frequency && activeData.s11?.s11_magnitude) {
      const minIndex = activeData.s11.s11_magnitude.indexOf(Math.min(...activeData.s11.s11_magnitude));
      const resonantFreq = activeData.s11.frequency[minIndex] / 1e9; // Hz to GHz
      const targetFreq = activeData.antenna_parameters?.frequency_band === '2.4GHz' ? 2.4 : 3.5;
      const deviation = Math.abs(resonantFreq - targetFreq);
      metrics.push({
        metric: 'Resonant Frequency',
        value: resonantFreq.toFixed(3),
        unit: 'GHz',
        status: deviation < 0.1 ? 'success' : deviation < 0.2 ? 'warning' : 'error',
      });
    }

    return metrics;
  }, [activeData]);

  const columns = [
    { key: 'metric', label: 'Metric' },
    {
      key: 'value',
      label: 'Value',
      render: (value: string, row: any) => (
        <span className={`metric-value metric-${row.status}`}>
          {value} <span className="metric-unit">{row.unit}</span>
        </span>
      ),
    },
  ];

  return (
    <div className="results-viewer">
      <div className="results-viewer-header">
        <div className="results-viewer-tabs">
          <button
            className={`results-tab ${activeView === 's11' ? 'active' : ''}`}
            onClick={() => setActiveView('s11')}
          >
            S11 Response
          </button>
          <button
            className={`results-tab ${activeView === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveView('metrics')}
          >
            Performance Metrics
          </button>
        </div>
        {activeData && (
          <div className="results-viewer-info">
            <span className="results-source">
              {simulationResults ? 'EM Simulation' : 'Surrogate Prediction'}
            </span>
            {simulationResults && activeData.solver_name && (
              <span className="results-solver">Solver: {activeData.solver_name}</span>
            )}
            {activeData.model_name && (
              <span className="results-model">Model: {activeData.model_name}</span>
            )}
            {activeData.model_version && (
              <span className="results-version">v{activeData.model_version}</span>
            )}
            {activeData.simulation_time !== undefined && (
              <span className="results-time">Time: {activeData.simulation_time.toFixed(2)}s</span>
            )}
            {activeData.prediction_time !== undefined && (
              <span className="results-time">Time: {activeData.prediction_time.toFixed(3)}s</span>
            )}
          </div>
        )}
      </div>

      <div className="results-viewer-content">
        {!activeData && (
          <div className="results-placeholder">
            <p>No results available. Run a simulation or get a prediction to view results.</p>
          </div>
        )}

        {activeView === 's11' && s11Data && (
          <div className="results-plot-container">
            <S11Plot
              frequency={s11Data.frequency}
              s11Magnitude={s11Data.s11Magnitude}
              confidenceLower={s11Data.confidenceLower}
              confidenceUpper={s11Data.confidenceUpper}
            />
          </div>
        )}

        {activeView === 'metrics' && metricsData.length > 0 && (
          <div className="results-metrics">
            <Table columns={columns} data={metricsData} />
          </div>
        )}

        {activeView === 'metrics' && metricsData.length === 0 && activeData && (
          <div className="results-placeholder">
            <p>No metrics available in results data.</p>
          </div>
        )}
      </div>
    </div>
  );
};
