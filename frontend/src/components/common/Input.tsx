import React from 'react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  unit?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  unit,
  fullWidth = false,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const classes = [
    'input-wrapper',
    fullWidth && 'input-wrapper-full',
    error && 'input-wrapper-error',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes}>
      {label && (
        <label htmlFor={inputId} className="input-label">
          {label}
        </label>
      )}
      <div className="input-container">
        <input
          id={inputId}
          className="input"
          {...props}
        />
        {unit && <span className="input-unit">{unit}</span>}
      </div>
      {error && <span className="input-error">{error}</span>}
    </div>
  );
};



















