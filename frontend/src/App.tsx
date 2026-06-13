import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { LandingPage } from './components/landing/LandingPage';
import { MicrostripCalculatorPage } from './pages/MicrostripCalculatorPage';
import { PhysicsCalculatorPage } from './pages/PhysicsCalculatorPage';
import { useAntennaStore } from './services/state';
import './styles/globals.css';
import './styles/components.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/microstrip"
            element={<TwinWorkspace antennaType="microstrip" antennaLabel="Microstrip" />}
          />
          <Route
            path="/dipole"
            element={<TwinWorkspace antennaType="dipole" antennaLabel="Dipole" />}
          />
          <Route path="/microstrip/calculator" element={<MicrostripCalculatorPage />} />
          <Route path="/physics" element={<PhysicsCalculatorPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

const TwinWorkspace: React.FC<{
  antennaType: 'microstrip' | 'dipole';
  antennaLabel: string;
}> = ({ antennaType, antennaLabel }) => {
  const { setAntennaType } = useAntennaStore();

  React.useEffect(() => {
    setAntennaType(antennaType);
  }, [antennaType, setAntennaType]);

  return <AppLayout antennaLabel={antennaLabel} />;
};

export default App;

