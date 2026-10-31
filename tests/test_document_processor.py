import os
import pytest
from app.rag.extractor import extract_document, extract_pdf, extract_docx, extract_txt
from app.rag.chunker import TextChunker
from app.rag.engine import compute_checksum

def test_extract_txt(tmp_path):
    txt_file = tmp_path / "test_notice.txt"
    txt_file.write_text("Apex Institute: Examination commences on Dec 1st.", encoding="utf-8")
    
    extracted = extract_txt(str(txt_file))
    assert len(extracted) == 1
    assert "Examination commences" in extracted[0]['text']
    assert extracted[0]['page'] == 1

def test_extract_sample_pdf(app):
    pdf_path = os.path.join(app.config['SAMPLE_DOCS_FOLDER'], 'College_Handbook.pdf')
    if os.path.exists(pdf_path):
        pages = extract_pdf(pdf_path)
        assert len(pages) > 0
        assert any("Academic Regulations" in p['text'] for p in pages)

def test_extract_sample_docx(app):
    docx_path = os.path.join(app.config['SAMPLE_DOCS_FOLDER'], 'Placement_Policy.docx')
    if os.path.exists(docx_path):
        docs = extract_docx(docx_path)
        assert len(docs) > 0
        assert "Placement Policy" in docs[0]['text']

def test_chunker_metadata_preservation():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    pages = [
        {'page': 1, 'text': 'Apex Institute was established in 2004. It offers courses in Computer Science and Engineering. Students must earn 160 credits to graduate with an engineering degree.'}
    ]
    meta = {
        'id': 42,
        'title': 'Test Handbook',
        'filename': 'handbook.pdf',
        'category': 'Academic'
    }
    chunks = chunker.chunk_document(pages, meta)
    assert len(chunks) > 0
    assert chunks[0]['metadata']['doc_id'] == 42
    assert chunks[0]['metadata']['title'] == 'Test Handbook'
    assert chunks[0]['metadata']['page'] == 1
    assert chunks[0]['id'].startswith('doc_42_p1_')

def test_checksum_computation(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Consistent SHA256 test", encoding="utf-8")
    c1 = compute_checksum(str(f))
    c2 = compute_checksum(str(f))
    assert c1 == c2
    assert len(c1) == 64
