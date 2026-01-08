"""
Document Reader for Evidence Extraction

Reads PDF documents (proposal, summary, terms, etc.) and provides
text access for pattern matching.

STEP NEXT-67: Deterministic text extraction only. NO OCR. NO LLM.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import pymupdf  # PyMuPDF


class DocumentSource:
    """Represents a single document source (PDF)"""

    def __init__(self, doc_type: str, pdf_path: Path):
        self.doc_type = doc_type  # 가입설계서, 약관, 사업방법서, 상품요약서
        self.pdf_path = pdf_path
        self._pages_text: Optional[Dict[int, str]] = None

    def load_text(self):
        """Load text from PDF (lazy loading)"""
        if self._pages_text is not None:
            return

        self._pages_text = {}

        try:
            doc = pymupdf.open(str(self.pdf_path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                self._pages_text[page_num + 1] = text  # 1-based page numbers
            doc.close()
        except Exception as e:
            raise RuntimeError(f"Failed to load PDF {self.pdf_path}: {e}")

    def get_page_text(self, page_num: int) -> str:
        """Get text for a specific page (1-based)"""
        if self._pages_text is None:
            self.load_text()
        return self._pages_text.get(page_num, "")

    def get_all_text(self) -> str:
        """Get concatenated text from all pages"""
        if self._pages_text is None:
            self.load_text()
        return "\n\n=== PAGE BREAK ===\n\n".join(
            self._pages_text[p] for p in sorted(self._pages_text.keys())
        )

    def get_page_count(self) -> int:
        """Get total page count"""
        if self._pages_text is None:
            self.load_text()
        return len(self._pages_text)


class DocumentSet:
    """Collection of documents for an insurer's product"""

    # Variant key to base insurer directory mapping
    VARIANT_TO_BASE_INSURER = {
        "db_over41": "db",
        "db_under40": "db",
        "lotte_female": "lotte",
        "lotte_male": "lotte"
    }

    def __init__(self, insurer_key: str, sources_base_dir: Path, variant_key: str = None):
        """
        Args:
            insurer_key: Insurer identifier (e.g., "kb", "samsung", "db_over41")
            sources_base_dir: Base directory containing insurer documents
            variant_key: Optional variant identifier for PDF selection
        """
        self.insurer_key = insurer_key
        self.variant_key = variant_key or insurer_key
        self.sources_base_dir = sources_base_dir
        self.documents: Dict[str, DocumentSource] = {}

        self._discover_documents()

    def _discover_documents(self):
        """
        Discover available documents for this insurer.

        Expected structure:
        data/sources/insurers/{insurer}/
            가입설계서/{insurer}_가입설계서.pdf
            상품요약서/{insurer}_상품요약서.pdf
            사업방법서/{insurer}_사업방법서.pdf
            약관/{insurer}_약관.pdf

        For variant insurers (db_over41, db_under40, lotte_female, lotte_male),
        maps to base directory (db, lotte) and selects variant-specific PDFs.
        """
        # Map variant key to base insurer directory
        base_insurer = self.VARIANT_TO_BASE_INSURER.get(self.insurer_key, self.insurer_key)
        insurer_dir = self.sources_base_dir / base_insurer

        print(f"[DocumentSet] Discovering documents for {self.insurer_key}")
        print(f"[DocumentSet] Base insurer: {base_insurer}, Directory: {insurer_dir}")

        if not insurer_dir.exists():
            raise RuntimeError(f"Insurer directory not found: {insurer_dir}")

        # Document types to search for (in priority order)
        doc_types = ["가입설계서", "상품요약서", "사업방법서", "약관"]

        for doc_type in doc_types:
            doc_dir = insurer_dir / doc_type
            if not doc_dir.exists():
                print(f"[DocumentSet] {doc_type} directory not found")
                continue

            # Find PDF in directory
            pdf_files = list(doc_dir.glob("*.pdf"))
            if not pdf_files:
                print(f"[DocumentSet] No PDFs found in {doc_type} directory")
                continue

            print(f"[DocumentSet] Found {len(pdf_files)} PDF(s) in {doc_type}: {[p.name for p in pdf_files]}")

            # For variant insurers, select variant-specific PDF
            selected_pdf = self._select_variant_pdf(pdf_files, self.insurer_key)
            if selected_pdf:
                print(f"[DocumentSet] Selected PDF for {doc_type}: {selected_pdf.name}")
                self.documents[doc_type] = DocumentSource(doc_type, selected_pdf)

        print(f"[DocumentSet] Total documents discovered: {len(self.documents)}")
        print(f"[DocumentSet] Document types: {list(self.documents.keys())}")
        print()

    def _select_variant_pdf(self, pdf_files: List[Path], insurer_key: str) -> Optional[Path]:
        """
        Select PDF file matching the variant.

        For db_over41/db_under40: matches age-based PDFs
        For lotte_female/lotte_male: matches gender-based PDFs
        For others: returns first PDF
        """
        if not pdf_files:
            return None

        # Variant-specific selection rules
        variant_patterns = {
            "db_over41": ["41세이상", "41세 이상"],
            "db_under40": ["40세이하", "40세 이하"],
            "lotte_female": ["여", "(여)"],
            "lotte_male": ["남", "(남)"]
        }

        patterns = variant_patterns.get(insurer_key)
        if patterns:
            # Try to find matching PDF
            for pdf_path in pdf_files:
                pdf_name = pdf_path.name
                if any(pattern in pdf_name for pattern in patterns):
                    return pdf_path
            # If no match found, log warning and use first PDF
            print(f"[WARNING] No variant-specific PDF found for {insurer_key}, using first available")

        # Default: use first PDF
        return pdf_files[0]

    def get_document(self, doc_type: str) -> Optional[DocumentSource]:
        """Get document by type"""
        return self.documents.get(doc_type)

    def get_available_doc_types(self) -> List[str]:
        """Get list of available document types"""
        return list(self.documents.keys())

    def search_all_documents(
        self,
        search_order: List[str] = None
    ) -> List[DocumentSource]:
        """
        Get documents in search order.

        Default order: 가입설계서 → 상품요약서 → 사업방법서 → 약관
        """
        if search_order is None:
            search_order = ["가입설계서", "상품요약서", "사업방법서", "약관"]

        docs = []
        for doc_type in search_order:
            doc = self.get_document(doc_type)
            if doc:
                docs.append(doc)

        return docs


def load_document_set(insurer_key: str, sources_base_dir: str = None) -> DocumentSet:
    """
    Convenience function to load document set for an insurer.

    Args:
        insurer_key: Insurer identifier
        sources_base_dir: Base directory (defaults to data/sources/insurers)

    Returns:
        DocumentSet instance
    """
    if sources_base_dir is None:
        # Default to project structure
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sources_base_dir = project_root / "data" / "sources" / "insurers"

    return DocumentSet(insurer_key, Path(sources_base_dir))
