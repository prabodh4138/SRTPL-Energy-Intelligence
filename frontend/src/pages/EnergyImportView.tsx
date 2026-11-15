import React, { useState } from 'react';
import { api } from '../api';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Eye,
  Check,
  FileText,
  X,
} from 'lucide-react';

export const EnergyImportView: React.FC = () => {
  const [selectedModule, setSelectedModule] = useState('eb');
  const [file, setFile] = useState<File | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any | null>(null);

  const [approvalReason, setApprovalReason] = useState('Supervisory reviewed and approved import batch');
  const [approving, setApproving] = useState(false);
  const [importResult, setImportResult] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setPreviewData(null);
      setImportResult(null);
      setErrorMessage(null);
    }
  };

  const handlePreview = async () => {
    if (!file) {
      alert('Please choose an Excel (.xlsx/.xls) or CSV file.');
      return;
    }
    setPreviewLoading(true);
    setErrorMessage(null);
    setImportResult(null);
    try {
      const res = await api.previewEnergyImport(file, selectedModule);
      setPreviewData(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to preview import file');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleApproveBatch = async () => {
    if (!previewData || !previewData.valid_preview) return;
    setApproving(true);
    setErrorMessage(null);
    try {
      const res = await api.approveEnergyImport({
        filename: previewData.filename,
        module: previewData.module,
        total_rows: previewData.total_rows,
        valid_rows: previewData.valid_preview,
        sha256: previewData.sha256,
        approval_reason: approvalReason.trim(),
        actor: 'admin@srtpl.com',
      });
      setImportResult(res);
      setPreviewData(null);
      setFile(null);
    } catch (err: any) {
      setErrorMessage(err.message || 'Import approval failed');
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                New Energy Ingestion Wizard
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
                JUNO Import Protected & Untouched
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-1.5">
              <UploadCloud className="w-5 h-5 text-emerald-400" />
              <span>Energy Readings Import & Batch Validation</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Guided upload, column mapping preview, duplicate rejection, supervisor approval, and batch audit logging. Never silently overwrites existing records.
            </p>
          </div>
        </div>

        {/* 4-Step Process Breadcrumb */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-4 border-t border-slate-800 text-xs">
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 font-bold flex items-center justify-center text-[10px]">1</span>
            <span className="text-slate-300 font-semibold">Select & Upload</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 font-bold flex items-center justify-center text-[10px]">2</span>
            <span className="text-slate-400">Map & Validate</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 font-bold flex items-center justify-center text-[10px]">3</span>
            <span className="text-slate-400">Review Duplicates</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 font-bold flex items-center justify-center text-[10px]">4</span>
            <span className="text-slate-400">Approve & Audit</span>
          </div>
        </div>
      </div>

      {/* Error / Success Notifications */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="p-1 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {importResult && (
        <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 text-xs space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5" />
            <span>Batch Import Successfully Approved & Audited</span>
          </div>
          <p className="text-slate-300">{importResult.message}</p>
          <div className="flex flex-wrap gap-4 text-slate-400 font-mono text-[11px] pt-2 border-t border-emerald-500/20">
            <span>Batch ID: <strong className="text-emerald-400">{importResult.batch_id}</strong></span>
            <span>Inserted Records: <strong className="text-emerald-400">{importResult.inserted_count}</strong></span>
            <span>Audit Trail: <strong className="text-emerald-400">Recorded</strong></span>
          </div>
        </div>
      )}

      {/* Step 1: File Selection & Module Target */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide">
          Step 1: Select Target Module & Energy Log File
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 font-medium mb-1.5">Target Equipment Module</label>
            <select
              value={selectedModule}
              onChange={(e) => setSelectedModule(e.target.value)}
              className="w-full bg-slate-950/60 border border-slate-700 rounded-xl px-3 py-2.5 text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="eb">⚡ EB Grid Supply</option>
              <option value="dg">🔥 Diesel Generator (DG)</option>
              <option value="solar">☀️ Solar Generation</option>
              <option value="transformer">🔌 Step-Down Transformer</option>
              <option value="ups">🔋 UPS System</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1.5">Upload Spreadsheet / CSV</label>
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="w-full bg-slate-950/60 border border-slate-700 rounded-xl px-3 py-2 text-slate-300 file:mr-3 file:py-1 file:px-2.5 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-slate-800 file:text-emerald-400 hover:file:bg-slate-700 cursor-pointer"
            />
          </div>
        </div>

        {file && (
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs">
            <div className="flex items-center gap-2 text-slate-300">
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span className="font-mono font-medium">{file.name}</span>
              <span className="text-slate-500">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button
              onClick={handlePreview}
              disabled={previewLoading}
              className="py-1.5 px-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition flex items-center gap-1.5 shadow-sm"
            >
              {previewLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
              <span>Inspect & Preview</span>
            </button>
          </div>
        )}
      </div>

      {/* Step 2 & 3: Preview, Mapping, and Duplicate Review */}
      {previewData && (
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Step 2 & 3: Column Mapping & Duplicate Analysis</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Total rows detected: {previewData.total_rows} · Valid: {previewData.valid_count} · Rejected / Duplicates: {previewData.rejected_count}
              </p>
            </div>
            <span className="font-mono text-[10px] px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300">
              SHA256: {previewData.sha256.slice(0, 16)}...
            </span>
          </div>

          {/* Mapping Summary */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-2">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block">
              Auto-Detected Column Mappings
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px]">
              {Object.entries(previewData.detected_mapping || {}).map(([target, source]: [string, any]) => (
                <div key={target} className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-slate-500 block text-[9px] uppercase">{target}</span>
                  <span className="text-emerald-400 font-bold truncate block">{String(source)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Rejected Rows / Duplicates Alert */}
          {previewData.rejected_count > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-bold">
                <AlertTriangle className="w-4 h-4" />
                <span>{previewData.rejected_count} Row(s) Flagged or Rejected (Duplicate Protection Enforced)</span>
              </div>
              <p className="text-slate-400 text-[11px]">
                The following rows will be excluded to prevent silent overwrites of existing readings:
              </p>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pt-1">
                {previewData.rejected_rows.map((rej: any, idx: number) => (
                  <div key={idx} className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] font-mono flex items-center justify-between">
                    <span className="text-slate-300">Row {rej.row_index}: {JSON.stringify(rej.data).slice(0, 80)}...</span>
                    <span className="text-rose-400 font-semibold">{rej.rejection_reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Valid Preview Rows Table */}
          <div className="space-y-2">
            <span className="text-slate-300 font-bold text-xs uppercase tracking-wide">
              Valid Rows Ready for Ingestion ({previewData.valid_count} rows)
            </span>
            <div className="rounded-xl border border-slate-800 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 font-medium border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Row #</th>
                    <th className="py-2.5 px-3">Raw Payload Snapshot</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 font-mono text-[11px]">
                  {previewData.valid_preview.slice(0, 5).map((row: any) => (
                    <tr key={row.row_index} className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 text-emerald-400 font-bold">{row.row_index}</td>
                      <td className="py-2 px-3 text-slate-300">{JSON.stringify(row.data)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Step 4: Supervisory Approval */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Step 4: Supervisor Authorization & Audit Reason
            </h4>
            <input
              type="text"
              required
              placeholder="Enter approval note or authorization reference (mandatory for audit)..."
              value={approvalReason}
              onChange={(e) => setApprovalReason(e.target.value)}
              className="w-full rounded-xl bg-slate-900 border border-slate-700 px-3 py-2 text-slate-200 outline-none text-xs"
            />
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setPreviewData(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
              >
                Discard Preview
              </button>
              <button
                type="button"
                onClick={handleApproveBatch}
                disabled={approving || previewData.valid_count === 0}
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition flex items-center gap-1.5 shadow-md shadow-emerald-950/30"
              >
                {approving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                <span>Authorize & Ingest {previewData.valid_count} Rows</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
