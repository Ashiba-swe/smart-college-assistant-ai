import re
from typing import List, Dict, Any

class TextChunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]

    def _split_text(self, text: str) -> List[str]:
        """Split text recursively by punctuation and whitespace."""
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        # Find best separator
        separator = " "
        for s in self.separators:
            if s in text:
                separator = s
                break

        parts = text.split(separator)
        chunks = []
        current_chunk = []
        current_len = 0

        for part in parts:
            part_str = part + (separator if separator != " " else " ")
            part_len = len(part_str)

            if current_len + part_len > self.chunk_size and current_chunk:
                chunk_text = "".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)

                # Keep overlap from previous chunk
                overlap_text = []
                overlap_len = 0
                for prev in reversed(current_chunk):
                    if overlap_len + len(prev) <= self.chunk_overlap:
                        overlap_text.insert(0, prev)
                        overlap_len += len(prev)
                    else:
                        break
                current_chunk = overlap_text
                current_len = overlap_len

            current_chunk.append(part_str)
            current_len += part_len

        if current_chunk:
            final_text = "".join(current_chunk).strip()
            if final_text:
                chunks.append(final_text)

        return chunks

    def chunk_document(
        self,
        extracted_pages: List[Dict[str, Any]],
        doc_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Takes raw page extractions and converts them into indexed chunks
        with metadata attached.
        """
        all_chunks = []
        chunk_idx = 0

        for page_data in extracted_pages:
            page_text = page_data.get('text', '')
            page_num = page_data.get('page', 1)
            raw_chunks = self._split_text(page_text)

            for text in raw_chunks:
                if len(text.strip()) < 20:  # Skip trivial fragments
                    continue

                chunk_id = f"doc_{doc_metadata.get('id', 0)}_p{page_num}_c{chunk_idx}"
                metadata = {
                    'doc_id': int(doc_metadata.get('id', 0)),
                    'title': str(doc_metadata.get('title', 'Unknown Document')),
                    'filename': str(doc_metadata.get('filename', '')),
                    'page': int(page_num),
                    'category': str(doc_metadata.get('category', 'General')),
                    'department': str(doc_metadata.get('department', 'All Departments')),
                    'chunk_index': int(chunk_idx)
                }
                all_chunks.append({
                    'id': chunk_id,
                    'text': text,
                    'metadata': metadata
                })
                chunk_idx += 1

        return all_chunks
