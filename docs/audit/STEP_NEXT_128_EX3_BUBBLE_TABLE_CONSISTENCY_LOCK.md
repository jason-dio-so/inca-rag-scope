# STEP NEXT-128: EX3_COMPARE Bubble ↔ Table Consistency (FINAL FIX)

**Status**: ✅ LOCKED
**Date**: 2026-01-04
**Scope**: ViewModel Layer ONLY (API Response Composer - Bubble Generation)

---

## 목적 (WHY)

현재 **EX3_COMPARE 화면에서 좌측 말풍선(bubble_markdown)**과
우측 비교 테이블(comparison_table)이 서로 **반대 내용**을 말하는 심각한 UX 버그가 존재한다.

### Evidence (현재 버그)

**테이블 (STEP NEXT-127 - CORRECT)**:
- Samsung → "보험기간 중 1회" (지급 한도/횟수 기준)
- Meritz → "3천만원" (보장금액 기준)

**말풍선 (STEP NEXT-126 hardcoded - WRONG)**:
- Samsung = "정해진 금액을 지급하는 구조" (❌ 완전히 반대)
- Meritz = "지급 횟수 기준으로 보장이 정의됩니다" (❌ 완전히 반대)

### 사용자 경험 (UX Impact)

사용자가 오른쪽 표를 보고:
> "아, Samsung은 한도 구조구나"

왼쪽 말풍선을 보고:
> "어? 말풍선은 Samsung이 정액이라고 하는데? 무슨 말이 맞지?"

→ **신뢰도 0%, 혼란 100%**

---

## 목표 (GOAL)

**"말풍선을 테이블의 사실에 100% 종속"**시킨다.

**핵심 원칙**:
> "Bubble is NOT an explanation - it RE-READS the table in natural language"

말풍선은 "설명"이 아니라, 이미 그려진 테이블을 말로 다시 읽어주는 역할만 한다.

---

## 적용 범위 (SCOPE)

### ✅ 수정 대상
- `apps/api/response_composers/ex3_compare_composer.py`
  - `_build_bubble_markdown`: Table-driven bubble generation

### ❌ 수정 금지
- Intent routing
- EX2 / EX4 composers
- Frontend templates (STEP NEXT-126 frontend override still works)
- Table structure (STEP NEXT-127 table logic unchanged)
- Bubble 6-line format (STEP NEXT-126 format preserved)

---

## 구현 방식

### 1. Table = SSOT (Single Source of Truth)

Bubble content는 반드시 **comparison_table.rows**에서 읽는다.

**특히 "핵심 보장 내용" row가 기준**:
```json
{
  "rows": [
    ...
    {
      "cells": [
        {"text": "핵심 보장 내용"},
        {"text": "보험기간 중 1회"},  // Samsung (LIMIT)
        {"text": "3천만원"}            // Meritz (AMOUNT)
      ]
    }
  ]
}
```

---

### 2. Structure Detection (DETERMINISTIC)

보험사별 구조는 `cells.text`를 키워드 매칭으로 판별:

**LIMIT structure indicators**:
- "보험기간 중"
- "지급 한도"
- "횟수"
- "회"

**AMOUNT structure indicators**:
- "만원"
- "천만원"
- "원"

**Priority**: LIMIT > AMOUNT (둘 다 있으면 LIMIT 우선)

---

### 3. Bubble Template (LOCKED - 6 lines)

Format은 STEP NEXT-126과 동일하게 유지 (6 lines EXACTLY).

**단, insurer ↔ structure 매핑은 table 판독 결과로 결정**:

```markdown
{LIMIT insurer}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,
{AMOUNT insurer}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다.

**즉,**
- {LIMIT insurer}: 지급 조건·횟수(한도) 기준
- {AMOUNT insurer}: 지급 금액이 명확한 정액(보장금액) 기준
```

---

## Constitutional Rules (LOCKED)

### ✅ Allowed
- Read structure from comparison_table.rows (SSOT)
- Deterministic keyword matching
- 6-line format (STEP NEXT-126 preserved)
- Adapt insurer order based on table structure

### ❌ Forbidden
- Hardcoded insurer order assumptions (NO "Samsung always = amount")
- "일부 보험사는..." (STEP NEXT-123 absolute forbidden)
- Abstract/vague language
- New UX / new sections / new cards
- LLM usage
- Data inference
- Coverage_code / insurer_code based branching

---

## Implementation Evidence

### Modified Function

**`_build_bubble_markdown` (lines 436-557)**:

**Before** (STEP NEXT-126 - Hardcoded):
```python
# Always hardcoded:
# Insurer1 = amount, Insurer2 = limit
lines = [
    f"{insurer1_display}는 진단 시 **정해진 금액을 지급하는 구조**이고,",
    f"{insurer2_display}는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**",
    ...
]
```

