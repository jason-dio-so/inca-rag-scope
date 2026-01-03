# STEP NEXT-112B: EX3_COMPARE Execution Lock (Backend Data Structure)

**Status**: ✅ COMPLETE
**Date**: 2026-01-04
**Parent**: STEP NEXT-112 (Comparison-First UX Lock)

---

## Problem Statement

STEP NEXT-112 redesigned the **bubble_markdown format** (left chat bubble), but the **actual comparison table structure** (right dock, sections array) was NOT changed.

**Root Cause**:
1. ❌ `summary_bullets` still contained abstract text (not structural comparison)
2. ❌ Table columns were `["구분", insurer1, insurer2]` (generic)
3. ❌ Table rows were `[보장금액, 보험료, 납입/만기, 지급유형]` (feature list, NOT comparison)

**Result**: Frontend received the OLD structure → rendered the OLD UI → **no visible change**.

---

## Solution (LOCKED)

### 1. `summary_bullets` — Structural Comparison (NOT Abstract)

**Before** ❌:
```json
"summary_bullets": [
  "2개 보험사의 암진단비를 비교했습니다",
  "가입설계서 기준 비교입니다"
]
```

**After** ✅:
```json
"summary_bullets": [
  "메리츠화재는 정액 지급 방식으로 보장이 정의되고, 삼성화재는 지급 한도 기준으로 보장이 정의됩니다",
  "가입설계서 기준 비교입니다"
]
```

**Rules**:
- ❌ NO abstract patterns ("N개 보험사를 비교했습니다")
- ✅ Explicit structural difference (insurer names + basis)
- ✅ Pattern: "{Insurer1}는 {basis1}으로 보장이 정의되고, {Insurer2}는 {basis2}으로 보장이 정의됩니다"

---

### 2. Table Section — Comparison-First Structure

**Before** ❌:
```json
{
  "kind": "comparison_table",
  "title": "암진단비 비교표",
  "columns": ["구분", "samsung", "meritz"],
  "rows": [
    {"cells": [{"text": "보장금액"}, {"text": "3000만원"}, {"text": "5000만원"}]},
    {"cells": [{"text": "보험료"}, {"text": "명시 없음"}, {"text": "명시 없음"}]},
    {"cells": [{"text": "납입/만기"}, {"text": "20년납/80세만기"}, {"text": "20년납/80세만기"}]},
    {"cells": [{"text": "지급유형"}, {"text": "정액형"}, {"text": "정액형"}]}
  ]
}
```

**Problems**:
- Columns use insurer codes (`samsung`, `meritz`) instead of display names
- Rows list features (보장금액, 보험료, 납입/만기, 지급유형) but NOT structural comparison
- NO "보장 정의 기준" row (the KEY insight)

**After** ✅:
```json
{
  "kind": "comparison_table",
  "title": "암진단비(유사암제외) 보장 기준 비교",
  "columns": ["비교 항목", "메리츠화재", "삼성화재"],
  "rows": [
    {"cells": [{"text": "보장 정의 기준"}, {"text": "정액 지급 방식"}, {"text": "지급 한도 기준"}]},
    {"cells": [{"text": "구체 내용"}, {"text": "3천만원"}, {"text": "보험기간 중 1회"}]},
    {"cells": [{"text": "지급유형"}, {"text": "정액형"}, {"text": "정액형"}]}
  ]
}
```

**Rules**:
- ✅ Columns: `["비교 항목", insurer1_display, insurer2_display]`
- ✅ Row 1 (ALWAYS): 보장 정의 기준
- ✅ Row 2 (conditional): 구체 내용 (if details exist)
- ✅ Row 3 (conditional): 보장금액 (if NOT already in 구체 내용)
- ✅ Row 4 (ALWAYS): 지급유형

---

## Implementation

**File**: `apps/api/response_composers/ex3_compare_composer.py`

### Change 1: `summary_bullets` Construction

```python
# STEP NEXT-112B: Structural basis detection
def get_definition_basis(amount, limit, payment):
    if amount != "명시 없음":
        return "정액 지급 방식"
    elif limit:
        return "지급 한도 기준"
    elif payment != "UNKNOWN":
        return f"{payment} 방식"
    else:
        return "기본 보장 방식"

basis1 = get_definition_basis(amount1, limit1, payment1)
basis2 = get_definition_basis(amount2, limit2, payment2)

# Build structural summary
if basis1 == basis2:
    structural_summary = f"{insurer1_display}와 {insurer2_display}는 모두 {basis1}으로 보장이 정의됩니다"
else:
    structural_summary = (
        f"{insurer1_display}는 {basis1}으로 보장이 정의되고, "
        f"{insurer2_display}는 {basis2}으로 보장이 정의됩니다"
    )

summary_bullets = [structural_summary, "가입설계서 기준 비교입니다"]
```

### Change 2: `_build_table_section()` Redesign

```python
@staticmethod
def _build_table_section(insurers, comparison_data, coverage_name):
    # Use display names in columns
    columns = ["비교 항목", insurer1_display, insurer2_display]
    
    # Detect structural basis
    basis1, detail1 = get_definition_basis(amount1, limit1, payment1)
    basis2, detail2 = get_definition_basis(amount2, limit2, payment2)
    
    rows = []
    
    # Row 1: 보장 정의 기준 (ALWAYS)
    rows.append({
        "cells": [
            {"text": "보장 정의 기준"},
            {"text": basis1},
            {"text": basis2}
        ]
    })
    
    # Row 2: 구체 내용 (conditional)
    if detail1 or detail2:
        rows.append({
            "cells": [
                {"text": "구체 내용"},
                {"text": detail1 if detail1 else "-"},
                {"text": detail2 if detail2 else "-"}
            ]
        })
    
    # Row 3: 보장금액 (if NOT in 구체 내용)
    if not detail1 and not detail2:
        rows.append({
            "cells": [
                {"text": "보장금액"},
                {"text": amount1},
                {"text": amount2}
            ]
        })
    
    # Row 4: 지급유형 (ALWAYS)
    rows.append({
        "cells": [
            {"text": "지급유형"},
            {"text": payment1_display},
            {"text": payment2_display}
        ]
    })
    
    return {
        "kind": "comparison_table",
        "title": f"{coverage_name} 보장 기준 비교",
        "columns": columns,
        "rows": rows
    }
```

