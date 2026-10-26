import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import type { TopDriver } from '../../types/api';
import { humanizeFeature, formatPct } from '../../lib/format';

interface SHAPBarChartProps {
  drivers: TopDriver[];
}

export const SHAPBarChart: React.FC<SHAPBarChartProps> = ({ drivers }) => {
  if (!drivers || drivers.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-slate-400">
        No feature attribution drivers available.
      </div>
    );
  }

  // Format data for horizontal bar chart
  const data = drivers.map((d) => ({
    rawName: d.feature,
    name: humanizeFeature(d.feature),
    pct: d.contribution_pct,
    direction: d.direction,
    displayLabel: `${d.direction}${formatPct(d.contribution_pct)}`,
  }));

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Top Cost Attribution Drivers (TreeSHAP)
        </span>
        <div className="flex items-center gap-3 text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            Cost Inflator (+)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            Cost Deflator (-)
          </span>
        </div>
      </div>

      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 5, right: 35, left: 10, bottom: 5 }}
          >
            <XAxis
              type="number"
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tick={{ fontSize: 11, fill: '#64748b' }}
              stroke="#cbd5e1"
            />
            <YAxis
              type="category"
              dataKey="name"
              width={140}
              tick={{ fontSize: 11, fill: '#334155', fontWeight: 500 }}
              stroke="#cbd5e1"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white text-xs p-2.5 rounded-lg shadow-xl border border-slate-700">
                      <div className="font-semibold text-slate-200">{item.name}</div>
                      <div className="mt-1 flex items-center gap-2">
                        <span
                          className={`font-mono font-bold ${
                            item.direction === '+' ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {item.direction === '+' ? 'Increased cost by' : 'Reduced cost by'}{' '}
                          {formatPct(item.pct)}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                        Pipeline feature: {item.rawName}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="pct" radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.direction === '+' ? '#10b981' : '#f43f5e'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[11px] text-slate-400 text-right mt-1">
        Values represent normalized local Shapley feature weights
      </p>
    </div>
  );
};
