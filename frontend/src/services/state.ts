import { create } from 'zustand';

interface AntennaState {
  parameters: any;
  setParameters: (params: any) => void;
  simulationResults: any;
  setSimulationResults: (results: any) => void;
  predictions: any;
  setPredictions: (predictions: any) => void;
}

export const useAntennaStore = create<AntennaState>((set) => ({
  parameters: null,
  setParameters: (params) => set({ parameters: params }),
  simulationResults: null,
  setSimulationResults: (results) => set({ simulationResults: results }),
  predictions: null,
  setPredictions: (predictions) => set({ predictions }),
}));
