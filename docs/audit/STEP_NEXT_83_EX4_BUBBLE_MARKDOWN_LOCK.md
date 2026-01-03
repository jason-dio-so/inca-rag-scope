# STEP NEXT-83 — EX4_ELIGIBILITY Bubble Markdown Enhancement

**Status**: ✅ COMPLETE
**Date**: 2026-01-02
**Purpose**: Align EX4_ELIGIBILITY bubble_markdown UX with EX3_COMPARE quality level

---

## Objective

Enhance the **central chat bubble markdown** (`bubble_markdown`) in EX4_ELIGIBILITY responses to match EX3_COMPARE's customer-facing quality.

- **NO UI changes** (backend-only enhancement)
- **Deterministic only** (NO LLM, NO scoring, NO inference)
- **Customer-friendly** summary (NO coverage_code exposure)
- **4-section structure** (aligned with EX3)

---

## Bubble Markdown Format (LOCKED)

### 4-Section Structure (Aligned with EX3)

```markdown
## 핵심 요약
이 비교는 {N}개 보험사 [**{coverage_name}**] **{subtype_keyword}**에 대해
가입설계서 및 약관 기준으로 보장 가능 여부를 확인한 결과입니다.

## 한눈에 보는 결론

- {conclusion_summary}
- {evaluation_summary}

## 보험사별 판단 요약

- **보장 가능**: {O_insurers}
- **감액 조건 존재**: {△_insurers}
- **보장 제외**: {X_insurers}
- **판단 근거 없음**: {Unknown_insurers}

## 유의사항

※ 본 결과는 가입설계서 기준 요약이며,
세부 조건(감액·면책·대기기간)은 상품 약관에 따라 달라질 수 있습니다.
```

---

## Data Mapping Rules

### Section 1: 핵심 요약

| Field | Data Source | Example |
|-------|-------------|---------|
| 보험사 수 | `len(eligibility_data)` | "3개 보험사" |
| Coverage Name | `coverage_display_name` (optional) | "암진단비(유사암 제외)" |
| Subtype | `subtype_keyword` | "제자리암" |
| Data Source | Static | "가입설계서 및 약관 기준" |

**Rules**:
- ❌ NEVER expose `coverage_code`
- ✅ Use `display_coverage_name()` helper (auto-sanitizes)
- ✅ Coverage name is optional (fallback: omit if not provided)

---

### Section 2: 한눈에 보는 결론

| Decision | Conclusion Summary | Example |
|----------|-------------------|---------|
| RECOMMEND | "보장 가능한 보험사가 다수입니다" | O majority |
| NOT_RECOMMEND | "보장되지 않는 보험사가 다수입니다" | X majority |
| NEUTRAL | "보험사별 보장 여부가 갈립니다" | Mixed O/X/△ |

**Data Source**: `evaluation_section["overall_evaluation"]["decision"]`

**Rules**:
- ✅ Convert decision enum to customer-friendly text
- ❌ NO emojis in conclusion bullets (✅❌⚠️ forbidden here)
- ✅ Include evaluation summary from decision logic

---

### Section 3: 보험사별 판단 요약

**Format**: Group insurers by status (O/△/X/Unknown)

| Status | Label | Example |
|--------|-------|---------|
| O | **보장 가능** | samsung, meritz |
| △ | **감액 조건 존재** | hanwha |
| X | **보장 제외** | kb |
| Unknown | **판단 근거 없음** | lotte |

**Data Source**: `eligibility_data` (group by `status` field)

**Rules**:
- ✅ Show only non-empty groups (omit if count = 0)
- ✅ List insurers comma-separated
- ✅ Order: O → △ → X → Unknown

---

### Section 4: 유의사항

**Fixed content** (do not modify):
```markdown
※ 본 결과는 가입설계서 기준 요약이며,
세부 조건(감액·면책·대기기간)은 상품 약관에 따라 달라질 수 있습니다.
```

