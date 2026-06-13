import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RectangularCalculator } from '../components/calculator/RectangularCalculator';
import { useAntennaStore } from '../services/state';
import './MicrostripCalculatorPage.css';

export const MicrostripCalculatorPage: React.FC = () => {
  const { setAntennaType } = useAntennaStore();

  useEffect(() => {
    setAntennaType('microstrip');
  }, [setAntennaType]);

  return (
    <div className="microstrip-calculator-page">
      <header className="microstrip-calculator-nav">
        <Link to="/microstrip" className="microstrip-calculator-back">
          ← Microstrip digital twin
        </Link>
        <Link to="/" className="microstrip-calculator-home">
          Home
        </Link>
      </header>
      <main className="microstrip-calculator-main">
        <RectangularCalculator />
      </main>
    </div>
  );
};
