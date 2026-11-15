import React from 'react';
import {
  LayoutDashboard,
  Zap,
  Layers,
  UploadCloud,
  ShieldAlert,
  Archive,
  FileCheck2,
  FileSpreadsheet,
  AlertTriangle,
  X,
  ShieldCheck,
} from 'lucide-react';

export type ModuleKey =
  | 'energy-overview'
  | 'readings'
  | 'asset-master'
  | 'energy-import'
  | 'exceptions'
  | 'energy-exports'
  | 'forensic-analytics'
  | 'bills'
  | 'juno'
  | 'reports'
  | 'dashboard'
  | 'validation';

interface SidebarProps {
  activeModule: ModuleKey;
  onSelectModule: (m: ModuleKey) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const ENERGY_MODULES: { id: ModuleKey; label: string; number: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'energy-overview', label: 'Energy Overview', number: '1', icon: LayoutDashboard },
  { id: 'readings', label: 'Readings & Monitoring', number: '2', icon: Zap },
  { id: 'asset-master', label: 'Asset Master Inventory', number: '3', icon: Layers },
  { id: 'energy-import', label: 'Energy Import Wizard', number: '4', icon: UploadCloud },
  { id: 'exceptions', label: 'Exception Center', number: '5', icon: ShieldAlert },
  { id: 'energy-exports', label: 'Exports & Backup', number: '6', icon: Archive },
  { id: 'forensic-analytics', label: 'Forensic Audit & Analytics', number: '7', icon: AlertTriangle },
];

export const PROTECTED_MODULES: { id: ModuleKey; label: string; tag: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'bills', label: 'Bill Reconciliation', tag: 'Protected', icon: FileCheck2 },
  { id: 'juno', label: 'Juno Import Centre', tag: 'Protected', icon: UploadCloud },
  { id: 'reports', label: 'Reports & Studio', tag: 'Protected', icon: FileSpreadsheet },
  { id: 'dashboard', label: 'Reconciliation Dashboard', tag: 'Preserved', icon: LayoutDashboard },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeModule,
  onSelectModule,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const handleItemClick = (id: ModuleKey) => {
    onSelectModule(id);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const navContent = (
    <div className="flex flex-col h-full">
      {/* Brand Header */}
      <div className="h-16 px-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-sky-500 flex items-center justify-center text-white shadow-lg shadow-emerald-950/40">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <span className="font-extrabold text-sm text-slate-100 tracking-wide block">SRTPL ENERGY</span>
            <span className="block text-[10px] text-emerald-400 font-bold tracking-wider uppercase">Command Center</span>
          </div>
        </div>

        {/* Mobile Close Button */}
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Modules */}
      <div className="p-3.5 flex-1 space-y-4 overflow-y-auto">
        {/* Section 1: In-Scope Energy Command Center */}
        <div>
          <div className="px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase text-emerald-400/90 flex items-center justify-between">
            <span>Energy Command Center</span>
            <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-[9px] font-mono border border-emerald-500/20">
              Active Scope
            </span>
          </div>

          <div className="space-y-1 mt-1">
            {ENERGY_MODULES.map((item) => {
              const Icon = item.icon;
              const isActive = activeModule === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleItemClick(item.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left font-medium text-xs transition duration-150 ${
                    isActive
                      ? 'bg-gradient-to-r from-emerald-600/25 to-sky-600/15 text-emerald-400 border border-emerald-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-lg flex items-center justify-center text-[10px] font-bold ${
                      isActive ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.number}
                  </div>
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                  <span className="flex-1 truncate">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 2: Preserved Protected Modules (Scope Freeze) */}
        <div className="pt-2 border-t border-slate-800/80">
          <div className="px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase text-slate-400 flex items-center justify-between">
            <span>Preserved Modules</span>
            <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 text-[9px] font-mono border border-slate-700">
              Frozen
            </span>
          </div>

          <div className="space-y-1 mt-1">
            {PROTECTED_MODULES.map((item) => {
              const Icon = item.icon;
              const isActive = activeModule === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleItemClick(item.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left font-medium text-xs transition duration-150 ${
                    isActive
                      ? 'bg-slate-800 text-sky-400 border border-sky-500/30'
                      : 'text-slate-400 hover:text-slate-300 hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                  <span className="flex-1 truncate text-[11px]">{item.label}</span>
                  <span className="text-[9px] font-mono text-slate-500">{item.tag}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Corridor Plazas Footer */}
      <div className="p-3.5 border-t border-slate-800/80 bg-slate-950/40">
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-300">Corridor Plazas</span>
            <span className="text-[9px] font-mono text-slate-400">Trusted Access</span>
          </div>
          <div className="flex gap-1.5 mt-1.5 text-[10px] text-slate-400">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono font-bold">TP01</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 font-mono font-bold">TP02</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-400 font-mono font-bold">TP03</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-2 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>Single Designated User Console</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Static Sidebar */}
      <aside className="hidden lg:flex lg:flex-col w-64 bg-slate-900 border-r border-slate-800 shrink-0 min-h-screen sticky top-0 h-screen overflow-hidden">
        {navContent}
      </aside>

      {/* Mobile Slide-Out Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <aside className="relative w-72 max-w-[85vw] bg-slate-900 border-r border-slate-800 z-50 flex flex-col h-full shadow-2xl animate-in slide-in-from-left duration-200">
            {navContent}
          </aside>
        </div>
      )}
    </>
  );
};
