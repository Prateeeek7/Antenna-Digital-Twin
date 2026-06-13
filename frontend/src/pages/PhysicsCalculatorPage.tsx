import React from 'react';
import { Link } from 'react-router-dom';
import { PhysicsCalculator } from '../components/physics/PhysicsCalculator';
import './PhysicsCalculatorPage.css';

export const PhysicsCalculatorPage: React.FC = () => (
  <div className="physics-calculator-page">
    <header className="physics-calculator-page-nav">
      <Link to="/" className="physics-calculator-page-link">
        ← Home
      </Link>
      <div className="physics-calculator-page-twins">
        <Link to="/microstrip" className="physics-calculator-page-link">
          Microstrip twin
        </Link>
        <span className="physics-calculator-page-sep" aria-hidden>
          |
        </span>
        <Link to="/dipole" className="physics-calculator-page-link">
          Dipole twin
        </Link>
      </div>
    </header>
    <main className="physics-calculator-page-main">
      <PhysicsCalculator />
    </main>
  </div>
);
