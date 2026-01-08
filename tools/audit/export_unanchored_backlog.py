"""
STEP NEXT-71: Export Unanchored Backlog with A/B Classification

Generate:
1. Full CSV of all unanchored coverages (62 rows)
2. Sample of 20 rows for documentation
3. A/B classification:
   - (A) Mapping/Excel gap: Step2-b also has no coverage_code
   - (B) Pipeline drop/carry-through bug: Step2-b has code but Step4 doesn't

Seed-based deterministic sampling for reproducibility.
"""

import json
import csv
import random
from pathlib import Path
from typing import List, Dict


class UnanchoredBacklogExporter:
    """Export unanchored coverage backlog with A/B classification"""

    INSURERS = [
        "samsung", "hanwha", "heungkuk", "hyundai", "kb", "meritz",
        "db_over41", "db_under40", "lotte_female", "lotte_male"
    ]

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.scope_dir = data_dir / "scope_v3"
        self.compare_file = data_dir / "compare_v1" / "compare_rows_v1.jsonl"

    def load_step2_mapping(self) -> Dict[str, Dict]:
        """
        Load Step2-b canonical data for all insurers.

        Returns:
            Dict[(insurer, coverage_name_raw), step2_row]
        """
        mapping = {}

        for insurer_file in self.INSURERS:
            step2_file = self.scope_dir / f"{insurer_file}_step2_canonical_scope_v1.jsonl"
            if not step2_file.exists():
                continue

            with open(step2_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    insurer_key = row.get('insurer_key', insurer_file)
                    coverage_name_raw = row.get('coverage_name_raw', '')

                    key = (insurer_key, coverage_name_raw)
                    mapping[key] = row

        return mapping

    def extract_unanchored_rows(self, step2_mapping: Dict) -> List[Dict]:
        """
        Extract all unanchored rows from compare_rows with A/B classification.

        Returns:
            List of classified unanchored rows
        """
        if not self.compare_file.exists():
            return []

        unanchored = []

        with open(self.compare_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                row = json.loads(line)

                # Filter: unanchored only
                if not row['meta']['unanchored']:
                    continue

                insurer_key = row['identity']['insurer_key']
                coverage_name_raw = row['identity']['coverage_name_raw']
                coverage_code_step4 = row['identity'].get('coverage_code')

                # Lookup Step2-b
                step2_key = (insurer_key, coverage_name_raw)
                step2_row = step2_mapping.get(step2_key, {})

                coverage_code_step2 = step2_row.get('coverage_code')
                coverage_name_normalized = step2_row.get('coverage_name_normalized', '')
                mapping_method = step2_row.get('mapping_method', '')
                drop_reason = step2_row.get('drop_reason')

                # A/B Classification
                if not coverage_code_step2:
                    classification = "A_MAPPING_GAP"
                    note = "No coverage_code in Step2-b canonical mapping"
                elif not coverage_code_step4:
                    classification = "B_PIPELINE_DROP"
                    note = "Step2-b has coverage_code but Step4 has null (carry-through bug)"
                else:
                    classification = "UNKNOWN"
                    note = "Unexpected: both have coverage_code but unanchored"

                unanchored_row = {
                    "insurer_key": insurer_key,
                    "product_key": row['identity']['product_key'],
                    "variant_key": row['identity']['variant_key'],
                    "coverage_name_raw": coverage_name_raw,
                    "coverage_name_normalized": coverage_name_normalized,
                    "coverage_code_step2": coverage_code_step2 or "",
                    "coverage_code_step4": coverage_code_step4 or "",
                    "mapping_method": mapping_method,
                    "step2b_has_code": "TRUE" if coverage_code_step2 else "FALSE",
                    "drop_reason": drop_reason or "",
                    "classification": classification,
                    "note": note
                }

                unanchored.append(unanchored_row)

        return unanchored

    def export_csv(self, rows: List[Dict], output_file: Path):
        """Export rows to CSV"""
        if not rows:
            print(f"No rows to export")
            return

        fieldnames = [
            "insurer_key", "product_key", "variant_key",
            "coverage_name_raw", "coverage_name_normalized",
            "coverage_code_step2", "coverage_code_step4",
            "mapping_method", "step2b_has_code", "drop_reason",
            "classification", "note"
        ]

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"✅ Exported {len(rows)} rows to {output_file}")

    def print_sample(self, rows: List[Dict], sample_size: int = 20):
        """Print markdown table of sample rows"""
        # Deterministic sampling (seed-based)
        random.seed(42)
        sample = rows[:sample_size] if len(rows) <= sample_size else random.sample(rows, sample_size)

        print(f"\n## Unanchored Backlog Sample (n={len(sample)})")
        print()
        print("| # | Class | Insurer | Coverage Name | Step2 Code | Classification |")
        print("|---|-------|---------|---------------|------------|----------------|")

        for i, row in enumerate(sample, 1):
            cls = row['classification'].replace('_', ' ')
            name = row['coverage_name_raw'][:50]
            step2_code = row['coverage_code_step2'] or "NULL"

            print(f"| {i} | **{cls}** | {row['insurer_key']} | {name} | {step2_code} | {row['note'][:40]} |")

        print()

    def print_summary(self, rows: List[Dict]):
        """Print classification summary"""
        a_count = sum(1 for r in rows if r['classification'] == 'A_MAPPING_GAP')
        b_count = sum(1 for r in rows if r['classification'] == 'B_PIPELINE_DROP')
        other_count = sum(1 for r in rows if r['classification'] not in ['A_MAPPING_GAP', 'B_PIPELINE_DROP'])

        total = len(rows)

        print(f"\n## Classification Summary")
        print(f"- Total unanchored: {total}")
        print(f"- **(A) Mapping/Excel gap**: {a_count} / {total} ({a_count/total*100:.1f}%)")
        print(f"- **(B) Pipeline drop/bug**: {b_count} / {total} ({b_count/total*100:.1f}%)")
        print(f"- **(?) Other**: {other_count} / {total}")
        print()

        if b_count > 0:
            print("⚠️ WARNING: Found pipeline drop/carry-through bugs (type B)")
            print("   These are P0 bugs requiring immediate fix")
        else:
            print("✅ No pipeline bugs detected")
            print("   All unanchored coverages are legitimate mapping gaps")
            print("   → Remaining work is mapping backlog (Excel updates)")


def main():
    project_root = Path(__file__).parent.parent.parent
    exporter = UnanchoredBacklogExporter(project_root / "data")

    print("[Unanchored Backlog Export]")
    print("=" * 80)
    print()

    # Load Step2-b mapping
    print("Loading Step2-b canonical mapping...")
    step2_mapping = exporter.load_step2_mapping()
    print(f"  Loaded {len(step2_mapping)} coverage mappings")
    print()

    # Extract unanchored rows
    print("Extracting unanchored rows from compare_rows...")
    unanchored = exporter.extract_unanchored_rows(step2_mapping)
    print(f"  Found {len(unanchored)} unanchored coverages")
    print()

    # Export full CSV
    output_csv = project_root / "docs" / "audit" / "unanchored_backlog_v1.csv"
    exporter.export_csv(unanchored, output_csv)

    # Print sample
    exporter.print_sample(unanchored, sample_size=20)

    # Print summary
    exporter.print_summary(unanchored)


if __name__ == "__main__":
    main()
