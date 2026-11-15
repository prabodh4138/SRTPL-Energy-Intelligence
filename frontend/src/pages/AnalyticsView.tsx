import React, { useState, useEffect } from 'react';
import {
  Zap,
  Flame,
  Sun,
  Cpu,
  BatteryCharging,
  AlertTriangle,
  Moon,
  Clock,
  ShieldCheck,
  Building2,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { api } from '../api';

type SubmoduleKey = 'DG' | 'EB' | 'SOLAR' | 'TRANSFORMER' | 'UPS';

interface SubmoduleTab {
  id: SubmoduleKey;
  label: string;
  icon: React.FC<{ className?: string }>;
}

const SUBMODULES: SubmoduleTab[] = [
  { id: 'DG', label: 'Diesel Generators (DG)', icon: Flame },
  { id: 'EB', label: 'Electricity Board (EB)', icon: Zap },
  { id: 'SOLAR', label: 'Solar Plants', icon: Sun },
  { id: 'TRANSFORMER', label: 'Transformers', icon: Cpu },
  { id: 'UPS', label: 'UPS & Battery', icon: BatteryCharging },
];

export const AnalyticsView: React.FC = () => {
  const [activeSubmodule, setActiveSubmodule] = useState<SubmoduleKey>('DG');
  const [plazaFilter, setPlazaFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async (submod = activeSubmodule, plz = plazaFilter) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getModuleAnalytics(submod, plz);
      if (res && res.data) {
        setData(res.data);
      } else {
        setData(null);
      }
    } catch (err: any) {
      setError(err.message || `Failed to fetch live analytics for ${submod}`);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(activeSubmodule, plazaFilter);
  }, [activeSubmodule, plazaFilter]);

  const kpis = data?.kpis || {};
  const hasData = data?.has_data === true && (data?.total_logs || 0) > 0;
  const lastReadings = data?.last_readings || [];
  const plazaComp = data?.plaza_comparison || [];
  const nightEntries = data?.night_entries || [];
  const wrongEntries = data?.wrong_entries || [];
  const techSummary = data?.technicians_summary || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Module 7 · Live Database Analytics
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mt-1">
            Analytics
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Live query from Supabase database SQL views (<code className="text-emerald-300">vw_&lt;module&gt;_reading_kpis</code>,{' '}
            <code className="text-emerald-300">vw_&lt;module&gt;_asset_latest_reading</code>). Auto-syncs on new ingestion.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchAnalytics(activeSubmodule, plazaFilter)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh SQL Views
          </button>
        </div>
      </div>

      {/* 5 Submodules Segmented Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {SUBMODULES.map((sub) => {
          const Icon = sub.icon;
          const isActive = activeSubmodule === sub.id;
          return (
            <button
              key={sub.id}
              onClick={() => setActiveSubmodule(sub.id)}
              className={`flex items-center justify-center gap-2.5 px-3 py-3 rounded-2xl text-xs font-bold transition border ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-600/30 to-teal-600/30 text-emerald-300 border-emerald-500/50 shadow-lg shadow-emerald-950/40'
                  : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border-slate-800 hover:border-slate-700'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
              <span>{sub.id}</span>
            </button>
          );
        })}
      </div>

      {/* Plaza Filter Bar */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <Filter className="w-3.5 h-3.5" />
          <span className="font-semibold">Plaza Scope:</span>
        </div>
        <div className="flex items-center gap-1.5">
          {['ALL', 'TP01', 'TP02', 'TP03'].map((plz) => (
            <button
              key={plz}
              onClick={() => setPlazaFilter(plz)}
              className={`px-3 py-1 rounded-lg font-bold transition ${
                plazaFilter === plz
                  ? 'bg-emerald-500 text-slate-950 shadow-md'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {plz}
            </button>
          ))}
        </div>
      </div>

      {/* Loading state */}
      {loading && !data && (
        <div className="p-12 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-400" />
          <p className="text-xs">Querying Supabase database views for {activeSubmodule}...</p>
        </div>
      )}

      {/* Error / Data Not Found State */}
      {!loading && (!hasData || error) && (
        <div className="p-8 rounded-2xl bg-amber-950/20 border border-amber-800/40 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 mx-auto text-amber-400" />
          <h3 className="text-base font-bold text-amber-300">Data Not Found for {activeSubmodule}</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {error ||
              `No verified readings or telemetry found in the database for ${activeSubmodule}. Please ingest logs via Juno Import Centre to populate this module.`}
          </p>
        </div>
      )}

      {/* Live Content when data exists */}
      {!loading && hasData && (
        <div className="space-y-6">
          {/* Live SQL View KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {activeSubmodule === 'DG' && (
              <>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Active DG Units
                  </span>
                  <div className="text-2xl font-black text-slate-100">{kpis.active_generators || 0} Units</div>
                  <p className="text-[11px] text-slate-500 mt-1">{data.total_logs?.toLocaleString()} total verified logs</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Backup Generation
                  </span>
                  <div className="text-2xl font-black text-emerald-400">
                    {Number(kpis.total_cumulative_kwh || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">From SQL View vw_dg_reading_kpis</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Runtime Hours
                  </span>
                  <div className="text-2xl font-black text-sky-400">
                    {Number(kpis.total_cumulative_run_hours || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} Hrs
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Cumulative engine run time</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Tracked Fuel Level
                  </span>
                  <div className="text-2xl font-black text-amber-400">
                    {Number(kpis.total_fuel_level || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} L
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Current reservoir volume</p>
                </div>
              </>
            )}

            {activeSubmodule === 'EB' && (
              <>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Active Meters
                  </span>
                  <div className="text-2xl font-black text-slate-100">{kpis.active_meters || 0} Meters</div>
                  <p className="text-[11px] text-slate-500 mt-1">{data.total_logs?.toLocaleString()} total verified logs</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Cumulative Grid Energy
                  </span>
                  <div className="text-2xl font-black text-emerald-400">
                    {Number(kpis.total_cumulative_kwh || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Interval Delta: +{Number(kpis.total_interval_kwh || 0).toLocaleString()} kWh</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Power Factor
                  </span>
                  <div className="text-2xl font-black text-teal-400">
                    {Number(kpis.avg_power_factor || 0.98).toFixed(2)}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Grid compliance standard &ge; 0.95</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Peak Demand (MD)
                  </span>
                  <div className="text-2xl font-black text-purple-400">
                    {Number(kpis.peak_demand || 0).toFixed(1)} kW
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Maximum recorded demand</p>
                </div>
              </>
            )}

            {activeSubmodule === 'SOLAR' && (
              <>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Active Solar Plants
                  </span>
                  <div className="text-2xl font-black text-slate-100">{kpis.active_plants || 0} Plants</div>
                  <p className="text-[11px] text-slate-500 mt-1">{data.total_logs?.toLocaleString()} total verified logs</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Solar Clean Generation
                  </span>
                  <div className="text-2xl font-black text-amber-400">
                    {Number(kpis.total_cumulative_kwh || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Delta: +{Number(kpis.total_interval_kwh || 0).toLocaleString()} kWh</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    CO₂ Offset
                  </span>
                  <div className="text-2xl font-black text-emerald-400">
                    {Number(kpis.co2_avoided_kg || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kg
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Calculated using 0.82 kg/kWh</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Corridor Capacity
                  </span>
                  <div className="text-2xl font-black text-sky-400">121.38 kWp</div>
                  <p className="text-[11px] text-slate-500 mt-1">40.46 kWp per plant (3 Plazas)</p>
                </div>
              </>
            )}

            {activeSubmodule === 'TRANSFORMER' && (
              <>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Active Transformers
                  </span>
                  <div className="text-2xl font-black text-slate-100">{kpis.active_transformers || 0} Units</div>
                  <p className="text-[11px] text-slate-500 mt-1">{data.total_logs?.toLocaleString()} total verified logs</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Throughput Energy
                  </span>
                  <div className="text-2xl font-black text-emerald-400">
                    {Number(kpis.total_cumulative_kwh || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">HT substation metering</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Thermal Health
                  </span>
                  <div className="text-2xl font-black text-amber-400">
                    {Number(kpis.avg_oil_temp || 0).toFixed(1)}°C / {Number(kpis.avg_winding_temp || 0).toFixed(1)}°C
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">OTI / WTI temperatures</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Power Factor
                  </span>
                  <div className="text-2xl font-black text-teal-400">
                    {Number(kpis.avg_power_factor || 0.98).toFixed(2)}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Phase balanced nominal</p>
                </div>
              </>
            )}

            {activeSubmodule === 'UPS' && (
              <>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Active UPS Systems
                  </span>
                  <div className="text-2xl font-black text-slate-100">{kpis.active_systems || 0} Banks</div>
                  <p className="text-[11px] text-slate-500 mt-1">{data.total_logs?.toLocaleString()} total verified logs</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Output Voltage
                  </span>
                  <div className="text-2xl font-black text-emerald-400">
                    {Number(kpis.avg_output_voltage || 230).toFixed(1)} V
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Regulated AC output</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Battery DC Bus
                  </span>
                  <div className="text-2xl font-black text-amber-400">
                    {Number(kpis.avg_battery_vdc || 380).toFixed(1)} VDC
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Envelope: 360 - 435 V</p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Battery Temperature
                  </span>
                  <div className="text-2xl font-black text-sky-400">
                    {Number(kpis.avg_battery_temp || 25).toFixed(1)} °C
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Continuous thermal monitoring</p>
                </div>
              </>
            )}
          </div>

          {/* Section 1: Plaza-Wise Asset-Wise Last Reading */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200">
              ⚡ Plaza-Wise & Asset-Wise Latest Telemetry · {activeSubmodule}
            </h3>
            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                  <tr>
                    <th className="py-3 px-4">Plaza</th>
                    <th className="py-3 px-4">Asset Code</th>
                    <th className="py-3 px-4">Asset Name</th>
                    <th className="py-3 px-4">Capacity</th>
                    <th className="py-3 px-4">Last Reading Datetime</th>
                    <th className="py-3 px-4">Cumulative Value</th>
                    <th className="py-3 px-4">Technician</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {lastReadings.map((r: any, idx: number) => {
                    const isNotFound = r.status === 'DATA_NOT_FOUND';
                    const isStale = r.status?.includes('STALE');
                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-bold text-slate-100">{r.plaza_id}</td>
                        <td className="py-3 px-4 text-emerald-400">{r.asset_code}</td>
                        <td className="py-3 px-4 font-sans text-slate-300">{r.asset_name}</td>
                        <td className="py-3 px-4 text-amber-400 font-bold">{r.capacity}</td>
                        <td className="py-3 px-4 text-slate-300">
                          {isNotFound ? (
                            <span className="text-rose-400 font-bold">Data Not Found</span>
                          ) : (
                            r.reading_datetime
                          )}
                        </td>
                        <td className="py-3 px-4 font-bold text-slate-100">
                          {r.cumulative_kwh != null
                            ? `${Number(r.cumulative_kwh).toLocaleString()} kWh`
                            : r.run_hours != null
                            ? `${Number(r.run_hours).toLocaleString()} Hrs`
                            : isNotFound
                            ? '—'
                            : 'Active'}
                        </td>
                        <td className="py-3 px-4 font-sans text-slate-400">{r.technician}</td>
                        <td className="py-3 px-4 font-sans">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              isNotFound
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : isStale
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            }`}
                          >
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: Plaza Neglect & Defect Comparison */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200">
              🏆 Plaza Neglect & Defect Comparison · {activeSubmodule}
            </h3>
            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                  <tr>
                    <th className="py-3 px-4">Plaza</th>
                    <th className="py-3 px-4">Total Logs</th>
                    <th className="py-3 px-4">Wrong Entries</th>
                    <th className="py-3 px-4">Defect Rate %</th>
                    <th className="py-3 px-4">Night Shift Logs (8p–8a)</th>
                    <th className="py-3 px-4">Night %</th>
                    <th className="py-3 px-4">Severe Delays (&gt;2d)</th>
                    <th className="py-3 px-4">Neglect Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {plazaComp.map((p: any) => (
                    <tr key={p.plaza_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-bold text-slate-100">{p.plaza_id}</td>
                      <td className="py-3 px-4">{p.total_records.toLocaleString()}</td>
                      <td className="py-3 px-4 text-rose-400 font-bold">{p.wrong_entries_count.toLocaleString()}</td>
                      <td className="py-3 px-4 text-rose-400 font-bold">{p.defect_rate_pct}%</td>
                      <td className="py-3 px-4 text-amber-400 font-bold">{p.night_entries_count.toLocaleString()}</td>
                      <td className="py-3 px-4 text-amber-400 font-bold">{p.night_entry_pct}%</td>
                      <td className="py-3 px-4 text-purple-400 font-bold">{p.severe_delays_count}</td>
                      <td className="py-3 px-4 font-sans text-xs text-slate-300">{p.verdict}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Technician Night Entries (8:00 PM – 8:00 AM) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-200">
                🌙 Technician Night Shift Submissions (8:00 PM – 8:00 AM) · {activeSubmodule}
              </h3>
              <span className="text-xs text-amber-400 font-semibold">
                {nightEntries.length} off-hours entries detected
              </span>
            </div>

            {nightEntries.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-xs">
                ✅ No night shift entries (8:00 PM – 8:00 AM) recorded in database for {activeSubmodule}.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl max-h-72 overflow-y-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">#</th>
                      <th className="py-2.5 px-3">Plaza</th>
                      <th className="py-2.5 px-3">Asset Code</th>
                      <th className="py-2.5 px-3">Technician Name</th>
                      <th className="py-2.5 px-3">Entry Hour</th>
                      <th className="py-2.5 px-3">Reading Datetime</th>
                      <th className="py-2.5 px-3">Logged Timestamp</th>
                      <th className="py-2.5 px-3">Delay</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono text-xs">
                    {nightEntries.slice(0, 25).map((n: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 text-slate-500">{idx + 1}</td>
                        <td className="py-2 px-3 font-bold text-slate-100">{n.plaza_id}</td>
                        <td className="py-2 px-3 text-sky-400">{n.asset_code}</td>
                        <td className="py-2 px-3 font-sans font-bold text-emerald-400">{n.technician}</td>
                        <td className="py-2 px-3 text-amber-400 font-bold">{n.entry_hour}</td>
                        <td className="py-2 px-3 text-slate-400">{n.reading_datetime}</td>
                        <td className="py-2 px-3 text-slate-400">{n.submission_timestamp}</td>
                        <td className="py-2 px-3 text-purple-400 font-bold">
                          {n.delay_days !== 'N/A' ? `${n.delay_days}d` : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Section 4: Wrong Entries & Technical Defects Register */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-200">
                ⚠️ Wrong Entries & Technical Deficiencies · {activeSubmodule}
              </h3>
              <span className="text-xs text-rose-400 font-semibold">
                {wrongEntries.length} technical defects detected
              </span>
            </div>

            {wrongEntries.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-xs">
                ✅ No technical defects or wrong entries detected in database for {activeSubmodule}.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl max-h-72 overflow-y-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">#</th>
                      <th className="py-2.5 px-3">Plaza</th>
                      <th className="py-2.5 px-3">Asset Code</th>
                      <th className="py-2.5 px-3">Technician</th>
                      <th className="py-2.5 px-3">Reading Datetime</th>
                      <th className="py-2.5 px-3">Defect / Anomaly Message</th>
                      <th className="py-2.5 px-3">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono text-xs">
                    {wrongEntries.slice(0, 25).map((w: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 text-slate-500">{idx + 1}</td>
                        <td className="py-2 px-3 font-bold text-slate-100">{w.plaza_id}</td>
                        <td className="py-2 px-3 text-sky-400">{w.asset_code}</td>
                        <td className="py-2 px-3 font-sans font-bold text-emerald-400">{w.technician}</td>
                        <td className="py-2 px-3 text-slate-400">{w.reading_datetime}</td>
                        <td className="py-2 px-3 font-sans text-rose-300 font-semibold">{w.violation}</td>
                        <td className="py-2 px-3 font-sans">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              w.severity === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            }`}
                          >
                            {w.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Section 5: Technician Performance Register for this Module */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200">
              👨‍🔧 Technician Performance Register · {activeSubmodule}
            </h3>
            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                  <tr>
                    <th className="py-3 px-4">Technician Name</th>
                    <th className="py-3 px-4">Plazas</th>
                    <th className="py-3 px-4">Total Logs</th>
                    <th className="py-3 px-4">Night Logs (8p–8a)</th>
                    <th className="py-3 px-4">Night %</th>
                    <th className="py-3 px-4">Defects</th>
                    <th className="py-3 px-4">Defect %</th>
                    <th className="py-3 px-4">Avg Delay</th>
                    <th className="py-3 px-4">Max Delay</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {techSummary.map((t: any) => (
                    <tr key={t.technician_name} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-sans font-bold text-slate-100">{t.technician_name}</td>
                      <td className="py-3 px-4 text-emerald-400">{t.plazas}</td>
                      <td className="py-3 px-4">{t.total_logs.toLocaleString()}</td>
                      <td className="py-3 px-4 text-amber-400 font-bold">{t.night_logs.toLocaleString()}</td>
                      <td className="py-3 px-4 text-amber-400 font-bold">{t.night_pct}%</td>
                      <td className="py-3 px-4 text-rose-400 font-bold">{t.defects_count}</td>
                      <td className="py-3 px-4 text-rose-400 font-bold">{t.defect_pct}%</td>
                      <td className="py-3 px-4">{t.avg_delay_days}d</td>
                      <td className="py-3 px-4 text-purple-400 font-bold">{t.max_delay_days}d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