---

## Before/After Comparison

### API Response Structure

**Before** (STEP NEXT-77, feature-list style):
```json
{
  "kind": "EX3_COMPARE",
  "title": "삼성화재 vs 메리츠화재 암진단비 비교",
  "summary_bullets": [
    "2개 보험사의 암진단비를 비교했습니다",  // ❌ Abstract
    "가입설계서 기준 비교입니다"
  ],
  "sections": [
    {
      "kind": "comparison_table",
      "title": "암진단비 비교표",
      "columns": ["구분", "samsung", "meritz"],  // ❌ Insurer codes
      "rows": [
        // ❌ NO "보장 정의 기준" row
        {"cells": [{"text": "보장금액"}, ...]},
        {"cells": [{"text": "보험료"}, ...]},
        {"cells": [{"text": "납입/만기"}, ...]},
        {"cells": [{"text": "지급유형"}, ...]}
      ]
    }
  ]
}
```

**After** (STEP NEXT-112B, comparison-first style):
```json
{
  "kind": "EX3_COMPARE",
  "title": "메리츠화재 vs 삼성화재 암진단비(유사암제외) 비교",
  "summary_bullets": [
    "메리츠화재는 정액 지급 방식으로 보장이 정의되고, 삼성화재는 지급 한도 기준으로 보장이 정의됩니다",  // ✅ Structural comparison
    "가입설계서 기준 비교입니다"
  ],
  "sections": [
    {
      "kind": "comparison_table",
      "title": "암진단비(유사암제외) 보장 기준 비교",
      "columns": ["비교 항목", "메리츠화재", "삼성화재"],  // ✅ Display names
      "rows": [
        {"cells": [{"text": "보장 정의 기준"}, {"text": "정액 지급 방식"}, {"text": "지급 한도 기준"}]},  // ✅ NEW: Key insight
        {"cells": [{"text": "구체 내용"}, {"text": "3천만원"}, {"text": "보험기간 중 1회"}]},
        {"cells": [{"text": "지급유형"}, {"text": "정액형"}, {"text": "정액형"}]}
      ]
    }
  ]
}
```

---

## Test Results

**All 21 tests PASS**:
- `tests/test_step_next_112_ex3_comparison_first.py` (12 tests)
- `tests/test_ex3_compare_schema_contract.py` (9 tests)

**Key Test**: `test_no_abstract_evasive_summary`
```python
def test_no_abstract_evasive_summary():
    response = EX3CompareComposer.compose(...)
    
    bubble = response["bubble_markdown"]
    assert "일부 보험사는" not in bubble  # ✅ PASS
    
    summary = response["summary_bullets"][0]
    assert "메리츠화재" in summary  # ✅ PASS
    assert "삼성화재" in summary  # ✅ PASS
    assert "정의되고" in summary or "정의됩니다" in summary  # ✅ PASS
```

---

## Frontend Impact

**Expected Frontend Rendering** (Right Dock):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
암진단비(유사암제외) 보장 기준 비교
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────┬──────────────┬──────────────┐
│ 비교 항목     │ 메리츠화재    │ 삼성화재      │
├──────────────┼──────────────┼──────────────┤
│ 보장 정의 기준│ 정액 지급 방식│ 지급 한도 기준│  ← KEY INSIGHT
├──────────────┼──────────────┼──────────────┤
│ 구체 내용     │ 3천만원       │ 보험기간 중 1회│  ← DIRECT COMPARISON
├──────────────┼──────────────┼──────────────┤
│ 지급유형      │ 정액형        │ 정액형        │
└──────────────┴──────────────┴──────────────┘
```

**Frontend rendering code** (no changes needed):
- Frontend already renders `comparison_table` rows correctly
- Display names are now in columns → table header shows "메리츠화재", "삼성화재"
- "보장 정의 기준" row is NEW → immediately visible

---

## Definition of Done ✅

1. ✅ `summary_bullets[0]` contains structural comparison (NOT abstract)
2. ✅ Table columns use display names (NOT insurer codes)
3. ✅ Table has "보장 정의 기준" row (structural basis)
4. ✅ Table has "구체 내용" row (direct comparison values)
5. ✅ All 21 tests PASS
6. ✅ NO LLM usage (deterministic only)
7. ✅ NO coverage_code / insurer_code in user-facing text

---

## Example Output (Real API Response)

```bash
$ python3 /tmp/ex3_example_output.py

📌 Summary Bullets (구조적 차이 요약):
  • 메리츠화재는 정액 지급 방식으로 보장이 정의되고, 삼성화재는 지급 한도 기준으로 보장이 정의됩니다
  • 가입설계서 기준 비교입니다

📌 Comparison Table (보장 기준 비교):
  Title: 암진단비(유사암제외) 보장 기준 비교
  Columns: ['비교 항목', '메리츠화재', '삼성화재']

  Row 1: 보장 정의 기준 | 정액 지급 방식 | 지급 한도 기준
  Row 2: 구체 내용 | 3천만원 | 보험기간 중 1회
  Row 3: 지급유형 | 정액형 | 정액형
```

---

**Status**: ✅ LOCKED
**Parent**: STEP NEXT-112 (Comparison-First UX Lock)
**Date**: 2026-01-04
