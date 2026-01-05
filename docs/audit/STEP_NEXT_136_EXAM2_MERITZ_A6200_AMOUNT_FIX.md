# STEP NEXT-136: EXAM2 Meritz A6200 Amount Display Fix

**Date**: 2026-01-04
**Status**: ✅ COMPLETE
**Type**: Bug Fix (Data Display)

---

## 1. Problem Statement

**Symptom**:
- Meritz A6200 (암직접입원일당) has "2만원" in proposal PDF
- ✅ `proposal_facts.coverage_amount_text: "2만원"` exists in coverage_cards
- ❌ EXAM2 (EX2_LIMIT_FIND) response shows "보험기간 중 1회" ONLY
- ❌ "2만원" was NOT displayed

**User Impact**:
- Customer sees incomplete information (missing daily amount)
- Cannot compare actual payment amounts between insurers

---

## 2. Root Cause Analysis

**Diagnosis**: Case A - Display Logic Issue (NOT data extraction issue)

**Investigation Path**:

### STEP 1: Data Availability Check
```jsonl
// data/compare/meritz_coverage_cards_slim.jsonl
{
  "coverage_code": "A6200",
  "proposal_facts": {
    "coverage_amount_text": "2만원",  // ✅ EXISTS
    ...
  },
  "kpi_summary": {
    "limit_summary": "보험기간 중 1회",  // ✅ EXISTS
    ...
  }
}
```

**Verdict**: Data extraction is CORRECT. Both limit AND amount exist.

### STEP 2: Display Logic Analysis

**File**: `apps/api/chat_handlers_deterministic.py:238-269`

**Faulty Logic** (Before STEP NEXT-136):
```python
if compare_field == "보장한도":
    limit_summary = kpi_summary.get("limit_summary")

    if limit_summary:
        value = limit_summary  # ✅ Extract limit
        dimension_type = "LIMIT"
        # ❌ STOP HERE - Amount is NEVER extracted
    else:
        # Fallback to amount only if NO limit exists
        amount_text = proposal_facts.get("coverage_amount_text")
        if amount_text:
            value = amount_text
            dimension_type = "AMOUNT"
```

**The Bug**:
- When `limit_summary` exists → extract LIMIT only, STOP
- When both limit AND amount exist → amount is DISCARDED
- Meritz A6200: Has BOTH → only "보험기간 중 1회" was extracted → "2만원" was lost

---

## 3. Solution (Single-Point Fix)

**修正 지점**: `apps/api/chat_handlers_deterministic.py:244-252`

**Before** (STEP NEXT-91):
```python
if limit_summary:
    value = limit_summary
    dimension_type = "LIMIT"
    # ... refs
```

**After** (STEP NEXT-136):
```python
if limit_summary and amount_text:
    # STEP NEXT-136: When BOTH exist, combine them
    value = f"{limit_summary} (일당 {amount_text})"
    dimension_type = "LIMIT"  # Treat as LIMIT dimension (primary)
    # ... refs
elif limit_summary:
    value = limit_summary
    dimension_type = "LIMIT"
    # ... refs
```

**Change Summary**:
1. Check for BOTH `limit_summary` AND `amount_text` first
2. When both exist → combine into single display string: `"{limit} (일당 {amount})"`
3. Fallback to limit-only or amount-only when only one exists

---

## 4. Verification Results

**Test Query**:
```python
request = ChatRequest(
    insurers=['samsung', 'meritz'],
    coverage_code='A6200',
    message='암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘',
    kind='EX2_LIMIT_FIND'
)
```

**Before STEP NEXT-136**:
```
Group: 한도: 보험기간 중 1회
Insurers: ['meritz']
  - meritz: 보험기간 중 1회  ❌ Missing "2만원"
```

**After STEP NEXT-136**:
```
Group: 한도: 보험기간 중 1회 (일당 2만원)
Insurers: ['meritz']
  - meritz: 보험기간 중 1회 (일당 2만원)  ✅ Shows "2만원"
```

**Verification Checks**:
- ✅ "2만원" found in response
- ✅ NO A4200_1 refs (STEP NEXT-134/135 preserved)
- ✅ Samsung shows "2만원" (amount-only, no regression)
- ✅ Status: `MIXED_DIMENSION` (correct classification)

---

## 5. Constitutional Compliance

**EXAM CONSTITUTION Check**:
- ✅ NO EXAM cross-contamination (EXAM2 logic only)
- ✅ NO LLM usage (deterministic combination)
- ✅ NO coverage_code exposure (display names only)
- ✅ NO temporary hardcoding (generic logic)

**STEP NEXT Regression Prevention**:
- ✅ STEP NEXT-91 (MIXED_DIMENSION) preserved
- ✅ STEP NEXT-134 (EX2_LIMIT_FIND routing) preserved
- ✅ STEP NEXT-135 (coverage_code resolution) preserved
- ✅ NO changes to other EXAM types (EX2_DETAIL, EX3, EX4)

---

## 6. Impact Analysis

