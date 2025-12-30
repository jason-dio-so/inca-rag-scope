# STEP 6-α — Multi-Insurer Report Summary (Historical)

## Overview

**Coverage Code**: A4200_1
**Report File**: ~~`reports/a4200_1_8insurers.md`~~ (REMOVED)
**Date**: 2025-12-27

⚠️ **Note**: This is a historical record. Current SSOT is `data/compare/*_coverage_cards.jsonl`

## Metrics

| Metric | Count |
|--------|-------|
| Total insurers with A4200_1 | 8 |
| With evidence | 8 |
| Without evidence | 0 |
| All matched | 8 |

## Per-Insurer Results

| Insurer | Exists | Mapping | Evidence | Evidence Count | Hits (약관/사업/상품) |
|---------|--------|---------|----------|----------------|---------------------|
| samsung | ✅ | matched | found    |              3 |               3/3/3 |
| meritz  | ✅ | matched | found    |              3 |               3/0/3 |
| db      | ✅ | matched | found    |              3 |               3/3/3 |
| hanwha  | ✅ | matched | found    |              3 |               3/3/3 |
| lotte   | ✅ | matched | found    |              3 |               3/3/3 |
| kb      | ✅ | matched | found    |              3 |               3/0/0 |
| hyundai | ✅ | matched | found    |              3 |               3/3/3 |
| heungkuk | ✅ | matched | found    |              3 |               3/3/3 |

## Evidence Document Type Coverage

- **All 3 doc types** (약관 + 사업방법서 + 상품요약서): 6 insurers
- **Policy only** (약관만): 1 insurers

## Verification Commands (Historical)

```bash
# View generated report (REMOVED)
# cat reports/a4200_1_8insurers.md
```

## Constraints Verified

✅ 1. **No code changes** (used existing cards)
✅ 2. **No Excel/Canonical changes**
✅ 3. **No LLM/vector/RAG**
✅ 4. **Fact-only** (snippets only, no interpretation)
✅ 5. **8 insurers** (all present)
✅ 6. **Lock table** (included in report)

## pytest Results

```bash
pytest -q
```

(Results will be appended below)
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 0.45s

**pytest executed**: 2025-12-27
