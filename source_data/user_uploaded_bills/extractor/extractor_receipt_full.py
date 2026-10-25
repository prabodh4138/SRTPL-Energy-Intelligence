import fitz  # PyMuPDF
import re


def extract_energy_receipt_data(pdf_file, source_name):
    """
    Extracts Energy Receipt data from ONE PDF.

    pdf_file   : file-like object (BytesIO / uploaded file)
    source_name: original PDF filename

    Returns: dict
    """

    receipt_data = {
        "Receipt No": source_name.replace(".pdf", ""),
        "Consumer No": "",
        "Amount Paid": "",
        "Collections Date": "",
        "Source PDF": source_name
    }

    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

        for page in doc:
            text = page.get_text()

            # ---------- Collections Date ----------
            match = re.search(r"\b(\d{2}-\d{2}-\d{4})\b", text)
            if match and not receipt_data["Collections Date"]:
                receipt_data["Collections Date"] = match.group(1).strip()

            # ---------- Consumer No ----------
            match = re.search(r"\b(\d{12})\s+Account\s*NO\b", text, re.IGNORECASE)
            if match and not receipt_data["Consumer No"]:
                receipt_data["Consumer No"] = match.group(1).strip()

            # ---------- Amount Paid ----------
            match = re.search(r"Amount\s+Paid\s+([\d,]+\.\d{2})", text, re.IGNORECASE)
            if match and not receipt_data["Amount Paid"]:
                receipt_data["Amount Paid"] = match.group(1).replace(",", "").strip()

    except Exception:
        # Fail silently – bad PDFs will be handled by caller
        pass

    return receipt_data
