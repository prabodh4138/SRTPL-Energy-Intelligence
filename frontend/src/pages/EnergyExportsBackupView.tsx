import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Download,
  FileSpreadsheet,
  FileText,
  ShieldCheck,
  History,
  Archive,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Lock,
  X,
  RefreshCw,
} from 'lucide-react';

export const EnergyExportsBackupView: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(true);

  // Restore Modal State
  const [restoreModalOpen, setRestoreModalOpen] = useState(false);
  const [restoreConfirm, setRestoreConfirm] = useState(false);
  const [restoreReason, setRestoreReason] = useState('');
  const [backupJson, setBackupJson] = useState('');
  const [restoring, setRestoring] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchAuditLog = async () => {
    setLoadingLogs(true);
    try {
      const res = await api.getEnergyAuditLog(100);
      setAuditLogs(res.logs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchAuditLog();
  }, []);

  const handleDownloadBackup = () => {
    window.open(api.downloadEnergyBackupUrl, '_blank');
  };

  const handleDownloadExcel = () => {
    window.open(api.downloadEnergyExcelUrl, '_blank');
  };

  const handleDownloadPdf = () => {
    window.open(api.downloadEnergyPdfUrl, '_blank');
  };

  const handleExecuteRestore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!restoreConfirm) {
      alert('You must check the explicit confirmation box to proceed.');
      return;
    }
    if (!restoreReason.trim() || !backupJson.trim()) {
      alert('Please provide a mandatory reason and the backup JSON.');
      return;
    }
    setRestoring(true);
    setNotification(null);
    try {
      const res = await api.restoreEnergyBackup({
        confirm: true,
        reason: restoreReason.trim(),
        backup_json: backupJson.trim(),
        actor: 'admin@srtpl.com',
      });
      setNotification({ type: 'success', text: res.message || 'Backup successfully verified and restored.' });
      setRestoreModalOpen(false);
      setBackupJson('');
      setRestoreReason('');
      setRestoreConfirm(false);
      fetchAuditLog();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Restore failed' });
    } finally {
      setRestoring(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Energy Command Center Scope
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
                Existing Reports Untouched
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-1.5">
              <Archive className="w-5 h-5 text-emerald-400" />
              <span>Energy Exports, Verifiable Backup & Audit Register</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Generate new energy-only Excel/PDF reports, execute cryptographically verifiable backups, and audit all reading corrections and master changes.
            </p>
          </div>
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

      {/* Export & Backup Action Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Energy Excel Workbook Export */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-slate-400 tracking-wider">Multi-Tab Excel</span>
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
            </div>
            <h3 className="text-base font-bold text-slate-100 mt-3">Energy Command Center Workbook</h3>
            <p className="text-xs text-slate-400 mt-1">
              Includes Overview KPIs, Master Assets (with verified 121.38 kWp solar), 28 baseline exceptions, and complete audit trail.
            </p>
          </div>
          <div className="mt-5 pt-3 border-t border-slate-800">
            <button
              onClick={handleDownloadExcel}
              className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center justify-center gap-2 border border-slate-700"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              <span>Download Excel (.xlsx)</span>
            </button>
          </div>
        </div>

        {/* Executive Summary PDF/Text Export */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-slate-400 tracking-wider">Executive Report</span>
              <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                <FileText className="w-4 h-4" />
              </div>
            </div>
            <h3 className="text-base font-bold text-slate-100 mt-3">Baseline Analytics Summary</h3>
            <p className="text-xs text-slate-400 mt-1">
              Official summary document with approved baseline figures, operations snapshot, and Transformer compliance rules.
            </p>
          </div>
          <div className="mt-5 pt-3 border-t border-slate-800">
            <button
              onClick={handleDownloadPdf}
              className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center justify-center gap-2 border border-slate-700"
            >
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Download Executive Summary</span>
            </button>
          </div>
        </div>

        {/* Verifiable Backup Snapshot */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-slate-400 tracking-wider">Verifiable Snapshot</span>
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
            <h3 className="text-base font-bold text-slate-100 mt-3">Cryptographic JSON Backup</h3>
            <p className="text-xs text-slate-400 mt-1">
              Complete operational backup with SHA256 checksum, schema versioning, and full audit recovery controls.
            </p>
          </div>
          <div className="mt-5 pt-3 border-t border-slate-800 flex gap-2">
            <button
              onClick={handleDownloadBackup}
              className="flex-1 py-2 px-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center justify-center gap-1.5 border border-slate-700"
            >
              <Download className="w-3.5 h-3.5 text-amber-400" />
              <span>Export</span>
            </button>
            <button
              onClick={() => {
                setRestoreConfirm(false);
                setRestoreReason('');
                setBackupJson('');
                setRestoreModalOpen(true);
              }}
              className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition flex items-center gap-1.5 border border-slate-700"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Restore</span>
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Chronological Audit Trail (Who / When / Why / Before-After Values)
            </span>
          </div>
          <button
            onClick={fetchAuditLog}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {loadingLogs ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-400 mb-2" />
            Loading audit records...
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No audit records recorded yet. Corrections, imports, and master modifications will appear here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 font-medium border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Audit ID</th>
                  <th className="py-3 px-4">Timestamp (IST)</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Module</th>
                  <th className="py-3 px-4">Entity ID</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Mandatory Reason</th>
                  <th className="py-3 px-4">Before / After Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {auditLogs.map((log) => (
                  <tr key={log.audit_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-medium text-slate-400">{log.audit_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">{log.timestamp}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-emerald-400 font-mono text-[10px] font-bold">
                        {log.action_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-semibold">{log.module}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{log.entity_id}</td>
                    <td className="py-3 px-4 text-slate-400">{log.actor}</td>
                    <td className="py-3 px-4 text-slate-200 max-w-xs truncate" title={log.reason}>
                      {log.reason}
                    </td>
                    <td className="py-3 px-4 font-mono text-[10px] text-slate-400">
                      {log.old_value && <div>Old: {log.old_value}</div>}
                      {log.new_value && <div className="text-emerald-400">New: {log.new_value}</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Controlled Restore Modal */}
      {restoreModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">Tested Restore Procedure</h3>
              </div>
              <button onClick={() => setRestoreModalOpen(false)} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleExecuteRestore} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300 space-y-1">
                <strong>Attention:</strong>
                <p className="text-[11px] text-amber-200/80">
                  Restore requires explicit confirmation and tested verification. Source records are preserved and restore operation will be permanently recorded in the audit register.
                </p>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Backup JSON Payload <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Paste verified backup JSON string here..."
                  value={backupJson}
                  onChange={(e) => setBackupJson(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 p-2.5 text-slate-200 font-mono text-[11px] outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Mandatory Restore Justification Reason <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Enter reason for invoking restore procedure..."
                  value={restoreReason}
                  onChange={(e) => setRestoreReason(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none text-xs"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 flex items-center gap-3">
                <input
                  type="checkbox"
                  id="confirmRestore"
                  checked={restoreConfirm}
                  onChange={(e) => setRestoreConfirm(e.target.checked)}
                  className="rounded border-slate-700 text-emerald-500 focus:ring-0 cursor-pointer"
                />
                <label htmlFor="confirmRestore" className="text-slate-300 font-medium cursor-pointer">
                  I explicitly authorize this system restore operation.
                </label>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setRestoreModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={restoring || !restoreConfirm}
                  className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold transition flex items-center gap-1.5"
                >
                  {restoring ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Execute Verified Restore</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
