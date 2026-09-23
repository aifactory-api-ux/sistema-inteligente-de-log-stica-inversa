import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppNavigationHeader } from './components/ui/AppNavigationHeader';
import { PortalHibrido } from './pages/PortalHibrido';
import { LogisticsDeliveryPage } from './pages/LogisticsDeliveryPage';
import { ControlTowerPage } from './pages/ControlTowerPage';
import { tokens } from './styles/tokens';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ backgroundColor: tokens.colors.pageBackground }}>
        <AppNavigationHeader />
        <Routes>
          <Route path="/" element={<PortalHibrido />} />
          <Route
            path="/logistics"
            element={<LogisticsDeliveryPage />}
          />
          <Route
            path="/control-tower"
            element={<ControlTowerPage />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
};

const ComingSoon: React.FC<{ title: string; description: string }> = ({ title, description }) => (
  <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
      <p className="text-gray-500 mt-2">{description}</p>
      <p className="text-sm text-gray-400 mt-4">Próximamente disponible</p>
    </div>
  </div>
);

export default App;
