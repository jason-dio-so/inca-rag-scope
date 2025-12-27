# How to Rerun Meritz Pipeline

## Overview

This document provides the golden CLI commands to reproduce the Meritz pipeline from scratch.

## Prerequisites

- Working directory: `inca-rag-scope/`
- Python environment with dependencies installed
- Source PDFs in `data/sources/insurers/meritz/`

## Pipeline Execution Order

### STEP 1: Scope Extraction

**Manual extraction required** - Extract coverage names from 가입설계서 to CSV.

**Output**:
- `data/scope/meritz_scope.csv`
- Format: `coverage_name_raw,insurer,source_page`
- Expected: 34 coverages (35 lines with header)

### STEP 2: Canonical Mapping

```bash
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer meritz
```

**Inputs**:
- `data/scope/meritz_scope.csv`
- `data/sources/mapping/담보명mapping자료.xlsx`

**Outputs** (creates/overwrites):
- `data/scope/meritz_scope_mapped.csv` (35 lines with header)
- `data/scope/meritz_unmatched_review.csv` (unmatched coverages for review)

**Expected Results**:
- Matched: 22
- Unmatched: 12
- Total: 34

### STEP 3: PDF Text Extraction

**Pre-step**: Create evidence manifest

```bash
# Create manifest (if not exists)
cat > data/evidence_sources/meritz_manifest.csv << 'EOF'
doc_type,file_path
약관,data/sources/insurers/meritz/약관/메리츠_약관.pdf
사업방법서,data/sources/insurers/meritz/사업방법서/메리츠_사업설명서.pdf
상품요약서,data/sources/insurers/meritz/상품요약서/메리츠_상품요약서.pdf
EOF
```

**Extract text**:

```bash
python -m pipeline.step3_extract_text.extract_pdf_text --insurer meritz
```

**Inputs**:
- `data/evidence_sources/meritz_manifest.csv`
- PDF files listed in manifest

**Outputs** (creates/overwrites):
- `data/evidence_text/meritz/약관/메리츠_약관.page.jsonl`
- `data/evidence_text/meritz/사업방법서/메리츠_사업설명서.page.jsonl`
- `data/evidence_text/meritz/상품요약서/메리츠_상품요약서.page.jsonl`

**Expected Results**:
- Success: 3 PDFs
- Failed: 0

### STEP 4: Evidence Search

```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer meritz
```

**Inputs**:
- `data/scope/meritz_scope_mapped.csv`
- `data/evidence_text/meritz/` (extracted text)

**Outputs** (creates/overwrites):
- `data/evidence_pack/meritz_evidence_pack.jsonl` (34 lines)
- `data/scope/meritz_unmatched_review.csv` (updated with top_hits)

**Expected Results**:
- Total coverages: 34
- Matched: 22
- Unmatched: 12
- With evidence: 27
- Without evidence: 7

### STEP 5: Coverage Cards

```bash
python -m pipeline.step5_build_cards.build_cards --insurer meritz
```

**Inputs**:
- `data/scope/meritz_scope_mapped.csv`
- `data/evidence_pack/meritz_evidence_pack.jsonl`

**Outputs** (creates/overwrites):
- `data/compare/meritz_coverage_cards.jsonl` (34 lines)

**Expected Results**:
- Total coverages: 34
- Matched: 22
- Unmatched: 12
- Evidence found: 27
- Evidence not found: 7

### STEP 6: Markdown Report

```bash
python -m pipeline.step6_build_report.build_report --insurer meritz
```

**Inputs**:
- `data/compare/meritz_coverage_cards.jsonl`
- `data/scope/meritz_unmatched_review.csv`

**Outputs** (creates/overwrites):
- `reports/meritz_scope_report.md`

**Expected Sections**:
- Summary (stats)
- Coverage List (34 rows)
- Unmatched Review (12 rows)
- Evidence Not Found (7 rows)

### STEP 7: Samsung vs Meritz Comparison

```bash
python -m pipeline.step7_compare.compare_insurers --insurer-a samsung --insurer-b meritz
```

**Inputs**:
- `data/compare/samsung_coverage_cards.jsonl`
- `data/compare/meritz_coverage_cards.jsonl`

**Outputs** (creates/overwrites):
- `data/compare/samsung_vs_meritz_compare.jsonl` (25 lines)
- `reports/samsung_vs_meritz_report.md`
- `data/compare/compare_stats.json`

**Expected Results**:
```json
{
  "total_codes_compared": 25,
  "both_matched_count": 15,
  "either_unmatched_count": 0,
  "evidence_found_both": 15,
  "evidence_missing_any": 0,
  "only_in_a": 4,
  "only_in_b": 6
}
```

## Full Pipeline Script

```bash
#!/bin/bash
# Run from inca-rag-scope/ directory

set -e  # Exit on error

echo "=== STEP 1: Scope Extraction ==="
echo "Manual step - ensure data/scope/meritz_scope.csv exists (34 coverages)"
test -f data/scope/meritz_scope.csv || { echo "ERROR: meritz_scope.csv not found"; exit 1; }

echo "=== STEP 2: Canonical Mapping ==="
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer meritz

echo "=== STEP 3: PDF Text Extraction ==="
test -f data/evidence_sources/meritz_manifest.csv || { echo "ERROR: manifest not found"; exit 1; }
python -m pipeline.step3_extract_text.extract_pdf_text --insurer meritz

echo "=== STEP 4: Evidence Search ==="
python -m pipeline.step4_evidence_search.search_evidence --insurer meritz

echo "=== STEP 5: Coverage Cards ==="
python -m pipeline.step5_build_cards.build_cards --insurer meritz

echo "=== STEP 6: Markdown Report ==="
python -m pipeline.step6_build_report.build_report --insurer meritz

echo "=== STEP 7: Comparison ==="
python -m pipeline.step7_compare.compare_insurers --insurer-a samsung --insurer-b meritz

echo "=== Pipeline Complete ==="
```

## File Generation Summary

| Step | Creates/Overwrites |
|---|---|
| 1 | `data/scope/meritz_scope.csv` |
| 2 | `data/scope/meritz_scope_mapped.csv`, `meritz_unmatched_review.csv` |
| 3 | `data/evidence_text/meritz/**/*.page.jsonl` (3 files) |
| 4 | `data/evidence_pack/meritz_evidence_pack.jsonl`, updates `unmatched_review.csv` |
| 5 | `data/compare/meritz_coverage_cards.jsonl` |
| 6 | `reports/meritz_scope_report.md` |
| 7 | `data/compare/samsung_vs_meritz_compare.jsonl`, `compare_stats.json`, `reports/samsung_vs_meritz_report.md` |

## Verification

After running the full pipeline, verify with:

```bash
# Line counts should match consistency snapshot
wc -l data/scope/meritz_scope.csv                    # 35 (with header)
wc -l data/compare/meritz_coverage_cards.jsonl       # 34
wc -l data/evidence_pack/meritz_evidence_pack.jsonl  # 34
wc -l data/compare/samsung_vs_meritz_compare.jsonl   # 25

# Run tests
pytest tests/ -v

# Check consistency
cat reports/step5_consistency_snapshot.txt
```

## Notes

- All steps use deterministic algorithms (no LLM, no embedding)
- Results should be reproducible across runs
- Scope gate enforces no out-of-scope coverage processing
- Canonical source is `담보명mapping자료.xlsx` ONLY (read-only)
