"""
STEP NEXT-45-C-β-4 P0-3: Pass B Page Diagnosis Script

Diagnose why specific pages (Hanwha p4, Lotte p3) are not being detected by Pass B.
Outputs detailed pattern scores for each table candidate on the page.
"""

import re
import sys
from pathlib import Path
from typing import List, Any

import pdfplumber


def diagnose_page(pdf_path: Path, page_no: int):
    """
    Diagnose Pass B detection for a specific page

    Args:
        pdf_path: Path to PDF
        page_no: 1-indexed page number
    """
    print(f"\n{'='*80}")
    print(f"Pass B Page Diagnosis: {pdf_path.name} - Page {page_no}")
    print(f"{'='*80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        if page_no < 1 or page_no > len(pdf.pages):
            print(f"❌ Invalid page number: {page_no} (PDF has {len(pdf.pages)} pages)")
            return

        page = pdf.pages[page_no - 1]
        tables = page.extract_tables()

        print(f"📄 Page {page_no}: Found {len(tables)} tables\n")

        if not tables:
            print("❌ No tables found on this page")
            return

        # Pattern definitions (same as Pass B detection)
        amt_pattern = re.compile(r'\d{1,3}(,\d{3})*\s*원|\d+\s*만원|\d+\s*천만원|\d+\s*억원')
        prem_period_pattern = re.compile(r'\d+\s*년|세\s*만기|갱신|납입|보험료|\d{1,3}(,\d{3})+')
        korean_pattern = re.compile(r'[가-힣]{2,}')
        clause_pattern = re.compile(r'경우|시|합니다|됩니다|진단 확정|보장개시일|면책|지급사유')

        # Analyze each table
        for table_idx, table in enumerate(tables):
            print(f"{'─'*80}")
            print(f"Table {table_idx} (rows: {len(table)}, cols: {len(table[0]) if table else 0})")
            print(f"{'─'*80}")

            if len(table) < 7:
                print(f"⚠️  Row count {len(table)} < 7 (Pass B minimum threshold)")
                print()
                continue

            # Skip header rows (first 3)
            data_rows = table[3:] if len(table) > 3 else table
            sample_rows = data_rows[:min(20, len(data_rows))]

            if not sample_rows:
                print("⚠️  No data rows after skipping header")
                print()
                continue

            # Determine column count
            col_counts = [len(row) for row in sample_rows if row]
            col_count = max(set(col_counts), key=col_counts.count) if col_counts else 0

            if col_count == 0:
                print("⚠️  Could not determine column count")
                print()
                continue

            # Initialize column scores
            amt_score = [0.0] * col_count
            prem_period_score = [0.0] * col_count
            korean_score = [0.0] * col_count
            clause_score = [0.0] * col_count

            # Analyze each column
            for row in sample_rows:
                for j in range(min(len(row), col_count)):
                    cell = str(row[j]).strip() if row[j] else ''

                    if not cell:
                        continue

                    # Amount score
                    if amt_pattern.search(cell):
                        amt_score[j] += 1

                    # Premium/period score
                    if prem_period_pattern.search(cell):
                        prem_period_score[j] += 1

                    # Korean text score (first 2 columns only for coverage name)
                    if j < 2:
                        korean_chars = len(korean_pattern.findall(cell))
                        if korean_chars > 0:
                            korean_score[j] += korean_chars / 10.0

                    # Clause score
                    if clause_pattern.search(cell):
                        clause_score[j] += 1

            # Normalize scores
            num_rows = len(sample_rows)
            amt_ratio = [s / num_rows for s in amt_score]
            prem_period_ratio = [s / num_rows for s in prem_period_score]
            korean_ratio = [s / num_rows for s in korean_score]
            clause_ratio_total = sum(clause_score) / (num_rows * col_count) if (num_rows * col_count) > 0 else 0

            # Calculate max scores
            max_amt = max(amt_ratio) if amt_ratio else 0
            max_prem_period = max(prem_period_ratio) if prem_period_ratio else 0
            max_korean = max(korean_ratio) if korean_ratio else 0

            # Pass B decision criteria (STEP NEXT-45-C-β-4 P0-3 adjusted thresholds)
            is_summary_like = (
                max_amt >= 0.25 and
                max_prem_period >= 0.20 and
                max_korean >= 0.20 and
                clause_ratio_total < 0.35
            )

            # Display results
            print(f"Sampled {num_rows} data rows (from {len(data_rows)} total)")
            print()
            print("Pattern Scores (max across columns):")
            print(f"  Amount ratio:        {max_amt:.2f} {'✅' if max_amt >= 0.25 else '❌'} (threshold: ≥0.25)")
            print(f"  Premium/Period ratio: {max_prem_period:.2f} {'✅' if max_prem_period >= 0.20 else '❌'} (threshold: ≥0.20)")
            print(f"  Korean text ratio:    {max_korean:.2f} {'✅' if max_korean >= 0.20 else '❌'} (threshold: ≥0.20)")
            print(f"  Clause ratio:         {clause_ratio_total:.2f} {'✅' if clause_ratio_total < 0.35 else '❌'} (threshold: <0.35)")
            print()
            print(f"Pass B Detection: {'✅ PASS' if is_summary_like else '❌ FAIL'}")
            print()

            # Show per-column breakdown
            print("Per-Column Scores:")
            print(f"  {'Col':>4} {'Amt':>6} {'Prem/Pd':>8} {'Korean':>8} {'Clause':>8}")
            print(f"  {'-'*4} {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
            for j in range(col_count):
                print(
                    f"  {j:>4} {amt_ratio[j]:>6.2f} {prem_period_ratio[j]:>8.2f} "
                    f"{korean_ratio[j]:>8.2f} {clause_score[j]:>8.0f}"
                )
            print()

            # Show sample rows
            print("Sample Rows (first 5):")
            for i, row in enumerate(sample_rows[:5]):
                row_text = ' | '.join(str(cell) if cell else '' for cell in row[:col_count])
                print(f"  [{i}] {row_text[:120]}")
            print()

    print(f"{'='*80}\n")


def main():
    """Main diagnosis script"""
    if len(sys.argv) < 3:
        print("Usage: python diagnose_passB_page.py <insurer> <page_no>")
        print("\nExample:")
        print("  python diagnose_passB_page.py hanwha 4")
        print("  python diagnose_passB_page.py lotte 3")
        sys.exit(1)

    insurer = sys.argv[1].lower()
    page_no = int(sys.argv[2])

    # PDF map
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

    if insurer not in pdf_map:
        print(f"❌ Unknown insurer: {insurer}")
        print(f"Available: {', '.join(pdf_map.keys())}")
        sys.exit(1)

    pdf_path = pdf_sources / pdf_map[insurer]

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)

    diagnose_page(pdf_path, page_no)


if __name__ == '__main__':
    main()
