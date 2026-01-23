import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import api from '../../services/api';
import './MeasurementUpload.css';

export const MeasurementUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [antennaInstanceId, setAntennaInstanceId] = useState('');
  const [fileType, setFileType] = useState('auto');
  const [temperature, setTemperature] = useState('');
  const [humidity, setHumidity] = useState('');
  const [operator, setOperator] = useState('');
  const [equipmentId, setEquipmentId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [instances, setInstances] = useState<Array<{ instance_id: string }>>([]);

  React.useEffect(() => {
    fetchInstances();
  }, []);

  const fetchInstances = async () => {
    try {
      const response = await api.get('/antenna-instances/');
      setInstances(response.data || []);
    } catch (err) {
      console.error('Failed to fetch instances:', err);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('file_type', fileType);
      
      if (antennaInstanceId) {
        formData.append('antenna_instance_id', antennaInstanceId);
      }
      if (temperature) {
        formData.append('temperature', temperature);
      }
      if (humidity) {
        formData.append('humidity', humidity);
      }
      if (operator) {
        formData.append('operator', operator);
      }
      if (equipmentId) {
        formData.append('equipment_id', equipmentId);
      }

      const response = await api.post('/measurements/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(`Measurement uploaded successfully! ID: ${response.data.measurement_id}`);
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById('measurement-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="measurement-upload">
      <div className="section-header">Measurement Upload</div>
      
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message" role="alert">
          {success}
        </div>
      )}

      <div className="upload-form">
        <div className="input-group">
          <div className="file-input-wrapper">
            <label htmlFor="measurement-file" className="file-label">
              Select Measurement File
            </label>
            <input
              id="measurement-file"
              type="file"
              accept=".s1p,.s2p,.snp,.csv,.txt,.json"
              onChange={handleFileChange}
              className="file-input"
            />
            {file && (
              <div className="file-info">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </div>
            )}
          </div>

          <Select
            label="File Type"
            value={fileType}
            onChange={(e) => setFileType(e.target.value)}
            options={[
              { value: 'auto', label: 'Auto-detect' },
              { value: 'vna', label: 'VNA (Touchstone, CSV)' },
              { value: 'chamber', label: 'Chamber (JSON, CSV)' },
            ]}
          />

          <Select
            label="Antenna Instance (optional)"
            value={antennaInstanceId}
            onChange={(e) => setAntennaInstanceId(e.target.value)}
            options={[
              { value: '', label: 'None (will be assigned)' },
              ...instances.map((inst) => ({
                value: inst.instance_id,
                label: inst.instance_id,
              })),
            ]}
          />

          <Input
            label="Temperature"
            type="number"
            unit="°C"
            value={temperature}
            onChange={(e) => setTemperature(e.target.value)}
            placeholder="25.0"
          />

          <Input
            label="Humidity"
            type="number"
            unit="%"
            value={humidity}
            onChange={(e) => setHumidity(e.target.value)}
            placeholder="50.0"
          />

          <Input
            label="Operator"
            type="text"
            value={operator}
            onChange={(e) => setOperator(e.target.value)}
            placeholder="Operator name"
          />

          <Input
            label="Equipment ID"
            type="text"
            value={equipmentId}
            onChange={(e) => setEquipmentId(e.target.value)}
            placeholder="Equipment identifier"
          />
        </div>

        <div className="upload-actions">
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Measurement'}
          </Button>
        </div>
      </div>

      <div className="upload-info">
        <div className="section-header">Supported Formats</div>
        <ul>
          <li>VNA: Touchstone (.s1p, .s2p, .snp), CSV, TXT</li>
          <li>Chamber: JSON, CSV</li>
          <li>Auto-detection available for most formats</li>
        </ul>
      </div>
    </div>
  );
};
