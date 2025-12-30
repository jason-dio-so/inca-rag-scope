# STEP NEXT-10B-2C-1 — Step7 Amount Lineage Verification Report

## Date
2025-12-28

## Objective
Verify that Step7 produces `amount` field in `coverage_cards.jsonl` BEFORE proceeding with DB/loader modifications.

---

## STOP Condition Triggered

### Test Executed
```python
import json, itertools, pathlib
p=pathlib.Path("data/compare/samsung_coverage_cards.jsonl")
amount_present=0
for line in itertools.islice(p.open(encoding="utf-8"), 200):
    o=json.loads(line)
    if "amount" in o and o["amount"] is not None:
        amount_present += 1
print("amount_present_in_first200:", amount_present)
```

### Result
```
amount_present_in_first200: 0
```

### Conclusion
**STOP:** Step7 is a STUB (or not applied).

The `amount` field does NOT exist in `samsung_coverage_cards.jsonl`. This means:
1. Step7 amount extraction has NEVER successfully run
2. Current Step7 implementation (from STEP NEXT-10B-1A) is a minimal stub
3. The stub correctly returns `NOT_IMPLEMENTED` status

---

## Evidence

### Step7 Status Check
```bash
python -m pipeline.step7_amount.run --insurer samsung --dry-run
```

**Output:**
```
Status: DRY_RUN
Coverage count: 0  # ← Step7 found 0 coverages to process
Message: STUB: Amount extraction logic to be implemented
```

### Current Step7 Implementation
From `pipeline/step7_amount/extract_proposal_amount.py:67-77`:
```python
def extract_amounts_from_proposal(insurer: str, dry_run: bool = False):
    # STUB: Actual extraction to be implemented in next STEP
    return {
        "action": "extract_amounts",
        "insurer": insurer,
        "status": "NOT_IMPLEMENTED",  # ← STUB
        "message": "STUB: Amount extraction logic to be implemented in STEP NEXT-10B-2"
    }
```

### Existing coverage_cards.jsonl Structure
Sample from `data/compare/samsung_coverage_cards.jsonl`:
```json
{
  "coverage_name_raw": "질병 사망",
  "coverage_code": "A1100",
  "evidences": [...],
  "hits_by_doc_type": {...},
  "flags": []
  // ❌ NO "amount" field
}
```

---

## Root Cause Analysis

### Timeline
1. **STEP NEXT-10B-1A (2025-12-28):** Created Step7 stub modules to lock lineage
   - Purpose: Prevent contamination, not to implement extraction
   - Result: Stub .py files created with `NOT_IMPLEMENTED` status

2. **STEP NEXT-10B-2 (2025-12-28):** Fixed loader to expect `amount` field
   - Loader now correctly uses `card.get('amount')` instead of extracting
   - If `amount` missing → writes `UNCONFIRMED` + NULL to DB

3. **Current State:** Step7 stub exists but does NOT produce `amount` field
   - `coverage_cards.jsonl` has NO `amount` data
   - Loader will write all `UNCONFIRMED` + NULL (correct behavior for stub)

### Why Step7 is a Stub
From `docs/audit/STEP_NEXT_10B_1A_STEP7_DIAG.md`:
> **Branch C confirmed**: Step7 amount extraction modules were implemented locally but **never committed to git**. Only the compiled bytecode remains from local execution.
>
> **Mitigation Strategy:**
> 1. Do NOT attempt decompilation
> 2. Reconstruct minimal step7 interface from documentation
> 3. Implement clean, scope-based step7 modules with explicit guards
> 4. **Stub returns NOT_IMPLEMENTED status for actual logic (to be refined in next STEP)**

---

## Impact Assessment

### Current DB State
- `amount_fact` table contains rows from PREVIOUS loader (with extraction logic)
- Those rows have extracted values from snippets (contaminated)
- **Recommendation:** DELETE all `amount_fact` rows before any new load

