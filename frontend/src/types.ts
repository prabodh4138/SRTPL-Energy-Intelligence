export interface DashboardKPIs {
  total_bills_found: number;
  held_for_review: number;
  verified_posted: number;
  duplicates_rejected: number;
  total_bill_amount: number;
  total_paid_amount: number;
  total_outstanding: number;
}

export interface PlazaSummary {
  plaza_id: string;
  bill_count: number;
  total_amount: number;
  total_kwh: number;
}

export interface TrendData {
  month: string;
  eb_units: number;
  dg_units: number;
  solar_units: number;
  billed_amount: number;
}

export interface CandidateResult {
  file: string;
  kind: string;
  consumer: string;
  month: string;
  detail: string;
  amount: number;
  result: 'VERIFIED' | 'REVIEW' | 'FAILED' | 'EXTRACTED' | 'DUPLICATE_REJECTED';
  payload: Record<string, any>;
  identifier?: string;
  is_receipt?: boolean;
}

export interface OfficialBill {
  bill_number: string;
  consumer_account_no: string;
  bill_month: string;
  toll_plaza_id?: string;
  bill_type?: string;
  bill_basis?: string;
  rebate_date?: string;
  prompt_rebate?: number;
  rebate_status?: string;
  rebate_availed?: number;
  rebate_loss?: number;
  rebate_remarks?: string;
  company_profit_rs?: number;
  company_loss_rs?: number;
  financial_impact?: string;
  total_amount_payable: number;
  amount_paid?: number;
  outstanding_balance?: number;
  verification_status?: string;
  created_at?: string;
  source_filename?: string;
}

export interface ReviewQueueItem {
  candidate_id: string;
  bill_number: string;
  consumer_account_no: string;
  bill_month: string;
  bill_basis: string;
  amount: number;
  exception_reason: string;
  hold_reason_code: string;
  status: string;
}

export interface ReceiptItem {
  receipt_no: string;
  consumer_no?: string;
  account_no: string;
  consumer_name?: string;
  payment_type?: string;
  payment_mode?: string;
  amount_paid: number;
  collections_date?: string;
  bill_month: string;
  category?: string;
  office_name?: string;
  transaction_id?: string;
  transaction_ref?: string;
  source_pdf?: string;
}

export interface MergedReconciliationItem {
  consumer_account_no: string;
  bill_month: string;
  bill_number?: string;
  toll_plaza_id?: string;
  bill_type?: string;
  consumer_scope?: string;
  meter_sl_no?: string;
  rebate_date?: string;
  prompt_rebate?: number;
  rebate_status?: string;
  rebate_availed?: number;
  rebate_loss?: number;
  rebate_remarks?: string;
  company_profit_rs?: number;
  company_loss_rs?: number;
  financial_impact?: string;
  total_amount_payable: number;
  net_payable_amount_before_rbt_dt_rs?: number;
  net_payable_amount_after_rbt_dt_rs?: number;
  meter_rent?: number;
  customer_service_charge?: number;
  receipt_no?: string;
  payment_type?: string;
  collections_date?: string;
  amount_paid: number;
  office_name?: string;
  category?: string;
  outstanding_balance: number;
  payment_status: 'PAID' | 'PARTIAL' | 'UNPAID';
}

export interface EquipmentReading {
  id: string;
  meter_code: string;
  plaza: string;
  date: string;
  prev_kwh?: number;
  curr_kwh?: number;
  diff_kwh?: number;
  pf?: number;
  status: string;
  [key: string]: any;
}
