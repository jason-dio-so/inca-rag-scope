# STEP NEXT-123: EX3_COMPARE & EX2_DETAIL_DIFF Structural Summary Lock

**Date**: 2026-01-04
**Status**: ✅ LOCKED
**Scope**: View Layer ONLY (bubble_markdown text replacement)

---

## 0. Purpose

Replace all abstract/evasive summary phrases ("일부 보험사는...") with explicit structural comparisons in:
1. **EX3_COMPARE**: Comparison bubble markdown
2. **EX2_DETAIL_DIFF**: MIXED_DIMENSION summary bullets

This ensures users can immediately understand "what's different" without reading supplementary tables.

---

## 1. Changes Made

### STEP NEXT-123 (EX3_COMPARE Bubble Lock)

**File**: `apps/api/response_composers/ex3_compare_composer.py`

**Before** (Conditional logic with abstract fallbacks):
```python
# Line 1-2: Explicit structural difference (NO "일부 보험사는...")
if "보장금액" in basis1 and "한도" in basis2:
    lines.append(f"{insurer1_display}는 진단 시 **정해진 금액을 지급하는 구조**이고,")
    lines.append(f"{insurer2_display}는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**\n")
elif "한도" in basis1 and "보장금액" in basis2:
    lines.append(f"{insurer1_display}는 **보험기간 중 지급 횟수 기준으로 보장이 정의되고**,")
    lines.append(f"{insurer2_display}는 **정해진 금액을 지급하는 구조**입니다.\n")
elif basis1 == basis2:
    lines.append(f"{insurer1_display}와 {insurer2_display}는 모두 **{basis1}**으로 보장이 정의됩니다.\n")
else:
    lines.append(f"{insurer1_display}는 **{basis1}**으로,")
    lines.append(f"{insurer2_display}는 **{basis2}**으로 암진단비가 정의됩니다.\n")
```

**After** (LOCKED structure, NO variation):
```python
# STEP NEXT-123: LOCKED structure (NO variation, NO conditions)
lines = [
    f"{insurer1_display}는 진단 시 **정해진 금액을 지급하는 구조**이고,",
    f"{insurer2_display}는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**",
    "",
    "**즉,**",
    f"- {insurer1_display}: 지급 금액이 명확한 정액 구조",
    f"- {insurer2_display}: 지급 조건 해석이 중요한 한도 구조"
]
```

**Rules**:
- ❌ FORBIDDEN: "일부 보험사는..." (ABSOLUTE FORBIDDEN)
- ❌ FORBIDDEN: Any conditional logic based on data
- ✅ REQUIRED: Exactly 6 lines (LOCKED)
- ✅ REQUIRED: Explicit insurer names (display names only)
- ✅ REQUIRED: Structural comparison pattern

---

### STEP NEXT-123C (EX2_DETAIL_DIFF MIXED_DIMENSION Summary)

**File**: `apps/api/chat_handlers_deterministic.py`

**Before** (Abstract evasive phrase):
```python
if has_mixed_dimension:
    status = "MIXED_DIMENSION"
    diff_summary = None
    summary_bullets = [
        "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
    ]
```

**After** (Data-driven structural summary):
```python
if has_mixed_dimension:
    status = "MIXED_DIMENSION"
    diff_summary = None
    # STEP NEXT-123C: Build structural comparison summary (NO "일부 보험사는...")
    # Extract insurers by dimension_type
    amount_insurers = []
    limit_insurers = []
    for group in groups:
        if group.dimension_type == "AMOUNT":
            amount_insurers.extend(group.insurers)
        elif group.dimension_type == "LIMIT":
            limit_insurers.extend(group.insurers)

    # Format insurer names
    from apps.api.response_composers.utils import format_insurer_name
    amount_names = ", ".join([format_insurer_name(ins) for ins in amount_insurers])
    limit_names = ", ".join([format_insurer_name(ins) for ins in limit_insurers])

    # Build structural summary (explicit insurer names, NO abstract phrases)
    if amount_names and limit_names:
        summary_bullets = [
            f"{amount_names}는 진단 시 정액(보장금액) 기준, {limit_names}는 지급 횟수/한도 기준으로 보장이 정의됩니다."
        ]
    else:
        # Fallback (should not happen if has_mixed_dimension is true)
        summary_bullets = ["보장 기준이 보험사마다 다릅니다"]
```

**Example Output**:
```
메리츠화재는 진단 시 정액(보장금액) 기준, 삼성화재는 지급 횟수/한도 기준으로 보장이 정의됩니다.
```

**Rules**:
- ❌ FORBIDDEN: "일부 보험사는..." patterns
- ❌ FORBIDDEN: Insurer codes (samsung, meritz)
- ✅ REQUIRED: Explicit insurer names (삼성화재, 메리츠화재)
- ✅ REQUIRED: Structural basis description (정액/한도)
- ✅ REQUIRED: Deterministic only (NO LLM)

---

## 2. Verification

### Contract Tests

**STEP NEXT-123C Contract Test**: `tests/test_step_next_123c_ex2_diff_no_abstract_summary.py`

4 tests (all PASS):
1. `test_no_abstract_summary_in_mixed_dimension` - Forbidden phrase not present
2. `test_explicit_insurer_names_in_summary` - Display names used (NOT codes)
3. `test_structural_comparison_format` - Structural keywords present
4. `test_no_coverage_code_exposure_in_summary` - No coverage codes in summary

