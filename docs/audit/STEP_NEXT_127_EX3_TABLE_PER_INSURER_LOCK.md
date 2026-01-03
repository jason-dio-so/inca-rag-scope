# STEP NEXT-127: EX3_COMPARE Table Per-Insurer Cells + Meta (FINAL FIX)

**Status**: ✅ LOCKED
**Date**: 2026-01-04
**Scope**: ViewModel Layer ONLY (API Response Composer)

---

## 목표

EX3_COMPARE의 `comparison_table (INTEGRATED_COMPARE)`에서:
1. **보험사별 핵심 차이 (금액 vs 한도/횟수)**가 반드시 **rows.cells에 직접 표현**되도록 수정
2. **Per-insurer meta**: 각 cell이 자신의 보험사 refs만 보유 (cross-contamination = 0%)
3. **Structural basis**: "보장 정의 기준" row에서 limit vs amount 차이 반영

**핵심 원칙**:
- **같은 입력 → 같은 출력** (재현성)
- **표에서 구조 차이가 한눈에 드러남** (limit vs amount)
- **View Layer ONLY** (비즈니스 로직 변경 금지)

---

## Evidence (현재 버그)

### 증상
현재 EX3_COMPARE 응답 JSON에서:
- `rows[1].cells`: 삼성 "3,000만원", 메리츠 "3천만원" (둘 다 금액만 표시)
- 삼성의 **"보험기간 중 1회"**는 `rows[*].meta.kpi_summary.limit_summary`에만 존재
  - → UI에서 누락 (cells.text에 없음)
- 모든 row meta/evidence_refs/proposal_detail_ref가 `PD:samsung:*`로 고정
  - → **Per-insurer meta 결합 실패** (삼성 데이터가 공통으로 복사되는 버그)

### 근본 원인
`_build_table_section`에서:
1. **meta1만 사용**: 모든 row가 `meta1` (insurer1의 meta)만 사용 → meritz column에도 samsung refs 노출
2. **detail 우선순위 오류**: `get_definition_basis` 함수가 amount를 우선시 → limit이 있어도 amount만 표시
3. **Structural basis 단순화**: 둘 다 "정액 지급 방식"으로 동일하게 표시 → 구조 차이 드러나지 않음

---

## 구현 방식

### 1. Per-Insurer Meta (STEP NEXT-127 Rule 3)

**변경 전** (Bug):
```python
meta1 = EX3CompareComposer._build_row_meta(data1)

rows.append({
    "cells": [...],
    "meta": meta1  # ALL rows use meta1 ONLY
})
```

**변경 후** (Fixed):
```python
meta1 = EX3CompareComposer._build_row_meta(data1)
meta2 = EX3CompareComposer._build_row_meta(data2)

rows.append({
    "cells": [
        {"text": "비교 항목"},
        {"text": value1, "meta": meta1},  # Per-cell meta
        {"text": value2, "meta": meta2}   # Per-cell meta
    ]
})
```

**효과**:
- Samsung cell → `PD:samsung:*`, `EV:samsung:*`
- Meritz cell → `PD:meritz:*`, `EV:meritz:*`
- Cross-contamination = 0%

---

### 2. Structural Basis + Detail (STEP NEXT-127 Rule 1 & 2)

**Priority (LOCKED)**:
1. If `limit exists` → basis = "지급 한도/횟수 기준", detail = limit
2. Elif `amount != "명시 없음"` → basis = "보장금액(정액) 기준", detail = amount
3. Else → basis = "표현 없음", detail = None

**변경 전** (Bug):
```python
def get_definition_basis(amount, limit, payment):
    if amount != "명시 없음":
        return "정액 지급 방식", amount  # Amount first (WRONG)
    elif limit:
        return "지급 한도 기준", limit
```

**변경 후** (Fixed):
```python
def get_definition_basis_and_detail(amount, limit, payment):
    if limit:  # Limit FIRST (priority)
        return "지급 한도/횟수 기준", limit
    elif amount != "명시 없음":
        return "보장금액(정액) 기준", amount
    else:
        return "표현 없음", None
```

**효과**:
- Samsung (limit=있음, amount=있음) → "지급 한도/횟수 기준", "보험기간 중 1회"
- Meritz (limit=없음, amount=있음) → "보장금액(정액) 기준", "3천만원"
- **Structural difference visible in table**

---

### 3. Table Structure (LOCKED)

**행 구성** (3 rows, FIXED):
1. **보장 정의 기준** (per-insurer basis)
   - Samsung: "지급 한도/횟수 기준"
   - Meritz: "보장금액(정액) 기준"
2. **핵심 보장 내용** (limit or amount per insurer)
   - Samsung: "보험기간 중 1회"
   - Meritz: "3천만원"
3. **지급유형** (payment_type)
   - Samsung: "정액형"
   - Meritz: "정액형"

**Row Name Change**:
- "구체 내용" → **"핵심 보장 내용"** (more specific, customer-friendly)

---

## Constitutional Rules (LOCKED)

