const API_BASE = 'http://localhost:8000/api';

export const api = {
  // Health
  checkHealth: async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await res.json();
    } catch (e) {
      return { status: 'OFFLINE', error: String(e) };
    }
  },

  // Dashboard
  getDashboard: async (plaza = 'ALL', month = 'ALL', type = 'ALL') => {
    const params = new URLSearchParams({ toll_plaza: plaza, bill_month: month, bill_type: type });
    const res = await fetch(`${API_BASE}/dashboard/summary?${params}`);
    return await res.json();
  },

  // Readings
  getReadings: async (assetType: string) => {
    const res = await fetch(`${API_BASE}/readings/${assetType}`);
    return await res.json();
  },
  addReading: async (assetType: string, payload: { meter_code: string; plaza: string; reading_value: number; notes?: string }) => {
    const res = await fetch(`${API_BASE}/readings/${assetType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  // Validation
  getValidation: async () => {
    const res = await fetch(`${API_BASE}/validation/summary`);
    return await res.json();
  },

  // Juno Import
  getJunoBatches: async () => {
    const res = await fetch(`${API_BASE}/juno/batches`);
    return await res.json();
  },
  uploadJunoFile: async (equipment: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/juno/upload?equipment=${encodeURIComponent(equipment)}`, {
      method: 'POST',
      body: formData,
    });
    return await res.json();
  },

  // Bills Reconciliation
  uploadBills: async (files: File[]) => {
    const formData = new FormData();
    for (const f of files) {
      formData.append('files', f);
    }
    const res = await fetch(`${API_BASE}/bills/upload`, {
      method: 'POST',
      body: formData,
    });
    return await res.json();
  },
  getOfficialRegister: async (plaza = 'ALL', month = 'ALL', type = 'ALL') => {
    const params = new URLSearchParams({ toll_plaza: plaza, bill_month: month, bill_type: type });
    const res = await fetch(`${API_BASE}/bills/register?${params}`);
    return await res.json();
  },
  getReviewQueue: async () => {
    const res = await fetch(`${API_BASE}/bills/review-queue`);
    return await res.json();
  },
  postReviewCandidate: async (candidateId: string, corrections = {}) => {
    const res = await fetch(`${API_BASE}/bills/review-queue/${candidateId}/verify-and-post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrections }),
    });
    return await res.json();
  },
  deleteReviewCandidate: async (candidateId: string) => {
    const res = await fetch(`${API_BASE}/bills/review-queue/${candidateId}/delete`, {
      method: 'POST',
    });
    return await res.json();
  },
  voidBill: async (billNumber: string, reason = 'Voided by operator') => {
    const res = await fetch(`${API_BASE}/bills/register/${encodeURIComponent(billNumber)}/void?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    });
    return await res.json();
  },
  getReceipts: async () => {
    const res = await fetch(`${API_BASE}/bills/receipts`);
    return await res.json();
  },
  allocateReceipt: async (payload: { receipt_no: string; bill_number: string; allocation_amount: number; notes?: string }) => {
    const res = await fetch(`${API_BASE}/bills/receipts/allocate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await res.json();
  },

  // Consumers
  getConsumers: async (plaza = 'ALL', type = 'ALL') => {
    const params = new URLSearchParams({ plaza, bill_type: type });
    const res = await fetch(`${API_BASE}/consumers/?${params}`);
    return await res.json();
  },

  // Reports
  getReportsSummary: async () => {
    const res = await fetch(`${API_BASE}/reports/summary`);
    return await res.json();
  },
  downloadBillsExcelUrl: `${API_BASE}/reports/download-bills-excel`,
  downloadBillsCsvUrl: `${API_BASE}/reports/download-bills-csv`,
  downloadConsumersExcelUrl: `${API_BASE}/reports/download-consumers-excel`,
};
