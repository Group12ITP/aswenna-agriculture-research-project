import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Layers,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Info,
  CheckCircle2,
  BarChart2,
  Table,
  ShieldAlert,
  ChevronDown
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot,
  ReferenceArea
} from 'recharts';

const API_BASE = 'http://localhost:8000';

const HORIZONS = [
  { value: 1, label: '1 Week', modelName: 'Lasso', tier: 'Linear' },
  { value: 4, label: '4 Weeks', modelName: 'AutoARIMA', tier: 'Statistical' },
  { value: 8, label: '8 Weeks', modelName: 'CatBoost', tier: 'Tree Ensemble' },
  { value: 12, label: '12 Weeks', modelName: 'Transformer', tier: 'Deep Learning' }
];

const MODEL_OPTIONS = [
  { value: 'selected', label: 'Rule-Selected Model (Default)', desc: 'Optimal architecture per horizon' },
  { value: 'naive', label: 'Naive Persistence (y_t)', desc: 'Last observed retail price' },
  { value: 'seasonal_mean_4yr', label: '4-Year Seasonal Mean', desc: 'Average of same week across 4 prior years' }
];

export default function App() {
  const [vegetables, setVegetables] = useState([]);
  const [selectedVeg, setSelectedVeg] = useState('Carrot');
  const [horizon, setHorizon] = useState(4);
  const [modelType, setModelType] = useState('selected');
  const [historyWeeks, setHistoryWeeks] = useState(104);

  const [forecastData, setForecastData] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [error, setError] = useState(null);

  // Group vegetables by category
  const groupedVegetables = useMemo(() => {
    const groups = {
      'leafy vegetables': [],
      'lowland vegetables': [],
      'upcountry vegetables': []
    };
    vegetables.forEach(v => {
      const cat = (v.category || '').toLowerCase();
      if (groups[cat]) {
        groups[cat].push(v);
      } else {
        if (!groups['other']) groups['other'] = [];
        groups['other'].push(v);
      }
    });
    return groups;
  }, [vegetables]);

  // Initial load: Fetch vegetable catalog
  useEffect(() => {
    async function loadCatalog() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/vegetables`);
        if (!res.ok) throw new Error(`Server returned ${res.status}`);
        const data = await res.json();
        setVegetables(data);
        if (data.length > 0 && !selectedVeg) {
          setSelectedVeg(data[0].name);
        }
      } catch (err) {
        setError(`Failed to connect to forecasting server: ${err.message}. Make sure the backend is running on port 8000.`);
      } finally {
        setLoading(false);
      }
    }
    loadCatalog();
  }, []);

  // Fetch forecast and history when selections change
  const fetchForecastAndHistory = async (vegName = selectedVeg, h = horizon, m = modelType, w = historyWeeks) => {
    if (!vegName) return;
    try {
      setError(null);
      setChartLoading(true);

      const [fcRes, histRes] = await Promise.all([
        fetch(`${API_BASE}/forecast?vegetable=${encodeURIComponent(vegName)}&horizon=${h}&model=${m}`),
        fetch(`${API_BASE}/history?vegetable=${encodeURIComponent(vegName)}&weeks=${w}`)
      ]);

      if (!fcRes.ok) {
        const errJson = await fcRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `Forecast failed with status ${fcRes.status}`);
      }
      if (!histRes.ok) {
        const errJson = await histRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `History failed with status ${histRes.status}`);
      }

      const fcData = await fcRes.json();
      const histData = await histRes.json();

      setForecastData(fcData);
      setHistoryData(histData.history || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    if (vegetables.length > 0 && selectedVeg) {
      fetchForecastAndHistory(selectedVeg, horizon, modelType, historyWeeks);
    }
  }, [selectedVeg, horizon, modelType, historyWeeks, vegetables.length]);

  // Format currency
  const fmtLkr = (val) => {
    if (val === null || val === undefined) return 'N/A';
    return `Rs. ${Number(val).toFixed(2)}`;
  };

  // Category badge color
  const getCatBadge = (cat) => {
    const c = (cat || '').toLowerCase();
    if (c.includes('leafy')) return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60';
    if (c.includes('lowland')) return 'bg-amber-950/80 text-amber-300 border-amber-800/60';
    return 'bg-indigo-950/80 text-indigo-300 border-indigo-800/60';
  };

  // Calculations for result card
  const priceChange = useMemo(() => {
    if (!forecastData || !forecastData.last_observed_price) return null;
    const diff = forecastData.point_forecast - forecastData.last_observed_price;
    const pct = (diff / forecastData.last_observed_price) * 100;
    return { diff, pct };
  }, [forecastData]);

  // Recharts Data Prep: merge historical series with the future forecast point
  const chartSeries = useMemo(() => {
    if (!historyData || historyData.length === 0 || !forecastData) return [];

    const series = historyData.map(pt => ({
      week: pt.week,
      date: pt.date,
      historicalPrice: pt.price,
      forecastPrice: null,
      lo80: null,
      hi80: null,
      type: 'history'
    }));

    // Add forecast point at target week
    series.push({
      week: forecastData.target_week,
      date: forecastData.target_date,
      historicalPrice: null,
      forecastPrice: forecastData.point_forecast,
      lo80: forecastData.interval_80 ? forecastData.interval_80.lo : null,
      hi80: forecastData.interval_80 ? forecastData.interval_80.hi : null,
      type: 'forecast'
    });

    return series;
  }, [historyData, forecastData]);

  // Y-axis bounds
  const yDomain = useMemo(() => {
    if (chartSeries.length === 0) return [0, 500];
    const vals = [];
    chartSeries.forEach(d => {
      if (d.historicalPrice) vals.push(d.historicalPrice);
      if (d.forecastPrice) vals.push(d.forecastPrice);
      if (d.lo80) vals.push(d.lo80);
      if (d.hi80) vals.push(d.hi80);
    });
    const minVal = Math.min(...vals);
    const maxVal = Math.max(...vals);
    const padding = (maxVal - minVal) * 0.15 || 20;
    return [Math.max(0, Math.floor(minVal - padding)), Math.ceil(maxVal + padding)];
  }, [chartSeries]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                Sri Lankan DCS Vegetable Price Forecaster
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  Production Inference
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Official Department of Census & Statistics Weekly Retail Prices • Origin Week 464 (2026-08-25)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center text-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/90 text-slate-300 border border-slate-700/60">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              32 Commodities Active
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6">

        {/* Global Statistical Note Banner */}
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm flex items-start gap-3 shadow-lg shadow-amber-950/20">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-amber-300">
              Retail prices (Rs/kg). h=4 selected model is not statistically better than naive persistence.
            </p>
            <p className="text-xs text-amber-200/80 leading-relaxed">
              At the 4-week primary planning horizon, Diebold-Mariano tests against Naive Persistence (p = 0.822) show no statistically significant improvement. Forecasts are generated strictly using causal prior information up to origin week 464.
            </p>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-200">System Alert</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
            <button
              onClick={() => fetchForecastAndHistory()}
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Top Control Bar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-sm">

          {/* 1. Vegetable Select */}
          <div className="md:col-span-4 space-y-1.5">
            <label htmlFor="vegetable-select" className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Select Vegetable</span>
              <span className="text-[11px] text-slate-500">32 commodities</span>
            </label>
            <div className="relative">
              <select
                id="vegetable-select"
                value={selectedVeg}
                onChange={(e) => setSelectedVeg(e.target.value)}
                className="w-full bg-slate-800/90 hover:bg-slate-800 text-white text-sm font-medium rounded-xl border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 py-2.5 px-3.5 appearance-none cursor-pointer transition shadow-inner"
              >
                {Object.entries(groupedVegetables).map(([cat, list]) => (
                  <optgroup
                    key={cat}
                    label={cat.toUpperCase()}
                    className="bg-slate-900 text-slate-400 font-semibold"
                  >
                    {list.map((v) => (
                      <option key={v.name} value={v.name} className="bg-slate-800 text-white font-normal py-1">
                        {v.name} ({fmtLkr(v.latest_price)})
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-3 pointer-events-none" />
            </div>
          </div>

          {/* 2. Horizon Buttons */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Forecast Horizon</span>
              <span className="text-[11px] text-slate-500">Selected: {horizon} weeks ahead</span>
            </label>
            <div className="grid grid-cols-4 gap-1.5 p-1 bg-slate-950/60 rounded-xl border border-slate-800">
              {HORIZONS.map((h) => {
                const isActive = horizon === h.value;
                return (
                  <button
                    key={h.value}
                    id={`horizon-${h.value}`}
                    onClick={() => setHorizon(h.value)}
                    type="button"
                    className={`py-2 px-2 rounded-lg text-xs font-medium transition flex flex-col items-center justify-center gap-0.5 ${
                      isActive
                        ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    <span>{h.label}</span>
                    <span className={`text-[10px] ${isActive ? 'text-slate-900' : 'text-slate-500'}`}>
                      {h.modelName}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Model Selector & Button */}
          <div className="md:col-span-3 space-y-1.5">
            <label htmlFor="model-select" className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span>Model Comparison</span>
              <span className="text-[11px] text-slate-500">Architecture</span>
            </label>
            <div className="flex gap-2">
              <select
                id="model-select"
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full bg-slate-800/90 text-white text-xs font-medium rounded-xl border border-slate-700/80 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 py-2.5 px-3 appearance-none cursor-pointer transition"
              >
                {MODEL_OPTIONS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <button
                id="forecast-btn"
                onClick={() => fetchForecastAndHistory()}
                disabled={chartLoading}
                className="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-emerald-400 font-semibold rounded-xl border border-slate-700 hover:border-emerald-500/50 transition flex items-center justify-center shrink-0 disabled:opacity-50"
                title="Refresh Forecast"
              >
                <RefreshCw className={`w-4 h-4 ${chartLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

        </div>

        {/* Core Result Cards */}
        {forecastData && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

            {/* Main Result Card */}
            <div className="lg:col-span-2 p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 shadow-xl flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>

              <div>
                <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xl font-bold text-white tracking-tight">
                      {forecastData.vegetable}
                    </span>
                    <span className={`text-xs px-2.5 py-1 rounded-full border font-medium capitalize ${getCatBadge(forecastData.category)}`}>
                      {forecastData.category}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                      {forecastData.unit}
                    </span>
                  </div>

                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-emerald-400 border border-slate-700/80 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {forecastData.model_used}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 my-4">
                  {/* Point Forecast */}
                  <div>
                    <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 block mb-1">
                      Point Retail Forecast (h={horizon}w)
                    </span>
                    <div className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight flex items-baseline gap-2">
                      <span>Rs. {Number(forecastData.point_forecast).toFixed(2)}</span>
                      <span className="text-sm font-normal text-slate-400">/{forecastData.unit}</span>
                    </div>

                    {/* Percentage change */}
                    {priceChange && (
                      <div className="flex items-center gap-2 mt-2 text-xs font-medium">
                        <span className="text-slate-400">vs Origin Week 464:</span>
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold ${
                            priceChange.diff >= 0
                              ? 'bg-rose-500/15 text-rose-300 border border-rose-500/20'
                              : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/20'
                          }`}
                        >
                          {priceChange.diff >= 0 ? (
                            <TrendingUp className="w-3 h-3 text-rose-400" />
                          ) : (
                            <TrendingDown className="w-3 h-3 text-emerald-400" />
                          )}
                          {priceChange.diff >= 0 ? '+' : ''}
                          {priceChange.pct.toFixed(1)}% ({priceChange.diff >= 0 ? '+' : ''}Rs. {priceChange.diff.toFixed(2)})
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Horizon Target Details */}
                  <div className="space-y-2 border-t sm:border-t-0 sm:border-l border-slate-800 sm:pl-6 pt-3 sm:pt-0">
                    <div>
                      <span className="text-xs font-semibold text-slate-400 block">Forecast Origin</span>
                      <span className="text-sm font-mono text-slate-200">
                        Week {forecastData.origin_week} ({forecastData.origin_date})
                      </span>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-400 block">Target Horizon Date</span>
                      <span className="text-sm font-mono font-bold text-emerald-400">
                        Week {forecastData.target_week} ({forecastData.target_date})
                      </span>
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-slate-400 block">Last Observed Price</span>
                      <span className="text-sm font-mono text-slate-300">
                        Rs. {Number(forecastData.last_observed_price).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Conformal Intervals Footer */}
              <div className="mt-4 pt-4 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {/* 80% Interval */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-emerald-500/20 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-emerald-400">80% Conformal Band</span>
                    <span className="text-[10px] text-slate-400">Scale-aware (cal. w393-416)</span>
                  </div>
                  {forecastData.interval_80 ? (
                    <div className="text-sm font-bold text-white font-mono">
                      Rs. {forecastData.interval_80.lo.toFixed(2)} — Rs. {forecastData.interval_80.hi.toFixed(2)}
                    </div>
                  ) : (
                    <div className="text-slate-400 italic">Not available</div>
                  )}
                </div>

                {/* 95% Interval */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-400">95% Conformal Band</span>
                    <span className="text-[10px] text-slate-500">Uncalibrated</span>
                  </div>
                  <div className="text-xs text-slate-400 font-mono italic">
                    null (Not in frozen category calibration)
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Baseline Comparison Card */}
            <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Table className="w-4 h-4 text-emerald-400" />
                  Horizon {horizon} Benchmarks
                </h3>

                <div className="space-y-3">
                  {/* Selected */}
                  <div className={`p-3 rounded-xl border transition ${
                    modelType === 'selected'
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                      : 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                  }`}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-bold flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        Selected: {HORIZONS.find(h => h.value === horizon)?.modelName}
                      </span>
                      <span className="font-mono font-bold text-white">
                        {fmtLkr(forecastData.point_forecast)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">Rule-selected by 1-SE validation rule</p>
                  </div>

                  {/* Naive */}
                  <div className={`p-3 rounded-xl border transition ${
                    modelType === 'naive'
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                      : 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                  }`}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-bold flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                        Naive Persistence
                      </span>
                      <span className="font-mono font-bold text-white">
                        {fmtLkr(forecastData.naive_forecast)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">Carries forward week 464 price</p>
                  </div>

                  {/* Seasonal Mean */}
                  <div className={`p-3 rounded-xl border transition ${
                    modelType === 'seasonal_mean_4yr'
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                      : 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                  }`}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-bold flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                        4-Year Seasonal Mean
                      </span>
                      <span className="font-mono font-bold text-white">
                        {fmtLkr(forecastData.seasonal_mean_4yr_forecast)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">Average of target calendar week across 2022–2025</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 leading-tight">
                Diebold-Mariano test p-value vs Seasonal Mean: <span className="font-mono text-slate-200">h=4 (p=0.038), h=8 (p=0.027)</span>
              </div>
            </div>

          </div>
        )}

        {/* Historical Chart with Forecast Point & Conformal Band */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-emerald-400" />
                Historical Retail Trajectory & Forward Forecast
              </h2>
              <p className="text-xs text-slate-400">
                Weekly retail prices (Rs/kg) showing past {historyWeeks} weeks with forward projection to Week {forecastData?.target_week}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">History window:</span>
              <div className="flex bg-slate-950 rounded-lg p-0.5 border border-slate-800 text-xs">
                <button
                  onClick={() => setHistoryWeeks(52)}
                  className={`px-2.5 py-1 rounded-md transition ${historyWeeks === 52 ? 'bg-slate-800 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                >
                  1 Year (52w)
                </button>
                <button
                  onClick={() => setHistoryWeeks(104)}
                  className={`px-2.5 py-1 rounded-md transition ${historyWeeks === 104 ? 'bg-slate-800 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                >
                  2 Years (104w)
                </button>
              </div>
            </div>
          </div>

          {/* Chart Container */}
          <div className="h-80 w-full relative">
            {chartLoading ? (
              <div className="h-full w-full flex items-center justify-center bg-slate-950/40 rounded-xl">
                <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
              </div>
            ) : chartSeries.length === 0 ? (
              <div className="h-full w-full flex items-center justify-center text-slate-400 text-sm">
                No history data available for {selectedVeg}.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={chartSeries}
                  margin={{ top: 15, right: 30, left: 10, bottom: 25 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis
                    dataKey="week"
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(w) => `W${w}`}
                    tickLine={false}
                  />
                  <YAxis
                    domain={yDomain}
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(p) => `Rs.${p}`}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload || !payload.length) return null;
                      const pt = payload[0].payload;
                      const isForecast = pt.type === 'forecast';
                      return (
                        <div className="p-3 bg-slate-900/95 border border-slate-700/80 rounded-xl shadow-2xl text-xs space-y-1">
                          <div className="font-bold text-white flex items-center justify-between gap-3">
                            <span>Week {pt.week}</span>
                            <span className="text-[11px] text-slate-400 font-normal">{pt.date}</span>
                          </div>
                          {isForecast ? (
                            <div className="space-y-1 pt-1 border-t border-slate-800">
                              <div className="text-emerald-400 font-bold">
                                Projected: Rs. {Number(pt.forecastPrice).toFixed(2)}
                              </div>
                              {pt.lo80 && pt.hi80 && (
                                <div className="text-[11px] text-slate-300">
                                  80% Band: Rs. {pt.lo80.toFixed(2)} – Rs. {pt.hi80.toFixed(2)}
                                </div>
                              )}
                              <div className="text-[10px] text-emerald-300 font-mono">
                                Model: {forecastData.model_used}
                              </div>
                            </div>
                          ) : (
                            <div className="text-slate-200 font-semibold pt-1 border-t border-slate-800">
                              Retail Price: Rs. {Number(pt.historicalPrice).toFixed(2)}
                            </div>
                          )}
                        </div>
                      );
                    }}
                  />

                  {/* Historical Line */}
                  <Line
                    type="monotone"
                    dataKey="historicalPrice"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: '#10b981', stroke: '#fff', strokeWidth: 1 }}
                    isAnimationActive={false}
                  />

                  {/* Forecast Point Dot */}
                  {forecastData && (
                    <ReferenceDot
                      x={forecastData.target_week}
                      y={forecastData.point_forecast}
                      r={7}
                      fill="#38bdf8"
                      stroke="#ffffff"
                      strokeWidth={2}
                    />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Chart Legend & Explanation */}
          <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-emerald-500"></span> Historical Price (Weeks 360–464)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400 border border-white"></span> Forward Forecast Point (Week {forecastData?.target_week})
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-2 rounded bg-emerald-500/20 border border-emerald-500/40"></span> 80% Conformal Band
              </span>
            </div>
            <div className="text-slate-500 text-[11px]">
              Origin: Week 464 (2026-08-25) • Strictly Causal
            </div>
          </div>
        </div>

        {/* Comparison Table */}
        {forecastData && (
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Table className="w-4 h-4 text-emerald-400" />
                  Model Performance Comparison for {selectedVeg} (h={horizon} weeks)
                </h3>
                <p className="text-xs text-slate-400">
                  Side-by-side benchmark comparison against persistence and multi-year seasonal baselines
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2.5 px-3 font-semibold">Model Architecture</th>
                    <th className="py-2.5 px-3 font-semibold">Model Class</th>
                    <th className="py-2.5 px-3 font-semibold">Point Forecast</th>
                    <th className="py-2.5 px-3 font-semibold">Delta vs Origin</th>
                    <th className="py-2.5 px-3 font-semibold">% Change</th>
                    <th className="py-2.5 px-3 font-semibold">80% Coverage Interval</th>
                    <th className="py-2.5 px-3 font-semibold">Research Selection</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {/* Selected Model Row */}
                  <tr className="bg-emerald-500/5 hover:bg-emerald-500/10 transition">
                    <td className="py-3 px-3 font-bold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      {HORIZONS.find(h => h.value === horizon)?.modelName}
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-sans">
                      {HORIZONS.find(h => h.value === horizon)?.tier}
                    </td>
                    <td className="py-3 px-3 font-bold text-emerald-400">
                      Rs. {Number(forecastData.point_forecast).toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {priceChange ? `${priceChange.diff >= 0 ? '+' : ''}${priceChange.diff.toFixed(2)}` : '0.00'}
                    </td>
                    <td className="py-3 px-3">
                      {priceChange && (
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          priceChange.diff >= 0 ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {priceChange.pct >= 0 ? '+' : ''}{priceChange.pct.toFixed(1)}%
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {forecastData.interval_80
                        ? `[Rs.${forecastData.interval_80.lo.toFixed(2)}, Rs.${forecastData.interval_80.hi.toFixed(2)}]`
                        : 'N/A'}
                    </td>
                    <td className="py-3 px-3 font-sans">
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-semibold">
                        Selected Model
                      </span>
                    </td>
                  </tr>

                  {/* Naive Row */}
                  <tr className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-medium text-slate-200 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                      Naive Persistence
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-sans">Statistical Baseline</td>
                    <td className="py-3 px-3 text-slate-200">
                      Rs. {Number(forecastData.naive_forecast).toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-slate-400">0.00</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-400">
                        0.0%
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-500 italic font-sans text-[11px]">
                      Historical point
                    </td>
                    <td className="py-3 px-3 font-sans text-slate-400 text-[11px]">
                      Reference Baseline
                    </td>
                  </tr>

                  {/* Seasonal Mean Row */}
                  <tr className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-medium text-slate-200 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                      Seasonal Mean 4-Year
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-sans">Seasonal Baseline</td>
                    <td className="py-3 px-3 text-slate-200">
                      Rs. {Number(forecastData.seasonal_mean_4yr_forecast).toFixed(2)}
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {(forecastData.seasonal_mean_4yr_forecast - forecastData.last_observed_price).toFixed(2)}
                    </td>
                    <td className="py-3 px-3">
                      {(() => {
                        const smDiff = forecastData.seasonal_mean_4yr_forecast - forecastData.last_observed_price;
                        const smPct = (smDiff / forecastData.last_observed_price) * 100;
                        return (
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            smDiff >= 0 ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
                          }`}>
                            {smPct >= 0 ? '+' : ''}{smPct.toFixed(1)}%
                          </span>
                        );
                      })()}
                    </td>
                    <td className="py-3 px-3 text-slate-500 italic font-sans text-[11px]">
                      Empirical mean
                    </td>
                    <td className="py-3 px-3 font-sans text-slate-400 text-[11px]">
                      Benchmark (Strong at h=8,12)
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          Sri Lankan Vegetable Price Forecasting • Sri Lanka DCS Weekly Market Data 2017–2026 • Strictly Causal Inference
        </div>
      </footer>
    </div>
  );
}
