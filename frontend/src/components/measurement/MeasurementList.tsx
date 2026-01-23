import React, { useState, useEffect } from 'react';
import { Table } from '../common/Table';
import { Select } from '../common/Select';
import api from '../../services/api';
import './MeasurementList.css';

interface Measurement {
  id: string;
  measurement_id: string;
  antenna_instance_id: string | null;
  gain: number | null;
  efficiency: number | null;
  temperature: number | null;
  humidity: number | null;
  quality_score: number | null;
  measured_at: string | null;
  created_at: string | null;
}

export const MeasurementList: React.FC = () => {
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [instances, setInstances] = useState<Array<{ instance_id: string }>>([]);
  const [selectedInstance, setSelectedInstance] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInstances();
  }, []);

  useEffect(() => {
    fetchMeasurements();
  }, [selectedInstance]);

  const fetchInstances = async () => {
    try {
      const response = await api.get('/antenna-instances/');
      setInstances(response.data || []);
    } catch (err) {
      console.error('Failed to fetch instances:', err);
    }
  };

  const fetchMeasurements = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (selectedInstance) {
        params.antenna_instance_id = selectedInstance;
      }
      const response = await api.get('/measurements/', { params });
      setMeasurements(response.data || []);
      setError(null);
    } catch (err: any) {
      setError(`Failed to load measurements: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { key: 'measurement_id', label: 'Measurement ID' },
    {
      key: 'antenna_instance_id',
      label: 'Instance ID',
      render: (value: string) => value || 'N/A',
    },
    {
      key: 'measured_at',
      label: 'Measured At',
      render: (value: string) => value ? new Date(value).toLocaleString() : 'N/A',
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
    {
      key: 'temperature',
      label: 'Temp (°C)',
      render: (value: number) => value ? value.toFixed(1) : 'N/A',
    },
  ];

  return (
    <div className="measurement-list">
      <div className="measurement-list-header">
        <h2 className="section-header">Measurement List</h2>
        <Select
          value={selectedInstance}
          onChange={(e) => setSelectedInstance(e.target.value)}
          options={[
            { value: '', label: 'All Instances' },
            ...instances.map((inst) => ({
              value: inst.instance_id,
              label: inst.instance_id,
            })),
          ]}
        />
      </div>

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-message">Loading measurements...</div>
      ) : measurements.length === 0 ? (
        <div className="no-data-message">No measurements found</div>
      ) : (
        <Table columns={columns} data={measurements} />
      )}
    </div>
  );
};
