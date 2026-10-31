import React from 'react';
import {
  LayoutDashboard,
  Zap,
  AlertTriangle,
  UploadCloud,
  FileCheck2,
  FileSpreadsheet,
  Layers,
} from 'lucide-react';

export type ModuleKey =
  | 'dashboard'
  | 'readings'
  | 'validation'
  | 'juno'
  | 'bills'
  | 'reports';

interface SidebarProps {
  activeModule: ModuleKey;
  onSelectModule: (m: ModuleKey) => void;
}

export const MODULE_LIST: { id: ModuleKey; label: string; number: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'dashboard', label: 'Dashboard', number: '1', icon: LayoutDashboard },
  { id: 'readings', label: 'Reading Section', number: '2', icon: Zap },
  { id: 'validation', label: 'Validation & Exceptions', number: '3', icon: AlertTriangle },
  { id: 'juno', label: 'Juno Import Centre', number: '4', icon: UploadCloud },
  { id: 'bills', label: 'Bill Reconciliation', number: '5', icon: FileCheck2 },
  { id: 'reports', label: 'Reports', number: '6', icon: FileSpreadsheet },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeModule, onSelectModule }) => {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="h-16 px-6 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-sky-500 flex items-center justify-center text-white shadow-lg shadow-emerald-950/40">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <span className="font-extrabold text-sm text-slate-100 tracking-wide">SRTPL ENERGY</span>
          <span className="block text-[10px] text-emerald-400 font-semibold tracking-wider uppercase">Intelligence v2</span>
        </div>
      </div>

      {/* Navigation Modules */}
      <div className="p-4 flex-1 space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider uppercase text-slate-500">
          Core Workflows
        </div>

        {MODULE_LIST.map((item) => {
          const Icon = item.icon;
          const isActive = activeModule === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectModule(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-left font-medium text-xs transition duration-150 ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-600/20 to-sky-600/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-lg flex items-center justify-center text-[11px] font-bold ${
                  isActive ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'
                }`}
              >
                {item.number}
              </div>
              <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
              <span className="flex-1 truncate">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Corridor Footer Info */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
          <div className="text-[11px] font-semibold text-slate-300">Corridor Toll Plazas</div>
          <div className="flex gap-2 mt-1.5 text-[10px] text-slate-400">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono">TP01</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 font-mono">TP02</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-400 font-mono">TP03</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-2">60 Consumers (3 HT / 57 LT)</div>
        </div>
      </div>
    </aside>
  );
};
