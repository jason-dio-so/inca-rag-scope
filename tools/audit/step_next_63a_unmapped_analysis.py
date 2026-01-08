"""
STEP NEXT-63-A: Unmapped Analysis (Constitution-Compliant)

PURPOSE:
Classify all unmapped rows from Step2-b mapping_report across ALL insurers into:
1. Excel-hit unmapped → pipeline bug (term exists in Excel but wasn't matched)
2. Excel-miss unmapped → mapping gap (term doesn't exist in Excel)

RULES (ACTIVE_CONSTITUTION.md §7.2):
- ❌ NO automatic fixing
- ✅ Classification = ANALYSIS ONLY
- ✅ All counts = line-based (SSOT)
- ✅ 4D identity preserved in output

OUTPUT:
- docs/audit/STEP_NEXT_63A_UNMAPPED_ANALYSIS.md
- data/scope_v3/{insurer}_step2_unmapped_diagnosis.json (per-insurer detail)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class UnmappedAnalyzer:
    """Analyze unmapped rows per ACTIVE_CONSTITUTION.md §7.2"""

    def __init__(self):
        self.scope_v3_dir = Path(__file__).parent.parent.parent / "data" / "scope_v3"
        self.mapping_xlsx = Path(__file__).parent.parent.parent / "data" / "sources" / "mapping" / "담보명mapping자료.xlsx"
        self.output_dir = Path(__file__).parent.parent.parent / "docs" / "audit"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load Excel mapping reference (SSOT per constitution §1.2)
        self.excel_terms = self._load_excel_terms()

    def _load_excel_terms(self) -> Dict[str, set]:
        """Load all coverage terms from Excel mapping file (per-insurer)"""
        logger.info(f"Loading Excel mapping reference: {self.mapping_xlsx}")

        df = pd.read_excel(self.mapping_xlsx, sheet_name='Sheet1')

        # Extract per-insurer terms
        excel_terms = {}
        insurer_columns = [col for col in df.columns if col not in ['통일코드', '대분류', '중분류', '소분류', '담보명(통일)']]

        for col in insurer_columns:
            # Normalize column name to insurer_key (lowercase)
            insurer_key = col.lower().strip()
            terms = set(df[col].dropna().astype(str).str.strip())
            excel_terms[insurer_key] = terms
            logger.info(f"  {insurer_key}: {len(terms)} terms")

        return excel_terms

    def analyze_insurer(self, insurer_key: str) -> Dict[str, Any]:
        """Analyze unmapped rows for single insurer"""
        mapping_report_path = self.scope_v3_dir / f"{insurer_key}_step2_mapping_report.jsonl"

        if not mapping_report_path.exists():
            logger.warning(f"Mapping report not found: {mapping_report_path}")
            return None

        # Load mapping report
        with open(mapping_report_path, 'r', encoding='utf-8') as f:
            rows = [json.loads(line) for line in f]

        # Filter unmapped rows (per constitution §6.3)
        unmapped = [r for r in rows if r.get('mapping_method') == 'unmapped']

        logger.info(f"{insurer_key}: {len(unmapped)}/{len(rows)} unmapped ({len(unmapped)/len(rows)*100:.1f}%)")

        if not unmapped:
            return {
                'insurer_key': insurer_key,
                'total_rows': len(rows),
                'unmapped_count': 0,
                'excel_hit_unmapped': [],
                'excel_miss_unmapped': [],
                'classification': {}
            }

        # Get Excel terms for this insurer
        excel_terms = self.excel_terms.get(insurer_key, set())

        # Classify unmapped
        excel_hit = []
        excel_miss = []

        for row in unmapped:
            coverage_name_normalized = row.get('coverage_name_normalized', '')
            coverage_name_raw = row.get('coverage_name_raw', '')

            # Check if term exists in Excel (exact match on normalized name)
            if coverage_name_normalized in excel_terms:
                # Excel-hit unmapped = pipeline bug (term exists but wasn't matched)
                excel_hit.append({
                    'coverage_name_raw': coverage_name_raw,
                    'coverage_name_normalized': coverage_name_normalized,
                    'product_key': row.get('product_key'),
                    'variant_key': row.get('variant_key'),
                    'diagnosis': 'PIPELINE_BUG',
                    'reason': 'Term exists in Excel but mapping logic failed'
                })
            else:
                # Excel-miss unmapped = mapping gap (term doesn't exist in Excel)
                excel_miss.append({
                    'coverage_name_raw': coverage_name_raw,
                    'coverage_name_normalized': coverage_name_normalized,
                    'product_key': row.get('product_key'),
                    'variant_key': row.get('variant_key'),
                    'diagnosis': 'MAPPING_GAP',
                    'reason': 'Term does not exist in Excel mapping reference'
                })

        result = {
            'insurer_key': insurer_key,
            'total_rows': len(rows),
            'unmapped_count': len(unmapped),
            'unmapped_rate': f"{len(unmapped)/len(rows)*100:.1f}%",
            'excel_hit_unmapped': excel_hit,
            'excel_hit_count': len(excel_hit),
            'excel_miss_unmapped': excel_miss,
            'excel_miss_count': len(excel_miss),
            'classification': {
                'PIPELINE_BUG': len(excel_hit),
                'MAPPING_GAP': len(excel_miss)
            }
        }

        # Save per-insurer diagnosis (constitution §2: 4D identity preserved)
        diagnosis_path = self.scope_v3_dir / f"{insurer_key}_step2_unmapped_diagnosis.json"
        with open(diagnosis_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"  Pipeline bugs: {len(excel_hit)}, Mapping gaps: {len(excel_miss)}")
        logger.info(f"  Diagnosis saved: {diagnosis_path}")

        return result

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate markdown audit report"""
        # Aggregate statistics
        total_rows = sum(r['total_rows'] for r in results)
        total_unmapped = sum(r['unmapped_count'] for r in results)
        total_bugs = sum(r['excel_hit_count'] for r in results)
        total_gaps = sum(r['excel_miss_count'] for r in results)

        report = f"""# STEP NEXT-63-A: Unmapped Analysis (Constitution-Compliant)

**Date**: 2026-01-08
**Scope**: ALL insurers (post STEP NEXT-63-PREP)
**Constitution**: ACTIVE_CONSTITUTION.md §7.2

## Executive Summary

- **Total rows**: {total_rows}
- **Unmapped rows**: {total_unmapped} ({total_unmapped/total_rows*100:.1f}%)
- **Classification**:
  - 🐛 **Pipeline bugs** (Excel-hit unmapped): {total_bugs} ({total_bugs/total_unmapped*100:.1f}% of unmapped)
  - 📋 **Mapping gaps** (Excel-miss unmapped): {total_gaps} ({total_gaps/total_unmapped*100:.1f}% of unmapped)

## Per-Insurer Breakdown

| Insurer | Total | Unmapped | Rate | Pipeline Bugs | Mapping Gaps |
|---------|-------|----------|------|---------------|--------------|
"""

        for r in sorted(results, key=lambda x: x['unmapped_count'], reverse=True):
            insurer = r['insurer_key']
            total = r['total_rows']
            unmapped = r['unmapped_count']
            rate = r['unmapped_rate']
            bugs = r['excel_hit_count']
            gaps = r['excel_miss_count']

            report += f"| {insurer:<12} | {total:>5} | {unmapped:>8} | {rate:>6} | {bugs:>13} | {gaps:>12} |\n"

        report += f"""
## Unmapped Classification (Constitution §7.2)

### 1. Excel-Hit Unmapped (Pipeline Bugs)

**Definition**: Terms that exist in `담보명mapping자료.xlsx` but were not matched by mapping logic.

**Root Cause**: Mapping logic bug (deterministic pattern matching failed).

**Action Required**: Fix mapping logic in `pipeline/step2_canonical_mapping/`.

**Count**: {total_bugs}

### 2. Excel-Miss Unmapped (Mapping Gaps)

**Definition**: Terms that do NOT exist in `담보명mapping자료.xlsx`.

**Root Cause**: Coverage not in canonical mapping reference.

**Action Required**: Update `담보명mapping자료.xlsx` with new coverage definitions.

**Count**: {total_gaps}

## Detail Files

Per-insurer diagnosis files (4D identity preserved):

"""

        for r in results:
            insurer = r['insurer_key']
            report += f"- `data/scope_v3/{insurer}_step2_unmapped_diagnosis.json`\n"

        report += f"""
## Constitution Compliance

✅ **§7.1**: All counts are line-based (SSOT)
✅ **§7.2**: Unmapped classification = ANALYSIS ONLY (NO automatic fixing)
✅ **§2**: 4D identity preserved in all outputs
✅ **§6.3**: Unmapped defined as `mapping_method == "unmapped"`

## Next Steps

1. **Fix pipeline bugs** ({total_bugs} rows):
   - Review mapping logic in `pipeline/step2_canonical_mapping/canonical_mapper.py`
   - Add missing normalization rules or exact match patterns
   - Re-run Step2-b for affected insurers

2. **Close mapping gaps** ({total_gaps} rows):
   - Review unmapped terms in diagnosis files
   - Update `담보명mapping자료.xlsx` with new canonical codes
   - Re-run Step2-b after Excel update

---

**Report Generated**: 2026-01-08
**Constitution Version**: ACTIVE_CONSTITUTION.md (2026-01-08)
"""

        return report


