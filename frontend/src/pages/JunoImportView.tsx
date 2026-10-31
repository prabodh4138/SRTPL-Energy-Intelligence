import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { UploadCloud, CheckCircle2, AlertCircle, FileSpreadsheet, Hash } from 'lucide-react';

const EQUIPMENT_OPTIONS = [
  '⚡ EB Grid Supply',
  '⚡ DG Backup Generator',
  '☀️ Solar Rooftop Array',
  '🔌 Step-Down Transformer',
  '🔋 UPS Battery System',
];

export const JunoImportView: React.FC = () => {
  const [batches, setBatches] = useState<any[]>([]);
  const [equipment, setEquipment] = useState(EQUIPMENT_OPTIONS[0]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadPhase, setUploadPhase] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');
  const [bytesStats, setBytesStats] = useState<{ loaded: number; total: number }>({ loaded: 0, total: 0 });
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchBatches = async () => {
    try {
      const res = await api.getJunoBatches();
      setBatches(res);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadPhase('uploading');
    setUploadProgress(0);
    setStatusMsg(null);

    try {
      const res = await api.uploadJunoFile(equipment, file, (percent, loaded, total) => {
        setUploadProgress(percent);
        setBytesStats({ loaded, total });
        if (percent >= 100) {
          setUploadPhase('processing');
        }
      });
      setUploadPhase('done');
      if (res.status === 'SUCCESS') {
        setStatusMsg({ type: 'success', text: res.message });
        setFile(null);
        fetchBatches();
      } else {
        setStatusMsg({ type: 'error', text: res.message });
      }
    } catch (err: any) {
      setUploadPhase('idle');
      setStatusMsg({ type: 'error', text: 'Upload failed: ' + err.message });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <UploadCloud className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">Juno Log Import & Ingestion Centre</h2>
            <p className="text-xs text-slate-400">Automated ingestion for DG, EB, Solar, Transformer, and UPS interval meter logs.</p>
          </div>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Select Equipment Feeder</label>
              <select
                value={equipment}
                onChange={(e) => setEquipment(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 outline-none"
              >
                {EQUIPMENT_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Select Meter File (CSV / XLSX)</label>
              <input
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-300 file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-500 file:text-slate-950 hover:file:bg-emerald-400 cursor-pointer"
                required
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Hash className="w-4 h-4 text-emerald-400" />
              <span>Durable SHA-256 fingerprinting prevents double ingestion automatically.</span>
            </div>

            <button
              type="submit"
              disabled={uploading || !file}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white font-bold text-xs shadow-lg shadow-emerald-950/40 disabled:opacity-50 transition"
            >
              {uploading ? 'Ingesting Batch...' : 'Process Juno Batch'}
            </button>
          </div>

          {/* Real-time Upload Progress Bar */}
          {uploadPhase !== 'idle' && (
            <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2 mt-4 animate-in fade-in duration-200">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200 flex items-center gap-2">
                  {uploadPhase === 'uploading' && (
                    <>
                      <UploadCloud className="w-4 h-4 text-sky-400 animate-bounce" />
                      Uploading log file: {uploadProgress}%
                    </>
                  )}
                  {uploadPhase === 'processing' && (
                    <>
                      <UploadCloud className="w-4 h-4 text-emerald-400 animate-spin" />
                      Ingesting interval records & validating duplicate hash...
                    </>
                  )}
                  {uploadPhase === 'done' && (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      Ingestion complete!
                    </>
                  )}
                </span>
                <span className="font-mono text-emerald-400 font-bold">
                  {uploadPhase === 'uploading'
                    ? `${uploadProgress}% (${(bytesStats.loaded / 1024).toFixed(1)} KB / ${(bytesStats.total / 1024).toFixed(1)} KB)`
                    : '100%'}
                </span>
              </div>

              <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    uploadPhase === 'done'
                      ? 'bg-emerald-500'
                      : uploadPhase === 'processing'
                      ? 'bg-gradient-to-r from-emerald-500 to-sky-500 animate-pulse'
                      : 'bg-sky-500'
                  }`}
                  style={{
                    width: `${uploadPhase === 'processing' || uploadPhase === 'done' ? 100 : uploadProgress}%`,
                  }}
                />
              </div>
            </div>
          )}
        </form>

        {statusMsg && (
          <div
            className={`p-3.5 rounded-xl text-xs mt-4 flex items-center gap-2.5 ${
              statusMsg.type === 'success'
                ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/40'
                : 'bg-rose-950/40 text-rose-300 border border-rose-800/40'
            }`}
          >
            {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{statusMsg.text}</span>
          </div>
        )}
      </div>

      {/* Historical Batches */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Historical Ingested Juno Batches</h3>
          <span className="text-xs text-slate-400">{batches.length} recorded batches</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
              <tr>
                <th className="px-6 py-3">Batch ID</th>
                <th className="px-6 py-3">File Name</th>
                <th className="px-6 py-3">Equipment</th>
                <th className="px-6 py-3">Record Count</th>
                <th className="px-6 py-3">SHA-256 Fingerprint</th>
                <th className="px-6 py-3">Ingested At</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {batches.map((b) => (
                <tr key={b.batch_id} className="hover:bg-slate-800/40 transition">
                  <td className="px-6 py-3 font-semibold text-emerald-400">{b.batch_id}</td>
                  <td className="px-6 py-3 text-slate-200 font-sans">{b.file_name}</td>
                  <td className="px-6 py-3 text-slate-300 font-sans">{b.equipment}</td>
                  <td className="px-6 py-3 text-slate-100 font-bold">{b.records_count}</td>
                  <td className="px-6 py-3 text-slate-500 text-[10px] truncate max-w-xs">{b.sha256}</td>
                  <td className="px-6 py-3 text-slate-400 font-sans text-[11px]">{b.imported_at}</td>
                  <td className="px-6 py-3">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-sans font-bold">
                      {b.status} ✓
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
