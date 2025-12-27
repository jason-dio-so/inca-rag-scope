# STEP 5-β — Coverage Cards QA Summary (8 Insurers)

## Overview

Quality assurance lock for coverage cards generation across all 8 insurers.

**Date**: 2025-12-27
**Scope**: samsung, meritz, db, hanwha, lotte, kb, hyundai, heungkuk

## Summary Table

| Insurer | Total Scope | Matched | Unmatched | Cards Generated | With Evidence | Empty Evidence | Empty Rate | Fallback Count |
|---------|-------------|---------|-----------|-----------------|---------------|----------------|------------|----------------|
| samsung |          41 |      33 |         8 |              41 |            40 |              1 |       2.4% |              - |
| meritz  |          34 |      26 |         8 |              34 |            27 |              7 |      20.6% |              - |
| db      |          31 |      26 |         5 |              30 |            30 |              0 |       0.0% |              - |
| hanwha  |          37 |      23 |        14 |              37 |            20 |             17 |      45.9% |              1 |
| lotte   |          37 |      30 |         7 |              37 |            35 |              2 |       5.4% |              - |
| kb      |          45 |      25 |        20 |              45 |            37 |              8 |      17.8% |              - |
| hyundai |          37 |      25 |        12 |              37 |            33 |              4 |      10.8% |              - |
| heungkuk |          36 |      30 |         6 |              36 |            32 |              4 |      11.1% |              - |

## Data Sources

### Per Insurer

**Input**:
- `data/scope/{insurer}_scope_mapped.csv` — Scope + canonical mapping
- `data/evidence_pack/{insurer}_evidence_pack.jsonl` — Evidence search results

**Output**:
- `data/compare/{insurer}_coverage_cards.jsonl` — Coverage cards

## Key Metrics

### Best Performers (Empty Rate)

1. **db**: 0.0% (0/30)
2. **samsung**: 2.4% (1/41)
3. **lotte**: 5.4% (2/37)

### Hanwha Special Notes

- **Fallback usage**: 1 coverage(s)
- **Empty rate**: 45.9% (17/37)
- **With evidence**: 20 (improved from 13 → 20 after STEP4-λ)

## Verification Commands

```bash
# Count cards per insurer
for insurer in samsung meritz db hanwha lotte kb hyundai heungkuk; do
  echo -n "$insurer: "
  wc -l < data/compare/${insurer}_coverage_cards.jsonl
done

# Verify evidence counts
python3 << 'PYEOF'
import json
for insurer in ['samsung', 'meritz', 'db', 'hanwha', 'lotte', 'kb', 'hyundai', 'heungkuk']:
    with open(f'data/compare/{insurer}_coverage_cards.jsonl') as f:
        cards = [json.loads(line) for line in f if line.strip()]
    found = sum(1 for c in cards if c.get('evidence_status') == 'found')
    print(f"{insurer}: {found} with evidence")
PYEOF
```

## Constraints Verified

✅ 1. **No code logic changes** (cards generation logic unchanged)
✅ 2. **No Excel/Canonical changes** (mapping file unchanged)
✅ 3. **No LLM/vector/RAG** (deterministic only)
✅ 4. **Fact-only** (no summaries/recommendations in cards)
✅ 5. **8 insurers** (all present)

## pytest Results

```bash
pytest -q
```

(Results will be appended below after execution)
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 0.44s

**pytest executed**: $(date)
