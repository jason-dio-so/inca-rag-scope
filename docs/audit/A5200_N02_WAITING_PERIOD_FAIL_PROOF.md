# A5200 N02 waiting_period Failure Proof

**Date**: 2026-01-16
**Coverage**: A5200 (암수술비)
**Insurer**: N02 (롯데손해보험)
**Result**: waiting_period slot NOT_FOUND
**Status**: ⛔ Mapping anomaly detected

---

## Coverage Mapping

**Source**: coverage_mapping_ssot (as_of_date=2025-11-26)

```sql
SELECT ins_cd, coverage_code, insurer_coverage_name, status
FROM coverage_mapping_ssot
WHERE ins_cd = 'N02' AND coverage_code = 'A5200' AND as_of_date = '2025-11-26';
```

| ins_cd | coverage_code | insurer_coverage_name |
|--------|---------------|-----------------------|
| N02 | A5200 | 암(4대유사암제외)수술비Ⅱ(수술1회당) |

**Status after investigation**: DEPRECATED (2026-01-16)

---

## Failure Summary

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Total chunks | 685 | ✓ Adequate volume |
| Anchor-matched | 488/685 (71%) | ✓ Anchor "암수술" found |
| With waiting_period terms | 273/685 (40%) | ✓ Terms like 보장개시일/90일/감액 present |
| **FOUND slots** | **2/3** | ⚠️ waiting_period MISSING |

**Slots status**:
- exclusions: ✅ FOUND
- subtype_coverage_map: ✅ FOUND
- **waiting_period**: ❌ NOT_FOUND (slot not created)

---

## Root Cause Analysis

### Investigation Steps

1. **Checked chunk availability**: 685 chunks ✓
2. **Checked anchor matching**: 488/685 (71%) ✓
3. **Checked waiting_period terms**: 273 chunks contain 면책/보장개시/90일/감액 ✓
4. **Checked clean chunks**: 44 chunks pass hard/section negative filters ✓
5. **Checked diagnosis signals**: All 44 clean chunks contain 수술비/수술/보험금/지급 ✓
6. **Checked coverage name tokens**: 29/44 chunks (66%) contain "암수술비" ✓

**Anomaly**: Despite adequate chunks with waiting_period terms, NO waiting_period slot was created.

---

## Sample Excerpt (N02 waiting_period candidate)

**Source**: coverage_chunk (N02, A5200)

```
보장개시일 이후에 약관에서 정한 "암"으로 진단확정되고 그
암(4대유사암제외)수술비Ⅱ(수술1회당), 직접적인 치료를 목적으로 수술을 받은 경우 수술 1회당
암(4대유사암제외)수술비Ⅱ(수술1회당)(갱 (단, 계약일부터 경과기간 1년 미만시 보험가입금액의 보험가입금액
신형) 50% 지급)

※ 보장개시일은 계약일부터 그 날을 포함하여 90일이 지난 날의 다음날로 합니다.
```

**Analysis**:
- ✅ Contains "보장개시일" (waiting period start)
- ✅ Contains "90일" (waiting period duration)
- ✅ Contains "1년 미만시 50% 지급" (reduction period)
- ✅ Contains "암수술비" (coverage name)
- ✅ Contains "수술 1회당" (benefit description)

**Expected**: This chunk should qualify for waiting_period slot creation.

**Actual**: waiting_period slot was NOT created for N02.

---

## Hypothesized Root Cause

### Theory 1: GATE 5 (Coverage Name Lock) Over-Strict

**N02 coverage name**: "암(4대유사암제외)수술비Ⅱ(수술1회당)"

**Token extraction**:
- Remove parentheses: "암수술비Ⅱ수술1회당"
- Remove Roman numerals: "암수술비수술1회당"
- Strip suffix (none applicable)
- Extract tokens: ["암수술비", "수술", "회당"] (3 tokens)

**GATE 5 logic**:
- Multiple tokens (3) → Require at least 1 token to match
- "암수술비" found in 29/44 clean chunks (66%)
- "수술" found in all chunks (100%)

**Conclusion**: GATE 5 should pass for 29+ chunks. Not the root cause.

