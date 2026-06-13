import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAntennaStore } from '../../services/state';
import './LandingPage.css';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { setAntennaType } = useAntennaStore();

  const handleOpenTwin = (antennaType: 'microstrip' | 'dipole') => {
    setAntennaType(antennaType);
    navigate(`/${antennaType}`);
  };

  const handleOpenPhysics = () => {
    navigate('/physics');
  };

  return (
    <div className="landing-page">
      <div className="landing-page-bg" aria-hidden="true">
        <svg className="landing-grid" viewBox="0 0 1200 700" preserveAspectRatio="none">
          <defs>
            <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(79, 179, 200, 0.28)" />
              <stop offset="65%" stopColor="rgba(77, 136, 255, 0.12)" />
              <stop offset="100%" stopColor="rgba(77, 136, 255, 0.01)" />
            </radialGradient>
          </defs>
          <circle cx="190" cy="170" r="180" fill="url(#radarGlow)" />
          <circle cx="1030" cy="520" r="240" fill="url(#radarGlow)" />
        </svg>
        <div className="landing-scanline" />
      </div>

      <header className="landing-intro">
        <p className="landing-eyebrow">Antenna Digital Twin</p>
        <h1 className="landing-title">Design, Simulate, and Validate RF Antennas</h1>
        <p className="landing-subtitle">
          A unified workspace for microstrip and dipole workflows with fast surrogate analysis and EM-ready design decisions.
        </p>
      </header>

      <div className="landing-card">
        <h2 className="landing-card-title">Choose Antenna Twin</h2>
        <p className="landing-card-subtitle">
          Open the digital twin workspace, or use analytical formulas for quick sizing and impedance estimates.
        </p>

        <div className="landing-actions">
          <button
            type="button"
            className="landing-btn"
            onClick={() => handleOpenTwin('microstrip')}
          >
            Microstrip Antenna
          </button>
          <button
            type="button"
            className="landing-btn"
            onClick={() => handleOpenTwin('dipole')}
          >
            Dipole Antenna
          </button>
          <button type="button" className="landing-btn landing-btn-physics" onClick={handleOpenPhysics}>
            Physics calculators
          </button>
        </div>
      </div>
    </div>
  );
};
