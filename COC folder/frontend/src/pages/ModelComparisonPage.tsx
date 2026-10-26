import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import {
  BarChart3,
  Info,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Award,
  AlertCircle,
  Lightbulb,
} from 'lucide-react';
import { useModelEvaluation } from '../hooks/useModelEvaluation';
import type { ModelEvaluationRow } from '../types/api';

type SortField =
  | 'Model_Name'
  | 'Model_Family'
  | 'LOSO_R2'
  | 'LOSO_MAE'
  | 'GKF_R2'
  | 'Training_Time_Seconds'
  | 'Inference_Time_ms';

type SortDirection = 'asc' | 'desc';

export const ModelComparisonPage: React.FC = () => {
  const { data, isLoading, isError, error } = useModelEvaluation();
  const [sortField, setSortField] = useState<SortField>('LOSO_R2');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const rows = data?.rows || [];

  // Helper to map long model names to clean abbreviations for X-axis ticks
  const getShortName = (name: string): string => {
    switch (name) {
      case 'LinearRegression':
        return 'Linear Reg';
      case 'DecisionTreeRegressor':
        return 'Decision Tree';
      case 'RandomForestRegressor':
        return 'Random Forest';
      case 'GradientBoostingRegressor':
        return 'Gradient Boost';
      case 'MLPRegressor':
        return 'MLP';
      default:
        return name;
    }
  };

  // Find best LOSO R² in dataset
  const bestR2 = useMemo(() => {
    if (rows.length === 0) return null;
    return Math.max(...rows.map((r) => r.LOSO_R2));
  }, [rows]);

  // Chart data sorted by LOSO R² descending
  const chartData = useMemo(() => {
    return [...rows]
      .sort((a, b) => b.LOSO_R2 - a.LOSO_R2)
      .map((r) => ({
        ...r,
        displayName: getShortName(r.Model_Name),
      }));
  }, [rows]);

  // Table sorting handler
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection(field === 'Model_Name' || field === 'Model_Family' ? 'asc' : 'desc');
    }
  };

  // Sorted rows for the table
  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (typeof valA === 'string' && typeof valB === 'string') {
        const comp = valA.localeCompare(valB);
        return sortDirection === 'asc' ? comp : -comp;
      }

      valA = Number(valA);
      valB = Number(valB);
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    });
  }, [rows, sortField, sortDirection]);

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 inline ml-1" />;
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="w-3.5 h-3.5 text-emerald-600 inline ml-1" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-emerald-600 inline ml-1" />
    );
  };

  // Custom Recharts Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload as ModelEvaluationRow & { displayName: string };
      const isDeep = item.Model_Family.toLowerCase() === 'deep';
      return (
        <div className="bg-slate-900 text-white p-3.5 rounded-xl shadow-xl border border-slate-800 text-xs space-y-1.5 min-w-[210px] animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-1.5">
            <span className="font-bold text-sm text-white">{item.Model_Name}</span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                isDeep
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}
            >
              {item.Model_Family}
            </span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>LOSO R²:</span>
            <span className="font-mono font-bold text-white text-xs">{item.LOSO_R2.toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>LOSO MAE:</span>
            <span className="font-mono font-bold text-emerald-400 text-xs">
              Rs {Math.round(item.LOSO_MAE).toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between items-center text-slate-300">
            <span>GKF R²:</span>
            <span className="font-mono text-slate-300 text-xs">{item.GKF_R2.toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px] pt-1 border-t border-slate-800">
            <span>Inference Time:</span>
            <span className="font-mono text-slate-300">{item.Inference_Time_ms.toFixed(2)} ms</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-950 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden border border-slate-800">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Empirical Benchmark (SO1)</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            Model Evaluation & Architecture Comparison
          </h2>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Rigorous cross-validation benchmark of 8 machine learning models (4 classical shallow vs. 4 deep/neural architectures) across 641 historical cultivation seasons under GroupKFold (Crop-stratified) and Leave-One-Season-Out (LOSO) temporal protocols.
          </p>
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading && (
        <div className="bg-white rounded-2xl p-12 border border-slate-200/80 shadow-xs text-center space-y-3">
          <div className="w-10 h-10 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-600 font-medium">Loading model evaluation metrics...</p>
        </div>
      )}

      {isError && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-sm text-rose-900">Failed to load model comparison</h4>
            <p className="text-xs text-rose-700 mt-1">{(error as any)?.message || 'An unexpected error occurred.'}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && rows.length === 0 && (
        <div className="bg-white rounded-2xl p-12 border border-slate-200/80 shadow-xs text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-2">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Model comparison data not available</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Model comparison data not available. Run the training pipeline to generate model_evaluation_full.csv.
          </p>
        </div>
      )}

      {/* Main Content */}
      {!isLoading && !isError && rows.length > 0 && (
        <>
          {/* Section 1: Bar Chart */}
          <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/90 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-emerald-600" />
                  Leave-One-Season-Out (LOSO) R² Benchmark
                </h3>
                <p className="text-xs text-slate-500">
                  Performance when predicting an entirely unseen historical cultivation year (temporal generalization). Sorted descending.
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#3b82f6]" />
                  <span className="font-medium text-slate-700">Shallow (#3b82f6)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-[#f59e0b]" />
                  <span className="font-medium text-slate-700">Deep (#f59e0b)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 border-t-2 border-dashed border-red-500" />
                  <span className="font-medium text-red-600">Target (0.80)</span>
                </div>
              </div>
            </div>

            {/* Recharts Bar Chart */}
            <div className="w-full pt-2">
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={chartData} margin={{ top: 25, right: 30, left: 0, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="displayName"
                    tick={{ fontSize: 11, fill: '#475569', fontWeight: 500 }}
                    interval={0}
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                  />
                  <YAxis
                    domain={[0.55, 1.0]}
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    tickFormatter={(v) => v.toFixed(2)}
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                    label={{
                      value: 'LOSO R² Score',
                      angle: -90,
                      position: 'insideLeft',
                      fontSize: 11,
                      fill: '#64748b',
                      offset: 15,
                    }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine
                    y={0.8}
                    stroke="#ef4444"
                    strokeDasharray="4 4"
                    strokeWidth={2}
                    label={{
                      value: 'Proposal Target R² = 0.80',
                      fill: '#ef4444',
                      position: 'top',
                      fontSize: 11,
                      fontWeight: 700,
                    }}
                  />
                  <Bar dataKey="LOSO_R2" radius={[6, 6, 0, 0]} maxBarSize={56}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.Model_Family.toLowerCase() === 'deep' ? '#f59e0b' : '#3b82f6'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Section 2: Detailed Sortable Table */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
              <div>
                <h3 className="text-base sm:text-lg font-bold text-slate-900">
                  Comprehensive Model Evaluation Metrics
                </h3>
                <p className="text-xs text-slate-500">
                  Click column headers to sort. The highest performing model under temporal validation is highlighted.
                </p>
              </div>
              <span className="text-xs text-slate-500 font-mono bg-white px-2.5 py-1 rounded-lg border border-slate-200 self-start sm:self-auto">
                {rows.length} Models Benchmarked
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 text-[11px] uppercase tracking-wider font-semibold select-none">
                  <tr>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group"
                      onClick={() => handleSort('Model_Name')}
                    >
                      <div className="flex items-center">
                        <span>Model</span>
                        {renderSortIcon('Model_Name')}
                      </div>
                    </th>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group"
                      onClick={() => handleSort('Model_Family')}
                    >
                      <div className="flex items-center">
                        <span>Family</span>
                        {renderSortIcon('Model_Family')}
                      </div>
                    </th>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group text-right"
                      onClick={() => handleSort('LOSO_R2')}
                    >
                      <div className="flex items-center justify-end">
                        <span>LOSO R²</span>
                        {renderSortIcon('LOSO_R2')}
                      </div>
                    </th>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group text-right"
                      onClick={() => handleSort('LOSO_MAE')}
                    >
                      <div className="flex items-center justify-end">
                        <span>LOSO MAE (Rs)</span>
                        {renderSortIcon('LOSO_MAE')}
                      </div>
                    </th>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group text-right"
                      onClick={() => handleSort('GKF_R2')}
                    >
                      <div className="flex items-center justify-end">
                        <span>GKF R²</span>
                        {renderSortIcon('GKF_R2')}
                      </div>
                    </th>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group text-right"
                      onClick={() => handleSort('Training_Time_Seconds')}
                    >
                      <div className="flex items-center justify-end">
                        <span>Training Time (s)</span>
                        {renderSortIcon('Training_Time_Seconds')}
                      </div>
                    </th>
                    <th
                      className="py-3.5 px-4 cursor-pointer hover:bg-slate-100/80 transition-colors group text-right"
                      onClick={() => handleSort('Inference_Time_ms')}
                    >
                      <div className="flex items-center justify-end">
                        <span>Inference Time (ms)</span>
                        {renderSortIcon('Inference_Time_ms')}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sortedRows.map((row) => {
                    const isBest = bestR2 !== null && row.LOSO_R2 === bestR2;
                    const isDeep = row.Model_Family.toLowerCase() === 'deep';
                    const isProduction = row.Model_Name === 'GradientBoostingRegressor';

                    return (
                      <tr
                        key={row.Model_Name}
                        className={`transition-colors ${
                          isBest
                            ? 'bg-emerald-50/70 hover:bg-emerald-100/60 font-medium'
                            : 'hover:bg-slate-50/70'
                        }`}
                      >
                        {/* Model */}
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-900">{row.Model_Name}</span>
                            {isBest && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                                <Award className="w-2.5 h-2.5 text-emerald-700" />
                                Best R²
                              </span>
                            )}
                            {isProduction && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">
                                Production
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Family */}
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                              isDeep
                                ? 'bg-amber-100/80 text-amber-800 border border-amber-300/80'
                                : 'bg-blue-100/80 text-blue-800 border border-blue-300/80'
                            }`}
                          >
                            {row.Model_Family}
                          </span>
                        </td>

                        {/* LOSO R² */}
                        <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                          {row.LOSO_R2.toFixed(4)}
                        </td>

                        {/* LOSO MAE */}
                        <td className="py-3 px-4 text-right font-mono text-slate-700">
                          Rs {Math.round(row.LOSO_MAE).toLocaleString()}
                        </td>

                        {/* GKF R² */}
                        <td className="py-3 px-4 text-right font-mono text-slate-700">
                          {row.GKF_R2.toFixed(4)}
                        </td>

                        {/* Training Time */}
                        <td className="py-3 px-4 text-right font-mono text-slate-600">
                          {row.Training_Time_Seconds.toFixed(2)}s
                        </td>

                        {/* Inference Time */}
                        <td className="py-3 px-4 text-right font-mono text-slate-600">
                          {row.Inference_Time_ms.toFixed(2)} ms
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Callout Card (Amber background with info icon) */}
          <div className="bg-amber-50 border border-amber-200/90 rounded-2xl p-5 sm:p-6 text-amber-950 shadow-xs flex items-start gap-3.5">
            <div className="w-8 h-8 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0 shadow-2xs mt-0.5">
              <Info className="w-5 h-5 text-amber-700" />
            </div>
            <div className="space-y-1 text-xs sm:text-sm leading-relaxed">
              <span className="font-bold text-amber-900 text-sm block">
                Key Finding:
              </span>
              <p className="text-amber-900">
                At 641 rows across 23 crops, classical tree ensembles (CatBoost 0.897, GradientBoosting 0.891, XGBoost 0.890) matched or exceeded neural architectures (MLP 0.868, TabNet 0.832). This is consistent with tabular deep learning literature (Shwartz-Ziv & Armon, 2022). Production model retained: GradientBoostingRegressor — best accuracy-per-millisecond tradeoff.
              </p>
            </div>
          </div>

          {/* Section 4: Small Card Explaining the Why */}
          <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/90 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-slate-900">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              <h4 className="text-sm sm:text-base font-bold text-slate-900">
                Architectural Analysis: Why Classical Ensembles Dominated
              </h4>
            </div>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-700">
              <li className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0 mt-1.5" />
                <span>
                  <strong>Native categorical partitioning:</strong> Tree models natively handle categorical features without embedding layers.
                </span>
              </li>
              <li className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0 mt-1.5" />
                <span>
                  <strong>Sample efficiency:</strong> Small N (641) favors low-variance models over high-capacity networks.
                </span>
              </li>
              <li className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0 mt-1.5" />
                <span>
                  <strong>Attention overhead:</strong> TabNet's GKF R² collapsed to −940 — attention mechanisms need substantially more data.
                </span>
              </li>
              <li className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0 mt-1.5" />
                <span>
                  <strong>Operational latency:</strong> Inference time matters for real-time officer use: GB = 0.01ms vs TabNet = 15ms (1500× difference).
                </span>
              </li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
};
