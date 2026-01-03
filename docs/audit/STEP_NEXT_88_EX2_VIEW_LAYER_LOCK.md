# STEP NEXT-88 — EX2_LIMIT_FIND View Layer Expression Lock

**Date**: 2026-01-03
**Status**: ✅ COMPLETE (All tests PASS)

---

## 1. Purpose

Lock the **view layer expressions** for EX2_LIMIT_FIND to ensure user-facing text is clear and grammatically correct:

1. **Question bubbles** must show context (insurers + coverage)
2. **Result bubbles** must use correct singular/plural grammar
3. **Coverage codes** must never be exposed to users
4. **Korean particles** must be grammatically correct (와/과)

---

## 2. Constitutional Rules (LOCKED)

### 2.1 Title Must Include Context

❌ **Forbidden**:
```
"보장한도 차이 비교"
```

✅ **Required**:
```
"삼성화재와 메리츠화재의 암진단비 보장한도 차이"
```

**Rule**: Title MUST include:
- Insurer names (formatted with display names)
- Coverage name (NEVER coverage_code)
- Compare field
- "차이" or similar action word

### 2.2 Singular/Plural Grammar

**Rule**: Use correct Korean grammar based on insurer count

- 1 insurer: "선택한 보험사의"
- 2+ insurers: "선택한 보험사들의" OR specific names

**Example**:
```
# 2 insurers (specific names preferred)
"삼성화재의 보장한도가 다릅니다"

# NOT generic:
❌ "선택한 보험사의 보장한도가 다릅니다"
```

### 2.3 Coverage Code Exposure = 0%

**Rule**: Coverage codes (e.g., `A4200_1`) must NEVER appear in:
- Title
- Summary bullets
- Section titles
- Table cells (user-facing)

**Allowed**: Only in refs (`PD:`, `EV:`)

### 2.4 Korean Particle Rules (와/과)

**Rule**: Use correct particle based on final consonant

- **와**: after vowel (받침 없음)
  - "삼성화재**와** 메리츠화재"
  - "KB손해보험**와** 롯데손해보험"

- **과**: after consonant (받침 있음)
  - "한화손해보험**과** 흥국화재"
  - "현대해상**과** DB손해보험"

---

## 3. Implementation

### 3.1 New Utility Functions (`apps/api/response_composers/utils.py`)

```python
# Insurer display name mapping
INSURER_DISPLAY_NAMES = {
    "samsung": "삼성화재",
    "meritz": "메리츠화재",
    "hanwha": "한화손해보험",
    "kb": "KB손해보험",
    "hyundai": "현대해상",
    "lotte": "롯데손해보험",
    "heungkuk": "흥국화재",
    "db": "DB손해보험"
}

def format_insurer_name(insurer_code: str) -> str
def format_insurer_list(insurers: List[str]) -> str  # Handles 와/과 particle
def get_insurer_subject(insurers: List[str]) -> str  # Handles singular/plural
def _get_korean_particle_wa_gwa(text: str) -> str    # Korean grammar helper
```

### 3.2 Composer Updates (`apps/api/response_composers/ex2_limit_find_composer.py`)

**Title generation**:
```python
# Before (STEP NEXT-87C)
title = f"{coverage_name or coverage_code} {compare_field} 차이 비교"

# After (STEP NEXT-88)
safe_coverage_name = display_coverage_name(
    coverage_name=coverage_name,
    coverage_code=coverage_code
)
insurer_list_str = format_insurer_list(insurers)
title = f"{insurer_list_str}의 {safe_coverage_name} {compare_field} 차이"
```

**Summary generation**:
```python
# Before
f"선택한 보험사의 {compare_field}는 모두 동일합니다"

# After
insurer_subject = get_insurer_subject(insurers)
f"{insurer_subject} {compare_field}는 모두 동일합니다"
```

**Table rows**:
```python
# Before
row_cells = [{"text": insurer}, ...]

# After
insurer_display = format_insurer_name(insurer)
row_cells = [{"text": insurer_display}, ...]
```

---

## 4. Test Results

