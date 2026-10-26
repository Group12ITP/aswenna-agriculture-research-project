import React, { useState } from 'react';
import {
  Server,
  Activity,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Database,
  Calendar,
  Info,
} from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl } from '../api/client';
import { getHealth } from '../api/health';
import { useMetadata } from '../hooks/useMetadata';
import { clearStoredPredictions } from '../lib/storage';
import type { HealthResponse } from '../types/api';

export const SettingsPage: React.FC = () => {
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());
  const [testResult, setTestResult] = useState<{
    tested: boolean;
    success: boolean;
    data?: HealthResponse;
    error?: string;
  } | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [historyCleared, setHistoryCleared] = useState(false);

  const { data: metadata } = useMetadata();

  const handleSaveUrl = () => {
    setApiBaseUrl(apiUrl);
    setTestResult(null);
    alert('API Base URL saved! Future network requests will use this endpoint.');
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      // Save current input before testing
      setApiBaseUrl(apiUrl);
      const res = await getHealth();
      setTestResult({ tested: true, success: true, data: res });
    } catch (err: any) {
      setTestResult({ tested: true, success: false, error: err.message || 'Connection failed' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleClearHistory = () => {
    if (window.confirm('Clear all stored predictions from your browser localStorage?')) {
      clearStoredPredictions();
      setHistoryCleared(true);
      setTimeout(() => setHistoryCleared(false), 3000);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-300 max-w-4xl mx-auto">
      {/* Settings Card: API Configuration */}
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-3 pb-5 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Server className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              API Server Configuration
            </h2>
            <p className="text-xs text-slate-500">
              Specify the target FastAPI REST microservice endpoint.
            </p>
          </div>
        </div>

        <div className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              API Base URL
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1 px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm font-mono focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSaveUrl}
                  className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition-colors"
                >
                  Save URL
                </button>
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isTesting ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Activity className="w-3.5 h-3.5" />
                  )}
                  <span>Test Connection</span>
                </button>
              </div>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5">
              Default is derived from <code className="text-emerald-700">VITE_API_BASE_URL</code> (http://localhost:8000). Stored locally in browser.
            </p>
          </div>

          {/* Test Result Feedback */}
          {testResult && (
            <div
              className={`p-4 rounded-xl border text-xs flex items-start gap-2.5 ${
                testResult.success
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}
            >
              {testResult.success ? (
                <>
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 mt-0.5" />
                  <div>
                    <span className="font-bold block">Connection Verified (HTTP 200 OK)</span>
                    <span className="text-[11px] font-mono mt-0.5 block">
                      Status: {testResult.data?.status} | Model: {testResult.data?.model_version} | Pipeline:{' '}
                      {testResult.data?.pipeline_loaded ? 'Ready' : 'Not Loaded'} | Uptime:{' '}
                      {testResult.data?.uptime_seconds}s
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
                  <div>
                    <span className="font-bold block">Connection Failed</span>
                    <span className="text-[11px] mt-0.5 block">{testResult.error}</span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Settings Card: Browser Storage Management */}
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-3 pb-5 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center">
            <Trash2 className="w-5 h-5 text-slate-600" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              Prediction Audit History
            </h2>
            <p className="text-xs text-slate-500">
              Manage client-side cached inferences stored in browser localStorage.
            </p>
          </div>
        </div>

        <div className="mt-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold text-slate-700 block">
              Purge Local History
            </span>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Permanently removes the 20 most recent cached predictions from this device.
            </p>
          </div>
          <button
            onClick={handleClearHistory}
            className="px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs transition-colors self-start sm:self-auto flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{historyCleared ? 'History Purged!' : 'Clear All History'}</span>
          </button>
        </div>
      </div>

      {/* Settings Card: Read-Only Model Metadata */}
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-3 pb-5 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Database className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              Model Metadata (Read-Only)
            </h2>
            <p className="text-xs text-slate-500">
              Active parameters exposed by the live FastAPI `/metadata` endpoint.
            </p>
          </div>
        </div>

        <div className="mt-5 space-y-3 text-xs">
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Model Pipeline Identifier:</span>
            <span className="font-mono font-bold text-slate-900">
              {metadata?.model_version || 'gb_tuned_v1'}
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Empirical Training Horizon:</span>
            <span className="font-mono font-bold text-slate-900">
              {metadata?.training_year_range
                ? `${metadata.training_year_range[0]} – ${metadata.training_year_range[1]}`
                : '2014 – 2025'}
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Training Mean LKR/USD Rate:</span>
            <span className="font-mono font-bold text-slate-900">
              {metadata?.training_usd_lkr_mean ? `${metadata.training_usd_lkr_mean} LKR/USD` : '201.07 LKR/USD'}
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Currency Shock Threshold:</span>
            <span className="font-mono font-bold text-slate-900">
              ±{metadata?.low_confidence_threshold_pct || 30}% Deviation
            </span>
          </div>
        </div>
      </div>

      {/* Settings Card: Model Reference Horizon & Retraining Policy */}
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-3 pb-5 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
            <Calendar className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900">
              Reference Data Horizon
            </h2>
            <p className="text-xs text-slate-500">
              Baseline dataset version and retraining policy.
            </p>
          </div>
        </div>

        <div className="mt-5 space-y-3 text-xs text-slate-700">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 font-mono space-y-1.5">
            <div>
              <span className="font-bold text-slate-900">Model Reference:</span> 2025 (latest training year)
            </div>
            <div>
              <span className="font-bold text-slate-900">Latest USD/LKR:</span> 300.73
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 flex items-center gap-2">
            <Info className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="font-medium">
              If you have 2026 data, contact the system administrator to retrain.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
