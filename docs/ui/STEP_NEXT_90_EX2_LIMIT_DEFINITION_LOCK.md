# STEP NEXT-90 — EX2_DETAIL_DIFF "보장한도" Terminology Definition Lock

**Status**: ✅ LOCKED (SSOT)
**Date**: 2026-01-03
**Scope**: EX2_DETAIL_DIFF handler only

---

## Problem Statement

Users asking "보장한도가 다른 상품은?" expect to see **보장금액** (coverage amount, e.g., "3,000만원").
However, the system interprets "보장한도" as **limit conditions** (e.g., "최초 1회한", "연 2회") only.

This mismatch causes:
- Samsung: `limit_summary = "보험기간 중 1회"` → Shows "보험기간 중 1회"
- Meritz: `limit_summary = null` → Shows "명시 없음" (even though `amount = "3천만원"` exists)

**User frustration**: "Why does it say '명시 없음' when the amount is clearly 3,000만원?"

---

## Policy Decision: **Policy A** (User-Aligned)

### Definition

**"보장한도" in EX2_DETAIL_DIFF context = "보장금액 또는 한도조건"**

When `compare_field = "보장한도"`:
1. **Primary**: Use `kpi_summary.limit_summary` if available (e.g., "보험기간 중 1회")
2. **Fallback**: If `limit_summary` is `null`/missing, use `proposal_facts.coverage_amount_text` (e.g., "3,000만원")
3. **Last resort**: If both are missing, return "명시 없음"

### Display Rules

- **Value Display**: Show either limit or amount (whichever is available)
- **Label**: Field label remains "보장한도" (no change to avoid confusion)
- **Evidence Refs**:
  - If from `limit_summary` → use `kpi_evidence_refs`
  - If from `amount` → use `proposal_detail_ref`

---

## Implementation Rules

### Handler Logic (apps/api/chat_handlers_deterministic.py)

```python
# STEP NEXT-90: Extract 보장한도 with fallback to amount
if compare_field == "보장한도":
    # Priority 1: KPI limit_summary
    kpi_summary = card.get("kpi_summary", {}) or {}
    limit_summary = kpi_summary.get("limit_summary")

    if limit_summary:
        value = limit_summary
        refs = kpi_summary.get("kpi_evidence_refs", [])
    else:
        # Priority 2: Fallback to coverage_amount_text
        proposal_facts = card.get("proposal_facts", {}) or {}
        amount_text = proposal_facts.get("coverage_amount_text")

        if amount_text:
            value = amount_text
            refs = [card.get("refs", {}).get("proposal_detail_ref")]
        else:
            value = None
            refs = []
```

### Why NOT Policy B

**Policy B** (strict separation) would require:
- Users to distinguish "보장한도" (limit) vs "보장금액" (amount)
- Additional UI hints/tooltips
- More complex intent routing

**Verdict**: Policy B increases cognitive load without clear benefit. Most users want to see **both** amount and limit conditions, not just limit alone.

---

## Evidence Refs Guarantee

**Constitutional Rule**: Every field value MUST have at least 1 ref (PD: or EV:)

### Ref Priority

1. **If value from `kpi_summary.limit_summary`**:
   - Use `kpi_summary.kpi_evidence_refs`
   - If empty → fallback to `refs.proposal_detail_ref`

2. **If value from `proposal_facts.coverage_amount_text`**:
   - Use `refs.proposal_detail_ref` (PD:{insurer}:{coverage_code})
   - If missing → generate on-the-fly: `f"PD:{insurer}:{coverage_code}"`

3. **If value = "명시 없음"**:
   - MUST still provide `refs.proposal_detail_ref` (검증 시작점 확보)
   - Add to `extraction_notes`: "한도 및 금액 정보 모두 추출 불가"

---

## Contract Tests

File: `tests/test_ex2_detail_diff_refs_and_limit_definition.py`

### Test Cases

1. **test_limit_uses_kpi_summary_when_available**:
   - Samsung A4200_1 (`limit_summary = "보험기간 중 1회"`)
   - Expected: value = "보험기간 중 1회", refs from kpi_evidence_refs

2. **test_limit_fallback_to_amount_when_no_limit_summary**:
   - Meritz A4200_1 (`limit_summary = null`, `amount = "3천만원"`)
   - Expected: value = "3천만원", refs from proposal_detail_ref

3. **test_limit_has_minimum_one_ref_even_when_none**:
   - Mock card with `limit_summary = null`, `amount = null`
   - Expected: value = "명시 없음", refs = ["PD:{insurer}:{coverage_code}"]

4. **test_no_coverage_code_exposure_in_view_fields**:
   - Regression test (STEP NEXT-89)
   - title/summary/sections.title MUST have 0% coverage_code

---

## Examples

### Before (STEP NEXT-89)

Query: "보장한도가 다른 상품은?" (Samsung + Meritz, 암진단비)

Response:
```json
{
  "status": "ALL_SAME",
  "groups": [
    {
      "value_display": "명시 없음",
      "insurers": ["samsung", "meritz"],
      "insurer_details": [
        {"insurer": "samsung", "evidence_refs": []},
        {"insurer": "meritz", "evidence_refs": []}
      ]
    }
  ]
}
```

**Problem**: Both show "명시 없음" even though Samsung has limit and both have amounts.

### After (STEP NEXT-90)

Response:
```json
{
  "status": "DIFF",
  "groups": [
    {
      "value_display": "보험기간 중 1회",
      "insurers": ["samsung"],
      "insurer_details": [
        {
          "insurer": "samsung",
          "raw_text": "보험기간 중 1회",
          "evidence_refs": ["PD:samsung:A4200_1"]
        }
      ]
    },
    {
      "value_display": "3천만원",
      "insurers": ["meritz"],
      "insurer_details": [
        {
          "insurer": "meritz",
          "raw_text": "3천만원",
          "evidence_refs": ["PD:meritz:A4200_1"],
          "notes": ["보장한도 정보 없음, 보장금액 표시"]
        }
      ]
    }
  ]
}
```

**Fixed**: Shows actual values + proper refs.

---

## Forbidden Actions

- ❌ Mixing "보장한도" and "보장금액" as separate compare_fields in same query
- ❌ Returning refs = [] (empty array) in any case
- ❌ Using free-text refs like "가입설계서(보장내용)" instead of PD:/EV:
- ❌ Exposing coverage_code in title/summary/section titles

---

## SSOT Lock Date

**2026-01-03**: This policy is LOCKED. Any changes require:
1. User research evidence showing Policy A fails
2. Alternative policy proposal with test coverage
3. Migration plan for existing queries
