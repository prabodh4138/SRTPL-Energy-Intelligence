const normalizeApiUrl = (raw: string): string => {
  const clean = raw.trim().replace(/\/+$/, '').replace(/\/api$/, '');
  return `${clean}/api`;
};

export const getApiBase = (): string => {
  if (typeof window !== 'undefined') {
    const override = localStorage.getItem('SRTPL_API_URL');
    if (override && override.trim()) {
      return normalizeApiUrl(override);
    }
  }
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.trim()) {
    return normalizeApiUrl(envUrl);
  }
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return 'https://srtpl-energy-backend.onrender.com/api';
  }
  return 'http://localhost:8000/api';
};

export const api = {
  getApiBase,
  setApiBase: (url: string) => {
    if (typeof window !== 'undefined') {
      if (!url) {
        localStorage.removeItem('SRTPL_API_URL');
      } else {
        localStorage.setItem('SRTPL_API_URL', url);
      }
    }
  },

  // Health check with fast 4s timeout & non-blocking AbortController
  checkHealth: async (timeoutMs = 4000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(`${getApiBase()}/health`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
      });
      clearTimeout(timeoutId);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return await res.json();
    } catch (e: any) {
      clearTimeout(timeoutId);
      if (e.name === 'AbortError') {
        return {
          status: 'WAKING UP...',
          database: 'Standby',
          error: 'Backend is waking up or spinning up on Render. Retrying shortly...',
        };
      }
      return { status: 'OFFLINE', database: 'Unreachable', error: String(e) };
    }
  },

  // Dashboard
  getDashboard: async (plaza = 'ALL', month = 'ALL', type = 'ALL') => {
    const params = new URLSearchParams({ toll_plaza: plaza, bill_month: month, bill_type: type });
    const res = await fetch(`${getApiBase()}/dashboard/summary?${params}`);
    return await res.json();
  },

  // Readings
  getReadings: async (assetType: string) => {
    const res = await fetch(`${getApiBase()}/readings/${assetType}`);
    return await res.json();
  },
  addReading: async (assetType: string, payload: { meter_code: string; plaza: string; reading_value: number; notes?: string }) => {
    const res = await fetch(`${getApiBase()}/readings/${assetType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  // Validation
  getValidation: async () => {
    const res = await fetch(`${getApiBase()}/validation/summary`);
    return await res.json();
  },

  // Juno Import
  getJunoBatches: async () => {
    const res = await fetch(`${getApiBase()}/juno/batches`);
    return await res.json();
  },
  uploadJunoFile: (
    file: File,
    equipment: string = 'AUTO',
    onProgress?: (percent: number, loaded: number, total: number) => void
  ): Promise<any> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${getApiBase()}/juno/upload?equipment=${encodeURIComponent(equipment)}`);

      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent, event.loaded, event.total);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error('Invalid JSON response'));
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || err.message || `Upload failed (HTTP ${xhr.status})`));
          } catch {
            reject(new Error(`Upload failed (HTTP ${xhr.status})`));
          }
        }
      };

      xhr.onerror = () => reject(new Error('Network error during file upload'));
      xhr.send(formData);
    });
  },
  uploadJunoFilesMulti: (
    files: File[],
    equipment: string = 'AUTO',
    onProgress?: (percent: number, loaded: number, total: number) => void
  ): Promise<{
    status: 'SUCCESS' | 'PARTIAL' | 'DUPLICATES_ONLY' | 'ERROR';
    total_files: number;
    successful: number;
    duplicates: number;
    failed: number;
    total_valid_rows: number;
    message: string;
    file_results: Array<{
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
    }>;
  }> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      for (const f of files) {
        formData.append('files', f);
      }
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${getApiBase()}/juno/upload-multi?equipment=${encodeURIComponent(equipment)}`);

      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent, event.loaded, event.total);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error('Invalid JSON response'));
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || err.message || `Upload failed (HTTP ${xhr.status})`));
          } catch {
            reject(new Error(`Upload failed (HTTP ${xhr.status})`));
          }
        }
      };

      xhr.onerror = () => reject(new Error('Network error during multi-file upload'));
      xhr.send(formData);
    });
  },

  // Bills Reconciliation Stream (Real-time per-bill extraction progress)
  uploadBillsStream: async (
    files: File[],
    onItemProgress: (current: number, total: number, file: string, candidate: any) => void
  ): Promise<{
    processed: number;
    verified: number;
    review: number;
    duplicates_rejected: number;
    failed: number;
    candidates: any[];
  }> => {
    const formData = new FormData();
    for (const f of files) {
      formData.append('files', f);
    }

    const response = await fetch(`${getApiBase()}/bills/upload-stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let msg = `Upload failed with status ${response.status}`;
      try {
        const err = await response.json();
        msg = err.detail || msg;
      } catch {}
      throw new Error(msg);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Streaming response not available.');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let finalSummary: any = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const ev = JSON.parse(line);
          if (ev.type === 'item_progress') {
            onItemProgress(ev.current, ev.total, ev.file, ev.candidate);
          } else if (ev.type === 'complete') {
            finalSummary = ev;
          }
        } catch {
          // Ignore partial chunk parsing
        }
      }
    }

    return (
      finalSummary || {
        processed: 0,
        verified: 0,
        review: 0,
        duplicates_rejected: 0,
        failed: 0,
        candidates: [],
      }
    );
  },

  // Bills Reconciliation
  uploadBills: (
    files: File[],
    onProgress?: (percent: number, loaded: number, total: number) => void
  ): Promise<{
    processed: number;
    verified: number;
    review: number;
    duplicates_rejected: number;
    failed: number;
    candidates: any[];
  }> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      for (const f of files) {
        formData.append('files', f);
      }
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${getApiBase()}/bills/upload`);

      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent, event.loaded, event.total);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error('Invalid JSON response from server'));
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || `Upload failed with HTTP ${xhr.status}`));
          } catch {
            reject(new Error(`Upload failed with HTTP ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => reject(new Error('Network error during bill upload'));
      xhr.send(formData);
    });
  },
  getOfficialRegister: async (plaza = 'ALL', month = 'ALL', type = 'ALL') => {
    const params = new URLSearchParams({ toll_plaza: plaza, bill_month: month, bill_type: type });
    const res = await fetch(`${getApiBase()}/bills/register?${params}`);
    return await res.json();
  },
  getReviewQueue: async () => {
    const res = await fetch(`${getApiBase()}/bills/review-queue`);
    return await res.json();
  },
  postReviewCandidate: async (candidateId: string, corrections = {}) => {
    const res = await fetch(`${getApiBase()}/bills/review-queue/${candidateId}/verify-and-post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrections }),
    });
    return await res.json();
  },
  deleteReviewCandidate: async (candidateId: string) => {
    const res = await fetch(`${getApiBase()}/bills/review-queue/${candidateId}/delete`, {
      method: 'POST',
    });
    return await res.json();
  },
  voidBill: async (billNumber: string, reason = 'Voided by operator') => {
    const res = await fetch(`${getApiBase()}/bills/register/${encodeURIComponent(billNumber)}/void?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    });
    return await res.json();
  },
  getReceipts: async () => {
    const res = await fetch(`${getApiBase()}/bills/receipts`);
    return await res.json();
  },
  allocateReceipt: async (payload: { receipt_no: string; bill_number: string; allocation_amount: number; notes?: string }) => {
    const res = await fetch(`${getApiBase()}/bills/receipts/allocate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  // Consumers
  getConsumers: async (plaza = 'ALL', type = 'ALL') => {
    const params = new URLSearchParams({ plaza, bill_type: type });
    const res = await fetch(`${getApiBase()}/consumers/?${params}`);
    return await res.json();
  },

  // Reports
  getReportsSummary: async () => {
    const res = await fetch(`${getApiBase()}/reports/summary`);
    return await res.json();
  },
  exportCustomReport: async (payload: {
    format: 'xlsx' | 'csv';
    title: string;
    columns: string[];
    labels: Record<string, string>;
    rows: any[];
  }) => {
    const res = await fetch(`${getApiBase()}/reports/custom-export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to export custom report');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SRTPL_${payload.title.replace(/\s+/g, '_')}.${payload.format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
  get downloadBillsExcelUrl() {
    return `${getApiBase()}/reports/download-bills-excel`;
  },
  get downloadBillsCsvUrl() {
    return `${getApiBase()}/reports/download-bills-csv`;
  },
  get downloadConsumersExcelUrl() {
    return `${getApiBase()}/reports/download-consumers-excel`;
  },
  get downloadReceiptsExcelUrl() {
    return `${getApiBase()}/reports/download-receipts-excel`;
  },
  get downloadReceiptsCsvUrl() {
    return `${getApiBase()}/reports/download-receipts-csv`;
  },
  get downloadMergedReconciliationExcelUrl() {
    return `${getApiBase()}/reports/download-merged-reconciliation-excel`;
  },
  get downloadMergedReconciliationCsvUrl() {
    return `${getApiBase()}/reports/download-merged-reconciliation-csv`;
  },
  getMergedReconciliation: async (): Promise<{ records: any[] }> => {
    const res = await fetch(`${getApiBase()}/reports/merged-reconciliation`);
    if (!res.ok) throw new Error('Failed to fetch merged reconciliation');
    return res.json();
  },
  get downloadMonthWiseExcelUrl() {
    return `${getApiBase()}/reports/download-month-wise-excel`;
  },
  get downloadMonthWiseCsvUrl() {
    return `${getApiBase()}/reports/download-month-wise-csv`;
  },
  getMonthWiseClearance: async (): Promise<{ summary: any[] }> => {
    const res = await fetch(`${getApiBase()}/reports/month-wise-clearance`);
    if (!res.ok) throw new Error('Failed to fetch month-wise clearance');
    return res.json();
  },
  getUnbilledConsumers: async (month: string): Promise<{ unbilled: any[] }> => {
    const res = await fetch(`${getApiBase()}/reports/unbilled-consumers/${encodeURIComponent(month)}`);
    if (!res.ok) throw new Error('Failed to fetch unbilled consumers');
    return res.json();
  },

  // --- SRTPL Energy Command Center APIs ---
  getEnergyOverview: async (plazaId = 'ALL', period = 'reviewed_baseline') => {
    const params = new URLSearchParams({ plaza_id: plazaId, period });
    const res = await fetch(`${getApiBase()}/energy/overview?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  getEnergyAssets: async (plazaId?: string, sourceType?: string, search?: string) => {
    const params = new URLSearchParams();
    if (plazaId && plazaId !== 'ALL') params.append('plaza_id', plazaId);
    if (sourceType && sourceType !== 'ALL') params.append('source_type', sourceType);
    if (search) params.append('search', search);
    const res = await fetch(`${getApiBase()}/energy/assets?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  createEnergyAsset: async (payload: {
    asset_code: string;
    asset_name: string;
    plaza_id: string;
    source_type: string;
    capacity_val: number;
    capacity_unit?: string;
    approval_reason: string;
    actor?: string;
  }) => {
    const res = await fetch(`${getApiBase()}/energy/assets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Asset creation failed');
    }
    return await res.json();
  },

  updateEnergyAsset: async (assetId: string, payload: {
    asset_name?: string;
    capacity_val?: number;
    is_active?: boolean;
    reason: string;
    actor?: string;
  }) => {
    const res = await fetch(`${getApiBase()}/energy/assets/${encodeURIComponent(assetId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Asset update failed');
    }
    return await res.json();
  },

  deactivateEnergyAsset: async (assetId: string, reason: string, actor = 'admin@srtpl.com') => {
    const formData = new FormData();
    formData.append('reason', reason);
    formData.append('actor', actor);
    const res = await fetch(`${getApiBase()}/energy/assets/${encodeURIComponent(assetId)}/deactivate`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Deactivation failed');
    }
    return await res.json();
  },

  getEnergyReadings: async (module = 'eb', plazaId = 'ALL', status = 'ALL') => {
    const params = new URLSearchParams({ module, plaza_id: plazaId, status });
    const res = await fetch(`${getApiBase()}/energy/readings?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  correctEnergyReading: async (payload: {
    reading_id: string;
    module: string;
    asset_code: string;
    plaza_id: string;
    field_name: string;
    original_value: number;
    proposed_value: number;
    reason: string;
    actor?: string;
  }) => {
    const res = await fetch(`${getApiBase()}/energy/readings/correct`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Correction failed');
    }
    return await res.json();
  },

  addEnergyReading: async (payload: {
    module: string;
    asset_code: string;
    plaza_id: string;
    reading_datetime: string;
    cumulative_value: number;
    interval_value?: number;
    power_factor?: number;
    notes?: string;
    actor?: string;
  }) => {
    const res = await fetch(`${getApiBase()}/energy/readings/entry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Reading submission failed');
    }
    return await res.json();
  },

  previewEnergyImport: async (file: File, module = 'eb') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('module', module);
    const res = await fetch(`${getApiBase()}/energy/import/preview`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Import preview failed');
    }
    return await res.json();
  },

  approveEnergyImport: async (payload: {
    filename: string;
    module: string;
    total_rows: number;
    valid_rows: any[];
    sha256: string;
    approval_reason?: string;
    actor?: string;
  }) => {
    const res = await fetch(`${getApiBase()}/energy/import/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Import approval failed');
    }
    return await res.json();
  },

  getEnergyExceptions: async (severity = 'ALL', status = 'ALL', plazaId = 'ALL', module = 'ALL') => {
    const params = new URLSearchParams({ severity, status, plaza_id: plazaId, module });
    const res = await fetch(`${getApiBase()}/energy/exceptions?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  reviewEnergyException: async (exceptionId: string, payload: {
    action: string;
    reason: string;
    proposed_correction?: number;
    actor?: string;
  }) => {
    const res = await fetch(`${getApiBase()}/energy/exceptions/${encodeURIComponent(exceptionId)}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Exception review failed');
    }
    return await res.json();
  },

  get downloadEnergyExcelUrl() {
    return `${getApiBase()}/energy/exports/excel`;
  },
  get downloadEnergyPdfUrl() {
    return `${getApiBase()}/energy/exports/pdf`;
  },
  get downloadEnergyBackupUrl() {
    return `${getApiBase()}/energy/backup/export`;
  },

  restoreEnergyBackup: async (payload: { confirm: boolean; reason: string; actor?: string; backup_json: string }) => {
    const res = await fetch(`${getApiBase()}/energy/backup/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Restore failed');
    }
    return await res.json();
  },

  getEnergyAuditLog: async (limit = 100) => {
    const res = await fetch(`${getApiBase()}/energy/audit-log?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },
};
