import React, { useState } from 'react';
import Papa from 'papaparse';
import {
  Upload,
  FileSpreadsheet,
  Download,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Layers,
  ArrowUpDown,
} from 'lucide-react';
import { predictBatch } from '../api/prediction';
import { formatLKR } from '../lib/format';
import type { PredictionRequest, PredictionResponse } from '../types/api';

interface BatchRowResult {
  input: PredictionRequest;
  output?: PredictionResponse;
  error?: string;
}

export const BatchPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [results, setResults] = useState<BatchRowResult[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<string>('predicted_cost');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  // Generate and download sample CSV template without year_start
  const handleDownloadSample = () => {
    const sampleCsv = `district,crop,season,irrigation_type,usd_lkr_rate,prev_season_cost
Anuradhapura,Paddy,Maha,Irrigated,301.68,125000
Nuwara Eliya,Potato,Maha,Irrigated,301.68,865823
Jaffna,Red Onion,Yala,Irrigated,301.68,450000
Matale,Big Onion,Yala,Irrigated,301.68,520000
Kurunegala,Kurakkan,Maha,Rainfed,301.68,`;

    const blob = new Blob([sampleCsv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'sample_coc_batch.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle CSV file selection and parsing
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setParseError(null);
    setResults([]);
  };

  // Run sequential batch prediction
  const handleProcessBatch = () => {
    if (!file) return;

    setParseError(null);
    setIsProcessing(true);

    Papa.parse<any>(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (parsed) => {
        try {
          const rawRows = parsed.data;
          if (!rawRows || rawRows.length === 0) {
            setParseError('The uploaded CSV file is empty.');
            setIsProcessing(false);
            return;
          }

          // Validate and normalize rows (no year_start needed)
          const requests: PredictionRequest[] = rawRows.map((row, index) => {
            const district = row.district || row.District || '';
            const crop = row.crop || row.Crop || '';
            const season = (row.season || row.Season || 'Maha') as 'Maha' | 'Yala';
            const irrigation_type = (row.irrigation_type ||
              row.Irrigation_Type ||
              'Irrigated') as 'Irrigated' | 'Rainfed' | 'Unspecified';
            const usd_lkr_rate = parseFloat(row.usd_lkr_rate || row.USD_LKR_Rate || '300.73');
            const prevCostRaw = row.prev_season_cost || row.Prev_Season_Cost;
            const prev_season_cost =
              prevCostRaw !== undefined && prevCostRaw !== '' && !isNaN(Number(prevCostRaw))
                ? Number(prevCostRaw)
                : null;

            if (!district || !crop) {
              throw new Error(`Row ${index + 1} is missing required 'district' or 'crop' fields.`);
            }

            return {
              district: district.trim(),
              crop: crop.trim(),
              season,
              irrigation_type,
              reference_year: 2025,
              usd_lkr_rate,
              prev_season_cost,
            };
          });

          setProgress({ completed: 0, total: requests.length });

          const rowResults: BatchRowResult[] = [];
          for (let i = 0; i < requests.length; i++) {
            const req = requests[i];
            try {
              const [res] = await predictBatch([req]);
              rowResults.push({ input: req, output: res });
            } catch (err: any) {
              rowResults.push({ input: req, error: err.message || 'Inference error' });
            }
            setProgress({ completed: i + 1, total: requests.length });
          }

          setResults(rowResults);
        } catch (err: any) {
          setParseError(err.message || 'Failed to process CSV file.');
        } finally {
          setIsProcessing(false);
        }
      },
      error: (error) => {
        setParseError(`CSV Parsing Error: ${error.message}`);
        setIsProcessing(false);
      },
    });
  };

  // Export results table to CSV
  const handleExportResults = () => {
    if (results.length === 0) return;

    const exportRows = results.map((r) => ({
      District: r.input.district,
      Crop: r.input.crop,
      Season: r.input.season,
      Irrigation_Type: r.input.irrigation_type,
      Reference_Year: r.output?.reference_year || 2025,
      USD_LKR_Rate: r.input.usd_lkr_rate,
      Prev_Season_Cost: r.input.prev_season_cost ?? '',
      Predicted_Cost_LKR: r.output?.predicted_cost ?? '',
      Interval_Low_LKR: r.output?.interval_low ?? '',
      Interval_High_LKR: r.output?.interval_high ?? '',
      Low_Confidence: r.output ? (r.output.low_confidence ? 'TRUE' : 'FALSE') : 'ERROR',
      Warning: r.output?.warning ?? '',
      Error_Message: r.error ?? '',
    }));

    const csvStr = Papa.unparse(exportRows);
    const blob = new Blob([csvStr], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `coc_batch_predictions_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Sort results table
  const sortedResults = [...results].sort((a, b) => {
    let aVal: any = 0;
    let bVal: any = 0;

    if (sortField === 'predicted_cost') {
      aVal = a.output?.predicted_cost ?? -1;
      bVal = b.output?.predicted_cost ?? -1;
    } else if (sortField === 'crop') {
      aVal = a.input.crop.toLowerCase();
      bVal = b.input.crop.toLowerCase();
    } else if (sortField === 'district') {
      aVal = a.input.district.toLowerCase();
      bVal = b.input.district.toLowerCase();
    }

    if (aVal < bVal) return sortAsc ? -1 : 1;
    if (aVal > bVal) return sortAsc ? 1 : -1;
    return 0;
  });

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-300">
      {/* Upload Header Card */}
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Upload className="w-5 h-5 text-emerald-600" />
              <span>Batch Cultivation Estimator</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Upload multi-crop agricultural scenarios to run automated sequential inferences without entering years.
            </p>
          </div>
          <button
            onClick={handleDownloadSample}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs transition-colors self-start sm:self-auto cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Download Sample CSV</span>
          </button>
        </div>

        {/* Expected Format Notice (No year_start) */}
        <div className="my-5 p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-600">
          <div className="font-semibold text-slate-800 mb-1 flex items-center gap-1.5">
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>Expected CSV Column Headers (no year column needed):</span>
          </div>
          <code className="text-[11px] font-mono text-emerald-800 bg-emerald-50/80 px-2 py-1 rounded border border-emerald-200/60 block overflow-x-auto">
            district, crop, season, irrigation_type, usd_lkr_rate, prev_season_cost
          </code>
        </div>

        {/* File Dropzone Area */}
        <div className="border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center hover:border-emerald-500 transition-colors bg-slate-50/40">
          <input
            type="file"
            id="csv-file-input"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="csv-file-input" className="cursor-pointer block">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3 shadow-inner">
              <Upload className="w-6 h-6 text-emerald-600" />
            </div>
            <span className="text-sm font-bold text-slate-800 block">
              {file ? file.name : 'Click to select or drop a CSV file'}
            </span>
            <span className="text-xs text-slate-400 block mt-1">
              Supports standard UTF-8 encoded comma-separated files
            </span>
          </label>
        </div>

        {parseError && (
          <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{parseError}</span>
          </div>
        )}

        {/* Action Button & Progress */}
        <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <button
            onClick={handleProcessBatch}
            disabled={!file || isProcessing}
            className="py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm tracking-wide shadow-md shadow-emerald-700/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            {isProcessing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                <span>
                  Processing Batch ({progress.completed} / {progress.total})...
                </span>
              </>
            ) : (
              <>
                <Layers className="w-4 h-4" />
                <span>Execute Batch Predictions</span>
              </>
            )}
          </button>

          {isProcessing && (
            <div className="flex-1 max-w-xs">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>Inference Progress</span>
                <span className="font-mono">
                  {Math.round((progress.completed / Math.max(progress.total, 1)) * 100)}%
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-emerald-500 h-2 transition-all duration-300 rounded-full"
                  style={{
                    width: `${(progress.completed / Math.max(progress.total, 1)) * 100}%`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results Table Card */}
      {results.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden animate-in fade-in duration-300">
          <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <span>Batch Inference Results ({results.length} Scenarios)</span>
                </h3>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 text-xs font-mono font-medium">
                  reference_year: 2025
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Forward predictions using latest 2025 reference data and calibrated 80% multiplicative intervals.
              </p>
            </div>
            <button
              onClick={handleExportResults}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-sm transition-all self-start sm:self-auto cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Results (CSV)</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 text-[11px] uppercase tracking-wider">
                <tr>
                  <th
                    className="py-3 px-4 font-semibold cursor-pointer hover:text-slate-900"
                    onClick={() => toggleSort('crop')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Crop / District</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th className="py-3 px-4 font-semibold">Season / Water</th>
                  <th
                    className="py-3 px-4 font-semibold cursor-pointer hover:text-slate-900"
                    onClick={() => toggleSort('predicted_cost')}
                  >
                    <div className="flex items-center gap-1">
                      <span>Predicted Cost</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                  <th className="py-3 px-4 font-semibold">80% Interval</th>
                  <th className="py-3 px-4 font-semibold">Confidence</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sortedResults.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{r.input.crop}</div>
                      <div className="text-xs text-slate-500">{r.input.district}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      <div>{r.input.season} (Ref: {r.output?.reference_year || 2025})</div>
                      <div className="text-[11px] text-slate-400">{r.input.irrigation_type}</div>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900 font-mono">
                      {r.output ? formatLKR(r.output.predicted_cost) : '—'}
                    </td>
                    <td className="py-3 px-4 text-xs font-mono text-slate-600">
                      {r.output
                        ? `${formatLKR(r.output.interval_low)} – ${formatLKR(r.output.interval_high)}`
                        : '—'}
                    </td>
                    <td className="py-3 px-4">
                      {r.output?.low_confidence ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          Low Confidence
                        </span>
                      ) : r.output ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Confident
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {r.output ? (
                        <span className="text-emerald-600 text-xs font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> OK
                        </span>
                      ) : (
                        <span className="text-rose-600 text-xs font-semibold flex items-center gap-1" title={r.error}>
                          <AlertTriangle className="w-3.5 h-3.5" /> Error
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
