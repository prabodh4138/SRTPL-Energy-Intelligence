import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Activity, ShieldCheck, Database, RefreshCw } from 'lucide-react';

interface HeaderProps {
  currentModule: string;
}

export const Header: React.FC<HeaderProps> = ({ currentModule }) => {
  const [health, setHealth] = useState<{ status: string; database?: string }>({ status: 'CHECKING...' });
  const [loading, setLoading] = useState(false);

  const checkStatus = async () => {
    setLoading(true);
    const data = await api.checkHealth();
    setHealth(data);
    setLoading(false);
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">SRTPL Corridors · NHAI</span>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            {currentModule}
          </h1>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Backend API status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
          <Activity className={`w-3.5 h-3.5 ${health.status === 'ONLINE' ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
          <span>FastAPI: <strong className={health.status === 'ONLINE' ? 'text-emerald-400' : 'text-amber-400'}>{health.status}</strong></span>
        </div>

        {/* Supabase status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
          <Database className="w-3.5 h-3.5 text-sky-400" />
          <span>Supabase: <strong className="text-sky-300">{health.database || 'Active'}</strong></span>
        </div>

        <button
          onClick={checkStatus}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
          title="Refresh connection status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>

        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
            SR
          </div>
          <div className="text-left hidden sm:block">
            <div className="text-xs font-medium text-slate-200">SRTPL Auditor</div>
            <div className="text-[10px] text-slate-500">Security & Billing</div>
          </div>
        </div>
      </div>
    </header>
  );
};
