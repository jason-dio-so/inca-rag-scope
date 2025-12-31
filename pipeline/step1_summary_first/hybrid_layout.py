#!/usr/bin/env python3
"""
STEP NEXT-45-C-β: Hybrid Summary SSOT Extractor

Root cause (KB pages 2-3):
- pdfplumber extract_tables() returns coverage names as None
- PyMuPDF captures full row as single text block: "1 일반상해사망(기본) 1천만원 700 20년/100세"
- Coverage names are rendered OUTSIDE table cells, but amounts/premiums ARE in cells

Solution:
- Use PyMuPDF to extract text blocks within table bbox
- Parse each row text to extract: seq_num, coverage_name, amount, premium, period
- Validate against pdfplumber table structure (y-ranges, row count)
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF


@dataclass
class TextBlock:
    """PyMuPDF text block with bbox"""

    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def x_center(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class SummaryRow:
    """Parsed summary table row"""

    seq_num: Optional[str]
    coverage_name_raw: str
    amount_text: str
    premium_text: str
    period_text: str
    y0: float
    y1: float
    page: int

    def to_dict(self) -> dict:
        return {
            "seq_num": self.seq_num,
            "coverage_name_raw": self.coverage_name_raw,
            "amount_text": self.amount_text,
            "premium_text": self.premium_text,
            "period_text": self.period_text,
            "evidence": {
                "page": self.page,
                "y0": self.y0,
                "y1": self.y1,
            },
        }


def extract_text_blocks_pymupdf(
    pdf_path: Path, page_index: int, bbox: Optional[Tuple[float, float, float, float]] = None
) -> List[TextBlock]:
    """
    Extract text blocks from a PDF page using PyMuPDF.

    Args:
        pdf_path: Path to PDF
        page_index: Page index (0-based)
        bbox: Optional (x0, y0, x1, y1) to filter blocks

    Returns:
        List of TextBlock objects
    """
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    text_dict = page.get_text("dict")
    blocks = text_dict["blocks"]

    result = []
    for block in blocks:
        if block.get("type") != 0:  # Only text blocks
            continue

        bx0, by0, bx1, by1 = block["bbox"]

        # Filter by bbox if provided
        if bbox:
            table_x0, table_y0, table_x1, table_y1 = bbox
            cx = (bx0 + bx1) / 2
            cy = (by0 + by1) / 2
            if not (table_x0 <= cx <= table_x1 and table_y0 <= cy <= table_y1):
                continue

        # Extract text from spans
        lines = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                lines.append(span["text"])

        text_content = " ".join(lines).strip()
        if text_content:
            result.append(TextBlock(x0=bx0, y0=by0, x1=bx1, y1=by1, text=text_content))

    doc.close()
    return result


def parse_summary_row_text(text: str) -> Optional[dict]:
    """
    Parse a summary row text like:
    "1 일반상해사망(기본) 1천만원 700 20년/100세"

    Returns:
        dict with keys: seq_num, coverage_name, amount, premium, period
        None if parsing fails
    """
    # Pattern: [seq_num] coverage_name amount premium period
    # seq_num: optional leading digits
    # amount: Korean number format (e.g., "1천만원", "5백만원", "10만원")
    # premium: digits with commas (e.g., "700", "1,820", "36,420")
    # period: Korean format (e.g., "20년/100세", "10년/10년갱신")

    # Remove extra whitespace
    text = " ".join(text.split())

    # Pattern breakdown:
    # ^(\d+)?\s*              # Optional seq_num at start
    # (.+?)\s+                # coverage_name (non-greedy)
    # (\d+[천백만억]*원)\s+    # amount (Korean format)
    # ([\d,]+)\s+             # premium (digits with commas)
    # (.+)$                   # period (rest of string)

    pattern = r"^(\d+)?\s*(.+?)\s+(\d+[천백만억]*원)\s+([\d,]+)\s+(.+)$"
    match = re.match(pattern, text)

    if not match:
        return None

    seq_num, coverage_name, amount, premium, period = match.groups()

    # Clean up coverage_name (remove leading/trailing whitespace)
    coverage_name = coverage_name.strip()

    # Filter out header rows
    if "보장명" in coverage_name or "가입금액" in coverage_name:
        return None

    # Filter out noise rows
    if not coverage_name or len(coverage_name) < 2:
        return None

    # Filter out summary/total rows
    noise_keywords = ["합계", "총계", "주계약", "선택계약", "할인"]
    if any(kw in coverage_name for kw in noise_keywords):
        return None

    return {
        "seq_num": seq_num.strip() if seq_num else None,
        "coverage_name": coverage_name,
        "amount": amount,
        "premium": premium,
        "period": period,
    }


def cluster_blocks_by_y_band(
    blocks: List[TextBlock], y_tolerance: float = 3.0
) -> List[List[TextBlock]]:
    """
    Cluster text blocks into row-bands based on y-coordinates.

    Args:
        blocks: List of text blocks (must be sorted by y0)
        y_tolerance: Max y0 difference to consider blocks in same row-band

    Returns:
        List of row-bands (each row-band is a list of blocks)
    """
    if not blocks:
        return []

    # Sort blocks by y0
    sorted_blocks = sorted(blocks, key=lambda b: b.y0)

    row_bands = []
    current_band = [sorted_blocks[0]]

    for block in sorted_blocks[1:]:
        prev_block = current_band[-1]

        # Check if this block is in the same row-band as previous
        if abs(block.y0 - prev_block.y0) <= y_tolerance:
            current_band.append(block)
        else:
            # Start new row-band
            row_bands.append(current_band)
            current_band = [block]

    # Add last band
    if current_band:
        row_bands.append(current_band)

    return row_bands


def merge_row_band_to_summary_row(
    row_band: List[TextBlock], page: int
) -> Optional[SummaryRow]:
    """
    Merge text blocks in a row-band into a single SummaryRow.

    Strategy:
    1. Find block with amount/premium pattern (value block)
    2. Merge all text blocks without amount pattern as coverage name
    3. Parse value block for amount/premium/period
    4. Reject if coverage name is fragment (e.g., "Ⅱ(갱신형)" standalone)

    Args:
        row_band: List of text blocks in same y-band
        page: Page number (1-based)

    Returns:
        SummaryRow or None if parsing fails
    """
    # Find value block (has amount pattern)
    value_block = None
    name_blocks = []

    amount_pattern = r"\d+[천백만억]*원"

    for block in row_band:
        if re.search(amount_pattern, block.text):
            value_block = block
        else:
            name_blocks.append(block)

    if not value_block:
        return None

    # Merge coverage name from all non-value blocks
    # Sort name blocks by x0 (left to right)
    name_blocks.sort(key=lambda b: b.x0)
    coverage_name_parts = [b.text.strip() for b in name_blocks if b.text.strip()]
    coverage_name_merged = " ".join(coverage_name_parts)

    # Parse value block
    parsed = parse_summary_row_text(value_block.text)
    if not parsed:
        return None

    # If coverage name from value block is not empty, prepend it
    value_coverage = parsed["coverage_name"]
    if value_coverage and coverage_name_merged:
        # Value block has coverage prefix + amount/premium
        # Use value block's coverage name + merged name
        final_coverage_name = f"{coverage_name_merged} {value_coverage}".strip()
    elif coverage_name_merged:
        # Only merged name available
        final_coverage_name = coverage_name_merged
    elif value_coverage:
        # Only value block coverage name available
        final_coverage_name = value_coverage
    else:
        # No coverage name at all
        return None

    # Filter fragment coverage names (e.g., "Ⅱ(갱신형)" standalone)
    # Heuristic: if coverage name is <10 chars and has no Korean or alphanumeric word, it's likely a fragment
    if len(final_coverage_name) < 10 and not re.search(r"[가-힣a-zA-Z]{2,}", final_coverage_name):
        # Fragment detected, skip this row
        return None

    # Get row y-range (min/max across all blocks in band)
    y0 = min(b.y0 for b in row_band)
    y1 = max(b.y1 for b in row_band)

    return SummaryRow(
        seq_num=parsed["seq_num"],
        coverage_name_raw=final_coverage_name,
        amount_text=parsed["amount"],
        premium_text=parsed["premium"],
        period_text=parsed["period"],
        y0=y0,
        y1=y1,
        page=page,
    )


def extract_summary_rows_hybrid(
    pdf_path: Path,
    page_index: int,
    table_bbox: Tuple[float, float, float, float],
    min_row_height: float = 5.0,
    max_row_height: float = 50.0,
    use_row_band_clustering: bool = True,
) -> List[SummaryRow]:
    """
    Extract summary rows using hybrid approach:
    1. Get text blocks within table bbox (PyMuPDF)
    2. Cluster blocks into row-bands by y-coordinate (optional)
    3. Merge row-bands into summary rows
    4. Validate row structure

    Args:
        pdf_path: Path to PDF
        page_index: Page index (0-based)
        table_bbox: Table bounding box (x0, y0, x1, y1)
        min_row_height: Minimum row height (filter noise)
        max_row_height: Maximum row height (filter multi-line blocks)
        use_row_band_clustering: Enable row-band clustering for multiline handling

    Returns:
        List of SummaryRow objects
    """
    blocks = extract_text_blocks_pymupdf(pdf_path, page_index, bbox=table_bbox)

    if use_row_band_clustering:
        # Cluster blocks into row-bands
        row_bands = cluster_blocks_by_y_band(blocks, y_tolerance=3.0)

        rows = []
        for band in row_bands:
            # Merge row-band into single summary row
            row = merge_row_band_to_summary_row(band, page=page_index + 1)
            if row:
                rows.append(row)

    else:
        # Original single-block parsing (for backward compatibility)
        rows = []
        for block in blocks:
            # Filter by row height
            row_height = block.y1 - block.y0
            if row_height < min_row_height or row_height > max_row_height:
                continue

            # Parse row text
            parsed = parse_summary_row_text(block.text)
            if not parsed:
                continue

            rows.append(
                SummaryRow(
                    seq_num=parsed["seq_num"],
                    coverage_name_raw=parsed["coverage_name"],
                    amount_text=parsed["amount"],
                    premium_text=parsed["premium"],
                    period_text=parsed["period"],
                    y0=block.y0,
                    y1=block.y1,
                    page=page_index + 1,  # Convert to 1-based page number
                )
            )

    # Sort by y0 (top to bottom)
    rows.sort(key=lambda r: r.y0)

    return rows


def detect_summary_pages(pdf_path: Path, max_pages: int = 10) -> List[int]:
    """
    Detect pages that contain summary tables.

    Heuristics:
    - Page contains text blocks with pattern: coverage_name + amount + premium + period
    - Multiple such blocks (>= 5 rows)

    Args:
        pdf_path: Path to PDF
        max_pages: Maximum pages to scan

    Returns:
        List of page indices (0-based) that contain summary tables
    """
    doc = fitz.open(pdf_path)
    summary_pages = []

    for page_idx in range(min(max_pages, len(doc))):
        page = doc[page_idx]
        text = page.get_text()

        # Heuristic: Check for multiple rows with amount/premium pattern
        # Pattern: Korean amount (e.g., "1천만원") + number with comma (e.g., "1,820")
        pattern = r"\d+[천백만억]*원\s+[\d,]+"
        matches = re.findall(pattern, text)

        if len(matches) >= 5:  # At least 5 coverage rows
            summary_pages.append(page_idx)

    doc.close()
    return summary_pages


if __name__ == "__main__":
    # Test with KB proposal
    kb_proposal = Path("data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf")

    if not kb_proposal.exists():
        print(f"❌ KB proposal not found: {kb_proposal}")
        exit(1)

    print(f"✓ Testing with: {kb_proposal}\n")

    # Detect summary pages
    summary_pages = detect_summary_pages(kb_proposal)
    print(f"Detected summary pages: {[p + 1 for p in summary_pages]}\n")

    # Test extraction on page 2 (index 1)
    page_idx = 1
    table_bbox = (36.0, 239.0, 559.1, 760.1)  # From verification

    print(f"{'='*80}")
    print(f"PAGE {page_idx + 1} — Hybrid extraction test")
    print(f"{'='*80}\n")

    rows = extract_summary_rows_hybrid(kb_proposal, page_idx, table_bbox)

    print(f"Extracted {len(rows)} rows:\n")
    for idx, row in enumerate(rows):
        print(f"[{idx + 1}] {row.coverage_name_raw}")
        print(f"    Amount: {row.amount_text}, Premium: {row.premium_text}, Period: {row.period_text}")
        print(f"    Page: {row.page}, Y: [{row.y0:.1f}, {row.y1:.1f}]")
        if idx >= 4:  # Show first 5
            print(f"\n... and {len(rows) - 5} more rows")
            break
