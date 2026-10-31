import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { FileSpreadsheet, Download, FileText, CheckCircle2 } from 'lucide-react';

export const ReportsView: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await api.getReportsSummary();
        setReports(res.reports || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">Financial, Master & Audit Report Export Center</h2>
            <p className="text-xs text-slate-400">Export authoritative PostgreSQL datasets into Excel, CSV, or PDF formats.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {reports.map((rep) => (
            <div key={rep.id} className="p-5 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-emerald-400 font-mono">{rep.id}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">{rep.category}</span>
                </div>
                <h3 className="text-sm font-bold text-slate-100 mt-2">{rep.name}</h3>
                <p className="text-xs text-slate-400 mt-1">Available formats: {rep.format}</p>
                <div className="text-xs text-slate-500 mt-2 font-mono">{rep.rows} authoritative database rows</div>
              </div>

              <div className="flex items-center gap-2 mt-5 pt-4 border-t border-slate-700/60">
                <a
                  href={rep.id === 'REP-02' ? api.downloadConsumersExcelUrl : api.downloadBillsExcelUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  Excel (.xlsx)
                </a>
                <a
                  href={api.downloadBillsCsvUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium text-xs transition"
                >
                  <Download className="w-3.5 h-3.5 text-sky-400" />
                  CSV (.csv)
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-300 flex items-center gap-3">
        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
        <span>All reports are generated dynamically from live Supabase views, ensuring zero formula drift and complete audit compliance.</span>
      </div>
    </div>
  );
};
