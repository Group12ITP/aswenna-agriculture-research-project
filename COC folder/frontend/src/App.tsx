import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { PredictPage } from './pages/PredictPage';
import { BatchPage } from './pages/BatchPage';
import { SimulationPage } from './pages/SimulationPage';
import { ExpenseTrackerPage } from './pages/ExpenseTrackerPage';
import { ChatPage } from './pages/ChatPage';
import { SettingsPage } from './pages/SettingsPage';
import { ModelComparisonPage } from './pages/ModelComparisonPage';

// Configure TanStack Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/predict" element={<PredictPage />} />
            <Route path="/model-comparison" element={<ModelComparisonPage />} />
            <Route path="/batch" element={<BatchPage />} />
            <Route path="/simulation" element={<SimulationPage />} />
            <Route path="/expenses" element={<ExpenseTrackerPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
