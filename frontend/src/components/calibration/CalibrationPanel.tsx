import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { Select } from '../common/Select';
import { Table } from '../common/Table';
import api from '../../services/api';
import { useAntennaStore } from '../../services/state';
import './CalibrationPanel.css';

interface CalibrationResult {
  antenna_instance_id: string;
  measurement_id: string;
  discrepancy: {
    s11_min?: {
      predicted: number;
      measured: number;
      difference: number;
      relative_error: number;
    };
    gain?: {
      predicted: number;
      measured: number;
      difference: number;
      relative_error: number;
    };
    efficiency?: {
      predicted: number;
      measured: number;
      difference: number;
      relative_error: number;
    };
  };
  calibration_confidence: number;
  calibration_status: string;
  timestamp: string;
}

interface Measurement {
  measurement_id: string;
  antenna_instance_id: string;
  measured_at: string;
  gain?: number;
  efficiency?: number;
  quality_score?: number;
}

export const CalibrationPanel: React.FC = () => {
  const { antennaType } = useAntennaStore();
  const [instances, setInstances] = useState<Array<{ instance_id: string }>>([]);
  const [selectedInstance, setSelectedInstance] = useState('');
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [selectedMeasurement, setSelectedMeasurement] = useState('');
  const [calibrating, setCalibrating] = useState(false);
  const [calibrationResult, setCalibrationResult] = useState<CalibrationResult | null>(null);
  const [calibrationHistory, setCalibrationHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    fetchInstances();
  }, []);

  useEffect(() => {
    if (selectedInstance) {
      fetchMeasurements(selectedInstance);
      fetchCalibrationHistory(selectedInstance);
    }
  }, [selectedInstance]);

  const fetchInstances = async () => {
    try {
      const response = await api.get('/antenna-instances/');
      setInstances(response.data || []);
    } catch (err) {
      console.error('Failed to fetch instances:', err);
    }
  };

  const fetchMeasurements = async (instanceId: string) => {
    try {
      const response = await api.get('/measurements/', {
        params: { antenna_instance_id: instanceId, limit: 50 },
      });
      setMeasurements(response.data || []);
    } catch (err) {
      console.error('Failed to fetch measurements:', err);
    }
  };

  const fetchCalibrationHistory = async (instanceId: string) => {
    try {
      setLoadingHistory(true);
      const response = await api.get(`/calibration/history/${instanceId}`);
      setCalibrationHistory(response.data.history || []);
    } catch (err) {
      console.error('Failed to fetch calibration history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleCalibrate = async () => {
    if (!selectedInstance || !selectedMeasurement) {
      setError('Please select both antenna instance and measurement');
      return;
    }

    setCalibrating(true);
    setError(null);
    setCalibrationResult(null);

    try {
      const response = await api.post(
        `/calibration/calibrate/${selectedInstance}?measurement_id=${selectedMeasurement}`
      );
      setCalibrationResult(response.data);
      fetchCalibrationHistory(selectedInstance);
    } catch (err: any) {
      setError(`Calibration failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setCalibrating(false);
    }
  };

  const historyColumns = [
    { key: 'measurement_id', label: 'Measurement ID' },
    {
      key: 'measured_at',
      label: 'Date',
      render: (value: string) => value ? new Date(value).toLocaleDateString() : 'N/A',
    },
    {
      key: 'gain',
      label: 'Gain (dBi)',
      render: (value: number) => value ? value.toFixed(2) : 'N/A',
    },
    {
      key: 'efficiency',
      label: 'Efficiency (%)',
      render: (value: number) => value ? (value * 100).toFixed(1) : 'N/A',
    },
    {
      key: 'quality_score',
      label: 'Quality',
      render: (value: number) => value ? (value * 100).toFixed(1) + '%' : 'N/A',
    },
  ];

  return (
    <div className="calibration-panel">
      <div className="section-header">Calibration Workflow</div>
      {antennaType === 'dipole' && (
        <p className="result-comparison-note" style={{ marginBottom: 12, maxWidth: 560 }}>
          Select an instance that matches your dipole (saved from Designer). Calibration compares model predictions to
          uploaded measurements the same way as for microstrip.
        </p>
      )}

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      <div className="calibration-form">
        <div className="input-group">
          <Select
            label="Antenna Instance"
            value={selectedInstance}
            onChange={(e) => setSelectedInstance(e.target.value)}
            options={[
              { value: '', label: 'Select instance...' },
              ...instances.map((inst) => ({
                value: inst.instance_id,
                label: inst.instance_id,
              })),
            ]}
          />

          {selectedInstance && (
            <Select
              label="Measurement"
              value={selectedMeasurement}
              onChange={(e) => setSelectedMeasurement(e.target.value)}
              options={[
                { value: '', label: 'Select measurement...' },
                ...measurements.map((meas) => ({
                  value: meas.measurement_id,
                  label: `${meas.measurement_id} (${meas.measured_at ? new Date(meas.measured_at).toLocaleDateString() : 'N/A'})`,
                })),
              ]}
            />
          )}
        </div>

        <div className="calibration-actions">
          <Button
            variant="primary"
            onClick={handleCalibrate}
            disabled={!selectedInstance || !selectedMeasurement || calibrating}
          >
            {calibrating ? 'Calibrating...' : 'Run Calibration'}
          </Button>
        </div>
      </div>

      {calibrationResult && (
        <div className="calibration-results">
          <div className="section-header">Calibration Results</div>
          <div className="result-grid">
            <div className="result-item">
              <span className="result-label">Status:</span>
              <span className={`result-value text-${calibrationResult.calibration_status === 'calibrated' ? 'success' : 'warning'}`}>
                {calibrationResult.calibration_status}
              </span>
            </div>
            <div className="result-item">
              <span className="result-label">Confidence:</span>
              <span className="result-value">
                {(calibrationResult.calibration_confidence * 100).toFixed(1)}%
              </span>
            </div>
            {calibrationResult.discrepancy.s11_min && (
              <div className="result-item">
                <span className="result-label">S11 Error:</span>
                <span className="result-value">
                  {calibrationResult.discrepancy.s11_min.relative_error
                    ? (calibrationResult.discrepancy.s11_min.relative_error * 100).toFixed(2) + '%'
                    : 'N/A'}
                </span>
              </div>
            )}
            {calibrationResult.discrepancy.gain && (
              <div className="result-item">
                <span className="result-label">Gain Error:</span>
                <span className="result-value">
                  {calibrationResult.discrepancy.gain.relative_error
                    ? (calibrationResult.discrepancy.gain.relative_error * 100).toFixed(2) + '%'
                    : 'N/A'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedInstance && (
        <div className="calibration-history">
          <div className="section-header">Calibration History</div>
          {loadingHistory ? (
            <div className="loading-message">Loading history...</div>
          ) : calibrationHistory.length === 0 ? (
            <div className="no-data-message">No calibration history available</div>
          ) : (
            <Table columns={historyColumns} data={calibrationHistory} />
          )}
        </div>
      )}
    </div>
  );
};
