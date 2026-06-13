import React from 'react';
import { ResizablePanel } from '../common/ResizablePanel';
import { Sidebar } from './Sidebar';
import { Workspace } from './Workspace';
import { ParametersPanel } from './ParametersPanel';
import { StatusBar } from './StatusBar';
import './AppLayout.css';

interface AppLayoutProps {
  antennaLabel: string;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ antennaLabel }) => {
  return (
    <div className="app-layout">
      <div className="app-layout-top">
        <ResizablePanel
          direction="vertical"
          defaultSize={240}
          minSize={150}
          maxSize={400}
          storageKey="sidebar-width"
          edge="right"
        >
          <Sidebar antennaLabel={antennaLabel} />
        </ResizablePanel>
        <div className="app-layout-main">
          <Workspace />
          <ResizablePanel
            direction="vertical"
            defaultSize={320}
            minSize={200}
            maxSize={500}
            storageKey="params-panel-width"
            edge="left"
          >
            <ParametersPanel />
          </ResizablePanel>
        </div>
      </div>
      <StatusBar antennaLabel={antennaLabel} />
    </div>
  );
};


