import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import StrategyManagement from '@/pages/StrategyManagement';
import TradingInterface from '@/pages/TradingInterface';
import RiskMonitoring from '@/pages/RiskMonitoring';
import Settings from '@/pages/Settings';

const App: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/strategies" element={<StrategyManagement />} />
          <Route path="/trading" element={<TradingInterface />} />
          <Route path="/risk" element={<RiskMonitoring />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Box>
  );
};

export default App;
