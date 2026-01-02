"""
STEP NEXT-66: Vector Chunking (Deterministic)

Constitutional Rules:
- NO LLM usage
- Deterministic text splitting (paragraph/sentence boundaries)
- Content-based deduplication (SHA256)
- Evidence traceability (doc_type/page/file_path)
"""

import re
import hashlib
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


# Embedding model version (FROZEN for reproducibility)
EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"
EMBEDDING_MODEL_VERSION = "v1.0"


@dataclass
class Chunk:
    """Vector chunk with metadata"""
    axis: str
    insurer: str
    doc_type: str
    file_path: str
    page: int
    chunk_id: str
    text: str
    content_hash: str

    def to_dict(self) -> dict:
        return asdict(self)


class TextChunker:
    """
    Deterministic text chunker for evidence documents.

    Rules:
    - Target chunk size: 200-500 characters
    - Split by paragraphs first, then sentences if needed
    - Normalize whitespace/newlines before hashing
    - Generate deterministic chunk_id: {axis}|{doc_type}|{page}|{seq:02d}
    """

    MIN_CHUNK_SIZE = 200
    MAX_CHUNK_SIZE = 500
    MIN_SENTENCE_LENGTH = 15

    # Noise patterns to skip (TOC, headers, page numbers)
    SKIP_PATTERNS = [
        r'^\s*\d+\s*/\s*\d+\s*$',  # Page numbers: "3 / 1559"
        r'^\s*\[\s*목\s*차\s*\]\s*$',  # [목차]
        r'^\s*제\d+조\s*$',  # Article numbers only
        r'^\s*\d+[-\.]\d+[-\.]?\d*\s*$',  # Section numbers only
    ]

    @classmethod
    def chunk_page(cls, axis: str, insurer: str, doc_type: str,
                   file_path: str, page: int, text: str) -> List[Chunk]:
        """
        Chunk a single page into semantic units.

        Args:
            axis: Insurance axis (e.g., "samsung")
            insurer: Insurer name
            doc_type: Document type (약관/사업방법서/상품요약서)
            file_path: Source file path
            page: Page number
            text: Full page text

        Returns:
            List of Chunk objects
        """
        # Skip empty pages
        if not text or len(text.strip()) < cls.MIN_SENTENCE_LENGTH:
            return []

        # Split into paragraphs
        paragraphs = cls._split_paragraphs(text)

        chunks = []
        chunk_seq = 0

        for para in paragraphs:
            # Skip noise
            if cls._is_noise(para):
                continue

            # If paragraph is within target size, use as-is
            if cls.MIN_CHUNK_SIZE <= len(para) <= cls.MAX_CHUNK_SIZE:
                chunk = cls._create_chunk(
                    axis, insurer, doc_type, file_path, page,
                    chunk_seq, para
                )
                chunks.append(chunk)
                chunk_seq += 1

            # If too large, split by sentences
            elif len(para) > cls.MAX_CHUNK_SIZE:
                sentences = cls._split_sentences(para)

                # Accumulate sentences until target size
                accumulated = []
                for sent in sentences:
                    accumulated.append(sent)
                    combined = ' '.join(accumulated)

                    if len(combined) >= cls.MIN_CHUNK_SIZE:
                        chunk = cls._create_chunk(
                            axis, insurer, doc_type, file_path, page,
                            chunk_seq, combined
                        )
                        chunks.append(chunk)
                        chunk_seq += 1
                        accumulated = []

                # Handle remaining sentences
                if accumulated:
                    combined = ' '.join(accumulated)
                    if len(combined) >= cls.MIN_SENTENCE_LENGTH:
                        chunk = cls._create_chunk(
                            axis, insurer, doc_type, file_path, page,
                            chunk_seq, combined
                        )
                        chunks.append(chunk)
                        chunk_seq += 1

            # If too small, skip (likely a fragment)
            # NOTE: Could accumulate small paragraphs, but keeping simple for MVP

        return chunks

    @classmethod
    def _split_paragraphs(cls, text: str) -> List[str]:
        """Split text into paragraphs (by double newline or bullet points)"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Split by common paragraph markers
        # Korean documents often use: ·, •, -, numbered lists
        para_markers = r'(?:^|\n)(?:·|•|-|\d+\.|\d+\))\s+'
        parts = re.split(para_markers, text)

        # Also split by double spaces (common in OCR)
        final_parts = []
        for part in parts:
            if '  ' in part:  # Double space
                final_parts.extend(part.split('  '))
            else:
                final_parts.append(part)

        # Filter and clean
        paragraphs = []
        for p in final_parts:
            p = p.strip()
            if p and len(p) >= cls.MIN_SENTENCE_LENGTH:
                paragraphs.append(p)

        return paragraphs

    @classmethod
    def _split_sentences(cls, text: str) -> List[str]:
        """Split text into sentences"""
        # Korean sentence endings: .  。 ! ?
        sentence_endings = r'[.。!?]\s+'
        sentences = re.split(sentence_endings, text)

        # Filter
        valid = []
        for s in sentences:
            s = s.strip()
            if s and len(s) >= cls.MIN_SENTENCE_LENGTH:
                valid.append(s)

        return valid

    @classmethod
    def _is_noise(cls, text: str) -> bool:
        """Check if text is structural noise (TOC, headers, etc.)"""
        for pattern in cls.SKIP_PATTERNS:
            if re.match(pattern, text.strip()):
                return True
        return False

    @classmethod
    def _create_chunk(cls, axis: str, insurer: str, doc_type: str,
                     file_path: str, page: int, seq: int, text: str) -> Chunk:
        """Create a Chunk object with metadata"""
        # Normalize text for hashing (whitespace normalization)
        normalized = re.sub(r'\s+', ' ', text.strip())
        content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()

        # Generate deterministic chunk_id
        chunk_id = f"{axis}|{doc_type}|{page:04d}|{seq:02d}"

        return Chunk(
            axis=axis,
            insurer=insurer,
            doc_type=doc_type,
            file_path=file_path,
            page=page,
            chunk_id=chunk_id,
            text=normalized,
            content_hash=content_hash
        )


def chunk_page_jsonl(axis: str, insurer: str, doc_type: str,
                     page_jsonl_path: str) -> List[Chunk]:
    """
    Chunk all pages in a page.jsonl file.

    Args:
        axis: Insurance axis
        insurer: Insurer name
        doc_type: Document type
        page_jsonl_path: Path to *.page.jsonl file

    Returns:
        List of Chunk objects
    """
    chunks = []

    with open(page_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            page_data = json.loads(line)
            page_num = page_data.get('page', 0)
            text = page_data.get('text', '')

            page_chunks = TextChunker.chunk_page(
                axis, insurer, doc_type, page_jsonl_path, page_num, text
            )
            chunks.extend(page_chunks)

    return chunks
