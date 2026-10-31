import pdfplumber
import re


def extract_md_bill_data(pdf_file, source_name, extracted_text=None):
    """
    pdf_file   : file-like object (BytesIO / uploaded file)
    source_name: original PDF filename

    Returns: dict with same columns as eb_bill_updated.py
    """

    entry = {}

    if extracted_text is not None:
        text = extracted_text
    else:
        with pdfplumber.open(pdf_file) as pdf:
            page = pdf.pages[0]
            text = page.extract_text() or ""

    # Normalize lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ---------- BASIC DETAILS ----------
    def grab(pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""

    entry["Consumer A/c No."] = grab(r"Consumer A/c No\.\s*:\s*([\w\-]+)")
    entry["Consumer ID"] = grab(r"Consumer ID\s*:\s*([A-Za-z0-9]+)")
    entry["Bill Number"] = grab(r"Bill Number\s*:\s*([A-Za-z0-9]+)")
    entry["Bill Month"] = grab(r"Bill Month\s*:\s*(\d{4}/\d{2})")
    entry["Contract Demand"] = grab(r"Contract Demand\s*:\s*([^:\n]+?)(?=\s+(?:Meter Sl|DT No|Pole No|\n|$))")

    # ---------- NET PAYABLE AMOUNT AFTER & BEFORE RBT DT ----------
    entry["Net Payable Amount After Rbt. Dt.(Rs.)"] = ""
    entry["Net Payable Amount Before Rbt. Dt.(Rs.)"] = ""

    for i, line in enumerate(lines):
        if (
            re.search(r"Before\s*Rbt\.?\s*Dt", line, re.IGNORECASE)
            and re.search(r"After\s*Rbt\.?\s*Dt", line, re.IGNORECASE)
        ):
            for j in range(i + 1, min(i + 4, len(lines))):
                nums = re.findall(r"[-+]?\d[\d,]*\.\d{2}", lines[j])
                if len(nums) >= 2:
                    entry["Net Payable Amount Before Rbt. Dt.(Rs.)"] = nums[0].replace(",", "")
                    entry["Net Payable Amount After Rbt. Dt.(Rs.)"] = nums[1].replace(",", "")
                    break
            break

    # ---------- MD & CUML MD (KW & KVA) ----------
    cuml_md_kw = ""
    cuml_md_kva = ""
    md_kw = ""
    md_kva = ""
    for l in lines:
        if re.search(r"^\s*CUML\s+MD[-\s]*KW\b", l, re.IGNORECASE):
            nums = re.findall(r"[\d,]+\.\d+", l)
            cuml_md_kw = nums[1].replace(",", "") if len(nums) >= 2 else (nums[-1].replace(",", "") if nums else "")
        elif re.search(r"^\s*CUML\s+MD[-\s]*KVA\b", l, re.IGNORECASE):
            nums = re.findall(r"[\d,]+\.\d+", l)
            cuml_md_kva = nums[1].replace(",", "") if len(nums) >= 2 else (nums[-1].replace(",", "") if nums else "")
        elif re.search(r"^\s*MD[-\s]*KW\b", l, re.IGNORECASE) and not re.search(r"CUML|Normal", l, re.IGNORECASE):
            nums = re.findall(r"[\d,]+\.\d+", l)
            md_kw = nums[1].replace(",", "") if len(nums) >= 2 else (nums[-1].replace(",", "") if nums else "")
        elif re.search(r"^\s*MD[-\s]*KVA\b", l, re.IGNORECASE) and not re.search(r"CUML|Normal", l, re.IGNORECASE):
            nums = re.findall(r"[\d,]+\.\d+", l)
            md_kva = nums[1].replace(",", "") if len(nums) >= 2 else (nums[-1].replace(",", "") if nums else "")

    entry["CUML MD-KW"] = cuml_md_kw
    entry["CUML MD-KVA"] = cuml_md_kva
    entry["MD-KW"] = md_kw or cuml_md_kw
    entry["MD-KVA"] = md_kva or cuml_md_kva

    # Billable Demand fallback
    if not entry["MD-KW"]:
        m_bkw = re.search(r"Billable Demand-KW\s*:\s*([\d\.]+)", text)
        if m_bkw:
            entry["MD-KW"] = m_bkw.group(1).strip()
    if not entry["MD-KVA"]:
        m_bkva = re.search(r"Billable Demand-KVA\s*:\s*([\d\.]+)", text)
        if m_bkva:
            entry["MD-KVA"] = m_bkva.group(1).strip()

    is_ht = "HT" in text.upper() or "KVA" in (entry.get("Contract Demand") or "").upper()
    primary_md = entry["MD-KVA"] if is_ht else entry["MD-KW"]
    if not primary_md or primary_md in ("0.0000", "0"):
        primary_md = entry["MD-KW"] if is_ht else entry["MD-KVA"]
    if not primary_md or primary_md in ("0.0000", "0"):
        primary_md = cuml_md_kva if is_ht else cuml_md_kw
    entry["MD"] = primary_md

    # ---------- SOURCE ----------
    entry["Source PDF"] = source_name

    return entry