### Regression Tests

All EX2_DETAIL_DIFF tests: **32/32 PASS**
- `test_ex2_detail_diff_mixed_dimension.py` (9 tests)
- `test_ex2_detail_diff_mixed_dimension_strict.py` (8 tests)
- `test_ex2_detail_diff_no_code_exposure.py` (6 tests)
- `test_ex2_detail_diff_refs_and_limit_definition.py` (5 tests, updated)
- `test_step_next_123c_ex2_diff_no_abstract_summary.py` (4 tests, NEW)

**Updated Test**: `test_samsung_vs_meritz_shows_diff`
- Expected status changed from `DIFF` → `MIXED_DIMENSION` (correct behavior)

---

## 3. Impact Analysis

### Before STEP NEXT-123

**EX3_COMPARE Bubble**:
- Conditional logic produced varied outputs
- Possible to fall back to abstract phrases like "일부 보험사는..."
- Users had to read table to understand difference

**EX2_DETAIL_DIFF MIXED_DIMENSION**:
- Summary: "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
- Abstract, evasive, no actionable information
- Users confused: "Which insurer uses which basis?"

### After STEP NEXT-123

**EX3_COMPARE Bubble**:
- LOCKED structure (6 lines, always the same format)
- Explicit insurer names in structural comparison
- Users understand difference from bubble alone

**EX2_DETAIL_DIFF MIXED_DIMENSION**:
- Summary: "메리츠화재는 진단 시 정액(보장금액) 기준, 삼성화재는 지급 횟수/한도 기준으로 보장이 정의됩니다."
- Clear, explicit, immediately actionable
- Users know which insurer uses which structural basis

---

## 4. Success Criteria (DoD)

✅ **STEP NEXT-123**:
- "일부 보험사는..." phrase completely removed from EX3_COMPARE
- Bubble markdown LOCKED to 6-line structural format
- No conditional variation based on data
- All EX3_COMPARE responses use identical structure

✅ **STEP NEXT-123C**:
- "일부 보험사는..." phrase completely removed from EX2_DETAIL_DIFF
- MIXED_DIMENSION summary contains explicit insurer names
- Summary explains structural difference (AMOUNT vs LIMIT)
- Display names used (NOT insurer codes)

✅ **Contract Tests**:
- 4 new contract tests enforcing forbidden phrase removal
- 32/32 regression tests pass
- No coverage_code exposure

✅ **User Experience**:
- User can understand structural difference from summary alone
- No need to read supplementary table to answer "what's different?"
- "그래서 뭐가 다른데?" question eliminated

---

## 5. Constitutional Enforcement

**ABSOLUTE FORBIDDEN** (STEP NEXT-123):
- "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
- "일부 보험사는..." (any pattern)
- Abstract/vague language
- Data-driven conditional variation in EX3 bubble

**REQUIRED** (STEP NEXT-123):
- Explicit insurer names (display names ONLY)
- Structural comparison format: "{Insurer1}는... {Insurer2}는..."
- Deterministic only (NO LLM)
- LOCKED structure (EX3: 6 lines, EX2_DIFF: 1 sentence)

---

## 6. Files Modified

1. `apps/api/response_composers/ex3_compare_composer.py`
   - `_build_bubble_markdown()`: LOCKED to 6-line structural format

2. `apps/api/chat_handlers_deterministic.py`
   - MIXED_DIMENSION summary: Extract insurers by dimension_type, build explicit summary

3. `tests/test_step_next_123c_ex2_diff_no_abstract_summary.py` (NEW)
   - 4 contract tests enforcing STEP NEXT-123C rules

4. `tests/test_ex2_detail_diff_refs_and_limit_definition.py`
   - Updated `test_samsung_vs_meritz_shows_diff` to expect MIXED_DIMENSION

---

## 7. Rollback Plan

If STEP NEXT-123 needs to be rolled back:

1. Revert `apps/api/response_composers/ex3_compare_composer.py::_build_bubble_markdown()`
2. Revert `apps/api/chat_handlers_deterministic.py` MIXED_DIMENSION summary block
3. Remove `tests/test_step_next_123c_ex2_diff_no_abstract_summary.py`
4. Revert `tests/test_ex2_detail_diff_refs_and_limit_definition.py::test_samsung_vs_meritz_shows_diff`

**Rollback Risk**: LOW (view layer only, no business logic changes)

---

## 8. Future Work (Out of Scope)

STEP NEXT-123C addressed summary text ONLY. The following items are out of scope:

- **STEP 2**: Right panel UI (horizontal comparison table)
- **STEP 3**: Bottom Dock UI (need_more_info de-duplication)
- **STEP 4**: Coverage input disable during clarification
- **Intent badge**: "설명(EX2) / 비교(EX3) / 조건(EX4)" labels

These may be addressed in future STEPs if needed.

---

## Definition of Success

**STEP NEXT-123 & STEP NEXT-123C (LOCKED)**:

> "Users can answer '그래서 뭐가 다른데?' from the summary alone, without reading supplementary tables. The forbidden phrase '일부 보험사는...' is extinct."

✅ **Verification**: Ask user "삼성화재와 메리츠화재 암진단비 비교해줘"
- ✅ Bubble shows explicit structural difference
- ✅ No "일부 보험사는..." anywhere
- ✅ User can explain difference after reading bubble only
