import React, { useState } from 'react';
import { Sidebar, ModuleKey, ENERGY_MODULES, PROTECTED_MODULES } from './components/Sidebar';
import { Header } from './components/Header';

// In-Scope Energy Command Center Modules
import { EnergyOverviewView } from './pages/EnergyOverviewView';
import { EnergyReadingsView } from './pages/EnergyReadingsView';
import { AssetMasterView } from './pages/AssetMasterView';
import { EnergyImportView } from './pages/EnergyImportView';
import { ExceptionManagementView } from './pages/ExceptionManagementView';
import { EnergyExportsBackupView } from './pages/EnergyExportsBackupView';

// Preserved & Protected Modules (Scope Freeze)
import { DashboardView } from './pages/DashboardView';
import { ReadingView } from './pages/ReadingView';
import { ValidationView } from './pages/ValidationView';
import { JunoImportView } from './pages/JunoImportView';
import { BillReconciliationView } from './pages/BillReconciliationView';
import { ReportsView } from './pages/ReportsView';

import {
  LayoutDashboard,
  Zap,
  Layers,
  UploadCloud,
  ShieldAlert,
  Archive,
  FileCheck2,
  FileSpreadsheet,
  Menu,
} from 'lucide-react';

export function App() {
  const [activeModule, setActiveModule] = useState<ModuleKey>('energy-overview');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const allModules = [...ENERGY_MODULES, ...PROTECTED_MODULES];
  const currentModuleTitle =
    allModules.find((m) => m.id === activeModule)?.label || 'Energy Command Center';

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950 font-sans">
      {/* Sidebar (Desktop Static + Mobile Drawer) */}
      <Sidebar
        activeModule={activeModule}
        onSelectModule={setActiveModule}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          currentModule={`SRTPL · ${currentModuleTitle}`}
          onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />

        {/* Responsive Content Container */}
        <main className="flex-1 p-3.5 sm:p-5 md:p-6 lg:p-8 max-w-7xl mx-auto w-full pb-24 lg:pb-8">
          {/* Energy Command Center Modules (Active Scope) */}
          {activeModule === 'energy-overview' && (
            <EnergyOverviewView onNavigateToModule={(mod) => setActiveModule(mod as ModuleKey)} />
          )}
          {activeModule === 'readings' && <EnergyReadingsView />}
          {activeModule === 'asset-master' && <AssetMasterView />}
          {activeModule === 'energy-import' && <EnergyImportView />}
          {activeModule === 'exceptions' && <ExceptionManagementView />}
          {activeModule === 'energy-exports' && <EnergyExportsBackupView />}

          {/* Protected Modules (Preserved & Accessible) */}
          {activeModule === 'bills' && <BillReconciliationView />}
          {activeModule === 'juno' && <JunoImportView />}
          {activeModule === 'reports' && <ReportsView />}
          {activeModule === 'dashboard' && <DashboardView />}
          {activeModule === 'validation' && <ValidationView />}
        </main>
      </div>

      {/* Mobile Fixed Bottom Navigation Bar (Visible on screens < lg) */}
      <nav
        aria-label="Mobile Navigation"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur-md border-t border-slate-800 px-3 py-2 flex items-center justify-around shadow-2xl safe-area-bottom"
      >
        <button
          onClick={() => setActiveModule('energy-overview')}
          className={`flex flex-col items-center gap-1 py-1 px-2 rounded-xl text-[10px] font-semibold transition ${
            activeModule === 'energy-overview'
              ? 'text-emerald-400 font-bold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <div
            className={`p-1 rounded-lg ${
              activeModule === 'energy-overview' ? 'bg-emerald-500/20 text-emerald-400' : ''
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
          </div>
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveModule('readings')}
          className={`flex flex-col items-center gap-1 py-1 px-2 rounded-xl text-[10px] font-semibold transition ${
            activeModule === 'readings'
              ? 'text-emerald-400 font-bold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <div
            className={`p-1 rounded-lg ${
              activeModule === 'readings' ? 'bg-emerald-500/20 text-emerald-400' : ''
            }`}
          >
            <Zap className="w-4 h-4" />
          </div>
          <span>Readings</span>
        </button>

        <button
          onClick={() => setActiveModule('exceptions')}
          className={`flex flex-col items-center gap-1 py-1 px-2 rounded-xl text-[10px] font-semibold transition ${
            activeModule === 'exceptions'
              ? 'text-amber-400 font-bold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <div
            className={`p-1 rounded-lg ${
              activeModule === 'exceptions' ? 'bg-amber-500/20 text-amber-400' : ''
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
          </div>
          <span>Exceptions</span>
        </button>

        <button
          onClick={() => setActiveModule('bills')}
          className={`flex flex-col items-center gap-1 py-1 px-2 rounded-xl text-[10px] font-semibold transition ${
            activeModule === 'bills'
              ? 'text-sky-400 font-bold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <div
            className={`p-1 rounded-lg ${
              activeModule === 'bills' ? 'bg-sky-500/20 text-sky-400' : ''
            }`}
          >
            <FileCheck2 className="w-4 h-4" />
          </div>
          <span>Bills</span>
        </button>

        <button
          onClick={() => setIsMobileMenuOpen(true)}
          className="flex flex-col items-center gap-1 py-1 px-2 rounded-xl text-[10px] font-semibold text-slate-400 hover:text-slate-200 transition"
        >
          <div className="p-1 rounded-lg hover:bg-slate-800">
            <Menu className="w-4 h-4" />
          </div>
          <span>All Modules</span>
        </button>
      </nav>
    </div>
  );
}

export default App;
