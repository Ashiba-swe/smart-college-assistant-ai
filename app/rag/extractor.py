import os
import re

def clean_text(text: str) -> str:
    """Normalize whitespace and strip non-printable characters."""
    if not text:
        return ""
    # Replace multiple newlines or tabs with standard spacing
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_pdf(file_path: str):
    """
    Extract text from PDF using PyMuPDF (fitz), returning page-by-page chunks.
    """
    import pymupdf
    pages_data = []
    filename = os.path.basename(file_path)
    
    with pymupdf.open(file_path) as doc:
        for page_idx, page in enumerate(doc):
            text = page.get_text()
            cleaned = clean_text(text)
            if cleaned:
                pages_data.append({
                    'page': page_idx + 1,
                    'text': cleaned,
                    'source': filename,
                    'file_type': 'pdf'
                })
    return pages_data

def extract_docx(file_path: str):
    """
    Extract text from DOCX file including paragraphs and tables.
    """
    import docx
    doc = docx.Document(file_path)
    filename = os.path.basename(file_path)
    full_text = []
    
    # Extract paragraphs
    for p in doc.paragraphs:
        if p.text.strip():
            full_text.append(p.text.strip())
            
    # Extract tables
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                full_text.append(" | ".join(row_text))
                
    combined = "\n\n".join(full_text)
    cleaned = clean_text(combined)
    return [{
        'page': 1,
        'text': cleaned,
        'source': filename,
        'file_type': 'docx'
    }] if cleaned else []

def extract_txt(file_path: str):
    """
    Extract text from standard UTF-8 text file.
    """
    filename = os.path.basename(file_path)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    cleaned = clean_text(content)
    return [{
        'page': 1,
        'text': cleaned,
        'source': filename,
        'file_type': 'txt'
    }] if cleaned else []

def extract_document(file_path: str):
    """
    Dispatcher to extract text based on file extension.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if ext == 'pdf':
        return extract_pdf(file_path)
    elif ext in ['docx', 'doc']:
        return extract_docx(file_path)
    elif ext in ['txt', 'md']:
        return extract_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: .{ext}")
