import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { DashboardKPIs, PlazaSummary, TrendData } from '../types';
import {
  FileText,
  AlertCircle,
  CheckCircle2,
  ShieldBan,
  IndianRupee,
  Clock,
  TrendingUp,
  Building2,
  Filter,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';

export const DashboardView: React.FC = () => {
  const [data, setData] = useState<{
    kpis: DashboardKPIs;
    plazas: PlazaSummary[];
    trend: TrendData[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [plazaFilter, setPlazaFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboard(plazaFilter, 'ALL', typeFilter);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [plazaFilter, typeFilter]);

  const kpis = data?.kpis || {
    total_bills_found: 0,
    held_for_review: 0,
    verified_posted: 0,
    duplicates_rejected: 0,
    total_bill_amount: 0,
    total_paid_amount: 0,
    total_outstanding: 0,
  };

  const formatMoney = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Filter className="w-4 h-4 text-emerald-400" />
          <span>GLOBAL RECONCILIATION FILTERS</span>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Plaza Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-2.5 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400">Plaza:</span>
            <select
              value={plazaFilter}
              onChange={(e) => setPlazaFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-medium cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Plazas</option>
              <option value="TP01" className="bg-slate-800">TP01 · Km 24+500</option>
              <option value="TP02" className="bg-slate-800">TP02 · Km 68+200</option>
              <option value="TP03" className="bg-slate-800">TP03 · Km 112+800</option>
            </select>
          </div>

          {/* Bill Type Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-2.5 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400">Feeder Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-medium cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Feeders (60)</option>
              <option value="HT" className="bg-slate-800">HT Feeders (3)</option>
              <option value="LT" className="bg-slate-800">LT Lighting (57)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 6 Key Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Bills Found */}
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Bills Found</span>
            <div className="p-2 rounded-xl bg-slate-800 text-slate-300">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">{kpis.total_bills_found}</div>
          <div className="text-[11px] text-slate-500 mt-1">Filtered records</div>
        </div>

        {/* Held for Review */}
        <div className="p-4 rounded-2xl bg-slate-900 border border-amber-900/40 shadow-sm hover:border-amber-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-400">Held for Review</span>
            <div className="p-2 rounded-xl bg-amber-950/40 text-amber-400">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-2">{kpis.held_for_review}</div>
          <div className="text-[11px] text-amber-500/80 mt-1">Audit / Provisional</div>
        </div>

        {/* Verified & Posted */}
        <div className="p-4 rounded-2xl bg-slate-900 border border-emerald-900/40 shadow-sm hover:border-emerald-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-emerald-400">Verified & Posted</span>
            <div className="p-2 rounded-xl bg-emerald-950/40 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-300 mt-2">{kpis.verified_posted}</div>
          <div className="text-[11px] text-emerald-500/80 mt-1">Official Register</div>
        </div>

        {/* Duplicates Blocked */}
        <div className="p-4 rounded-2xl bg-slate-900 border border-rose-900/40 shadow-sm hover:border-rose-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-rose-400">Duplicates Blocked</span>
            <div className="p-2 rounded-xl bg-rose-950/40 text-rose-400">
              <ShieldBan className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-300 mt-2">{kpis.duplicates_rejected}</div>
          <div className="text-[11px] text-rose-500/80 mt-1">Protected by Key</div>
        </div>

        {/* Total Bill Value */}
        <div className="p-4 rounded-2xl bg-slate-900 border border-sky-900/40 shadow-sm hover:border-sky-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-sky-400">Total Billed</span>
            <div className="p-2 rounded-xl bg-sky-950/40 text-sky-400">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-sky-300 mt-2">{formatMoney(kpis.total_bill_amount)}</div>
          <div className="text-[11px] text-sky-500/80 mt-1">Posted actuals</div>
        </div>

        {/* Outstanding Balance */}
        <div className="p-4 rounded-2xl bg-slate-900 border border-indigo-900/40 shadow-sm hover:border-indigo-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-indigo-400">Outstanding</span>
            <div className="p-2 rounded-xl bg-indigo-950/40 text-indigo-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-indigo-300 mt-2">{formatMoney(kpis.total_outstanding)}</div>
          <div className="text-[11px] text-indigo-500/80 mt-1">Pending payment</div>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Multi-Month Generation & Grid Trend */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Corridor Monthly Energy Mix (kWh)
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">EB Grid Supply vs Solar Renewable vs DG Backup</p>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  labelStyle={{ color: '#f8fafc' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="eb_units" name="EB Grid (kWh)" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="solar_units" name="Solar Gen (kWh)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="dg_units" name="DG Gen (kWh)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Toll Plaza Comparison */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-sky-400" />
              Toll Plaza Expenditure Comparison
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Authoritative billed spend by corridor section</p>

            <div className="space-y-4 mt-6">
              {(data?.plazas || []).map((p) => (
                <div key={p.plaza_id} className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="text-slate-200">{p.plaza_id} Section</span>
                    <span className="text-emerald-400 font-mono">{formatMoney(p.total_amount)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                    <span>{p.bill_count} Bills Posted</span>
                    <span>{p.total_kwh.toLocaleString()} kWh</span>
                  </div>
                  <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-sky-400 h-full rounded-full"
                      style={{
                        width: `${Math.min(100, Math.max(15, (p.total_amount / (kpis.total_bill_amount || 1)) * 100))}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-[11px] text-emerald-300 mt-4">
            ✓ PostgreSQL schema authority: zero UI-side formula drift.
          </div>
        </div>
      </div>
    </div>
  );
};
