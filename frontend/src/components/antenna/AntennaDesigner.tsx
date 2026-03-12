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

// Defaults within model training range: L 30–35 mm, W 26–31 mm, H 1.2–2 mm, Feed X −7 to −3 mm, εr 3.8–4.6, tan δ 0–0.02
const DEFAULT_PARAMS: AntennaParams = {
  length: 32.5,
  width: 28.5,
  height: 1.6,
  feedX: -5.0,
  feedY: 0.0,
  substrateType: 'fr4',
  permittivity: 4.4,
  lossTangent: 0.02,
  frequencyBand: '2.4ghz',
};

export const AntennaDesigner: React.FC = () => {
  const [params, setParams] = useState<AntennaParams>(DEFAULT_PARAMS);

  const [isSimulating, setIsSimulating] = useState(false);
  const [isRunningOpenEMS, setIsRunningOpenEMS] = useState(false);
  const [s11Data, setS11Data] = useState<{ frequency: number[]; s11Magnitude: number[]; resonanceFrequencyGHz?: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const { setParameters, setSimulationResults } = useAntennaStore();

  // Sync params to store: convert feed offset (mm) to absolute position (m)
  useEffect(() => {
    const feedXAbsMm = Math.max(0, Math.min(params.length, params.length / 2 + params.feedX));
    const feedYAbsMm = Math.max(0, Math.min(params.width, params.width / 2 + params.feedY));
    const antennaParams = {
      geometry: {
        length: params.length / 1000, // mm to m
        width: params.width / 1000,
        height: params.height / 1000,
        feed_x: feedXAbsMm / 1000,
        feed_y: feedYAbsMm / 1000,
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
    const feedXAbs = params.length / 2 + params.feedX;
    const feedYAbs = params.width / 2 + params.feedY;
    if (feedXAbs < 0 || feedXAbs > params.length) {
      errors.push({ field: 'feedX', message: `Feed X offset: keep on patch (−${(params.length / 2).toFixed(0)} to +${(params.length / 2).toFixed(0)} mm). Training: −7 to −3 mm` });
    }
    if (feedYAbs < 0 || feedYAbs > params.width) {
      errors.push({ field: 'feedY', message: `Feed Y offset: keep on patch (−${(params.width / 2).toFixed(0)} to +${(params.width / 2).toFixed(0)} mm)` });
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
      const feedXAbsMm = Math.max(0, Math.min(params.length, params.length / 2 + params.feedX));
      const feedYAbsMm = Math.max(0, Math.min(params.width, params.width / 2 + params.feedY));
      const antennaParams = {
        geometry: {
          length: params.length / 1000,
          width: params.width / 1000,
          height: params.height / 1000,
          feed_x: feedXAbsMm / 1000,
          feed_y: feedYAbsMm / 1000,
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

      // Use surrogate model by default (fast). For full EM use solver_name: 'openems'.
      const response = await api.post('/em/simulate', antennaParams, {
        params: { solver_name: 'surrogate' },
        timeout: 60000, // 1 min for model; use 300000 if using openems
      });
      
      
      if (response.data && response.data.s11) {
        const freqGHz = response.data.s11.frequency.map((f: number) => f / 1e9);
        const mag = response.data.s11.s11_magnitude;
        const resHz = response.data.metadata?.resonance_frequency;
        setS11Data({
          frequency: freqGHz,
          s11Magnitude: mag,
          resonanceFrequencyGHz: resHz != null ? resHz / 1e9 : undefined,
        });
        setParameters(response.data.antenna_parameters || antennaParams);
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

  const handleRunOpenEMS = async () => {
    setError(null);
    const errors = validateParameters();
    if (errors.length > 0) {
      setValidationErrors(errors);
      setError(`Validation failed: ${errors.map((e) => e.message).join(', ')}`);
      return;
    }
    setIsRunningOpenEMS(true);
    setValidationErrors([]);
    try {
      const feedXAbsMm = Math.max(0, Math.min(params.length, params.length / 2 + params.feedX));
      const feedYAbsMm = Math.max(0, Math.min(params.width, params.width / 2 + params.feedY));
      const antennaParams = {
        geometry: {
          length: params.length / 1000,
          width: params.width / 1000,
          height: params.height / 1000,
          feed_x: feedXAbsMm / 1000,
          feed_y: feedYAbsMm / 1000,
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
        params: { solver_name: 'openems', fast: false },
        timeout: 300000, // 5 min for full FDTD
      });
      if (response.data && response.data.s11) {
        const freqGHz = response.data.s11.frequency.map((f: number) => f / 1e9);
        const mag = response.data.s11.s11_magnitude;
        const resHz = response.data.metadata?.resonance_frequency;
        setS11Data({
          frequency: freqGHz,
          s11Magnitude: mag,
          resonanceFrequencyGHz: resHz != null ? resHz / 1e9 : undefined,
        });
        setParameters(response.data.antenna_parameters || antennaParams);
        setSimulationResults(response.data);
        setError(null);
      } else {
        throw new Error('Invalid response format from OpenEMS simulation');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'OpenEMS simulation failed.';
      setError(`OpenEMS: ${msg}`);
      console.error('OpenEMS error:', err);
    } finally {
      setIsRunningOpenEMS(false);
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
            label="Feed X offset"
            type="number"
            unit="mm"
            value={params.feedX.toString()}
            onChange={handleNumberInputChange('feedX')}
            error={getFieldError('feedX')}
            min="-20"
            max="20"
            step="0.1"
            title="Offset from patch center. Training range: −7 to −3 mm"
          />
          <Input
            label="Feed Y offset"
            type="number"
            unit="mm"
            value={params.feedY.toString()}
            onChange={handleNumberInputChange('feedY')}
            error={getFieldError('feedY')}
            min="-20"
            max="20"
            step="0.1"
            title="Offset from patch center (0 = center)"
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
            onChange={(e) => {
              const band = e.target.value as '2.4ghz' | '3.5ghz';
              setParams((prev) => ({
                ...prev,
                frequencyBand: band,
                length: band === '2.4ghz' ? 29.0 : 21.0,
                width: band === '2.4ghz' ? 36.0 : 26.0,
                feedX: band === '2.4ghz' ? -5.0 : -3.0,  // offset from center (training range −7 to −3)
                feedY: 0.0,
              }));
            }}
          />
        </div>

        <div className="antenna-designer-actions">
          <Button
            variant="primary"
            onClick={handleRunSimulation}
            disabled={isSimulating || isRunningOpenEMS}
          >
            {isSimulating ? 'Running…' : 'Get result (model)'}
          </Button>
          <Button
            variant="secondary"
            onClick={handleRunOpenEMS}
            disabled={isSimulating || isRunningOpenEMS}
          >
            {isRunningOpenEMS ? 'OpenEMS running…' : 'Run with OpenEMS'}
          </Button>
        </div>
        <p className="result-comparison-note" style={{ fontSize: '12px', color: 'var(--color-text-secondary, #666)', marginTop: '8px', maxWidth: '520px' }}>
          Model is for <strong>2.4&#8203;GHz</strong> band. Trained on 1200 OpenEMS runs. Reliable within: L 30–35&#8203;mm, W 26–31&#8203;mm, H 1.2–2&#8203;mm, Feed X offset −7 to −3&#8203;mm, εr 3.8–4.6.
        </p>
      </div>

      <div className="antenna-designer-visualization">
        {s11Data ? (
          <S11Plot
            frequency={s11Data.frequency}
            s11Magnitude={s11Data.s11Magnitude}
          />
        ) : (
          <div className="visualization-placeholder">
            <p>Get result (model) to view S11 and metrics</p>
          </div>
        )}
      </div>
    </div>
  );
};
