"""Check what text is extracted from each page of the PDF"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber

with pdfplumber.open("backend/knowledge/Kaizen.pdf") as pdf:
    for i, page in enumerate(pdf.pages, 1):
        text = page.extract_text()
        if text and text.strip():
            preview = text.strip()[:200].replace('\n', ' | ')
            print(f"Page {i}: {preview}")
        else:
            print(f"Page {i}: [EMPTY / NO TEXT]")