### If Loader Runs Now
With current stub Step7:
1. `coverage_cards.jsonl` has NO `amount` field
2. Loader reads cards, finds NO `amount` field
3. Loader writes `amount_fact` with:
   - `status = 'UNCONFIRMED'`
   - `value_text = NULL`
   - `evidence_id = NULL`

**This is CORRECT behavior** for a stub/unimplemented Step7.

---

## Next Steps

### Option 1: Implement Step7 Amount Extraction (RECOMMENDED)
**File:** `pipeline/step7_amount/extract_proposal_amount.py`

**Requirements:**
1. Read from **가입설계서 (proposal)** PDF first (PRIMARY)
2. Search for amount keywords: `가입금액`, `보험가입금액`, `보험금액`
3. Extract clean value (e.g., "3000만원") — NO table of contents, NO clause numbers
4. If not found in 가입설계서, try 사업방법서/상품요약서/약관 (SECONDARY)
5. Write to `coverage_cards.jsonl` with `amount` field:
   ```json
   {
     "coverage_name_raw": "...",
     "amount": {
       "status": "CONFIRMED",
       "value_text": "3000만원",
       "source_doc_type": "가입설계서",
       "source_priority": "PRIMARY",
       "evidence": {...},
       "notes": []
     }
   }
   ```

**Constraints:**
- ✅ Only process coverages from `data/scope/samsung_scope.csv` (scope-first)
- ✅ Extract text as-is (no LLM, no calculation)
- ❌ NO imports from `apps.*`, `inca-rag-final`
- ❌ NO inference/judgment about what "should be" the amount

### Option 2: Continue Without Amounts (NOT RECOMMENDED)
Accept that `amount_fact` will remain `UNCONFIRMED` + NULL until Step7 is implemented.

**Pros:** Can proceed with other work
**Cons:** Cannot demonstrate amount comparison functionality

---

## Recommendations

### Immediate (Before DB Work)
1. **DO NOT** re-populate DB yet
2. **DO NOT** modify loader further (it's correct now)
3. **DECIDE:** Implement Step7 or accept NULL amounts?

### If Implementing Step7
1. Create test: `tests/test_step7_amount_extraction.py`
2. Implement: `pipeline/step7_amount/extract_proposal_amount.py`
3. Run: `python -m pipeline.step7_amount.run --insurer samsung`
4. Verify: Re-run this verification (amount_present should be > 0)
5. Then: Proceed with DB re-population

### If Accepting NULL Amounts
1. Document decision
2. Re-populate DB (all `UNCONFIRMED` + NULL)
3. Update API to handle NULL amounts gracefully
4. Schedule Step7 implementation for future

---

## DoD Status

### ❌ FAILED (STOP Condition)
- ❌ `amount` field exists in `samsung_coverage_cards.jsonl`: **NO** (0/200 records)
- ❌ PRIMARY/SECONDARY lineage demonstrated: **N/A** (no amounts)
- ❌ Forbidden patterns check: **N/A** (no amounts)
- ❌ Tests added: **N/A** (stopped at verification)
- ❌ Report generated: **This document**

### Next STEP Decision Required
**User must decide:**
- Option A: Implement Step7 extraction → Proceed with full verification
- Option B: Accept NULL amounts → Proceed with DB re-population (UNCONFIRMED only)

---

## References

- Step7 stub: `pipeline/step7_amount/extract_proposal_amount.py`
- Loader fix: `apps/loader/step9_loader.py:519-658`
- Branch: `fix/10b2c-step7-lineage-verify`
- Previous diagnostic: `docs/audit/STEP_NEXT_10B_1A_STEP7_DIAG.md`
- Loader audit: `docs/audit/STEP_NEXT_10B_2_LOADER_AUDIT.md`

---

## Status

**⚠️  VERIFICATION INCOMPLETE — STOP CONDITION MET**

Step7 is a stub. No `amount` field in coverage_cards.jsonl.

**Decision required before proceeding.**
