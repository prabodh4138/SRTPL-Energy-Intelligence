import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Zap,
  Flame,
  Sun,
  Cpu,
  BatteryCharging,
  Search,
  Filter,
  Plus,
  Edit3,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  X,
  RefreshCw,
} from 'lucide-react';

type EquipmentType = 'eb' | 'dg' | 'solar' | 'transformer' | 'ups';

const EQUIPMENT_TABS: { id: EquipmentType; label: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'eb', label: 'EB Grid Supply', icon: Zap },
  { id: 'dg', label: 'Diesel Generator (DG)', icon: Flame },
  { id: 'solar', label: 'Solar Generation', icon: Sun },
  { id: 'transformer', label: 'Transformers', icon: Cpu },
  { id: 'ups', label: 'UPS Systems', icon: BatteryCharging },
];

export const EnergyReadingsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<EquipmentType>('eb');
  const [plazaFilter, setPlazaFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [readings, setReadings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Correction Modal State
  const [correctModalOpen, setCorrectModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [proposedValue, setProposedValue] = useState<number | ''>('');
  const [correctionReason, setCorrectionReason] = useState('');
  const [correctionField, setCorrectionField] = useState('cumulative_kwh');
  const [submittingCorrection, setSubmittingCorrection] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Manual Entry Modal State
  const [entryModalOpen, setEntryModalOpen] = useState(false);
  const [newAssetCode, setNewAssetCode] = useState('');
  const [newPlazaId, setNewPlazaId] = useState('TP01');
  const [newReadingDatetime, setNewReadingDatetime] = useState(new Date().toISOString().slice(0, 19).replace('T', ' '));
  const [newCumValue, setNewCumValue] = useState<number | ''>('');
  const [newIntervalValue, setNewIntervalValue] = useState<number | ''>('');
  const [newNotes, setNewNotes] = useState('');
  const [submittingEntry, setSubmittingEntry] = useState(false);

  const fetchReadings = async () => {
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await api.getEnergyReadings(activeTab, plazaFilter, statusFilter);
      setReadings(res.records || []);
    } catch (err) {
      console.error(err);
      setActionMessage({ type: 'error', text: 'Failed to fetch energy readings' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReadings();
  }, [activeTab, plazaFilter, statusFilter]);

  // Open correction modal
  const handleOpenCorrection = (r: any) => {
    setSelectedRecord(r);
    const field = activeTab === 'ups' ? 'battery_vdc' : 'cumulative_kwh';
    setCorrectionField(field);
    const currentVal = r[field] !== undefined && r[field] !== null ? r[field] : 0;
    setProposedValue(currentVal);
    setCorrectionReason('');
    setCorrectModalOpen(true);
  };

  // Submit correction
  const handleConfirmCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecord || proposedValue === '' || !correctionReason.trim()) {
      alert('Please enter a proposed value and a mandatory justification reason.');
      return;
    }
    setSubmittingCorrection(true);
    try {
      const origVal = Number(selectedRecord[correctionField] || 0);
      const res = await api.correctEnergyReading({
        reading_id: selectedRecord.reading_id || selectedRecord.id,
        module: activeTab,
        asset_code: selectedRecord.asset_code || selectedRecord.asset_id,
        plaza_id: selectedRecord.plaza_id || selectedRecord.plaza || 'TP01',
        field_name: correctionField,
        original_value: origVal,
        proposed_value: Number(proposedValue),
        reason: correctionReason.trim(),
        actor: 'admin@srtpl.com',
      });
      setActionMessage({ type: 'success', text: res.message || 'Correction successfully recorded and audited.' });
      setCorrectModalOpen(false);
      fetchReadings();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Correction failed' });
    } finally {
      setSubmittingCorrection(false);
    }
  };

  // Submit manual entry
  const handleConfirmEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAssetCode || newCumValue === '') {
      alert('Please specify an asset code and cumulative reading value.');
      return;
    }
    setSubmittingEntry(true);
    try {
      const res = await api.addEnergyReading({
        module: activeTab,
        asset_code: newAssetCode.trim(),
        plaza_id: newPlazaId,
        reading_datetime: newReadingDatetime,
        cumulative_value: Number(newCumValue),
        interval_value: newIntervalValue === '' ? 0 : Number(newIntervalValue),
        notes: newNotes,
        actor: 'admin@srtpl.com',
      });
      setActionMessage({ type: 'success', text: res.message || 'Reading entry recorded and audited.' });
      setEntryModalOpen(false);
      fetchReadings();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Reading entry failed' });
    } finally {
      setSubmittingEntry(false);
    }
  };

  // Filter records by search
  const filteredReadings = readings.filter((r) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return (
      (r.asset_code && String(r.asset_code).toLowerCase().includes(s)) ||
      (r.reading_id && String(r.reading_id).toLowerCase().includes(s)) ||
      (r.remarks && String(r.remarks).toLowerCase().includes(s))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header and Equipment Tabs */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Zap className="w-5 h-5 text-emerald-400" />
              <span>Energy Readings & Asset Monitoring</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Search, filter, view status, and perform controlled readings entry with full audit retention.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setEntryModalOpen(true)}
              className="py-2 px-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition flex items-center gap-1.5 shadow-md shadow-emerald-950/40"
            >
              <Plus className="w-4 h-4" />
              <span>Add Controlled Reading</span>
            </button>
          </div>
        </div>

        {/* Equipment Selector Tabs */}
        <div className="mt-5 flex flex-wrap gap-2 pt-4 border-t border-slate-800">
          {EQUIPMENT_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-slate-800 text-emerald-400 border border-emerald-500/40 shadow-sm'
                    : 'bg-slate-950/40 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Action Notification Message */}
      {actionMessage && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-medium ${
            actionMessage.type === 'success'
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionMessage.text}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="p-1 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filters & Search Toolbar */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[240px] max-w-md bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by asset code, reading ID, remarks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-slate-200 outline-none w-full text-xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Plaza Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400 font-medium">Plaza:</span>
            <select
              value={plazaFilter}
              onChange={(e) => setPlazaFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer font-mono"
            >
              <option value="ALL" className="bg-slate-800">ALL Plazas</option>
              <option value="TP01" className="bg-slate-800">TP01</option>
              <option value="TP02" className="bg-slate-800">TP02</option>
              <option value="TP03" className="bg-slate-800">TP03</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400 font-medium">Quality Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Statuses</option>
              <option value="CONFIRMED" className="bg-slate-800">CONFIRMED</option>
              <option value="UNVERIFIED" className="bg-slate-800">UNVERIFIED</option>
              <option value="EXCLUDED" className="bg-slate-800">EXCLUDED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Readings Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            {activeTab.toUpperCase()} Readings Register ({filteredReadings.length} records)
          </span>
          <span className="text-[11px] text-slate-500">
            Click 'Correct' to compare original and propose values with audit reason
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-400 mb-2" />
            Loading {activeTab.toUpperCase()} records...
          </div>
        ) : filteredReadings.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No readings found for the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 font-medium border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Reading ID</th>
                  <th className="py-3 px-4">Asset Code</th>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Timestamp (IST)</th>
                  <th className="py-3 px-4 text-right">Cumulative Value</th>
                  <th className="py-3 px-4 text-right">Interval Delta</th>
                  <th className="py-3 px-4 text-center">Quality Status</th>
                  <th className="py-3 px-4">Audit Remarks</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredReadings.map((r, idx) => {
                  const cum =
                    r.cumulative_kwh !== undefined && r.cumulative_kwh !== null
                      ? r.cumulative_kwh
                      : r.curr_kwh || r.battery_vdc || 0;
                  const intVal =
                    r.interval_kwh !== undefined && r.interval_kwh !== null
                      ? r.interval_kwh
                      : r.diff_kwh !== undefined
                      ? r.diff_kwh
                      : null;
                  const qStatus = r.data_quality_status || r.status || 'CONFIRMED';
                  const plz = r.plaza_id || r.plaza || 'TP01';

                  return (
                    <tr key={r.reading_id || r.id || idx} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono font-medium text-slate-300">
                        {r.reading_id || r.id}
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-emerald-400">
                        {r.asset_code || r.asset_id}
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]">
                          {plz}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {r.reading_datetime || r.date || '—'}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-100">
                        {Number(cum).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-medium">
                        {intVal !== null && intVal !== undefined ? (
                          <span className="text-emerald-400">+{Number(intVal).toFixed(1)}</span>
                        ) : (
                          <span className="text-slate-500 italic">NULL (First Rdg)</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            qStatus === 'CONFIRMED' || qStatus === 'VALID'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : qStatus === 'UNVERIFIED'
                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {qStatus}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 max-w-xs truncate text-[11px]" title={r.remarks || r.notes || ''}>
                        {r.remarks || r.notes || '—'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenCorrection(r)}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center gap-1 ml-auto border border-slate-700"
                        >
                          <Edit3 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Correct</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Correction Workflow Modal (Section 7: Search reading -> compare original and proposed values -> enter mandatory reason -> confirm -> backend records timestamp, actor, old/new values. No automatic correction.) */}
      {correctModalOpen && selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">Controlled Reading Correction</h3>
              </div>
              <button
                onClick={() => setCorrectModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleConfirmCorrection} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Reading ID:</span>
                  <span className="font-mono font-bold text-slate-200">{selectedRecord.reading_id || selectedRecord.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Asset Code:</span>
                  <span className="font-mono font-bold text-emerald-400">{selectedRecord.asset_code || selectedRecord.asset_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Plaza ID:</span>
                  <span className="font-mono text-slate-200">{selectedRecord.plaza_id || selectedRecord.plaza || 'TP01'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Timestamp:</span>
                  <span className="font-mono text-slate-300">{selectedRecord.reading_datetime || selectedRecord.date}</span>
                </div>
              </div>

              {/* Comparison Box */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Original Recorded Value</span>
                  <div className="text-lg font-mono font-bold text-slate-300">
                    {Number(selectedRecord[correctionField] || 0).toLocaleString('en-US', { minimumFractionDigits: 1 })}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">{correctionField}</span>
                </div>

                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/40">
                  <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">Proposed Corrected Value</span>
                  <input
                    type="number"
                    step="any"
                    required
                    value={proposedValue}
                    onChange={(e) => setProposedValue(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full bg-slate-900 border border-emerald-500/50 rounded-lg px-2.5 py-1 text-base font-mono font-bold text-emerald-300 outline-none"
                  />
                  <span className="text-[10px] text-emerald-500 font-mono">No automatic overwrite</span>
                </div>
              </div>

              {/* Mandatory Justification Reason */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Mandatory Justification Reason <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Enter explicit operational/calibration justification (mandatory for audit)..."
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 p-2.5 text-slate-200 outline-none focus:border-emerald-500 text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setCorrectModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCorrection}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition flex items-center gap-1.5"
                >
                  {submittingCorrection ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Confirm & Log Audit</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manual Reading Entry Modal */}
      {entryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">Add Controlled Reading ({activeTab.toUpperCase()})</h3>
              </div>
              <button
                onClick={() => setEntryModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleConfirmEntry} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Asset Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SR-E-EM-EB-000TP01"
                    value={newAssetCode}
                    onChange={(e) => setNewAssetCode(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Plaza ID *</label>
                  <select
                    value={newPlazaId}
                    onChange={(e) => setNewPlazaId(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono cursor-pointer"
                  >
                    <option value="TP01">TP01</option>
                    <option value="TP02">TP02</option>
                    <option value="TP03">TP03</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Reading Datetime (IST) *</label>
                <input
                  type="text"
                  required
                  value={newReadingDatetime}
                  onChange={(e) => setNewReadingDatetime(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Cumulative Value *</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="e.g. 92620.0"
                    value={newCumValue}
                    onChange={(e) => setNewCumValue(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Interval Delta</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="e.g. 14.2"
                    value={newIntervalValue}
                    onChange={(e) => setNewIntervalValue(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Operator Notes</label>
                <input
                  type="text"
                  placeholder="Optional log remarks"
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEntryModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingEntry}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition flex items-center gap-1.5"
                >
                  {submittingEntry ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Save Reading</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
