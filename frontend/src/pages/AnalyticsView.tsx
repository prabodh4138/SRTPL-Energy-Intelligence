import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BatteryCharging,
  Clock3,
  Cpu,
  Flame,
  Moon,
  RefreshCw,
  ShieldAlert,
  Sun,
  Zap,
} from 'lucide-react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api';

type SubmoduleKey = 'DG' | 'EB' | 'SOLAR' | 'TRANSFORMER' | 'UPS';
type PeriodKey = 'daily' | 'monthly' | 'yearly';
type MetricDef = { label: string; key: string; unit?: string; format?: 'hhmm' | 'percent' | 'count' };

const SUBMODULES: Array<{ id: SubmoduleKey; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: 'DG', label: 'Diesel Generators', icon: Flame },
  { id: 'EB', label: 'Electricity Board', icon: Zap },
  { id: 'SOLAR', label: 'Solar Plants', icon: Sun },
  { id: 'TRANSFORMER', label: 'Transformers', icon: Cpu },
  { id: 'UPS', label: 'UPS & Battery', icon: BatteryCharging },
];

const PERIODS: Array<{ id: PeriodKey; label: string }> = [
  { id: 'daily', label: 'Daily' },
  { id: 'monthly', label: 'Monthly' },
  { id: 'yearly', label: 'Yearly' },
];

const METRICS: Record<SubmoduleKey, MetricDef[]> = {
  DG: [
    { label: 'Confirmed generation', key: 'confirmed_generation_kwh', unit: 'kWh' },
    { label: 'Validated runtime', key: 'validated_runtime_minutes', unit: 'HH:MM', format: 'hhmm' },
    { label: 'Confirmed diesel use', key: 'confirmed_diesel_consumption_l', unit: 'L' },
    { label: 'Fuel per generation', key: 'diesel_l_per_kwh', unit: 'L/kWh' },
    { label: 'Average power factor', key: 'average_pf' },
    { label: 'Average voltage imbalance', key: 'average_voltage_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Average current imbalance', key: 'average_current_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Confirmed generation intervals', key: 'confirmed_generation_interval_count', format: 'count' },
    { label: 'Unverified generation intervals', key: 'unverified_generation_interval_count', format: 'count' },
    { label: 'Zero-generation intervals', key: 'zero_generation_interval_count', format: 'count' },
    { label: 'Negative fuel reconciliations', key: 'negative_fuel_reconciliation_exception_count', format: 'count' },
    { label: 'Maximum voltage imbalance', key: 'maximum_voltage_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Maximum current imbalance', key: 'maximum_current_imbalance_pct', unit: '%', format: 'percent' },
  ],
  EB: [
    { label: 'Valid interval energy', key: 'valid_interval_kwh', unit: 'kWh' },
    { label: 'Valid apparent energy', key: 'valid_interval_kvah', unit: 'kVAh' },
    { label: 'Valid reactive energy', key: 'valid_interval_kvarh', unit: 'kvarh' },
    { label: 'Average power factor', key: 'average_pf' },
    { label: 'Maximum recorded demand', key: 'maximum_recorded_demand' },
  ],
  SOLAR: [
    { label: 'Valid generation', key: 'valid_generation_kwh', unit: 'kWh' },
    { label: 'Average generation interval', key: 'average_generation_interval_kwh', unit: 'kWh' },
    { label: 'Negative cumulative deltas', key: 'negative_cumulative_delta_exception_count', format: 'count' },
    { label: 'Interval reconciliation checks', key: 'interval_reconciliation_comparable_count', format: 'count' },
  ],
  TRANSFORMER: [
    { label: 'Primary voltage imbalance', key: 'average_primary_voltage_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Secondary voltage imbalance', key: 'average_secondary_voltage_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Primary current imbalance', key: 'average_primary_current_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Secondary current imbalance', key: 'average_secondary_current_imbalance_pct', unit: '%', format: 'percent' },
    { label: 'Average power factor', key: 'average_pf' },
    { label: 'Average frequency', key: 'average_frequency_hz', unit: 'Hz' },
    { label: 'Average oil temperature', key: 'average_oil_temperature_c', unit: '°C' },
    { label: 'Average winding temperature', key: 'average_winding_temperature_c', unit: '°C' },
  ],
  UPS: [
    { label: 'Average output voltage', key: 'average_output_voltage', unit: 'V' },
    { label: 'Average output current', key: 'average_output_current', unit: 'A' },
    { label: 'Average output frequency', key: 'average_output_frequency', unit: 'Hz' },
    { label: 'Average battery voltage', key: 'average_battery_vdc', unit: 'VDC' },
    { label: 'Average battery temperature', key: 'average_battery_temperature', unit: '°C' },
    { label: 'Average rectifier voltage', key: 'average_rectifier_voltage', unit: 'V' },
  ],
};