### 4.1 View Layer Tests (`tests/test_ex2_limit_find_view_layer.py`)

```
test_title_includes_insurer_context PASSED
test_title_includes_coverage_name PASSED
test_singular_plural_grammar PASSED
test_korean_particle_wa_gwa PASSED
test_coverage_code_not_in_title PASSED
test_coverage_code_not_in_summary PASSED
test_insurer_display_names_in_table PASSED
test_3_insurer_list_formatting PASSED
test_compare_field_in_title PASSED
test_title_structure PASSED

10 passed in 0.02s
```

### 4.2 Content Contract Tests (`tests/test_ex2_limit_find_content_contract.py`)

```
test_ex2_limit_find_contract_validation_function PASSED
test_scenario_1_limit_difference PASSED
test_scenario_2_waiting_period_difference PASSED
test_scenario_3_condition_difference PASSED
test_scenario_4_limit_difference_multi_insurer PASSED
test_scenario_5_reduction_condition_filter PASSED
test_scenario_6_waiver_condition_difference PASSED

7 passed in 0.01s
```

### 4.3 All EX2/EX3 Tests

```
43 passed, 1 deselected, 9 warnings in 0.10s
```

**All existing tests pass** ✅

---

## 5. Example Outputs

### Before (STEP NEXT-87C)
```
Title: "암직접입원비 보장한도 차이 비교"
Summary: ["samsung의 보장한도가 다릅니다", ...]
Table: [{"text": "samsung"}, ...]
```

**Problems**:
- No insurer context in title
- Insurer codes instead of display names
- Missing Korean grammar (와/과)

### After (STEP NEXT-88)
```
Title: "삼성화재와 메리츠화재의 암직접입원비 보장한도 차이"
Summary: ["삼성화재의 보장한도가 다릅니다", ...]
Table: [{"text": "삼성화재"}, ...]
```

**Fixed**:
- ✅ Insurer context in title
- ✅ Display names everywhere
- ✅ Correct Korean particle (와)
- ✅ No coverage code exposure

---

## 6. Definition of Done (DoD)

✅ **All DoD items completed:**

- [x] Title includes insurer+coverage context
- [x] Singular/plural grammar is correct
- [x] Coverage code exposure = 0%
- [x] Korean particles (와/과) are grammatically correct
- [x] Insurer display names used throughout
- [x] All view layer tests pass
- [x] All content contract tests pass
- [x] All existing EX2/EX3 tests pass
- [x] No logic changes (view layer only)
- [x] Deterministic only (NO LLM)

---

## 7. Files Modified/Created

### Modified
- `apps/api/response_composers/utils.py` - Added view layer helpers
- `apps/api/response_composers/ex2_limit_find_composer.py` - Updated title/summary/table generation
- `apps/api/chat_handlers_deterministic.py` - Fixed EX2_DETAIL_DIFF title generation (line 376-382)

### Created
- `tests/test_ex2_limit_find_view_layer.py` - View layer contract tests
- `docs/audit/STEP_NEXT_88_EX2_VIEW_LAYER_LOCK.md` - This document

---

## 8. Next Steps

**EX2_LIMIT_FIND view layer is LOCKED** ✅

Future enhancements:
1. Apply same rules to EX3_COMPARE
2. Apply same rules to EX4_ELIGIBILITY
3. Add question bubble rewriting (frontend or backend)

---

## 9. References

- **SSOT**: `docs/ui/INTENT_ROUTER_RULES.md` (EX2_LIMIT_FIND section)
- **Composer**: `apps/api/response_composers/ex2_limit_find_composer.py`
- **Utils**: `apps/api/response_composers/utils.py`
- **View Tests**: `tests/test_ex2_limit_find_view_layer.py`
- **Content Tests**: `tests/test_ex2_limit_find_content_contract.py`
- **Samples**: `tests/manual_test_ex2_limit_find_samples.py`

---

**STEP NEXT-88 COMPLETE** ✅

User-facing text for EX2_LIMIT_FIND is now clear, grammatically correct, and constitutionally compliant.
