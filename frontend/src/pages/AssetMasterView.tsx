import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Layers,
  Search,
  Filter,
  Plus,
  Edit2,
  Trash2,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Sun,
  Flame,
  Zap,
  Cpu,
  BatteryCharging,
  X,
  RefreshCw,
} from 'lucide-react';

export const AssetMasterView: React.FC = () => {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [plazaFilter, setPlazaFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [solarTotalKwp, setSolarTotalKwp] = useState(121.38);

  // Modals
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deactModalOpen, setDeactModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any | null>(null);

  // Add Form State
  const [addCode, setAddCode] = useState('');
  const [addName, setAddName] = useState('');
  const [addPlaza, setAddPlaza] = useState('TP01');
  const [addType, setAddType] = useState('SOLAR');
  const [addCap, setAddCap] = useState<number | ''>(40.46);
  const [addReason, setAddReason] = useState('');

  // Edit Form State
  const [editName, setEditName] = useState('');
  const [editCap, setEditCap] = useState<number | ''>('');
  const [editReason, setEditReason] = useState('');

  // Deactivate Form State
  const [deactReason, setDeactReason] = useState('');

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchAssets = async () => {
    setLoading(true);
    setNotification(null);
    try {
      const res = await api.getEnergyAssets(plazaFilter, typeFilter, search);
      setAssets(res.assets || []);
      if (res.solar_capacity_total_kwp) {
        setSolarTotalKwp(res.solar_capacity_total_kwp);
      }
    } catch (err) {
      console.error(err);
      setNotification({ type: 'error', text: 'Failed to load master assets' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [plazaFilter, typeFilter]);

  // Open Edit Modal
  const handleOpenEdit = (a: any) => {
    setSelectedAsset(a);
    setEditName(a.asset_name);
    setEditCap(a.capacity);
    setEditReason('');
    setEditModalOpen(true);
  };

  // Open Deactivate Modal
  const handleOpenDeactivate = (a: any) => {
    setSelectedAsset(a);
    setDeactReason('');
    setDeactModalOpen(true);
  };

  // Submit Add Asset
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addCode.trim() || !addName.trim() || addCap === '' || !addReason.trim()) {
      alert('Please fill in all mandatory fields.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.createEnergyAsset({
        asset_code: addCode.trim(),
        asset_name: addName.trim(),
        plaza_id: addPlaza,
        source_type: addType,
        capacity_val: Number(addCap),
        capacity_unit: addType === 'SOLAR' ? 'kWp' : 'kVA',
        approval_reason: addReason.trim(),
        actor: 'admin@srtpl.com',
      });
      setNotification({ type: 'success', text: res.message || 'Asset created with audit log' });
      setAddModalOpen(false);
      fetchAssets();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Failed to create asset' });
    } finally {
      setSubmitting(false);
    }
  };

  // Submit Edit Asset
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsset || !editReason.trim()) {
      alert('Mandatory audit reason is required.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.updateEnergyAsset(selectedAsset.asset_id, {
        asset_name: editName.trim(),
        capacity_val: editCap === '' ? undefined : Number(editCap),
        reason: editReason.trim(),
        actor: 'admin@srtpl.com',
      });
      setNotification({ type: 'success', text: res.message || 'Asset updated' });
      setEditModalOpen(false);
      fetchAssets();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Update failed' });
    } finally {
      setSubmitting(false);
    }
  };

  // Submit Soft Deactivate
  const handleDeactivateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsset || !deactReason.trim()) {
      alert('Mandatory justification reason is required.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.deactivateEnergyAsset(selectedAsset.asset_id, deactReason.trim(), 'admin@srtpl.com');
      setNotification({ type: 'success', text: res.message || 'Asset deactivated' });
      setDeactModalOpen(false);
      fetchAssets();
    } catch (err: any) {
      setNotification({ type: 'error', text: err.message || 'Deactivation failed' });
    } finally {
      setSubmitting(false);
    }
  };

  const filteredAssets = assets.filter((a) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return (
      a.asset_code.toLowerCase().includes(s) ||
      a.asset_name.toLowerCase().includes(s) ||
      a.asset_id.toLowerCase().includes(s)
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-400" />
              <span>Asset Master Inventory & Capacities</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Search assets, inspect verified capacities (Solar 40.46 kWp each = 121.38 kWp total), controlled add/edit/deactivate after approval.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setAddCode('');
                setAddName('');
                setAddReason('');
                setAddModalOpen(true);
              }}
              className="py-2 px-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition flex items-center gap-1.5 shadow-md shadow-emerald-950/40"
            >
              <Plus className="w-4 h-4" />
              <span>Controlled Add Asset</span>
            </button>
          </div>
        </div>

        {/* Solar Rule Highlight Callout */}
        <div className="mt-4 p-3.5 rounded-xl bg-sky-950/20 border border-sky-500/30 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-sky-300">
            <Sun className="w-4 h-4 text-sky-400 shrink-0" />
            <span>
              <strong>Solar Capacity Rule:</strong> Three Solar assets, each <strong>40.46 kWp</strong> (Total: <strong>{solarTotalKwp} kWp</strong>). Always use capacity_kwp, not kVA.
            </span>
          </div>
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-bold hidden sm:inline">
            Verified Specification
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

      {/* Filters & Search Toolbar */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[240px] max-w-md bg-slate-950/60 border border-slate-800 rounded-xl px-3 py-2">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by asset code, name, ID..."
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

          {/* Type Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <span className="text-slate-400 font-medium">Equipment Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-transparent text-slate-200 outline-none font-semibold cursor-pointer"
            >
              <option value="ALL" className="bg-slate-800">ALL Types</option>
              <option value="EB" className="bg-slate-800">EB Grid Supply</option>
              <option value="DG" className="bg-slate-800">Diesel Generator</option>
              <option value="SOLAR" className="bg-slate-800">Solar Plants</option>
              <option value="TRANSFORMER" className="bg-slate-800">Transformer</option>
              <option value="UPS" className="bg-slate-800">UPS Units</option>
            </select>
          </div>
        </div>
      </div>

      {/* Asset Table */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Master Asset Inventory ({filteredAssets.length} verified units)
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            Plaza IDs: TP01 / TP02 / TP03
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-400 mb-2" />
            Loading asset master inventory...
          </div>
        ) : filteredAssets.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No assets match the current filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 font-medium border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Asset ID</th>
                  <th className="py-3 px-4">Asset Code</th>
                  <th className="py-3 px-4">Asset Name</th>
                  <th className="py-3 px-4">Plaza</th>
                  <th className="py-3 px-4">Equipment Type</th>
                  <th className="py-3 px-4 text-right">Capacity</th>
                  <th className="py-3 px-4 text-right">Total Readings</th>
                  <th className="py-3 px-4 text-center">Date Range (Start → Last)</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredAssets.map((a) => {
                  const isSolar = a.source_type === 'SOLAR';
                  const dateRangeStr =
                    a.start_date && a.last_date
                      ? `${String(a.start_date).substring(0, 10)} → ${String(a.last_date).substring(0, 10)}`
                      : a.start_date
                      ? `${String(a.start_date).substring(0, 10)} → Ongoing`
                      : '—';

                  return (
                    <tr key={a.asset_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono font-medium text-slate-400">{a.asset_id}</td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">{a.asset_code}</td>
                      <td className="py-3 px-4 font-medium text-slate-200">{a.asset_name}</td>
                      <td className="py-3 px-4 font-mono">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]">
                          {a.plaza_id}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 font-mono text-[10px] font-semibold">
                          {a.source_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold">
                        {isSolar ? (
                          <span className="text-sky-400">40.46 kWp</span>
                        ) : (
                          <span className="text-slate-300">{a.capacity} {a.capacity_unit}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-100">
                        {a.total_readings ? `${Number(a.total_readings).toLocaleString()} rows` : '0 rows'}
                      </td>
                      <td className="py-3 px-4 text-center font-mono text-[11px] text-slate-400">
                        {dateRangeStr}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            a.is_active
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {a.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenEdit(a)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                            title="Controlled Edit"
                          >
                            <Edit2 className="w-3.5 h-3.5 text-emerald-400" />
                          </button>
                          {a.is_active && (
                            <button
                              onClick={() => handleOpenDeactivate(a)}
                              className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 transition"
                              title="Controlled Soft Deactivate"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Controlled Add Asset Modal */}
      {addModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">Controlled Add Asset (After Approval)</h3>
              </div>
              <button onClick={() => setAddModalOpen(false)} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Asset Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SR-E-AP-SPX-000004"
                    value={addCode}
                    onChange={(e) => setAddCode(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Equipment Type *</label>
                  <select
                    value={addType}
                    onChange={(e) => {
                      setAddType(e.target.value);
                      if (e.target.value === 'SOLAR') setAddCap(40.46);
                    }}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none cursor-pointer"
                  >
                    <option value="SOLAR">Solar Generation (kWp)</option>
                    <option value="EB">EB Grid Supply</option>
                    <option value="DG">Diesel Generator</option>
                    <option value="TRANSFORMER">Transformer</option>
                    <option value="UPS">UPS System</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Asset Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Solar Plant Inverter 4"
                  value={addName}
                  onChange={(e) => setAddName(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Plaza ID *</label>
                  <select
                    value={addPlaza}
                    onChange={(e) => setAddPlaza(e.target.value)}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono cursor-pointer"
                  >
                    <option value="TP01">TP01</option>
                    <option value="TP02">TP02</option>
                    <option value="TP03">TP03</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">
                    Capacity ({addType === 'SOLAR' ? 'kWp' : 'kVA'}) *
                  </label>
                  <input
                    type="number"
                    step="any"
                    required
                    value={addCap}
                    onChange={(e) => setAddCap(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Approval & Justification Reason <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Enter supervisory approval reference and operational reason..."
                  value={addReason}
                  onChange={(e) => setAddReason(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 p-2.5 text-slate-200 outline-none text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
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
                  <span>Save Asset & Log Audit</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Controlled Edit Asset Modal */}
      {editModalOpen && selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">Controlled Edit: {selectedAsset.asset_code}</h3>
              </div>
              <button onClick={() => setEditModalOpen(false)} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Asset Name</label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  Capacity ({selectedAsset.source_type === 'SOLAR' ? 'kWp' : 'kVA'})
                </label>
                <input
                  type="number"
                  step="any"
                  value={editCap}
                  onChange={(e) => setEditCap(e.target.value === '' ? '' : parseFloat(e.target.value))}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 px-3 py-2 text-slate-200 outline-none font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Mandatory Modification Reason <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Enter reason for modifying master asset specification..."
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 p-2.5 text-slate-200 outline-none text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditModalOpen(false)}
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
                  <span>Confirm Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Controlled Soft Deactivation Modal */}
      {deactModalOpen && selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Trash2 className="w-5 h-5 text-rose-400" />
                <h3 className="text-base font-bold text-slate-100">Soft-Deactivate Asset</h3>
              </div>
              <button onClick={() => setDeactModalOpen(false)} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleDeactivateSubmit} className="space-y-4 text-xs">
              <p className="text-slate-300">
                You are soft-deactivating <strong>{selectedAsset.asset_code}</strong> ({selectedAsset.asset_name}).
                Source records are preserved; physical deletion is prevented.
              </p>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Mandatory Deactivation Reason <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Enter reason for deactivating this asset..."
                  value={deactReason}
                  onChange={(e) => setDeactReason(e.target.value)}
                  className="w-full rounded-xl bg-slate-950/60 border border-slate-700 p-2.5 text-slate-200 outline-none text-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setDeactModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5"
                >
                  {submitting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                  <span>Confirm Deactivation</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
