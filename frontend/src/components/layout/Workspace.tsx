import React, { useEffect, useMemo, useState } from 'react';
import { AntennaDesigner } from '../antenna/AntennaDesigner';
import { DesignFromFrequency } from '../antenna/DesignFromFrequency';
import { DipoleQuickDesign } from '../antenna/DipoleQuickDesign';
import { useAntennaStore } from '../../services/state';
import { ResultsViewer } from '../results/ResultsViewer';
import { OptimizationPanel } from '../optimization/OptimizationPanel';
import { ValidationDashboard } from '../validation/ValidationDashboard';
import { InstanceManager } from '../management/InstanceManager';
import { MeasurementUpload } from '../measurement/MeasurementUpload';
import { MeasurementList } from '../measurement/MeasurementList';
import { CalibrationPanel } from '../calibration/CalibrationPanel';
import './Workspace.css';

type WorkspaceTab = 'designer' | 'design' | 'results' | 'optimization' | 'validation' | 'instances' | 'measurements' | 'calibration';

export const Workspace: React.FC = () => {
  const { antennaType } = useAntennaStore();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('designer');

  const tabs: Array<{ id: WorkspaceTab; label: string }> = useMemo(() => {
    const all: Array<{ id: WorkspaceTab; label: string }> = [
      { id: 'designer', label: 'Designer' },
      { id: 'design', label: 'Design' },
      { id: 'results', label: 'Results' },
      { id: 'optimization', label: 'Optimization' },
      { id: 'validation', label: 'Validation' },
      { id: 'instances', label: 'Instances' },
      { id: 'measurements', label: 'Measurements' },
      { id: 'calibration', label: 'Calibration' },
    ];
    if (antennaType === 'dipole') {
      return all.filter((t) => t.id !== 'validation');
    }
    return all;
  }, [antennaType]);

  useEffect(() => {
    if (antennaType === 'dipole' && activeTab === 'validation') {
      setActiveTab('designer');
    }
  }, [antennaType, activeTab]);

  return (
    <div className="workspace">
      <div className="workspace-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`workspace-tab ${activeTab === tab.id ? 'workspace-tab-active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="workspace-content">
        {activeTab === 'designer' && <AntennaDesigner />}
        {activeTab === 'design' && (antennaType === 'dipole' ? <DipoleQuickDesign /> : <DesignFromFrequency />)}
        {activeTab === 'results' && <ResultsViewer />}
        {activeTab === 'optimization' && <OptimizationPanel />}
        {activeTab === 'validation' && <ValidationDashboard />}
        {activeTab === 'instances' && <InstanceManager />}
        {activeTab === 'measurements' && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ flex: '0 0 auto', borderBottom: '1px solid #2D3748' }}>
              <MeasurementUpload />
            </div>
            <div style={{ flex: '1 1 auto', overflow: 'auto' }}>
              <MeasurementList />
            </div>
          </div>
        )}
        {activeTab === 'calibration' && <CalibrationPanel />}
      </div>
    </div>
  );
};