---

## Constitutional Rules (Hard Stop)

1. ❌ **NO coverage_code exposure** (e.g., `A4200_1`)
2. ❌ **NO raw_text in bubble** (refs only)
3. ❌ **NO LLM usage** (deterministic only)
4. ❌ **NO scoring/weighting/inference**
5. ❌ **NO emotional phrases** ("좋아 보임", "합리적")
6. ✅ **4 sections MANDATORY** (핵심 요약, 한눈에 보는 결론, 보험사별 판단 요약, 유의사항)
7. ✅ **Customer-facing language** (NO internal jargon)
8. ✅ **Deterministic pattern matching** ONLY

---

## Implementation

### Files Modified
- `apps/api/response_composers/ex4_eligibility_composer.py:23-27` (imports)
- `apps/api/response_composers/ex4_eligibility_composer.py:47-154` (compose method)
- `apps/api/response_composers/ex4_eligibility_composer.py:360-427` (bubble method)

### Key Changes

1. **Added imports**:
   ```python
   from apps.api.response_composers.utils import display_coverage_name, sanitize_no_coverage_code
   ```

2. **Updated compose() signature**:
   - Added `coverage_name` parameter (optional)
   - Added `coverage_code` parameter (optional, NEVER exposed)
   - Added final sanitization pass (title, summary, bubble, sections)

3. **Enhanced _build_bubble_markdown()**:
   - **Section 1 (핵심 요약)**: Added coverage name context
   - **Section 2 (한눈에 보는 결론)**: Natural language decision summary (NO emojis)
   - **Section 3 (보험사별 판단 요약)**: Grouped insurers by status (O/△/X/Unknown)
   - **Section 4 (유의사항)**: Simplified disclaimers

4. **Removed old format**:
   - ❌ Emoji-heavy decision display ("✅ 추천", "❌ 비추천")
   - ❌ Distribution count bullets ("✅ **보장 가능(O)**: 2개 보험사")
   - ❌ Evidence guide section (redundant with table)

---

## Validation

### Test Suite
- `tests/test_ex4_bubble_markdown_step_next_83.py`
- **12 test cases** covering:
  - 4-section structure enforcement
  - coverage_code exposure prevention
  - Section content verification
  - Decision type handling (RECOMMEND / NOT_RECOMMEND / NEUTRAL)
  - Insurer grouping by status
  - NO emojis in conclusion
  - Deterministic/NO LLM validation
  - Coverage name context
  - Unknown status handling

### Manual Test
- `tests/manual_test_ex4_bubble_step_next_83.py`
- Realistic scenario with O/△/X statuses

### Results
```
✓ 12 tests PASSED
✓ 9 regression tests PASSED (test_ex4_overall_evaluation_contract.py)
✓ coverage_code exposure: 0
✓ raw_text in bubble: 0
✓ evidence_snippet in bubble: 0
✓ Deterministic: True
✓ LLM used: False
✓ NO emojis in conclusion: True
```

---

## Example Output

### Input
```python
insurers = ["samsung", "meritz", "hanwha"]
subtype_keyword = "제자리암"
coverage_name = "암진단비(유사암 제외)"
eligibility_data = [
    {"insurer": "samsung", "status": "O", "evidence_type": "정의", ...},
    {"insurer": "meritz", "status": "X", "evidence_type": "면책", ...},
    {"insurer": "hanwha", "status": "△", "evidence_type": "감액", ...}
]
```

### Output
```markdown
## 핵심 요약

이 비교는 3개 보험사 **암진단비(유사암 제외)** **제자리암**에 대해
가입설계서 및 약관 기준으로 보장 가능 여부를 확인한 결과입니다.

## 한눈에 보는 결론

- 보험사별 보장 여부가 갈립니다
- 장단점 혼재로 우열 판단이 어렵습니다

## 보험사별 판단 요약

- **보장 가능**: samsung
- **감액 조건 존재**: hanwha
- **보장 제외**: meritz

## 유의사항

※ 본 결과는 가입설계서 기준 요약이며,
세부 조건(감액·면책·대기기간)은 상품 약관에 따라 달라질 수 있습니다.
```

