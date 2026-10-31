import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Activity, Database, RefreshCw, Settings, X, Check } from 'lucide-react';

interface HeaderProps {
  currentModule: string;
}

export const Header: React.FC<HeaderProps> = ({ currentModule }) => {
  const [health, setHealth] = useState<{ status: string; database?: string }>({ status: 'CHECKING...' });
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [customUrl, setCustomUrl] = useState('');

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

  const handleOpenConfig = () => {
    setCustomUrl(api.getApiBase().replace(/\/api$/, ''));
    setShowConfig(true);
  };

  const handleSaveConfig = () => {
    api.setApiBase(customUrl.trim());
    setShowConfig(false);
    checkStatus();
  };

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
        <button
          onClick={handleOpenConfig}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 hover:border-slate-600 text-xs text-slate-300 transition cursor-pointer"
          title="Click to configure backend API URL"
        >
          <Activity className={`w-3.5 h-3.5 ${health.status === 'ONLINE' ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
          <span>FastAPI: <strong className={health.status === 'ONLINE' ? 'text-emerald-400' : 'text-amber-400'}>{health.status}</strong></span>
          <Settings className="w-3 h-3 text-slate-500" />
        </button>

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

      {/* Backend API Configuration Modal */}
      {showConfig && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Settings className="w-4 h-4 text-emerald-400" />
                Backend API Endpoint Configuration
              </h3>
              <button
                onClick={() => setShowConfig(false)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-4 space-y-3">
              <p className="text-xs text-slate-400 leading-relaxed">
                Configure your deployed FastAPI backend URL. By default, it points to the Render service or local server:
              </p>
              <input
                type="text"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                placeholder="https://srtpl-energy-backend.onrender.com"
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span>Default: <code className="text-emerald-400 font-mono">https://srtpl-energy-backend.onrender.com</code></span>
                <button
                  type="button"
                  onClick={() => setCustomUrl('https://srtpl-energy-backend.onrender.com')}
                  className="text-emerald-400 hover:underline"
                >
                  Reset Render
                </button>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowConfig(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveConfig}
                className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" />
                Save & Connect
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
