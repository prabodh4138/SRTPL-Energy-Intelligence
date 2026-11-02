import io
import os
import re

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def extract_energy_receipt_data(pdf_file, source_name: str, extracted_text: str = "") -> dict:
    """
    Extracts Energy Receipt data from ONE PDF file or BytesIO stream.

    pdf_file       : file path (str/Path) or file-like object (BytesIO / uploaded file)
    source_name    : original PDF filename
    extracted_text : optional pre-extracted text to avoid re-parsing PDF

    Returns: dict with dual Title Case & snake_case keys:
             Receipt No / receipt_no, Consumer No / consumer_no, Account NO / account_no,
             Amount Paid / amount_paid, Collections Date / collections_date,
             Consumer Name / consumer_name, Payment Type / payment_type,
             Transaction ID / transaction_id, Bill Month / bill_month,
             Category / category, Source PDF / source_pdf
    """
    receipt_data = {
        "Receipt No": "",
        "Consumer No": "",
        "Account NO": "",
        "Consumer Name": "",
        "Collections Date": "",
        "Amount Paid": "",
        "Payment Type": "",
        "Transaction ID": "",
        "Bill Month": "",
        "Category": "",
        "Source PDF": source_name,
    }

    try:
        pages_text: list[str] = []
        if extracted_text and extracted_text.strip():
            pages_text.append(extracted_text)
        elif HAS_FITZ:
            if isinstance(pdf_file, (str, os.PathLike)):
                doc = fitz.open(pdf_file)
            else:
                if hasattr(pdf_file, "seek"):
                    pdf_file.seek(0)
                stream_bytes = pdf_file.read() if hasattr(pdf_file, "read") else pdf_file
                doc = fitz.open(stream=stream_bytes, filetype="pdf")
            for page in doc:
                pages_text.append(page.get_text() or "")
        elif HAS_PDFPLUMBER:
            if isinstance(pdf_file, (str, os.PathLike)):
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text() or ""
                        pages_text.append(t)
            else:
                if hasattr(pdf_file, "seek"):
                    pdf_file.seek(0)
                file_obj = pdf_file if hasattr(pdf_file, "read") else io.BytesIO(pdf_file)
                with pdfplumber.open(file_obj) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text() or ""
                        pages_text.append(t)

        for text in pages_text:
            # ---------- Receipt No ----------
            match_rno = (
                re.search(r"Receipt\s*No[^\w\n]*[:\s\n]+([A-Za-z0-9]+)", text, re.IGNORECASE)
                or re.search(r"Receipt\s*Number[^\w\n]*[:\s\n]+([A-Za-z0-9]+)", text, re.IGNORECASE)
            )
            if match_rno and not receipt_data["Receipt No"]:
                receipt_data["Receipt No"] = match_rno.group(1).strip()

            # ---------- Collections Date ----------
            match_dt = re.search(r"Collections\s*Date[^\d\n]*[:\s\n]+(\d{2}-\d{2}-\d{4})", text, re.IGNORECASE) or re.search(r"\b(\d{2}-\d{2}-\d{4})\b", text)
            if match_dt and not receipt_data["Collections Date"]:
                receipt_data["Collections Date"] = match_dt.group(1).strip()

            # ---------- Account NO ----------
            match_acc = (
                re.search(r"Account\s*NO[^\d\n]*[:\s\n]+(\d+)", text, re.IGNORECASE)
                or re.search(r"\b(\d{11,12})\s+Account\s*NO\b", text, re.IGNORECASE)
            )
            if match_acc and not receipt_data["Account NO"]:
                receipt_data["Account NO"] = match_acc.group(1).strip()

            # ---------- Consumer No ----------
            match_cno = re.search(r"Consumer\s*No[^\d\n]*[:\s\n]+(\d+)", text, re.IGNORECASE)
            if match_cno and not receipt_data["Consumer No"]:
                receipt_data["Consumer No"] = match_cno.group(1).strip()

            # Fallback for Consumer No if not found
            if not receipt_data["Consumer No"]:
                match_cno_alt = re.search(r"\b(\d{11,12})\b", text)
                if match_cno_alt and match_cno_alt.group(1) != receipt_data.get("Account NO"):
                    receipt_data["Consumer No"] = match_cno_alt.group(1).strip()

            # ---------- Consumer Name ----------
            match_name = (
                re.search(r"Consumer\s*Name[^\w\n]*[:\s\n]+(M/S[^\n]+|[^\n]+)", text, re.IGNORECASE)
                or re.search(r"Account\s*NO\s*\n\s*(M/S[^\n]+)", text, re.IGNORECASE)
            )
            if match_name and not receipt_data["Consumer Name"]:
                receipt_data["Consumer Name"] = match_name.group(1).strip()

            # ---------- Amount Paid ----------
            match_amt = re.search(r"Amount\s+Paid[^\d\n]*[:\s\n]+([\d,]+\.\d{2})", text, re.IGNORECASE)
            if match_amt and not receipt_data["Amount Paid"]:
                receipt_data["Amount Paid"] = match_amt.group(1).replace(",", "").strip()

            # ---------- Payment Type ----------
            match_ptype = re.search(r"Payment\s*Type[^\w\n]*[:\s\n]+([A-Za-z0-9]+)", text, re.IGNORECASE)
            if match_ptype and not receipt_data["Payment Type"]:
                receipt_data["Payment Type"] = match_ptype.group(1).strip()

            # ---------- Transaction ID ----------
            match_tx = re.search(r"Transaction\s*ID[^\w\n-]*[:\s\n]+([A-Za-z0-9]+|-)", text, re.IGNORECASE)
            if match_tx and not receipt_data["Transaction ID"]:
                receipt_data["Transaction ID"] = match_tx.group(1).strip()

            # ---------- Bill Month ----------
            match_bm = (
                re.search(r"Bill\s*Month[^\w\n]*[:\s\n]+([A-Za-z]+)\s*(?:-\s*)?(\d{4})", text, re.IGNORECASE)
                or re.search(r"Bill Month\s*\n\s*([A-Za-z]+)\s*\n.*?\b(202\d)\b", text, re.DOTALL)
            )
            if match_bm and not receipt_data["Bill Month"]:
                receipt_data["Bill Month"] = f"{match_bm.group(1)} {match_bm.group(2)}"

            # ---------- Category ----------
            match_cat = (
                re.search(r"Category[^\w\n]*[:\s\n]+([A-Za-z\s]+?)(?=\n|Order ID|Amount Paid|$)", text, re.IGNORECASE)
                or re.search(r"Category\s*\n.*?\b([A-Z\s]{4,}?)\s*\n\s*Order ID", text, re.DOTALL)
            )
            if match_cat and not receipt_data["Category"]:
                receipt_data["Category"] = match_cat.group(1).strip()

    except Exception:
        pass

    # Ensure Receipt No has a fallback to clean filename if not extracted
    if not receipt_data["Receipt No"]:
        clean_base = re.sub(r"\.pdf$", "", os.path.basename(source_name), flags=re.IGNORECASE).strip()
        receipt_data["Receipt No"] = clean_base

    # Numerical parse for amount paid
    amt_val = 0.0
    if receipt_data.get("Amount Paid"):
        try:
            amt_val = float(str(receipt_data["Amount Paid"]).replace(",", "").strip())
        except (ValueError, TypeError):
            amt_val = 0.0

    # Enrich with snake_case keys for database synchronization & backend compatibility
    receipt_data["receipt_no"] = receipt_data["Receipt No"]
    receipt_data["consumer_no"] = receipt_data["Consumer No"]
    receipt_data["account_no"] = receipt_data["Account NO"]
    receipt_data["consumer_name"] = receipt_data["Consumer Name"]
    receipt_data["collections_date"] = receipt_data["Collections Date"]
    receipt_data["amount_paid"] = amt_val
    receipt_data["payment_type"] = receipt_data["Payment Type"]
    receipt_data["transaction_id"] = receipt_data["Transaction ID"]
    receipt_data["bill_month"] = receipt_data["Bill Month"]
    receipt_data["category"] = receipt_data["Category"]
    receipt_data["source_pdf"] = receipt_data["Source PDF"]

    return receipt_data
