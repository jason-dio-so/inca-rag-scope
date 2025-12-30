# STEP NEXT-10B-2 — Loader Lineage Audit

## Date
2025-12-28

## Objective
Audit loader for lineage contamination and extraction/inference violations.

---

## Audit Findings

### ✅ PASS: No Step7 Imports
```bash
grep -r "step7\|step7_amount" apps/loader/*.py
```
**Result:** No matches found

**Conclusion:** Loader does NOT import step7 modules directly.

---

### ✅ PASS: No inca-rag-final Imports
```bash
grep -r "inca.rag.final\|inca_rag_final" apps/loader/*.py
```
**Result:** No matches found

**Conclusion:** Loader does NOT import inca-rag-final lineage.

---

### ✅ PASS: Correct Input Files
**Loader reads from:**
- `data/evidence_pack/{insurer}_evidence_pack.jsonl`
- `data/compare/{insurer}_coverage_cards.jsonl`
- `data/sources/mapping/담보명mapping자료.xlsx` (canonical only)
- `apps/metadata/products.yml` (FK only)

**Conclusion:** Loader uses CSV/JSONL pipeline outputs as specified.

---

### ❌ FAIL: Loader Performs Extraction/Inference

**Location:** `apps/loader/step9_loader.py:564-586`

**Violation Code:**
```python
# Line 564-586: EXTRACTION from evidence snippets
for ev in evidences:
    if ev.get('doc_type') == '가입설계서':
        snippet = ev.get('snippet', '')
        if '만원' in snippet or '원' in snippet:
            value_text = snippet[:200]  # ← EXTRACTING from snippet
            source_doc_type = '가입설계서'
            break
```

**Violations:**
1. **Keyword search** (`'만원' in snippet`, `'원' in snippet`) — This is EXTRACTION logic
2. **Substring extraction** (`snippet[:200]`) — Creating new data from snippet
3. **Heuristic priority** (가입설계서 first, then fallback) — This is INFERENCE
4. **Status determination** based on extracted content — This is LOGIC

**Problem:**
Loader is acting as an **extractor** instead of a **mapper**.

---

### 🔍 Root Cause Analysis

**Expected:** `coverage_cards.jsonl` should contain:
```json
{
  "coverage_name_raw": "암 진단비",
  "coverage_code": "A4200_1",
  "amount": {
    "status": "CONFIRMED",
    "value_text": "3000만원",
    "source_doc_type": "가입설계서",
    "source_priority": "PRIMARY",
    "evidence": {
      "file_path": "...",
      "page": 2,
      "snippet": "..."
    },
    "notes": []
  }
}
```

**Actual:** `coverage_cards.jsonl` contains:
```json
{
  "coverage_name_raw": "질병 사망",
  "coverage_code": "A1100",
  "evidences": [...],
  // ❌ NO "amount" field
}
```

**Conclusion:**
- Step7 amount extraction pipeline has NEVER run
- `coverage_cards.jsonl` does NOT contain `amount` data
- Loader is trying to "fill the gap" by extracting amounts on-the-fly
- This violates scope-first/canonical-first principles

---

## Recommended Fix

### Strategy: Stub amount_fact Population

**Principle:** Loader should ONLY map existing data, NOT create new data.

Since `coverage_cards.jsonl` has NO `amount` field:
1. Loader should write `amount_fact` rows with:
   - `status = 'UNCONFIRMED'`
   - `value_text = NULL`
   - `evidence_id = NULL`
   - `source_doc_type = NULL`
   - `source_priority = NULL`

2. Remove ALL extraction logic (lines 564-627)

3. Wait for Step7 to produce `coverage_cards.jsonl` with proper `amount` field

**Alternative:** Skip `amount_fact` population entirely until Step7 is ready.

---

## Impact Assessment

**Current contamination:**
- `amount_fact` table contains EXTRACTED values (not from pipeline)
- Cannot distinguish between "real data" and "loader-inferred data"
- Breaks audit trail (no evidence link for extraction logic)

**After fix:**
- All `amount_fact` rows will be `UNCONFIRMED` with NULL values
- Clear signal: "amounts not yet extracted by Step7"
- DB state accurately reflects pipeline state

---

## Action Items

1. **Remove extraction logic** from `load_amount_fact` method
2. **Add lineage guardrail tests** to prevent future extraction
3. **Re-populate DB** with fixed loader
4. **Audit DB** to confirm no extracted/inferred values remain

---

## References

- Loader source: `apps/loader/step9_loader.py`
- Coverage cards example: `data/compare/samsung_coverage_cards.jsonl`
- DB schema: `docs/foundation/ERD_PHYSICAL.md`
- Step9 spec: `docs/foundation/STEP9_DB_POPULATION_SPEC.md`
