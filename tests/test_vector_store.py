import pytest
from app.rag.vector_store import VectorStore

def test_vector_store_crud(temp_chroma_dir):
    vs = VectorStore(persist_directory=temp_chroma_dir)
    vs.clear()

    # 1. Add chunks
    chunks = [
        {
            'id': 'chunk_1',
            'text': 'The college central library remains open from 8am to 8pm on weekdays.',
            'metadata': {'doc_id': 101, 'title': 'Library Policy', 'filename': 'lib.pdf', 'page': 1, 'category': 'Library'}
        },
        {
            'id': 'chunk_2',
            'text': 'A minimum of 75 percent attendance is mandatory to appear for university examinations.',
            'metadata': {'doc_id': 102, 'title': 'Handbook', 'filename': 'handbook.pdf', 'page': 2, 'category': 'Academics'}
        }
    ]
    added = vs.add_chunks(chunks)
    assert added == 2
    assert vs.count() == 2

    # 2. Semantic search
    results = vs.search("What are the library hours?", k=1)
    assert len(results) == 1
    assert "8am to 8pm" in results[0]['text']
    assert results[0]['title'] == 'Library Policy'
    assert results[0]['similarity'] > 40.0

    # 3. Delete by doc_id
    deleted = vs.delete_by_doc_id(101)
    assert deleted is True
    assert vs.count() == 1

    # Remaining chunk should be handbook
    remaining = vs.search("attendance", k=1)
    assert len(remaining) == 1
    assert remaining[0]['metadata']['doc_id'] == 102
