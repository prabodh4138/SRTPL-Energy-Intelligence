import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { CandidateResult, OfficialBill, ReviewQueueItem, ReceiptItem } from '../types';
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
} from 'lucide-react';

export const BillReconciliationView: React.FC = () => {
  const [activeSubtab, setActiveSubtab] = useState<'extract' | 'review' | 'register' | 'receipts' | 'consumers'>('extract');

  // Extraction State
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [candidates, setCandidates] = useState<CandidateResult[]>([]);

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

  const loadTabData = async () => {
    setLoadingData(true);
    try {
      if (activeSubtab === 'review') {
        const res = await api.getReviewQueue();
        setReviewQueue(res.items || []);
      } else if (activeSubtab === 'register') {
        const res = await api.getOfficialRegister();
        setOfficialBills(res.bills || []);
      } else if (activeSubtab === 'receipts') {
        const res = await api.getReceipts();
        setReceipts(res.receipts || []);
      } else if (activeSubtab === 'consumers') {
        const res = await api.getConsumers();
        setConsumers(res.consumers || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingData(false);
    }
  };

  const handleRunExtraction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFiles || selectedFiles.length === 0) {
      alert('Please select one or more PDF or ZIP files to extract.');
      return;
    }

    setExtracting(true);
    try {
      const fileArr = Array.from(selectedFiles);
      const res = await api.uploadBills(fileArr);
      setCandidates(res.candidates || []);
      setSelectedFiles(null);
    } catch (err: any) {
      alert('Extraction failed: ' + err.message);
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
            4. Receipts & Allocations
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
            5. Consumer Master (60)
          </button>
        </div>

        {/* Quick export buttons */}
        <div className="flex items-center gap-2">
          <a
            href={api.downloadBillsExcelUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            Export Excel
          </a>
          <a
            href={api.downloadBillsCsvUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            Export CSV
          </a>
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
            </form>
          </div>

          {/* Extracted Candidates Table */}
          {candidates.length > 0 && (
            <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200">Candidate Extraction Results</h3>
                <span className="text-xs text-emerald-400 font-semibold">{candidates.length} processed items</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
                    <tr>
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
                    {candidates.map((cand, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition">
                        <td className="px-6 py-3 text-slate-300 font-sans">{cand.file}</td>
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
                            className={`px-2.5 py-1 rounded-full text-[10px] font-bold font-sans ${
                              cand.result === 'VERIFIED'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : cand.result === 'REVIEW'
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {cand.result} {cand.result === 'VERIFIED' ? '✓' : ''}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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

      {/* TAB 4: RECEIPTS */}
      {activeSubtab === 'receipts' && (
        <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">Payment Receipts Register</h3>
            <span className="text-xs text-sky-400 font-semibold">{receipts.length} receipts</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/40 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3">Receipt No</th>
                  <th className="px-6 py-3">Account No</th>
                  <th className="px-6 py-3">Bill Month</th>
                  <th className="px-6 py-3">Amount Paid</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {receipts.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-3 font-semibold text-sky-400">{r.receipt_no}</td>
                    <td className="px-6 py-3 text-slate-200">{r.account_no}</td>
                    <td className="px-6 py-3 text-slate-400">{r.bill_month}</td>
                    <td className="px-6 py-3 text-emerald-400 font-bold">{formatMoney(r.amount_paid)}</td>
                    <td className="px-6 py-3">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-sans">
                        CLEARED ✓
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

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
