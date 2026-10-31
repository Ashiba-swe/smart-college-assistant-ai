import hashlib
import os
from typing import List, Dict, Any, Optional
from app.rag.extractor import extract_document
from app.rag.chunker import TextChunker
from app.rag.vector_store import VectorStore
from app.rag.llm import LLMProvider

def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file to avoid redundant indexing."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()

class RAGEngine:
    def __init__(self, chroma_dir: str, gemini_api_key: str = "", model_name: str = "gemini-2.5-flash"):
        self.chroma_dir = chroma_dir
        self.vector_store = VectorStore(persist_directory=chroma_dir)
        self.chunker = TextChunker(chunk_size=600, chunk_overlap=100)
        self.llm = LLMProvider(api_key=gemini_api_key, model_name=model_name)

    def process_and_index_document(self, doc_record: Dict[str, Any]) -> int:
        """
        Extracts, chunks, and indexes a single document into the vector database.
        Returns the number of indexed chunks.
        """
        file_path = doc_record.get('file_path')
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file does not exist: {file_path}")

        # 1. Extract text
        extracted_pages = extract_document(file_path)
        if not extracted_pages:
            return 0

        # 2. Chunk document
        chunks = self.chunker.chunk_document(extracted_pages, doc_record)
        if not chunks:
            return 0

        # 3. Index chunks in ChromaDB
        indexed_count = self.vector_store.add_chunks(chunks)
        return indexed_count

    def index_faq(self, faq_record: Dict[str, Any]) -> int:
        """
        Indexes a verified FAQ into the vector store as a dedicated chunk.
        """
        faq_id = faq_record.get('id', 0)
        question = faq_record.get('question', '')
        answer = faq_record.get('answer', '')
        category = faq_record.get('category', 'General')
        department = faq_record.get('department', 'All Departments')

        text = f"Frequently Asked Question:\nQ: {question}\nA: {answer}"
        chunk = [{
            'id': f"faq_{faq_id}",
            'text': text,
            'metadata': {
                'doc_id': int(faq_id),
                'title': f"Verified FAQ: {question[:50]}",
                'filename': 'Official_FAQ_Database',
                'page': 1,
                'category': category,
                'department': department,
                'chunk_index': 0
            }
        }]
        return self.vector_store.add_chunks(chunk)

    def deindex_document(self, doc_id: int) -> bool:
        """Removes a document's chunks from vector database."""
        return self.vector_store.delete_by_doc_id(doc_id)

    def query(self, user_question: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Full RAG pipeline execution:
        Question -> Semantic Vector Search -> Context Assembly -> LLM Grounding -> Response & Citations
        """
        # 1. Semantic retrieval from vector store
        retrieved = self.vector_store.search(user_question, k=5, category=category)

        # 2. Generate grounded response with citations
        answer, sources, is_no_answer = self.llm.generate_response(
            question=user_question,
            retrieved_contexts=retrieved
        )

        return {
            'answer': answer,
            'sources': sources,
            'is_no_answer': is_no_answer,
            'retrieved_count': len(retrieved),
            'top_similarity': retrieved[0]['similarity'] if retrieved else 0.0
        }

    def get_stats(self) -> Dict[str, Any]:
        """Vector index diagnostics."""
        return {
            'total_indexed_chunks': self.vector_store.count(),
            'storage_directory': self.chroma_dir
        }
