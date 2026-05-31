import os
from docling.document_converter import DocumentConverter

def parse_fir_pdf(file_path: str) -> str:
    if not os.path.exists(file_path): raise FileNotFoundError("File not found")
    ext = file_path.lower().split('.')[-1]
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f: return f.read()
        return DocumentConverter().convert(file_path).document.export_to_markdown()
    except Exception as e:
        if ext == 'pdf':
            from pypdf import PdfReader
            text = ""
            for page in PdfReader(file_path).pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
            return text
        return f"Extraction failed: {e}"
