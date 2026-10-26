import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Cpu,
  Clock,
  Layers,
  MapPin,
  Calendar,
  DollarSign,
  TrendingUp,
  ArrowRight,
  Calculator,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Database,
  BarChart3
} from 'lucide-react';
import { useHealth } from '../hooks/useHealth';
import { useMetadata } from '../hooks/useMetadata';
import { useCropDistrictMatrix } from '../hooks/useCropDistrictMatrix';
import { getStoredPredictions, clearStoredPredictions } from '../lib/storage';
import { formatLKR, formatUptime, formatDateTime } from '../lib/format';
import type { StoredPrediction } from '../types/api';

export const DashboardPage: React.FC = () => {
  const { data: health, isLoading: healthLoading, isError: healthError } = useHealth();
  const { data: metadata } = useMetadata();
  const { data: matrix } = useCropDistrictMatrix();
  const [recentPredictions, setRecentPredictions] = useState<StoredPrediction[]>([]);

  useEffect(() => {
    setRecentPredictions(getStoredPredictions());
  }, []);

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear your local prediction history?')) {
      clearStoredPredictions();
      setRecentPredictions([]);
    }
  };

  const isServerOnline = !healthLoading && !healthError && health?.status === 'ok';

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-300">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-slate-900 to-slate-950 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden border border-emerald-800/40">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <span>SO1 Machine Learning Pipeline</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            Sri Lanka Agricultural Cultivation Cost Estimator
          </h2>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
            Calibrated probabilistic forecasting model trained on over a decade of Department of Agriculture (DOA) socio-economic field surveys, featuring macroeconomic inflation regime stratification and TreeSHAP explainability.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/predict"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40"
            >
              <Calculator className="w-4 h-4" />
              <span>Predict Cultivation Cost</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
            <Link
              to="/batch"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-colors border border-slate-700"
            >
              <span>Batch Estimation</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 3 Core System Health Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
        {/* Model Version Card */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Model Version
            </span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 font-mono">
              {health?.model_version || 'gb_tuned_v1'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Tuned GradientBoosting Regressor</p>
        </div>

        {/* Pipeline Status Card */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Pipeline Status
            </span>
            <div
              className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                isServerOnline
                  ? 'bg-emerald-50 text-emerald-600'
                  : 'bg-rose-50 text-rose-600'
              }`}
            >
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isServerOnline ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span className="text-2xl font-bold text-emerald-700">Loaded & Ready</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5 text-rose-600" />
                <span className="text-2xl font-bold text-rose-700">
                  {healthLoading ? 'Connecting...' : 'Disconnected'}
                </span>
              </>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {isServerOnline ? 'Model & TreeSHAP pre-warmed in memory' : 'Ensure FastAPI backend is running on :8000'}
          </p>
        </div>

        {/* Server Uptime Card */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Server Uptime
            </span>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 font-mono">
              {health?.uptime_seconds !== undefined
                ? formatUptime(health.uptime_seconds)
                : '—'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Monitored via FastAPI lifespan hook</p>
        </div>
      </div>

      {/* Model Comparison Card */}
      <div className="bg-gradient-to-br from-white to-blue-50/40 rounded-xl p-5 sm:p-6 border border-blue-100 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-xl bg-blue-100/80 text-blue-700 flex items-center justify-center shrink-0 shadow-2xs">
            <BarChart3 className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900">
              Model Comparison
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 mt-0.5">
              See how 8 ML models (4 shallow, 4 deep) performed under Leave-One-Season-Out validation.
            </p>
          </div>
        </div>
        <Link
          to="/model-comparison"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-xs transition-colors shrink-0 self-start sm:self-center"
        >
          <span>View Comparison →</span>
        </Link>
      </div>

      {/* Model Scope Card */}
      <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Training & Model Scope</h3>
            <p className="text-xs sm:text-sm text-slate-500">
              Valid input spaces parameterized directly from verified Department of Agriculture datasets.
            </p>
          </div>
          <span className="self-start sm:self-auto text-xs px-2.5 py-1 rounded-full bg-slate-100 font-medium text-slate-700 font-mono">
            LOSO CV R² = 0.8528
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-5">
          <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <Layers className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold">Crops Supported</span>
            </div>
            <span className="text-2xl font-extrabold text-slate-900">
              {metadata?.crops_supported?.length || 23}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">High/Medium sample tiers</p>
          </div>

          <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <MapPin className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold">Districts / Systems</span>
            </div>
            <span className="text-2xl font-extrabold text-slate-900">
              {metadata?.districts_supported?.length || 25}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">National agricultural zones</p>
          </div>

          <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <Calendar className="w-4 h-4 text-amber-600" />
              <span className="text-xs font-semibold">Survey Horizon</span>
            </div>
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {metadata?.training_year_range
                ? `${metadata.training_year_range[0]}–${metadata.training_year_range[1]}`
                : '2014–2025'}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">11-year empirical span</p>
          </div>

          <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 text-slate-500 mb-1">
              <DollarSign className="w-4 h-4 text-violet-600" />
              <span className="text-xs font-semibold">Mean LKR/USD Rate</span>
            </div>
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {metadata?.training_usd_lkr_mean
                ? `${metadata.training_usd_lkr_mean.toFixed(1)}`
                : '201.1'}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">Shock threshold: ±30%</p>
          </div>
        </div>

        {/* Crops badges */}
        <div className="pt-3 border-t border-slate-100">
          <span className="text-xs font-semibold text-slate-600 block mb-2">
            Sample Validated Crops:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {metadata?.crops_supported?.slice(0, 15).map((crop) => (
              <span
                key={crop}
                className="text-xs px-2.5 py-1 rounded-lg bg-emerald-50/80 text-emerald-800 border border-emerald-200/60 font-medium"
              >
                {crop}
              </span>
            ))}
            {(metadata?.crops_supported?.length || 0) > 15 && (
              <span className="text-xs px-2 py-1 rounded-lg bg-slate-100 text-slate-500 font-medium">
                +{metadata!.crops_supported.length - 15} more
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Data Coverage Card */}
      <div className="bg-white rounded-xl p-5 sm:p-6 border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Database className="w-4 h-4 text-emerald-600" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Data Coverage</h3>
              <p className="text-xs text-slate-500">
                Empirical coverage across Sri Lankan agricultural production regions
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
            Verified Surveys
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Districts with data</span>
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {matrix?.all_districts?.filter((d: string) => matrix.districts[d] && Object.keys(matrix.districts[d].crops).length > 0).length || 25}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">Agricultural zones</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Crops with data</span>
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              {matrix?.all_crops?.length || 23}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">Field & horticultural</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Crop-district combinations</span>
            <span className="text-2xl font-extrabold text-emerald-700 font-mono">
              {matrix?.total_combinations || 55}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">Active cultivation pairs</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Total combinations tested</span>
            <span className="text-2xl font-extrabold text-slate-900 font-mono">
              ~{matrix?.total_samples || 641}
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">Seasonal survey records</p>
          </div>
        </div>
      </div>

      {/* Recent Predictions Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base sm:text-lg font-bold text-slate-900">
              Recent Predictions
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
              {recentPredictions.length} / 20
            </span>
          </div>
          {recentPredictions.length > 0 && (
            <button
              onClick={handleClearHistory}
              className="text-xs text-slate-400 hover:text-rose-600 flex items-center gap-1 transition-colors px-2 py-1 rounded-md hover:bg-rose-50"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear History</span>
            </button>
          )}
        </div>

        {recentPredictions.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <Calculator className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-700">No predictions recorded yet</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
              Execute your first agricultural cultivation cost prediction to view historical outputs here.
            </p>
            <Link
              to="/predict"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-sm transition-all"
            >
              <span>Make Your First Prediction</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 font-semibold">Crop & District</th>
                  <th className="py-3 px-4 font-semibold">Season / Reference</th>
                  <th className="py-3 px-4 font-semibold">Predicted Cost</th>
                  <th className="py-3 px-4 font-semibold">80% Interval</th>
                  <th className="py-3 px-4 font-semibold">Confidence</th>
                  <th className="py-3 px-4 font-semibold text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentPredictions.map((pred) => (
                  <tr key={pred.request_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{pred.crop}</div>
                      <div className="text-xs text-slate-500">{pred.district}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      <span>{pred.season} (Ref: {pred.reference_year || 2025})</span>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900 font-mono">
                      {formatLKR(pred.predicted_cost)}
                    </td>
                    <td className="py-3 px-4 text-xs font-mono text-slate-600">
                      {formatLKR(pred.interval_low)} – {formatLKR(pred.interval_high)}
                    </td>
                    <td className="py-3 px-4">
                      {pred.low_confidence ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          Low Confidence
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Confident
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right text-xs text-slate-400 font-mono">
                      {formatDateTime(pred.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
