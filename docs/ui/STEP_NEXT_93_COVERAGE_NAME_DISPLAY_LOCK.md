# STEP NEXT-93: Coverage Name Display Normalization Lock

## Purpose

Eliminate spacing and variation issues in coverage_name display across all UI surfaces.

**Problem:**
- User inputs: `"암 진단비"`, `"암진단 비"`, `"암-진단비"` (inconsistent spacing/separators)
- Current behavior: Displayed as-is → UX confusion, inconsistent presentation
- Same coverage appears differently in title/summary/bubble depending on input

**Solution:**
- Normalize ALL coverage_name display through single SSOT function
- `"암 진단비"` → `"암진단비"` (always)
- Apply normalization transparently in existing `display_coverage_name()` utility

**Scope:**
- View Layer ONLY (display strings)
- NO changes to coverage_code, mapping, or compiler logic
- Deterministic only (NO LLM)

---

## Constitutional Rules

✅ **REQUIRED:**
- All coverage_name display goes through `display_coverage_name()`
- Normalization always applied (transparent to callers)
- coverage_code UI exposure remains 0%
- refs (PD:/EV:) preserved
- Deterministic only

❌ **FORBIDDEN:**
- coverage_code patterns (A4200_1) in display
- Raw request.coverage_names bypassing normalization
- LLM usage
- New inference/recommendation in EX2

---

## Implementation

### 1) Normalization Function

**Location:** `apps/api/response_composers/utils.py:18-80`

**Function:**
```python
def normalize_coverage_name_for_display(name: str) -> str:
    """
    Normalize coverage name for consistent UI display

    RULES:
    - Remove spaces between Korean characters: "암 진단비" → "암진단비"
    - Remove separators: [-_/·•] → ""
    - Keep only: 가-힣, 0-9, (), %, ·
    - Reject coverage_code patterns (A4200_1)
    - Return "" if invalid
    """
```

**Algorithm:**
1. Trim whitespace
2. Reject coverage_code patterns immediately
3. Replace separators with spaces
4. Remove non-allowed characters
5. Remove spaces between Korean characters
6. Collapse multiple spaces
7. Final trim
8. Reject if too short (<=1)

### 2) Enhanced display_coverage_name()

**Location:** `apps/api/response_composers/utils.py:83-130`

**Before:**
```python
def display_coverage_name(*, coverage_name, coverage_code):
    if not coverage_name:
        return "해당 담보"
    if re.match(r"^[A-Z]\d{4}_\d+$", coverage_name):
        return "해당 담보"
    return coverage_name  # ❌ Raw name
```

**After (STEP NEXT-93):**
```python
def display_coverage_name(*, coverage_name, coverage_code):
    if not coverage_name:
        return "해당 담보"

    # STEP NEXT-93: ALWAYS normalize
    normalized = normalize_coverage_name_for_display(coverage_name)

    if not normalized:
        return "해당 담보"

    return normalized  # ✅ Normalized name
```

### 3) Automatic Application

**Coverage via existing usage:**
- `apps/api/chat_handlers_deterministic.py` (EX2_DETAIL_DIFF)
- `apps/api/response_composers/ex2_limit_find_composer.py`
- `apps/api/response_composers/ex2_detail_composer.py`
- `apps/api/response_composers/ex3_compare_composer.py`
- `apps/api/response_composers/ex4_eligibility_composer.py`

All already call `display_coverage_name()` → normalization applied automatically.

---

## Normalization Examples

### Basic Space Removal
```
"암 진단비" → "암진단비"
"뇌 출혈 진단비" → "뇌출혈진단비"
"급성 심근경색 진단비" → "급성심근경색진단비"
```

### Trim and Multiple Spaces
```
"  암진단비  " → "암진단비"
"  암   진단비  " → "암진단비"
"\t암\t진단비\t" → "암진단비"
```

### Separator Removal
```
"암-진단비" → "암진단비"
"암_진단비" → "암진단비"
"암/진단비" → "암진단비"
"뇌 출혈-진단비" → "뇌출혈진단비"
```

### coverage_code Rejection
```
"A4200_1" → "" (rejected → fallback to "해당 담보")
"B1100_2" → "" (rejected → fallback to "해당 담보")
```

