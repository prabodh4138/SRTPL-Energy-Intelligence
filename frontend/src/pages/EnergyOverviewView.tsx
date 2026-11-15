import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Zap,
  Flame,
  Sun,
  IndianRupee,
  Activity,
  AlertTriangle,
  Clock,
  Layers,
  ChevronRight,
  ShieldCheck,
  RefreshCw,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

interface EnergyOverviewData {
  status: string;
  title: string;
  subtitle: string;
  kpis: {
    eb: {
      label: string;
      value: number;
      unit: string;
      period: string;
      tp01: number;
      tp02: number;
      tp03: number;
      total: number;
      schedule: string;
      rule: string;
    };
    dg: {
      label: string;
      value: number;
      unit: string;
      confirmed_kwh: number;
      unverified_kwh: number;
      runtime_minutes: number;
      runtime_hours: number;
      rule: string;
    };
    solar: {
      label: string;
      value: number;
      unit: string;
      daily_interval_total_kwh: number;
      tp01: number;
      tp02: number;
      tp03: number;
      month_end_snapshot_total_kwh: number;
      snapshot_confirmed_asset_months: number;
      total_capacity_kwp: number;
      rule: string;
    };
    energy_cost: {
      label: string;
      value: number | null;
      display_value: string;
      subtitle: string;
      rule: string;
    };
    solar_saving: {
      label: string;
      value: number | null;
      display_value: string;
      subtitle: string;
      rule: string;
    };
  };
  operations_snapshot: {
    dg_running_time: string;
    dg_running_time_val: number;
    solar_capacity: string;
    solar_capacity_val: number;
    open_exceptions: number;
    open_exceptions_label: string;
    cost_saving: string;
    plaza_ids: string[];
  };
  monthly_trend: Array<{
    month: string;
    eb: number;
    dg: number;
    solar: number;
  }>;
  plaza_comparison: Array<{
    plaza_id: string;
    eb_kwh: number;
    dg_kwh: number | null;
    dg_display: string;
    solar_kwh: number;
    solar_display: string;
    dg_available: boolean;
  }>;
  exceptions_summary: {
    total_open: number;
    critical_count: number;
    warning_count: number;
    dg_critical_decrease: number;
    dg_source_warnings: number;
    transformer_cumulative_warnings: number;
  };
  transformer_rules: {
    frequency_range: string;
    primary_voltage: string;
    secondary_voltage: string;
    clean_voltage_imbalance: string;
    clean_current_imbalance: string;
    timestamps: string;
    authoritative_rule: string;
  };
}

interface EnergyOverviewProps {
  onNavigateToModule?: (moduleKey: string) => void;
}

