#!/usr/bin/env python3
"""
STEP NEXT-45-C-β: P0-1 — KB layout verification
Examine KB proposal pages 2-3 to verify:
1. Table bbox (amount/premium columns)
2. Left text blocks (coverage names)
3. Y-coordinate join feasibility
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path


def verify_kb_layout():
    kb_proposal = Path("data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf")

    if not kb_proposal.exists():
        print(f"❌ KB proposal not found: {kb_proposal}")
        return

    print(f"✓ KB proposal: {kb_proposal}\n")

    # Pages to examine (0-indexed: page 2-3 = index 1-2)
    for page_idx in [1, 2]:
        print(f"\n{'='*80}")
        print(f"PAGE {page_idx + 1}")
        print(f"{'='*80}\n")

        # (A) pdfplumber: extract tables
        print(f"--- [A] pdfplumber tables ---")
        with pdfplumber.open(kb_proposal) as pdf:
            page = pdf.pages[page_idx]
            tables = page.extract_tables()

            if not tables:
                print(f"  No tables found on page {page_idx + 1}")
            else:
                for t_idx, table in enumerate(tables):
                    print(f"\n  Table {t_idx + 1}:")
                    print(f"    Rows: {len(table)}")
                    print(f"    Columns: {len(table[0]) if table else 0}")

                    # Show first 3 rows
                    for r_idx, row in enumerate(table[:3]):
                        print(f"    Row {r_idx}: {row}")

                    # Try to find table bbox
                    table_settings = page.find_tables()[t_idx] if page.find_tables() else None
                    if table_settings:
                        bbox = table_settings.bbox
                        print(f"    Table bbox: x0={bbox[0]:.1f}, y0={bbox[1]:.1f}, x1={bbox[2]:.1f}, y1={bbox[3]:.1f}")

        # (B) PyMuPDF: extract text blocks
        print(f"\n--- [B] PyMuPDF text blocks ---")
        doc = fitz.open(kb_proposal)
        page_fitz = doc[page_idx]
        blocks = page_fitz.get_text("blocks")

        # Filter blocks on left side (x0 < 200 as initial heuristic)
        left_blocks = [b for b in blocks if b[0] < 200]  # b[0] = x0

        print(f"  Total blocks: {len(blocks)}")
        print(f"  Left blocks (x0 < 200): {len(left_blocks)}\n")

        for b_idx, block in enumerate(left_blocks[:10]):  # Show first 10
            x0, y0, x1, y1, text, block_no, block_type = block
            text_clean = text.strip().replace('\n', ' ')[:60]
            print(f"  [{b_idx}] x0={x0:6.1f} y0={y0:6.1f} x1={x1:6.1f} y1={y1:6.1f} | {text_clean}")

        doc.close()

        # (C) Coordinate join feasibility
        print(f"\n--- [C] Join feasibility ---")
        with pdfplumber.open(kb_proposal) as pdf:
            page_plumber = pdf.pages[page_idx]
            tables_info = page_plumber.find_tables()

            if not tables_info:
                print("  No table metadata available")
                continue

            # Assume first table is summary
            table_bbox = tables_info[0].bbox
            t_x0, t_y0, t_x1, t_y1 = table_bbox

            print(f"  Table bbox: x0={t_x0:.1f}, y0={t_y0:.1f}, x1={t_x1:.1f}, y1={t_y1:.1f}")

            # Extract table rows with y-ranges
            table_data = page_plumber.extract_tables()[0]
            if not table_data:
                print("  Table data empty")
                continue

            # Get row y-ranges (approximate via table height / row count)
            row_count = len(table_data)
            row_height = (t_y1 - t_y0) / max(row_count, 1)

            print(f"  Estimated row height: {row_height:.1f}pt")
            print(f"\n  Sample row y-ranges (first 5 rows):")

            for r_idx in range(min(5, row_count)):
                row_y0 = t_y0 + r_idx * row_height
                row_y1 = row_y0 + row_height
                row_center = (row_y0 + row_y1) / 2

                # Find matching left blocks
                doc_fitz = fitz.open(kb_proposal)
                page_fitz = doc_fitz[page_idx]
                blocks_fitz = page_fitz.get_text("blocks")
                doc_fitz.close()

                matching = []
                for block in blocks_fitz:
                    bx0, by0, bx1, by1, btext, _, _ = block
                    if bx1 < t_x0 + 10:  # Left of table
                        b_center = (by0 + by1) / 2
                        if row_y0 <= b_center <= row_y1:
                            matching.append((btext.strip().replace('\n', ' ')[:40], by0, by1))

                print(f"    Row {r_idx}: y=[{row_y0:.1f}, {row_y1:.1f}] center={row_center:.1f}")
                if matching:
                    for match_text, match_y0, match_y1 in matching:
                        print(f"      → Match: y=[{match_y0:.1f}, {match_y1:.1f}] | {match_text}")
                else:
                    print(f"      → No left block match")


if __name__ == "__main__":
    verify_kb_layout()