**After** (STEP NEXT-128 - Table-driven):
```python
# Read from table (SSOT)
detail_row = find("핵심 보장 내용")
insurer1_structure = detect_structure(detail_row.cells[1].text)
insurer2_structure = detect_structure(detail_row.cells[2].text)

# Adapt bubble based on detected structure
if insurer1_structure == "LIMIT" and insurer2_structure == "AMOUNT":
    lines = [
        f"{insurer1_display}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,",
        f"{insurer2_display}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다.",
        ...
    ]
elif insurer1_structure == "AMOUNT" and insurer2_structure == "LIMIT":
    lines = [
        f"{insurer1_display}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의되고,",
        f"{insurer2_display}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의됩니다.",
        ...
    ]
```

**Function Signature Change**:
```python
# Before
def _build_bubble_markdown(insurers, insurer_display_names, display_name, comparison_data)

# After (STEP NEXT-128)
def _build_bubble_markdown(insurers, insurer_display_names, display_name, comparison_data, table_section)
```

---

## Contract Tests (7/7 PASS)

**Location**: `tests/test_step_next_128_ex3_bubble_table_consistency.py`

1. ✅ `test_ex3_bubble_samsung_limit_meritz_amount` **(CRITICAL)**
   - Samsung (limit) vs Meritz (amount) → bubble says Samsung = limit
2. ✅ `test_ex3_bubble_reversed_order`
   - Reversed order (meritz, samsung) → bubble adapts correctly
3. ✅ `test_ex3_bubble_always_6_lines` **(REGRESSION)**
   - Bubble is EXACTLY 6 lines (STEP NEXT-126 format preserved)
4. ✅ `test_ex3_bubble_no_ilbu_phrase` **(REGRESSION)**
   - NO "일부 보험사는..." (STEP NEXT-123 absolute lock)
5. ✅ `test_ex3_bubble_table_consistency_samsung_first` **(CRITICAL)**
   - Bubble ↔ Table 100% consistency verification
6. ✅ `test_ex3_table_unchanged` **(REGRESSION)**
   - Table structure unchanged (STEP NEXT-127 preserved)
7. ✅ `test_ex3_bubble_reproducibility` **(REGRESSION)**
   - Same input → same bubble (STEP NEXT-126 reproducibility)

---

## Verification Scenario (Manual)

**Query**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected Table** (STEP NEXT-127):
| 비교 항목 | 삼성화재 | 메리츠화재 |
|----------|---------|----------|
| 보장 정의 기준 | 지급 한도/횟수 기준 | 보장금액(정액) 기준 |
| 핵심 보장 내용 | 보험기간 중 1회 | 3천만원 |

**Expected Bubble** (STEP NEXT-128 - MUST MATCH TABLE):
```
삼성화재는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,
메리츠화재는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다.

**즉,**
- 삼성화재: 지급 조건·횟수(한도) 기준
- 메리츠화재: 지급 금액이 명확한 정액(보장금액) 기준
```

**⚠️ FAILURE CASE** (하나라도 반대로 나오면 실패):
- Bubble says "삼성화재는 진단 시 정해진 금액..." → ❌ FAIL (table says limit)
- Bubble says "메리츠화재는 보험기간 중..." → ❌ FAIL (table says amount)

---

## Definition of Done (DoD)

- ✅ EX3_COMPARE에서 bubble ↔ table 구조 불일치 0%
- ✅ Samsung (limit) vs Meritz (amount) → bubble correctly says Samsung = limit
- ✅ Same input → same bubble (reproducibility 100%)
- ✅ EX2 / EX4 화면 변화 없음
- ✅ 신규 UX 없음 (table-driven logic ONLY)
- ✅ Contract tests 7/7 PASS
- ✅ STEP NEXT-127 regression tests 8/8 PASS
- ✅ "왜 말이 다르지?"라는 사용자 의문 0%
- ✅ SSOT 문서 + CLAUDE.md 업데이트 완료

---

## Key Insight (STEP NEXT-128 Philosophy)

**Before** (STEP NEXT-126):
> "Bubble은 고정 템플릿이다 (재현성)"

**After** (STEP NEXT-128):
> "Bubble은 **Table을 읽는 고정 방식**이다 (재현성 + 정합성)"

STEP NEXT-126의 재현성 원칙은 유지하되, 내용을 table에 종속시킴으로써 **정합성**을 추가로 확보한다.

---

## 다음 단계 (STEP NEXT-129+)

**금지 사항 (ABSOLUTE)**:
- Hardcoded insurer order 재도입 (table-driven은 LOCKED)
- Bubble format 변경 (6 lines는 LOCKED)
- "일부 보험사는..." 재도입 (ABSOLUTE FORBIDDEN)

**개선 가능 영역**:
- Structure detection keyword 확장 (if new KPI types added)
- Fallback logic refinement (both same structure case)
- Coverage-specific bubble variation (maintaining table-driven principle)

---

**LOCKED**: 2026-01-04
**Review Required**: 새로운 EX3 bubble 요구사항 발생 시 이 문서를 먼저 확인
