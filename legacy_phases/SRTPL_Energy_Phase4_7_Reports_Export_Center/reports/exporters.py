from io import BytesIO, StringIO
import csv

def export_csv(rows, columns):
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8-sig")

def export_xlsx(rows, columns):
    # Production implementation should use openpyxl.
    # This lightweight phase keeps export contract separate from data retrieval.
    try:
        from openpyxl import Workbook
    except ImportError:
        raise RuntimeError("openpyxl is required for Excel export.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    ws.append(columns)
    for row in rows:
        ws.append([row.get(c) for c in columns])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

def export_pdf(report_title, rows, columns):
    # Production implementation should use reportlab.
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    except ImportError:
        raise RuntimeError("reportlab is required for PDF export.")

    from io import BytesIO
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    data = [columns] + [[str(row.get(c, "")) for c in columns] for row in rows[:500]]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ]))
    doc.build([Paragraph(report_title, styles["Title"]), table])
    return buf.getvalue()
