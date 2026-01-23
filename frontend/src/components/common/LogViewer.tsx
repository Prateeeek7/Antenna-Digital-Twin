import React from 'react';
import './LogViewer.css';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

interface LogViewerProps {
  logs: LogEntry[];
  maxLines?: number;
}

export const LogViewer: React.FC<LogViewerProps> = ({ logs, maxLines = 100 }) => {
  const displayLogs = logs.slice(-maxLines);

  return (
    <div className="log-viewer">
      {displayLogs.map((log, idx) => (
        <div key={idx} className={`log-entry log-${log.level}`}>
          <span className="log-time">{log.timestamp}</span>
          <span className="log-level">{log.level.toUpperCase()}</span>
          <span className="log-message">{log.message}</span>
        </div>
      ))}
    </div>
  );
};



















