-- ============================================================================
-- SRTPL PROJECT — COMPLETE DIRECT DATA SEED SCRIPT FOR SUPABASE
-- Run this directly in Supabase SQL Editor to instantly inject all data!
-- ============================================================================

-- 1. SEED 13 ENERGY BILLS
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '411001070208_82025_EN.pdf', '411001070208', '34110012497', 'STL-SBP-218', '411010709251615163',
    '2025/08', '02/08/2025 - 01/09/2025', '31/1.0000', '10029454', '34/60',
    36360.14, 'PUBLIC LIGHT', 'SED SAMBALPUR', 'SDO-I SAMBALPUR', 'ESO RE SECTION',
    2646.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 16405.2, 0.0,
    16560.2, 0.0, 17366.41,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '411001070208_92026_EN.pdf', '411001070208', '34110012497', 'STL-SBP-218', '411010710261293606',
    '2026/09', '02/09/2026 - 01/10/2026', '30/1.0000', '10029454', '47/60',
    36360.14, 'PUBLIC LIGHT', 'SED SAMBALPUR', 'SDO-I SAMBALPUR', 'ESO RE SECTION',
    2076.0, 0.0, 0.0, 0.0, 32.99,
    0.0, 0.0, 12871.2, 0.0,
    13026.2, 0.0, 13680.65,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '413001070102_92026_EN.pdf', '413001070102', '34130015224', '101-STL-SPD', '413010710261229528',
    '2026/09', '02/09/2026 - 01/10/2026', '30/1.0000', '10010726', '49/60',
    64391.05, 'PUBLIC LIGHT', 'JED JHARSUGUDA', 'SDO JHARSUGUDA-II', 'ESO SAHAPADA',
    1225.0, 1334.0, 25.0, 0.0, 54.17,
    0.0, 0.0, 16832.38, 0.0,
    17017.38, 0.0, 17840.68,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '413001070344_82025_EN.pdf', '413001070344', '142452232667', 'BTM', '413010709251688219',
    '2025/08', '02/08/2025 - 01/09/2025', '31/1.0000', 'TWSL12001179', '0/60',
    179770.0, 'PUBLIC LIGHT', 'JED JHARSUGUDA', 'SDO JHARSUGUDA-I', 'ESO JED-2',
    6093.0, 0.0, 0.0, 0.0, 0.01,
    0.0, 0.0, 37776.6, 0.0,
    39221.6, 0.0, 40769.86,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416000000110_92026_EN.pdf', '416000000110', '4160000110', 'LE-110', '416000010262972491',
    '2026/09', '01/09/2026 - 30/09/2026', '30/1.0000', 'TWN20045', '13/60',
    390096.0, 'GENERAL PURPOSE >= 110 KVA', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON',
    9899.0, 8124.0, 4630.0, 0.0, 0.0,
    0.0, 0.0, 134627.81, 0.0,
    158627.81, 0.0, 170637.23,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001070082_92026_EN.pdf', '416001070082', '34160003188', 'ST-SSN-0037', '416010710261304116',
    '2026/09', '02/09/2026 - 01/10/2026', '30/1.0000', '10025846', '46/60',
    85149.0, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON',
    1921.0, 2189.0, 19.0, 0.0, 28.04,
    0.0, 0.0, 26945.2, 0.0,
    27250.2, 0.0, 28478.01,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001070084_82025_EN.pdf', '416001070084', '34160003190', 'ST-RGL-0039', '416010709251608075',
    '2025/08', '02/08/2025 - 01/09/2025', '31/1.0000', '10040807', '31/60',
    65781.0, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI',
    3402.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 21092.4, 0.0,
    21865.0, 0.0, 22879.8,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001070086_82025_EN.pdf', '416001070086', '34160003218', 'ST-RGL-0041', '416010709251691494',
    '2025/08', '02/08/2025 - 01/09/2025', '31/1.0000', 'TWSC59033983', '12/60',
    70231.24, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI',
    5111.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 31688.2, 0.0,
    32292.9, 0.0, 33722.42,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001070090_82025_EN.pdf', '416001070090', '34160003251', 'ST-RGL-0045', '416010709251608419',
    '2025/08', '02/08/2025 - 01/09/2025', '31/1.0000', '10029687', '31/60',
    34610.78, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI',
    2399.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 14873.8, 0.0,
    15013.8, 0.0, 15758.75,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001070090_92026_EN.pdf', '416001070090', '34160003251', 'ST-RGL-0045', '416010710261304692',
    '2026/09', '02/09/2026 - 01/10/2026', '30/1.0000', '10029687', '44/60',
    34610.78, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI',
    1688.0, 0.0, 0.0, 0.0, 34.52,
    0.0, 0.0, 10465.6, 0.0,
    10590.6, 0.0, 11159.22,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001111004_42025_EN.pdf', '416001111004', '34160003985', 'COM-SSN-1245', '416011105251608613',
    '2025/04', '02/04/2025 - 01/05/2025', '30/1.0000', '10028787', '30/60',
    19165.0, 'GENERAL PURPOSE < 110 KVA', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON',
    100.0, 200.0, 706.0, 0.0, 0.0,
    0.0, 0.0, 7355.6, 0.0,
    7475.6, 0.0, 7919.82,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '416001111004_92026_EN.pdf', '416001111004', '34160003985', 'COM-SSN-1245', '416011110261308077',
    '2026/09', '02/09/2026 - 01/10/2026', '30/1.0000', '10028787', '47/60',
    19165.0, 'GENERAL PURPOSE < 110 KVA', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON',
    100.0, 200.0, 692.0, 0.0, 19.85,
    0.0, 0.0, 7249.2, 0.0,
    7369.2, 0.0, 7809.17,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;
