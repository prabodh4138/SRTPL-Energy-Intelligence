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
    equipment: string,
    file: File,
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
  get downloadBillsExcelUrl() {
    return `${getApiBase()}/reports/download-bills-excel`;
  },
  get downloadBillsCsvUrl() {
    return `${getApiBase()}/reports/download-bills-csv`;
  },
  get downloadConsumersExcelUrl() {
    return `${getApiBase()}/reports/download-consumers-excel`;
  },
};
