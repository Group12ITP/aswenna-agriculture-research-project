import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { PieChart as PieIcon, Info } from 'lucide-react';
import type { CostBreakdown } from '../../types/api';
import { formatLKR } from '../../lib/format';

interface CostBreakdownChartProps {
  breakdown?: CostBreakdown;
  totalCost: number;
  breakdownSource?: string;
  breakdownAliasNote?: string | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  'Cultivation Labour': '#10b981',    // emerald
  'Fertilizer': '#f59e0b',            // amber
  'Land Preparation': '#3b82f6',      // blue
  'Fuel & Machinery': '#ef4444',      // red
  'Seeds': '#8b5cf6',                 // violet
  'Mechanized Irrigation': '#06b6d4', // cyan
  'Agrochemicals & Other': '#6b7280', // gray
  // Legacy keys fallback
  'Labour': '#10b981',
  'Machinery': '#3b82f6',
  'Fuel': '#ef4444',
  'Irrigation': '#06b6d4',
  'Others': '#6b7280',
};

const CATEGORY_CONFIG: { key: string; legacyKey: string; label: string }[] = [
  { key: 'Cultivation Labour', legacyKey: 'Labour', label: 'Cultivation Labour' },
  { key: 'Fertilizer', legacyKey: 'Fertilizer', label: 'Fertilizer' },
  { key: 'Land Preparation', legacyKey: 'Machinery', label: 'Land Preparation' },
  { key: 'Fuel & Machinery', legacyKey: 'Fuel', label: 'Fuel & Machinery' },
  { key: 'Seeds', legacyKey: 'Seeds', label: 'Seeds' },
  { key: 'Mechanized Irrigation', legacyKey: 'Irrigation', label: 'Mechanized Irrigation' },
  { key: 'Agrochemicals & Other', legacyKey: 'Others', label: 'Agrochemicals & Other' },
];

export const CostBreakdownChart: React.FC<CostBreakdownChartProps> = ({
  breakdown,
  totalCost,
  breakdownSource: _breakdownSource,
  breakdownAliasNote,
}) => {
  if (!breakdown || Object.keys(breakdown).length === 0) {
    return null;
  }

  // Format and order the data
  const data = CATEGORY_CONFIG.map(({ key, legacyKey, label }) => {
    const item = breakdown[key] || breakdown[legacyKey] || { percent: 0, estimated_cost: 0 };
    return {
      name: label,
      percent: item.percent,
      estimated_cost: item.estimated_cost,
      value: item.estimated_cost,
      color: CATEGORY_COLORS[label] || '#94a3b8',
    };
  }).filter((item) => item.percent > 0 || item.estimated_cost > 0);

  return (
    <div className="pt-4 border-t border-slate-100">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <PieIcon className="w-3.5 h-3.5 text-emerald-600" />
          <span>Historical Cost Component Breakdown</span>
        </span>
        <span className="text-[11px] text-slate-400">
          7 Key Agronomic Cost Centres
        </span>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between gap-6 bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
        {/* Donut Chart (200px diameter) with Center Total */}
        <div className="relative w-[200px] h-[200px] shrink-0 flex items-center justify-center">
          <ResponsiveContainer width={200} height={200}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={58}
                outerRadius={86}
                paddingAngle={2}
                dataKey="value"
                strokeWidth={1}
                stroke="#ffffff"
              >
                {data.map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload as typeof data[0];
                    return (
                      <div className="bg-slate-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg border border-slate-700">
                        <div className="flex items-center gap-1.5 font-bold mb-1">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                          <span>{d.name}</span>
                        </div>
                        <div className="font-mono text-emerald-300 font-bold">
                          {formatLKR(d.estimated_cost)}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {d.percent.toFixed(1)}% of total cost
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Centered Donut Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center px-2">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Total</span>
            <span className="text-xs sm:text-sm font-extrabold text-slate-800 font-mono leading-tight">
              {formatLKR(totalCost)}
            </span>
          </div>
        </div>

        {/* Legend on the right */}
        <div className="flex-1 w-full space-y-1.5">
          {data.map((item) => (
            <div
              key={item.name}
              className="flex items-center justify-between text-xs py-1 px-2.5 rounded-lg bg-white/80 border border-slate-200/60 hover:bg-white transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0 shadow-xs"
                  style={{ backgroundColor: item.color }}
                />
                <span className="font-semibold text-slate-700 truncate">
                  {item.name}
                </span>
              </div>
              <div className="font-mono text-right shrink-0 flex items-center gap-2">
                <span className="font-bold text-slate-900">
                  {formatLKR(item.estimated_cost)}
                </span>
                <span className="text-slate-400 text-[11px] min-w-[42px] text-right">
                  ({item.percent.toFixed(1)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footnote and Notes below Donut Chart & Legend */}
      <div className="mt-3 space-y-2">
        {/* Footnote on irrigation accounting */}
        <p className="text-[11px] text-slate-400 leading-normal">
          <span className="font-semibold text-slate-500">Note:</span> In Sri Lanka's Department of Agriculture accounting practice, most irrigation labour (furrow opening, manual watering) is recorded under Cultivation Labour. The Mechanized Irrigation category reflects only pump-based and energy-driven irrigation costs.
        </p>

        {/* Alias / Fallback disclosure note */}
        {breakdownAliasNote && (
          <div className="flex items-start gap-2 p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs shadow-xs">
            <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span className="leading-relaxed font-medium">
              {breakdownAliasNote}
            </span>
          </div>
        )}

        {/* Explanatory footer note */}
        <p className="text-[11px] text-slate-400">
          Component breakdown estimated from historical district-crop ratios (2019–2024). Total is the model's prediction.
        </p>
      </div>
    </div>
  );
};