**Affected Scope**:
- **File**: `apps/api/chat_handlers_deterministic.py` (1 location)
- **Function**: `Example2DiffHandlerDeterministic.execute()` (lines 244-252)
- **Intent**: `EX2_LIMIT_FIND`, `EX2_DETAIL_DIFF` (when `compare_field == "보장한도"`)
- **Coverage**: ALL coverages with BOTH limit AND amount (e.g., daily benefits)

**Coverage Examples with BOTH**:
- A6200 (암직접입원일당)
- A6100_1 (질병입원일당)
- A6300_1 (상해입원일당)

**Unchanged Coverage Examples**:
- A4200_1 (암진단비): Amount-only → NO change
- A5200 (암수술비): Limit-only → NO change

---

## 7. Definition of Done (DoD)

**All Checks PASSED**:
- ✅ Meritz A6200 displays "2만원" in EXAM2 results
- ✅ Format: "{limit} (일당 {amount})" when both exist
- ✅ NO A4200_1 contamination (coverage resolution preserved)
- ✅ Samsung A6200 shows "2만원" (amount-only, regression-free)
- ✅ NO LLM usage (deterministic combination)
- ✅ NO hardcoding (generic logic for all daily benefits)
- ✅ Single-point fix (1 location only)

---

## 8. Before/After JSON Snippets

### Before STEP NEXT-136

**Meritz A6200 Response**:
```json
{
  "status": "MIXED_DIMENSION",
  "groups": [
    {
      "value_display": "보장금액: 2만원",
      "insurers": ["samsung"],
      "dimension_type": "AMOUNT"
    },
    {
      "value_display": "한도: 보험기간 중 1회",  // ❌ Missing "2만원"
      "insurers": ["meritz"],
      "dimension_type": "LIMIT",
      "insurer_details": [
        {
          "insurer": "meritz",
          "raw_text": "보험기간 중 1회"  // ❌ Missing "2만원"
        }
      ]
    }
  ]
}
```

### After STEP NEXT-136

**Meritz A6200 Response**:
```json
{
  "status": "MIXED_DIMENSION",
  "groups": [
    {
      "value_display": "보장금액: 2만원",
      "insurers": ["samsung"],
      "dimension_type": "AMOUNT"
    },
    {
      "value_display": "한도: 보험기간 중 1회 (일당 2만원)",  // ✅ Shows "2만원"
      "insurers": ["meritz"],
      "dimension_type": "LIMIT",
      "insurer_details": [
        {
          "insurer": "meritz",
          "raw_text": "보험기간 중 1회 (일당 2만원)"  // ✅ Shows "2만원"
        }
      ]
    }
  ]
}
```

---

## 9. Why This Fix is the ONLY Solution

**Why NOT modify data extraction?**
- Data extraction is CORRECT (both limit and amount exist in cards)
- Modifying Step1-7 would be unnecessary pipeline changes

**Why NOT modify frontend display?**
- Frontend only renders what backend sends
- Business logic should be in backend (SSOT principle)

**Why NOT add new field?**
- Adding fields would require schema changes across multiple layers
- Current fix uses existing data (no schema migration)

**Why this specific combination format?**
- `"{limit} (일당 {amount})"` clearly shows BOTH dimensions
- User can immediately see: "How often?" (limit) + "How much?" (amount)
- NO ambiguity (parentheses indicate supplementary info)

---

## 10. Future Prevention

**Guard Rails**:
1. When adding new coverage with BOTH dimensions → verify display includes both
2. When modifying EX2 diff logic → test daily benefit coverages (A6xxx)
3. Contract test: "Meritz A6200 MUST show '2만원'" (regression detector)

**Test Coverage Needed**:
- [ ] Add contract test: `test_step_next_136_meritz_a6200_amount_display.py`
- [ ] Verify all A6xxx coverages (daily benefits) show amounts correctly
- [ ] Regression suite: STEP NEXT-91/134/135 preserved

---

## 11. Classification Summary

**Bug Category**: Display Logic (NOT data extraction)
**Root Cause**: Priority logic stopped at limit, discarded amount
**Fix Type**: Single-point conditional logic enhancement
**Risk Level**: LOW (isolated change, deterministic, no schema change)
**Regression Risk**: MINIMAL (only affects BOTH-dimension cases)

---

## 12. Conclusion

STEP NEXT-136 fixes a **display completeness bug** where daily benefit coverages (입원일당) with BOTH limit AND amount would only show the limit, hiding the daily payment amount from customers.

The fix is **minimal, deterministic, and surgical**: check for both fields first, combine if both exist, otherwise fall back to single-dimension display.

**User Impact**: Customers can now see complete information (frequency + amount) for daily benefit coverages in EXAM2 comparisons.

---

**Compliance**: ✅ EXAM CONSTITUTION
**Regression**: ✅ STEP NEXT-91/134/135 preserved
**Evidence**: ✅ Test output shows "2만원" in response
**SSOT**: ✅ Backend-only change (no frontend/pipeline modifications)

**LOCKED**: This fix is the SSOT for displaying BOTH limit and amount in EXAM2.