const numberValue = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const formatNumber = (value: unknown, digits = 2): string => {
  const n = numberValue(value);
  return n === null
    ? '—'
    : n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
};

const formatRuntime = (minutes: unknown): string => {
  const n = numberValue(minutes);
  if (n === null) return '—';
  const total = Math.max(0, Math.round(n));
  const hours = Math.floor(total / 60);
  return String(hours).padStart(2, '0') + ':' + String(total % 60).padStart(2, '0');
};

const dateTime = (value: unknown): string => {
  if (!value) return '—';
  return String(value).replace('T', ' ').replace(/\+00:00$/, ' UTC').slice(0, 22);
};

const metricValue = (kpis: Record<string, unknown>, def: MetricDef): string => {
  const value = kpis?.[def.key];
  if (def.format === 'hhmm') return formatRuntime(value);
  if (def.format === 'count') return formatNumber(value, 0);
  if (def.format === 'percent') {
    const n = numberValue(value);
    return n === null ? '—' : n.toLocaleString(undefined, { maximumFractionDigits: 2 }) + '%';
  }
  const formatted = formatNumber(value);
  return formatted === '—' ? '—' : def.unit ? formatted + ' ' + def.unit : formatted;
};

const StatusPill: React.FC<{ value?: string | null }> = ({ value }) => {
  const valid = String(value || '').toUpperCase() === 'VALID';
  return (
    <span className={valid
      ? 'inline-flex rounded-full border border-emerald-700/60 bg-emerald-500/10 px-2 py-1 text-[10px] font-bold text-emerald-300'
      : 'inline-flex rounded-full border border-amber-700/60 bg-amber-500/10 px-2 py-1 text-[10px] font-bold text-amber-300'}>
      {value || 'UNKNOWN'}
    </span>
  );
};

const MetricCard: React.FC<{ label: string; value: string; tone?: string; note?: string }> = ({
  label, value, tone = 'text-slate-100', note,
}) => (
  <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-lg">
    <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{label}</div>
    <div className={'mt-2 text-2xl font-black ' + tone}>{value}</div>
    {note && <div className="mt-1 text-[11px] text-slate-500">{note}</div>}
  </div>
);

const TableFrame: React.FC<{ title: string; note?: string; children: React.ReactNode; count?: number }> = ({
  title, note, children, count,
}) => (
  <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg">
    <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
      <div>
        <h2 className="text-sm font-bold text-slate-100">{title}</h2>
        {note && <p className="mt-1 text-[11px] text-slate-500">{note}</p>}
      </div>
      {count !== undefined && <span className="rounded-full bg-slate-800 px-2.5 py-1 text-[10px] font-bold text-slate-300">{count.toLocaleString()}</span>}
    </div>
    {children}
  </section>
);