def main():
    """Run unmapped analysis for all insurers"""
    analyzer = UnmappedAnalyzer()

    # Get all insurers from scope_v3
    mapping_reports = list(analyzer.scope_v3_dir.glob("*_step2_mapping_report.jsonl"))
    insurers = sorted(set(f.stem.replace('_step2_mapping_report', '') for f in mapping_reports))

    logger.info(f"Analyzing {len(insurers)} insurers: {', '.join(insurers)}")

    results = []
    for insurer in insurers:
        result = analyzer.analyze_insurer(insurer)
        if result:
            results.append(result)

    # Generate report
    report = analyzer.generate_report(results)

    # Save report
    report_path = analyzer.output_dir / "STEP_NEXT_63A_UNMAPPED_ANALYSIS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"\n{'='*80}")
    logger.info(f"✅ STEP NEXT-63-A Analysis Complete")
    logger.info(f"{'='*80}")
    logger.info(f"Report: {report_path}")
    logger.info(f"Diagnosis files: data/scope_v3/*_step2_unmapped_diagnosis.json")
    logger.info(f"{'='*80}\n")

    # Print summary
    total_bugs = sum(r['excel_hit_count'] for r in results)
    total_gaps = sum(r['excel_miss_count'] for r in results)

    print("\n" + "="*80)
    print("UNMAPPED CLASSIFICATION SUMMARY")
    print("="*80)
    print(f"🐛 Pipeline Bugs (Excel-hit unmapped):  {total_bugs}")
    print(f"📋 Mapping Gaps (Excel-miss unmapped):  {total_gaps}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
