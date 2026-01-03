# STEP NEXT-82 — EX3_COMPARE Bubble Markdown Enhancement

**Status**: ✅ COMPLETE
**Date**: 2026-01-02
**Purpose**: Enhance EX3_COMPARE bubble_markdown to provide comprehensive customer-facing summaries

---

## Objective

Enhance the **central chat bubble markdown** (`bubble_markdown`) in EX3_COMPARE responses to deliver immediate, actionable insights to customers without requiring table interaction.

- **NO UI changes** (backend-only enhancement)
- **Deterministic only** (NO LLM)
- **Customer-friendly** summary (NO coverage_code exposure)

---

## Bubble Markdown Format (LOCKED)

### 4-Section Structure

```markdown
## 핵심 요약
- 선택한 보험사: {insurer1}, {insurer2}
- 비교 대상 담보: {coverage_display_name}
- 기준 문서: 가입설계서

## 한눈에 보는 결론
- 보장금액: {공통/상이 요약}
- 지급유형: {정액형/일당형/혼합 등}
- 주요 차이: {있음/없음 + 한 줄 요약}

## 세부 비교 포인트
- {insurer1}: {핵심 특징 1줄}
- {insurer2}: {핵심 특징 1줄}

## 유의사항
- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

---

## Data Mapping Rules

| Section | Data Source |
|---------|-------------|
| **선택한 보험사** | `insurers` parameter (e.g., ["samsung", "meritz"]) |
| **비교 대상 담보** | `coverage_name_canonical` → `display_coverage_name()` (NO code) |
| **보장금액 요약** | `comparison_data[insurer]["amount"]` |
| **지급유형** | `kpi_summary.payment_type` (`UNKNOWN` → "표현 없음") |
| **주요 차이** | `kpi_condition` (waiting_period / reduction / exclusion) |
| **세부 특징** | `amount` + `payment_type` + `limit_summary` (max 3) |

---

## Constitutional Rules (Hard Stop)

1. ❌ **NO coverage_code exposure** (e.g., `A4200_1`)
2. ❌ **NO raw_text** in bubble (refs only)
3. ❌ **NO LLM usage** (deterministic only)
4. ✅ **4 sections MANDATORY** (핵심 요약, 한눈에 보는 결론, 세부 비교 포인트, 유의사항)
5. ✅ **Customer-facing language** (NO internal jargon)
6. ✅ **Deterministic logic** (pattern matching, NOT inference)

---

## Implementation

### File Modified
- `apps/api/response_composers/ex3_compare_composer.py:360-501`

### Method Updated
- `EX3CompareComposer._build_bubble_markdown()`

### Key Changes
1. **Replaced old 5-section format** with new 4-section format
2. **Enhanced Section 1 (핵심 요약)**:
   - Lists selected insurers explicitly
   - Shows coverage display name (NO code)
   - States data source ("가입설계서")
3. **Enhanced Section 2 (한눈에 보는 결론)**:
   - Amount comparison (공통/상이)
   - Payment type (정액형/일당형/혼합)
   - Major differences summary (대기기간/감액조건/면책조건)
4. **Enhanced Section 3 (세부 비교 포인트)**:
   - Per-insurer feature summary (max 3 features)
   - Includes amount + payment type + limit_summary
   - Fallback to "가입설계서 기준 보장" if no KPI
5. **Simplified Section 4 (유의사항)**:
   - Disclaimers for contract terms
   - Directs to table for detailed comparison

---

## Validation

### Test Suite
- `tests/test_ex3_bubble_markdown_step_next_82.py`
- **10 test cases** covering:
  - 4-section structure enforcement
  - coverage_code exposure prevention
  - Section content verification
  - Condition difference detection
  - UNKNOWN payment_type handling
  - Deterministic/NO LLM validation
  - Graceful KPI fallback

### Manual Test
- `tests/manual_test_ex3_bubble_step_next_82.py`
- Realistic scenario with KPI summary/condition data

### Results
```
✓ 10 tests PASSED
✓ coverage_code exposure: 0
✓ raw_text in bubble: 0
✓ UNKNOWN exposure: 0
✓ Deterministic: True
✓ LLM used: False
```

---

## Example Output

### Input
```python
insurers = ["samsung", "meritz"]
coverage_name = "암진단비(유사암 제외)"
comparison_data = {
    "samsung": {
        "amount": "3000만원",
        "payment_type": "정액형",
        "kpi_summary": {"limit_summary": "1회한 지급"},
        "kpi_condition": {"waiting_period": "90일"}
    },
    "meritz": {
        "amount": "5000만원",
        "payment_type": "정액형",
        "kpi_summary": {"limit_summary": "1회한 지급"},
        "kpi_condition": {"waiting_period": "90일", "reduction_condition": "1년 50%"}
    }
}
```

### Output
```markdown
## 핵심 요약
- 선택한 보험사: samsung, meritz
- 비교 대상 담보: 암진단비(유사암 제외)
- 기준 문서: 가입설계서

## 한눈에 보는 결론

- 보장금액: 상이 (samsung 3000만원, meritz 5000만원)
- 지급유형: 정액형
- 주요 차이: 있음 (감액조건 차이 확인)

## 세부 비교 포인트

- samsung: 보장금액 3000만원, 정액형, 1회한 지급
- meritz: 보장금액 5000만원, 정액형, 1회한 지급

## 유의사항

- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

---

## Impact Assessment

### What Changed
- ✅ `bubble_markdown` content **significantly enhanced**
- ✅ Customer can immediately understand comparison without scrolling

### What Stayed Same
- ✅ EX3_COMPARE schema (SSOT: `docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md`)
- ✅ Table structure (columns, rows, meta)
- ✅ KPI section structure
- ✅ refs-based evidence loading
- ✅ UI rendering logic

### Backward Compatibility
- ✅ **100% compatible** (bubble_markdown is a string field, no schema change)
- ✅ UI will render new markdown automatically

---

## DoD (Definition of Done)

- [x] `_build_bubble_markdown()` method updated with LOCKED format
- [x] 10 test cases PASSED
- [x] Manual test confirms realistic output
- [x] coverage_code exposure: 0
- [x] raw_text in bubble: 0
- [x] UNKNOWN display as "표현 없음"
- [x] Deterministic logic (NO LLM)
- [x] Documentation complete (`STEP_NEXT_82_EX3_BUBBLE_MARKDOWN_LOCK.md`)

---

## Next Steps

### Immediate
- None (STEP NEXT-82 is complete)

### Future Enhancements
- **STEP NEXT-83** (if needed): Multi-insurer (3+) bubble_markdown support
- **STEP NEXT-84** (if needed): EX2_LIMIT_FIND bubble_markdown enhancement

---

**Version**: STEP NEXT-82
**Author**: Backend Team
**Reviewed**: 2026-01-02
**Status**: ✅ SSOT LOCKED
