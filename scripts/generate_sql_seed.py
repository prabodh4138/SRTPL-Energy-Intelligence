import sys
import glob
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "active_app"))

from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.verifier import verify_bill_calculations
from bill_extractor.extractor_receipt_full import extract_energy_receipt_data

sql_lines = []
sql_lines.append("-- ============================================================================")
sql_lines.append("-- SRTPL PROJECT — COMPLETE DIRECT DATA SEED SCRIPT FOR SUPABASE")
sql_lines.append("-- Run this directly in Supabase SQL Editor to instantly inject all data!")
sql_lines.append("-- ============================================================================\n")

# 1. Bills
bill_files = [
    f for f in sorted(glob.glob(str(ROOT / "source_data" / "user_uploaded_bills" / "extractor" / "*.pdf")))
    if "HDFC" not in os.path.basename(f)
]
print(f"Generating SQL for {len(bill_files)} bills...")
sql_lines.append("-- 1. SEED 13 ENERGY BILLS")
for bf in bill_files:
    fname = os.path.basename(bf)
    raw = extract_energy_bill_full(bf, fname)
    v = verify_bill_calculations(raw)

    def _f(val):
        try:
            return float(str(val).replace(",", "").strip())
        except Exception:
            return 0.0

    def _s(val):
        s = str(val or "").replace("'", "''").strip()
        return f"'{s}'"

    sql = f"""INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    {_s(fname)}, {_s(raw.get('Consumer A/c No.', ''))}, {_s(raw.get('Consumer ID', ''))}, {_s(raw.get('Old Consumer No.', ''))}, {_s(raw.get('Bill Number', ''))},
    {_s(raw.get('Bill Month', ''))}, {_s(raw.get('Bill Period', ''))}, {_s(raw.get('Bill Days/Months', ''))}, {_s(raw.get('Meter Sl. No.', ''))}, {_s(raw.get('Meter Rent Count', ''))},
    {_f(raw.get('Security Deposit', 0))}, {_s(raw.get('Tariff Category', ''))}, {_s(raw.get('Division', ''))}, {_s(raw.get('Sub-Division', ''))}, {_s(raw.get('Section', ''))},
    {_f(raw.get('Slab Normal - KWH', 0))}, {_f(raw.get('Slab Peak - KWH', 0))}, {_f(raw.get('Slab Solar - KWH', 0))}, {_f(raw.get('Energy Charges', 0))}, {_f(raw.get('DPS(Rs.)', 0))},
    {_f(raw.get('Current Total', 0))}, {_f(raw.get('Total Amount Payable', 0))}, {v.get('cal_energy_charges', 0.0)}, {v.get('diff_energy_charges', 0.0)},
    {v.get('cal_electricity_charges', 0.0)}, {v.get('diff_electricity_charges', 0.0)}, {v.get('cal_current_total', 0.0)},
    {v.get('diff_current_total', 0.0)}, {_s(v.get('audit_status', 'VERIFIED_MATCH'))}
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;"""
    sql_lines.append(sql)

# 2. Receipts
receipt_files = sorted(glob.glob(str(ROOT / "source_data" / "user_uploaded_bills" / "extractor" / "*HDFC*.pdf")))
print(f"Generating SQL for {len(receipt_files)} receipts...")
sql_lines.append("\n-- 2. SEED 4 PAYMENT RECEIPTS")
for rf in receipt_files:
    fname = os.path.basename(rf)
    rdata = extract_energy_receipt_data(rf, fname)

    def _f(val):
        try:
            return float(str(val).replace(",", "").strip())
        except Exception:
            return 0.0

    def _s(val):
        s = str(val or "").replace("'", "''").strip()
        return f"'{s}'"

    sql = f"""INSERT INTO public.payment_receipts (
    receipt_no, consumer_no, account_no, consumer_name, collections_date,
    amount_paid, payment_type, transaction_id, bill_month, category, source_pdf
) VALUES (
    {_s(rdata.get('Receipt No', fname))}, {_s(rdata.get('Consumer No', ''))}, {_s(rdata.get('Account NO', ''))}, {_s(rdata.get('Consumer Name', ''))}, {_s(rdata.get('Collections Date', ''))},
    {_f(rdata.get('Amount Paid', 0))}, {_s(rdata.get('Payment Type', ''))}, {_s(rdata.get('Transaction ID', ''))}, {_s(rdata.get('Bill Month', ''))}, {_s(rdata.get('Category', ''))}, {_s(fname)}
) ON CONFLICT (receipt_no) DO NOTHING;"""
    sql_lines.append(sql)

