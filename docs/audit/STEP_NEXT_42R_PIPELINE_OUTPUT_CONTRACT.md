# STEP NEXT-42R: Canonical Pipeline Output Contract (AS-IS)

## SSOT Location
```
data/compare/*_coverage_cards.jsonl
```

**Currently populated insurers**: kb, samsung, meritz, hanwha, heungkuk, hyundai, lotte, db

---

## Schema Definition (Canonical)

Source: `core/compare_types.py:43-67` (CoverageCard dataclass)

### Required Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `insurer` | string | NO | Insurer key (lowercase: "kb", "samsung", etc.) |
| `coverage_name_raw` | string | NO | Raw coverage name from scope CSV |
| `coverage_code` | string | YES | Canonical coverage code (NULL if mapping_status="unmatched") |
| `coverage_name_canonical` | string | YES | Canonical coverage name (NULL if mapping_status="unmatched") |
| `mapping_status` | string | NO | `"matched"` or `"unmatched"` |
| `evidence_status` | string | NO | `"found"` or `"not_found"` |
| `evidences` | array[Evidence] | NO | Evidence list (max 3, can be empty if not_found) |
| `hits_by_doc_type` | object | NO | `{"약관": int, "사업방법서": int, "상품요약서": int}` |
| `flags` | array[string] | NO | Flags (e.g., `["policy_only"]`) |

### Evidence Sub-Schema

Source: `core/compare_types.py:29-40` (Evidence dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `doc_type` | string | `"약관"`, `"사업방법서"`, or `"상품요약서"` |
| `file_path` | string | Absolute path to evidence text JSONL |
| `page` | int | Page number (1-indexed) |
| `snippet` | string | Text snippet (max ~400 chars) |
| `match_keyword` | string | Keyword used for search (may contain fallback markers) |

---

## Field-Level Constraints

### `amount` field
**Status**: **DOES NOT EXIST in current pipeline output**

- Pipeline Step 1-5 do NOT produce `amount` field
- `amount` is added ONLY by optional Step 7 (amount_extraction)
- **Coverage cards from Step 5 have NO `amount` field**
- Measured: KB 0/36, Samsung 0/42, Meritz 0/34 cards have `amount`

### `mapping_status` constraints
- `"matched"` → `coverage_code` and `coverage_name_canonical` MUST be non-null
- `"unmatched"` → `coverage_code` and `coverage_name_canonical` MUST be null

### `evidence_status` constraints
- `"found"` → `evidences` array has 1-3 items, `hits_by_doc_type` has counts
- `"not_found"` → `evidences` array is empty, `hits_by_doc_type` is empty

### `evidences` array rules
- Max 3 items (diversity selection: 약관 > 사업방법서 > 상품요약서)
- Deduplication by (doc_type, file_path, page, snippet)
- Non-fallback keywords prioritized over fallback keywords
- Sorted by: non-fallback → doc_type priority → page → file_path → snippet

### `flags` array
- `["policy_only"]` → Coverage found ONLY in 약관, not in 사업방법서/상품요약서
- Empty array `[]` → No special flags

---

## Data Volume (Current)

| Insurer | Card Count | Example |
|---------|------------|---------|
| KB | 36 | A1100 (질병사망) |
| Samsung | 42 | A4200_1 (암진단비) |
| Meritz | 34 | A4200_1 (암진단비(유사암제외)) |
| Hanwha | TBD | |
| Heungkuk | TBD | |
| Hyundai | TBD | |
| Lotte | TBD | |
| DB | TBD | |

---

## Pipeline Stages (Step 1-5)

| Step | Input | Output | Adds to Card |
|------|-------|--------|--------------|
| Step 1 | PDF (가입설계서) | `*_scope.csv` | - |
| Step 2 | `*_scope.csv` + mapping Excel | `*_scope_mapped.csv` | - |
| Step 1.5 (Sanitize) | `*_scope_mapped.csv` | `*_scope_mapped.sanitized.csv` | - |
| Step 3 | PDF (약관/사업방법서/상품요약서) | `evidence_text/*.jsonl` | - |
| Step 4 | Sanitized scope + evidence_text | `*_evidence_pack.jsonl` | - |
| **Step 5** | Scope + evidence_pack | `*_coverage_cards.jsonl` | **ALL fields** |

**Step 7 (Optional)**: Adds `amount` field via LLM extraction (NOT part of canonical pipeline)

---

## Nullability Summary

| Field | Can be NULL? | When NULL? |
|-------|--------------|------------|
| `insurer` | NO | Never |
| `coverage_name_raw` | NO | Never |
| `coverage_code` | YES | When `mapping_status="unmatched"` |
| `coverage_name_canonical` | YES | When `mapping_status="unmatched"` |
| `mapping_status` | NO | Never |
| `evidence_status` | NO | Never |
| `evidences` | NO (array) | Can be empty `[]` |
| `hits_by_doc_type` | NO (object) | Can be empty `{}` |
| `flags` | NO (array) | Can be empty `[]` |
| **`amount`** | **N/A** | **Field does not exist in Step 5 output** |

---

## Key Invariants (Pipeline Guarantees)

1. **Join-rate gate**: Step 5 enforces 95% join rate (mapping_status="matched")
2. **Scope snapshot**: Step 4 and Step 5 use identical sanitized CSV via `resolve_scope_csv()`
3. **Evidence dedup**: Evidences are deduplicated by (doc_type, file_path, page, snippet)
4. **Doc-type diversity**: Max 1 evidence per doc_type in first-pass selection
5. **Fallback demotion**: Non-fallback keywords prioritized over fallback keywords
6. **No amount field**: Pipeline Step 1-5 output does NOT contain `amount` field

---

## CRITICAL: What This Contract Does NOT Include

❌ **NOT in contract**:
- `amount` field (Step 7 adds this, Step 5 does NOT)
- `status` field (e.g., "CONFIRMED", "PENDING")
- `source_doc_type` field
- `value_text` field
- Any LLM-generated content
- Any inference/interpretation

✅ **Only in contract**:
- Coverage mapping (code + canonical name)
- Evidence search results (doc_type, page, snippet)
- Evidence hit counts by doc_type
- Special flags (policy_only)

---

## Next: Compare with DB Schema Intent Model
See: `STEP_NEXT_42R_DB_INTENT_MODEL.md`
