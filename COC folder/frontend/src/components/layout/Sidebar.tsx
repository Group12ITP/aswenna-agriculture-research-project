import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  Calculator,
  Upload,
  Sliders,
  Wallet,
  MessageSquare,
  Settings,
  Sprout,
  X,
  ExternalLink,
  BarChart3,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  label?: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Dashboard', label: 'Dashboard', path: '/', icon: Home },
  { name: 'Predict Cost', label: 'Predict Cost', path: '/predict', icon: Calculator, badge: 'SO1' },
  { name: 'Model Comparison', label: 'Model Comparison', path: '/model-comparison', icon: BarChart3 },
  { name: 'Batch Predict', label: 'Batch Predict', path: '/batch', icon: Upload },
  { name: 'Simulation', label: 'Simulation', path: '/simulation', icon: Sliders, tag: 'SO2' },
  { name: 'Expense Tracker', label: 'Expense Tracker', path: '/expenses', icon: Wallet, tag: 'SO3' },
  { name: 'Chat Assistant', label: 'Chat Assistant', path: '/chat', icon: MessageSquare, tag: 'LLM' },
  { name: 'Settings', label: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-slate-100 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } border-r border-slate-800 shadow-xl lg:shadow-none`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-inner">
              <Sprout className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white block">
                AgriCost <span className="text-emerald-400 font-extrabold">AI</span>
              </span>
              <span className="text-[11px] font-medium text-slate-400 block tracking-wide uppercase">
                Sri Lanka COC • SO1
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Main Modules
          </div>

          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                    isActive
                      ? 'bg-emerald-600 text-white font-semibold shadow-md shadow-emerald-900/30'
                      : 'text-slate-300 hover:bg-slate-800/70 hover:text-white'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-emerald-400'
                        }`}
                      />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-emerald-400/20 text-emerald-300 border border-emerald-400/30">
                        {item.badge}
                      </span>
                    )}
                    {item.tag && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-mono text-slate-400 bg-slate-800 border border-slate-700/60">
                        {item.tag}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer info card */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/30">
          <div className="bg-slate-800/60 rounded-xl p-3 border border-slate-700/50">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-slate-300">DOA Survey Engine</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 font-mono">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Trained on 11-year DOA cost of cultivation data (2014–2025).
            </p>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="mt-2.5 inline-flex items-center gap-1.5 text-[11px] text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
            >
              <span>Swagger API Docs</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </aside>
    </>
  );
};
