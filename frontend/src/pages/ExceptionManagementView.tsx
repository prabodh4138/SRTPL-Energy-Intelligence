import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Filter,
  Search,
  Eye,
  Check,
  Edit3,
  Clock,
  Layers,
  Flame,
  Cpu,
  Zap,
  Sun,
  X,
  RefreshCw,
} from 'lucide-react';

export const ExceptionManagementView: React.FC = () => {
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [plazaFilter, setPlazaFilter] = useState('ALL');
  const [moduleFilter, setModuleFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  // Disposition Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedException, setSelectedException] = useState<any | null>(null);
  const [actionType, setActionType] = useState('MARK_REVIEWED');
  const [reason, setReason] = useState('');
  const [proposedValue, setProposedValue] = useState<number | ''>('');
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchExceptions = async () => {
    setLoading(true);
    setNotification(null);
    try {
      const res = await api.getEnergyExceptions(severityFilter, statusFilter, plazaFilter, moduleFilter);
      setExceptions(res.exceptions || []);
    } catch (err) {
      console.error(err);
      setNotification({ type: 'error', text: 'Failed to fetch exceptions' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, [severityFilter, statusFilter, plazaFilter, moduleFilter]);

  const handleOpenReview = (exc: any) => {
    setSelectedException(exc);
    setActionType('MARK_REVIEWED');
    setReason('');
    setProposedValue('');
    setModalOpen(true);
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedException || !reason.trim()) {
      alert('Mandatory reason is required.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.reviewEnergyException(selectedException.exception_id, {
        action: actionType,
        reason: reason.trim(),
        proposed_correction: proposedValue === '' ? undefined : Number(proposedValue),
        actor: 'admin@srtpl.com',
      });
      setNotification({ type: 'success', text: res.message || 'Disposition recorded with audit retention.' });
      setModalOpen(false);
      fetchExceptions();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to review exception' });
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = exceptions.filter((exc) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return (
      exc.exception_id.toLowerCase().includes(s) ||
      exc.asset_code.toLowerCase().includes(s) ||
      exc.message.toLowerCase().includes(s) ||
      exc.rule_code.toLowerCase().includes(s)
    );
  });

  const criticalCount = exceptions.filter((e) => e.severity === 'CRITICAL').length;
  const warningCount = exceptions.filter((e) => e.severity === 'WARNING').length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <span>Exception Management & Validation Center</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Reviewed open exceptions snapshot (28 exceptions): 1 critical DG cumulative decrease, 16 DG source warnings, 11 Transformer cumulative decrease warnings.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800 text-xs">
              <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-400 font-bold border border-rose-500/30">
                {criticalCount} Critical
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 font-bold border border-amber-500/30">
                {warningCount} Warnings
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 font-bold">
                {exceptions.length} Total
              </span>
            </div>
          </div>
        </div>

        {/* Reviewed Snapshot Callout strictly from PDF Page 4 */}
        <div className="mt-4 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Reviewed Open Exceptions Baseline:</strong> 1 critical DG cumulative decrease; 16 DG source exceptions (warnings); 11 Transformer cumulative decreases (warnings). Counts update as new readings arrive.
            </span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 font-bold">
            Audit Trails Retained
          </span>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-medium ${
            notification.type === 'success'
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            )}
            <span>{notification.text}</span>
          </div>
          <button onClick={() => setNotification(null)} className="p-1 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[240px] max-w-md bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by exception ID, asset code, rule, message..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-slate-200 outline-none w-full text-xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Severity */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400 font-medium">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Severities</option>
              <option value="CRITICAL" className="bg-slate-800">CRITICAL</option>
              <option value="WARNING" className="bg-slate-800">WARNING</option>
              <option value="REVIEW" className="bg-slate-800">REVIEW</option>
            </select>
          </div>

          {/* Module */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400 font-medium">Module:</span>
            <select
              value={moduleFilter}
              onChange={(e) => setModuleFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Modules</option>
              <option value="DG" className="bg-slate-800">DG Generator</option>
              <option value="TRANSFORMER" className="bg-slate-800">Transformer</option>
              <option value="EB" className="bg-slate-800">EB Grid</option>
              <option value="SOLAR" className="bg-slate-800">Solar Plant</option>
            </select>
          </div>

          {/* Plaza */}
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

          {/* Status */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Statuses</option>
              <option value="OPEN" className="bg-slate-800">OPEN</option>
              <option value="REVIEWED" className="bg-slate-800">REVIEWED</option>
              <option value="RESOLVED" className="bg-slate-800">RESOLVED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Exceptions Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Exception Log ({filtered.length} matching items)
          </span>
          <span className="text-[11px] text-slate-500">
            Click 'Disposition' to review or propose corrections with reason
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-400 mb-2" />
            Loading exceptions register...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No exceptions found matching the current filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 font-medium border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Exception ID</th>
                  <th className="py-3 px-4">Asset Code</th>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Rule Code</th>
                  <th className="py-3 px-4">Timestamp (IST)</th>
                  <th className="py-3 px-4">Anomaly Message</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filtered.map((exc) => {
                  const isCrit = exc.severity === 'CRITICAL';
                  return (
                    <tr key={exc.exception_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isCrit
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {exc.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-slate-300">
                        {exc.exception_id}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                        {exc.asset_code}
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]">
                          {exc.plaza_id}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                        {exc.rule_code}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                        {exc.reading_datetime}
                      </td>
                      <td className="py-3 px-4 text-slate-200 max-w-md truncate text-[11px]" title={exc.message}>
                        {exc.message}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-semibold ${
                            exc.status === 'OPEN'
                              ? 'bg-amber-950/40 text-amber-300 border border-amber-700/40'
                              : exc.status === 'REVIEWED'
                              ? 'bg-sky-950/40 text-sky-300 border border-sky-700/40'
                              : 'bg-emerald-950/40 text-emerald-300 border border-emerald-700/40'
                          }`}
                        >
                          {exc.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenReview(exc)}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center gap-1 ml-auto border border-slate-700"
                        >
                          <Edit3 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Review</span>
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

      {/* Exception Disposition Modal */}
      {modalOpen && selectedException && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">Review Exception: {selectedException.exception_id}</h3>
              </div>
              <button onClick={() => setModalOpen(false)} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Asset:</span>
                  <span className="font-mono font-bold text-emerald-400">{selectedException.asset_code} ({selectedException.plaza_id})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Rule Violation:</span>
                  <span className="font-mono text-slate-200">{selectedException.rule_code}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Severity:</span>
                  <span className="font-bold text-amber-400">{selectedException.severity}</span>
                </div>
                <div className="pt-1 text-slate-300">
                  <span className="text-slate-500 block text-[10px] uppercase">Anomaly Details</span>
                  {selectedException.message}
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Disposition Action</label>
                <select
                  value={actionType}
                  onChange={(e) => setActionType(e.target.value)}
                  className="w-full bg-slate-950/60 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 outline-none cursor-pointer"
                >
                  <option value="MARK_REVIEWED">Mark Reviewed (Keep source record, add audit note)</option>
                  <option value="PROPOSE_CORRECTION">Propose Value Correction (Preserve source, stage proposal)</option>
                  <option value="DISMISS">Dismiss Exception (Verified benign operation)</option>
                </select>
              </div>

              {actionType === 'PROPOSE_CORRECTION' && (
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Proposed Corrected Value</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="Enter revised interval/cumulative value"
                    value={proposedValue}
                    onChange={(e) => setProposedValue(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full bg-slate-950/60 border border-emerald-500/50 rounded-xl px-3 py-2 text-emerald-300 outline-none font-mono"
                  />
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Mandatory Review Reason <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Enter explicit review justification (mandatory for audit)..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 p-2.5 text-slate-200 outline-none text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition flex items-center gap-1.5"
                >
                  {submitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Submit Disposition</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
