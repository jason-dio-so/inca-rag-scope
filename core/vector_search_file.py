"""
STEP NEXT-66: File-based Vector Search (MVP)

Constitutional Rules:
- NO LLM usage
- Uses local sentence-transformers (ko-sroberta-multitask)
- File-based index (JSONL + numpy arrays)
- Cosine similarity ranking
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer

from core.vector_chunk import EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_VERSION


# Model singleton (lazy load)
_MODEL = None


def get_model() -> SentenceTransformer:
    """Get or create embedding model (singleton)"""
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _MODEL


@dataclass
class ChunkHit:
    """Search result hit"""
    chunk_id: str
    axis: str
    doc_type: str
    page: int
    text: str
    score: float
    file_path: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class FileVectorIndex:
    """
    File-based vector index.

    Structure:
    - data/vector_index/v1/{axis}__chunks.jsonl (metadata + text)
    - data/vector_index/v1/{axis}__embeddings.npy (embeddings array)
    """

    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.model = get_model()

    def load_index(self, axis: str) -> tuple[List[Dict], np.ndarray]:
        """
        Load index for an axis.

        Returns:
            (chunks_metadata, embeddings_array)
        """
        chunks_path = self.index_dir / f"{axis}__chunks.jsonl"
        embeddings_path = self.index_dir / f"{axis}__embeddings.npy"

        if not chunks_path.exists():
            raise FileNotFoundError(f"Index not found: {chunks_path}")
        if not embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings not found: {embeddings_path}")

        # Load chunks metadata
        chunks = []
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunks.append(json.loads(line))

        # Load embeddings
        embeddings = np.load(embeddings_path)

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
            )

        return chunks, embeddings

    def search(self, axis: str, query: str,
               doc_types: Optional[List[str]] = None,
               top_k: int = 10) -> List[ChunkHit]:
        """
        Search for relevant chunks.

        Args:
            axis: Insurance axis to search
            query: Search query text
            doc_types: Filter by doc_type (e.g., ['약관', '사업방법서'])
            top_k: Number of results to return

        Returns:
            List of ChunkHit objects, sorted by score (descending)
        """
        # Load index
        chunks, embeddings = self.load_index(axis)

        # Filter by doc_type if specified
        if doc_types:
            filtered_indices = [
                i for i, c in enumerate(chunks)
                if c.get('doc_type') in doc_types
            ]
            chunks = [chunks[i] for i in filtered_indices]
            embeddings = embeddings[filtered_indices]

        if len(chunks) == 0:
            return []

        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Compute cosine similarity
        scores = self._cosine_similarity(query_embedding, embeddings)

        # Get top_k
        top_indices = np.argsort(scores)[::-1][:top_k]

        hits = []
        for idx in top_indices:
            chunk = chunks[idx]
            hit = ChunkHit(
                chunk_id=chunk['chunk_id'],
                axis=chunk['axis'],
                doc_type=chunk['doc_type'],
                page=chunk['page'],
                text=chunk['text'][:500],  # Truncate for preview
                score=float(scores[idx]),
                file_path=chunk.get('file_path')
            )
            hits.append(hit)

        return hits

    @staticmethod
    def _cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and documents.

        Args:
            query_vec: 1D array (embedding dimension)
            doc_vecs: 2D array (num_docs x embedding_dim)

        Returns:
            1D array of similarity scores
        """
        # Normalize
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-8)

        # Dot product
        scores = np.dot(doc_norms, query_norm)

        return scores


# Convenience function
def search_chunks(axis: str, query: str,
                 doc_types: Optional[List[str]] = None,
                 top_k: int = 10,
                 index_dir: str = "data/vector_index/v1") -> List[ChunkHit]:
    """
    Search for chunks (convenience wrapper).

    Args:
        axis: Insurance axis (e.g., "samsung")
        query: Search query
        doc_types: Filter by document types
        top_k: Number of results
        index_dir: Index directory path

    Returns:
        List of ChunkHit objects
    """
    index = FileVectorIndex(Path(index_dir))
    return index.search(axis, query, doc_types, top_k)
