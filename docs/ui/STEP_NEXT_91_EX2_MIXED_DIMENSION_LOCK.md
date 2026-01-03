# STEP NEXT-91: EX2_DETAIL_DIFF Mixed Dimension Lock

## Purpose

When EX2_DETAIL_DIFF compares values from different dimensions (limit_summary vs coverage_amount_text), prevent user confusion by making the difference explicit in the view layer.

Maintains Policy A from STEP NEXT-90 (limit → amount fallback) while adding clear presentation rules for mixed comparisons.

---

## Problem Statement

- Some insurers (samsung) only have `kpi_summary.limit_summary`
- Some insurers (meritz) lack limit and only have `coverage_amount_text`
- Previous implementation displayed these as same-dimension DIFF → semantic confusion

---

## Constitutional Principles

- ❌ FORBIDDEN: Display different dimensions (frequency/period vs amount) as same-dimension comparison
- ✅ REQUIRED: Make mixed comparisons explicit with clear explanation
- ✅ REQUIRED: 0% coverage_code exposure in UI
- ✅ REQUIRED: Minimum 1 ref (PD:/EV:) per row
- ✅ REQUIRED: Deterministic only (NO LLM)

---

## Design Changes

### 1) Status Branch Rules

EX2_DETAIL_DIFF result status must be one of:

- **DIFF**
  - Only when comparing same dimension (limit vs limit, amount vs amount)

- **MIXED_DIMENSION** (NEW)
  - When limit_summary ↔ amount fallback mixing occurs

- **ALL_SAME**
  - Existing behavior preserved

---

### 2) value_display Format (CRITICAL)

When mixed dimension occurs, MUST include dimension type tag:

**limit_summary used:**
```
한도: 보험기간 중 1회
```

**amount fallback used:**
```
보장금액: 3천만원
```

**ABSOLUTELY FORBIDDEN:**
```
보험기간 중 1회 vs 3천만원  ❌ (no tags)
```

---

### 3) Title/Summary Rules

When status == MIXED_DIMENSION:

**Title:**
```
{insurers}의 {coverage_name} 보장 기준 차이
```
(NOT "보장한도 차이" → USE "보장 기준 차이")

**Summary bullets (minimum 1 required):**
- "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"

---

### 4) Table/Groups Rules

- Add `dimension_type` metadata to each group:
  - `LIMIT` | `AMOUNT`
- NOT exposed in UI, but included for testing/validation

---

### 5) Notes Rules

For insurers using amount fallback ONLY:
```
보장한도 정보가 없어 보장금액 기준으로 표시되었습니다
```

---

## Implementation Location

**Backend:**
- `apps/api/chat_handlers_deterministic.py`
  - EX2_DETAIL_DIFF handler
  - Add MIXED_DIMENSION status logic
  - Apply value_display prefix
- `apps/api/response_composers/ex2_detail_diff_composer.py` (if needed)

**View Model:**
- `apps/api/chat_vm.py`
  - Add MIXED_DIMENSION to status enum

**SSOT Document:**
- `docs/ui/STEP_NEXT_91_EX2_MIXED_DIMENSION_LOCK.md` (this file)

---

## Contract Test

**New test file:**
`tests/test_ex2_detail_diff_mixed_dimension.py`

**Validation items:**
1. ✅ Mixed limit+amount → status == MIXED_DIMENSION
2. ✅ value_display contains `한도:` / `보장금액:` prefix
3. ✅ title uses "보장 기준 차이"
4. ✅ summary_bullets contains mixed dimension explanation
5. ✅ 0% coverage_code exposure
6. ✅ Minimum 1 ref per row

---

## Definition of Done

- ✅ Mixed comparisons NOT displayed as DIFF
- ✅ User immediately understands "why different" from UI
- ✅ STEP NEXT-90 Policy A maintained
- ✅ No regression in existing EX2/EX3/EX4
- ✅ pytest passes

---

## Example Output

### Input Scenario
- Samsung: `limit_summary: "보험기간 중 1회"`
- Meritz: `limit_summary: null`, `coverage_amount_text: "3천만원"`

### Expected Output
```json
{
  "kind": "EX2_DETAIL_DIFF",
  "title": "삼성화재, 메리츠화재의 암진단비 보장 기준 차이",
  "summary_bullets": [
    "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
  ],
  "groups": [
    {
      "dimension_type": "LIMIT",
      "items": [
        {
          "insurer": "삼성화재",
          "value_display": "한도: 보험기간 중 1회",
          "refs": ["PD:samsung:A1000_1"]
        }
      ]
    },
    {
      "dimension_type": "AMOUNT",
      "items": [
        {
          "insurer": "메리츠화재",
          "value_display": "보장금액: 3천만원",
          "refs": ["PD:meritz:A1000_1"],
          "notes": ["보장한도 정보가 없어 보장금액 기준으로 표시되었습니다"]
        }
      ]
    }
  ],
  "status": "MIXED_DIMENSION"
}
```

---

## Future Note

When ontology is introduced later, `dimension_type` (LIMIT/AMOUNT) can be directly promoted to concept nodes.

---

**Created:** 2026-01-03
**STEP:** NEXT-91
**Status:** ✅ LOCKED
