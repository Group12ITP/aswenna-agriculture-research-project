import React, { useState } from 'react';
import {
  DollarSign,
  ShieldCheck,
  AlertTriangle,
  Info,
  Copy,
  Check,
  BookmarkPlus,
  Sparkles,
} from 'lucide-react';
import type { PredictionResponse, PredictionRequest } from '../../types/api';
import { formatLKR, formatPct, humanizeFeature } from '../../lib/format';
import { SHAPBarChart } from './SHAPBarChart';
import { CostBreakdownChart } from './CostBreakdownChart';
import { addStoredPrediction } from '../../lib/storage';

interface PredictionResultProps {
  result: PredictionResponse | null;
  requestParams: PredictionRequest | null;
  isLoading: boolean;
  error: Error | null;
}

export const PredictionResult: React.FC<PredictionResultProps> = ({
  result,
  requestParams,
  isLoading,
  error,
}) => {
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);

  // Copy plain text summary to clipboard
  const handleCopySummary = async () => {
    if (!result || !requestParams) return;
    const top = result.top_drivers?.[0];
    const topDriverText = top
      ? `Top driver: ${humanizeFeature(top.feature)} (${top.direction}${formatPct(top.contribution_pct)}).`
      : '';
    const text = `Predicted cost for ${requestParams.crop} in ${requestParams.district}: ${formatLKR(
      result.predicted_cost
    )}. Expected range: ${formatLKR(result.interval_low)} – ${formatLKR(
      result.interval_high
    )}. ${topDriverText}`;

    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  // Save to localStorage history
  const handleSaveToHistory = () => {
    if (!result || !requestParams) return;
    addStoredPrediction({
      request_id: result.request_id,
      timestamp: result.timestamp,
      crop: requestParams.crop,
      district: requestParams.district,
      season: requestParams.season,
      reference_year: result.reference_year,
      predicted_cost: result.predicted_cost,
      interval_low: result.interval_low,
      interval_high: result.interval_high,
      low_confidence: result.low_confidence,
      warning: result.warning,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  // 1. Loading Skeleton State
  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/80 shadow-xs animate-pulse space-y-6">
        <div className="h-4 bg-slate-200 rounded w-1/3 mb-2" />
        <div className="h-12 bg-slate-200 rounded w-2/3" />
        <div className="h-6 bg-slate-100 rounded w-full" />
        <div className="h-48 bg-slate-100 rounded-xl" />
        <div className="flex gap-3">
          <div className="h-10 bg-slate-200 rounded-xl w-1/2" />
          <div className="h-10 bg-slate-200 rounded-xl w-1/2" />
        </div>
      </div>
    );
  }

  // 2. Error State (Verbatim backend / 422 error display)
  if (error) {
    return (
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-rose-200 shadow-xs">
        <div className="flex items-start gap-3.5 text-rose-700">
          <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-rose-900">
              Inference / Validation Error
            </h3>
            <p className="text-xs text-rose-600 mt-0.5">
              The API server rejected the request with status 422 or encountered an error.
            </p>
            <div className="mt-3 p-3.5 bg-rose-50 rounded-xl border border-rose-200/70 text-xs font-mono text-rose-900 break-words leading-relaxed">
              {error.message || 'An unexpected network error occurred while querying /predict.'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 3. Initial Empty State
  if (!result) {
    return (
      <div className="bg-white rounded-2xl p-8 border border-dashed border-slate-300 text-center flex flex-col items-center justify-center min-h-[460px]">
        <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 shadow-inner">
          <DollarSign className="w-8 h-8 text-emerald-600" />
        </div>
        <h3 className="text-base font-bold text-slate-800">
          Awaiting Parameter Input
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Select your target district, crop, season, and macroeconomic exchange rate on the left, then click <b>Predict Cultivation Cost</b>.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2 text-[11px] text-slate-400">
          <span className="px-2.5 py-1 bg-slate-100 rounded-lg">80% Calibrated Intervals</span>
          <span className="px-2.5 py-1 bg-slate-100 rounded-lg">Local TreeSHAP Drivers</span>
          <span className="px-2.5 py-1 bg-slate-100 rounded-lg">Strict Homoscedasticity</span>
        </div>
      </div>
    );
  }

  // 4. Render Active Prediction Result
  return (
    <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-600" />
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
            Model Prediction Result
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Reference Year Pill */}
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200 shadow-xs">
            Reference: {result.reference_year || 2025}
          </span>
        </div>
      </div>

      {/* Primary Cost Display (BIG NUMBER) */}
      <div>
        <div className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight font-mono">
          {formatLKR(result.predicted_cost)}
        </div>
        <p className="text-xs sm:text-sm font-medium text-slate-500 mt-1">
          Estimated cultivation cost per acre ({requestParams?.crop} • {requestParams?.district})
        </p>
      </div>

      {/* Interval Pill */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            <span>Expected Range (80% Confidence):</span>
            <div
              className="group relative cursor-pointer text-slate-400 hover:text-slate-600"
              title="80% of historical outcomes fall within this range under similar macroeconomic regimes"
            >
              <Info className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-base sm:text-lg font-bold font-mono text-emerald-800 mt-0.5">
            {formatLKR(result.interval_low)} – {formatLKR(result.interval_high)}
          </div>
        </div>
        <span className="self-start sm:self-auto text-[11px] font-medium text-slate-500 bg-white px-2.5 py-1 rounded-lg border border-slate-200">
          Multiplicative Log-Normal
        </span>
      </div>

      {/* Lag Saturation Amber Callout */}
      {result.lag_saturation_detected && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-start gap-2.5 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed font-normal">
            <span className="font-semibold text-amber-950">⚠️ Prior cost exceeds the model's training range. </span>
            This prediction is a ceiling estimate (capped at Rs {result.lag_saturation_threshold ? Math.round(result.lag_saturation_threshold).toLocaleString() : ''}).
          </div>
        </div>
      )}

      {/* Confidence badge — GREEN or RED based on low_confidence */}
      {result.low_confidence ? (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-300 text-rose-900 text-xs flex items-start gap-2.5 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold text-rose-900 block">Low Confidence — Model Extrapolating</span>
            <span className="text-rose-700 leading-relaxed font-normal">
              {result.low_confidence_reason || result.warning || 'Macroeconomic inputs fall outside the model training range. Interval has been widened by 1.5x.'}
            </span>
          </div>
        </div>
      ) : (
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-xs">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Confident Prediction — Input parameters are within historical training range</span>
        </div>
      )}

      {/* SHAP Feature Drivers Chart */}
      <div className="pt-2">
        <SHAPBarChart drivers={result.top_drivers} />
      </div>

      {/* Historical Cost Component Breakdown Donut Chart */}
      {result.cost_breakdown && (
        <CostBreakdownChart
          breakdown={result.cost_breakdown}
          totalCost={result.predicted_cost}
          breakdownSource={result.breakdown_source}
          breakdownAliasNote={result.breakdown_alias_note}
        />
      )}

      {/* Action Buttons: Copy Summary & Save History */}
      <div className="pt-4 border-t border-slate-100 flex flex-wrap gap-3">
        <button
          onClick={handleCopySummary}
          className="flex-1 py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs transition-colors flex items-center justify-center gap-1.5 shadow-xs"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span>Summary Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-600" />
              <span>Copy Summary</span>
            </>
          )}
        </button>

        <button
          onClick={handleSaveToHistory}
          className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 font-semibold text-xs transition-colors flex items-center justify-center gap-1.5 shadow-xs"
        >
          {saved ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span>Saved to History!</span>
            </>
          ) : (
            <>
              <BookmarkPlus className="w-3.5 h-3.5 text-emerald-700" />
              <span>Save to History</span>
            </>
          )}
        </button>
      </div>

      {/* Gray italic reference note at the bottom */}
      <div className="pt-3 border-t border-slate-100">
        <p className="text-xs text-slate-400 italic text-center sm:text-left">
          {result.reference_note || "Model reference year is 2025 (latest available data). Predictions will refresh when 2026 data is ingested."}
        </p>
      </div>
    </div>
  );
};
