import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './StatusBar.css';

interface LogEntry {
  time: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  message: string;
}

export const StatusBar: React.FC = () => {
  const [showLogs, setShowLogs] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    // Check backend connection
    const checkConnection = async () => {
      try {
        // Use base URL directly for health check (not under /api/v1)
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
        
        const response = await fetch(`${baseUrl}/health`, {
          method: 'GET',
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
          },
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          setConnectionStatus('connected');
          // Only log on first successful connection to avoid spam
          if (logs.length === 0 || logs[logs.length - 1].level !== 'SUCCESS') {
            addLog('SUCCESS', 'Backend connection established');
          }
        } else {
          setConnectionStatus('disconnected');
          addLog('WARNING', `Backend returned status ${response.status}`);
        }
      } catch (error: any) {
        setConnectionStatus('disconnected');
        if (error.name === 'AbortError') {
          addLog('ERROR', 'Backend connection timeout - server may not be running');
        } else if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
          addLog('ERROR', 'Cannot reach backend - ensure server is running on port 8000');
        } else {
          addLog('ERROR', `Connection error: ${error.message || 'Unknown error'}`);
        }
      }
    };

    // Initial check
    checkConnection();
    // Then check every 10 seconds (more frequent for better UX)
    const interval = setInterval(checkConnection, 10000);

    return () => clearInterval(interval);
  }, []);

  const addLog = (level: LogEntry['level'], message: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev.slice(-9), { time, level, message }]);
  };

  return (
    <div className="status-bar">
      <div className="status-bar-main">
        <div className="status-bar-left">
          <span className={`status-indicator ${connectionStatus === 'connected' ? 'success' : connectionStatus === 'checking' ? 'warning' : 'error'}`} />
          <span className="status-text">
            {connectionStatus === 'connected' ? 'Ready' : connectionStatus === 'checking' ? 'Checking...' : 'Disconnected'}
          </span>
          <span className="status-divider">|</span>
          <span className="status-text">Model: v1.0</span>
          <span className="status-divider">|</span>
          <span className="status-text">
            {connectionStatus === 'connected' ? 'Connected' : 'Not Connected'}
          </span>
        </div>
        <div className="status-bar-right">
          <button
            className="status-bar-toggle"
            onClick={() => setShowLogs(!showLogs)}
            aria-label="Toggle logs"
          >
            {showLogs ? '▼' : '▲'} Logs
          </button>
        </div>
      </div>
      {showLogs && (
        <div className="status-bar-logs">
          {logs.length === 0 ? (
            <div className="log-entry">
              <span className="log-message">No log entries</span>
            </div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="log-entry">
                <span className="log-time">[{log.time}]</span>
                <span className={`log-level log-${log.level.toLowerCase()}`}>{log.level}</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
