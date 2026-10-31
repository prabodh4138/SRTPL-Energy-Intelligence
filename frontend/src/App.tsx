import React, { useState } from 'react';
import { Sidebar, ModuleKey, MODULE_LIST } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardView } from './pages/DashboardView';
import { ReadingView } from './pages/ReadingView';
import { ValidationView } from './pages/ValidationView';
import { JunoImportView } from './pages/JunoImportView';
import { BillReconciliationView } from './pages/BillReconciliationView';
import { ReportsView } from './pages/ReportsView';

export function App() {
  const [activeModule, setActiveModule] = useState<ModuleKey>('dashboard');

  const currentModuleTitle =
    MODULE_LIST.find((m) => m.id === activeModule)?.label || 'Dashboard';

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950 font-sans">
      {/* 6-Module Sidebar */}
      <Sidebar activeModule={activeModule} onSelectModule={setActiveModule} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header currentModule={`${activeModule.toUpperCase()} · ${currentModuleTitle}`} />

        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {activeModule === 'dashboard' && <DashboardView />}
          {activeModule === 'readings' && <ReadingView />}
          {activeModule === 'validation' && <ValidationView />}
          {activeModule === 'juno' && <JunoImportView />}
          {activeModule === 'bills' && <BillReconciliationView />}
          {activeModule === 'reports' && <ReportsView />}
        </main>
      </div>
    </div>
  );
}

export default App;
