# STEP NEXT-10B-2 — Loader Lineage Fix COMPLETION

## Date
2025-12-28

## Objective
Fix loader to stop performing extraction/inference and only map CSV/JSONL → DB.

---

## Problem Identified

**Critical Violation:** Loader was performing amount extraction from evidence snippets instead of using pre-existing `amount` field from pipeline output.

### Evidence
- `apps/loader/step9_loader.py:564-627` contained keyword search logic (`'만원' in snippet`)
- Loader was creating new data (extracting amounts) instead of mapping existing data
- This violated scope-first/canonical-first/evidence principles
- Root cause: `coverage_cards.jsonl` missing `amount` field (Step7 never ran)

---

## Safety Gate Execution

### Branch Isolation
✅ Created freeze tag: `freeze/pre-10b2-20251228-2303` (commit: c6fad90)
✅ Created work branch: `fix/10b2-loader-lineage-safe`
✅ Snapshotted step7 files: `docs/lineage_snapshots/pre_10b2/`

### Halt Conditions Checked
- ✅ Current branch was `stage/step-next-db-2c-gamma` → Isolated
- ✅ Step7 stub files exist → Documented as "containment barriers"
- ✅ Loader had NO step7 imports → Verified clean

---

## Changes Made

### 1. Loader Fix (`apps/loader/step9_loader.py`)

**Before (EXTRACTION):**
```python
# Lines 564-586: VIOLATION
for ev in evidences:
    snippet = ev.get('snippet', '')
    if '만원' in snippet or '원' in snippet:  # ← KEYWORD SEARCH
        value_text = snippet[:200]  # ← SUBSTRING EXTRACTION
        source_doc_type = '가입설계서'
        break
```

**After (MAPPING ONLY):**
```python
# Lines 580-623: FIXED
amount_data = card.get('amount')  # ← Use existing field

if not amount_data:
    # Missing field → write UNCONFIRMED/NULL
    status = 'UNCONFIRMED'
    value_text = None
else:
    # Map existing fields directly (NO extraction)
    status = amount_data.get('status')
    value_text = amount_data.get('value_text')
```

**Key Changes:**
- Removed ALL snippet keyword search (`'만원' in snippet`, `'원' in snippet`)
- Removed substring extraction (`snippet[:200]`)
- Removed heuristic priority logic (가입설계서 first)
- Now expects `card['amount']` field from `coverage_cards.jsonl`
- If `amount` missing → writes `UNCONFIRMED` with NULL values

### 2. Deprecated Simple Loader (`apps/loader/step9_loader_simple.py`)

Added deprecation warning at top of file:
```python
⚠️  DEPRECATED: This version contains extraction logic violations.
    Use apps/loader/step9_loader.py instead.
```

### 3. Lineage Guardrail Tests (`tests/test_lineage_lock_loader.py`)

Added 5 tests (all PASS ✅):
- `test_loader_no_step7_imports` — Block step7 module imports
- `test_loader_no_inca_rag_final_imports` — Block inca-rag-final imports
- `test_loader_no_snippet_extraction` — Block keyword search in snippets
- `test_loader_allowed_inputs_only` — Enforce CSV/JSONL input paths
- `test_loader_amount_fact_uses_card_field` — Require `card['amount']` usage

### 4. Audit Documentation (`docs/audit/STEP_NEXT_10B_2_LOADER_AUDIT.md`)

Documented:
- Violation details with line numbers
- Root cause analysis
- Expected vs actual `coverage_cards.jsonl` schema
- Recommended fix strategy

### 5. Lineage Snapshot (`docs/lineage_snapshots/pre_10b2/`)

Created:
- `step7_filelist.txt` — 6 files
- `step7_hashes.json` — SHA256 hashes
- `README.md` — Snapshot purpose and restoration instructions

---

## Verification Results

### Tests
```bash
pytest tests/test_lineage_lock_loader.py -v
# 5 passed in 0.01s ✅

pytest -q
# 106 passed in 0.56s ✅
```

### Loader Behavior (Expected)
When loader runs now:
1. Reads `coverage_cards.jsonl` (NO snippet extraction)
2. Checks for `card['amount']` field
3. If missing → writes `UNCONFIRMED` status with NULL `value_text`
4. If present → maps fields directly to `amount_fact` table

### DB State Impact
- All existing `amount_fact` rows with extracted values are contaminated
- **Recommendation:** DELETE all `amount_fact` rows and re-populate with fixed loader
- After re-population: All rows will be `UNCONFIRMED` (correct, since Step7 hasn't run)

---

## Files Changed

### Modified
- `apps/loader/step9_loader.py` — Removed extraction logic
- `apps/loader/step9_loader_simple.py` — Added deprecation warning

### Added
- `tests/test_lineage_lock_loader.py` — 5 guardrail tests
- `docs/audit/STEP_NEXT_10B_2_LOADER_AUDIT.md` — Audit report
- `docs/lineage_snapshots/pre_10b2/` — Step7 snapshot (3 files)
- `STEP_NEXT_10B_2_COMPLETION.md` — This document

---

## Definition of Done (DoD)

✅ Step7 NOT called by loader
✅ Loader uses CSV/JSONL inputs exclusively
✅ CSV/JSONL ↔ DB 1:1 mapping (no extraction)
✅ pytest全体 PASS (106 tests)
✅ Lineage lock tests PASS (5 tests)
✅ Audit documentation complete
✅ Branch isolated from main

---

## Next Steps

### Immediate (STEP NEXT-10B-3)
1. **DB Re-population:**
   ```bash
   # Clear amount_fact table
   # Re-run loader with fixed version
   python -m apps.loader.step9_loader --db-url $DB_URL --mode reset_then_load
   ```

2. **Audit DB:**
   ```sql
   SELECT status, COUNT(*) FROM amount_fact GROUP BY status;
   -- Expected: All UNCONFIRMED

   SELECT COUNT(*) FROM amount_fact WHERE value_text IS NOT NULL;
   -- Expected: 0 (all NULL until Step7 runs)
   ```

### Future (STEP NEXT-10B-4)
1. Implement Step7 amount extraction (using stub as foundation)
2. Run Step7 to populate `coverage_cards.jsonl` with `amount` field
3. Re-run loader → `amount_fact` will have CONFIRMED rows

---

## Critical Agreements

❌ **NEVER again:** Loader performs extraction/inference
❌ **NEVER again:** Step7 logic embedded in loader/API
✅ **ALWAYS:** Pipeline (CSV/JSONL) → Loader (DB) → API (read-only)
✅ **ALWAYS:** Lineage lock tests run before any loader changes

---

## References

- Loader source: `apps/loader/step9_loader.py`
- Guardrail tests: `tests/test_lineage_lock_loader.py`
- Audit report: `docs/audit/STEP_NEXT_10B_2_LOADER_AUDIT.md`
- Freeze tag: `freeze/pre-10b2-20251228-2303`
- Work branch: `fix/10b2-loader-lineage-safe`

---

## Status

**✅ COMPLETE**

Loader is now lineage-safe and only performs CSV/JSONL → DB mapping.
Ready for DB re-population and audit.
