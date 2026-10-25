import pdfplumber

with pdfplumber.open('source_data/user_uploaded_bills/extractor/411001070208_82025_EN.pdf') as pdf:
    lines = pdf.pages[0].extract_text().splitlines()
    for idx, l in enumerate(lines):
        if 'Bill Period' in l:
            for k in range(max(0, idx-2), min(len(lines), idx+4)):
                print(f'{k}: {lines[k]}')
