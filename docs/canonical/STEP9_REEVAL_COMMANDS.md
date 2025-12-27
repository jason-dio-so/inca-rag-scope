# STEP 9 - Re-evaluation Commands (After Excel Update)

## Prerequisite
Excel file `data/sources/mapping/담보명mapping자료.xlsx` has been updated with 25 cancer coverages.

## Working Directory
```bash
cd /Users/cheollee/inca-rag-scope
```

## Re-run Canonical Mapping (Step 2)

### Hanwha
```bash
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer hanwha
```

### DB
```bash
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer db
```

### Meritz
```bash
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer meritz
```

## Re-run Evidence Search (Step 4)

### Hanwha
```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer hanwha
```

### DB
```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer db
```

### Meritz
```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer meritz
```

## Re-run Coverage Cards (Step 5)

### Hanwha
```bash
python -m pipeline.step5_build_cards.build_cards --insurer hanwha
```

### DB
```bash
python -m pipeline.step5_build_cards.build_cards --insurer db
```

### Meritz
```bash
python -m pipeline.step5_build_cards.build_cards --insurer meritz
```

## Re-run Reports (Step 6)

### Hanwha
```bash
python -m pipeline.step6_build_report.build_report --insurer hanwha
```

### DB
```bash
python -m pipeline.step6_build_report.build_report --insurer db
```

### Meritz
```bash
python -m pipeline.step6_build_report.build_report --insurer meritz
```

## Batch Execution (All Steps, All Insurers)

```bash
for insurer in hanwha db meritz; do
  echo "=== Re-evaluating $insurer ==="
  python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer $insurer
  python -m pipeline.step4_evidence_search.search_evidence --insurer $insurer
  python -m pipeline.step5_build_cards.build_cards --insurer $insurer
  python -m pipeline.step6_build_report.build_report --insurer $insurer
done
```

## Verification

### Check Mapping Results
```bash
grep "matched" data/scope/hanwha_scope_mapped.csv | wc -l
grep "matched" data/scope/db_scope_mapped.csv | wc -l
grep "matched" data/scope/meritz_scope_mapped.csv | wc -l
```

### Check Evidence Pack
```bash
wc -l data/evidence_pack/hanwha_evidence_pack.jsonl
wc -l data/evidence_pack/db_evidence_pack.jsonl
wc -l data/evidence_pack/meritz_evidence_pack.jsonl
```

### Check Reports
```bash
ls -lh reports/hanwha_scope_report.md
ls -lh reports/db_scope_report.md
ls -lh reports/meritz_scope_report.md
```

## Success Criteria
Refer to `STEP9_SUCCESS_METRICS.md` for expected numerical improvements.
