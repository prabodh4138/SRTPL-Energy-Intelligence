import pdfplumber
import re


def extract_clean_number(pattern, text_blob, group_num=1, flags=0):
    match = re.search(pattern, text_blob or "", flags=flags)
    if match:
        return match.group(group_num).replace(",", "").strip()
    return ""


def extract_energy_bill_full(pdf_file, source_name):
    """
    Extracts FULL energy bill data across both old and new formats.
    Includes all 14 requested columns:
    - Meter Rent Count
    - Security Deposit
    - Bill Period
    - Bill Days/Months
    - Meter Sl. No.
    - a. Energy Charges
    - Slab Normal - KWH
    - Slab Peak - KWH
    - Slab Solar - KWH
    - DPS(Rs.)
    - Tariff Category
    - Division
    - Sub-Division
    - Section
    Plus existing bill header, net payable and meter details.
    """
    entry = {}

    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        text = page.extract_text() or ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ================= HEADER INFO =================
    entry["Rebate Date"] = extract_clean_number(r"Rebate Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    entry["Due Date"] = extract_clean_number(r"Due Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    entry["Consumer A/c No."] = extract_clean_number(r"Consumer A/c No\.\s*:\s*([\w\-]+)", text)
    entry["Consumer ID"] = extract_clean_number(r"Consumer ID\s*:\s*(\d+)", text)
    entry["Old Consumer No."] = extract_clean_number(r"Old Consumer No\.\s*:\s*([\w\-]*)", text)
    entry["Bill Number"] = extract_clean_number(r"Bill Number\s*:\s*(\d+)", text)
    entry["Bill Issue Date"] = extract_clean_number(r"Bill Issue Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    entry["Bill Basis"] = extract_clean_number(r"Bill Basis\s*:\s*([A-Z]+)", text)
    entry["Bill Month"] = extract_clean_number(r"Bill Month\s*:\s*(\d{4}/\d{2})", text)
    entry["Last Bill Issue Date"] = extract_clean_number(r"Last Bill Issue Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)

    # ================= AREA & JURISDICTION DETAILS =================
    entry["Division"] = extract_clean_number(
        r"Division\s*:\s*([^:\n]+?)(?=\s+(?:Tariff Category|Sub-Division|Section|\n|$))", text
    )
    entry["Sub-Division"] = extract_clean_number(
        r"Sub-Division\s*:\s*([^:\n]+?)(?=\s+(?:Category Type|Section|Billable Demand|\n|$))", text
    )
    entry["Section"] = extract_clean_number(
        r"Section\s*:\s*([^:\n]+?)(?=\s+(?:Contract Demand|Pole No|DT No|Meter Sl|\n|$))", text
    )

    raw_cat = extract_clean_number(
        r"Tariff Category\s*:\s*([^:\n]+?)(?=\s+(?:Power Factor|Category Type|Billable Demand|Supply Voltage|\n|$))", text
    )
    if raw_cat.endswith("<") or raw_cat.endswith(">=") or raw_cat.endswith(">"):
        m_next = re.search(re.escape(raw_cat) + r".*?\n\s*(\d+\s*KVA)", text, re.DOTALL | re.IGNORECASE)
        if m_next:
            raw_cat = f"{raw_cat} {m_next.group(1).strip()}"
    entry["Tariff Category"] = raw_cat

    # ================= SUPPLY & METER DETAILS =================
    entry["Meter Sl. No."] = extract_clean_number(r"Meter Sl\.\s*No\.?\s*:\s*([\w\-]+)", text)
    entry["Meter Rent Count"] = extract_clean_number(r"Meter Rent Count\s*:\s*([\d/]+)", text)
    entry["Security Deposit"] = extract_clean_number(r"Security Deposit\s*:\s*([\d,]+\.?\d*)", text)

    # Extract Bill Period (handles same line or wrapped date on next line)
    period = ""
    for idx, l in enumerate(lines):
        if "Bill Period" in l:
            m1 = re.search(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", l)
            if m1:
                period = f"{m1.group(1)} - {m1.group(2)}"
            else:
                m_start = re.search(r"(\d{2}/\d{2}/\d{4})\s*-", l)
                if m_start and idx + 1 < len(lines):
                    m_end = re.search(r"(\d{2}/\d{2}/\d{4})", lines[idx + 1])
                    if m_end:
                        period = f"{m_start.group(1)} - {m_end.group(1)}"
            break
    entry["Bill Period"] = period
    entry["Bill Days/Months"] = extract_clean_number(r"Bill Days/Months\s*:\s*([\d/\.]+)", text)

    # ================= TABLE AREA: SLABS & CHARGES =================
    table_text = text.split("Last Bill Issue Date")[-1] if "Last Bill Issue Date" in text else text

    # a. Energy Charges
    entry["a. Energy Charges"] = extract_clean_number(r"a\.\s*Energy Charges\s*[^\d]*([\d,]+\.?\d*)", table_text)

    # Dynamic Slab Extraction (handles GPS tiered slabs, TOD Normal/Peak/Solar, and Single Flat Slabs)
    slab_matches = re.findall(
        r"Slab\s+([A-Za-z0-9\s]+?)\s*[-:]?\s*(?:KWH|KVAH)\s*(\d+)@\s*([\d\.]+)\s*([\d,\.]+)",
        table_text
    )
    has_gps_tiers = False
    for s_name, s_units, s_rate, s_amt in slab_matches:
        c_name = s_name.strip()
        u_str = s_units.strip()
        r_str = s_rate.strip()
        a_str = s_amt.replace(",", "").strip()
        if c_name in ["1", "2", "3"]:
            entry[f"Slab {c_name} - KWH"] = u_str
            entry[f"Slab {c_name} Rate"] = r_str
            entry[f"Slab {c_name} Amount"] = a_str
            if c_name in ["2", "3"]:
                has_gps_tiers = True
        elif "Normal" in c_name:
            entry["Slab Normal - KWH"] = u_str
            entry["Slab Normal Rate"] = r_str
            entry["Slab Normal Amount"] = a_str
        elif "Peak" in c_name:
            entry["Slab Peak - KWH"] = u_str
            entry["Slab Peak Rate"] = r_str
            entry["Slab Peak Amount"] = a_str
        elif "Solar" in c_name:
            entry["Slab Solar - KWH"] = u_str
            entry["Slab Solar Rate"] = r_str
            entry["Slab Solar Amount"] = a_str

    if has_gps_tiers:
        entry["Tariff Type"] = "GPS (General Purpose < 110 kVA Tiered Slabs)"
        # Maintain backward compatibility with 14 target columns
        if not entry.get("Slab Normal - KWH") and entry.get("Slab 1 - KWH"):
            entry["Slab Normal - KWH"] = entry["Slab 1 - KWH"]
        if not entry.get("Slab Peak - KWH") and entry.get("Slab 2 - KWH"):
            entry["Slab Peak - KWH"] = entry["Slab 2 - KWH"]
        if not entry.get("Slab Solar - KWH") and entry.get("Slab 3 - KWH"):
            entry["Slab Solar - KWH"] = entry["Slab 3 - KWH"]
    elif "110 KVA" in entry.get("Tariff Category", ""):
        entry["Tariff Type"] = "HT General Purpose >= 110 kVA (TOD Tariff)"
    else:
        entry["Tariff Type"] = "Public Lighting / Commercial (TOD / Flat)"
        if not entry.get("Slab Normal - KWH") and entry.get("Slab 1 - KWH"):
            entry["Slab Normal - KWH"] = entry["Slab 1 - KWH"]

    # Fallback if regex missed normal slab
    if not entry.get("Slab Normal - KWH"):
        slab_normal = extract_clean_number(r"Slab Normal\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", table_text)
        if not slab_normal:
            slab_normal = extract_clean_number(r"Slab\s*1\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", table_text)
        entry["Slab Normal - KWH"] = slab_normal
    if not entry.get("Slab Peak - KWH"):
        entry["Slab Peak - KWH"] = extract_clean_number(r"Slab Peak\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", table_text)
    if not entry.get("Slab Solar - KWH"):
        entry["Slab Solar - KWH"] = extract_clean_number(r"Slab Solar\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", table_text)

    # DPS(Rs.) extraction from summary charges row
    dps_val = ""
    for idx, l in enumerate(lines):
        if "dps(rs.)" in l.lower():
            for j in range(idx + 1, min(idx + 4, len(lines))):
                nums = re.findall(r"[-+]?\d{1,3}(?:,\d{3})*\.\d{2}", lines[j])
                if len(nums) >= 3:
                    dps_val = nums[1].replace(",", "").strip()
                    break
            break
    entry["DPS(Rs.)"] = dps_val

    # TOD & other charges
    match_tod = re.search(
        r"Incentive on TOD\s*/\s*TOD Surchg\s*.*?([\d\.\-]+)\s*/\s*([\d\.\-]+)",
        table_text
    )
    entry["Incentive on TOD / TOD Surchg"] = (
        f"{match_tod.group(1)} / {match_tod.group(2)}" if match_tod else ""
    )

    entry["Demand Charge / MMFC"] = extract_clean_number(
        r"Demand Charge\s*/\s*MMFC\s*[^\d]*(\d[\d,\.]*)", table_text
    )
    entry["Electricity Charge (i)"] = extract_clean_number(
        r"i\.\s*Electricity Charge\s*[^\d]*(\d[\d,\.]*)", table_text
    )
    entry["Electricity Duty (j)"] = extract_clean_number(
        r"j\.\s*Electricity Duty\s*\(\d+%\)\s*[^\d]*(\d[\d,\.]*)", table_text
    )
    entry["Meter Rent (k)"] = extract_clean_number(
        r"k\.\s*Meter Rent\s*[^\d]*(\d[\d,\.]*)", table_text
    )
    entry["Customer Service Charge (l)"] = extract_clean_number(
        r"l\.\s*Customer Service Charge\s*[^\d]*(\d[\d,\.]*)", table_text
    )
    entry["Current Total (o)"] = extract_clean_number(
        r"o\.\s*Current Total.*?[^\d]*(\d[\d,\.]*)", table_text
    )

    # Net Payable Before Rebate Date
    entry["Net Payable Amount Before Rbt. Dt.(Rs.)"] = extract_clean_number(
        r"Net Payable Amount.*?Before.*?Rbt.*?Dt.*?Rs.*?[^\d]*(\d[\d,\.]*)",
        table_text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Rebate
    rebate_match = re.search(
        r"Prompt Payment\+Rural\+Special Rebate[^\d\-]*([-\d,\.]+)",
        text
    )
    entry["Rebate Allowable"] = (
        rebate_match.group(1).replace(",", "").strip() if rebate_match else ""
    )

    entry["raw_text"] = text
    entry["Source PDF"] = source_name
    return entry
