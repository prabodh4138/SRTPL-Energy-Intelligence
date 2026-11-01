import React, { useEffect, useState, useMemo } from 'react';
import { api } from '../api';
import {
  FileSpreadsheet,
  Download,
  Filter,
  Columns,
  Search,
  RotateCcw,
  CheckSquare,
  Square,
  CheckCircle2,
  AlertCircle,
  Building2,
  Calendar,
  Layers,
  Sparkles,
  Zap,
} from 'lucide-react';

interface ColumnDef {
  key: string;
  label: string;
  category: 'core' | 'financial' | 'meter' | 'audit';
}

const ALL_BILL_COLUMNS: ColumnDef[] = [
  // Core Reconciliation
  { key: 'consumer_account_no', label: 'Consumer A/C No.', category: 'core' },
  { key: 'bill_month', label: 'Bill Month', category: 'core' },
  { key: 'bill_number', label: 'Bill Number', category: 'core' },
  { key: 'toll_plaza_id', label: 'Toll Plaza', category: 'core' },
  { key: 'bill_type', label: 'Feeder (HT/LT)', category: 'core' },
  { key: 'consumer_scope', label: 'Scope (PLAZA/HIGHWAY)', category: 'core' },
  { key: 'meter_sl_no', label: 'Meter Sl. No.', category: 'core' },
  { key: 'financial_year', label: 'Financial Year', category: 'core' },
  { key: 'bill_period', label: 'Bill Period', category: 'core' },
  { key: 'bill_days', label: 'Bill Days', category: 'core' },
  { key: 'bill_basis', label: 'Bill Basis', category: 'core' },
  { key: 'payment_status', label: 'Payment Status', category: 'core' },

  // Financial & Charges
  { key: 'total_billed_kwh', label: 'Total Units (kWh)', category: 'financial' },
  { key: 'energy_charges', label: 'Energy Charges (₹)', category: 'financial' },
  { key: 'demand_charge', label: 'Demand Charge (₹)', category: 'financial' },
  { key: 'tod_incentive', label: 'TOD Incentive (₹)', category: 'financial' },
  { key: 'tod_surcharge', label: 'TOD Surcharge (₹)', category: 'financial' },
  { key: 'electricity_charges', label: 'Electricity Charges (₹)', category: 'financial' },
  { key: 'electricity_duty', label: 'Electricity Duty (₹)', category: 'financial' },
  { key: 'meter_rent', label: 'Meter Rent (₹)', category: 'financial' },
  { key: 'customer_service_charge', label: 'Customer Service (₹)', category: 'financial' },
  { key: 'dps_rs', label: 'DPS (₹)', category: 'financial' },
  { key: 'current_total', label: 'Current Total (₹)', category: 'financial' },
  { key: 'prompt_rebate', label: 'Prompt Rebate (₹)', category: 'financial' },
  { key: 'total_amount_payable', label: 'Total Payable (₹)', category: 'financial' },
  { key: 'amount_paid', label: 'Amount Paid (₹)', category: 'financial' },
  { key: 'outstanding_balance', label: 'Outstanding Balance (₹)', category: 'financial' },

  // Meter & Demand
  { key: 'contract_demand', label: 'Contract Demand', category: 'meter' },
  { key: 'sanctioned_load_kw', label: 'Sanctioned Load (kW)', category: 'meter' },
  { key: 'security_deposit', label: 'Security Deposit (₹)', category: 'meter' },
  { key: 'md', label: 'Recorded MD', category: 'meter' },
  { key: 'cuml_md_kw', label: 'CUML MD-KW', category: 'meter' },
  { key: 'cuml_md_kva', label: 'CUML MD-KVA', category: 'meter' },
  { key: 'slab_normal_kwh', label: 'Slab Normal (kWh)', category: 'meter' },
  { key: 'slab_peak_kwh', label: 'Slab Peak (kWh)', category: 'meter' },
  { key: 'slab_solar_kwh', label: 'Slab Solar (kWh)', category: 'meter' },

  // Audit & Jurisdiction
  { key: 'tariff_category', label: 'Tariff Category', category: 'audit' },
  { key: 'division_name', label: 'Division', category: 'audit' },
  { key: 'sub_division', label: 'Sub-Division', category: 'audit' },
  { key: 'section', label: 'Section', category: 'audit' },
  { key: 'rebate_date', label: 'Rebate Date', category: 'audit' },
  { key: 'due_date', label: 'Due Date', category: 'audit' },
  { key: 'verification_status', label: 'Verification Status', category: 'audit' },
  { key: 'source_filename', label: 'Source File', category: 'audit' },
  { key: 'location', label: 'Location', category: 'audit' },
];

