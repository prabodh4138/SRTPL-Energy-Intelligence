import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Moon,
  Clock,
  ShieldCheck,
  Building2,
  Users,
  Layers,
  Download,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { api } from '../api';

export const ForensicAnalyticsView: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<
    'scorecard' | 'technicians' | 'wrong_entries' | 'asset_readings' | 'master_data'
  >('scorecard');

  // Filters
  const [plazaFilter, setPlazaFilter] = useState<string>('ALL');
  const [techSearch, setTechSearch] = useState<string>('');
  const [moduleFilter, setModuleFilter] = useState<string>('ALL');

  const loadData = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getForensicSummary(forceRefresh);
      if (res && res.data) {
        setData(res.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch forensic analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
        <p className="text-sm">Running forensic evaluation on 15,199 telemetry records & SQL views...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800 text-rose-300 space-y-3">
        <div className="flex items-center gap-2 font-bold text-rose-400">
          <AlertTriangle className="w-5 h-5" />
          <span>Forensic Analytics Error</span>
        </div>
        <p className="text-xs">{error}</p>
        <button
          onClick={() => loadData(true)}
          className="px-3 py-1.5 rounded-lg bg-rose-800 hover:bg-rose-700 text-xs font-semibold text-white transition"
        >
          Retry Forensic Evaluation
        </button>
      </div>
    );
  }

  const scorecard = data?.plaza_neglect_scorecard || [];
  const techs = data?.technician_performance_register || [];
  const lastReadings = data?.asset_last_readings || [];
  const wrongEntries = data?.sample_wrong_entries || [];
  const nightEntries = data?.sample_night_entries || [];
  const totalRecords = data?.total_records_analyzed || 15199;

  const totalDefects = scorecard.reduce((sum: number, p: any) => sum + (p.wrong_entries_count || 0), 0);
  const totalNight = scorecard.reduce((sum: number, p: any) => sum + (p.night_entries_count || 0), 0);
  const nightPct = totalRecords > 0 ? ((totalNight / totalRecords) * 100).toFixed(1) : '0';

  // Filtered techs
  const filteredTechs = techs.filter((t: any) => {
    const matchPlaza = plazaFilter === 'ALL' || t.assigned_plazas?.includes(plazaFilter);
    const matchSearch =
      !techSearch || t.technician_name?.toLowerCase().includes(techSearch.toLowerCase());
    return matchPlaza && matchSearch;
  });

  // Filtered wrong entries
  const filteredWrong = wrongEntries.filter((w: any) => {
    return moduleFilter === 'ALL' || w.module?.toUpperCase() === moduleFilter.toUpperCase();
  });

  const exportScorecardCsv = () => {
    if (!scorecard.length) return;
    const headers = ['Rank', 'Plaza', 'Total Logs', 'Defects', 'Defect %', 'Night Logs', 'Night %', 'Severe Delays', 'Forensic Summary'];
    const rows = scorecard.map((p: any) => [
      p.rank,
      p.plaza_id,
      p.total_records,
      p.wrong_entries_count,
      `${p.defect_rate_pct}%`,
      p.night_entries_count,
      `${p.night_entry_pct}%`,
      p.severe_delays_count,
      `"${p.forensic_summary?.replace(/"/g, '""') || ''}"`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r: any) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `SRTPL_Plaza_Neglect_Scorecard_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Eyebrow & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            Module 7 · Forensic Telemetry & Compliance Audit
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mt-1">
            Forensic Energy Analytics & Operator Audit
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Auditing 15,199 raw telemetry logs across 21 JUNO files, PostgreSQL <code className="text-amber-300">energy_analytics</code> views, and corrected Supabase master records.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadData(true)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Audit
          </button>
          <button
            onClick={exportScorecardCsv}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-xs font-semibold text-white shadow-lg shadow-emerald-950/40 transition"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>
        </div>
      </div>

      {/* 4 KPI Banner Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Total Telemetry Parsed</span>
            <Layers className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-black text-slate-100">{totalRecords.toLocaleString()}</div>
          <p className="text-[11px] text-slate-400 mt-1">Across EB, DG, Solar, TRF, UPS (21 raw logs)</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/80 border border-rose-900/40 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Wrong / Defective Entries</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-rose-400">{totalDefects.toLocaleString()}</div>
          <p className="text-[11px] text-rose-300/80 mt-1">63.7% corridor telemetry defect rate</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/80 border border-amber-900/40 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Night Logs (8 PM – 8 AM)</span>
            <Moon className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400">{totalNight.toLocaleString()}</div>
          <p className="text-[11px] text-amber-300/80 mt-1">{nightPct}% off-hours shift submissions</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/80 border border-purple-900/40 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Neglect Leader</span>
            <Building2 className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xl font-black text-purple-300">TP01 & TP02</div>
          <p className="text-[11px] text-slate-400 mt-1">TP01: 80.8% Err | TP02: Abandoned logs</p>
        </div>
      </div>

      {/* Subtab Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {[
          { key: 'scorecard', label: '🏆 Plaza Neglect Scorecard' },
          { key: 'technicians', label: '👨‍🔧 Technician Night Audit (8p–8a)' },
          { key: 'wrong_entries', label: '⚠️ Wrong Entries Register' },
          { key: 'asset_readings', label: '⚡ Asset-Wise Last Readings' },
          { key: 'master_data', label: '🛠️ Corrected Asset Master' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
              activeTab === tab.key
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-lg shadow-emerald-950/20'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: PLAZA NEGLECT SCORECARD */}
      {activeTab === 'scorecard' && (
        <div className="space-y-5">
          <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 text-emerald-300 text-xs">
            <span className="font-bold">Corridor Neglect Verdict:</span> TP01 has committed the{' '}
            <b>highest wrong entries (80.82% error rate)</b>. TP03 leads in{' '}
            <b>night off-hours submissions (58.96%)</b>. TP02 exhibits{' '}
            <b>severe monitoring abandonment (50% fewer logs, readings delayed up to 40 days, stale DG and EB telemetry)</b>.
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-3 px-4">Rank</th>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Total Logs</th>
                  <th className="py-3 px-4">Wrong Entries</th>
                  <th className="py-3 px-4">Error Rate</th>
                  <th className="py-3 px-4">Night Logs (8p-8a)</th>
                  <th className="py-3 px-4">Night %</th>
                  <th className="py-3 px-4">Severe Delays (&gt;2d)</th>
                  <th className="py-3 px-4">Forensic Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {scorecard.map((p: any) => (
                  <tr key={p.plaza_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-bold text-amber-400">#{p.rank}</td>
                    <td className="py-3 px-4 font-bold text-slate-100">{p.plaza_id}</td>
                    <td className="py-3 px-4">{p.total_records.toLocaleString()}</td>
                    <td className="py-3 px-4 text-rose-400 font-bold">{p.wrong_entries_count.toLocaleString()}</td>
                    <td className="py-3 px-4 text-rose-400 font-bold">{p.defect_rate_pct}%</td>
                    <td className="py-3 px-4 text-amber-400 font-bold">{p.night_entries_count.toLocaleString()}</td>
                    <td className="py-3 px-4 text-amber-400 font-bold">{p.night_entry_pct}%</td>
                    <td className="py-3 px-4 text-purple-400 font-bold">{p.severe_delays_count}</td>
                    <td className="py-3 px-4 font-sans text-xs text-slate-300">{p.forensic_summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div className="p-5 rounded-2xl bg-rose-950/20 border border-rose-800/50 space-y-3">
              <div className="flex items-center gap-2 text-rose-400 font-extrabold text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>RANK #1: TP01 (Max Wrong Entries)</span>
              </div>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4">
                <li><b>5,190 Defect Entries (80.82% error rate)</b></li>
                <li><b>1,332 records</b> with UPS DC bus collapsed to 82.0V – 82.1V</li>
                <li><b>981 records</b> with 463V overvoltage</li>
                <li>EB meter counter drops: 1,380 &rarr; 1,220 &rarr; 1,140 kWh</li>
                <li><b>Zero Transformer Monitoring:</b> 0 logs in JUNO exports!</li>
                <li>Technicians: Chandan Meher, Deepak Behera, Kshirod Khadia, Prabodh Rana, Ranjan Khadia</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-800/50 space-y-3">
              <div className="flex items-center gap-2 text-amber-400 font-extrabold text-sm">
                <Moon className="w-4 h-4" />
                <span>RANK #2: TP03 (Max Night Entries)</span>
              </div>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4">
                <li><b>3,222 Night Logs (58.96%) — Highest Corridor %</b></li>
                <li>Heavy clustering between 21:00–23:45 and 05:00–06:45</li>
                <li><b>1,376 records</b> with DC bus voltage at 82.0V</li>
                <li><b>1,770 records</b> between 463.2V and 464.2V</li>
                <li>DG run hours logged with 0.0 kW active power generation</li>
                <li>Technicians: Krishna Chandra Patra, Pritam Mahapatra, Sanurjya Roudia, Srikant Sunani</li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-purple-950/20 border border-purple-800/50 space-y-3">
              <div className="flex items-center gap-2 text-purple-400 font-extrabold text-sm">
                <Clock className="w-4 h-4" />
                <span>RANK #3: TP02 (Severe Abandonment)</span>
              </div>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4">
                <li><b>Only 3,312 Logs</b> (&sim;50% fewer logs than TP01)</li>
                <li><b>345 severe delays</b> stretching up to <b>40.0 days late</b>!</li>
                <li>Rabi Narayan Singh logged readings 40 days late</li>
                <li>Pritam Mahapatra logged 25.5 days late at 23:11</li>
                <li><b>Abandoned Equipment:</b> DG stopped logging 08-Sep; EB stopped 14-Sep</li>
                <li><b>Zero UPS logs</b> in JUNO exports</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TECHNICIAN NIGHT AUDIT */}
      {activeTab === 'technicians' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={techSearch}
                onChange={(e) => setTechSearch(e.target.value)}
                placeholder="Search technician name (Rabi, Pritam, Prabodh...)"
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 w-full sm:w-64 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-semibold">Filter Plaza:</span>
              {['ALL', 'TP01', 'TP02', 'TP03'].map((plz) => (
                <button
                  key={plz}
                  onClick={() => setPlazaFilter(plz)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                    plazaFilter === plz
                      ? 'bg-emerald-500 text-slate-950 font-bold'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {plz}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-3 px-4">Technician Name</th>
                  <th className="py-3 px-4">Plazas</th>
                  <th className="py-3 px-4">Modules</th>
                  <th className="py-3 px-4">Total Logs</th>
                  <th className="py-3 px-4">Night Logs (8p–8a)</th>
                  <th className="py-3 px-4">Night %</th>
                  <th className="py-3 px-4">Defects</th>
                  <th className="py-3 px-4">Avg Delay</th>
                  <th className="py-3 px-4">Max Delay</th>
                  <th className="py-3 px-4">Compliance Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {filteredTechs.map((t: any) => (
                  <tr key={t.technician_name} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-sans font-bold text-slate-100">{t.technician_name}</td>
                    <td className="py-3 px-4 text-emerald-400">{t.assigned_plazas?.join(', ')}</td>
                    <td className="py-3 px-4 text-slate-400">{t.modules_handled?.join(', ')}</td>
                    <td className="py-3 px-4">{t.total_logs?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-amber-400 font-bold">{t.night_entries_count?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-amber-400 font-bold">{t.night_entry_pct}%</td>
                    <td className="py-3 px-4 text-rose-400 font-bold">{t.defects_count}</td>
                    <td className="py-3 px-4">{t.avg_delay_days}d</td>
                    <td className="py-3 px-4 text-purple-400 font-bold">{t.max_delay_days}d</td>
                    <td className="py-3 px-4 font-sans">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          t.risk_profile?.includes('CRITICAL')
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : t.risk_profile?.includes('DELAY')
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                            : t.risk_profile?.includes('HABITUAL')
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {t.risk_profile}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h4 className="text-sm font-bold text-slate-200 mt-6">Sample Night & Backdated Submissions (8:00 PM – 8:00 AM)</h4>
          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl max-h-72 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 sticky top-0">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Plaza</th>
                  <th className="py-2.5 px-3">Module</th>
                  <th className="py-2.5 px-3">Asset Code</th>
                  <th className="py-2.5 px-3">Technician</th>
                  <th className="py-2.5 px-3">Entry Hour</th>
                  <th className="py-2.5 px-3">Reading Datetime</th>
                  <th className="py-2.5 px-3">Logged Timestamp</th>
                  <th className="py-2.5 px-3">Delay</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
                {nightEntries.slice(0, 20).map((n: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-2 px-3 text-slate-500">{idx + 1}</td>
                    <td className="py-2 px-3 font-bold text-slate-200">{n.plaza_id}</td>
                    <td className="py-2 px-3 text-sky-400">{n.module}</td>
                    <td className="py-2 px-3">{n.asset_code}</td>
                    <td className="py-2 px-3 font-sans font-bold text-emerald-400">{n.technician}</td>
                    <td className="py-2 px-3 text-amber-400 font-bold">{n.hour}:00</td>
                    <td className="py-2 px-3 text-slate-400">{n.reading_datetime}</td>
                    <td className="py-2 px-3 text-slate-400">{n.created_on}</td>
                    <td className="py-2 px-3 text-purple-400 font-bold">{n.delay_days} days</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: WRONG ENTRIES REGISTER */}
      {activeTab === 'wrong_entries' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 font-semibold">Filter Module:</span>
            {['ALL', 'EB', 'DG', 'Solar', 'Transformer', 'UPS'].map((m) => (
              <button
                key={m}
                onClick={() => setModuleFilter(m)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  moduleFilter === m
                    ? 'bg-rose-500 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl max-h-96 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 sticky top-0">
                <tr>
                  <th className="py-3 px-4">#</th>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Module</th>
                  <th className="py-3 px-4">Asset Code</th>
                  <th className="py-3 px-4">Technician</th>
                  <th className="py-3 px-4">Reading Datetime</th>
                  <th className="py-3 px-4">Defect / Anomaly Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono text-xs">
                {filteredWrong.slice(0, 30).map((w: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 text-slate-500">{idx + 1}</td>
                    <td className="py-2.5 px-4 font-bold text-slate-200">{w.plaza_id}</td>
                    <td className="py-2.5 px-4 text-sky-400 font-bold">{w.module}</td>
                    <td className="py-2.5 px-4">{w.asset_code}</td>
                    <td className="py-2.5 px-4 font-sans text-emerald-400 font-semibold">{w.technician}</td>
                    <td className="py-2.5 px-4 text-slate-400">{w.reading_datetime}</td>
                    <td className="py-2.5 px-4 text-rose-300 font-sans font-semibold">{w.violation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: ASSET-WISE LAST READINGS */}
      {activeTab === 'asset_readings' && (
        <div className="space-y-4">
          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Module</th>
                  <th className="py-3 px-4">Asset Code</th>
                  <th className="py-3 px-4">Last Reading Datetime</th>
                  <th className="py-3 px-4">Cumulative kWh</th>
                  <th className="py-3 px-4">Responsible Technician</th>
                  <th className="py-3 px-4">Submission Timestamp</th>
                  <th className="py-3 px-4">Monitoring Health Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono text-xs">
                {lastReadings.map((r: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-bold text-slate-100">{r.plaza_id}</td>
                    <td className="py-3 px-4 font-bold text-sky-400">{r.module}</td>
                    <td className="py-3 px-4">{r.asset_code}</td>
                    <td className="py-3 px-4 text-slate-200">{r.reading_datetime}</td>
                    <td className="py-3 px-4 font-bold text-emerald-400">
                      {r.cumulative_kwh != null ? `${r.cumulative_kwh.toLocaleString()} kWh` : 'Active'}
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-300 font-semibold">{r.technician}</td>
                    <td className="py-3 px-4 text-slate-500">{r.created_on || 'N/A'}</td>
                    <td className="py-3 px-4 font-sans">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.monitoring_status?.includes('STALE')
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : r.monitoring_status?.includes('UNMONITORED')
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {r.monitoring_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: CORRECTED ASSET MASTER DATA */}
      {activeTab === 'master_data' && (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-sky-950/20 border border-sky-800/40 text-sky-300 text-xs">
            <span className="font-bold">Corrected Supabase Master Data:</span> Solar capacity is{' '}
            <b>40.46 kWp per plant (121.38 kWp corridor total)</b>. Transformers are verified at{' '}
            <b>TP02 (TRF-01/TP-02)</b> and <b>TP03 (TRF-01/TP-03)</b>. UPS is mapped to{' '}
            <b>TP01 (UPS-04/TP-01)</b> and <b>TP03 (UPS-01/TP-03)</b>.
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-3 px-4">Asset Code</th>
                  <th className="py-3 px-4">Asset Name</th>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Module</th>
                  <th className="py-3 px-4">Capacity Rating</th>
                  <th className="py-3 px-4">Correction Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono text-xs">
                {[
                  { code: 'SR-E-AP-SPX-000001', name: 'Rooftop Solar Plant TP01', plaza: 'TP01', mod: 'SOLAR', cap: '40.46 kWp', note: 'Corrected to kWp (Total Corridor: 121.38 kWp)' },
                  { code: 'SR-E-AP-SPX-000002', name: 'Rooftop Solar Plant TP02', plaza: 'TP02', mod: 'SOLAR', cap: '40.46 kWp', note: 'Corrected to kWp (Total Corridor: 121.38 kWp)' },
                  { code: 'SR-E-AP-SPX-000003', name: 'Rooftop Solar Plant TP03', plaza: 'TP03', mod: 'SOLAR', cap: '40.46 kWp', note: 'Corrected to kWp (Total Corridor: 121.38 kWp)' },
                  { code: 'SR-E-HT-TFR-000001', name: 'HT Substation Transformer TP01', plaza: 'TP01', mod: 'TRANSFORMER', cap: '500 kVA', note: 'TP01 Incomer' },
                  { code: 'SR-E-HT-TFR-000002', name: 'HT Substation Transformer TP02', plaza: 'TP02', mod: 'TRANSFORMER', cap: '500 kVA', note: 'Remapped to TP02 (Tag: TRF-01/TP-02)' },
                  { code: 'SR-E-HT-TFR-000003', name: 'HT Substation Transformer TP03', plaza: 'TP03', mod: 'TRANSFORMER', cap: '500 kVA', note: 'Remapped to TP03 (Tag: TRF-01/TP-03)' },
                  { code: 'SR-E-AP-UPS-000004', name: 'Main Toll Plaza UPS 4', plaza: 'TP01', mod: 'UPS', cap: '40 kVA', note: 'Remapped to TP01 (Tag: UPS-04/TP-01)' },
                  { code: 'SR-E-AP-UPS-000009', name: 'Main Toll Plaza UPS 9', plaza: 'TP03', mod: 'UPS', cap: '40 kVA', note: 'Remapped to TP03 (Tag: UPS-01/TP-03)' },
                ].map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-bold text-slate-100">{row.code}</td>
                    <td className="py-3 px-4 font-sans">{row.name}</td>
                    <td className="py-3 px-4 font-bold text-emerald-400">{row.plaza}</td>
                    <td className="py-3 px-4 text-sky-400">{row.mod}</td>
                    <td className="py-3 px-4 font-bold text-amber-400">{row.cap}</td>
                    <td className="py-3 px-4 font-sans text-slate-400 text-[11px]">{row.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
