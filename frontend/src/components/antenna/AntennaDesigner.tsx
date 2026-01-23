import React, { useState, useEffect } from 'react';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Button } from '../common/Button';
import { S11Plot } from '../visualization/S11Plot';
import { useAntennaStore } from '../../services/state';
import api from '../../services/api';
import './AntennaDesigner.css';

interface AntennaParams {
  length: number;
  width: number;
  height: number;
  feedX: number;
  feedY: number;
  substrateType: string;
  permittivity: number;
  lossTangent: number;
  frequencyBand: string;
}

interface ValidationError {
  field: string;
  message: string;
}

export const AntennaDesigner: React.FC = () => {
  const [params, setParams] = useState<AntennaParams>({
    length: 30.0,
    width: 40.0,
    height: 1.6,
    feedX: 15.0,
    feedY: 20.0,
    substrateType: 'fr4',
    permittivity: 4.4,
    lossTangent: 0.02,
    frequencyBand: '2.4ghz',
  });

  const [isSimulating, setIsSimulating] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [s11Data, setS11Data] = useState<{ frequency: number[]; s11Magnitude: number[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const { setParameters, setPredictions, setSimulationResults } = useAntennaStore();

  // Sync params to store when they change
  useEffect(() => {
    const antennaParams = {
      geometry: {
        length: params.length / 1000, // mm to m
        width: params.width / 1000,
        height: params.height / 1000,
        feed_x: params.feedX / 1000,
        feed_y: params.feedY / 1000,
      },
      substrate: {
        substrate_type: params.substrateType.toUpperCase(),
        relative_permittivity: params.permittivity,
        loss_tangent: params.lossTangent,
        thickness: params.height / 1000,
      },
      feed_type: 'INSET',
      frequency_band: params.frequencyBand === '2.4ghz' ? '2.4GHz' : '3.5GHz',
      frequency_range: params.frequencyBand === '2.4ghz' ? [2.0e9, 3.0e9] : [3.0e9, 4.0e9],
    };
    setParameters(antennaParams);
  }, [params, setParameters]);

  const validateParameters = (): ValidationError[] => {
    const errors: ValidationError[] = [];

    if (params.length <= 0 || params.length > 100) {
      errors.push({ field: 'length', message: 'Length must be between 0.1 and 100 mm' });
    }
    if (params.width <= 0 || params.width > 100) {
      errors.push({ field: 'width', message: 'Width must be between 0.1 and 100 mm' });
    }
    if (params.height <= 0 || params.height > 10) {
      errors.push({ field: 'height', message: 'Height must be between 0.1 and 10 mm' });
    }
    if (params.feedX < 0 || params.feedX > params.length) {
      errors.push({ field: 'feedX', message: `Feed X must be between 0 and ${params.length.toFixed(2)} mm` });
    }
    if (params.feedY < 0 || params.feedY > params.width) {
      errors.push({ field: 'feedY', message: `Feed Y must be between 0 and ${params.width.toFixed(2)} mm` });
    }
    if (params.permittivity < 1.0 || params.permittivity > 20.0) {
      errors.push({ field: 'permittivity', message: 'Relative permittivity must be between 1.0 and 20.0' });
    }
    if (params.lossTangent < 0 || params.lossTangent > 1.0) {
      errors.push({ field: 'lossTangent', message: 'Loss tangent must be between 0 and 1.0' });
    }

    return errors;
  };

  const handleParamChange = (field: keyof AntennaParams, value: string | number) => {
    setParams((prev) => ({ ...prev, [field]: value }));
    // Clear validation errors for this field
    setValidationErrors((prev) => prev.filter((e) => e.field !== field));
    setError(null);
  };

  const handleNumberInputChange = (field: keyof AntennaParams) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.trim();
    if (val === '') {
      handleParamChange(field, 0);
      return;
    }
    const numVal = parseFloat(val);
    if (!isNaN(numVal) && isFinite(numVal)) {
      handleParamChange(field, numVal);
    }
  };

  const handleRunSimulation = async () => {
    setError(null);
    const errors = validateParameters();
    if (errors.length > 0) {
      setValidationErrors(errors);
      setError(`Validation failed: ${errors.map((e) => e.message).join(', ')}`);
      return;
    }

    setIsSimulating(true);
    setValidationErrors([]);
    try {
      const antennaParams = {
        geometry: {
          length: params.length / 1000, // mm to m
          width: params.width / 1000,
          height: params.height / 1000,
          feed_x: params.feedX / 1000,
          feed_y: params.feedY / 1000,
        },
        substrate: {
          substrate_type: params.substrateType.toUpperCase(),
          relative_permittivity: params.permittivity,
          loss_tangent: params.lossTangent,
          thickness: params.height / 1000,
        },
        feed_type: 'INSET',
        frequency_band: params.frequencyBand === '2.4ghz' ? '2.4GHz' : '3.5GHz',
        frequency_range: params.frequencyBand === '2.4ghz' ? [2.0e9, 3.0e9] : [3.0e9, 4.0e9],
      };

      const response = await api.post('/em/simulate', antennaParams, {
        params: { solver_name: 'meep' },
      });
      
      console.log('Simulation response:', response.data);
      
      if (response.data && response.data.s11) {
        setS11Data({
          frequency: response.data.s11.frequency.map((f: number) => f / 1e9), // Hz to GHz
          s11Magnitude: response.data.s11.s11_magnitude,
        });
        setParameters(antennaParams);
        // Store full simulation results including gain, efficiency, solver info, etc.
        setSimulationResults(response.data);
        setError(null);
      } else {
        console.error('Invalid simulation response:', response.data);
        throw new Error('Invalid response format from simulation');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Simulation failed. Please check your parameters and try again.';
      setError(`Simulation Error: ${errorMessage}`);
      console.error('Simulation error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleGetPrediction = async () => {
    setError(null);
    const errors = validateParameters();
    if (errors.length > 0) {
      setValidationErrors(errors);
      setError(`Validation failed: ${errors.map((e) => e.message).join(', ')}`);
      return;
    }

    setIsPredicting(true);
    setValidationErrors([]);
    try {
      const antennaParams = {
        geometry: {
          length: params.length / 1000,
          width: params.width / 1000,
          height: params.height / 1000,
          feed_x: params.feedX / 1000,
          feed_y: params.feedY / 1000,
        },
        substrate: {
          substrate_type: params.substrateType.toUpperCase(),
          relative_permittivity: params.permittivity,
          loss_tangent: params.lossTangent,
          thickness: params.height / 1000,
        },
        feed_type: 'INSET',
        frequency_band: params.frequencyBand === '2.4ghz' ? '2.4GHz' : '3.5GHz',
        frequency_range: params.frequencyBand === '2.4ghz' ? [2.0e9, 3.0e9] : [3.0e9, 4.0e9],
      };

      const response = await api.post('/predictions/predict', antennaParams);
      
      console.log('Prediction response:', response.data);
      
      if (response.data && response.data.s11) {
        setS11Data({
          frequency: response.data.s11.frequency.map((f: number) => f / 1e9),
          s11Magnitude: response.data.s11.s11_magnitude,
        });
        // Store full prediction results including gain, efficiency, confidence intervals, model info, etc.
        setPredictions(response.data);
        setError(null);
      } else {
        console.error('Invalid prediction response:', response.data);
        throw new Error('Invalid response format from prediction service');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Prediction failed. Please check your parameters and try again.';
      setError(`Prediction Error: ${errorMessage}`);
      console.error('Prediction error:', err);
    } finally {
      setIsPredicting(false);
    }
  };

  const getFieldError = (fieldName: string): string | undefined => {
    return validationErrors.find((e) => e.field === fieldName)?.message;
  };

  return (
    <div className="antenna-designer">
      <div className="antenna-designer-form">
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <div className="section-header">Geometry Parameters</div>
        <div className="input-group">
          <Input
            label="Length (L)"
            type="number"
            unit="mm"
            value={params.length.toString()}
            onChange={handleNumberInputChange('length')}
            error={getFieldError('length')}
            min="0.1"
            max="100"
            step="0.1"
          />
          <Input
            label="Width (W)"
            type="number"
            unit="mm"
            value={params.width.toString()}
            onChange={handleNumberInputChange('width')}
            error={getFieldError('width')}
            min="0.1"
            max="100"
            step="0.1"
          />
          <Input
            label="Height (h)"
            type="number"
            unit="mm"
            value={params.height.toString()}
            onChange={handleNumberInputChange('height')}
            error={getFieldError('height')}
            min="0.1"
            max="10"
            step="0.01"
          />
          <Input
            label="Feed X"
            type="number"
            unit="mm"
            value={params.feedX.toString()}
            onChange={handleNumberInputChange('feedX')}
            error={getFieldError('feedX')}
            min="0"
            step="0.1"
          />
          <Input
            label="Feed Y"
            type="number"
            unit="mm"
            value={params.feedY.toString()}
            onChange={handleNumberInputChange('feedY')}
            error={getFieldError('feedY')}
            min="0"
            step="0.1"
          />
        </div>

        <div className="divider" />

        <div className="section-header">Substrate Properties</div>
        <div className="input-group">
          <Select
            label="Substrate Type"
            options={[
              { value: 'fr4', label: 'FR-4' },
              { value: 'ro4003', label: 'Rogers RO4003' },
              { value: 'ro4350', label: 'Rogers RO4350' },
            ]}
            value={params.substrateType}
            onChange={(e) => {
              const type = e.target.value;
              handleParamChange('substrateType', type);
              if (type === 'fr4') {
                handleParamChange('permittivity', 4.4);
                handleParamChange('lossTangent', 0.02);
              } else if (type === 'ro4003') {
                handleParamChange('permittivity', 3.38);
                handleParamChange('lossTangent', 0.0027);
              } else if (type === 'ro4350') {
                handleParamChange('permittivity', 3.48);
                handleParamChange('lossTangent', 0.0037);
              }
            }}
          />
          <Input
            label="Relative Permittivity (εr)"
            type="number"
            step="0.1"
            value={params.permittivity.toString()}
            onChange={handleNumberInputChange('permittivity')}
            error={getFieldError('permittivity')}
            min="1.0"
            max="20.0"
          />
          <Input
            label="Loss Tangent (tan δ)"
            type="number"
            step="0.001"
            value={params.lossTangent.toString()}
            onChange={handleNumberInputChange('lossTangent')}
            error={getFieldError('lossTangent')}
            min="0"
            max="1.0"
          />
        </div>

        <div className="divider" />

        <div className="section-header">Frequency</div>
        <div className="input-group">
          <Select
            label="Frequency Band"
            options={[
              { value: '2.4ghz', label: '2.4 GHz' },
              { value: '3.5ghz', label: '3.5 GHz' },
            ]}
            value={params.frequencyBand}
            onChange={(e) => handleParamChange('frequencyBand', e.target.value)}
          />
        </div>

        <div className="antenna-designer-actions">
          <Button
            variant="primary"
            onClick={handleRunSimulation}
            disabled={isSimulating || isPredicting}
          >
            {isSimulating ? 'Running Simulation...' : 'Run Simulation'}
          </Button>
          <Button
            variant="secondary"
            onClick={handleGetPrediction}
            disabled={isSimulating || isPredicting}
          >
            {isPredicting ? 'Computing Prediction...' : 'Get Prediction'}
          </Button>
        </div>
      </div>

      <div className="antenna-designer-visualization">
        {s11Data ? (
          <S11Plot
            frequency={s11Data.frequency}
            s11Magnitude={s11Data.s11Magnitude}
          />
        ) : (
          <div className="visualization-placeholder">
            <p>Run simulation or get prediction to view S11 response</p>
          </div>
        )}
      </div>
    </div>
  );
};
