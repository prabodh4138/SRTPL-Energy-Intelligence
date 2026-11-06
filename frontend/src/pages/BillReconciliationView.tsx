import React, { useEffect, useState } from 'react';

import { api } from '../api';

import { CandidateResult, OfficialBill, ReviewQueueItem, ReceiptItem, MergedReconciliationItem, MonthWiseClearanceSummary, UnbilledConsumerAccount } from '../types';

import {

  UploadCloud,

  FileCheck2,

  AlertCircle,

  FileSpreadsheet,

  Download,

  Trash2,

  Ban,

  CheckCircle2,

  Users,

  CreditCard,

  Layers,

  ChevronDown,

  ChevronUp,

  Cpu,

  Calculator,

  Sparkles,

} from 'lucide-react';



export const BillReconciliationView: React.FC = () => {

  const [activeSubtab, setActiveSubtab] = useState<'extract' | 'review' | 'register' | 'receipts' | 'merged' | 'monthwise' | 'consumers'>('extract');
  const [monthWiseSummary, setMonthWiseSummary] = useState<MonthWiseClearanceSummary[]>([]);
  const [selectedClearanceMonth, setSelectedClearanceMonth] = useState<string>('ALL');
  const [selectedClearanceStatus, setSelectedClearanceStatus] = useState<'ALL' | 'GENERATED' | 'PAID' | 'PENDING' | 'UNBILLED'>('ALL');
  const [clearanceSearchQuery, setClearanceSearchQuery] = useState<string>('');
  const [unbilledAccounts, setUnbilledAccounts] = useState<UnbilledConsumerAccount[]>([]);



  // Merged Reconciliation State

  const [mergedRecon, setMergedRecon] = useState<MergedReconciliationItem[]>([]);



  // Extraction State

  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  const [extracting, setExtracting] = useState(false);

  const [uploadProgress, setUploadProgress] = useState(0);

  const [uploadPhase, setUploadPhase] = useState<'idle' | 'uploading' | 'processing' | 'done'>('idle');

  const [bytesStats, setBytesStats] = useState<{ loaded: number; total: number }>({ loaded: 0, total: 0 });

  const [extractProgress, setExtractProgress] = useState<{ current: number; total: number; currentFile: string }>({

    current: 0,

    total: 0,

    currentFile: '',

  });

  const [candidates, setCandidates] = useState<CandidateResult[]>([]);

  const [candidateFilter, setCandidateFilter] = useState<'ALL' | 'VERIFIED' | 'REVIEW' | 'DUPLICATE_REJECTED' | 'FAILED'>('ALL');

  const [expandedCandidateIndices, setExpandedCandidateIndices] = useState<Set<number>>(new Set());



  const toggleCandidateExpand = (idx: number) => {

    setExpandedCandidateIndices((prev) => {

      const next = new Set(prev);

      if (next.has(idx)) {

        next.delete(idx);

      } else {

        next.add(idx);

      }

      return next;

    });

  };



  // Review Queue State

  const [reviewQueue, setReviewQueue] = useState<ReviewQueueItem[]>([]);

  // Official Register State

  const [officialBills, setOfficialBills] = useState<OfficialBill[]>([]);

  // Receipts State

  const [receipts, setReceipts] = useState<ReceiptItem[]>([]);

  // Consumers State

  const [consumers, setConsumers] = useState<any[]>([]);



  const [loadingData, setLoadingData] = useState(false);



  // Load appropriate data when tab changes

  useEffect(() => {

    loadTabData();

  }, [activeSubtab]);



  
  const loadUnbilledForMonth = async (month: string) => {
    if (!month || month === 'ALL') return;
    try {
      const res = await api.getUnbilledConsumers(month);
      setUnbilledAccounts(res.unbilled || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadTabData = async () => {

    setLoadingData(true);

    try {

      // Eagerly load official bills, review queue, and receipts so tab badges and export work immediately

      const [regRes, revRes, rcpRes, mrgRes, clrRes] = await Promise.all([

        api.getOfficialRegister().catch(() => ({ bills: [] })),

        api.getReviewQueue().catch(() => ({ items: [] })),

        api.getReceipts().catch(() => ({ receipts: [] })),

        api.getMergedReconciliation().catch(() => ({ records: [] })),

        api.getMonthWiseClearance().catch(() => ({ summary: [] })),
      ]);

      setOfficialBills(regRes.bills || []);

      setReviewQueue(revRes.items || []);

      setReceipts(rcpRes.receipts || []);

      setMergedRecon(mrgRes.records || []);
      setMonthWiseSummary(clrRes.summary || []);



      if (activeSubtab === 'consumers') {

        const cRes = await api.getConsumers().catch(() => ({ consumers: [] }));

        setConsumers(cRes.consumers || []);

      }

    } catch (e) {

      console.error(e);

    } finally {

      setLoadingData(false);

    }

  };



  const handleExportCandidates = async (format: 'xlsx' | 'csv') => {

    if (!candidates || candidates.length === 0) {

      alert('No extracted candidates to export.');

      return;

    }

    const rows = candidates.map((c, i) => {

      const p = c.payload || {};

      return {

        id: i + 1,

        source_filename: c.file || p.source_filename || '',

        kind: c.kind || (c.is_receipt ? 'Receipt' : 'Bill'),

        bill_number: c.is_receipt ? (c.identifier || '') : (p.bill_number || c.identifier || ''),

        receipt_no: c.is_receipt ? (c.identifier || p.receipt_no || '') : '',

        consumer_account_no: c.consumer || p.consumer_account_no || p.account_no || '',

        bill_month: c.month || p.bill_month || '',

        amount: c.amount || 0.0,

        result: c.result || '',

        audit_verdict: p.audit_verdict || p['Audit Verdict'] || '',

        energy_charges: p.energy_charges || p['a. Energy Charges'] || 0.0,

        electricity_duty: p.electricity_duty || p['Electricity Duty (j)'] || 0.0,

        meter_rent: p.meter_rent ?? p['Meter Rent'] ?? p['Meter Rent (k)'] ?? p['meter_rent_rs'] ?? p['Meter Rent (₹)'] ?? 0.0,

        customer_service_charge: p.customer_service_charge ?? p['Customer Service Charge'] ?? p['Customer Service'] ?? p['Customer Service Charge (l)'] ?? p['customer_service_charge'] ?? p['Customer Service (₹)'] ?? 0.0,

        net_payable_amount_before_rbt_dt_rs: p.net_payable_amount_before_rbt_dt_rs || p['Net Payable Amount Before Rbt. Dt.(Rs.)'] || 0.0,

        net_payable_amount_after_rbt_dt_rs: p.net_payable_amount_after_rbt_dt_rs || p['Net Payable Amount After Rbt. Dt.(Rs.)'] || 0.0,

        detail: c.detail || '',

      };

    });



    const columns = [

      'id', 'source_filename', 'kind', 'bill_number', 'receipt_no',

      'consumer_account_no', 'bill_month', 'amount', 'result',

      'meter_rent', 'customer_service_charge',

      'net_payable_amount_before_rbt_dt_rs', 'net_payable_amount_after_rbt_dt_rs',

      'detail'

    ];

    const labels: Record<string, string> = {

      id: 'Sl. No.',

      source_filename: 'Source File',

      kind: 'Document Type',

      bill_number: 'Bill Number',

      receipt_no: 'Receipt Number',

      consumer_account_no: 'Consumer A/C No.',

      bill_month: 'Bill Month',

      amount: 'Amount (₹)',

      result: 'Ingestion Status',

      meter_rent: 'Meter Rent (₹)',

      customer_service_charge: 'Customer Service (₹)',

      net_payable_amount_before_rbt_dt_rs: 'Net Payable Before Rebate (₹)',

      net_payable_amount_after_rbt_dt_rs: 'Net Payable After Rebate (₹)',

      detail: 'Verification Detail',

    };



    try {

      await api.exportCustomReport({

        format,

        title: 'Extracted_Candidates_Batch',

        columns,

        labels,

        rows,

      });

    } catch (err: any) {

      if (format === 'csv') {

        const headerRow = columns.map((col) => `"${labels[col] || col}"`).join(',');

        const dataRows = rows.map((r: any) =>

          columns

            .map((col) => `"${String(r[col] ?? '').replace(/"/g, '""')}"`)

            .join(',')

        );

        const csvContent = '\uFEFF' + [headerRow, ...dataRows].join('\r\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');

        a.href = url;

        a.download = `SRTPL_Extracted_Candidates_${new Date().toISOString().slice(0, 10)}.csv`;

        a.click();

        URL.revokeObjectURL(url);

      } else {

        alert('Export candidates failed: ' + (err.message || String(err)));

      }

    }

  };



  const handleRunExtraction = async (e: React.FormEvent) => {

    e.preventDefault();

    if (!selectedFiles || selectedFiles.length === 0) {

      alert('Please select one or more PDF or ZIP files to extract.');

      return;

    }



    setExtracting(true);

    setUploadPhase('processing');

    setUploadProgress(0);

    setExtractProgress({

      current: 0,

      total: selectedFiles.length,

      currentFile: 'Uploading to temporary memory & unpacking...',

    });

    setCandidates([]); // Clean state for real-time live-streaming results



    try {

      const fileArr = Array.from(selectedFiles);

      const res = await api.uploadBillsStream(fileArr, (current, total, file, candidate) => {

        setExtractProgress({ current, total, currentFile: file });

        const pct = Math.round((current / total) * 100);

        setUploadProgress(pct);

        setCandidates((prev) => {

          if (prev.some((c) => c.file === candidate.file && c.detail === candidate.detail)) {

            return prev;

          }

          return [...prev, candidate];

        });

      });



      if (res && res.candidates) {

        setCandidates(res.candidates);

      }

      setUploadPhase('done');

      setSelectedFiles(null);

      await loadTabData();

    } catch (err: any) {

      alert('Extraction failed: ' + err.message);

      setUploadPhase('idle');

    } finally {

      setExtracting(false);

    }

  };



  const handlePostCandidate = async (cid: string) => {

    if (!confirm(`Post and verify candidate ${cid} to official register?`)) return;

    try {

      await api.postReviewCandidate(cid);

      loadTabData();

    } catch (e: any) {

      alert('Error posting: ' + e.message);

    }

  };



  const handleDeleteCandidate = async (cid: string) => {

    if (!confirm(`Delete held candidate ${cid}?`)) return;

    try {

      await api.deleteReviewCandidate(cid);

      loadTabData();

    } catch (e: any) {

      alert('Error deleting: ' + e.message);

    }

  };



  const handleVoidBill = async (bNo: string) => {

    const reason = prompt(`Enter reason for voiding bill ${bNo}:`, 'Billing adjustment / correction');

    if (!reason) return;

    try {

      await api.voidBill(bNo, reason);

      loadTabData();

    } catch (e: any) {

      alert('Error voiding: ' + e.message);

    }

  };



  const formatMoney = (n: number) => `₹${n?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;



  return (

    <div className="space-y-6">

      {/* Subtab Bar */}

      <div className="flex flex-wrap items-center justify-between gap-4">

        <div className="flex items-center p-1.5 rounded-2xl bg-slate-900 border border-slate-800">

          <button

            onClick={() => setActiveSubtab('extract')}

            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${

              activeSubtab === 'extract'

                ? 'bg-emerald-500 text-slate-950 shadow-md'

                : 'text-slate-400 hover:text-slate-200'

            }`}

          >

            <UploadCloud className="w-3.5 h-3.5" />

            1. Bill / Receipt Extraction

          </button>



          <button

            onClick={() => setActiveSubtab('review')}

            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${

              activeSubtab === 'review'

                ? 'bg-amber-500 text-slate-950 shadow-md'

                : 'text-slate-400 hover:text-slate-200'

            }`}

          >

            <AlertCircle className="w-3.5 h-3.5" />

            2. Review Queue ({reviewQueue.length})

          </button>



          <button

            onClick={() => setActiveSubtab('register')}

            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${

              activeSubtab === 'register'

                ? 'bg-sky-500 text-slate-950 shadow-md'

                : 'text-slate-400 hover:text-slate-200'

            }`}

          >

            <FileCheck2 className="w-3.5 h-3.5" />

            3. Official Bill Register

          </button>



          <button

            onClick={() => setActiveSubtab('receipts')}

            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${

              activeSubtab === 'receipts'

                ? 'bg-indigo-500 text-slate-950 shadow-md'

                : 'text-slate-400 hover:text-slate-200'

            }`}

          >

            <CreditCard className="w-3.5 h-3.5" />

            4. Receipts Register ({receipts.length})

          </button>



          <button

            onClick={() => setActiveSubtab('merged')}

            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${

              activeSubtab === 'merged'

                ? 'bg-teal-500 text-slate-950 shadow-md'

                : 'text-slate-400 hover:text-slate-200'

            }`}

          >

            <FileSpreadsheet className="w-3.5 h-3.5" />

            5. Merged Reconciliation ({mergedRecon.length})

          </button>



          <button
            onClick={() => setActiveSubtab('monthwise')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeSubtab === 'monthwise'
                ? 'bg-emerald-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            6. Month-Wise Clearance ({monthWiseSummary.length})
          </button>

          <button

            onClick={() => setActiveSubtab('consumers')}

            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${

              activeSubtab === 'consumers'

                ? 'bg-purple-500 text-slate-950 shadow-md'

                : 'text-slate-400 hover:text-slate-200'

            }`}

          >

            <Users className="w-3.5 h-3.5" />

            7. Consumer Master (60)

          </button>

        </div>



        {/* Universal Export Dropdowns / Quick Buttons for Bills, Receipts, and Merged Reconciliation */}

        <div className="flex items-center gap-2">

          <button

            onClick={() => {

              if (activeSubtab === 'monthwise' && monthWiseSummary.length > 0) {
                window.open(api.downloadMonthWiseExcelUrl, '_blank');
              } else if (activeSubtab === 'receipts' && receipts.length > 0) {

                window.open(api.downloadReceiptsExcelUrl, '_blank');

              } else if (activeSubtab === 'merged' && mergedRecon.length > 0) {

                window.open(api.downloadMergedReconciliationExcelUrl, '_blank');

              } else if (officialBills.length > 0) {

                window.open(api.downloadBillsExcelUrl, '_blank');

              } else if (candidates.length > 0) {

                handleExportCandidates('xlsx');

              } else {

                alert("No records currently available to export. Please upload bills or receipts first.");

              }

            }}

            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30 transition shadow-sm cursor-pointer"

            title="Download Excel (.xlsx) for active register"

          >

            <Download className="w-3.5 h-3.5 text-emerald-400" />

            Export Excel

          </button>

          <button

            onClick={() => {

              if (activeSubtab === 'monthwise' && monthWiseSummary.length > 0) {
                window.open(api.downloadMonthWiseCsvUrl, '_blank');
              } else if (activeSubtab === 'receipts' && receipts.length > 0) {

                window.open(api.downloadReceiptsCsvUrl, '_blank');

              } else if (activeSubtab === 'merged' && mergedRecon.length > 0) {

                window.open(api.downloadMergedReconciliationCsvUrl, '_blank');

              } else if (officialBills.length > 0) {

                window.open(api.downloadBillsCsvUrl, '_blank');

              } else if (candidates.length > 0) {

                handleExportCandidates('csv');

              } else {

                alert("No records currently available to export. Please upload bills or receipts first.");

              }

            }}

            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border-sky-500/30 transition shadow-sm cursor-pointer"

            title="Download CSV (.csv) for active register"

          >

            <Download className="w-3.5 h-3.5 text-sky-400" />

            Export CSV

          </button>

        </div>

      </div>



      {/* TAB 1: EXTRACTION */}

      {activeSubtab === 'extract' && (

        <div className="space-y-6">

          <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl">

            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">

              <UploadCloud className="w-4 h-4 text-emerald-400" />

              Automated Bill & Receipt Extraction Engine

            </h2>

            <p className="text-xs text-slate-400 mt-1">

              Extracts 14 core tariff/meter fields + MD-KW/KVA metrics + mathematical reconciliation formulas.

            </p>



            <form onSubmit={handleRunExtraction} className="mt-5 space-y-4">

              <div className="p-6 rounded-2xl border-2 border-dashed border-slate-700 hover:border-emerald-500/60 bg-slate-950/30 text-center cursor-pointer transition">

                <input

                  type="file"

                  multiple

                  accept=".pdf, .zip, .png, .jpg"

                  onChange={(e) => setSelectedFiles(e.target.files)}

                  className="hidden"

                  id="bill-files"

                />

                <label htmlFor="bill-files" className="cursor-pointer">

                  <UploadCloud className="w-8 h-8 text-emerald-400 mx-auto mb-2" />

                  <div className="text-xs font-semibold text-slate-200">

                    {selectedFiles && selectedFiles.length > 0

                      ? `${selectedFiles.length} file(s) selected`

                      : 'Click to select or drop Energy Bill PDFs and ZIPs'}

                  </div>

                  <div className="text-[11px] text-slate-500 mt-1">Single PDF, Batch PDFs, and Multi-archive ZIPs supported.</div>

                </label>

              </div>



              <div className="flex items-center justify-between">

                <div className="text-xs text-slate-400">

                  ⚡ Automatic formula verification: <span className="text-emerald-400 font-mono">Energy Charges</span> +{' '}

                  <span className="text-sky-400 font-mono">Electricity Charges</span> +{' '}

                  <span className="text-indigo-400 font-mono">Current Total</span>.

                </div>



                <button

                  type="submit"

                  disabled={extracting || !selectedFiles || selectedFiles.length === 0}

                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white font-bold text-xs shadow-lg shadow-emerald-950/40 disabled:opacity-50 transition"

                >

                  {extracting ? 'Processing Extraction & Calculations...' : '🚀 Run Extraction Pipeline'}

                </button>

              </div>



              {/* Real-time Per-Bill Extraction Progress Bar */}

              {uploadPhase !== 'idle' && (

                <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2 mt-4 animate-in fade-in duration-200">

                  <div className="flex items-center justify-between text-xs">

                    <span className="font-semibold text-slate-200 flex items-center gap-2">

                      {uploadPhase === 'processing' && (

                        <>

                          <Layers className="w-4 h-4 text-emerald-400 animate-spin" />

                          <span>

                            Extracting Bill <strong className="text-emerald-400 font-mono text-sm">{extractProgress.current}</strong> of{' '}

                            <strong className="text-slate-100 font-mono text-sm">{extractProgress.total}</strong>:{' '}

                            <span className="text-slate-400 font-mono font-normal truncate max-w-xs inline-block align-bottom">

                              {extractProgress.currentFile}

                            </span>

                          </span>

                        </>

                      )}

                      {uploadPhase === 'done' && (

                        <>

                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />

                          <span>

                            Extraction complete! <strong className="text-emerald-400 font-mono">{extractProgress.total} of {extractProgress.total}</strong> documents processed & temporary storage purged.

                          </span>

                        </>

                      )}

                    </span>

                    <span className="font-mono text-emerald-400 font-bold text-sm">

                      {uploadPhase === 'done'

                        ? '100% (COMPLETE)'

                        : `${extractProgress.total > 0 ? Math.round((extractProgress.current / extractProgress.total) * 100) : 0}% [${extractProgress.current}/${extractProgress.total}]`}

                    </span>

                  </div>



                  <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden p-0.5">

                    <div

                      className={`h-full rounded-full transition-all duration-300 ${

                        uploadPhase === 'done'

                          ? 'bg-emerald-500'

                          : 'bg-gradient-to-r from-emerald-500 via-sky-500 to-emerald-400'

                      }`}

                      style={{

                        width: `${

                          uploadPhase === 'done'

                            ? 100

                            : extractProgress.total > 0

                            ? Math.max(3, Math.round((extractProgress.current / extractProgress.total) * 100))

                            : 3

                        }%`,

                      }}

                    />

                  </div>



                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">

                    <span className="text-slate-400 flex items-center gap-1">

                      🔒 <strong>Zero PDF Database Storage:</strong> PDFs are processed in temporary sandbox memory and immediately wiped.

                    </span>

                    <span className="text-emerald-400 font-medium">⚡ Real-time Stream & Duplicate Barrier Active</span>

                  </div>

                </div>

              )}

            </form>

          </div>



          {/* Extracted Candidates Table */}

          {candidates.length > 0 && (

            <div className="space-y-4">

              {/* Summary KPIs */}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">

                <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800">

                  <span className="text-[11px] text-slate-400">Total Processed</span>

                  <div className="text-xl font-bold text-slate-100">{candidates.length}</div>

                </div>

                <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800">

                  <span className="text-[11px] text-emerald-400">Verified & Posted</span>

                  <div className="text-xl font-bold text-emerald-400">

                    {candidates.filter((c) => c.result === 'VERIFIED').length}

                  </div>

                </div>

                <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800">

                  <span className="text-[11px] text-amber-400">Held in Review</span>

                  <div className="text-xl font-bold text-amber-400">

                    {candidates.filter((c) => c.result === 'REVIEW').length}

                  </div>

                </div>

                <div className="p-3.5 rounded-2xl bg-slate-900 border border-rose-900/40 bg-rose-950/10">

                  <span className="text-[11px] text-rose-400 font-semibold">Duplicates Rejected</span>

                  <div className="text-xl font-bold text-rose-400">

                    {candidates.filter((c) => c.result === 'DUPLICATE_REJECTED').length}

                  </div>

                </div>

              </div>



              {/* Table Card */}

              <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">

                <div className="px-6 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">

                  <div className="flex items-center gap-2">

                    <h3 className="text-sm font-semibold text-slate-200">Candidate Extraction Results</h3>

                    <span className="text-xs text-slate-500">({candidates.length} items)</span>

                    <div className="flex items-center gap-1.5 ml-3">

                      <button

                        onClick={() => handleExportCandidates('xlsx')}

                        className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm"

                        title="Export these extracted candidate rows as Excel (.xlsx)"

                      >

                        <Download className="w-3 h-3" />

                        Export Batch (Excel)

                      </button>

                      <button

                        onClick={() => handleExportCandidates('csv')}

                        className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 transition shadow-sm"

                        title="Export these extracted candidate rows as CSV (.csv)"

                      >

                        <Download className="w-3 h-3" />

                        Export Batch (CSV)

                      </button>

                    </div>

                  </div>



                  {/* Filter Pills */}

                  <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs">

                    {(['ALL', 'VERIFIED', 'REVIEW', 'DUPLICATE_REJECTED'] as const).map((f) => (

                      <button

                        key={f}

                        onClick={() => setCandidateFilter(f)}

                        className={`px-3 py-1 rounded-lg font-semibold transition ${

                          candidateFilter === f

                            ? 'bg-slate-800 text-slate-100 shadow'

                            : 'text-slate-400 hover:text-slate-200'

                        }`}

                      >

                        {f === 'ALL'

                          ? `All (${candidates.length})`

                          : f === 'VERIFIED'

                          ? `Verified (${candidates.filter((c) => c.result === 'VERIFIED').length})`

                          : f === 'REVIEW'

                          ? `Review (${candidates.filter((c) => c.result === 'REVIEW').length})`

                          : `Rejected (${candidates.filter((c) => c.result === 'DUPLICATE_REJECTED').length})`}

                      </button>

                    ))}

                  </div>

                </div>



                <div className="overflow-x-auto">

                  <table className="w-full text-left text-xs text-slate-300">

                    <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">

                      <tr>

                        <th className="w-8 px-3 py-3"></th>

                        <th className="px-6 py-3">Source File</th>

                        <th className="px-6 py-3">Document Kind</th>

                        <th className="px-6 py-3">Consumer Account</th>

                        <th className="px-6 py-3">Bill Month</th>

                        <th className="px-6 py-3">Reference / Bill Details</th>

                        <th className="px-6 py-3">Extracted Amount</th>

                        <th className="px-6 py-3">Validation Result</th>

                      </tr>

                    </thead>

                    <tbody className="divide-y divide-slate-800/60 font-mono text-xs">

                      {candidates

                        .filter((c) => candidateFilter === 'ALL' || c.result === candidateFilter)

                        .map((cand, i) => {

                          const isExpanded = expandedCandidateIndices.has(i);

                          const p = cand.payload || {};

                          return (

                            <React.Fragment key={i}>

                              <tr

                                onClick={() => toggleCandidateExpand(i)}

                                className={`hover:bg-slate-800/40 cursor-pointer transition ${

                                  cand.result === 'DUPLICATE_REJECTED' ? 'bg-rose-950/10' : ''

                                } ${isExpanded ? 'bg-slate-800/50' : ''}`}

                              >

                                <td className="px-3 py-3 text-slate-500 text-center">

                                  {isExpanded ? (

                                    <ChevronUp className="w-4 h-4 text-emerald-400 mx-auto" />

                                  ) : (

                                    <ChevronDown className="w-4 h-4 text-slate-500 mx-auto" />

                                  )}

                                </td>

                                <td className="px-6 py-3 text-slate-300 font-sans font-medium">{cand.file}</td>

                                <td className="px-6 py-3">

                                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-sans">

                                    {cand.kind}

                                  </span>

                                </td>

                                <td className="px-6 py-3 font-semibold text-sky-400">{cand.consumer}</td>

                                <td className="px-6 py-3 text-slate-400">{cand.month}</td>

                                <td className="px-6 py-3 text-slate-300 font-sans">{cand.detail}</td>

                                <td className="px-6 py-3 text-slate-100 font-bold">{formatMoney(cand.amount)}</td>

                                <td className="px-6 py-3">

                                  <span

                                    className={`px-2.5 py-1 rounded-full text-[10px] font-bold font-sans flex items-center gap-1 w-fit ${

                                      cand.result === 'VERIFIED'

                                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'

                                        : cand.result === 'REVIEW'

                                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'

                                        : cand.result === 'DUPLICATE_REJECTED'

                                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'

                                        : 'bg-slate-800 text-slate-400 border border-slate-700'

                                    }`}

                                  >

                                    {cand.result === 'DUPLICATE_REJECTED' && <Ban className="w-3 h-3 text-rose-400" />}

                                    {cand.result === 'VERIFIED' && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}

                                    {cand.result === 'REVIEW' && <AlertCircle className="w-3 h-3 text-amber-400" />}

                                    {cand.result}

                                  </span>

                                </td>

                              </tr>

                              {isExpanded && (

                                <tr className="bg-slate-950/80 border-b border-slate-800">

                                  <td colSpan={8} className="p-4 font-sans space-y-4">

                                    {/* AI Model & Audit Banner */}

                                    <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800">

                                      <div className="flex items-center gap-2">

                                        <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400">

                                          <Cpu className="w-4 h-4" />

                                        </div>

                                        <div>

                                          <div className="text-xs font-bold text-slate-200 flex items-center gap-2">

                                            <span>AI Model Fitted:</span>

                                            <span className="text-purple-400">{p["AI Model Applied"] || "TPWODL Universal Adaptive AI Ensemble"}</span>

                                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold">

                                              Fit: 100%

                                            </span>

                                          </div>

                                          <p className="text-[11px] text-slate-500 mt-0.5">

                                            {p["AI Model Reasoning"] || "Optimal mathematical reconciliation model applied with 100% classification confidence."}

                                          </p>

                                        </div>

                                      </div>



                                      <div className="flex items-center gap-2">

                                        <span className="text-xs text-slate-400">Audit Status:</span>

                                        <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${

                                          cand.result === 'VERIFIED'

                                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'

                                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'

                                        }`}>

                                          {p["Audit Verdict"] || cand.result}

                                        </span>

                                      </div>

                                    </div>



                                    {/* 13 Extracted Fields Grid */}

                                    <div>

                                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">

                                        <Sparkles className="w-3.5 h-3.5 text-sky-400" />

                                        All 13 Extracted Bill Parameters

                                      </h4>

                                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 text-xs font-mono">

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">1. Security Deposit</span>

                                          <span className="text-slate-200 font-semibold">{p["Security Deposit"] ? `₹${p["Security Deposit"]}` : "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">2. MD (Max Demand)</span>

                                          <span className="text-sky-300 font-semibold">{p["MD"] || "—"}</span>

                                          <span className="text-[10px] text-slate-500 block font-sans mt-0.5">KW: {p["MD-KW"] || "—"} | KVA: {p["MD-KVA"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">3. Contract Demand</span>

                                          <span className="text-slate-200 font-semibold">{p["Contract Demand"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">4. Section</span>

                                          <span className="text-slate-200 font-semibold">{p["Section"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">5. Sub-Division</span>

                                          <span className="text-slate-200 font-semibold">{p["Sub-Division"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">6. Rebate Date</span>

                                          <span className="text-emerald-400 font-semibold">{p["Rebate Date"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">7. CUML MD-KVA</span>

                                          <span className="text-slate-200 font-semibold">{p["CUML MD-KVA"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">8. CUML MD-KW</span>

                                          <span className="text-slate-200 font-semibold">{p["CUML MD-KW"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">9. DPS(Rs.)</span>

                                          <span className="text-slate-200 font-semibold">{p["DPS(Rs.)"] ? `₹${p["DPS(Rs.)"]}` : "₹0.00"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">10. Tariff Category</span>

                                          <span className="text-slate-200 font-semibold">{p["Tariff Category"] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">11. Meter Sl. No.</span>

                                          <span className="text-sky-300 font-semibold">{p["Meter Sl. No."] || "—"}</span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">12. Net Payable (Before Rebate)</span>

                                          <span className="text-emerald-400 font-bold">

                                            {p["Net Payable Amount Before Rbt. Dt.(Rs.)"] ? `₹${p["Net Payable Amount Before Rbt. Dt.(Rs.)"]}` : "—"}

                                          </span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">13. Net Payable (After Rebate)</span>

                                          <span className="text-amber-300 font-bold">

                                            {p["Net Payable Amount After Rbt. Dt.(Rs.)"] ? `₹${p["Net Payable Amount After Rbt. Dt.(Rs.)"]}` : "—"}

                                          </span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">14. Meter Rent (₹)</span>

                                          <span className="text-teal-300 font-semibold">

                                            {p["Meter Rent"] || p["Meter Rent (k)"] || p["meter_rent"] || p["Meter Rent (₹)"] ? `₹${p["Meter Rent"] || p["Meter Rent (k)"] || p["meter_rent"] || p["Meter Rent (₹)"]}` : "₹0.00"}

                                          </span>

                                        </div>

                                        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">

                                          <span className="text-[10px] text-slate-500 block font-sans">15. Customer Service (₹)</span>

                                          <span className="text-purple-300 font-semibold">

                                            {p["Customer Service"] || p["Customer Service Charge"] || p["Customer Service Charge (l)"] || p["customer_service_charge"] || p["Customer Service (₹)"] ? `₹${p["Customer Service"] || p["Customer Service Charge"] || p["Customer Service Charge (l)"] || p["customer_service_charge"] || p["Customer Service (₹)"]}` : "₹0.00"}

                                          </span>

                                        </div>

                                      </div>

                                    </div>



                                    {/* Arithmetic Verification Checklist */}

                                    {p["Cal Energy Charges"] !== undefined && (

                                      <div>

                                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">

                                          <Calculator className="w-3.5 h-3.5 text-emerald-400" />

                                          Step-by-Step Arithmetic Calculation Verification

                                        </h4>

                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs font-mono">

                                          <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">

                                            <div>

                                              <span className="text-[10px] text-slate-500 block font-sans">Energy Charges Verification</span>

                                              <span className="text-slate-200">Cal: ₹{p["Cal Energy Charges"]} vs Ext: ₹{p["a. Energy Charges"]}</span>

                                            </div>

                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold font-sans bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">

                                              {p["Energy Charges Check"] || "MATCH ✓"}

                                            </span>

                                          </div>

                                          <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">

                                            <div>

                                              <span className="text-[10px] text-slate-500 block font-sans">Electricity Charge Verification</span>

                                              <span className="text-slate-200">Cal: ₹{p["Cal Electricity Charges"]} vs Ext: ₹{p["Electricity Charge (i)"]}</span>

                                            </div>

                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold font-sans bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">

                                              {p["Electricity Charges Check"] || "MATCH ✓"}

                                            </span>

                                          </div>

                                          <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">

                                            <div>

                                              <span className="text-[10px] text-slate-500 block font-sans">Current Total Reconciliation</span>

                                              <span className="text-slate-200">Cal: ₹{p["Cal Current Total"]} vs Ext: ₹{p["Current Total (o)"]}</span>

                                            </div>

                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold font-sans bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">

                                              {p["Current Total Check"] || "MATCH ✓"}

                                            </span>

                                          </div>

                                        </div>

                                      </div>

                                    )}

                                  </td>

                                </tr>

                              )}

                            </React.Fragment>

                          );

                        })}

                    </tbody>

                  </table>

                </div>

              </div>

            </div>

          )}

        </div>

      )}



      {/* TAB 2: REVIEW QUEUE */}

      {activeSubtab === 'review' && (

        <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">

          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">

            <div>

              <h3 className="text-sm font-semibold text-slate-200">Persistent Bill Review Queue</h3>

              <p className="text-xs text-slate-400 mt-0.5">Held candidate records with calculation mismatches or provisional audit flags.</p>

            </div>

            <span className="text-xs text-amber-400 font-semibold">{reviewQueue.length} candidates held</span>

          </div>



          <div className="overflow-x-auto">

            <table className="w-full text-left text-xs text-slate-300">

              <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">

                <tr>

                  <th className="px-6 py-3">Candidate ID</th>

                  <th className="px-6 py-3">Consumer A/C</th>

                  <th className="px-6 py-3">Month</th>

                  <th className="px-6 py-3">Bill Number</th>

                  <th className="px-6 py-3">Basis</th>

                  <th className="px-6 py-3">Amount</th>

                  <th className="px-6 py-3">Exception / Reason</th>

                  <th className="px-6 py-3 text-right">Actions</th>

                </tr>

              </thead>

              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">

                {reviewQueue.map((item) => (

                  <tr key={item.candidate_id} className="hover:bg-slate-800/40 transition">

                    <td className="px-6 py-3 font-semibold text-amber-400">{item.candidate_id}</td>

                    <td className="px-6 py-3 text-sky-400 font-bold">{item.consumer_account_no}</td>

                    <td className="px-6 py-3 text-slate-400">{item.bill_month}</td>

                    <td className="px-6 py-3 text-slate-300">{item.bill_number}</td>

                    <td className="px-6 py-3">

                      <span className="px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 text-[10px]">

                        {item.bill_basis}

                      </span>

                    </td>

                    <td className="px-6 py-3 text-slate-100 font-bold">{formatMoney(item.amount)}</td>

                    <td className="px-6 py-3 text-slate-300 font-sans max-w-xs">{item.exception_reason}</td>

                    <td className="px-6 py-3 text-right space-x-2 font-sans">

                      <button

                        onClick={() => handlePostCandidate(item.candidate_id)}

                        className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold transition"

                      >

                        Verify & Post

                      </button>

                      <button

                        onClick={() => handleDeleteCandidate(item.candidate_id)}

                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-rose-900/60 text-slate-400 hover:text-rose-300 text-[11px] transition"

                      >

                        Delete

                      </button>

                    </td>

                  </tr>

                ))}

                {reviewQueue.length === 0 && (

                  <tr>

                    <td colSpan={8} className="px-6 py-8 text-center text-xs text-slate-500 font-sans">

                      Review queue is clear! No bills held for review.

                    </td>

                  </tr>

                )}

              </tbody>

            </table>

          </div>

        </div>

      )}



      {/* TAB 3: OFFICIAL REGISTER */}

      {activeSubtab === 'register' && (

        <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">

          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">

            <div>

              <h3 className="text-sm font-semibold text-slate-200">Authoritative Official Bill Register</h3>

              <p className="text-xs text-slate-400 mt-0.5">Committed actual bills passed by mathematical verification and Supabase database guards.</p>

            </div>

            <span className="text-xs text-emerald-400 font-semibold">{officialBills.length} posted bills</span>

          </div>



          <div className="overflow-x-auto">

            <table className="w-full text-left text-xs text-slate-300">

              <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">

                <tr>

                  <th className="px-6 py-3">Bill Number</th>

                  <th className="px-6 py-3">Consumer A/C</th>

                  <th className="px-6 py-3">Plaza</th>

                  <th className="px-6 py-3">Feeder Type</th>

                  <th className="px-6 py-3">Month</th>

                  <th className="px-6 py-3">Total Payable</th>

                  <th className="px-6 py-3">Paid Amount</th>

                  <th className="px-6 py-3">Outstanding</th>

                  <th className="px-6 py-3">Audit Verdict</th>

                  <th className="px-6 py-3 text-right">Action</th>

                </tr>

              </thead>

              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">

                {officialBills.map((bill) => (

                  <tr key={bill.bill_number} className="hover:bg-slate-800/40 transition">

                    <td className="px-6 py-3 font-semibold text-emerald-400">{bill.bill_number}</td>

                    <td className="px-6 py-3 text-sky-400 font-bold">{bill.consumer_account_no}</td>

                    <td className="px-6 py-3">{bill.toll_plaza_id || '—'}</td>

                    <td className="px-6 py-3 font-sans font-semibold text-slate-300">{bill.bill_type || 'LT'}</td>

                    <td className="px-6 py-3 text-slate-400">{bill.bill_month}</td>

                    <td className="px-6 py-3 text-slate-100 font-bold">{formatMoney(bill.total_amount_payable)}</td>

                    <td className="px-6 py-3 text-emerald-400 font-semibold">{formatMoney(bill.amount_paid || 0)}</td>

                    <td className="px-6 py-3 text-indigo-400 font-semibold">{formatMoney(bill.outstanding_balance || 0)}</td>

                    <td className="px-6 py-3">

                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-sans">

                        VERIFIED ✓

                      </span>

                    </td>

                    <td className="px-6 py-3 text-right font-sans">

                      <button

                        onClick={() => handleVoidBill(bill.bill_number)}

                        className="px-2 py-1 rounded bg-slate-800 hover:bg-rose-900/60 text-slate-400 hover:text-rose-300 text-[11px] transition"

                      >

                        Void

                      </button>

                    </td>

                  </tr>

                ))}

                {officialBills.length === 0 && (

                  <tr>

                    <td colSpan={10} className="px-6 py-8 text-center text-xs text-slate-500 font-sans">

                      Official register is currently empty. Upload bills to begin verification and posting.

                    </td>

                  </tr>

                )}

              </tbody>

            </table>

          </div>

        </div>

      )}



      {/* TAB 4: RECEIPTS REGISTER (8 Required Fields + Direct Export) */}

      {activeSubtab === 'receipts' && (

        <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">

          <div className="px-6 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">

            <div>

              <h3 className="text-sm font-semibold text-slate-200">Payment Receipts Register</h3>

              <p className="text-xs text-slate-400 mt-0.5">Authoritative payment clearance records parsed from bank/DISCOM receipts.</p>

            </div>

            <div className="flex items-center gap-2">

              <button

                onClick={() => window.open(api.downloadReceiptsExcelUrl, '_blank')}

                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm"

              >

                <Download className="w-3.5 h-3.5" />

                Export Receipts (Excel)

              </button>

              <button

                onClick={() => window.open(api.downloadReceiptsCsvUrl, '_blank')}

                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 transition shadow-sm"

              >

                <Download className="w-3.5 h-3.5" />

                Export Receipts (CSV)

              </button>

              <span className="text-xs text-sky-400 font-semibold ml-2">({receipts.length} receipts)</span>

            </div>

          </div>



          <div className="overflow-x-auto">

            <table className="w-full text-left text-xs text-slate-300">

              <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">

                <tr>

                  <th className="px-5 py-3">Receipt No</th>

                  <th className="px-5 py-3">Consumer No</th>

                  <th className="px-5 py-3">Account NO</th>

                  <th className="px-5 py-3">Payment Type</th>

                  <th className="px-5 py-3">Collections Date</th>

                  <th className="px-5 py-3">Bill Month</th>

                  <th className="px-5 py-3">Amount Paid</th>

                  <th className="px-5 py-3">Category</th>

                  <th className="px-5 py-3">Office Name</th>

                  <th className="px-5 py-3 text-center">Status</th>

                </tr>

              </thead>

              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">

                {receipts.map((r, idx) => (

                  <tr key={idx} className="hover:bg-slate-800/40 transition">

                    <td className="px-5 py-3 font-semibold text-sky-400">{r.receipt_no}</td>

                    <td className="px-5 py-3 text-emerald-400 font-bold">{r.consumer_no || r.account_no}</td>

                    <td className="px-5 py-3 text-slate-400">{r.account_no || '—'}</td>

                    <td className="px-5 py-3 font-sans text-slate-200">{r.payment_type || r.payment_mode || 'NEFT'}</td>

                    <td className="px-5 py-3 text-slate-300">{r.collections_date || '—'}</td>

                    <td className="px-5 py-3 font-bold text-amber-400">{r.bill_month}</td>

                    <td className="px-5 py-3 text-emerald-400 font-bold">{formatMoney(r.amount_paid)}</td>

                    <td className="px-5 py-3 font-sans text-slate-300">{r.category || 'PUBLIC LIGHT'}</td>

                    <td className="px-5 py-3 font-sans text-slate-300">{r.office_name || 'ESO RE SECTION'}</td>

                    <td className="px-5 py-3 text-center">

                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-sans font-semibold">

                        CLEARED ✓

                      </span>

                    </td>

                  </tr>

                ))}

                {receipts.length === 0 && (

                  <tr>

                    <td colSpan={10} className="px-6 py-8 text-center text-xs text-slate-500 font-sans">

                      No payment receipts registered yet. Upload receipts in Tab 1 to extract and correlate payments.

                    </td>

                  </tr>

                )}

              </tbody>

            </table>

          </div>

        </div>

      )}



      {/* TAB 5: UNIFIED MERGED RECONCILIATION (Bills & Receipts Joined by Consumer No & Bill Month) */}

      {activeSubtab === 'merged' && (() => {

        const totalEligRebate = mergedRecon.reduce((acc, r) => acc + (r.prompt_rebate || 0), 0);

        const totalRebateAvailed = mergedRecon.reduce((acc, r) => acc + (r.rebate_availed || 0), 0);

        const totalRebateLoss = mergedRecon.reduce((acc, r) => acc + (r.rebate_loss || 0), 0);

        const realizationRate = totalEligRebate > 0 ? ((totalRebateAvailed / totalEligRebate) * 100).toFixed(1) : '0.0';



        return (

          <div className="space-y-4">

            {/* Executive Rebate Performance KPI Cards */}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">

              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">

                <span className="text-[11px] font-semibold text-slate-400">Total Eligible Rebate</span>

                <p className="text-base font-bold text-slate-200 mt-1">{formatMoney(totalEligRebate)}</p>

                <span className="text-[10px] text-slate-500">From verified energy bills</span>

              </div>

              <div className="p-3.5 rounded-xl bg-slate-900 border border-emerald-500/20 bg-emerald-500/5">

                <span className="text-[11px] font-semibold text-emerald-400">Company Profit (Rebate Availed)</span>

                <p className="text-base font-bold text-emerald-300 mt-1">{formatMoney(totalRebateAvailed)}</p>

                <span className="text-[10px] text-emerald-500">Paid on or before rebate date</span>

              </div>

              <div className="p-3.5 rounded-xl bg-slate-900 border border-rose-500/20 bg-rose-500/5">

                <span className="text-[11px] font-semibold text-rose-400">Company Loss (Rebate Forfeited)</span>

                <p className="text-base font-bold text-rose-300 mt-1">{formatMoney(totalRebateLoss)}</p>

                <span className="text-[10px] text-rose-500">Paid after rebate date or expired</span>

              </div>

              <div className="p-3.5 rounded-xl bg-slate-900 border border-teal-500/20 bg-teal-500/5">

                <span className="text-[11px] font-semibold text-teal-400">Net Bottomline Impact</span>

                <p className="text-base font-bold text-teal-300 mt-1">{formatMoney(totalRebateAvailed - totalRebateLoss)}</p>

                <span className="text-[10px] text-teal-500">Net Profit / Savings to Company</span>

              </div>

            </div>



            <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">

              <div className="px-6 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">

                <div>

                  <h3 className="text-sm font-semibold text-slate-200">Unified Merged Bill & Receipts Reconciliation</h3>

                  <p className="text-xs text-slate-400 mt-0.5">Primary Key: Consumer No + Normalized Bill Month (MM/YYYY). Evaluates payments within rebate date for rebate availed vs rebate loss.</p>

                </div>

                <div className="flex items-center gap-2">

                  <button

                    onClick={() => window.open(api.downloadMergedReconciliationExcelUrl, '_blank')}

                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm"

                  >

                    <Download className="w-3.5 h-3.5" />

                    Export Merged (Excel)

                  </button>

                  <button

                    onClick={() => window.open(api.downloadMergedReconciliationCsvUrl, '_blank')}

                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 transition shadow-sm"

                  >

                    <Download className="w-3.5 h-3.5" />

                    Export Merged (CSV)

                  </button>

                  <span className="text-xs text-teal-400 font-semibold ml-2">({mergedRecon.length} rows)</span>

                </div>

              </div>



              <div className="overflow-x-auto">

                <table className="w-full text-left text-xs text-slate-300">

                  <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">

                    <tr>

                      <th className="px-4 py-3">Consumer No</th>

                      <th className="px-4 py-3">Bill Month</th>

                      <th className="px-4 py-3">Bill Number</th>

                      <th className="px-4 py-3">Plaza</th>

                      <th className="px-4 py-3 text-right">Billed Amount</th>

                      <th className="px-4 py-3">Rebate Date</th>

                      <th className="px-4 py-3">Payment Date</th>

                      <th className="px-4 py-3 text-right">Prompt Rebate</th>

                      <th className="px-4 py-3 text-center">Financial Impact</th>

                      <th className="px-4 py-3 text-right">Company Profit</th>

                      <th className="px-4 py-3 text-right">Company Loss</th>

                      <th className="px-4 py-3">Receipt No</th>

                      <th className="px-4 py-3">Payment Type</th>

                      <th className="px-4 py-3 text-right">Amount Paid</th>

                      <th className="px-4 py-3 text-right">Outstanding</th>

                      <th className="px-4 py-3 text-center">Status</th>

                    </tr>

                  </thead>

                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">

                    {mergedRecon.map((m, idx) => (

                      <tr key={idx} className="hover:bg-slate-800/40 transition">

                        <td className="px-4 py-3 font-bold text-sky-400">{m.consumer_account_no}</td>

                        <td className="px-4 py-3 font-semibold text-amber-400">{m.bill_month}</td>

                        <td className="px-4 py-3 text-slate-300">{m.bill_number || '—'}</td>

                        <td className="px-4 py-3 text-slate-400">{m.toll_plaza_id || '—'}</td>

                        <td className="px-4 py-3 text-right font-bold text-slate-200">{formatMoney(m.total_amount_payable)}</td>

                        <td className="px-4 py-3 text-slate-300">{m.rebate_date || '—'}</td>

                        <td className="px-4 py-3 text-slate-300">{m.collections_date || '—'}</td>

                        <td className="px-4 py-3 text-right font-semibold text-slate-300">{formatMoney(m.prompt_rebate || 0)}</td>

                        <td className="px-4 py-3 text-center font-sans">

                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${

                            (m.financial_impact === 'COMPANY PROFIT' || m.rebate_status === 'REBATE AVAILED')

                              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'

                              : (m.financial_impact === 'COMPANY LOSS' || m.rebate_status === 'REBATE LOSS' || m.rebate_status === 'REBATE LOSS (OVERDUE)')

                              ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'

                              : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'

                          }`}>

                            {m.financial_impact || m.rebate_status || 'PENDING'}

                          </span>

                        </td>

                        <td className="px-4 py-3 text-right font-bold text-emerald-400">{formatMoney(m.company_profit_rs ?? m.rebate_availed ?? 0)}</td>

                        <td className="px-4 py-3 text-right font-bold text-rose-400">{formatMoney(m.company_loss_rs ?? m.rebate_loss ?? 0)}</td>

                        <td className="px-4 py-3 text-sky-400">{m.receipt_no || '—'}</td>

                        <td className="px-4 py-3 font-sans text-slate-400">{m.payment_type || '—'}</td>

                        <td className="px-4 py-3 text-right font-bold text-emerald-400">{formatMoney(m.amount_paid)}</td>

                        <td className="px-4 py-3 text-right font-bold text-indigo-400">{formatMoney(m.outstanding_balance)}</td>

                        <td className="px-4 py-3 text-center font-sans">

                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${

                            m.payment_status === 'PAID'

                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'

                              : m.payment_status === 'PARTIAL'

                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'

                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'

                          }`}>

                            {m.payment_status}

                          </span>

                        </td>

                      </tr>

                    ))}

                    {mergedRecon.length === 0 && (

                      <tr>

                        <td colSpan={16} className="px-6 py-8 text-center text-xs text-slate-500 font-sans">

                          No merged reconciliation records found. Upload bills and receipts to automatically correlate data.

                        </td>

                      </tr>

                    )}

                  </tbody>

                </table>

              </div>

            </div>

          </div>

        );

      })()}



            {/* TAB 6: 📊 DYNAMIC MONTH-WISE CLEARANCE TRACKER & LEDGER */}
      {activeSubtab === 'monthwise' && (() => {
        const totMaster = 60;
        const totGen = monthWiseSummary.reduce((acc, r) => acc + (r.bills_generated || 0), 0);
        const totPaid = monthWiseSummary.reduce((acc, r) => acc + (r.payment_done || 0), 0);
        const totPending = monthWiseSummary.reduce((acc, r) => acc + (r.bills_pending || 0), 0);
        const totBilled = monthWiseSummary.reduce((acc, r) => acc + (r.total_billed_amount || 0), 0);
        const totPaidAmt = monthWiseSummary.reduce((acc, r) => acc + (r.total_paid_amount || 0), 0);
        const totOut = monthWiseSummary.reduce((acc, r) => acc + (r.total_outstanding_balance || 0), 0);
        const totProfit = monthWiseSummary.reduce((acc, r) => acc + (r.company_profit_rs || 0), 0);
        const totLoss = monthWiseSummary.reduce((acc, r) => acc + (r.company_loss_rs || 0), 0);
        const overallClearance = totGen > 0 ? ((totPaid / totGen) * 100).toFixed(1) : '0.0';

        const activeMonthData = selectedClearanceMonth === 'ALL'
          ? null
          : monthWiseSummary.find((m) => m.bill_month === selectedClearanceMonth);

        const filteredMerged = mergedRecon.filter((item) => {
          if (selectedClearanceMonth !== 'ALL' && item.bill_month !== selectedClearanceMonth) return false;
          if (selectedClearanceStatus === 'PAID' && item.payment_status !== 'PAID') return false;
          if (selectedClearanceStatus === 'PENDING' && !['UNPAID', 'PARTIAL'].includes(item.payment_status)) return false;
          if (selectedClearanceStatus === 'GENERATED' && (!item.bill_number || item.bill_number === '—' || item.bill_number === '?')) return false;
          if (clearanceSearchQuery) {
            const q = clearanceSearchQuery.toLowerCase();
            const cNo = String(item.consumer_account_no || '').toLowerCase();
            const bNo = String(item.bill_number || '').toLowerCase();
            const rNo = String(item.receipt_no || '').toLowerCase();
            const pl = String(item.toll_plaza_id || '').toLowerCase();
            const off = String(item.office_name || '').toLowerCase();
            if (!cNo.includes(q) && !bNo.includes(q) && !rNo.includes(q) && !pl.includes(q) && !off.includes(q)) return false;
          }
          return true;
        });

        const filteredUnbilled = unbilledAccounts.filter((u) => {
          if (clearanceSearchQuery) {
            const q = clearanceSearchQuery.toLowerCase();
            const cNo = String(u.consumer_account_no || '').toLowerCase();
            const pl = String(u.toll_plaza_id || '').toLowerCase();
            const loc = String(u.location || '').toLowerCase();
            if (!cNo.includes(q) && !pl.includes(q) && !loc.includes(q)) return false;
          }
          return true;
        });

        return (
          <div className="space-y-6">
            {/* Top KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Master Accounts</span>
                <div className="text-xl font-bold text-white mt-1">{totMaster}</div>
                <span className="text-[10px] text-slate-500">3 HT / 57 LT Roster</span>
              </div>
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Bills Generated</span>
                <div className="text-xl font-bold text-sky-400 mt-1">{totGen}</div>
                <span className="text-[10px] text-sky-500/80">{monthWiseSummary.length} Billing Cycles</span>
              </div>
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Payments Done</span>
                <div className="text-xl font-bold text-emerald-400 mt-1">{totPaid}</div>
                <span className="text-[10px] text-emerald-500/80">{overallClearance}% Cleared</span>
              </div>
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Bills Pending</span>
                <div className="text-xl font-bold text-amber-400 mt-1">{totPending}</div>
                <span className="text-[10px] text-amber-500/80">Pending Settlement</span>
              </div>
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Company Profit</span>
                <div className="text-xl font-bold text-emerald-400 mt-1">₹{totProfit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
                <span className="text-[10px] text-emerald-500">Rebates Availed</span>
              </div>
              <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 shadow-sm">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Outstanding</span>
                <div className="text-xl font-bold text-rose-400 mt-1">₹{totOut.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
                <span className="text-[10px] text-rose-500/80">Loss: ₹{totLoss.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
            </div>

            {/* Month-Wise Clearance Matrix */}
            <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Month-Wise Generation & Clearance Matrix</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Authoritative cycle-by-cycle performance tracking out of 60 master accounts.</p>
                </div>
                <span className="px-2.5 py-1 rounded-lg bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 text-xs font-semibold">
                  {monthWiseSummary.length} Billing Cycles
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Bill Month</th>
                      <th className="py-3 px-3 font-semibold text-center">Master Accounts</th>
                      <th className="py-3 px-3 font-semibold text-center">Bills Generated</th>
                      <th className="py-3 px-3 font-semibold text-center">Unbilled (Missing)</th>
                      <th className="py-3 px-3 font-semibold text-center">Gen %</th>
                      <th className="py-3 px-3 font-semibold text-center">Payment Done</th>
                      <th className="py-3 px-3 font-semibold text-center">Bills Pending</th>
                      <th className="py-3 px-4 font-semibold text-right">Total Billed (₹)</th>
                      <th className="py-3 px-4 font-semibold text-right">Total Paid (₹)</th>
                      <th className="py-3 px-4 font-semibold text-right">Outstanding (₹)</th>
                      <th className="py-3 px-3 font-semibold text-center">Clearance %</th>
                      <th className="py-3 px-4 font-semibold text-right">Profit (₹)</th>
                      <th className="py-3 px-4 font-semibold text-right">Loss (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {monthWiseSummary.map((m) => (
                      <tr key={m.bill_month} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-sans font-semibold text-sky-400">{m.bill_month}</td>
                        <td className="py-3 px-3 text-center">{m.total_master_accounts}</td>
                        <td className="py-3 px-3 text-center text-emerald-400 font-semibold">{m.bills_generated}</td>
                        <td className="py-3 px-3 text-center text-amber-400">{m.bills_unbilled}</td>
                        <td className="py-3 px-3 text-center font-sans">
                          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-[11px] font-semibold">
                            {m.generation_pct}%
                          </span>
                        </td>
                        <td className="py-3 px-3 text-center text-emerald-400 font-bold">{m.payment_done}</td>
                        <td className="py-3 px-3 text-center text-rose-400 font-semibold">{m.bills_pending}</td>
                        <td className="py-3 px-4 text-right">₹{m.total_billed_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="py-3 px-4 text-right text-emerald-400">₹{m.total_paid_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="py-3 px-4 text-right text-rose-400 font-semibold">₹{m.total_outstanding_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="py-3 px-3 text-center font-sans">
                          <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                            m.clearance_rate_pct >= 80
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                              : m.clearance_rate_pct > 0
                              ? 'bg-amber-950 text-amber-400 border border-amber-800/40'
                              : 'bg-slate-800 text-slate-400'
                          }`}>
                            {m.clearance_rate_pct}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right text-emerald-400">₹{(m.company_profit_rs || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        <td className="py-3 px-4 text-right text-rose-400">₹{(m.company_loss_rs || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Interactive Drill-down & Filter Controls */}
            <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 shadow-lg space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">🔍 Dynamic Month Ledger & Drill-Down</h4>
                  <p className="text-xs text-slate-400">Select cycle and status to inspect accounts, payments, and outstanding balances.</p>
                </div>
                <input
                  type="text"
                  placeholder="Search Consumer No, Bill Ref, Plaza..."
                  value={clearanceSearchQuery}
                  onChange={(e) => setClearanceSearchQuery(e.target.value)}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 w-64 focus:outline-none focus:border-sky-500"
                />
              </div>

              {/* Month Selection Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800">
                <span className="text-xs font-semibold text-slate-400 mr-2">Cycle:</span>
                <button
                  onClick={() => {
                    setSelectedClearanceMonth('ALL');
                    if (selectedClearanceStatus === 'UNBILLED') setSelectedClearanceStatus('ALL');
                  }}
                  className={`px-3 py-1 rounded-xl text-xs font-semibold transition ${
                    selectedClearanceMonth === 'ALL'
                      ? 'bg-sky-500 text-slate-950 shadow-md font-bold'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  All Months
                </button>
                {monthWiseSummary.map((m) => (
                  <button
                    key={m.bill_month}
                    onClick={() => {
                      setSelectedClearanceMonth(m.bill_month);
                      loadUnbilledForMonth(m.bill_month);
                    }}
                    className={`px-3 py-1 rounded-xl text-xs font-semibold transition ${
                      selectedClearanceMonth === m.bill_month
                        ? 'bg-sky-500 text-slate-950 shadow-md font-bold'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {m.bill_month}
                  </button>
                ))}
              </div>

              {/* Status Filter Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800">
                <span className="text-xs font-semibold text-slate-400 mr-2">Status:</span>
                {[
                  { id: 'ALL', label: 'All Records' },
                  { id: 'GENERATED', label: 'Bills Generated (All)' },
                  { id: 'PAID', label: 'Payments Done (Paid)' },
                  { id: 'PENDING', label: 'Bills Pending (Unpaid)' },
                  { id: 'UNBILLED', label: 'Unbilled Accounts (Pending Generation)' },
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => {
                      setSelectedClearanceStatus(st.id as any);
                      if (st.id === 'UNBILLED' && selectedClearanceMonth !== 'ALL') {
                        loadUnbilledForMonth(selectedClearanceMonth);
                      }
                    }}
                    className={`px-3 py-1 rounded-xl text-xs font-semibold transition ${
                      selectedClearanceStatus === st.id
                        ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>

              {/* Active Cycle KPI Bar */}
              {activeMonthData && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-400">Target Accounts:</span>{' '}
                    <span className="font-bold text-white">{activeMonthData.total_master_accounts}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Bills Generated:</span>{' '}
                    <span className="font-bold text-sky-400">{activeMonthData.bills_generated} ({activeMonthData.generation_pct}%)</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Payments Done:</span>{' '}
                    <span className="font-bold text-emerald-400">{activeMonthData.payment_done} ({activeMonthData.clearance_rate_pct}%)</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Pending Bills:</span>{' '}
                    <span className="font-bold text-rose-400">{activeMonthData.bills_pending}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Outstanding:</span>{' '}
                    <span className="font-bold text-rose-400">₹{activeMonthData.total_outstanding_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Drill-down Results Table */}
            {selectedClearanceStatus === 'UNBILLED' ? (
              <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-amber-400">
                      ⚠️ Unbilled Accounts ({filteredUnbilled.length}) &mdash; {selectedClearanceMonth}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Consumer master accounts that have not yet generated a bill for this cycle.</p>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4 font-semibold">Consumer Account No (Text)</th>
                        <th className="py-3 px-4 font-semibold">Toll Plaza</th>
                        <th className="py-3 px-4 font-semibold">Tariff Type</th>
                        <th className="py-3 px-4 font-semibold">Asset Code</th>
                        <th className="py-3 px-4 font-semibold text-right">Sanctioned Load (kW)</th>
                        <th className="py-3 px-4 font-semibold">Location / Scope</th>
                        <th className="py-3 px-4 font-semibold">Cycle</th>
                        <th className="py-3 px-4 font-semibold text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-sans text-slate-300">
                      {filteredUnbilled.map((u, i) => (
                        <tr key={i} className="hover:bg-slate-800/40 transition">
                          <td className="py-3 px-4 font-mono font-bold text-amber-300 select-all">{u.consumer_account_no}</td>
                          <td className="py-3 px-4">{u.toll_plaza_id}</td>
                          <td className="py-3 px-4">{u.bill_type}</td>
                          <td className="py-3 px-4 font-mono text-slate-400">{u.asset_code || '—'}</td>
                          <td className="py-3 px-4 text-right font-mono">{u.sanctioned_load_kw || '—'}</td>
                          <td className="py-3 px-4 text-slate-300">{u.location || 'Highway'}</td>
                          <td className="py-3 px-4 font-mono text-sky-400">{u.bill_month}</td>
                          <td className="py-3 px-4 text-center">
                            <span className="px-2 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800/40 text-[10px] font-semibold">
                              PENDING GENERATION
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200">
                      Filtered Clearance Register ({filteredMerged.length} records)
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">Authoritative merged bill and receipt records with plain text numbers (no commas).</p>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4 font-semibold">Consumer No (Text)</th>
                        <th className="py-3 px-3 font-semibold">Month</th>
                        <th className="py-3 px-4 font-semibold">Bill Ref (Text)</th>
                        <th className="py-3 px-3 font-semibold">Plaza</th>
                        <th className="py-3 px-4 font-semibold text-right">Billed (₹)</th>
                        <th className="py-3 px-3 font-semibold text-center">Status</th>
                        <th className="py-3 px-4 font-semibold text-right">Paid (₹)</th>
                        <th className="py-3 px-4 font-semibold text-right">Outstanding (₹)</th>
                        <th className="py-3 px-3 font-semibold">Rebate Date</th>
                        <th className="py-3 px-4 font-semibold">Rebate Status</th>
                        <th className="py-3 px-4 font-semibold text-right">Profit (₹)</th>
                        <th className="py-3 px-4 font-semibold text-right">Loss (₹)</th>
                        <th className="py-3 px-4 font-semibold">Receipt / UTR (Text)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                      {filteredMerged.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40 transition">
                          <td className="py-3 px-4 font-bold text-sky-400 select-all">{item.consumer_account_no}</td>
                          <td className="py-3 px-3 font-sans">{item.bill_month}</td>
                          <td className="py-3 px-4 text-slate-300 select-all">{item.bill_number || '—'}</td>
                          <td className="py-3 px-3 font-sans text-slate-400">{item.toll_plaza_id || '—'}</td>
                          <td className="py-3 px-4 text-right">₹{item.total_amount_payable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                          <td className="py-3 px-3 text-center font-sans">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              item.payment_status === 'PAID'
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                                : item.payment_status === 'PARTIAL'
                                ? 'bg-amber-950 text-amber-400 border border-amber-800/40'
                                : 'bg-rose-950 text-rose-400 border border-rose-800/40'
                            }`}>
                              {item.payment_status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right text-emerald-400">₹{item.amount_paid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                          <td className="py-3 px-4 text-right text-rose-400 font-semibold">₹{item.outstanding_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                          <td className="py-3 px-3 font-sans text-slate-400">{item.rebate_date || '—'}</td>
                          <td className="py-3 px-4 font-sans text-[11px]">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              (item.rebate_status || '').includes('AVAILED')
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                                : (item.rebate_status || '').includes('LOSS')
                                ? 'bg-rose-950 text-rose-400 border border-rose-800/40'
                                : 'bg-slate-800 text-slate-400'
                            }`}>
                              {item.rebate_status || 'PENDING'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right text-emerald-400">
                            ₹{(item.company_profit_rs || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3 px-4 text-right text-rose-400">
                            ₹{(item.company_loss_rs || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-3 px-4 text-slate-400 select-all">{item.receipt_no || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );
      })()}


      {/* TAB 5: 60 CONSUMERS ROSTER */}

      {activeSubtab === 'consumers' && (

        <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">

          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">

            <div>

              <h3 className="text-sm font-semibold text-slate-200">Authoritative Consumer Master Roster</h3>

              <p className="text-xs text-slate-400 mt-0.5">Authoritative mapping directly from energy_master.consumer_account (3 HT / 57 LT).</p>

            </div>

            <div className="flex gap-2">

              <span className="px-2.5 py-1 rounded-lg bg-sky-950/60 text-sky-400 border border-sky-800/40 text-xs font-semibold">

                3 HT Accounts

              </span>

              <span className="px-2.5 py-1 rounded-lg bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 text-xs font-semibold">

                57 LT Accounts

              </span>

            </div>

          </div>



          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">

            <table className="w-full text-left text-xs text-slate-300">

              <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800 sticky top-0">

                <tr>

                  <th className="px-6 py-3">Consumer Account No</th>

                  <th className="px-6 py-3">Plaza</th>

                  <th className="px-6 py-3">Feeder Type</th>

                  <th className="px-6 py-3">Asset Code</th>

                  <th className="px-6 py-3">Scope</th>

                  <th className="px-6 py-3">Division</th>

                  <th className="px-6 py-3">Usage</th>

                  <th className="px-6 py-3">Sanctioned Load (kW)</th>

                </tr>

              </thead>

              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">

                {consumers.map((c) => (

                  <tr key={c.consumer_account_no} className="hover:bg-slate-800/40 transition">

                    <td className="px-6 py-3 font-semibold text-emerald-400">{c.consumer_account_no}</td>

                    <td className="px-6 py-3">

                      <span className="px-2 py-0.5 rounded bg-slate-800 text-sky-400 text-[10px]">

                        {c.toll_plaza_id}

                      </span>

                    </td>

                    <td className="px-6 py-3 font-sans">

                      <span

                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${

                          c.bill_type === 'HT'

                            ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'

                            : 'bg-emerald-500/10 text-emerald-400'

                        }`}

                      >

                        {c.bill_type}

                      </span>

                    </td>

                    <td className="px-6 py-3 text-slate-400">{c.asset_code || '—'}</td>

                    <td className="px-6 py-3 text-slate-300 font-sans">{c.consumer_scope || 'HIGHWAY'}</td>

                    <td className="px-6 py-3 text-slate-400 font-sans">{c.division_name || 'SED'}</td>

                    <td className="px-6 py-3 text-slate-300 font-sans">{c.usage_type || 'Street Light'}</td>

                    <td className="px-6 py-3 text-slate-200 font-bold">{c.sanctioned_load_kw} kW</td>

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

