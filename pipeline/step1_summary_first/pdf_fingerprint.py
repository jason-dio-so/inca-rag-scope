"""
PDF Fingerprint Module (STEP NEXT-45-D)

Purpose:
    Compute deterministic fingerprint of PDF files to ensure profile reproducibility.

Constitutional:
    - Deterministic only (no LLM/inference)
    - SHA256 hash of first 2MB (or entire file if smaller)
    - Page count + file size + basename

Usage:
    fingerprint = compute_pdf_fingerprint(pdf_path)
"""

import hashlib
import os
from pathlib import Path
from typing import Dict

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def compute_pdf_fingerprint(pdf_path: str) -> Dict[str, any]:
    """
    Compute deterministic fingerprint of a PDF file.

    Args:
        pdf_path: Absolute or relative path to PDF file

    Returns:
        Dictionary containing:
        - file_size_bytes: int
        - page_count: int
        - sha256_first_2mb: str (hex digest)
        - source_basename: str

    Raises:
        FileNotFoundError: If PDF does not exist
        RuntimeError: If PDF cannot be opened
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # File size
    file_size = pdf_path.stat().st_size

    # Page count
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF {pdf_path}: {e}")

    # SHA256 of first 2MB (or entire file if smaller)
    hash_obj = hashlib.sha256()
    bytes_to_read = min(file_size, 2 * 1024 * 1024)  # 2MB

    with open(pdf_path, 'rb') as f:
        chunk = f.read(bytes_to_read)
        hash_obj.update(chunk)

    sha256_digest = hash_obj.hexdigest()

    return {
        "file_size_bytes": file_size,
        "page_count": page_count,
        "sha256_first_2mb": sha256_digest,
        "source_basename": pdf_path.name
    }


def fingerprints_match(fp1: Dict, fp2: Dict) -> bool:
    """
    Check if two fingerprints match exactly.

    Args:
        fp1, fp2: Fingerprint dictionaries from compute_pdf_fingerprint()

    Returns:
        True if all fields match, False otherwise
    """
    required_fields = ["file_size_bytes", "page_count", "sha256_first_2mb", "source_basename"]

    for field in required_fields:
        if field not in fp1 or field not in fp2:
            return False
        if fp1[field] != fp2[field]:
            return False

    return True
