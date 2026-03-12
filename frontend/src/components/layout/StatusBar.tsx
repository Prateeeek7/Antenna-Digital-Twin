import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAntennaStore } from '../../services/state';
import { KaTeX } from '../common/KaTeX';
import './StatusBar.css';

interface LogEntry {
  time: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  message: string;
}

export const StatusBar: React.FC = () => {
  const { calculationDetails } = useAntennaStore();
  const [showLogs, setShowLogs] = useState(false);
  const [showCalculation, setShowCalculation] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    const checkConnection = async () => {
      try {
        const response = await api.get('/health', { timeout: 8000 });
        if (response?.status >= 200 && response?.status < 300) {
          setConnectionStatus('connected');
          setLogs((prev) => {
            const last = prev[prev.length - 1];
            if (prev.length === 0 || last?.level !== 'SUCCESS') {
              return [...prev.slice(-9), { time: new Date().toLocaleTimeString(), level: 'SUCCESS' as const, message: 'Backend connected' }];
            }
            return prev;
          });
          return;
        }
      } catch (_) {
        try {
          const ctrl = new AbortController();
          const t = setTimeout(() => ctrl.abort(), 5000);
          const res = await fetch(`${baseUrl}/health`, { method: 'GET', signal: ctrl.signal });
          clearTimeout(t);
          if (res.ok) {
            setConnectionStatus('connected');
            setLogs((prev) => {
              const last = prev[prev.length - 1];
              if (prev.length === 0 || last?.level !== 'SUCCESS') {
                return [...prev.slice(-9), { time: new Date().toLocaleTimeString(), level: 'SUCCESS' as const, message: 'Backend connected' }];
              }
              return prev;
            });
            return;
          }
        } catch (_) {}
      }
      setConnectionStatus('disconnected');
      setLogs((prev) => {
        const msg = `Backend not reachable at ${baseUrl}. Run: ./run_engine.sh backend`;
        const last = prev[prev.length - 1];
        if (last?.message !== msg) {
          return [...prev.slice(-9), { time: new Date().toLocaleTimeString(), level: 'ERROR' as const, message: msg }];
        }
        return prev;
      });
    };

    // Initial check; retry a few times in case backend is still starting
    let connected = false;
    const runWithRetries = async (attempts = 3) => {
      for (let i = 0; i < attempts; i++) {
        try {
          const response = await api.get('/health', { timeout: 8000 });
          if (response?.status >= 200 && response?.status < 300) {
            setConnectionStatus('connected');
            setLogs((prev) => [...prev.slice(-9), { time: new Date().toLocaleTimeString(), level: 'SUCCESS' as const, message: 'Backend connected' }]);
            connected = true;
            return;
          }
        } catch (_) {
          try {
            const res = await fetch(`${baseUrl}/health`, { method: 'GET' });
            if (res.ok) {
              setConnectionStatus('connected');
              setLogs((prev) => [...prev.slice(-9), { time: new Date().toLocaleTimeString(), level: 'SUCCESS' as const, message: 'Backend connected' }]);
              connected = true;
              return;
            }
          } catch (_) {}
        }
        if (i < attempts - 1) await new Promise((r) => setTimeout(r, 2000));
      }
      if (!connected) {
        setConnectionStatus('disconnected');
        setLogs((prev) => [...prev.slice(-9), { time: new Date().toLocaleTimeString(), level: 'ERROR' as const, message: `Backend not reachable at ${baseUrl}. Run: ./run_engine.sh backend` }]);
      }
    };
    runWithRetries();

    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

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
            onClick={() => setShowCalculation(!showCalculation)}
            aria-label="Toggle calculation details"
          >
            {showCalculation ? '▼ Calculation' : '▲ Calculation'}
          </button>
          <button
            className="status-bar-toggle"
            onClick={() => setShowLogs(!showLogs)}
            aria-label="Toggle logs"
          >
            {showLogs ? '▼ Logs' : '▲ Logs'}
          </button>
        </div>
      </div>
      {showCalculation && (
        <div className="status-bar-calculation">
          {!calculationDetails ? (
            <div className="calc-placeholder">Run Design to see calculation details</div>
          ) : (
            <>
              <div className="calc-title">{calculationDetails.title}</div>
              <div className="calc-section">
                <div className="calc-section-head">Inputs</div>
                <div className="calc-kv">
                  {calculationDetails.inputs.map((inp, i) => (
                    <span key={i} className="calc-row">
                      <KaTeX math={inp.label} /> = {inp.value} {inp.unit}
                    </span>
                  ))}
                </div>
              </div>
              <div className="calc-section">
                <div className="calc-section-head">Steps</div>
                <div className="calc-steps">
                  {calculationDetails.steps.map((step, i) => (
                    <div key={i} className="calc-step">
                      <div className="calc-step-formula">
                        <KaTeX math={step.formula} displayMode />
                      </div>
                      <div className="calc-step-result">
                        <KaTeX math={step.name} /> = {step.value} {step.unit}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="calc-section">
                <div className="calc-section-head">Output</div>
                <div className="calc-kv">
                  {calculationDetails.output.map((out, i) => (
                    <span key={i} className="calc-row">
                      {out.label}: {out.value} {out.unit}
                    </span>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
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
