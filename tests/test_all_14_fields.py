import pdfplumber
import glob
import re
import os

def extract_clean_number(pattern, text_blob, group_num=1, flags=0):
    match = re.search(pattern, text_blob or "", flags=flags)
    if match:
        return match.group(group_num).replace(",", "").strip()
    return ""

def parse_bill_fields(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
        lines = text.splitlines()

    res = {}
    res['File'] = os.path.basename(pdf_path)

    # 1. Meter Rent Count
    res['Meter Rent Count'] = extract_clean_number(r"Meter Rent Count\s*:\s*([\d/]+)", text)

    # 2. Security Deposit
    res['Security Deposit'] = extract_clean_number(r"Security Deposit\s*:\s*([\d,]+\.?\d*)", text)

    # 3. Bill Period
    period = ""
    for idx, l in enumerate(lines):
        if "Bill Period" in l:
            m1 = re.search(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", l)
            if m1:
                period = f"{m1.group(1)} - {m1.group(2)}"
            else:
                m_start = re.search(r"(\d{2}/\d{2}/\d{4})\s*-", l)
                if m_start and idx + 1 < len(lines):
                    next_l = lines[idx + 1]
                    m_end = re.search(r"(\d{2}/\d{2}/\d{4})", next_l)
                    if m_end:
                        period = f"{m_start.group(1)} - {m_end.group(1)}"
            break
    res['Bill Period'] = period

    # 4. Bill Days/Months
    res['Bill Days/Months'] = extract_clean_number(r"Bill Days/Months\s*:\s*([\d/\.]+)", text)

    # 5. Meter Sl. No.
    res['Meter Sl. No.'] = extract_clean_number(r"Meter Sl\.\s*No\.?\s*:\s*([\w\-]+)", text)

    # 6. a. Energy Charges
    res['a. Energy Charges'] = extract_clean_number(r"a\.\s*Energy Charges\s*[^\d]*([\d,]+\.?\d*)", text)

    # 7. Slab Normal - KWH (or KVAH for HT bills, or Slab 1 for GPS)
    slab_norm = extract_clean_number(r"Slab Normal\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", text)
    if not slab_norm:
        slab_norm = extract_clean_number(r"Slab\s*1\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", text)
    res['Slab Normal - KWH'] = slab_norm

    # 8. Slab Peak - KWH (or KVAH for HT bills, or Slab 2 for GPS)
    slab_peak = extract_clean_number(r"Slab Peak\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", text)
    if not slab_peak:
        slab_peak = extract_clean_number(r"Slab\s*2\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", text)
    res['Slab Peak - KWH'] = slab_peak

    # 9. Slab Solar - KWH (or KVAH for HT bills, or Slab 3 for GPS)
    slab_solar = extract_clean_number(r"Slab Solar\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", text)
    if not slab_solar:
        slab_solar = extract_clean_number(r"Slab\s*3\s*[-:]?\s*(?:KWH|KVAH)\s*[^\d]*(\d+)", text)
    res['Slab Solar - KWH'] = slab_solar

    # 10. DPS(Rs.)
    dps = ""
    for idx, l in enumerate(lines):
        if "dps(rs.)" in l.lower():
            for j in range(idx + 1, min(idx + 4, len(lines))):
                nums = re.findall(r"[-+]?\d{1,3}(?:,\d{3})*\.\d{2}", lines[j])
                if len(nums) >= 3:
                    dps = nums[1].replace(",", "").strip()
                    break
            break
    res['DPS(Rs.)'] = dps

    # 11. Tariff Category
    cat = extract_clean_number(r"Tariff Category\s*:\s*([^:\n]+?)(?=\s+(?:Power Factor|Category Type|Billable Demand|Supply Voltage|\n|$))", text)
    if cat.endswith("<") or cat.endswith(">=") or cat.endswith(">"):
        m_next = re.search(re.escape(cat) + r".*?\n\s*(\d+\s*KVA)", text, re.DOTALL | re.IGNORECASE)
        if m_next:
            cat = f"{cat} {m_next.group(1).strip()}"
    res['Tariff Category'] = cat

    # 12. Division
    res['Division'] = extract_clean_number(r"Division\s*:\s*([^:\n]+?)(?=\s+(?:Tariff Category|Sub-Division|Section|\n|$))", text)

    # 13. Sub-Division
    res['Sub-Division'] = extract_clean_number(r"Sub-Division\s*:\s*([^:\n]+?)(?=\s+(?:Category Type|Section|Billable Demand|\n|$))", text)

    # 14. Section
    res['Section'] = extract_clean_number(r"Section\s*:\s*([^:\n]+?)(?=\s+(?:Contract Demand|Pole No|DT No|Meter Sl|\n|$))", text)

    return res


def test_all_14_fields_extracted_from_bills():
    pdfs = sorted(glob.glob('source_data/user_uploaded_bills/extractor/*EN.pdf'))
    assert len(pdfs) >= 11, f"Found {len(pdfs)} bill PDFs, expected at least 11"

    for p in pdfs:
        data = parse_bill_fields(p)
        assert data['Meter Rent Count'] != "", f"Missing Meter Rent Count in {data['File']}"
        assert data['Security Deposit'] != "", f"Missing Security Deposit in {data['File']}"
        assert data['Bill Period'] != "", f"Missing Bill Period in {data['File']}"
        assert data['Bill Days/Months'] != "", f"Missing Bill Days/Months in {data['File']}"
        assert data['Meter Sl. No.'] != "", f"Missing Meter Sl. No. in {data['File']}"
        assert data['a. Energy Charges'] != "", f"Missing a. Energy Charges in {data['File']}"
        assert data['Slab Normal - KWH'] != "", f"Missing Slab Normal in {data['File']}"
        assert data['DPS(Rs.)'] != "", f"Missing DPS(Rs.) in {data['File']}"
        assert data['Tariff Category'] != "", f"Missing Tariff Category in {data['File']}"
        assert data['Division'] != "", f"Missing Division in {data['File']}"
        assert data['Sub-Division'] != "", f"Missing Sub-Division in {data['File']}"
        assert data['Section'] != "", f"Missing Section in {data['File']}"