### ✅ Allowed
- Per-cell meta (each cell carries its own insurer's refs)
- Limit priority over amount (structural comparison purpose)
- View layer modification ONLY (ViewModel composition)
- Deterministic logic

### ❌ Forbidden
- Business logic change (extract/normalize 자체 의미 변경)
- LLM usage
- Judgment / recommendation
- Insurer code exposure (display names ONLY)
- Meta sharing across insurers (samsung refs in meritz cell = 0%)

---

## Contract Tests (8/8 PASS)

**Location**: `tests/test_step_next_127_ex3_table_per_insurer_cells.py`

1. ✅ `test_ex3_table_samsung_limit_shown_in_cells`
   - Samsung limit ("보험기간 중 1회") appears in cells.text
2. ✅ `test_ex3_table_meritz_amount_shown_in_cells`
   - Meritz amount ("3천만원") appears in cells.text
3. ✅ `test_ex3_table_structural_basis_different_per_insurer`
   - "보장 정의 기준" row shows DIFFERENT basis (한도 vs 금액)
4. ✅ `test_ex3_table_no_samsung_refs_in_meritz_cells` **CRITICAL**
   - NO samsung refs in meritz cells (PD:samsung:*, EV:samsung:* = 0%)
5. ✅ `test_ex3_table_meritz_refs_present`
   - Meritz cells contain meritz refs (PD:meritz:*, EV:meritz:*)
6. ✅ `test_ex3_table_samsung_refs_present`
   - Samsung cells contain samsung refs (PD:samsung:*, EV:samsung:*)
7. ✅ `test_ex3_bubble_unchanged` **(REGRESSION)**
   - STEP NEXT-126 fixed bubble template preserved
8. ✅ `test_ex3_no_coverage_code_exposure` **(REGRESSION)**
   - NO coverage_code (A4200_1) in user-facing text

---

## Verification Scenario (Manual)

**Query**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected Table** (3 rows):

| 비교 항목 | 삼성화재 | 메리츠화재 |
|----------|---------|----------|
| 보장 정의 기준 | 지급 한도/횟수 기준 | 보장금액(정액) 기준 |
| 핵심 보장 내용 | 보험기간 중 1회 | 3천만원 |
| 지급유형 | 정액형 | 정액형 |

**Expected Meta**:
- Samsung column cells → `PD:samsung:A4200_1`, `EV:samsung:A4200_1:*`
- Meritz column cells → `PD:meritz:A4200_1`, `EV:meritz:A4200_1:*`
- NO cross-contamination

**DevTools JSON Verification**:
```json
{
  "rows": [
    {
      "cells": [
        {"text": "보장 정의 기준"},
        {"text": "지급 한도/횟수 기준", "meta": {...samsung_refs...}},
        {"text": "보장금액(정액) 기준", "meta": {...meritz_refs...}}
      ]
    },
    {
      "cells": [
        {"text": "핵심 보장 내용"},
        {"text": "보험기간 중 1회", "meta": {...samsung_refs...}},
        {"text": "3천만원", "meta": {...meritz_refs...}}
      ]
    }
  ]
}
```

---

## Definition of Done (DoD)

- ✅ EX3 table에서 "한도 vs 금액" 구조 차이가 cells로 드러남
- ✅ Per-insurer refs 섞이지 않음 (samsung refs in meritz column = 0%)
- ✅ Samsung limit ("보험기간 중 1회") cells.text에 직접 표시
- ✅ Meritz amount ("3천만원") cells.text에 직접 표시
- ✅ "보장 정의 기준" row에서 보험사별 구조 차이 표시
- ✅ Contract tests 8/8 PASS
- ✅ EX2/EX4 회귀 없음 (EX2 113 tests: 10/10 PASS)
- ✅ SSOT 문서 + CLAUDE.md 업데이트 완료

---

## Implementation Evidence

### Modified Files (2)

1. **`apps/api/response_composers/ex3_compare_composer.py`**
   - `_build_table_section`: Per-insurer cells + meta (lines 260-362)
   - `get_definition_basis_and_detail`: Limit priority (lines 302-316)
   - `_build_kpi_section`: None handling fix (lines 249-252)
   - Row structure: 3 rows (보장 정의 기준, 핵심 보장 내용, 지급유형)

2. **`tests/test_step_next_127_ex3_table_per_insurer_cells.py`** (NEW)
   - 8 contract tests (all PASS)

### Test Results

```bash
$ python -m pytest tests/test_step_next_127_ex3_table_per_insurer_cells.py -v
============================= test session starts ==============================
collected 8 items

test_ex3_table_samsung_limit_shown_in_cells PASSED         [ 12%]
test_ex3_table_meritz_amount_shown_in_cells PASSED         [ 25%]
test_ex3_table_structural_basis_different_per_insurer PASSED [ 37%]
test_ex3_table_no_samsung_refs_in_meritz_cells PASSED      [ 50%]
test_ex3_table_meritz_refs_present PASSED                  [ 62%]
test_ex3_table_samsung_refs_present PASSED                 [ 75%]
test_ex3_bubble_unchanged PASSED                           [ 87%]
test_ex3_no_coverage_code_exposure PASSED                  [100%]

============================== 8 passed in 0.02s ===============================
```

**Regression Tests**:
```bash
$ python -m pytest tests/test_step_next_113_ex2_chatgpt_ux.py -v
============================== 10 passed in 0.02s ===============================
```

---

## 다음 단계 (STEP NEXT-128+)

**금지 사항 (ABSOLUTE)**:
- Meta 공유 재도입 (per-cell meta는 LOCKED)
- Amount 우선순위 (limit priority는 LOCKED)
- "구체 내용" 행 이름 변경 ("핵심 보장 내용"으로 LOCKED)

**개선 가능 영역**:
- UI rendering optimization (frontend table display)
- Additional row types (if needed for new comparison scenarios)
- Coverage-specific basis detection (currently generic)

---

**LOCKED**: 2026-01-04
**Review Required**: 새로운 EX3 table 요구사항 발생 시 이 문서를 먼저 확인
