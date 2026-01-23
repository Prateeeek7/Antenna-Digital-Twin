import React, { useState } from 'react';
import { Input } from '../common/Input';
import { Button } from '../common/Button';
import { Select } from '../common/Select';
import { useAntennaStore } from '../../services/state';
import api from '../../services/api';
import './OptimizationPanel.css';

export const OptimizationPanel: React.FC = () => {
  const { parameters, setParameters } = useAntennaStore();
  const [objective, setObjective] = useState('minimize_s11');
  const [targetS11, setTargetS11] = useState('-10.0');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [whatIfVariation, setWhatIfVariation] = useState({ length: 0, width: 0 });
  const [whatIfResult, setWhatIfResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleOptimize = async () => {
    if (!parameters) {
      setError('Please set antenna parameters first');
      return;
    }

    setIsOptimizing(true);
    setError(null);
    try {
      const response = await api.post('/optimization/optimize', parameters, {
        params: {
          objective,
          target_s11: parseFloat(targetS11),
        },
      });

      setOptimizationResult({
        optimized: true,
        optimizedParameters: response.data,
      });
      setParameters(response.data);
      setError(null);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Optimization failed';
      setError(`Optimization Error: ${errorMessage}`);
      console.error('Optimization error:', err);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleWhatIfAnalysis = async () => {
    if (!parameters) {
      setError('Please set antenna parameters first');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    try {
      const variation: Record<string, number> = {};
      if (whatIfVariation.length !== 0) {
        variation.length = whatIfVariation.length / 100; // Convert percentage to factor
      }
      if (whatIfVariation.width !== 0) {
        variation.width = whatIfVariation.width / 100;
      }

      // Send variation in request body
      const response = await api.post('/optimization/what-if', {
        parameters: parameters,
        variation: variation,
      });

      setWhatIfResult(response.data);
      setError(null);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'What-if analysis failed';
      setError(`Analysis Error: ${errorMessage}`);
      console.error('What-if analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="optimization-panel">
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      <div className="section-header">Optimization Settings</div>
      
      <div className="input-group">
        <Select
          label="Objective"
          options={[
            { value: 'minimize_s11', label: 'Minimize S11' },
            { value: 'maximize_gain', label: 'Maximize Gain' },
            { value: 'maximize_efficiency', label: 'Maximize Efficiency' },
          ]}
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
        />
      </div>

      {objective === 'minimize_s11' && (
        <div className="input-group">
          <Input
            label="Target S11"
            type="number"
            unit="dB"
            value={targetS11}
            onChange={(e) => setTargetS11(e.target.value)}
            min="-40"
            max="0"
            step="0.1"
          />
        </div>
      )}

      <div className="optimization-actions">
        <Button
          variant="primary"
          onClick={handleOptimize}
          disabled={isOptimizing || !parameters}
        >
          {isOptimizing ? 'Optimizing...' : 'Start Optimization'}
        </Button>
      </div>

      {optimizationResult && (
        <div className="optimization-results">
          <div className="section-header">Optimization Results</div>
          <div className="result-item">
            <span className="result-label">Status:</span>
            <span className="result-value text-success">Optimized</span>
          </div>
          {optimizationResult.optimizedParameters && (
            <div className="result-item">
              <span className="result-label">Optimized Length:</span>
              <span className="result-value">
                {(optimizationResult.optimizedParameters.geometry.length * 1000).toFixed(2)} mm
              </span>
            </div>
          )}
          {optimizationResult.optimizedParameters && (
            <div className="result-item">
              <span className="result-label">Optimized Width:</span>
              <span className="result-value">
                {(optimizationResult.optimizedParameters.geometry.width * 1000).toFixed(2)} mm
              </span>
            </div>
          )}
        </div>
      )}

      <div className="divider" />

      <div className="section-header">What-If Analysis</div>
      <div className="whatif-controls">
        <div className="input-group">
          <Input
            label="Length Variation"
            type="number"
            unit="%"
            value={whatIfVariation.length.toString()}
            onChange={(e) => setWhatIfVariation((prev) => ({ ...prev, length: parseFloat(e.target.value) || 0 }))}
            placeholder="±10"
            min="-50"
            max="50"
            step="1"
          />
        </div>
        <div className="input-group">
          <Input
            label="Width Variation"
            type="number"
            unit="%"
            value={whatIfVariation.width.toString()}
            onChange={(e) => setWhatIfVariation((prev) => ({ ...prev, width: parseFloat(e.target.value) || 0 }))}
            placeholder="±10"
            min="-50"
            max="50"
            step="1"
          />
        </div>
        <Button 
          variant="secondary"
          onClick={handleWhatIfAnalysis}
          disabled={isAnalyzing || !parameters}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze'}
        </Button>
      </div>

      {whatIfResult && (
        <div className="whatif-results">
          <div className="section-header">Analysis Results</div>
          <div className="result-item">
            <span className="result-label">Predicted S11:</span>
            <span className="result-value">
              {whatIfResult.s11_min?.toFixed(2) || 'N/A'} dB
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Predicted Gain:</span>
            <span className="result-value">
              {whatIfResult.gain?.toFixed(2) || 'N/A'} dBi
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