### Parentheses Preservation
```
"암진단비(유사암 제외)" → "암진단비(유사암제외)"
"뇌출혈진단비(뇌졸중 포함)" → "뇌출혈진단비(뇌졸중포함)"
```

Note: Spaces inside parentheses are also removed (between Korean characters).

---

## Test Coverage

### Unit Tests

**File:** `tests/test_coverage_name_display_normalize.py` (17/17 passing)

**Test Classes:**
1. `TestNormalizeCoverageNameForDisplay` (9 tests)
   - Basic space removal
   - Trim and multiple spaces
   - Separator removal
   - coverage_code rejection
   - Parentheses preservation
   - Percentage preservation
   - Empty/too-short handling
   - Invalid characters removal
   - Mixed separators

2. `TestDisplayCoverageName` (7 tests)
   - Basic normalization applied
   - No spaces in output
   - coverage_code rejection
   - None/empty fallback
   - Parentheses handling
   - Multiple input consistency

3. `TestRegressionNoCoverageCodeExposure` (1 test)
   - coverage_code never returned

### Regression Tests

**Updated tests:**
- `test_ex3_bubble_markdown_step_next_82.py::test_bubble_markdown_section1_summary`
  - Updated to expect `"암진단비(유사암제외)"` (normalized)
  - Previously expected `"암진단비(유사암 제외)"` (with space)

**All passing:**
- 55/55 total tests (EX2/EX3/EX4 + new normalization tests)
- No regressions

---

## Impact Analysis

### Before (Problems)

**Inconsistent Display:**
```
Title: "삼성화재의 암 진단비 보장한도 차이"
Summary: "암진단비는..."
Bubble: "선택한 담보: 암 진단 비"
```

**User Confusion:**
- Same coverage appears with different spacing
- Difficult to search/compare
- Unprofessional appearance

### After (Fixed)

**Consistent Display:**
```
Title: "삼성화재의 암진단비 보장한도 차이"
Summary: "암진단비는..."
Bubble: "선택한 담보: 암진단비"
```

**Benefits:**
- 100% consistent presentation
- Professional appearance
- Easier to search/compare
- Reduced UX confusion

---

## SSOT Priority (Display Name Selection)

When displaying coverage_name, use this priority:

1. `card.customer_view.coverage_name` (if exists)
2. `card.coverage_name_canonical` (slim card)
3. `request.coverage_names[0]` (user input, **normalized**)
4. Fallback: `"해당 담보"`

**Critical:** Step 3 MUST go through `normalize_coverage_name_for_display()`.

---

## Migration Notes

### Breaking Changes

None - enhancement only.

### Behavior Changes

**Display strings now normalized:**
- Before: `"암 진단비(유사암 제외)"` (preserved as-is)
- After: `"암진단비(유사암제외)"` (normalized)

**Test updates required:**
- Tests expecting specific spacing must be updated to expect normalized form
- Example: `test_ex3_bubble_markdown_step_next_82.py` updated

---

## Future Enhancements

### Potential Additions

1. **Alias Mapping** (optional)
   - `"암보험금"` → `"암진단비"`
   - `"뇌졸중"` → `"뇌출혈진단비"`
   - Could be added to normalization function

2. **Coverage Name Registry** (optional)
   - Canonical list of allowed coverage names
   - Validation against registry
   - Fuzzy matching for typos

3. **Synonym Handling** (optional)
   - Multiple names → single canonical name
   - Backend mapping without UI changes

---

## Definition of Done

✅ `"암 진단비"` input → always displays as `"암진단비"`
✅ coverage_code UI exposure = 0%
✅ All display paths use `display_coverage_name()`
✅ Unit tests passing (17/17)
✅ Regression tests passing (55/55)
✅ No spacing variations in title/summary/sections/bubble
✅ Deterministic only (NO LLM)

---

## Related Steps

- **STEP NEXT-81B**: Coverage code exposure prevention (foundation)
- **STEP NEXT-88**: View layer expression rules (insurer formatting)
- **STEP NEXT-89**: View layer sanitization (coverage_code removal)
- **STEP NEXT-93**: Coverage name normalization (this step)

---

**Created:** 2026-01-03
**STEP:** NEXT-93
**Status:** ✅ LOCKED
**Impact:** View Layer ONLY (display strings)
