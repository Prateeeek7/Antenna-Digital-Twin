import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Table } from '../common/Table';
import api from '../../services/api';
import { useAntennaStore } from '../../services/state';
import { decodeDipolePhysicalFromGeometry } from '../../utils/dipoleParams';
import './InstanceManager.css';

interface AntennaInstance {
  id: string;
  instance_id: string;
  parameters: {
    geometry: {
      length: number;
      width: number;
      height: number;
      feed_x: number;
      feed_y: number;
    };
    substrate: {
      substrate_type: string;
      relative_permittivity: number;
      loss_tangent: number;
      thickness: number;
    };
    feed_type: string;
    frequency_band: string;
    frequency_range: [number, number];
  };
  created_at: string;
  updated_at?: string;
  metadata?: { antenna_type?: string; [k: string]: unknown };
}

export const InstanceManager: React.FC = () => {
  const { parameters: designerParameters, antennaType } = useAntennaStore();
  const [instances, setInstances] = useState<AntennaInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingInstance, setEditingInstance] = useState<AntennaInstance | null>(null);
  const [formData, setFormData] = useState({
    instance_id: '',
    length: 30.0,
    width: 40.0,
    height: 1.6,
    feed_x: 15.0,
    feed_y: 20.0,
    substrate_type: 'FR4',
    permittivity: 4.4,
    loss_tangent: 0.02,
    frequency_band: '2.4GHz',
  });

  useEffect(() => {
    fetchInstances();
  }, []);

  const handleSaveFromDesigner = async () => {
    if (!designerParameters) {
      setError('Open the Designer tab first so parameters are set (run dipole surrogate if you need fresh results).');
      return;
    }
    try {
      setError(null);
      await api.post('/antenna-instances/', designerParameters, {
        params: formData.instance_id.trim() ? { instance_id: formData.instance_id.trim() } : {},
      });
      await fetchInstances();
    } catch (err: any) {
      setError(`Save failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  const fetchInstances = async () => {
    try {
      setLoading(true);
      const response = await api.get('/antenna-instances/');
      setInstances(response.data || []);
      setError(null);
    } catch (err: any) {
      setError(`Failed to load instances: ${err.response?.data?.detail || err.message}`);
      console.error('Error fetching instances:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setError(null);
      const antennaParams = {
        geometry: {
          length: formData.length / 1000,
          width: formData.width / 1000,
          height: formData.height / 1000,
          feed_x: formData.feed_x / 1000,
          feed_y: formData.feed_y / 1000,
        },
        substrate: {
          substrate_type: formData.substrate_type,
          relative_permittivity: formData.permittivity,
          loss_tangent: formData.loss_tangent,
          thickness: formData.height / 1000,
        },
        feed_type: 'INSET',
        frequency_band: formData.frequency_band,
        frequency_range: formData.frequency_band === '2.4GHz' ? [2.0e9, 3.0e9] : [3.0e9, 4.0e9],
      };

      await api.post('/antenna-instances/', antennaParams, {
        params: formData.instance_id.trim() ? { instance_id: formData.instance_id.trim() } : {},
      });
      setShowCreateForm(false);
      resetForm();
      fetchInstances();
    } catch (err: any) {
      setError(`Failed to create instance: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleUpdate = async (instance: AntennaInstance) => {
    try {
      setError(null);
      const antennaParams = {
        geometry: {
          length: formData.length / 1000,
          width: formData.width / 1000,
          height: formData.height / 1000,
          feed_x: formData.feed_x / 1000,
          feed_y: formData.feed_y / 1000,
        },
        substrate: {
          substrate_type: formData.substrate_type,
          relative_permittivity: formData.permittivity,
          loss_tangent: formData.loss_tangent,
          thickness: formData.height / 1000,
        },
        feed_type: 'INSET',
        frequency_band: formData.frequency_band,
        frequency_range: formData.frequency_band === '2.4GHz' ? [2.0e9, 3.0e9] : [3.0e9, 4.0e9],
      };

      await api.put(`/antenna-instances/${instance.instance_id}`, antennaParams);
      setEditingInstance(null);
      resetForm();
      fetchInstances();
    } catch (err: any) {
      setError(`Failed to update instance: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleDelete = async (instanceId: string) => {
    if (!confirm(`Delete antenna instance ${instanceId}?`)) {
      return;
    }

    try {
      setError(null);
      await api.delete(`/antenna-instances/${instanceId}`);
      fetchInstances();
    } catch (err: any) {
      setError(`Failed to delete instance: ${err.response?.data?.detail || err.message}`);
    }
  };

  const startEdit = (instance: AntennaInstance) => {
    setEditingInstance(instance);
    setFormData({
      instance_id: instance.instance_id,
      length: instance.parameters.geometry.length * 1000,
      width: instance.parameters.geometry.width * 1000,
      height: instance.parameters.geometry.height * 1000,
      feed_x: instance.parameters.geometry.feed_x * 1000,
      feed_y: instance.parameters.geometry.feed_y * 1000,
      substrate_type: instance.parameters.substrate.substrate_type,
      permittivity: instance.parameters.substrate.relative_permittivity,
      loss_tangent: instance.parameters.substrate.loss_tangent,
      frequency_band: instance.parameters.frequency_band,
    });
    setShowCreateForm(true);
  };

  const resetForm = () => {
    setFormData({
      instance_id: '',
      length: 30.0,
      width: 40.0,
      height: 1.6,
      feed_x: 15.0,
      feed_y: 20.0,
      substrate_type: 'FR4',
      permittivity: 4.4,
      loss_tangent: 0.02,
      frequency_band: '2.4GHz',
    });
    setEditingInstance(null);
  };

  const columns = [
    { key: 'instance_id', label: 'Instance ID' },
    {
      key: 'frequency_band',
      label: 'Frequency',
      render: (_: any, row: AntennaInstance) => row.parameters.frequency_band,
    },
    {
      key: 'geometry',
      label: antennaType === 'dipole' ? 'Dipole (decoded)' : 'Size (mm)',
      render: (_: any, row: AntennaInstance) => {
        if (antennaType === 'dipole') {
          const d = decodeDipolePhysicalFromGeometry(row.parameters.geometry);
          return `L ${d.dipoleLengthMm.toFixed(1)} · 2R ${(2 * d.wireRadiusMm).toFixed(2)} · gap ${d.feedGapMm.toFixed(2)}`;
        }
        return `${(row.parameters.geometry.length * 1000).toFixed(1)} × ${(row.parameters.geometry.width * 1000).toFixed(1)}`;
      },
    },
    {
      key: 'substrate',
      label: 'Substrate',
      render: (_: any, row: AntennaInstance) =>
        antennaType === 'dipole' ? '— (surrogate encoding)' : row.parameters.substrate.substrate_type,
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_: any, row: AntennaInstance) => (
        <div className="instance-actions">
          <Button variant="secondary" size="sm" onClick={() => startEdit(row)}>
            Edit
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleDelete(row.instance_id)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="instance-manager">
      <div className="instance-manager-header">
        <h2 className="section-header">Antenna Instance Management</h2>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {antennaType === 'dipole' && (
            <Button variant="secondary" onClick={handleSaveFromDesigner} disabled={!designerParameters}>
              Save current Designer parameters
            </Button>
          )}
          <Button
            variant="primary"
            onClick={() => {
              resetForm();
              setShowCreateForm(true);
            }}
          >
            {antennaType === 'dipole' ? 'Create (manual geometry)' : 'Create New Instance'}
          </Button>
        </div>
      </div>
      {antennaType === 'dipole' && (
        <p className="result-comparison-note" style={{ marginBottom: 12, maxWidth: 640 }}>
          Instances store the same encoded geometry as the dipole surrogate. Prefer <strong>Save current Designer parameters</strong>,
          or use manual create if you edit raw encoded length / width / height / feeds.
        </p>
      )}

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="instance-form">
          <div className="section-header">
            {editingInstance ? 'Edit Instance' : 'Create New Instance'}
          </div>
          <div className="input-group">
            <Input
              label="Instance ID (optional, auto-generated if empty)"
              value={formData.instance_id}
              onChange={(e) => setFormData({ ...formData, instance_id: e.target.value })}
              placeholder="ANT-XXXXXXXX"
            />
            <Input
              label="Length"
              type="number"
              unit="mm"
              value={formData.length.toString()}
              onChange={(e) => setFormData({ ...formData, length: parseFloat(e.target.value) || 0 })}
            />
            <Input
              label="Width"
              type="number"
              unit="mm"
              value={formData.width.toString()}
              onChange={(e) => setFormData({ ...formData, width: parseFloat(e.target.value) || 0 })}
            />
            <Input
              label="Height"
              type="number"
              unit="mm"
              value={formData.height.toString()}
              onChange={(e) => setFormData({ ...formData, height: parseFloat(e.target.value) || 0 })}
            />
            <Input
              label="Feed X"
              type="number"
              unit="mm"
              value={formData.feed_x.toString()}
              onChange={(e) => setFormData({ ...formData, feed_x: parseFloat(e.target.value) || 0 })}
            />
            <Input
              label="Feed Y"
              type="number"
              unit="mm"
              value={formData.feed_y.toString()}
              onChange={(e) => setFormData({ ...formData, feed_y: parseFloat(e.target.value) || 0 })}
            />
            <Select
              label="Substrate Type"
              value={formData.substrate_type}
              onChange={(e) => setFormData({ ...formData, substrate_type: e.target.value })}
              options={[
                { value: 'FR4', label: 'FR-4' },
                { value: 'RO4003', label: 'Rogers RO4003' },
                { value: 'RO4350', label: 'Rogers RO4350' },
              ]}
            />
            <Input
              label="Permittivity"
              type="number"
              value={formData.permittivity.toString()}
              onChange={(e) => setFormData({ ...formData, permittivity: parseFloat(e.target.value) || 0 })}
            />
            <Input
              label="Loss Tangent"
              type="number"
              value={formData.loss_tangent.toString()}
              onChange={(e) => setFormData({ ...formData, loss_tangent: parseFloat(e.target.value) || 0 })}
            />
            <Select
              label="Frequency Band"
              value={formData.frequency_band}
              onChange={(e) => setFormData({ ...formData, frequency_band: e.target.value })}
              options={[
                { value: '2.4GHz', label: '2.4 GHz' },
                { value: '3.5GHz', label: '3.5 GHz' },
              ]}
            />
          </div>
          <div className="form-actions">
            <Button
              variant="primary"
              onClick={() => (editingInstance ? handleUpdate(editingInstance) : handleCreate())}
            >
              {editingInstance ? 'Update' : 'Create'}
            </Button>
            <Button variant="secondary" onClick={() => {
              setShowCreateForm(false);
              resetForm();
            }}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      <div className="instance-list">
        {loading ? (
          <div className="loading-message">Loading instances...</div>
        ) : instances.length === 0 ? (
          <div className="no-data-message">No antenna instances. Create one to get started.</div>
        ) : (
          <Table columns={columns} data={instances} />
        )}
      </div>
    </div>
  );
};