const PRESETS: Record<string, string[]> = {
  reconciliation: [
    'consumer_account_no',
    'bill_month',
    'bill_number',
    'toll_plaza_id',
    'meter_sl_no',
    'total_billed_kwh',
    'energy_charges',
    'total_amount_payable',
    'amount_paid',
    'outstanding_balance',
    'payment_status',
  ],
  financial: [
    'consumer_account_no',
    'bill_month',
    'bill_number',
    'total_billed_kwh',
    'energy_charges',
    'demand_charge',
    'electricity_charges',
    'electricity_duty',
    'meter_rent',
    'dps_rs',
    'total_amount_payable',
    'amount_paid',
    'outstanding_balance',
  ],
  meter: [
    'consumer_account_no',
    'meter_sl_no',
    'toll_plaza_id',
    'bill_type',
    'contract_demand',
    'sanctioned_load_kw',
    'md',
    'cuml_md_kw',
    'cuml_md_kva',
    'total_billed_kwh',
    'security_deposit',
  ],
  audit: [
    'consumer_account_no',
    'bill_number',
    'division_name',
    'sub_division',
    'section',
    'tariff_category',
    'rebate_date',
    'due_date',
    'verification_status',
    'source_filename',
  ],
};

export const ReportsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'custom' | 'packs'>('custom');
  const [reports, setReports] = useState<any[]>([]);
  const [billsData, setBillsData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  // Filters State
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [selectedPlazas, setSelectedPlazas] = useState<string[]>([]);
  const [selectedFYears, setSelectedFYears] = useState<string[]>([]);
  const [selectedFeeder, setSelectedFeeder] = useState<string>('ALL');
  const [selectedScope, setSelectedScope] = useState<string>('ALL');
  const [selectedPaymentStatus, setSelectedPaymentStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Column Selector State
  const [selectedColumns, setSelectedColumns] = useState<string[]>(PRESETS.reconciliation);
  const [showColumnPicker, setShowColumnPicker] = useState<boolean>(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [sumRes, regRes] = await Promise.all([
          api.getReportsSummary().catch(() => ({ reports: [] })),
          api.getOfficialRegister().catch(() => ({ bills: [] })),
        ]);
        setReports(sumRes.reports || []);
        const rawBills = regRes.bills || [];
        setBillsData(rawBills);

        // Auto-select all available months, plazas, fyears initially
        const months = Array.from(new Set(rawBills.map((b: any) => b.bill_month).filter(Boolean))) as string[];
        const plazas = Array.from(new Set(rawBills.map((b: any) => b.toll_plaza_id).filter(Boolean))) as string[];
        const fyears = Array.from(new Set(rawBills.map((b: any) => b.financial_year).filter(Boolean))) as string[];
        setSelectedMonths(months);
        setSelectedPlazas(plazas);
        setSelectedFYears(fyears);
      } catch (err) {
        console.error('Failed to load reports data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Distinct Options for Dropdowns / Badges
  const distinctMonths = useMemo(() => {
    return Array.from(new Set(billsData.map((b) => b.bill_month).filter(Boolean))).sort() as string[];
  }, [billsData]);

  const distinctPlazas = useMemo(() => {
    return Array.from(new Set(billsData.map((b) => b.toll_plaza_id).filter(Boolean))).sort() as string[];
  }, [billsData]);

  const distinctFYears = useMemo(() => {
    return Array.from(new Set(billsData.map((b) => b.financial_year).filter(Boolean))).sort() as string[];
  }, [billsData]);

  // Filtered Records
  const filteredData = useMemo(() => {
    return billsData.filter((row) => {
      // Month Filter
      if (selectedMonths.length > 0 && row.bill_month && !selectedMonths.includes(row.bill_month)) {
        return false;
      }
      // Plaza Filter
      if (selectedPlazas.length > 0 && row.toll_plaza_id && !selectedPlazas.includes(row.toll_plaza_id)) {
        return false;
      }
      // Financial Year Filter
      if (selectedFYears.length > 0 && row.financial_year && !selectedFYears.includes(row.financial_year)) {
        return false;
      }
      // Feeder Filter
      if (selectedFeeder !== 'ALL' && row.bill_type !== selectedFeeder) {
        return false;
      }
      // Scope Filter
      if (selectedScope !== 'ALL' && row.consumer_scope !== selectedScope) {
        return false;
      }
      // Payment Status Filter
      if (selectedPaymentStatus !== 'ALL' && row.payment_status !== selectedPaymentStatus) {
        return false;
      }
      // Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const searchFields = [
          row.consumer_account_no,
          row.bill_number,
          row.meter_sl_no,
          row.location,
          row.section,
          row.division_name,
        ]
          .filter(Boolean)
          .map(String)
          .join(' ')
          .toLowerCase();
        if (!searchFields.includes(q)) return false;
      }
      return true;
    });
  }, [
    billsData,
    selectedMonths,
    selectedPlazas,
    selectedFYears,
    selectedFeeder,
    selectedScope,
    selectedPaymentStatus,
    searchQuery,
  ]);

  // Summary Metrics
  const summaryMetrics = useMemo(() => {
    const totalUnits = filteredData.reduce((acc, r) => acc + (Number(r.total_billed_kwh) || 0), 0);
    const totalPayable = filteredData.reduce((acc, r) => acc + (Number(r.total_amount_payable) || 0), 0);
    const totalPaid = filteredData.reduce((acc, r) => acc + (Number(r.amount_paid) || 0), 0);
    const totalBal = filteredData.reduce((acc, r) => acc + (Number(r.outstanding_balance) || 0), 0);
    const realization = totalPayable > 0 ? (totalPaid / totalPayable) * 100 : 0;
    return {
      count: filteredData.length,
      totalUnits,
      totalPayable,
      totalPaid,
      totalBal,
      realization,
    };
  }, [filteredData]);

  // Column Presets and Toggle Helpers
  const toggleColumn = (key: string) => {
    if (selectedColumns.includes(key)) {
      if (selectedColumns.length > 1) {
        setSelectedColumns(selectedColumns.filter((c) => c !== key));
      }
    } else {
      setSelectedColumns([...selectedColumns, key]);
    }
  };

  const selectAllColumns = () => {
    setSelectedColumns(ALL_BILL_COLUMNS.map((c) => c.key));
  };

  const deselectAllColumns = () => {
    setSelectedColumns(['consumer_account_no', 'bill_number', 'total_amount_payable']);
  };

  const columnLabelMap = useMemo(() => {
    const map: Record<string, string> = {};
    ALL_BILL_COLUMNS.forEach((c) => {
      map[c.key] = c.label;
    });
    return map;
  }, []);

  // Export Handlers
  const handleExport = async (format: 'xlsx' | 'csv') => {
    if (filteredData.length === 0) {
      alert('Cannot export: No rows match your active filter criteria.');
      return;
    }
    try {
      setExporting(true);
      await api.exportCustomReport({
        format,
        title: 'Bill_Reconciliation_Custom_View',
        columns: selectedColumns,
        labels: columnLabelMap,
        rows: filteredData,
      });
    } catch (e: any) {
      console.error(e);
      // Fallback to client-side CSV download if network fails
      if (format === 'csv') {
        const headerRow = selectedColumns.map((c) => `"${columnLabelMap[c] || c}"`).join(',');
        const dataRows = filteredData.map((row) =>
          selectedColumns
            .map((col) => {
              const val = row[col] === null || row[col] === undefined ? '' : String(row[col]);
              return `"${val.replace(/"/g, '""')}"`;
            })
            .join(',')
        );
        const csvContent = '\uFEFF' + [headerRow, ...dataRows].join('\r\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `SRTPL_Custom_Reconciliation_Report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert('Export failed: ' + (e.message || String(e)));
      }
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Tab Navigation */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-100">Financial, Master & Audit Report Export Center</h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Custom Studio Active
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Design custom analytical views with multi-parameter filtering, grilled column toggles, and instant Excel / CSV exports.
              </p>
            </div>
          </div>

          {/* Tab Selector */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-800/80 rounded-2xl border border-slate-700/60 shrink-0">
            <button
              onClick={() => setActiveTab('custom')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                activeTab === 'custom'
                  ? 'bg-sky-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Custom View Studio
            </button>
            <button
              onClick={() => setActiveTab('packs')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                activeTab === 'packs'
                  ? 'bg-sky-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Pre-configured Packs (REP 01-04)
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'custom' ? (
        <div className="space-y-6">
          {/* 1. Multi-Parameter Filters Toolbar */}
          <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wider">
                <Filter className="w-4 h-4 text-sky-400" />
                <span>Multi-Parameter Slicing & Drilling</span>
              </div>
              <button
                onClick={() => {
                  setSelectedMonths(distinctMonths);
                  setSelectedPlazas(distinctPlazas);
                  setSelectedFYears(distinctFYears);
                  setSelectedFeeder('ALL');
                  setSelectedScope('ALL');
                  setSelectedPaymentStatus('ALL');
                  setSearchQuery('');
                }}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-sky-400 transition"
              >
                <RotateCcw className="w-3 h-3" />
                Reset All Filters
              </button>
            </div>

            {/* Filter Rows */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Toll Plaza Filter */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">Toll Plaza</span>
                  <div className="flex items-center gap-1.5 text-[10px]">
                    <button
                      onClick={() => setSelectedPlazas(distinctPlazas)}
                      className="text-sky-400 hover:underline"
                    >
                      Select All
                    </button>
                    <span>·</span>
                    <button
                      onClick={() => setSelectedPlazas([])}
                      className="text-slate-500 hover:underline"
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {distinctPlazas.map((p) => {
                    const isSel = selectedPlazas.includes(p);
                    return (
                      <button
                        key={p}
                        onClick={() =>
                          setSelectedPlazas((prev) =>
                            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
                          )
                        }
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold border transition ${
                          isSel
                            ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                            : 'bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200'
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                  {distinctPlazas.length === 0 && (
                    <span className="text-xs text-slate-500 italic">No plazas found</span>
                  )}
                </div>
              </div>

              {/* Bill Month Filter */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">Bill Month</span>
                  <div className="flex items-center gap-1.5 text-[10px]">
                    <button
                      onClick={() => setSelectedMonths(distinctMonths)}
                      className="text-sky-400 hover:underline"
                    >
                      Select All
                    </button>
                    <span>·</span>
                    <button
                      onClick={() => setSelectedMonths([])}
                      className="text-slate-500 hover:underline"
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
                  {distinctMonths.map((m) => {
                    const isSel = selectedMonths.includes(m);
                    return (
                      <button
                        key={m}
                        onClick={() =>
                          setSelectedMonths((prev) =>
                            prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]
                          )
                        }
                        className={`px-2 py-0.5 rounded-lg text-[11px] font-mono border transition ${
                          isSel
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 font-bold'
                            : 'bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200'
                        }`}
                      >
                        {m}
                      </button>
                    );
                  })}
                  {distinctMonths.length === 0 && (
                    <span className="text-xs text-slate-500 italic">No months available</span>
                  )}
                </div>
              </div>

              {/* Financial Year / Period Filter */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">Period / FY</span>
                  <div className="flex items-center gap-1.5 text-[10px]">
                    <button
                      onClick={() => setSelectedFYears(distinctFYears)}
                      className="text-sky-400 hover:underline"
                    >
                      Select All
                    </button>
                    <span>·</span>
                    <button
                      onClick={() => setSelectedFYears([])}
                      className="text-slate-500 hover:underline"
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {distinctFYears.map((fy) => {
                    const isSel = selectedFYears.includes(fy);
                    return (
                      <button
                        key={fy}
                        onClick={() =>
                          setSelectedFYears((prev) =>
                            prev.includes(fy) ? prev.filter((x) => x !== fy) : [...prev, fy]
                          )
                        }
                        className={`px-2.5 py-1 rounded-lg text-xs font-mono border transition ${
                          isSel
                            ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 font-bold'
                            : 'bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200'
                        }`}
                      >
                        {fy}
                      </button>
                    );
                  })}
                  {distinctFYears.length === 0 && (
                    <span className="text-xs text-slate-500 italic">No periods available</span>
                  )}
                </div>
              </div>

              {/* Feeder & Scope Dropdowns */}
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[11px] font-semibold text-slate-300 block mb-1">Feeder</label>
                    <select
                      value={selectedFeeder}
                      onChange={(e) => setSelectedFeeder(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                    >
                      <option value="ALL">All (HT & LT)</option>
                      <option value="HT">HT Only</option>
                      <option value="LT">LT Only</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-semibold text-slate-300 block mb-1">Scope</label>
                    <select
                      value={selectedScope}
                      onChange={(e) => setSelectedScope(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                    >
                      <option value="ALL">All Scopes</option>
                      <option value="PLAZA">Plaza</option>
                      <option value="HIGHWAY">Highway</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">Payment Status</label>
                  <select
                    value={selectedPaymentStatus}
                    onChange={(e) => setSelectedPaymentStatus(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="PAID">Paid</option>
                    <option value="PARTIAL">Partial</option>
                    <option value="UNPAID">Unpaid</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Search Input Bar */}
            <div className="relative pt-2">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-5" />
              <input
                type="text"
                placeholder="Search by Consumer A/C No., Meter Sl. No., Bill Number, Section, Division, or Location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          {/* 2. Column Selector & Presets Toolbar */}
          <div className="p-5 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Columns className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Grilled Column Selector ({selectedColumns.length} of {ALL_BILL_COLUMNS.length} Active)
                </span>
              </div>

              {/* Column Control Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={selectAllColumns}
                  className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 text-[11px] font-bold transition"
                >
                  Select All Columns
                </button>
                <button
                  onClick={deselectAllColumns}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700 text-[11px] transition"
                >
                  Clear Non-Core
                </button>
                <button
                  onClick={() => setShowColumnPicker(!showColumnPicker)}
                  className="px-3 py-1 rounded-lg bg-sky-500/20 text-sky-300 border border-sky-500/40 text-[11px] font-bold transition"
                >
                  {showColumnPicker ? 'Hide Column Grid ▲' : 'Show Column Grid ▼'}
                </button>
              </div>
            </div>

            {/* Quick Presets Bar */}
            <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800 text-xs">
              <span className="text-[11px] text-slate-500 font-semibold mr-1">Presets:</span>
              <button
                onClick={() => setSelectedColumns(PRESETS.reconciliation)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              >
                Reconciliation Core (11)
              </button>
              <button
                onClick={() => setSelectedColumns(PRESETS.financial)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              >
                Financial & Slabs (13)
              </button>
              <button
                onClick={() => setSelectedColumns(PRESETS.meter)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              >
                Meters & Demands (11)
              </button>
              <button
                onClick={() => setSelectedColumns(PRESETS.audit)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700 transition"
              >
                Audit & Jurisdiction (10)
              </button>
            </div>

            {/* Collapsible Column Checkboxes Grid */}
            {showColumnPicker && (
              <div className="pt-3 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5 max-h-64 overflow-y-auto pr-1">
                {ALL_BILL_COLUMNS.map((col) => {
                  const checked = selectedColumns.includes(col.key);
                  return (
                    <button
                      key={col.key}
                      onClick={() => toggleColumn(col.key)}
                      className={`flex items-center gap-2 p-2 rounded-xl text-left border text-xs transition ${
                        checked
                          ? 'bg-slate-800 border-sky-500/50 text-slate-100 font-medium'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {checked ? (
                        <CheckSquare className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                      ) : (
                        <Square className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                      )}
                      <span className="truncate">{col.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* 3. Executive KPI Summary Bar */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow">
              <span className="text-[10px] uppercase font-bold text-slate-400">Filtered Rows</span>
              <div className="text-xl font-bold font-mono text-slate-100 mt-1">
                {summaryMetrics.count.toLocaleString()}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow">
              <span className="text-[10px] uppercase font-bold text-sky-400">Total Energy</span>
              <div className="text-xl font-bold font-mono text-sky-300 mt-1">
                {summaryMetrics.totalUnits.toLocaleString(undefined, { maximumFractionDigits: 0 })}{' '}
                <span className="text-xs font-normal text-slate-400">kWh</span>
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow">
              <span className="text-[10px] uppercase font-bold text-amber-400">Total Billed</span>
              <div className="text-xl font-bold font-mono text-amber-300 mt-1">
                ₹ {summaryMetrics.totalPayable.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow">
              <span className="text-[10px] uppercase font-bold text-emerald-400">Amount Paid</span>
              <div className="text-xl font-bold font-mono text-emerald-300 mt-1">
                ₹ {summaryMetrics.totalPaid.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow">
              <span className="text-[10px] uppercase font-bold text-rose-400">Outstanding Balance</span>
              <div className="text-xl font-bold font-mono text-rose-300 mt-1">
                ₹ {summaryMetrics.totalBal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow">
              <span className="text-[10px] uppercase font-bold text-purple-400">Realization Rate</span>
              <div className="text-xl font-bold font-mono text-purple-300 mt-1">
                {summaryMetrics.realization.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* 4. Grilled Data Table */}
          <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-100">
                  Custom Sliced View Table ({filteredData.length} records × {selectedColumns.length} columns)
                </h3>
                <p className="text-xs text-slate-400">
                  Spreadsheet grid view styled with border lines, right-aligned monetary figures, and active audit markers.
                </p>
              </div>

              {/* Instant Export Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleExport('xlsx')}
                  disabled={exporting || filteredData.length === 0}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download Excel (.xlsx)
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  disabled={exporting || filteredData.length === 0}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="w-3.5 h-3.5 text-sky-400" />
                  Download CSV (.csv)
                </button>
              </div>
            </div>

            {/* Table Container */}
            <div className="border border-slate-800 rounded-2xl overflow-hidden">
              <div className="overflow-x-auto max-h-[550px]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-950/90 text-slate-300 uppercase tracking-wider text-[11px] font-bold sticky top-0 z-10 border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-3 border-r border-slate-800 w-12 text-center text-slate-500">
                        #
                      </th>
                      {selectedColumns.map((colKey) => (
                        <th
                          key={colKey}
                          className="py-3 px-3 border-r border-slate-800 last:border-r-0 whitespace-nowrap"
                        >
                          {columnLabelMap[colKey] || colKey}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 bg-slate-900/40">
                    {filteredData.map((row, idx) => (
                      <tr
                        key={row.bill_number || row.bill_id || idx}
                        className="hover:bg-slate-800/50 transition-colors"
                      >
                        <td className="py-2.5 px-3 border-r border-slate-800/80 text-center font-mono text-slate-500 text-[11px]">
                          {idx + 1}
                        </td>
                        {selectedColumns.map((colKey) => {
                          const val = row[colKey];
                          const isNumeric =
                            typeof val === 'number' ||
                            (typeof val === 'string' &&
                              !isNaN(Number(val)) &&
                              val.trim() !== '' &&
                              !colKey.includes('no') &&
                              !colKey.includes('id') &&
                              !colKey.includes('month') &&
                              !colKey.includes('date'));

                          // Badges for specific status / classifications
                          if (colKey === 'payment_status') {
                            const st = String(val || 'UNPAID').toUpperCase();
                            const cls =
                              st === 'PAID'
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                : st === 'PARTIAL'
                                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                : 'bg-rose-500/10 text-rose-400 border-rose-500/20';
                            return (
                              <td
                                key={colKey}
                                className="py-2.5 px-3 border-r border-slate-800/80 last:border-r-0 whitespace-nowrap"
                              >
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${cls}`}>
                                  {st}
                                </span>
                              </td>
                            );
                          }

                          if (colKey === 'bill_type') {
                            const bt = String(val || 'LT').toUpperCase();
                            return (
                              <td
                                key={colKey}
                                className="py-2.5 px-3 border-r border-slate-800/80 last:border-r-0 whitespace-nowrap"
                              >
                                <span
                                  className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                                    bt === 'HT'
                                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                                      : 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                                  }`}
                                >
                                  {bt}
                                </span>
                              </td>
                            );
                          }

                          if (colKey === 'consumer_scope') {
                            const sc = String(val || 'HIGHWAY').toUpperCase();
                            return (
                              <td
                                key={colKey}
                                className="py-2.5 px-3 border-r border-slate-800/80 last:border-r-0 whitespace-nowrap"
                              >
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                    sc === 'PLAZA'
                                      ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                                  }`}
                                >
                                  {sc}
                                </span>
                              </td>
                            );
                          }

                          return (
                            <td
                              key={colKey}
                              className={`py-2.5 px-3 border-r border-slate-800/80 last:border-r-0 whitespace-nowrap font-mono text-slate-300 ${
                                isNumeric ? 'text-right' : 'text-left'
                              }`}
                            >
                              {val === null || val === undefined || val === ''
                                ? '—'
                                : isNumeric
                                ? typeof val === 'number'
                                  ? val.toLocaleString(undefined, {
                                      minimumFractionDigits: val % 1 !== 0 ? 2 : 0,
                                      maximumFractionDigits: 4,
                                    })
                                  : Number(val).toLocaleString(undefined, {
                                      minimumFractionDigits: Number(val) % 1 !== 0 ? 2 : 0,
                                      maximumFractionDigits: 4,
                                    })
                                : String(val)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}

                    {filteredData.length === 0 && (
                      <tr>
                        <td
                          colSpan={selectedColumns.length + 1}
                          className="py-12 text-center text-slate-500 text-xs"
                        >
                          <div className="flex flex-col items-center justify-center gap-2">
                            <AlertCircle className="w-6 h-6 text-slate-600" />
                            <span>No bill records found matching your selected filters.</span>
                            <button
                              onClick={() => {
                                setSelectedMonths(distinctMonths);
                                setSelectedPlazas(distinctPlazas);
                                setSelectedFYears(distinctFYears);
                                setSelectedFeeder('ALL');
                                setSelectedScope('ALL');
                                setSelectedPaymentStatus('ALL');
                                setSearchQuery('');
                              }}
                              className="text-sky-400 hover:underline text-xs mt-1"
                            >
                              Reset filters to view all records
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* TAB 2: Pre-configured Packs (REP-01 to REP-04) */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reports.map((rep) => (
              <div
                key={rep.id}
                className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-emerald-400 font-mono">{rep.id}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                      {rep.category}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-100 mt-2">{rep.name}</h3>
                  <p className="text-xs text-slate-400 mt-1">Available formats: {rep.format}</p>
                  <div className="text-xs text-slate-500 mt-2 font-mono">
                    {rep.rows} authoritative database rows
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-5 pt-4 border-t border-slate-800">
                  <button
                    onClick={() => {
                      if (rep.rows === 0) {
                        alert(`Cannot export ${rep.name}: No records are present in the Supabase database.`);
                        return;
                      }
                      const url = rep.id === 'REP-02' ? api.downloadConsumersExcelUrl : api.downloadBillsExcelUrl;
                      window.open(url, '_blank');
                    }}
                    disabled={rep.rows === 0}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl font-bold text-xs transition ${
                      rep.rows > 0
                        ? 'bg-emerald-600 hover:bg-emerald-500 text-slate-950 cursor-pointer'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50 opacity-60'
                    }`}
                    title={rep.rows === 0 ? 'Cannot export: No records in database' : 'Export Excel (.xlsx)'}
                  >
                    <Download className="w-3.5 h-3.5" />
                    Excel (.xlsx)
                  </button>
                  <button
                    onClick={() => {
                      if (rep.rows === 0) {
                        alert(`Cannot export ${rep.name}: No records are present in the Supabase database.`);
                        return;
                      }
                      window.open(api.downloadBillsCsvUrl, '_blank');
                    }}
                    disabled={rep.rows === 0}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl font-medium text-xs transition ${
                      rep.rows > 0
                        ? 'bg-slate-700 hover:bg-slate-600 text-slate-200 cursor-pointer'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50 opacity-60'
                    }`}
                    title={rep.rows === 0 ? 'Cannot export: No records in database' : 'Export CSV (.csv)'}
                  >
                    <Download className="w-3.5 h-3.5 text-sky-400" />
                    CSV (.csv)
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-300 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <span>
              All reports are generated dynamically from live Supabase views, ensuring zero formula drift and complete audit compliance.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
