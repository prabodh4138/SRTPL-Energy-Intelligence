import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Zap, Sun, BatteryCharging, Power, Plus, ShieldCheck } from 'lucide-react';

const TABS = [
  { id: 'eb', label: 'EB Grid Reading', icon: Zap },
  { id: 'dg', label: 'DG Generator', icon: Power },
  { id: 'solar', label: 'Solar Rooftop', icon: Sun },
  { id: 'transformer', label: 'Transformers', icon: Zap },
  { id: 'ups', label: 'UPS Systems', icon: BatteryCharging },
];

export const ReadingView: React.FC = () => {
  const [activeTab, setActiveTab] = useState('eb');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Manual entry modal state
  const [showModal, setShowModal] = useState(false);
  const [meterCode, setMeterCode] = useState('');
  const [plaza, setPlaza] = useState('TP01');
  const [readingVal, setReadingVal] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchTab = async (t: string) => {
    setLoading(true);
    try {
      const res = await api.getReadings(t);
      setData(res);
      if (res.records?.[0]?.meter_code) {
        setMeterCode(res.records[0].meter_code);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTab(activeTab);
  }, [activeTab]);

  const handleAddReading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!readingVal) return;
    setSubmitting(true);
    try {
      await api.addReading(activeTab, {
        meter_code: meterCode || `${activeTab.toUpperCase()}-METER-01`,
        plaza,
        reading_value: parseFloat(readingVal),
        notes,
      });
      setShowModal(false);
      setReadingVal('');
      setNotes('');
      fetchTab(activeTab);
    } catch (err) {
      alert('Error adding reading: ' + err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Subtab selection */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center p-1.5 rounded-2xl bg-slate-900 border border-slate-800">
          {TABS.map((t) => {
            const Icon = t.icon;
            const isSel = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
                  isSel
                    ? 'bg-emerald-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {t.label}
              </button>
            );
          })}
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition"
        >
          <Plus className="w-4 h-4" />
          Log Manual Reading
        </button>
      </div>

      {/* Equipment Header & Live KPIs */}
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(data.kpis || []).map((k: any, i: number) => (
              <div key={i} className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
                <span className="text-xs font-medium text-slate-400">{k.label}</span>
                <div className="text-xl font-bold text-slate-100 mt-1.5">{k.value}</div>
                <div className="text-[11px] text-emerald-400/90 mt-1">{k.sub}</div>
              </div>
            ))}
          </div>

          {/* Governing Rules */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-semibold text-slate-200">Equipment Governing Validation Protocols</div>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                {(data.rules || []).map((r: string, idx: number) => (
                  <li key={idx} className="text-[11px] text-slate-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Reading Records Table */}
          <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200">Recent Validated Meter Logs</h3>
              <span className="text-xs text-slate-400">{data.records?.length || 0} records available</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-3">Entry ID</th>
                    <th className="px-6 py-3">Meter Asset</th>
                    <th className="px-6 py-3">Plaza</th>
                    <th className="px-6 py-3">Log Date</th>
                    <th className="px-6 py-3">Reading (kWh / Units)</th>
                    <th className="px-6 py-3">Interval Delta</th>
                    <th className="px-6 py-3">Audit Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {(data.records || []).map((row: any) => (
                    <tr key={row.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-6 py-3 font-semibold text-emerald-400">{row.id}</td>
                      <td className="px-6 py-3 text-slate-300">{row.meter_code}</td>
                      <td className="px-6 py-3">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-sky-400 text-[10px]">
                          {row.plaza}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-slate-400">{row.date}</td>
                      <td className="px-6 py-3 text-slate-100 font-bold">{row.curr_kwh?.toLocaleString()}</td>
                      <td className="px-6 py-3 text-emerald-400 font-semibold">
                        {row.diff_kwh ? `+${row.diff_kwh.toLocaleString()}` : '—'}
                      </td>
                      <td className="px-6 py-3">
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
                          VALID ✓
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Manual Reading Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100">Log Manual Meter Reading</h3>
            <p className="text-xs text-slate-400 mt-1">Submit reading directly into validation pipeline.</p>

            <form onSubmit={handleAddReading} className="space-y-4 mt-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Meter Code / Feeder ID</label>
                <input
                  type="text"
                  value={meterCode}
                  onChange={(e) => setMeterCode(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Toll Plaza</label>
                  <select
                    value={plaza}
                    onChange={(e) => setPlaza(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 outline-none"
                  >
                    <option value="TP01">TP01 · Km 24+500</option>
                    <option value="TP02">TP02 · Km 68+200</option>
                    <option value="TP03">TP03 · Km 112+800</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Reading Value</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="e.g. 142850"
                    value={readingVal}
                    onChange={(e) => setReadingVal(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 outline-none focus:border-emerald-500 font-mono"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Operator Notes</label>
                <input
                  type="text"
                  placeholder="Routine morning check..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition"
                >
                  {submitting ? 'Verifying...' : 'Submit & Validate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
