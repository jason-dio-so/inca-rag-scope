"""
STEP NEXT-44-Δ: PDF Structure Scanner (NO EXTRACTION)

Scan PDF table structure WITHOUT extracting values.
Output: Raw structural metadata (pages, headers, table characteristics).

⚠️ CRITICAL: This script MUST NOT extract coverage names, amounts, or any values.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


def scan_pdf_structure(pdf_path: Path, insurer: str) -> Dict[str, Any]:
    """
    Scan PDF structure for table layout analysis

    Returns structural metadata ONLY (no value extraction)
    """
    structure = {
        "insurer": insurer,
        "pdf_path": str(pdf_path),
        "total_pages": 0,
        "pages_with_tables": [],
        "table_snapshots": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        structure["total_pages"] = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            if not tables:
                continue

            structure["pages_with_tables"].append(page_num)

            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue

                # Capture header rows (raw text, no interpretation)
                header_rows = []
                for row_idx in range(min(3, len(table))):  # First 3 rows
                    header_row = [str(cell) if cell else "" for cell in table[row_idx]]
                    header_rows.append(header_row)

                # Detect keyword presence (structure only, not extraction)
                header_text = ' '.join(str(cell) for row in header_rows for cell in row if cell)
                header_normalized = header_text.replace(' ', '').replace('\n', '')

                has_coverage_keyword = any(kw in header_normalized for kw in ['담보', '보장', '가입담보'])
                has_amount_keyword = '보험료' in header_text or '가입금액' in header_text
                has_period_keyword = '납입' in header_text or '만기' in header_text

                # Record structural snapshot
                snapshot = {
                    "page": page_num,
                    "table_index": table_idx,
                    "row_count": len(table),
                    "col_count": len(table[0]) if table else 0,
                    "header_rows_raw": header_rows,
                    "header_text_raw": header_text,
                    "keywords_detected": {
                        "has_coverage_keyword": has_coverage_keyword,
                        "has_amount_keyword": has_amount_keyword,
                        "has_period_keyword": has_period_keyword
                    },
                    "evidence": {
                        "page": page_num,
                        "snippet": header_text[:200]  # First 200 chars
                    }
                }

                structure["table_snapshots"].append(snapshot)

    return structure


def main():
    """Scan all 8 insurer PDFs"""

    pdf_sources = Path(__file__).parent.parent.parent / "data" / "sources" / "insurers"

    pdf_map = {
        "samsung": "samsung/가입설계서/삼성_가입설계서_2511.pdf",
        "meritz": "meritz/가입설계서/메리츠_가입설계서_2511.pdf",
        "kb": "kb/가입설계서/KB_가입설계서.pdf",
        "hanwha": "hanwha/가입설계서/한화_가입설계서_2511.pdf",
        "hyundai": "hyundai/가입설계서/현대_가입설계서_2511.pdf",
        "lotte": "lotte/가입설계서/롯데_가입설계서(남)_2511.pdf",
        "heungkuk": "heungkuk/가입설계서/흥국_가입설계서_2511.pdf",
        "db": "db/가입설계서/DB_가입설계서(40세이하)_2511.pdf"
    }

    output_dir = Path(__file__).parent.parent.parent / "data" / "profile"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*80)
    print("STEP NEXT-44-Δ: PDF Structure Scanner")
    print("="*80 + "\n")

    for insurer, pdf_filename in pdf_map.items():
        pdf_path = pdf_sources / pdf_filename

        if not pdf_path.exists():
            print(f"⚠️  {insurer}: PDF not found - {pdf_path}")
            continue

        print(f"📄 {insurer}: Scanning structure...")
        structure = scan_pdf_structure(pdf_path, insurer)

        # Save raw structure scan
        output_path = output_dir / f"{insurer}_structure_scan.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        print(f"   ✓ Pages: {structure['total_pages']}, Tables found: {len(structure['table_snapshots'])}")
        print(f"   ✓ Pages with tables: {structure['pages_with_tables']}")
        print(f"   ✓ Output: {output_path}\n")

    print("="*80)
    print("✅ Structure scan complete (NO extraction performed)")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
