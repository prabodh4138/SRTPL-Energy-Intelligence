import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Activity, Database, RefreshCw, Settings, X, Check, Menu } from 'lucide-react';

interface HeaderProps {
  currentModule: string;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentModule, onToggleMobileMenu }) => {
  const [health, setHealth] = useState<{ status: string; database?: string }>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('SRTPL_LAST_HEALTH');
        if (saved) return JSON.parse(saved);
      } catch {
        // ignore
      }
    }
    return { status: 'ONLINE', database: 'Active' };
  });
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [customUrl, setCustomUrl] = useState('');

  const checkStatus = async () => {
    setLoading(true);
    try {
      const data = await api.checkHealth(4000);
      setHealth(data);
      if (data.status === 'ONLINE' && typeof window !== 'undefined') {
        localStorage.setItem('SRTPL_LAST_HEALTH', JSON.stringify(data));
      }
    } catch {
      setHealth({ status: 'OFFLINE', database: 'Unreachable' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 20000);
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
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-3 sm:px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-2 sm:gap-4 min-w-0">
        {/* Mobile Hamburger Menu Button */}
        {onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            className="lg:hidden p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition shrink-0"
            aria-label="Toggle navigation drawer"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="min-w-0">
          <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-emerald-400 block truncate">
            SRTPL Corridors · NHAI
          </span>
          <h1 className="text-xs sm:text-base md:text-lg font-bold text-slate-100 truncate">
            {currentModule}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* Backend API status */}
        <button
          onClick={handleOpenConfig}
          className="flex items-center gap-1.5 px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-full bg-slate-800 border border-slate-700 hover:border-slate-600 text-xs text-slate-300 transition cursor-pointer"
          title="Click to configure backend API URL"
        >
          <Activity
            className={`w-3.5 h-3.5 ${
              health.status === 'ONLINE'
                ? 'text-emerald-400 animate-pulse'
                : health.status.includes('WAKING')
                ? 'text-amber-300 animate-spin'
                : health.status === 'OFFLINE'
                ? 'text-rose-400'
                : 'text-amber-400'
            }`}
          />
          <span className="hidden sm:inline">
            FastAPI:{' '}
            <strong
              className={
                health.status === 'ONLINE'
                  ? 'text-emerald-400'
                  : health.status.includes('WAKING')
                  ? 'text-amber-300'
                  : health.status === 'OFFLINE'
                  ? 'text-rose-400'
                  : 'text-amber-400'
              }
            >
              {health.status}
            </strong>
          </span>
          <Settings className="w-3 h-3 text-slate-500 hidden sm:inline" />
        </button>

        {/* Supabase status (hidden on extra small screens, visible on md) */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
          <Database className="w-3.5 h-3.5 text-sky-400" />
          <span>
            Supabase: <strong className="text-sky-300">{health.database || 'Active'}</strong>
          </span>
        </div>

        {/* Refresh Connection Button */}
        <button
          onClick={checkStatus}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
          title="Refresh connection status"
        >
          <RefreshCw className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>

        {/* User Avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
            SR
          </div>
          <div className="text-left hidden xl:block">
            <div className="text-xs font-medium text-slate-200">SRTPL Auditor</div>
            <div className="text-[10px] text-slate-500">Superuser Access</div>
          </div>
        </div>
      </div>

      {/* Backend API Configuration Modal */}
      {showConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Settings className="w-4 h-4 text-emerald-400" />
                Backend Connection Settings
              </h3>
              <button
                onClick={() => setShowConfig(false)}
                className="text-slate-500 hover:text-slate-300 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1.5">
                  FastAPI Server URL
                </label>
                <input
                  type="text"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>

              <div className="text-[11px] text-slate-400 space-y-1 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <p>
                  <strong>Local Dev:</strong>{' '}
                  <button
                    type="button"
                    onClick={() => setCustomUrl('http://localhost:8000')}
                    className="text-sky-400 hover:underline font-mono"
                  >
                    http://localhost:8000
                  </button>
                </p>
                <p>
                  <strong>Local IP (Mobile Testing):</strong>{' '}
                  <span className="text-slate-300 font-mono">http://&lt;your-pc-ip&gt;:8000</span>
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConfig(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveConfig}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow"
              >
                <Check className="w-3.5 h-3.5" />
                Apply & Test
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
