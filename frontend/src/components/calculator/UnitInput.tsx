import React from 'react';
import type { FrequencyUnit, LengthUnit } from '../../lib/units';
import { FREQUENCY_UNITS, LENGTH_UNITS } from '../../lib/units';

interface UnitInputProps {
  label: string;
  value: number;
  unit: FrequencyUnit;
  onValueChange: (v: number) => void;
  onUnitChange: (u: FrequencyUnit) => void;
  unitOptions?: { value: FrequencyUnit; label: string }[];
}

export const UnitInput: React.FC<UnitInputProps> = ({
  label,
  value,
  unit,
  onValueChange,
  onUnitChange,
  unitOptions = FREQUENCY_UNITS,
}) => (
  <div className="unit-input">
    <label>
      <span className="label-text">{label}</span>
      <div className="input-row">
        <input
          type="number"
          step="any"
          value={Number.isFinite(value) ? value : 0}
          onChange={(e) => onValueChange(parseFloat(e.target.value) || 0)}
        />
        <select value={unit} onChange={(e) => onUnitChange(e.target.value as FrequencyUnit)}>
          {unitOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>
    </label>
  </div>
);

interface LengthInputProps {
  label: string;
  value: number;
  unit: LengthUnit;
  onValueChange: (v: number) => void;
  onUnitChange: (u: LengthUnit) => void;
}

export const LengthInput: React.FC<LengthInputProps> = ({
  label,
  value,
  unit,
  onValueChange,
  onUnitChange,
}) => (
  <div className="unit-input">
    <label>
      <span className="label-text">{label}</span>
      <div className="input-row">
        <input
          type="number"
          step="any"
          value={Number.isFinite(value) ? value : 0}
          onChange={(e) => onValueChange(parseFloat(e.target.value) || 0)}
        />
        <select value={unit} onChange={(e) => onUnitChange(e.target.value as LengthUnit)}>
          {LENGTH_UNITS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>
    </label>
  </div>
);
