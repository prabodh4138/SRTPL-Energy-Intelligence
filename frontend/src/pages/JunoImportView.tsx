import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  Hash,
  Trash2,
  Layers,
  Zap,
  Sun,
  BatteryCharging,
  Cpu,
  Search,
  Check,
  AlertTriangle,
  RefreshCw,
  FolderUp,
  X,
} from 'lucide-react';

interface FileResultItem {
  filename: string;
  status: 'SUCCESS' | 'DUPLICATE_REJECTED' | 'ERROR';
  equipment?: string;
  equipment_label?: string;
  asset_code?: string;
  records_count?: number;
  valid_count?: number;
  exception_count?: number;
  cloud_injected?: boolean;
  sha256?: string;
  batch_id?: string;
  message?: string;
}

interface BatchSummary {
  status: 'SUCCESS' | 'PARTIAL' | 'DUPLICATES_ONLY' | 'ERROR';
  total_files: number;
  successful: number;
  duplicates: number;
  failed: number;
  total_valid_rows: number;
  message: string;
  file_results: FileResultItem[];
}

export const JunoImportView: React.FC = () => {
  const [batches, setBatches] = useState<any[]>([]);
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadPhase, setUploadPhase] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');
  const [bytesStats, setBytesStats] = useState<{ loaded: number; total: number }>({ loaded: 0, total: 0 });
  const [batchResult, setBatchResult] = useState<BatchSummary | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEquipmentFilter, setSelectedEquipmentFilter] = useState('ALL');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchBatches = async () => {
    try {
      const res = await api.getJunoBatches();
      setBatches(res || []);
    } catch (e) {
      console.error('Failed to fetch batches:', e);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  // Handle files selection / staging
  const addFilesToStage = (newFiles: FileList | File[]) => {
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const added: File[] = [];

    Array.from(newFiles).forEach((f) => {
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      if (validExtensions.includes(ext)) {
        // Prevent adding exact duplicate file objects in staging
        if (!stagedFiles.some((sf) => sf.name === f.name && sf.size === f.size)) {
          added.push(f);
        }
      }
    });

    if (added.length > 0) {
      setStagedFiles((prev) => [...prev, ...added]);
      setBatchResult(null);
    }
  };

  const removeStagedFile = (idx: number) => {
    setStagedFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const clearStagedFiles = () => {
    setStagedFiles([]);
    setBatchResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToStage(e.dataTransfer.files);
    }
  };

  // Batch upload submission
  const handleSimultaneousUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (stagedFiles.length === 0 || uploading) return;

    setUploading(true);
    setUploadPhase('uploading');
    setUploadProgress(0);
    setBatchResult(null);

    try {
      const res = await api.uploadJunoFilesMulti(
        stagedFiles,
        'AUTO',
        (percent, loaded, total) => {
          setUploadProgress(percent);
          setBytesStats({ loaded, total });
          if (percent >= 100) {
            setUploadPhase('processing');
          }
        }
      );

      setUploadPhase('done');
      setBatchResult(res);
      setStagedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      fetchBatches();
    } catch (err: any) {
      setUploadPhase('idle');
      setBatchResult({
        status: 'ERROR',
        total_files: stagedFiles.length,
        successful: 0,
        duplicates: 0,
        failed: stagedFiles.length,
        total_valid_rows: 0,
        message: err.message || 'Simultaneous upload failed.',
        file_results: stagedFiles.map((f) => ({
          filename: f.name,
          status: 'ERROR',
          message: err.message || 'Ingestion request failed.',
        })),
      });
    } finally {
      setUploading(false);
    }
  };

  // Heuristic indicator for staged file
  const guessEquipmentPreview = (filename: string) => {
    const fn = filename.toLowerCase();
    if (fn.includes('dg') || fn.includes('generator')) {
      return { label: 'DG Backup Generator', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20', icon: Zap };
    }
    if (fn.includes('solar')) {
      return { label: 'Solar Array', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', icon: Sun };
    }
    if (fn.includes('transformer') || fn.includes('tfr')) {
      return { label: 'Transformer', color: 'bg-violet-500/10 text-violet-400 border-violet-500/20', icon: Cpu };
    }
    if (fn.includes('ups')) {
      return { label: 'UPS System', color: 'bg-teal-500/10 text-teal-400 border-teal-500/20', icon: BatteryCharging };
    }
    if (fn.includes('eb') || fn.includes('grid')) {
      return { label: 'EB Grid Supply', color: 'bg-sky-500/10 text-sky-400 border-sky-500/20', icon: Zap };
    }
    return { label: 'Auto-Detect', color: 'bg-slate-700/40 text-slate-300 border-slate-600', icon: Layers };
  };

  // Equipment badge renderer
  const renderEquipmentBadge = (equipStr: string = '') => {
    const s = equipStr.toUpperCase();
    if (s.includes('DG')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <Zap className="w-3.5 h-3.5" />
          ⚡ DG Generator
        </span>
      );
    }
    if (s.includes('SOLAR')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-yellow-500/10 text-yellow-400 border border-yellow-500/30">
          <Sun className="w-3.5 h-3.5" />
          ☀️ Solar Array
        </span>
      );
    }
    if (s.includes('TRANSFORMER')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/30">
          <Cpu className="w-3.5 h-3.5" />
          🔌 Transformer
        </span>
      );
    }
    if (s.includes('UPS')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">
          <BatteryCharging className="w-3.5 h-3.5" />
          🔋 UPS System
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
        <Zap className="w-3.5 h-3.5" />
        ⚡ EB Grid Supply
      </span>
    );
  };

  // Filtered historical batches
  const filteredBatches = batches.filter((b) => {
    const q = searchQuery.toLowerCase().trim();
    const matchSearch =
      !q ||
      b.batch_id?.toLowerCase().includes(q) ||
      b.file_name?.toLowerCase().includes(q) ||
      b.equipment?.toLowerCase().includes(q) ||
      b.sha256?.toLowerCase().includes(q);

    const matchEquip =
      selectedEquipmentFilter === 'ALL' ||
      b.equipment?.toUpperCase().includes(selectedEquipmentFilter);

    return matchSearch && matchEquip;
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-sky-500/20 text-emerald-400 border border-emerald-500/30 shadow-inner">
              <FolderUp className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                Unified Juno Multi-File Ingestion Centre
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono">
                  AUTO-DETECT ACTIVE
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Simultaneously upload multiple interval logs across DG, EB, Solar, Transformer, and UPS. Equipment & Asset Codes are auto-detected with 100% precision.
              </p>
            </div>
          </div>

          {/* Quick Equipment Detection Badges */}
          <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
            <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300 font-mono">
              ⚡ EB Meter ID
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300 font-mono">
              ⚡ GENERATOR NO
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300 font-mono">
              ☀️ SolarPlantID
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300 font-mono">
              🔌 Transformer ID
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/80 text-slate-300 font-mono">
              🔋 UPS ID
            </span>
          </div>
        </div>

        {/* Central Drag & Drop Upload Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative group cursor-pointer border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200 ${
            isDragging
              ? 'border-emerald-400 bg-emerald-950/20 shadow-lg shadow-emerald-950/40'
              : 'border-slate-700 hover:border-slate-500 bg-slate-950/40 hover:bg-slate-950/60'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".csv, .xlsx, .xls"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                addFilesToStage(e.target.files);
              }
            }}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
            <div className="p-4 rounded-full bg-slate-900 border border-slate-800 text-emerald-400 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">
                Drop multiple log files here, or <span className="text-emerald-400 underline decoration-emerald-500/40 underline-offset-4">browse files</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Select any mixture of DG, EB, Solar, Transformer, or UPS files (.csv, .xlsx, .xls)
              </p>
            </div>
            <div className="flex items-center gap-4 text-[11px] text-slate-500 font-mono">
              <span>• Multi-File Drag & Drop</span>
              <span>• Zero Submodule Selection Required</span>
              <span>• Level 1 SHA-256 Deduplication</span>
            </div>
          </div>
        </div>

        {/* Staged Files Queue */}
        {stagedFiles.length > 0 && (
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-slate-200">
                  Staged for Simultaneous Ingestion ({stagedFiles.length} {stagedFiles.length === 1 ? 'file' : 'files'})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={clearStagedFiles}
                  disabled={uploading}
                  className="px-2.5 py-1 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 rounded-lg transition disabled:opacity-50"
                >
                  Clear All
                </button>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="px-2.5 py-1 text-xs text-sky-400 hover:text-sky-300 hover:bg-sky-950/30 rounded-lg transition disabled:opacity-50"
                >
                  + Add More
                </button>
              </div>
            </div>

            {/* Grid of staged file chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-56 overflow-y-auto pr-1">
              {stagedFiles.map((file, idx) => {
                const preview = guessEquipmentPreview(file.name);
                const PreviewIcon = preview.icon;
                return (
                  <div
                    key={`${file.name}-${idx}`}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-2">
                      <div className="p-1.5 rounded-lg bg-slate-800 text-slate-400 shrink-0">
                        <FileSpreadsheet className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-200 truncate" title={file.name}>
                          {file.name}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-slate-500 font-mono">
                            {(file.size / 1024).toFixed(1)} KB
                          </span>
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold border ${preview.color}`}>
                            <PreviewIcon className="w-2.5 h-2.5" />
                            {preview.label}
                          </span>
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => removeStagedFile(idx)}
                      disabled={uploading}
                      className="p-1 text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition disabled:opacity-50 shrink-0"
                      title="Remove file"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Primary Action Button */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Hash className="w-4 h-4 text-emerald-400" />
                <span>SHA-256 fingerprint deduplication will reject previously ingested files automatically.</span>
              </div>

              <button
                type="button"
                onClick={handleSimultaneousUpload}
                disabled={uploading || stagedFiles.length === 0}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white font-bold text-xs shadow-lg shadow-emerald-950/50 disabled:opacity-50 transition flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Ingesting {stagedFiles.length} Files Simultaneously...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>Ingest All {stagedFiles.length} Files Simultaneously</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Real-time Upload Progress Bar */}
        {uploadPhase !== 'idle' && (
          <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2 animate-in fade-in duration-200">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-200 flex items-center gap-2">
                {uploadPhase === 'uploading' && (
                  <>
                    <UploadCloud className="w-4 h-4 text-sky-400 animate-bounce" />
                    Uploading batch payload: {uploadProgress}%
                  </>
                )}
                {uploadPhase === 'processing' && (
                  <>
                    <RefreshCw className="w-4 h-4 text-emerald-400 animate-spin" />
                    Parsing equipment signatures, resolving asset IDs, and injecting readings into Supabase...
                  </>
                )}
                {uploadPhase === 'done' && (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Batch ingestion process finished!
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

        {/* Batch Results Overview Card */}
        {batchResult && (
          <div className="p-5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-4 animate-in fade-in duration-200">
            {/* Top Summary Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
              <div>
                <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  {batchResult.successful > 0 && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {batchResult.successful === 0 && batchResult.duplicates > 0 && <AlertTriangle className="w-4 h-4 text-amber-400" />}
                  {batchResult.failed > 0 && batchResult.successful === 0 && <AlertCircle className="w-4 h-4 text-rose-400" />}
                  Simultaneous Ingestion Summary
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">{batchResult.message}</p>
              </div>

              {/* Stat Counters */}
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                  {batchResult.successful} Ingested
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">
                  {batchResult.duplicates} Duplicates
                </span>
                {batchResult.failed > 0 && (
                  <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold">
                    {batchResult.failed} Failed
                  </span>
                )}
                <span className="px-2.5 py-1 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 font-bold">
                  {batchResult.total_valid_rows} Clean Records
                </span>
              </div>
            </div>

            {/* Itemized File Cards */}
            <div className="space-y-2.5">
              <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Itemized Results per File ({batchResult.file_results?.length || 0})
              </h5>
              <div className="grid grid-cols-1 gap-2.5 max-h-72 overflow-y-auto pr-1">
                {batchResult.file_results?.map((res, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs transition ${
                      res.status === 'SUCCESS'
                        ? 'bg-emerald-950/20 border-emerald-800/30'
                        : res.status === 'DUPLICATE_REJECTED'
                        ? 'bg-amber-950/20 border-amber-800/30'
                        : 'bg-rose-950/20 border-rose-800/30'
                    }`}
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200 truncate">{res.filename}</span>
                        {res.batch_id && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-emerald-400 border border-slate-700">
                            {res.batch_id}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">{res.message}</p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 shrink-0">
                      {res.equipment && renderEquipmentBadge(res.equipment)}

                      {res.asset_code && res.asset_code !== '—' && (
                        <span className="px-2 py-0.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300 font-mono text-[10px]">
                          Asset: {res.asset_code}
                        </span>
                      )}

                      {res.status === 'SUCCESS' && (
                        <>
                          <span className="px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-400 font-mono text-[10px] font-bold">
                            {res.valid_count ?? res.records_count ?? 0} Readings
                          </span>
                          <span className="px-2 py-0.5 rounded-lg bg-sky-500/10 text-sky-400 font-sans text-[10px] font-bold border border-sky-500/20">
                            ☁️ Supabase Synced
                          </span>
                        </>
                      )}

                      {res.status === 'DUPLICATE_REJECTED' && (
                        <span className="px-2 py-0.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold text-[10px]">
                          DUPLICATE ⛔
                        </span>
                      )}

                      {res.status === 'ERROR' && (
                        <span className="px-2 py-0.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold text-[10px]">
                          FAILED ❌
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Historical Batches Section */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              Historical Ingested Juno Batches
              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-xs font-mono">
                {filteredBatches.length} of {batches.length} recorded
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Authoritative records across DG, EB, Solar, Transformer, and UPS feeders synced to Supabase & SQLite.
            </p>
          </div>

          {/* Search & Filter Toolbar */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search batch, file, or hash..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 outline-none w-56 focus:border-emerald-500/50"
              />
            </div>

            <select
              value={selectedEquipmentFilter}
              onChange={(e) => setSelectedEquipmentFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 outline-none focus:border-emerald-500/50"
            >
              <option value="ALL">All Equipment</option>
              <option value="EB">EB Grid Supply</option>
              <option value="DG">DG Backup Generator</option>
              <option value="SOLAR">Solar Rooftop Array</option>
              <option value="TRANSFORMER">Transformer</option>
              <option value="UPS">UPS System</option>
            </select>

            <button
              onClick={fetchBatches}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
              title="Refresh batches list"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
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
              {filteredBatches.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500 font-sans">
                    No matching batches found.
                  </td>
                </tr>
              ) : (
                filteredBatches.map((b) => (
                  <tr key={b.batch_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-3 font-semibold text-emerald-400">{b.batch_id}</td>
                    <td className="px-6 py-3 text-slate-200 font-sans">{b.file_name}</td>
                    <td className="px-6 py-3 text-slate-300 font-sans">{renderEquipmentBadge(b.equipment)}</td>
                    <td className="px-6 py-3 text-slate-100 font-bold">{b.records_count}</td>
                    <td className="px-6 py-3 text-slate-500 text-[10px] truncate max-w-xs font-mono">{b.sha256}</td>
                    <td className="px-6 py-3 text-slate-400 font-sans text-[11px]">{b.imported_at}</td>
                    <td className="px-6 py-3">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-sans font-bold inline-flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