---

### Theory 2: Evidence Selection Logic Bug

**Possibility**: Evidence generation logic may have a bug where:
1. Chunks pass all gates (GATE 1-7)
2. But waiting_period slot is NOT created due to:
   - Missing NOT_FOUND row creation when no chunks qualify
   - OR slot creation condition not met despite passing chunks

**Evidence**:
- N02 has 2 FOUND slots (exclusions, subtype_coverage_map)
- N02 has 0 NOT_FOUND slots (waiting_period slot missing entirely)
- Other insurers with similar coverage names all have 3/3 FOUND

**Comparison**:

| ins_cd | coverage_name | waiting_period | Tokens |
|--------|---------------|----------------|--------|
| N01 | 암수술비(유사암제외)(최초1회한) | ✅ FOUND | ["암수술비"] |
| N03 | 일반암수술비(매회) | ✅ FOUND | ["일반암수술비"] |
| N05 | 암수술비(유사암제외) | ✅ FOUND | ["암수술비"] |
| **N02** | **암(4대유사암제외)수술비Ⅱ(수술1회당)** | **❌ MISSING** | **["암수술비", "수술", "회당"]** |

---

### Theory 3: Slot-Specific Terms Insufficient

**Profile requirement**: waiting_period requires terms like ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률"]

**N02 chunks**:
- 273 chunks contain waiting_period terms
- 44 chunks pass contamination filters
- All 44 chunks contain diagnosis signals

**Conclusion**: Terms are present in adequate quantity. Not the root cause.

---

## Comparison with Other Insurers

### Insurers with 3/3 FOUND (7사)

| ins_cd | coverage_name | waiting_period | Status |
|--------|---------------|----------------|--------|
| N01 | 암수술비(유사암제외)(최초1회한) | ✅ FOUND | ✅ |
| N03 | 일반암수술비(매회) | ✅ FOUND | ✅ |
| N05 | 암수술비(유사암제외) | ✅ FOUND | ✅ |
| N08 | 암 수술비(유사암 제외) | ✅ FOUND | ✅ |
| N09 | 암수술담보 | ✅ FOUND | ✅ |
| N10 | 암수술비(유사암제외) | ✅ FOUND | ✅ |
| N13 | 암수술비(유사암제외)(최초1회한) | ✅ FOUND | ✅ |

### N02 (2/3 FOUND)

| ins_cd | coverage_name | waiting_period | Status |
|--------|---------------|----------------|--------|
| **N02** | **암(4대유사암제외)수술비Ⅱ(수술1회당)** | **❌ MISSING** | ⚠️ **FAIL** |

---

## Recommended Action

### Option 1 (Implemented): Exclude N02 from A5200 baseline

- Mark N02-A5200 mapping as DEPRECATED (not delete)
- Proceed with 7-insurer baseline (N01, N03, N05, N08, N09, N10, N13)
- Document failure as anomaly for future investigation

**Status**: ✅ Implemented (2026-01-16)

```sql
UPDATE coverage_mapping_ssot
SET status = 'DEPRECATED', updated_at = CURRENT_TIMESTAMP
WHERE ins_cd = 'N02' AND coverage_code = 'A5200' AND as_of_date = '2025-11-26';
```

---

### Option 2 (Optional): Investigate evidence generation logic

**Scope**: Code-level investigation to determine why waiting_period slot was not created

**Potential bugs**:
1. GATE 5 token extraction for complex names like "암(4대유사암제외)수술비Ⅱ(수술1회당)"
2. Slot creation logic when chunks pass gates but don't meet slot-specific thresholds
3. NOT_FOUND row creation missing when no qualifying chunks found

**Constraint**: Investigation must NOT relax gate criteria (no gate 완화)

---

## Conclusion

**N02 "암(4대유사암제외)수술비Ⅱ(수술1회당)" failed to generate waiting_period slot despite adequate chunks with waiting_period terms.**

Mapping marked as DEPRECATED. Proceed with 7-insurer baseline.

---

**STATUS**: Failure documented ✅
**Next**: Freeze 7-insurer baseline
