#!/usr/bin/env python3
"""
STEP NEXT-45-C-β: P0-1 refined — KB layout verification v2
Focus on Table 4 (page 2) and Table 1 (page 3) - the main summary tables
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path


def verify_kb_summary_table():
    kb_proposal = Path("data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf")

    if not kb_proposal.exists():
        print(f"❌ KB proposal not found: {kb_proposal}")
        return

    print(f"✓ KB proposal: {kb_proposal}\n")

    # Page 2, Table 4 is the main summary (index 1, table index 3)
    page_idx = 1
    target_table_idx = 3

    print(f"{'='*80}")
    print(f"PAGE {page_idx + 1} — Table {target_table_idx + 1} (main summary)")
    print(f"{'='*80}\n")

    with pdfplumber.open(kb_proposal) as pdf:
        page = pdf.pages[page_idx]
        tables = page.extract_tables()

        if len(tables) <= target_table_idx:
            print(f"❌ Table {target_table_idx + 1} not found")
            return

        table_data = tables[target_table_idx]
        print(f"Table has {len(table_data)} rows\n")

        # Show all rows
        print("--- Table content (all rows) ---")
        for r_idx, row in enumerate(table_data):
            # Clean up None values
            row_clean = [str(cell) if cell is not None else "" for cell in row]
            print(f"Row {r_idx:2d}: {row_clean}")

        # Table bbox
        table_obj = page.find_tables()[target_table_idx]
        bbox = table_obj.bbox
        print(f"\nTable bbox: x0={bbox[0]:.1f}, y0={bbox[1]:.1f}, x1={bbox[2]:.1f}, y1={bbox[3]:.1f}")

        # Column structure analysis
        print(f"\n--- Column structure ---")
        if len(table_data) > 0:
            header = table_data[0]
            print(f"Header row: {header}")
            print(f"Column count: {len(header)}")

            # Check if first data row has pattern: [seq_num, coverage_name, amount, premium, period]
            if len(table_data) > 1:
                sample_row = table_data[1]
                print(f"\nSample data row (row 1): {sample_row}")

                # Hypothesis: coverage names ARE in the table, but pdfplumber returns them as None
                # Let's check PyMuPDF for the same region

    print(f"\n--- PyMuPDF text extraction (same region) ---")
    doc = fitz.open(kb_proposal)
    page_fitz = doc[page_idx]

    # Extract text with position
    text_dict = page_fitz.get_text("dict")
    blocks = text_dict["blocks"]

    # Filter blocks within table bbox (y: 239.0 - 760.1, x: 36.0 - 559.1)
    table_y0, table_y1 = 239.0, 760.1
    table_x0, table_x1 = 36.0, 559.1

    print(f"Blocks within table bbox:")
    count = 0
    for block in blocks:
        if block.get("type") == 0:  # Text block
            bbox_b = block["bbox"]
            bx0, by0, bx1, by1 = bbox_b

            # Check if center is within table
            cx = (bx0 + bx1) / 2
            cy = (by0 + by1) / 2

            if table_x0 <= cx <= table_x1 and table_y0 <= cy <= table_y1:
                # Extract text
                lines = []
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        lines.append(span["text"])
                text_content = " ".join(lines).strip()

                if text_content:
                    print(f"  y=[{by0:6.1f}, {by1:6.1f}] x=[{bx0:6.1f}, {bx1:6.1f}] | {text_content[:80]}")
                    count += 1
                    if count >= 20:  # Limit output
                        break

    doc.close()

    # Now check page 3, table 1
    print(f"\n\n{'='*80}")
    print(f"PAGE 3 — Table 1 (continuation)")
    print(f"{'='*80}\n")

    page_idx = 2
    target_table_idx = 0

    with pdfplumber.open(kb_proposal) as pdf:
        page = pdf.pages[page_idx]
        tables = page.extract_tables()

        if len(tables) <= target_table_idx:
            print(f"❌ Table {target_table_idx + 1} not found")
            return

        table_data = tables[target_table_idx]
        print(f"Table has {len(table_data)} rows\n")

        # Show all rows
        print("--- Table content (first 10 rows) ---")
        for r_idx, row in enumerate(table_data[:10]):
            row_clean = [str(cell) if cell is not None else "" for cell in row]
            print(f"Row {r_idx:2d}: {row_clean}")


if __name__ == "__main__":
    verify_kb_summary_table()