---

## Impact Assessment

### What Changed
- ✅ `bubble_markdown` content **significantly enhanced**
- ✅ 4-section structure (aligned with EX3)
- ✅ Natural language conclusion (NO emojis in bullets)
- ✅ Insurer grouping by status
- ✅ Coverage name context (optional)

### What Stayed Same
- ✅ EX4_ELIGIBILITY schema (SSOT: `STEP_NEXT_79_EX4_OVERALL_EVALUATION_LOCK.md`)
- ✅ Matrix table structure
- ✅ Overall evaluation section
- ✅ Decision logic (RECOMMEND / NOT_RECOMMEND / NEUTRAL)
- ✅ UI rendering logic

### Backward Compatibility
- ✅ **100% compatible** (bubble_markdown is a string field, no schema change)
- ✅ UI will render new markdown automatically
- ✅ Optional `coverage_name`/`coverage_code` parameters (backward compatible)

---

## Before vs After Comparison

### Before (STEP NEXT-81B)
```markdown
# 제자리암 보장 가능 여부 요약

## 종합 평가

**⚠️ 유보**

## 보험사별 분포

- ✅ **보장 가능(O)**: 1개 보험사
- ❌ **면책(X)**: 1개 보험사
- ⚠️ **감액(△)**: 1개 보험사

## 근거 확인

상세 근거는 **ⓘ 아이콘** 및 비교표에서 확인하실 수 있습니다.

## 유의사항

- O: 보장 가능, X: 면책, △: 감액, Unknown: 판단 근거 없음
- 본 비교는 약관 및 상품요약서 기준이며, 실제 보장 여부는 원문 확인이 필요합니다.
```

### After (STEP NEXT-83)
```markdown
## 핵심 요약

이 비교는 3개 보험사 **암진단비(유사암 제외)** **제자리암**에 대해
가입설계서 및 약관 기준으로 보장 가능 여부를 확인한 결과입니다.

## 한눈에 보는 결론

- 보험사별 보장 여부가 갈립니다
- 장단점 혼재로 우열 판단이 어렵습니다

## 보험사별 판단 요약

- **보장 가능**: samsung
- **감액 조건 존재**: hanwha
- **보장 제외**: meritz

## 유의사항

※ 본 결과는 가입설계서 기준 요약이며,
세부 조건(감액·면책·대기기간)은 상품 약관에 따라 달라질 수 있습니다.
```

### Key Improvements
1. **Clearer context** (insurance count, coverage name)
2. **Natural language** conclusion (NO emoji-heavy bullets)
3. **Actionable grouping** (insurers by status, not just counts)
4. **Simpler disclaimers** (concise, focused)

---

## DoD (Definition of Done)

- [x] `_build_bubble_markdown()` method updated with LOCKED format
- [x] 4-section structure implemented
- [x] coverage_name parameter support added
- [x] coverage_code sanitization applied
- [x] 12 test cases PASSED
- [x] 9 regression tests PASSED (NO regressions)
- [x] Manual test confirms realistic output
- [x] coverage_code exposure: 0 instances
- [x] raw_text in bubble: 0 instances
- [x] NO emojis in conclusion
- [x] Deterministic logic (NO LLM)
- [x] Documentation complete

---

## Next Steps

### Immediate
- None (STEP NEXT-83 is complete)

### Future Enhancements
- **STEP NEXT-84** (if needed): EX2_LIMIT_FIND bubble_markdown enhancement
- **STEP NEXT-85** (if needed): Multi-coverage EX4 scenarios

---

**Version**: STEP NEXT-83
**Author**: Backend Team
**Reviewed**: 2026-01-02
**Status**: ✅ SSOT LOCKED
