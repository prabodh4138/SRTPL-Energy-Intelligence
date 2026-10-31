import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { AlertTriangle, ShieldCheck, CheckCircle2, History } from 'lucide-react';

export const ValidationView: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchValidation = async () => {
    setLoading(true);
    try {
      const res = await api.getValidation();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchValidation();
  }, []);

  const kpis = data?.kpis || {
    total_open_exceptions: 0,
    critical_holds: 0,
    investigating: 0,
    resolved_today: 0,
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <span className="text-xs font-medium text-slate-400">Total Exceptions</span>
          <div className="text-2xl font-bold text-slate-100 mt-1.5">{kpis.total_open_exceptions}</div>
          <div className="text-[11px] text-slate-500 mt-1">Requiring action</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-rose-900/40">
          <span className="text-xs font-medium text-rose-400">Critical Audit Holds</span>
          <div className="text-2xl font-bold text-rose-300 mt-1.5">{kpis.critical_holds}</div>
          <div className="text-[11px] text-rose-500/80 mt-1">Formula & Provisional</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-amber-900/40">
          <span className="text-xs font-medium text-amber-400">Investigating</span>
          <div className="text-2xl font-bold text-amber-300 mt-1.5">{kpis.investigating}</div>
          <div className="text-[11px] text-amber-500/80 mt-1">Under review</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-emerald-900/40">
          <span className="text-xs font-medium text-emerald-400">Resolved Today</span>
          <div className="text-2xl font-bold text-emerald-300 mt-1.5">{kpis.resolved_today}</div>
          <div className="text-[11px] text-emerald-500/80 mt-1">Approved & cleared</div>
        </div>
      </div>

      {/* Active Exceptions Center */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Active Exceptions & Audit Hold Queue
          </h3>
          <span className="text-xs text-slate-400">{data?.exceptions?.length || 0} open incidents</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
              <tr>
                <th className="px-6 py-3">Exception ID</th>
                <th className="px-6 py-3">Rule / Code</th>
                <th className="px-6 py-3">Asset / Consumer</th>
                <th className="px-6 py-3">Description</th>
                <th className="px-6 py-3">Severity</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Detected At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {(data?.exceptions || []).map((exc: any) => (
                <tr key={exc.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-6 py-3 font-semibold text-amber-400">{exc.id}</td>
                  <td className="px-6 py-3">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-sky-400 text-[10px]">
                      {exc.rule}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-slate-200">{exc.asset_code}</td>
                  <td className="px-6 py-3 text-slate-300 font-sans">{exc.description}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-sans font-bold ${
                        exc.severity === 'HIGH'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {exc.severity}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-sans">
                    <span className="text-slate-300 text-xs">{exc.status}</span>
                  </td>
                  <td className="px-6 py-3 text-slate-400 text-[11px]">{exc.detected_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Events Log */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <History className="w-4 h-4 text-emerald-400" />
            Immutable Audit Trail Log
          </h3>
          <span className="text-xs text-slate-500">PostgreSQL Durable Record</span>
        </div>

        <div className="divide-y divide-slate-800/60 max-h-72 overflow-y-auto">
          {(data?.audit_logs || []).map((ev: any, i: number) => (
            <div key={i} className="px-6 py-3 flex items-center justify-between text-xs hover:bg-slate-800/30 transition">
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono text-[10px]">
                  {ev.event_type}
                </span>
                <span className="text-slate-300 font-sans">{ev.details}</span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">{ev.time}</div>
            </div>
          ))}
          {(!data?.audit_logs || data.audit_logs.length === 0) && (
            <div className="p-6 text-center text-xs text-slate-500">Audit event log is currently clear.</div>
          )}
        </div>
      </div>
    </div>
  );
};
