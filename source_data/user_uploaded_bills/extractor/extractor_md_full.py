import pdfplumber
import re


def extract_md_bill_data(pdf_file, source_name):
    """
    pdf_file   : file-like object (BytesIO / uploaded file)
    source_name: original PDF filename

    Returns: dict with same columns as eb_bill_updated.py
    """

    entry = {}

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
    entry["Consumer ID"] = grab(r"Consumer ID\s*:\s*(\d+)")
    entry["Bill Number"] = grab(r"Bill Number\s*:\s*(\d+)")
    entry["Bill Month"] = grab(r"Bill Month\s*:\s*(\d{4}/\d{2})")

    # ---------- NET PAYABLE AMOUNT AFTER RBT DT ----------
    entry["Net Payable Amount After Rbt. Dt.(Rs.)"] = ""

    for i, line in enumerate(lines):
        if (
            re.search(r"Before\s*Rbt\.?\s*Dt", line, re.IGNORECASE)
            and re.search(r"After\s*Rbt\.?\s*Dt", line, re.IGNORECASE)
        ):
            numbers = []
            for j in range(i + 1, min(i + 4, len(lines))):
                numbers.extend(
                    re.findall(
                        r"\b\d{1,3}(?:,\d{3})*\.\d{2}\b",
                        lines[j]
                    )
                )
            if len(numbers) >= 2:
                entry["Net Payable Amount After Rbt. Dt.(Rs.)"] = numbers[1].replace(",", "")
            break

    # ---------- MD-KW (CURRENT READING) ----------
    entry["MD-KW"] = ""

    for line in lines:
        if re.search(r"\b(CUML\s*)?MD[-\s]*KW\b", line, re.IGNORECASE):
            nums = re.findall(r"\d+\.\d+", line)
            if len(nums) >= 2:
                entry["MD-KW"] = nums[1]
            break

    # ---------- MD-KVA (CURRENT READING) ----------
    entry["MD-KVA"] = ""

    for line in lines:
        if re.search(r"\b(CUML\s*)?MD[-\s]*KVA\b", line, re.IGNORECASE):
            nums = re.findall(r"\d+\.\d+", line)
            if len(nums) >= 2:
                entry["MD-KVA"] = nums[1]
            break

    # ---------- SOURCE ----------
    entry["Source PDF"] = source_name

    return entry
