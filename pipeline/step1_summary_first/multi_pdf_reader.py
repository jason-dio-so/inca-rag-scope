"""
STEP NEXT-45-B: Multi-PDF Reader

Multi-reader architecture for robust table extraction.
Tries multiple PDF parsers and selects best result based on table quality.

Readers:
- pdfplumber (default, fast)
- PyMuPDF (fitz, good for complex layouts)
- Camelot (lattice + stream, best for structured tables)

Quality Metric:
- Summary table detection rate (header keyword match + column count)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass

# PDF readers
import pdfplumber
import fitz  # PyMuPDF
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

logger = logging.getLogger(__name__)

ReaderType = Literal["pdfplumber", "pymupdf", "camelot_lattice", "camelot_stream"]


@dataclass
class TableSnapshot:
    """Single table snapshot from PDF"""
    page: int
    table_index: int
    row_count: int
    col_count: int
    header_rows: List[List[str]]  # First 3 rows
    header_text: str  # Joined header text
    has_coverage_keyword: bool
    has_amount_keyword: bool
    has_period_keyword: bool
    reader_type: ReaderType


@dataclass
class PDFStructure:
    """PDF structure metadata from a reader"""
    insurer: str
    pdf_path: str
    reader_type: ReaderType
    total_pages: int
    pages_with_tables: List[int]
    table_snapshots: List[TableSnapshot]
    summary_table_candidates: List[TableSnapshot]
    quality_score: float  # Summary table detection quality


class MultiPDFReader:
    """Multi-reader PDF parser with quality-based selection"""

    COVERAGE_KEYWORDS = ['담보', '보장', '가입담보']
    AMOUNT_KEYWORDS = ['보험료', '가입금액']
    PERIOD_KEYWORDS = ['납입', '만기', '납기']

    def __init__(self, pdf_path: Path, insurer: str):
        self.pdf_path = pdf_path
        self.insurer = insurer

    def read_all_readers(self) -> Dict[ReaderType, PDFStructure]:
        """Read PDF with all available readers"""
        results = {}

        # 1. pdfplumber (always available)
        logger.info(f"Reading {self.insurer} with pdfplumber...")
        results["pdfplumber"] = self._read_pdfplumber()

        # 2. PyMuPDF (always available)
        logger.info(f"Reading {self.insurer} with PyMuPDF...")
        results["pymupdf"] = self._read_pymupdf()

        # 3. Camelot (optional)
        if CAMELOT_AVAILABLE:
            logger.info(f"Reading {self.insurer} with Camelot (lattice)...")
            results["camelot_lattice"] = self._read_camelot(flavor="lattice")
            logger.info(f"Reading {self.insurer} with Camelot (stream)...")
            results["camelot_stream"] = self._read_camelot(flavor="stream")
        else:
            logger.warning("Camelot not available, skipping...")

        return results

    def select_best_reader(self, results: Dict[ReaderType, PDFStructure]) -> PDFStructure:
        """Select reader with highest summary table detection quality"""
        if not results:
            raise RuntimeError("No readers succeeded")

        best_reader = max(results.items(), key=lambda x: x[1].quality_score)
        logger.info(f"Best reader for {self.insurer}: {best_reader[0]} (quality: {best_reader[1].quality_score:.2f})")
        return best_reader[1]

    def _read_pdfplumber(self) -> PDFStructure:
        """Read PDF with pdfplumber"""
        snapshots = []
        pages_with_tables = []

        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()

                if not tables:
                    continue

                pages_with_tables.append(page_num)

                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue

                    snapshot = self._create_snapshot(
                        page_num, table_idx, table, "pdfplumber"
                    )
                    snapshots.append(snapshot)

        return self._build_structure("pdfplumber", total_pages, pages_with_tables, snapshots)

    def _read_pymupdf(self) -> PDFStructure:
        """Read PDF with PyMuPDF (fitz)"""
        snapshots = []
        pages_with_tables = []

        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)

        for page_num in range(total_pages):
            page = doc[page_num]
            tables = page.find_tables()

            if not tables.tables:
                continue

            pages_with_tables.append(page_num + 1)

            for table_idx, table in enumerate(tables.tables):
                raw_table = table.extract()
                if not raw_table or len(raw_table) < 2:
                    continue

                snapshot = self._create_snapshot(
                    page_num + 1, table_idx, raw_table, "pymupdf"
                )
                snapshots.append(snapshot)

        doc.close()
        return self._build_structure("pymupdf", total_pages, pages_with_tables, snapshots)

    def _read_camelot(self, flavor: str) -> PDFStructure:
        """Read PDF with Camelot"""
        if not CAMELOT_AVAILABLE:
            return self._empty_structure(f"camelot_{flavor}")

        snapshots = []
        pages_with_tables = []

        # Camelot requires page range
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)

        try:
            tables = camelot.read_pdf(
                str(self.pdf_path),
                pages='all',
                flavor=flavor,
                suppress_stdout=True
            )

            for table_idx, table in enumerate(tables):
                page_num = table.page
                raw_table = table.df.values.tolist()

                if not raw_table or len(raw_table) < 2:
                    continue

                if page_num not in pages_with_tables:
                    pages_with_tables.append(page_num)

                snapshot = self._create_snapshot(
                    page_num, table_idx, raw_table, f"camelot_{flavor}"
                )
                snapshots.append(snapshot)

        except Exception as e:
            logger.warning(f"Camelot {flavor} failed for {self.insurer}: {e}")
            return self._empty_structure(f"camelot_{flavor}")

        return self._build_structure(f"camelot_{flavor}", total_pages, pages_with_tables, snapshots)

    def _create_snapshot(
        self,
        page_num: int,
        table_idx: int,
        table: List[List[Any]],
        reader_type: ReaderType
    ) -> TableSnapshot:
        """Create table snapshot from raw table data"""
        # Extract header rows (first 3 rows)
        header_rows = []
        for row_idx in range(min(3, len(table))):
            header_row = [str(cell) if cell else "" for cell in table[row_idx]]
            header_rows.append(header_row)

        # Join header text
        header_text = ' '.join(
            str(cell) for row in header_rows for cell in row if cell
        )
        header_normalized = header_text.replace(' ', '').replace('\n', '')

        # Keyword detection
        has_coverage = any(kw in header_normalized for kw in self.COVERAGE_KEYWORDS)
        has_amount = any(kw in header_text for kw in self.AMOUNT_KEYWORDS)
        has_period = any(kw in header_text for kw in self.PERIOD_KEYWORDS)

        return TableSnapshot(
            page=page_num,
            table_index=table_idx,
            row_count=len(table),
            col_count=len(table[0]) if table else 0,
            header_rows=header_rows,
            header_text=header_text,
            has_coverage_keyword=has_coverage,
            has_amount_keyword=has_amount,
            has_period_keyword=has_period,
            reader_type=reader_type
        )

    def _build_structure(
        self,
        reader_type: ReaderType,
        total_pages: int,
        pages_with_tables: List[int],
        snapshots: List[TableSnapshot]
    ) -> PDFStructure:
        """Build PDFStructure from snapshots"""
        # Identify summary table candidates
        candidates = [
            s for s in snapshots
            if s.has_coverage_keyword and s.has_amount_keyword
        ]

        # Calculate quality score
        quality_score = self._calculate_quality(snapshots, candidates)

        return PDFStructure(
            insurer=self.insurer,
            pdf_path=str(self.pdf_path),
            reader_type=reader_type,
            total_pages=total_pages,
            pages_with_tables=sorted(set(pages_with_tables)),
            table_snapshots=snapshots,
            summary_table_candidates=candidates,
            quality_score=quality_score
        )

    def _calculate_quality(
        self,
        all_snapshots: List[TableSnapshot],
        summary_candidates: List[TableSnapshot]
    ) -> float:
        """
        Calculate quality score based on summary table detection

        Metrics:
        - Summary candidate ratio (0-1)
        - Average summary candidate row count (higher = better)
        - Keyword completeness (coverage + amount + period)
        """
        if not all_snapshots:
            return 0.0

        # Ratio of summary candidates
        ratio = len(summary_candidates) / len(all_snapshots)

        # Average row count for summary candidates (normalize to 0-1)
        avg_rows = sum(s.row_count for s in summary_candidates) / len(summary_candidates) if summary_candidates else 0
        row_score = min(avg_rows / 40.0, 1.0)  # Assume 40 rows as "ideal"

        # Keyword completeness
        complete_count = sum(
            1 for s in summary_candidates
            if s.has_coverage_keyword and s.has_amount_keyword and s.has_period_keyword
        )
        completeness = complete_count / len(summary_candidates) if summary_candidates else 0

        # Weighted average
        quality = (ratio * 0.3) + (row_score * 0.3) + (completeness * 0.4)
        return quality

    def _empty_structure(self, reader_type: ReaderType) -> PDFStructure:
        """Return empty structure for failed reader"""
        return PDFStructure(
            insurer=self.insurer,
            pdf_path=str(self.pdf_path),
            reader_type=reader_type,
            total_pages=0,
            pages_with_tables=[],
            table_snapshots=[],
            summary_table_candidates=[],
            quality_score=0.0
        )
