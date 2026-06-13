import React, { useState, useEffect } from 'react';
import { Table } from '../common/Table';
import api from '../../services/api';
import { useAntennaStore } from '../../services/state';
import './ValidationDashboard.css';

export const ValidationDashboard: React.FC = () => {
  const { antennaType } = useAntennaStore();
  const [validationData, setValidationData] = useState<any[]>([]);
  const [kpiData, setKpiData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchValidationMetrics = async () => {
      try {
        setLoading(true);
        const response = await api.get('/validation/metrics');
        if (response.data) {
          setValidationData(response.data.validation_metrics || []);
          setKpiData(response.data.kpis || []);
        }
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch validation metrics:', err);
        setError('Failed to load validation metrics');
        // Use default empty data on error
        setValidationData([]);
        setKpiData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchValidationMetrics();
  }, []);

  const validationColumns = [
    { key: 'metric', label: 'Metric' },
    {
      key: 'value',
      label: 'Value',
      render: (value: string, row: any) => (
        <span className={`validation-value validation-${row.status}`}>{value}</span>
      ),
    },
    { key: 'target', label: 'Target' },
  ];

  const kpiColumns = [
    { key: 'kpi', label: 'KPI' },
    {
      key: 'value',
      label: 'Value',
      render: (value: string) => (
        <span className="kpi-value">{value}</span>
      ),
    },
    {
      key: 'trend',
      label: 'Trend',
      render: (trend: string) => (
        <span className={`kpi-trend ${trend.includes('+') ? 'positive' : ''}`}>
          {trend}
        </span>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="validation-dashboard">
        <div className="loading-message">Loading validation metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="validation-dashboard">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="validation-dashboard">
      {antennaType === 'dipole' && (
        <p className="result-comparison-note" style={{ marginBottom: 16, maxWidth: 560 }}>
          Validation metrics are loaded from the shared backend; they are not dipole-specific but apply to the whole twin pipeline.
        </p>
      )}
      <div className="validation-section">
        <div className="section-header">Validation Metrics</div>
        {validationData.length > 0 ? (
          <Table columns={validationColumns} data={validationData} />
        ) : (
          <div className="no-data-message">No validation data available</div>
        )}
      </div>

      <div className="divider" />

      <div className="validation-section">
        <div className="section-header">Key Performance Indicators</div>
        {kpiData.length > 0 ? (
          <Table columns={kpiColumns} data={kpiData} />
        ) : (
          <div className="no-data-message">No KPI data available</div>
        )}
      </div>
    </div>
  );
};



















