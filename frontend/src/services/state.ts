import { create } from 'zustand';

export interface CalculationStep {
  name: string;
  formula: string;
  value: string;
  unit: string;
}

export interface CalculationDetails {
  type: 'design';
  title: string;
  inputs: Array<{ label: string; value: string; unit: string }>;
  steps: CalculationStep[];
  output: Array<{ label: string; value: string; unit: string }>;
}

interface AntennaState {
  antennaType: 'microstrip' | 'dipole';
  setAntennaType: (antennaType: 'microstrip' | 'dipole') => void;
  parameters: any;
  setParameters: (params: any) => void;
  simulationResults: any;
  setSimulationResults: (results: any) => void;
  predictions: any;
  setPredictions: (predictions: any) => void;
  calculationDetails: CalculationDetails | null;
  setCalculationDetails: (details: CalculationDetails | null) => void;
}

export const useAntennaStore = create<AntennaState>((set) => ({
  antennaType: 'microstrip',
  setAntennaType: (antennaType) => set({ antennaType }),
  parameters: null,
  setParameters: (params) => set({ parameters: params }),
  simulationResults: null,
  setSimulationResults: (results) => set({ simulationResults: results }),
  predictions: null,
  setPredictions: (predictions) => set({ predictions }),
  calculationDetails: null,
  setCalculationDetails: (details) => set({ calculationDetails: details }),
}));