export const EnergyOverviewView: React.FC<EnergyOverviewProps> = ({ onNavigateToModule }) => {
  const [data, setData] = useState<EnergyOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [plazaFilter, setPlazaFilter] = useState('ALL');
  const [periodFilter, setPeriodFilter] = useState('reviewed_baseline');

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await api.getEnergyOverview(plazaFilter, periodFilter);
      setData(res);
    } catch (err) {
      console.error('Failed to load Energy Overview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [plazaFilter, periodFilter]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] text-slate-400 gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
        <span className="text-sm font-medium">Loading SRTPL Energy Command Center...</span>
      </div>
    );
  }

  const kpis = data?.kpis;
  const snapshot = data?.operations_snapshot;
  const trend = data?.monthly_trend || [];
  const plazas = data?.plaza_comparison || [];
  const excSummary = data?.exceptions_summary;
  const trfRules = data?.transformer_rules;

  return (
    <div className="space-y-6">
      {/* 1. Header Banner strictly matching PDF Page 3 */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-sky-950/40 border border-slate-800 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Designated Single User
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-500/10 text-sky-400 border border-sky-500/30">
                Password-Free Trusted Host
              </span>
            </div>
            <h1 className="text-2xl font-black text-slate-100 tracking-tight mt-1.5 flex items-center gap-2">
              <span>SRTPL ENERGY COMMAND CENTER</span>
            </h1>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mt-0.5">
              ENERGY OVERVIEW | DEMO DATA — illustrative only (Reviewed Baseline)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchOverview}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1.5 text-xs font-medium border border-slate-700"
              title="Refresh Baseline Data"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sync</span>
            </button>
            <div className="text-right hidden sm:block">
              <span className="text-[10px] text-slate-400 font-mono block">Baseline Window</span>
              <span className="text-xs font-bold text-emerald-400 font-mono">1 Apr – 25 Oct 2026</span>
            </div>
          </div>
        </div>

        {/* Filters Row */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-slate-400 font-medium">Plaza ID:</span>
            <div className="flex gap-1.5 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
              {['ALL', 'TP01', 'TP02', 'TP03'].map((pid) => (
                <button
                  key={pid}
                  onClick={() => setPlazaFilter(pid)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition ${
                    plazaFilter === pid
                      ? 'bg-emerald-500 text-slate-950 font-bold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {pid}
                </button>
              ))}
            </div>
            <span className="text-[11px] text-slate-500 italic ml-1">
              (Use TP01, TP02, TP03 only until plaza names are verified)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Period:</span>
            <select
              value={periodFilter}
              onChange={(e) => setPeriodFilter(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-xl px-3 py-1 outline-none text-xs font-medium cursor-pointer"
            >
              <option value="reviewed_baseline">Reviewed Baseline (Apr - Oct 2026)</option>
              <option value="operational_live">Live Operational Database</option>
            </select>
          </div>
        </div>
      </div>

      {/* 2. Primary 4 KPI Cards (Matching Page 3) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* EB CONSUMPTION */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              EB CONSUMPTION
            </span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-100 font-mono tracking-tight">
              {kpis?.eb.value.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) || '2,672.4'}
            </span>
            <span className="text-sm font-bold text-emerald-400 font-mono">kWh</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 space-y-0.5">
            <div className="text-slate-300 font-mono text-[10px]">
              TP01: 926.20 | TP02: 945.70 | TP03: 800.50
            </div>
            <div className="text-slate-500 text-[10px]">
              08:00 meter schedule · First reading NULL
            </div>
          </div>
        </div>

        {/* DG GENERATION */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              DG GENERATION
            </span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-100 font-mono tracking-tight">
              {kpis?.dg.value.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) || '11,590.6'}
            </span>
            <span className="text-xs font-semibold text-amber-400 font-mono">confirmed kWh</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 space-y-0.5">
            <div className="text-amber-300/80 font-mono text-[10px]">
              Unverified generation: 3.00 kWh (shown separately)
            </div>
            <div className="text-slate-500 text-[10px]">
              Only TP01 reviewed · TP02/TP03 no readings
            </div>
          </div>
        </div>

        {/* SOLAR GENERATION */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              SOLAR GENERATION
            </span>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Sun className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-100 font-mono tracking-tight">
              {kpis?.solar.value.toLocaleString('en-US') || '54,380'}
            </span>
            <span className="text-xs font-semibold text-sky-400 font-mono">interval kWh</span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 space-y-0.5">
            <div className="text-sky-300/80 font-mono text-[10px]">
              TP01 18,440 · TP02 17,921 · TP03 18,019
            </div>
            <div className="text-slate-500 text-[10px]">
              Month snapshot 27,502 kWh (never add to interval)
            </div>
          </div>
        </div>

        {/* ENERGY COST */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              ENERGY COST
            </span>
            <div className="p-2 rounded-xl bg-slate-800 text-slate-400 border border-slate-700">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-300 tracking-tight">
              {kpis?.energy_cost.display_value || 'Unavailable'}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400 space-y-0.5">
            <div className="text-amber-400 font-medium text-[10px]">
              {kpis?.energy_cost.subtitle || 'tariff pending'}
            </div>
            <div className="text-slate-500 text-[10px]">
              Cost/saving only after tariff inputs verified
            </div>
          </div>
        </div>
      </div>

      {/* 3. Middle Section: Monthly Trend & Operations Snapshot */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Energy Trend Chart (2 Columns) */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-200 tracking-wide uppercase">
                  MONTHLY ENERGY TREND — SAMPLE
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Comparative trend across reviewed baseline months (Apr – Oct 2026)
                </p>
              </div>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                kWh Intervals
              </span>
            </div>

            <div className="h-64 mt-4 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trend} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      fontSize: '11px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Bar dataKey="solar" name="Solar (kWh)" fill="#0284c7" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="dg" name="DG (kWh)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="eb" name="EB (kWh)" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 italic flex items-center justify-between">
            <span>* Illustrative design sample — keep Solar daily intervals separate from snapshots.</span>
            <span className="font-mono text-emerald-400">Total Solar: 54,380 kWh</span>
          </div>
        </div>

        {/* OPERATIONS SNAPSHOT (1 Column strictly matching PDF Page 3) */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-200 tracking-wide uppercase flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>OPERATIONS SNAPSHOT</span>
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                Verified
              </span>
            </div>

            <div className="mt-4 space-y-4">
              {/* DG Running Time */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-medium block">DG running time</span>
                  <span className="text-[10px] text-slate-500 font-mono">26,471 mins aggregated</span>
                </div>
                <div className="text-right">
                  <span className="text-base font-bold text-slate-100 font-mono">
                    {snapshot?.dg_running_time || '441.18 h'}
                  </span>
                </div>
              </div>

              {/* Solar Capacity */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-medium block">Solar capacity</span>
                  <span className="text-[10px] text-slate-500">3 plants × 40.46 kWp</span>
                </div>
                <div className="text-right">
                  <span className="text-base font-bold text-sky-400 font-mono">
                    {snapshot?.solar_capacity || '121.38 kWp'}
                  </span>
                  <span className="text-[9px] text-slate-500 block">capacity_kwp</span>
                </div>
              </div>

              {/* Open Exceptions */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-medium block">Open exceptions</span>
                  <span className="text-[10px] text-amber-500/80">1 critical DG · 27 warnings</span>
                </div>
                <div className="text-right">
                  <span className="text-base font-bold text-amber-400 font-mono">
                    {snapshot?.open_exceptions_label || '28 (reviewed snapshot)'}
                  </span>
                </div>
              </div>

              {/* Cost / Saving */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-medium block">Cost / saving</span>
                  <span className="text-[10px] text-slate-500">Tariff pending verification</span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold text-slate-300">
                    {snapshot?.cost_saving || 'Await verified inputs'}
                  </span>
                </div>
              </div>

              {/* Plaza IDs */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                <div>
                  <span className="text-xs text-slate-400 font-medium block">Plaza IDs</span>
                  <span className="text-[10px] text-slate-500">Corridor toll plazas</span>
                </div>
                <div className="flex items-center gap-1.5 font-mono text-xs font-bold">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400">TP01</span>
                  <span className="text-slate-600">/</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-400">TP02</span>
                  <span className="text-slate-600">/</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-400">TP03</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800">
            {onNavigateToModule && (
              <button
                onClick={() => onNavigateToModule('exceptions')}
                className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center justify-center gap-1.5 border border-slate-700"
              >
                <span>Inspect 28 Open Exceptions</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 4. Plaza Performance Comparison (Rule: TP02/TP03 DG show "No DG readings available", not zero) */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-200 tracking-wide uppercase">
              PLAZA PERFORMANCE COMPARISON & DG AVAILABILITY RULE
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Rule: Only TP01 has reviewed DG readings. TP02/TP03 must show "No DG readings available", not zero.
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-bold">
            Honest Metrics Policy
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plazas.map((p) => (
            <div
              key={p.plaza_id}
              className={`p-4 rounded-xl border transition ${
                plazaFilter === p.plaza_id
                  ? 'bg-slate-800/80 border-emerald-500/50 shadow-md'
                  : 'bg-slate-950/40 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-base font-bold text-slate-100 font-mono">{p.plaza_id}</span>
                <span className="text-[10px] font-semibold text-slate-400">
                  {p.plaza_id === 'TP01'
                    ? 'Km 24+500'
                    : p.plaza_id === 'TP02'
                    ? 'Km 68+200'
                    : 'Km 112+800'}
                </span>
              </div>

              <div className="mt-3 space-y-2 text-xs">
                {/* EB */}
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">EB Consumption:</span>
                  <span className="font-mono font-semibold text-slate-200">
                    {p.eb_kwh.toFixed(2)} kWh
                  </span>
                </div>

                {/* DG (Strict Rule Display) */}
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">DG Generation:</span>
                  {p.dg_available ? (
                    <span className="font-mono font-bold text-amber-400">
                      {p.dg_display}
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-semibold italic border border-slate-700">
                      {p.dg_display}
                    </span>
                  )}
                </div>

                {/* Solar */}
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Solar Generation:</span>
                  <span className="font-mono font-semibold text-sky-400">
                    {p.solar_display}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Approved Analytics Rules Summary Callout */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-slate-200 tracking-wide uppercase">
            APPROVED TECHNICAL RULES & SCOPE BOUNDARY SUMMARY
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-emerald-400 font-bold block mb-1">⚡ EB Rules</span>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>• 08:00 meter-reading schedule.</li>
              <li>• First reading has NULL interval, not zero.</li>
              <li>• Total: 2,672.40 kWh (1 Apr–25 Oct).</li>
            </ul>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-amber-400 font-bold block mb-1">🔥 DG Rules</span>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>• Only TP01 has reviewed DG readings.</li>
              <li>• 11,590.6 kWh confirmed; 3.0 kWh unverified.</li>
              <li>• 441.18 hrs (26,471 mins aggregate).</li>
            </ul>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-sky-400 font-bold block mb-1">☀️ Solar Rules</span>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>• 3 plants × 40.46 kWp = 121.38 kWp.</li>
              <li>• Use capacity_kwp, not kVA.</li>
              <li>• Never add snapshot and daily interval totals.</li>
            </ul>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-indigo-400 font-bold block mb-1">🔌 Transformer Rules</span>
            <ul className="text-slate-400 space-y-1 text-[11px]">
              <li>• Frequency 49–51 Hz range; &lt;49 / &gt;51 REVIEW.</li>
              <li>• Clean V imbalance ≤5%; Clean I imbalance ≤30%.</li>
              <li>• Use reading_datetime, not created_at.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
