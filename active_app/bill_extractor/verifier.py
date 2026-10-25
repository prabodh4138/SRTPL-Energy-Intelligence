import re
from bill_extractor.ai_model_router import classify_bill_format, compute_derived_sbm_slabs


def _parse_num(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(",", "").strip()
    if not s or s == "-":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def verify_bill_calculations(bill_data: dict, raw_text: str = "") -> dict:
    """
    Performs comprehensive mathematical audit and reconciliation of an Energy Bill.
    Supports dynamic tariff categories:
      - GPS (General Purpose < 110 kVA): Tiered slabs (Slab 1 <= 100 @ 5.90, Slab 2 >100-300 @ 7.00, Slab 3 >300 @ 7.60)
      - Public Lighting / Commercial: Flat (6.20) or TOD (Normal 6.20, Peak 6.82, Solar 5.58)
      - HT General Purpose (>= 110 kVA): TOD (Normal 5.85, Peak 6.44, Solar 5.27)

    Reconciles:
      1. Cal Energy Charges = Sum(Slab_i Units * Rate_i) == a. Energy Charges
      2. Cal Electricity Charges = Cal Energy Charges + Demand Charge/MMFC + TOD Incentive + TOD Surchg == i. Electricity Charge
      3. Cal Current Total = Cal Electricity Charges + Duty + Meter Rent + Cust Service - EBill Rebate == o. Current Total / 3. Total Current Bill
      4. Cal Net After Rebate = Cal Current Total - Prompt Payment Rebate == Net Current payment after Rebate
    """
    text = raw_text or bill_data.get("raw_text") or ""
    cat = (bill_data.get("Tariff Category") or "").upper()

    # ---------- 1. DYNAMIC SLAB EXTRACTION & MULTI-CATEGORY FORMULA ----------
    # Match all slabs printed on bill (handles integer and decimal load-factor units):
    slab_matches = re.findall(
        r"Slab\s+([A-Za-z0-9\s]+?)\s*[-:]?\s*(?:KWH|KVAH)\s*([\d\.]+)@\s*([\d\.]+)\s*([\d,\.]+)",
        text
    )

    slab_details = []
    cal_energy_charges = 0.0
    formula_parts = []
    has_gps = False
    has_tod = False

    if slab_matches:
        for s_name, s_units, s_rate, s_amt in slab_matches:
            c_name = s_name.strip()
            u = _parse_num(s_units)
            r = _parse_num(s_rate)
            subtotal = round(u * r, 2)
            cal_energy_charges += subtotal
            slab_details.append({
                "name": c_name,
                "units": u,
                "rate": r,
                "amount": subtotal,
                "billed_amount": _parse_num(s_amt),
            })
            formula_parts.append(f"{c_name} ({u:,.2f}×₹{r:.2f}=₹{subtotal:,.2f})")
            if c_name in ["2", "3"]:
                has_gps = True
            elif c_name in ["Peak", "Solar"]:
                has_tod = True
        cal_energy_charges = round(cal_energy_charges, 2)
    else:
        # Check if bill is LT SBM / GPS with total billed units in meter row
        tot_units = _parse_num(bill_data.get("Total Billed Units"))
        if tot_units == 0.0:
            m_meter = re.search(r"(?:KWH|KVAH)\s+[\d,\.]+\s+[\d,\.]+\s+([\d,\.]+)\s+[\d,\.]+\s+([\d,\.]+)", text)
            if m_meter:
                tot_units = _parse_num(m_meter.group(2))

        if tot_units > 0 and ("< 110" in cat or "GPS" in cat or "SBM" in text.upper()):
            derived_slabs, cal_energy_charges = compute_derived_sbm_slabs(tot_units)
            slab_details = derived_slabs
            for ds in derived_slabs:
                formula_parts.append(f"Slab {ds['name']} ({ds['units']:,.0f}×₹{ds['rate']:.2f}=₹{ds['amount']:,.2f})")
            has_gps = True
        else:
            # Fallback to key-value fields if text regex finds no direct table line
            norm_u = _parse_num(bill_data.get("Slab Normal - KWH") or bill_data.get("Slab 1 - KWH"))
            norm_r = 5.85 if "110 KVA" in cat else 6.20
            peak_u = _parse_num(bill_data.get("Slab Peak - KWH"))
            peak_r = 6.44 if "110 KVA" in cat else 6.82
            sol_u = _parse_num(bill_data.get("Slab Solar - KWH"))
            sol_r = 5.27 if "110 KVA" in cat else 5.58

            amt1 = round(norm_u * norm_r, 2)
            amt2 = round(peak_u * peak_r, 2)
            amt3 = round(sol_u * sol_r, 2)
            cal_energy_charges = round(amt1 + amt2 + amt3, 2)
            if peak_u > 0:
                formula_parts = [f"Normal ({norm_u:,.0f}×₹{norm_r:.2f})", f"Peak ({peak_u:,.0f}×₹{peak_r:.2f})", f"Solar ({sol_u:,.0f}×₹{sol_r:.2f})"]
            else:
                formula_parts = [f"Slab 1 ({norm_u:,.0f}×₹{norm_r:.2f})"]

    # Determine Tariff Classification & Applicable Official Schedule
    if ">70" in cat or ">70 KVA" in cat:
        tariff_type = "HT General Purpose >70 to <110 kVA (Time-of-Day HT Tariff)"
        tariff_rules = "Normal (16-18, 00-08): ₹5.85/kVAh | Peak (18-00): ₹6.44/kVAh (+10%) | Solar (08-16): ₹5.27/kVAh (-10%) | Demand Charge: ₹250/kVA"
    elif ">= 110 KVA" in cat or "HT" in cat or ("110 KVA" in cat and "<" not in cat):
        tariff_type = "HT General Purpose ≥ 110 kVA (Time-of-Day HT Tariff)"
        tariff_rules = "Normal (16-18, 00-08): ₹5.85/kVAh | Peak (18-00): ₹6.44/kVAh (+10%) | Solar (08-16): ₹5.27/kVAh (-10%) | Demand Charge: ₹250/kVA"
    elif has_gps or "< 110 KVA" in cat or "GPS" in cat:
        tariff_type = "GPS (General Purpose < 110 kVA — Tiered Consumption Slabs)"
        tariff_rules = "Slab 1 (≤100 units): ₹5.90/kWh | Slab 2 (>100, ≤300 units): ₹7.00/kWh | Slab 3 (>300 units): ₹7.60/kWh | MMFC: ₹30/kW"
    elif has_tod:
        tariff_type = "Public Lighting / Commercial (Time-of-Day LT Tariff)"
        tariff_rules = "Normal (16-18, 00-08): ₹6.20/kWh | Peak (18-00): ₹6.82/kWh (+10%) | Solar (08-16): ₹5.58/kWh (-10%)"
    else:
        tariff_type = "Public Lighting / Commercial (Single Flat Slab Tariff)"
        tariff_rules = "Flat Energy Charge: ₹6.20/kWh | MMFC on First kW: ₹20, Addl: ₹15"

    ext_energy_charges = _parse_num(bill_data.get("a. Energy Charges"))
    diff_energy_charges = round(cal_energy_charges - ext_energy_charges, 2)
    match_energy_charges = abs(diff_energy_charges) <= 0.05

    # ---------- 2. ELECTRICITY CHARGES RECONCILIATION ----------
    demand_charge = _parse_num(bill_data.get("Demand Charge / MMFC"))
    tod_inc = 0.0
    tod_sur = 0.0
    tod_raw = bill_data.get("Incentive on TOD / TOD Surchg") or ""
    if "/" in tod_raw:
        parts = tod_raw.split("/")
        tod_inc = _parse_num(parts[0])
        tod_sur = _parse_num(parts[1])
    else:
        m_tod = re.search(
            r"Incentive on TOD\s*/\s*TOD Surchg\s*[:\s]*([-+]?[\d,]+\.?\d*)\s*/\s*([-+]?[\d,]+\.?\d*)",
            text
        )
        if m_tod:
            tod_inc = _parse_num(m_tod.group(1))
            tod_sur = _parse_num(m_tod.group(2))

    ext_elec_charge = _parse_num(bill_data.get("Electricity Charge (i)"))
    cal_elec_charges = round(cal_energy_charges + tod_inc + tod_sur + demand_charge, 2)
    diff_elec_charges = round(cal_elec_charges - ext_elec_charge, 2)
    match_elec_charges = abs(diff_elec_charges) <= 0.05

    # ---------- 3. TOTAL CURRENT BILL RECONCILIATION ----------
    elec_duty = _parse_num(bill_data.get("Electricity Duty (j)"))
    if elec_duty == 0.0:
        m_j = re.search(r"j\.\s*Electricity Duty\s*(?:\(\d+%\))?\s*[^\d]*([\d,]+\.?\d*)", text)
        if m_j:
            elec_duty = _parse_num(m_j.group(1))

    meter_rent = _parse_num(bill_data.get("Meter Rent (k)"))
    cust_service = _parse_num(bill_data.get("Customer Service Charge (l)"))

    ebill_rebate = 0.0
    m_eb = re.search(
        r"LF Rebate/\s*Spl Discount\s*/\s*EBill Rebate\s*.*?([-+]?[\d,]+\.?\d*)\s*/\s*([-+]?[\d,]+\.?\d*)\s*/\s*([-+]?[\d,]+\.?\d*)",
        text
    )
    if m_eb:
        ebill_rebate = _parse_num(m_eb.group(3))

    ext_curr_total = _parse_num(bill_data.get("Current Total (o)"))
    if ext_curr_total == 0.0:
        m_tot = re.search(r"(?:3\.\s*Total Current Bill|o\.\s*Current Total).*?[^\d]*([\d,]+\.?\d*)", text)
        if m_tot:
            ext_curr_total = _parse_num(m_tot.group(1))

    cal_curr_total = round(cal_elec_charges + elec_duty + meter_rent + cust_service - ebill_rebate, 2)
    diff_curr_total = round(cal_curr_total - ext_curr_total, 2)
    match_curr_total = abs(diff_curr_total) <= 0.05

    # ---------- 4. NET PAYABLE AFTER PROMPT REBATE ----------
    prompt_rebate = abs(_parse_num(bill_data.get("Rebate Allowable")))
    if prompt_rebate == 0.0:
        m_pr = re.search(r"Prompt Payment\+Rural\+Special Rebate\s*([-\d,\.]+)", text)
        if m_pr:
            prompt_rebate = abs(_parse_num(m_pr.group(1)))

    cal_net_after_rebate = round(cal_curr_total - prompt_rebate, 2)
    ext_net_before_rbt = _parse_num(bill_data.get("Net Payable Amount Before Rbt. Dt.(Rs.)"))

    all_matched = match_energy_charges and match_elec_charges and match_curr_total
    audit_status = "VERIFIED ✓" if all_matched else "AUDIT REQUIRED ⚠️"

    ai_cls = classify_bill_format(text)

    return {
        "tariff_category": cat,
        "tariff_type": tariff_type,
        "tariff_rules": tariff_rules,
        "slab_details": slab_details,
        "cal_energy_charges": cal_energy_charges,
        "ext_energy_charges": ext_energy_charges,
        "diff_energy_charges": diff_energy_charges,
        "match_energy_charges": match_energy_charges,
        "tod_incentive": tod_inc,
        "tod_surcharge": tod_sur,
        "demand_charge": demand_charge,
        "cal_electricity_charges": cal_elec_charges,
        "ext_electricity_charges": ext_elec_charge,
        "diff_electricity_charges": diff_elec_charges,
        "match_electricity_charges": match_elec_charges,
        "electricity_duty": elec_duty,
        "meter_rent": meter_rent,
        "customer_service_charge": cust_service,
        "ebill_rebate": ebill_rebate,
        "cal_current_total": cal_curr_total,
        "ext_current_total": ext_curr_total,
        "diff_current_total": diff_curr_total,
        "match_current_total": match_curr_total,
        "prompt_rebate": prompt_rebate,
        "cal_net_after_rebate": cal_net_after_rebate,
        "ext_net_before_rebate": ext_net_before_rbt,
        "audit_status": audit_status,
        "formula_energy_charges": " + ".join(formula_parts) if formula_parts else f"₹{cal_energy_charges:,.2f}",
        "formula_electricity_charges": f"₹{cal_energy_charges:,.2f} + ₹{demand_charge:,.2f} (MMFC) + ₹{tod_inc:,.2f} (TOD Inc) + ₹{tod_sur:,.2f} (TOD Sur)",
        "formula_current_total": f"₹{cal_elec_charges:,.2f} + ₹{elec_duty:,.2f} (ED) + ₹{meter_rent:,.2f} (Rent) + ₹{cust_service:,.2f} (Service) - ₹{ebill_rebate:,.2f} (EBill)",
        "ai_model_name": ai_cls["model_name"],
        "ai_model_id": ai_cls["model_id"],
        "ai_model_confidence": ai_cls["confidence_pct"],
        "ai_model_reasoning": ai_cls["reasoning"],
    }
