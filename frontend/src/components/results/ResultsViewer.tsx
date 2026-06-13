import React, { useState, useMemo } from 'react';
import { S11Plot } from '../visualization/S11Plot';
import { Table } from '../common/Table';
import { useAntennaStore } from '../../services/state';
import './ResultsViewer.css';

export const ResultsViewer: React.FC = () => {
  const { simulationResults, predictions, antennaType } = useAntennaStore();
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

    // Gain: typical patch 4–8 dBi; thin dipole surrogate often ~1.5–3 dBi
    if (activeData.gain !== undefined) {
      let gainValue = activeData.gain.toFixed(2);
      if (activeData.gain_confidence_lower !== undefined && activeData.gain_confidence_upper !== undefined) {
        gainValue += ` [${activeData.gain_confidence_lower.toFixed(2)}, ${activeData.gain_confidence_upper.toFixed(2)}]`;
      }
      const g = activeData.gain;
      const gainOk =
        antennaType === 'dipole'
          ? g >= 1.2 && g <= 4.0
          : g >= 4 && g <= 8;
      const gainWarn =
        antennaType === 'dipole'
          ? g >= 0 && g <= 5.5
          : g >= 3 && g <= 9;
      metrics.push({
        metric: 'Peak Gain',
        value: gainValue,
        unit: 'dBi',
        status: gainOk ? 'success' : gainWarn ? 'warning' : 'error',
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

    // Bandwidth (-10dB): contiguous interval around resonant frequency (not full sweep)
    if (activeData.s11?.frequency && activeData.s11?.s11_magnitude) {
      const mags = activeData.s11.s11_magnitude;
      const freqs = activeData.s11.frequency;
      const minIdx = mags.indexOf(Math.min(...mags));
      let lo = minIdx;
      let hi = minIdx;
      while (lo > 0 && mags[lo - 1] < -10) lo -= 1;
      while (hi < freqs.length - 1 && mags[hi + 1] < -10) hi += 1;
      if (hi > lo) {
        const bandwidthHz = freqs[hi] - freqs[lo];
        const bandwidth = bandwidthHz / 1e6;
        const bwOk = bandwidth >= 20 && bandwidth <= 150;
        const bwWarn = bandwidth >= 10 && bandwidth <= 200;
        metrics.push({
          metric: 'Bandwidth (-10dB)',
          value: bandwidth.toFixed(0),
          unit: 'MHz',
          status: bwOk ? 'success' : bwWarn ? 'warning' : 'error',
        });
      }
    }

    // Resonant Frequency: use design center from frequency_range when available
    if (activeData.s11?.frequency && activeData.s11?.s11_magnitude) {
      const minIndex = activeData.s11.s11_magnitude.indexOf(Math.min(...activeData.s11.s11_magnitude));
      const resonantFreq = activeData.s11.frequency[minIndex] / 1e9; // Hz to GHz
      const band = activeData.antenna_parameters?.frequency_band;
      const range = activeData.antenna_parameters?.frequency_range;
      const targetFreq = range && Array.isArray(range) && range.length === 2
        ? (range[0] + range[1]) / 2 / 1e9
        : (band === '3.5GHz' ? 3.5 : 2.4);
      const deviation = Math.abs(resonantFreq - targetFreq);
      const devPct = targetFreq > 0 ? (deviation / targetFreq) * 100 : deviation * 100;
      metrics.push({
        metric: 'Resonant Frequency',
        value: resonantFreq.toFixed(3),
        unit: 'GHz',
        status: devPct < 3 ? 'success' : devPct < 6 ? 'warning' : 'error',
      });
    }

    return metrics;
  }, [activeData, antennaType]);

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
              {simulationResults?.solver_name === 'surrogate'
                ? 'Model (Surrogate)'
                : simulationResults
                  ? 'EM Simulation'
                  : 'Surrogate Prediction'}
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
            {antennaType === 'dipole' && (
              <p style={{ marginTop: 8, fontSize: 13, opacity: 0.85 }}>
                For the dipole twin, run <strong>Get result (dipole model)</strong> on the Designer tab first.
              </p>
            )}
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
