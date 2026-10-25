import pdfplumber
import glob
import re

pdfs = glob.glob('source_data/user_uploaded_bills/extractor/*EN.pdf')

for p in pdfs:
    fname = p.split('\\')[-1]
    with pdfplumber.open(p) as pdf:
        text = pdf.pages[0].extract_text()
        m = re.search(r'Bill Period\s*:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', text)
        if m:
            print(f'{fname}: {m.group(1)} - {m.group(2)}')
        else:
            m2 = re.search(r'Bill Period\s*:\s*([0-9/\s\-]+)', text)
            raw = m2.group(1).replace('\n', ' ').strip() if m2 else 'NONE'
            print(f'{fname} RAW: {raw}')
