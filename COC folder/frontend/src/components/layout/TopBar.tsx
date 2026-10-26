import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, Globe } from 'lucide-react';
import { useHealth } from '../../hooks/useHealth';

interface TopBarProps {
  onToggleMenu: () => void;
}

const ROUTE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'System Overview', subtitle: 'Model health, dataset coverage, and historical audits' },
  '/predict': { title: 'Cultivation Cost Predictor', subtitle: 'SO1: Calibrated prediction intervals & TreeSHAP feature drivers' },
  '/batch': { title: 'Batch CSV Estimator', subtitle: 'Upload and process bulk agricultural scenarios sequentially' },
  '/simulation': { title: 'Interactive What-If Simulation', subtitle: 'Module owned by SO2 (K.U.R.C.T Rathnayake)' },
  '/expenses': { title: 'Daily Expense Tracker', subtitle: 'Module owned by SO3 (D.G.K.A Thasindu)' },
  '/chat': { title: 'Agricultural Assistant', subtitle: 'Natural language queries backed by calibrated predictive models' },
  '/settings': { title: 'API & Environment Settings', subtitle: 'Configure endpoints and inspect model parameters' },
};

export const TopBar: React.FC<TopBarProps> = ({ onToggleMenu }) => {
  const location = useLocation();
  const { data: health, isLoading: healthLoading, isError: healthError } = useHealth();

  const currentRoute = ROUTE_TITLES[location.pathname] || {
    title: 'AgriCost AI',
    subtitle: 'Cost of Cultivation Prediction System',
  };

  const isHealthy = !healthLoading && !healthError && health?.status === 'ok' && health?.pipeline_loaded;

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-6 flex items-center justify-between transition-colors">
      {/* Left: Mobile hamburger & Dynamic page title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMenu}
          className="p-2 -ml-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 lg:hidden"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight leading-tight">
            {currentRoute.title}
          </h1>
          <p className="text-[11px] sm:text-xs text-slate-500 font-normal hidden sm:block">
            {currentRoute.subtitle}
          </p>
        </div>
      </div>

      {/* Right: Model Version, Health Status Dot, Language Toggle */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Model Version Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono font-medium shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>{health?.model_version || 'gb_tuned_v1'}</span>
        </div>

        {/* API Health Status Indicator */}
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border shadow-sm transition-all ${
            isHealthy
              ? 'bg-emerald-50 border-emerald-200/80 text-emerald-800'
              : 'bg-rose-50 border-rose-200/80 text-rose-800'
          }`}
          title={
            isHealthy
              ? `API Online (Uptime: ${health?.uptime_seconds}s)`
              : 'API Offline or Connecting to http://localhost:8000'
          }
        >
          <span className="relative flex h-2 w-2">
            {isHealthy && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isHealthy ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
          </span>
          <span className="font-semibold hidden md:inline">
            {isHealthy ? 'API Active' : 'API Disconnected'}
          </span>
          {health?.uptime_seconds !== undefined && isHealthy && (
            <span className="text-[10px] text-emerald-600 font-mono hidden lg:inline">
              ({health.uptime_seconds}s)
            </span>
          )}
        </div>

        {/* Language Toggle Stub */}
        <div className="flex items-center rounded-lg border border-slate-200 bg-slate-100/80 p-0.5 text-xs text-slate-400 cursor-not-allowed">
          <span className="px-2 py-0.5 rounded font-semibold bg-white text-slate-800 shadow-xs flex items-center gap-1">
            <Globe className="w-3 h-3 text-slate-500" />
            EN
          </span>
          <span className="px-2 py-0.5 rounded font-medium text-slate-400 select-none">
            සිං
          </span>
        </div>
      </div>
    </header>
  );
};