export const AnalyticsView: React.FC = () => {
  const [activeSubmodule, setActiveSubmodule] = useState<SubmoduleKey>('DG');
  const [plazaFilter, setPlazaFilter] = useState('ALL');
  const [period, setPeriod] = useState<PeriodKey>('daily');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [refreshToken, setRefreshToken] = useState(0);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    setLoading(true);
    setError(null);
    api.getModuleAnalytics(
      activeSubmodule,
      plazaFilter,
      period,
      dateFrom || undefined,
      dateTo || undefined,
    )
      .then((response: any) => {
        if (current) setData(response?.data || null);
      })
      .catch((err: any) => {
        if (current) {
          setData(null);
          setError(err?.message || 'Could not load Module 7 analytics.');
        }
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => { current = false; };
  }, [activeSubmodule, plazaFilter, period, dateFrom, dateTo, refreshToken]);

  const summary = data?.summary || {};
  const kpis = summary?.kpis || {};
  const hasData = data?.status === 'READY' && data?.has_data === true;
  const chartRows = data?.daily_trends || [];
  const latestReadings = data?.latest_readings || [];
  const exceptions = data?.exceptions || [];
  const corrections = data?.corrections || [];
  const nightEntries = data?.night_entries || [];
  const technicians = data?.technicians || [];
  const filteredErrors = useMemo(() => {
    if (error) return error;
    if (data?.status === 'SQL_VIEWS_UNAVAILABLE') return data.message;
    if (data?.status === 'DATABASE_NOT_CONFIGURED') return data.message;
    return null;
  }, [data, error]);

  return (
    <main className="space-y-6 pb-10">
      <header className="flex flex-col gap-4 border-b border-slate-800 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-300">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Module 7 · SQL analytics
          </div>
          <h1 className="mt-1 text-3xl font-black text-slate-100">Energy Analytics</h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-400">
            Validated metrics from the Module 7 SQL views. Every reporting scope reconciles total records to VALID plus EXCEPTION.
          </p>
        </div>
        <button
          onClick={() => setRefreshToken((value) => value + 1)}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-xs font-bold text-slate-100 transition hover:border-emerald-600"
        >
          <RefreshCw className={'h-4 w-4 ' + (loading ? 'animate-spin' : '')} />
          Refresh analytics
        </button>
      </header>

      <nav className="grid grid-cols-2 gap-2 sm:grid-cols-5" aria-label="Analytics submodule">
        {SUBMODULES.map((module) => {
          const Icon = module.icon;
          const active = activeSubmodule === module.id;
          return (
            <button
              key={module.id}
              onClick={() => setActiveSubmodule(module.id)}
              aria-pressed={active}
              className={active
                ? 'flex items-center justify-center gap-2 rounded-xl border border-emerald-500/60 bg-emerald-500/10 px-3 py-3 text-xs font-bold text-emerald-200'
                : 'flex items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-3 text-xs font-bold text-slate-400 hover:border-slate-600 hover:text-slate-200'}
            >
              <Icon className="h-4 w-4" />
              <span>{module.id}</span>
            </button>
          );
        })}
      </nav>

      <section className="grid grid-cols-1 gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 md:grid-cols-2 xl:grid-cols-5">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Plaza
          <select
            value={plazaFilter}
            onChange={(event) => setPlazaFilter(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs normal-case text-slate-100"
          >
            <option value="ALL">All plazas</option>
            <option value="TP01">TP01</option>
            <option value="TP02">TP02</option>
            <option value="TP03">TP03</option>
          </select>
        </label>
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          From date
          <input type="date" value={dateFrom} max={dateTo || undefined} onChange={(event) => setDateFrom(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs normal-case text-slate-100" />
        </label>
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          To date
          <input type="date" value={dateTo} min={dateFrom || undefined} onChange={(event) => setDateTo(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs normal-case text-slate-100" />
        </label>
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Aggregation
          <select value={period} onChange={(event) => setPeriod(event.target.value as PeriodKey)}
            className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs normal-case text-slate-100">
            {PERIODS.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select>
        </label>
        <div className="flex items-end">
          <button onClick={() => { setDateFrom(''); setDateTo(''); setPlazaFilter('ALL'); }}
            className="w-full rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800">
            Clear filters
          </button>
        </div>
      </section>

      {loading && !data && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-12 text-center text-sm text-slate-400">
          <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin text-emerald-400" />
          Reading the Module 7 SQL views…
        </div>
      )}

      {!loading && filteredErrors && (
        <section className="rounded-2xl border border-amber-700/40 bg-amber-950/20 p-5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
            <div>
              <h2 className="font-bold text-amber-200">Analytics views need attention</h2>
              <p className="mt-1 text-sm text-slate-300">{filteredErrors}</p>
              {data?.required_views && (
                <p className="mt-2 break-all text-[11px] text-slate-500">
                  Required views: {data.required_views.join(', ')}
                </p>
              )}
            </div>
          </div>
        </section>
      )}

      {!loading && data?.status === 'READY' && !hasData && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center">
          <Activity className="mx-auto h-8 w-8 text-slate-500" />
          <h2 className="mt-3 font-bold text-slate-200">No records in this filter</h2>
          <p className="mt-1 text-sm text-slate-400">{data.message || 'No readings match the selected plaza and date range.'}</p>
        </section>
      )}

      {hasData && (
        <>
          <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total records" value={formatNumber(summary.total_records, 0)} tone="text-slate-100" note="All received readings in scope" />
            <MetricCard label="VALID records" value={formatNumber(summary.valid_records, 0)} tone="text-emerald-300" />
            <MetricCard label="EXCEPTION records" value={formatNumber(summary.exception_records, 0)} tone="text-amber-300" />
            <MetricCard
              label="Reconciliation difference"
              value={formatNumber(summary.reconciliation_difference, 0)}
              tone={numberValue(summary.reconciliation_difference) === 0 ? 'text-emerald-300' : 'text-rose-300'}
              note="Total − VALID − EXCEPTION (expected 0)"
            />
          </section>

          <section>
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-300" />
              <h2 className="text-sm font-bold text-slate-100">{activeSubmodule} performance</h2>
              <span className="text-[11px] text-slate-500">VALID readings only where applicable</span>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {METRICS[activeSubmodule].map((metric) => (
                <MetricCard key={metric.key} label={metric.label} value={metricValue(kpis, metric)}
                  tone="text-emerald-300" note={metric.key.includes('imbalance') ? 'Formula output; no severity threshold applied' : undefined} />
              ))}
            </div>
          </section>

          <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Delayed entries (≥24h)" value={formatNumber(summary.delayed_entry_count, 0)} tone="text-amber-300" note="created_on − reading_datetime" />
            <MetricCard label="Night readings" value={formatNumber(summary.night_reading_count, 0)} tone="text-sky-300" note="reading_datetime: 22:00–06:00 IST" />
            <MetricCard label="Night entries" value={formatNumber(summary.night_entry_count, 0)} tone="text-sky-300" note="created_on: 22:00–06:00 IST" />
            <MetricCard label="Timestamp anomalies" value={formatNumber(summary.negative_entry_delay_timestamp_anomaly_count, 0)} tone="text-rose-300" note="Creation time precedes reading time" />
          </section>

          <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 xl:col-span-2">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-100">{period[0].toUpperCase() + period.slice(1)} trend</h2>
                  <p className="mt-1 text-[11px] text-slate-500">Record totals and {data.daily_trends?.[0]?.metric_label || 'approved module metric'}</p>
                </div>
                <Activity className="h-4 w-4 text-emerald-300" />
              </div>
              {chartRows.length === 0 ? (
                <div className="grid h-64 place-items-center text-sm text-slate-500">No trend rows for the selected range.</div>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={chartRows} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#263246" />
                    <XAxis dataKey="period" stroke="#94a3b8" tick={{ fontSize: 10 }} minTickGap={20} />
                    <YAxis yAxisId="records" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="metric" orientation="right" stroke="#34d399" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 12, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar yAxisId="records" dataKey="valid_records" name="VALID" stackId="quality" fill="#10b981" />
                    <Bar yAxisId="records" dataKey="exception_records" name="EXCEPTION" stackId="quality" fill="#f59e0b" />
                    <Line yAxisId="metric" type="monotone" dataKey="metric_value" name={chartRows[0]?.metric_label || 'Module metric'} stroke="#38bdf8" strokeWidth={2} dot={false} connectNulls />
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h2 className="text-sm font-bold text-slate-100">Night-entry indicators</h2>
              <p className="mt-1 text-[11px] text-slate-500">22:00 inclusive · 06:00 exclusive · Asia/Kolkata</p>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between rounded-xl bg-slate-950/70 p-3">
                  <span className="flex items-center gap-2 text-xs text-slate-300"><Clock3 className="h-4 w-4 text-sky-300" />Reading time at night</span>
                  <strong className="text-sm text-sky-200">{formatNumber(summary.night_reading_count, 0)}</strong>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-950/70 p-3">
                  <span className="flex items-center gap-2 text-xs text-slate-300"><Moon className="h-4 w-4 text-indigo-300" />Entry time at night</span>
                  <strong className="text-sm text-indigo-200">{formatNumber(summary.night_entry_count, 0)}</strong>
                </div>
                <div className="flex items-start gap-2 rounded-xl border border-slate-800 p-3 text-[11px] leading-5 text-slate-400">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                  Indicators only. Night time does not change VALID/EXCEPTION or delayed-entry classification.
                </div>
              </div>
            </div>
          </section>

          <TableFrame title="Latest reading by asset" note="Latest available row per asset; timestamp is independent of the selected trend range." count={latestReadings.length}>
            {latestReadings.length === 0 ? <p className="p-5 text-sm text-slate-500">No assets returned by the latest-reading view.</p> : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[820px] text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/80 text-[10px] uppercase tracking-wider text-slate-400">
                    <tr><th className="px-4 py-3">Plaza</th><th className="px-4 py-3">Asset</th><th className="px-4 py-3">Latest reading</th><th className="px-4 py-3">Reading value</th><th className="px-4 py-3">Cumulative runtime</th><th className="px-4 py-3">Entered by</th><th className="px-4 py-3">Source quality</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {latestReadings.map((row: any, index: number) => {
                      const value = row.latest_cumulative_kwh ?? row.latest_output_voltage ?? row.latest_battery_vdc ?? row.latest_interval_kwh;
                      const unit = row.latest_cumulative_kwh != null || row.latest_interval_kwh != null ? 'kWh' : row.latest_output_voltage != null ? 'V' : row.latest_battery_vdc != null ? 'VDC' : '';
                      return (
                        <tr key={row.reading_id || row.asset_id || index} className="hover:bg-slate-800/40">
                          <td className="px-4 py-3 font-bold text-slate-100">{row.plaza_id || '—'}</td>
                          <td className="px-4 py-3"><div className="font-bold text-emerald-300">{row.asset_code || '—'}</div><div className="mt-0.5 text-[10px] text-slate-500">{row.asset_name || '—'}</div></td>
                          <td className="px-4 py-3">{dateTime(row.reading_datetime)}</td>
                          <td className="px-4 py-3 font-semibold text-slate-100">{value == null ? '—' : formatNumber(value) + (unit ? ' ' + unit : '')}</td>
                          <td className="px-4 py-3 font-mono text-sky-300">{row.cumulative_running_hours_hh_mm || '—'}</td>
                          <td className="px-4 py-3">{row.created_by || 'Unassigned'}</td>
                          <td className="px-4 py-3"><StatusPill value={row.source_data_quality_status} /></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </TableFrame>

          <TableFrame title="Night-flagged readings and entries" note="Reading and creation timestamps are classified independently." count={nightEntries.length}>
            {nightEntries.length === 0 ? <p className="p-5 text-sm text-slate-500">No night indicators in the selected range.</p> : (
              <div className="max-h-[380px] overflow-auto">
                <table className="w-full min-w-[900px] text-left text-xs text-slate-300">
                  <thead className="sticky top-0 bg-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                    <tr><th className="px-4 py-3">Plaza</th><th className="px-4 py-3">Asset</th><th className="px-4 py-3">Reading time</th><th className="px-4 py-3">Created on</th><th className="px-4 py-3">Delay</th><th className="px-4 py-3">Reading night</th><th className="px-4 py-3">Entry night</th><th className="px-4 py-3">Quality</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {nightEntries.slice(0, 250).map((row: any, index: number) => (
                      <tr key={row.reading_id || index}>
                        <td className="px-4 py-3">{row.plaza_id || '—'}</td>
                        <td className="px-4 py-3 font-semibold text-sky-300">{row.asset_code || '—'}</td>
                        <td className="px-4 py-3">{dateTime(row.reading_datetime)}</td>
                        <td className="px-4 py-3">{dateTime(row.created_on)}</td>
                        <td className="px-4 py-3">{row.entry_delay_hours == null ? '—' : formatNumber(row.entry_delay_hours) + ' h'}</td>
                        <td className="px-4 py-3">{row.reading_datetime_night_indicator === true ? 'Yes' : 'No'}</td>
                        <td className="px-4 py-3">{row.created_on_night_indicator === true ? 'Yes' : row.created_on_night_indicator === false ? 'No' : '—'}</td>
                        <td className="px-4 py-3"><StatusPill value={row.analytics_quality_class} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </TableFrame>

          <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <TableFrame title="Exception register" note="Current EXCEPTION readings and their SQL rule reasons." count={exceptions.length}>
              {exceptions.length === 0 ? <p className="p-5 text-sm text-slate-500">No exceptions in the selected range.</p> : (
                <div className="max-h-[360px] overflow-auto">
                  <table className="w-full min-w-[650px] text-left text-xs text-slate-300">
                    <thead className="sticky top-0 bg-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                      <tr><th className="px-4 py-3">Reading</th><th className="px-4 py-3">Asset</th><th className="px-4 py-3">Reason</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {exceptions.map((row: any, index: number) => (
                        <tr key={row.reading_id || index}>
                          <td className="px-4 py-3">{dateTime(row.reading_datetime)}</td>
                          <td className="px-4 py-3 font-semibold text-amber-300">{row.asset_code || '—'}</td>
                          <td className="px-4 py-3 whitespace-normal">{row.analytics_exception_reasons || 'Source record classified as EXCEPTION'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TableFrame>

            <TableFrame title="Correction audit" note={data.correction_audit_available
              ? 'Recorded correction events for the selected module and plaza/date scope.'
              : 'Optional audit source or view is not available; correction events are not inferred.'}
              count={corrections.length}>
              {!data.correction_audit_available ? (
                <div className="flex items-start gap-2 p-5 text-sm text-slate-400">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
                  The correction audit view is optional and is skipped when its audit table or columns are absent.
                </div>
              ) : corrections.length === 0 ? (
                <p className="p-5 text-sm text-slate-500">No correction events in the selected range.</p>
              ) : (
                <div className="max-h-[360px] overflow-auto">
                  <table className="w-full min-w-[700px] text-left text-xs text-slate-300">
                    <thead className="sticky top-0 bg-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                      <tr><th className="px-4 py-3">Audit time</th><th className="px-4 py-3">Actor</th><th className="px-4 py-3">Asset</th><th className="px-4 py-3">Action</th><th className="px-4 py-3">Reason</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {corrections.map((row: any, index: number) => (
                        <tr key={row.audit_id || index}>
                          <td className="px-4 py-3">{dateTime(row.audit_timestamp)}</td>
                          <td className="px-4 py-3">{row.actor_user_id || '—'}</td>
                          <td className="px-4 py-3 font-semibold text-sky-300">{row.asset_code || '—'}</td>
                          <td className="px-4 py-3">{row.action || '—'}</td>
                          <td className="px-4 py-3 whitespace-normal">{row.reason || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TableFrame>

            <TableFrame title="Technician night-entry summary" note="Grouped from the selected entry-audit rows." count={technicians.length}>
              {technicians.length === 0 ? <p className="p-5 text-sm text-slate-500">No technician submissions in the selected range.</p> : (
                <div className="max-h-[360px] overflow-auto">
                  <table className="w-full min-w-[520px] text-left text-xs text-slate-300">
                    <thead className="sticky top-0 bg-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                      <tr><th className="px-4 py-3">Technician</th><th className="px-4 py-3">Records</th><th className="px-4 py-3">VALID</th><th className="px-4 py-3">EXCEPTION</th><th className="px-4 py-3">Night entries</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {technicians.slice(0, 30).map((row: any) => (
                        <tr key={row.technician_name}>
                          <td className="px-4 py-3 font-semibold text-slate-100">{row.technician_name}</td>
                          <td className="px-4 py-3">{formatNumber(row.total_records, 0)}</td>
                          <td className="px-4 py-3 text-emerald-300">{formatNumber(row.valid_records, 0)}</td>
                          <td className="px-4 py-3 text-amber-300">{formatNumber(row.exception_records, 0)}</td>
                          <td className="px-4 py-3 text-sky-300">{formatNumber(row.night_entry_count, 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </TableFrame>
          </section>

          {data?.limits?.summary_truncated && (
            <p className="text-[11px] text-amber-300">The SQL summary result reached the API safety limit. Narrow the date range to see complete totals.</p>
          )}
          {data?.limits?.entry_audit_truncated && (
            <p className="text-[11px] text-amber-300">Entry detail is capped at the latest 10,000 rows; summary KPI counts still use the SQL daily views.</p>
          )}
        </>
      )}

      {loading && data && (
        <div className="flex items-center gap-2 text-xs text-slate-500"><RefreshCw className="h-3.5 w-3.5 animate-spin" />Updating selected filters…</div>
      )}
    </main>
  );
};