#!/usr/bin/env python3
"""Debug Samsung hybrid extraction"""

from pathlib import Path
import json
import pdfplumber
from pipeline.step1_summary_first.hybrid_layout import extract_summary_rows_hybrid

# Load Samsung profile
profile_path = Path("data/profile/samsung_proposal_profile_v3.json")
with open(profile_path) as f:
    profile = json.load(f)

pdf_path = Path("data/sources/insurers/samsung/가입설계서/삼성_가입설계서_2511.pdf")

signatures = profile["summary_table"]["table_signatures"]

print(f"Samsung has {len(signatures)} table signatures\n")

for idx, sig in enumerate(signatures):
    page = sig["page"]
    table_index = sig["table_index"]

    print(f"\n{'='*80}")
    print(f"Signature {idx + 1}: Page {page}, Table {table_index}")
    print(f"{'='*80}\n")

    # Get table bbox
    with pdfplumber.open(pdf_path) as pdf_obj:
        page_obj = pdf_obj.pages[page - 1]
        tables_info = page_obj.find_tables()

        if table_index >= len(tables_info):
            print(f"  ⚠️ Table index {table_index} out of range (total: {len(tables_info)})")
            continue

        table_bbox = tables_info[table_index].bbox
        print(f"  Table bbox: x0={table_bbox[0]:.1f}, y0={table_bbox[1]:.1f}, x1={table_bbox[2]:.1f}, y1={table_bbox[3]:.1f}")

        # Extract rows
        rows = extract_summary_rows_hybrid(pdf_path, page - 1, table_bbox)

        print(f"  Extracted {len(rows)} rows\n")

        for r_idx, row in enumerate(rows[:5]):
            print(f"    [{r_idx + 1}] {row.coverage_name_raw}")
            print(f"        Amount: {row.amount_text}, Premium: {row.premium_text}")
            print(f"        Period: {row.period_text}")

        if len(rows) > 5:
            print(f"\n    ... and {len(rows) - 5} more rows")
