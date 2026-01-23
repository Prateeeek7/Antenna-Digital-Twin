import React from 'react';
import { ResizablePanel } from '../common/ResizablePanel';
import { Sidebar } from './Sidebar';
import { Workspace } from './Workspace';
import { ParametersPanel } from './ParametersPanel';
import { StatusBar } from './StatusBar';
import './AppLayout.css';

export const AppLayout: React.FC = () => {
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
          <Sidebar />
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
      <ResizablePanel
        direction="horizontal"
        defaultSize={200}
        minSize={100}
        maxSize={400}
        storageKey="status-bar-height"
      >
        <StatusBar />
      </ResizablePanel>
    </div>
  );
};


