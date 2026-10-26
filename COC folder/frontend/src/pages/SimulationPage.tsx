import React from 'react';
import { Sliders } from 'lucide-react';

export const SimulationPage: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Module Ownership Banner */}
      <div className="bg-gradient-to-r from-amber-500/10 via-amber-600/5 to-transparent border border-amber-300/80 rounded-2xl p-6 sm:p-7">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-800 border border-amber-300 flex items-center justify-center shrink-0">
              <Sliders className="w-6 h-6 text-amber-700" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 text-[11px] font-bold uppercase tracking-wider mb-1">
                <span>Research Objective 2 (SO2)</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900">
                Interactive What-If Simulation Engine
              </h2>
              <p className="text-xs sm:text-sm text-slate-600 mt-1">
                Owned & Developed by: <span className="font-semibold text-slate-900">K.U.R.C.T Rathnayake</span>
              </p>
            </div>
          </div>
          <span className="self-start sm:self-auto text-xs px-3 py-1 rounded-full bg-amber-100 text-amber-800 font-mono font-bold">
            Status: In Development
          </span>
        </div>
      </div>

      {/* Module Architecture Placeholder Cards */}
      <div className="bg-white rounded-2xl p-8 border border-slate-200/80 text-center max-w-2xl mx-auto shadow-xs">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-4">
          <Sliders className="w-8 h-8 text-slate-500" />
        </div>
        <h3 className="text-base font-bold text-slate-800">
          Simulation Workspace Ready for SO2 Integration
        </h3>
        <p className="text-xs sm:text-sm text-slate-500 mt-2 leading-relaxed">
          This route and layout container have been pre-configured for SO2. Once teammate <b>K.U.R.C.T Rathnayake</b> completes the macroeconomic sensitivity sliders (fertilizer tariff shifts, diesel price hikes, rainfall anomalies), the simulation UI can be mounted directly into this view.
        </p>

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
            <span className="text-xs font-bold text-slate-700 block mb-1">Fertilizer Subsidies</span>
            <p className="text-[11px] text-slate-500 leading-normal">
              Simulate cash transfer vs. in-kind synthetic urea quota policies.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
            <span className="text-xs font-bold text-slate-700 block mb-1">Currency Fluctuations</span>
            <p className="text-[11px] text-slate-500 leading-normal">
              Dynamic stress testing under rapid LKR devaluation cycles.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
            <span className="text-xs font-bold text-slate-700 block mb-1">Mechanization Costs</span>
            <p className="text-[11px] text-slate-500 leading-normal">
              4-wheel tractor hire and diesel transport tariff adjustments.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
