import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional

class VectorStore:
    def __init__(self, persist_directory: str):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False, is_persistent=True)
        )
        self.collection_name = "college_knowledge_base"
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Apex Institute Knowledge Base Chunks"}
            )
        return self._collection

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Add list of chunks to the vector store.
        Each chunk: {'id': str, 'text': str, 'metadata': dict}
        """
        if not chunks:
            return 0

        ids = [c['id'] for c in chunks]
        documents = [c['text'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]

        # ChromaDB accepts batches of up to ~4000 items
        batch_size = 200
        for i in range(0, len(ids), batch_size):
            b_ids = ids[i:i+batch_size]
            b_docs = documents[i:i+batch_size]
            b_meta = metadatas[i:i+batch_size]
            self.collection.upsert(
                ids=b_ids,
                documents=b_docs,
                metadatas=b_meta
            )
        return len(ids)

    def delete_by_doc_id(self, doc_id: int) -> bool:
        """
        Delete all indexed chunks associated with a specific document ID.
        """
        try:
            self.collection.delete(where={"doc_id": int(doc_id)})
            return True
        except Exception as e:
            print(f"Error deleting chunks for doc_id {doc_id}: {e}")
            return False

    def search(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity retrieval.
        Returns sorted list of matches with metadata and similarity scores.
        """
        if not query or not query.strip():
            return []

        where_clause = None
        if category and category.lower() != 'all' and category.lower() != 'all departments':
            where_clause = {"category": category}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(k, max(1, self.collection.count())),
                where=where_clause
            )
        except Exception as e:
            print(f"ChromaDB search error: {e}")
            return []

        retrieved = []
        if not results or not results.get('documents') or not results['documents'][0]:
            return []

        docs = results['documents'][0]
        metas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(docs)
        distances = results['distances'][0] if results.get('distances') else [1.0] * len(docs)

        for text, meta, dist in zip(docs, metas, distances):
            # ChromaDB cosine distance: 0.0 (identical) to 2.0 (opposite)
            # Standard Cosine Similarity formula: S = (1.0 - (dist / 2.0)) * 100%
            similarity_pct = round(max(0.0, min(100.0, (1.0 - (dist / 2.0)) * 100)), 1)
            
            retrieved.append({
                'text': text,
                'metadata': meta,
                'distance': dist,
                'similarity': similarity_pct,
                'title': meta.get('title', 'College Document'),
                'page': meta.get('page', 1),
                'filename': meta.get('filename', ''),
                'category': meta.get('category', 'General')
            })

        # Sort by highest similarity
        retrieved.sort(key=lambda x: x['similarity'], reverse=True)
        return retrieved

    def count(self) -> int:
        """Total chunks currently indexed."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear(self):
        """Reset the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self._collection = None
        except Exception:
            pass