# 3. Telemetry samples
sql_lines.append("""
-- 3. SEED TELEMETRY INTERVAL READINGS
INSERT INTO energy_readings.eb (asset_id, reading_datetime, cumulative_kwh, cumulative_kvah, cumulative_kvarh, interval_kwh, interval_kvah, interval_kvarh, pf, data_quality_status) VALUES
('AST-EB-01', NOW() - INTERVAL '1 day', 452100.5, 475890.0, 14520.0, 125.4, 132.0, 4.0, 0.95, 'VALID'),
('AST-EB-01', NOW() - INTERVAL '12 hours', 452225.9, 476022.0, 14524.0, 125.4, 132.0, 4.0, 0.95, 'VALID'),
('AST-EB-02', NOW() - INTERVAL '1 day', 389400.0, 410000.0, 12000.0, 110.2, 116.0, 3.5, 0.95, 'VALID'),
('AST-EB-03', NOW() - INTERVAL '1 day', 512000.0, 538000.0, 16000.0, 142.8, 150.0, 5.0, 0.95, 'VALID')
ON CONFLICT DO NOTHING;

INSERT INTO energy_readings.dg (asset_id, reading_datetime, cumulative_kwh, cumulative_running_hours, interval_kwh, interval_running_hours, pf, data_quality_status) VALUES
('AST-DG-01', NOW() - INTERVAL '1 day', 15420.0, 312.5, 45.0, 1.5, 0.92, 'VALID'),
('AST-DG-03', NOW() - INTERVAL '1 day', 18900.0, 405.0, 60.0, 2.0, 0.91, 'VALID'),
('AST-DG-05', NOW() - INTERVAL '1 day', 12300.0, 250.0, 30.0, 1.0, 0.90, 'VALID')
ON CONFLICT DO NOTHING;

INSERT INTO energy_readings.solar (asset_id, reading_datetime, cumulative_kwh, interval_kwh, data_quality_status) VALUES
('AST-SOL-01', NOW() - INTERVAL '1 day', 89200.0, 320.5, 'VALID'),
('AST-SOL-02', NOW() - INTERVAL '1 day', 76400.0, 280.0, 'VALID'),
('AST-SOL-03', NOW() - INTERVAL '1 day', 94100.0, 345.0, 'VALID')
ON CONFLICT DO NOTHING;

INSERT INTO energy_validation.exception_record (asset_id, rule_code, severity, status, reading_datetime, detected_value, message) VALUES
('AST-DG-01', 'VAL-DG-001', 'WARNING', 'OPEN', NOW() - INTERVAL '2 days', -12.4, 'Cumulative kWh decreased between consecutive intervals'),
('AST-EB-01', 'VAL-EB-003', 'INFO', 'ACKNOWLEDGED', NOW() - INTERVAL '3 days', 0.88, 'Power factor dipped below target 0.90 threshold'),
('AST-TRF-02', 'VAL-TRF-PV-IMB', 'WARNING', 'OPEN', NOW() - INTERVAL '1 day', 1.82, 'Primary voltage phase imbalance exceeded 1.5% warning threshold')
ON CONFLICT DO NOTHING;

DO $$
BEGIN
    RAISE NOTICE 'SUCCESS: 13 Bills, 4 Receipts, Telemetry Readings, and Exceptions successfully seeded into Supabase!';
END $$;
""")

output_path = ROOT / "sql" / "seed_all_data_into_supabase.sql"
with open(output_path, "w", encoding="utf-8") as fp:
    fp.write("\n".join(sql_lines))

print(f"SUCCESS: Generated {output_path} with {len(sql_lines)} SQL statements.")
