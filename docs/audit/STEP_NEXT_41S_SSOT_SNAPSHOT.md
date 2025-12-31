# STEP NEXT-41S: SSOT Snapshot (Phase A-2)

**Date**: 2025-12-31
**SSOT Location**: `data/compare/*_coverage_cards.jsonl`
**SSOT Contract**: coverage_cards.jsonl (Step 5 output)

---

## File Inventory

| Insurer | File | Rows | Size | Last Modified |
|---------|------|------|------|---------------|
| KB | kb_coverage_cards.jsonl | 36 | 70K | 2025-12-31 11:47 |
| Meritz | meritz_coverage_cards.jsonl | 34 | 55K | 2025-12-31 13:11 |
| Samsung | samsung_coverage_cards.jsonl | 42 | 65K | 2025-12-31 11:46 |
| DB | db_coverage_cards.jsonl | - | 72K | 2025-12-31 11:32 |
| Hanwha | hanwha_coverage_cards.jsonl | - | 50K | 2025-12-31 11:32 |
| Heungkuk | heungkuk_coverage_cards.jsonl | - | 69K | 2025-12-31 11:32 |
| Hyundai | hyundai_coverage_cards.jsonl | - | 77K | 2025-12-31 11:32 |
| Lotte | lotte_coverage_cards.jsonl | - | 94K | 2025-12-31 11:32 |

**Total Rows**: 112 (KB + Meritz + Samsung)

---

## SSOT Schema (coverage_cards.jsonl)

### Top-Level Fields (9 fields)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `insurer` | string | YES | Insurer key (e.g., "kb", "samsung") |
| `coverage_name_raw` | string | YES | Original coverage name from insurer |
| `coverage_code` | string | YES (if matched) | Canonical coverage code (e.g., "A4200_1") |
| `coverage_name_canonical` | string | YES (if matched) | Canonical coverage name |
| `mapping_status` | string | YES | "matched" or "unmatched" |
| `evidence_status` | string | YES | "found" or "not_found" |
| `evidences` | array | YES | Array of evidence objects (may be empty) |
| `hits_by_doc_type` | object | YES | Evidence count by doc_type (약관/사업방법서/상품요약서) |
| `flags` | array | YES | Feature flags (e.g., "policy_only", "kb_bm_definition_hit") |

**CRITICAL FINDING**: **NO `amount` field exists in current SSOT.**

---

### Evidence Object Schema (5 fields)

Each object in the `evidences[]` array contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_type` | string | YES | Document type: "약관", "사업방법서", "상품요약서" |
| `file_path` | string | YES | Absolute path to evidence text JSONL |
| `page` | integer | YES | Page number in document |
| `snippet` | string | YES | Original text snippet (no summarization) |
| `match_keyword` | string | YES | Keyword used for matching |

**NO `rank` field** in SSOT evidence objects.

---

### hits_by_doc_type Object

Example structure:
```json
{
  "약관": 3,
  "사업방법서": 3,
  "상품요약서": 3
}
```

Keys: `"약관"`, `"사업방법서"`, `"상품요약서"`
Values: Integer counts (0 or positive)

---

### flags Array

Sample values observed:
- `"policy_only"` — Coverage found only in 약관 (not in 사업방법서/상품요약서)
- `"kb_bm_definition_hit"` — KB-specific flag (business method definition hit)

---

## Sample SSOT Record (KB - A1100)

```json
{
    "insurer": "kb",
    "coverage_name_raw": "질병사망",
    "coverage_code": "A1100",
    "coverage_name_canonical": "질병사망",
    "mapping_status": "matched",
    "evidence_status": "found",
    "evidences": [
        {
            "doc_type": "약관",
            "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/kb/약관/KB_약관.page.jsonl",
            "page": 4,
            "snippet": "55. 상급종합병원 간병인사용 상해입원일당(1-180일) ···········································································175\n제3장 질병 관련 특별약관\n1. 질병사망···································································································································································································································180\n2. 질병50%이상후유장해···················································································································································································180\n3. 질병후유장해(3~100%) ··············································································································································································181",
            "match_keyword": "질병사망"
        },
        {
            "doc_type": "사업방법서",
            "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/kb/사업방법서/KB_사업방법서.page.jsonl",
            "page": 10,
            "snippet": "대장기이식수술비\n5\n질병사망\n세만기\n80",
            "match_keyword": "질병사망"
        },
        {
            "doc_type": "상품요약서",
            "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/kb/상품요약서/KB_상품요약서.page.jsonl",
            "page": 9,
            "snippet": "대장기이식수술비\n5\n질병사망\n세만기\n80",
            "match_keyword": "질병사망"
        }
    ],
    "hits_by_doc_type": {
        "약관": 3,
        "사업방법서": 3,
        "상품요약서": 3
    },
    "flags": []
}
```

---

## CRITICAL FINDINGS

### 1. NO Amount Data in SSOT

Coverage_cards.jsonl **does NOT contain `amount` field**.

**Implication**:
- If DB has amount_fact data (285 rows), it came from a **different source** (not SSOT).
- Either:
  - (a) amount data is in a **separate JSONL** (e.g., `*_amounts.jsonl`), OR
  - (b) amount enrichment was done **directly to DB** (bypassing SSOT), OR
  - (c) amount data is **deprecated/stale**

**Action Required**: Locate amount source or confirm amount_fact should be reset.

### 2. NO Rank Field in SSOT Evidence

DB schema includes `evidence_ref.rank` (1-3), but SSOT evidences[] **do NOT have rank**.

**Implication**:
- Loader MUST generate rank (e.g., array index + 1) during insert.
- OR: Rank is assigned by loader logic (not in SSOT).

### 3. Evidence file_path Format

SSOT uses **absolute paths** (e.g., `/Users/cheollee/inca-rag-scope/data/evidence_text/kb/약관/KB_약관.page.jsonl`).

DB schema expects **relative paths** (`data/pdf/samsung/...`).

**Mismatch**: Path format differs between SSOT and DB schema contract.

---

## Field Extraction Method

```python
import json

ssot_files = [
    "data/compare/kb_coverage_cards.jsonl",
    "data/compare/meritz_coverage_cards.jsonl",
    "data/compare/samsung_coverage_cards.jsonl",
]

for file_path in ssot_files:
    with open(file_path) as f:
        for line in f:
            card = json.loads(line)
            # Extract keys: card.keys(), evidences[0].keys(), etc.
```

---

**Phase A-2 Complete**: SSOT snapshot captured with 3 critical findings.