INSERT INTO public.energy_bills (
    source_filename, consumer_account_no, consumer_id, old_consumer_no, bill_number,
    bill_month, bill_period, bill_days, meter_sl_no, meter_rent_count,
    security_deposit, tariff_category, division, sub_division, section,
    slab_normal_kwh, slab_peak_kwh, slab_solar_kwh, energy_charges, dps_rs,
    current_total, total_amount_payable, cal_energy_charges, diff_energy_charges,
    cal_electricity_charges, diff_electricity_charges, cal_current_total,
    diff_current_total, verification_status
) VALUES (
    '812001070018_92026_EN.pdf', '812001070018', '38120003515', 'STL-18-S', '812010710261330579',
    '2026/09', '02/09/2026 - 01/10/2026', '30/1.0000', '10006888', '48/60',
    92260.0, 'PUBLIC LIGHT', 'SED SUNDARAGADA', 'SDO SUNDARAGADA', 'ESO NO-I',
    2180.0, 2424.0, 4.0, 0.0, 70.17,
    0.0, 0.0, 30070.0, 0.0,
    30405.0, 0.0, 31757.8,
    0.0, 'VERIFIED ✓'
) ON CONFLICT (bill_number) DO UPDATE SET
    current_total = EXCLUDED.current_total,
    total_amount_payable = EXCLUDED.total_amount_payable;

-- 2. SEED 4 PAYMENT RECEIPTS
INSERT INTO public.payment_receipts (
    receipt_no, consumer_no, account_no, consumer_name, collections_date,
    amount_paid, payment_type, transaction_id, bill_month, category, source_pdf
) VALUES (
    '657221121225HDFC0003', '411001070208', '34110012497', 'M/S. L & T SAMBALPUR-ROURKELA', '12-12-2025',
    15497.0, 'NEFT', '-', 'November 2025', 'PUBLIC LIGHT', '657221121225HDFC0003.pdf'
) ON CONFLICT (receipt_no) DO NOTHING;
INSERT INTO public.payment_receipts (
    receipt_no, consumer_no, account_no, consumer_name, collections_date,
    amount_paid, payment_type, transaction_id, bill_month, category, source_pdf
) VALUES (
    '657221171225HDFC0004', '411001070209', '34110012498', 'M/S. L & T SBP-RKL TOLLWAY LIMITED', '17-12-2025',
    44429.0, 'NEFT', '-', 'November 2025', 'PUBLIC LIGHT', '657221171225HDFC0004.pdf'
) ON CONFLICT (receipt_no) DO NOTHING;
INSERT INTO public.payment_receipts (
    receipt_no, consumer_no, account_no, consumer_name, collections_date,
    amount_paid, payment_type, transaction_id, bill_month, category, source_pdf
) VALUES (
    '657245121225HDFC0005', '416001070085', '34160003191', 'M/S L & T SAMBALPUR-RKL TOLLWAYS L', '12-12-2025',
    10513.0, 'NEFT', '-', 'November 2025', 'PUBLIC LIGHT', '657245121225HDFC0005.pdf'
) ON CONFLICT (receipt_no) DO NOTHING;
INSERT INTO public.payment_receipts (
    receipt_no, consumer_no, account_no, consumer_name, collections_date,
    amount_paid, payment_type, transaction_id, bill_month, category, source_pdf
) VALUES (
    '657245121225HDFC0006', '416001070084', '34160003190', 'M/S L & T SAMBALPUR-RKL TOLLWAYS LT', '12-12-2025',
    28850.0, 'NEFT', '-', 'November 2025', 'PUBLIC LIGHT', '657245121225HDFC0006.pdf'
) ON CONFLICT (receipt_no) DO NOTHING;

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
