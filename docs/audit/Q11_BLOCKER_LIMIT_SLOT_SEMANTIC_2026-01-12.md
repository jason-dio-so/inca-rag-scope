# Q11 BLOCKER: payout_limit Slot Semantic Mismatch

**Date**: 2026-01-12
**Task**: STEP NEXT-P2-Q11
**Status**: ❌ **BLOCKED**
**Blocker Type**: Slot Semantic Confusion (Limit vs Amount)

---

## Executive Summary

**Q11 Implementation CANNOT proceed** due to semantic mismatch in `payout_limit` slot for A6200 (암직접입원비).

**Customer Question**: "암직접입원비 담보 중 보장한도가 다른 상품을 비교해줘."

**Customer Intent**: Compare **duration/frequency limits** (e.g., "90일한도", "연간 1회한")

**Current Slot Data**:
- **payout_limit.value**: Contains **daily AMOUNT** (20,000 won), NOT limit
- **Actual limit**: Embedded in unstructured evidence text
- **Cannot extract structured limit**: Same G5 Gate attribution failure as Q5

---

## Data Reality Check (2026-01-12)

### Source
`data/compare_v1/compare_rows_v1.jsonl` — A6200 coverage rows (7 insurers)

### A6200 payout_limit Slot Status

```
Insurer  | Slot Status   | Slot Value | Semantic Meaning  | Customer Needs
---------|---------------|------------|-------------------|----------------
samsung  | FOUND         | 20000      | Daily amount      | "90일한도" (from evidence)
db       | FOUND         | 20000      | Daily amount      | Unknown limit
heungkuk | FOUND_GLOBAL  | 1, 11, 10  | Unparsable        | Unknown limit
hyundai  | FOUND         | 20000      | Daily amount      | Unknown limit
kb       | FOUND         | 20000      | Daily amount      | Unknown limit
lotte    | FOUND         | 20000      | Daily amount      | Unknown limit
meritz   | FOUND         | 20000      | Daily amount      | "연간1회한" (from evidence)
hanwha   | N/A           | N/A        | No A6200 coverage | N/A
```

**Summary**:
- **Slot value semantics**: 6/7 insurers have daily AMOUNT (not limit)
- **Actual limit location**: Unstructured evidence text
- **Usable structured limit**: 0/7 insurers

---

## Root Cause Analysis

### 1. Slot Name vs Slot Content Mismatch

**Slot Name**: `payout_limit` (suggests frequency/duration limit)

**Actual Content**:
- **Daily benefits** (A6200): Contains daily AMOUNT (20,000원/일)
- **Diagnosis benefits** (A4200_1): Contains frequency limit ("최초 1회")

**Problem**: Same slot name used for TWO different semantic types:
1. **Amount-based payouts**: Daily amount per event
2. **Frequency-based limits**: How many times benefit pays

**A6200 Case**: Needs BOTH (daily amount + duration limit), but slot only captures amount.

### 2. Limit Information in Evidence Text

**Samsung A6200 Evidence Excerpt**:
```
암 직접치료 입원일당Ⅱ(1일이상)(요양병원 제외)
암 요양병원 입원일당Ⅱ(1일이상, 90일한도)  ← LIMIT HERE
암 직접치료 통원일당(상급종합병원)(연간10회한)
```

**Problem**:
- "90일한도" appears in evidence text
- But mixed with OTHER coverages' limits (입원일당, 통원일당)
- Cannot attribute "90일한도" to A6200 specifically (G5 Gate failure)
- Multiple coverage limits appear in same excerpt

**Meritz A6200 Evidence Excerpt**:
```
암직접치료입원일당(Ⅱ)(요양병원제외, 1일이상)보장특약
32대질병관혈수술비(연간1회한)보장특약
5대질환수술비(연간1회한)보장특약
```

**Problem**:
- "연간1회한" appears but belongs to OTHER coverages (수술비)
- Cannot determine if A6200 has its own limit
- Evidence aggregation mixed multiple coverages

### 3. Heungkuk FOUND_GLOBAL Case

**Value**: "1, 11, 10" (tokenized fragments)

**Problem**:
- Unparsable format (no schema)
- Cannot determine if "1" means "1회" (1 time) or "1일" (1 day)
- FOUND_GLOBAL status indicates attribution uncertainty

---

## Q11 Requirements (Cannot Be Met)

### From STEP NEXT-P2-Q11 Directive

**Input Requirements**:
> "compare_rows_v1.jsonl 내 payout_limit 슬롯 사용"

**Customer Intent**:
> "보장한도가 다른 상품" — Compare **duration/frequency limits**

**Current Reality**:
- ❌ payout_limit contains **daily amount**, not **duration limit**
- ❌ Duration limit exists in evidence text but not attributable
- ❌ Cannot rank by "보장한도" using slot values
- ❌ 0/7 insurers have structured limit data

**Decision**: Cannot implement Q11 without structured duration/frequency limit SSOT.

---

## Semantic Analysis: What Q11 Actually Needs

### Daily Benefit Coverage Structure

**A6200 (암직접입원비)** pays:
- **AMOUNT**: 20,000 won per day hospitalized
- **LIMIT**: Up to N days (e.g., "90일한도", "120일한도")

**Customer Question Breakdown**:
1. **"암직접입원비 담보"** → Coverage A6200 ✅
2. **"보장한도가 다른"** → Compare duration limits (N days) ❌ NO DATA
3. **"상품"** → By insurer ✅

**What Customer Wants**:
```
Insurer  | Daily Amount | Duration Limit | Total Max Payout
---------|--------------|----------------|------------------
Samsung  | 20,000원     | 90일           | 1,800,000원
Meritz   | 20,000원     | 120일          | 2,400,000원
KB       | 20,000원     | 60일           | 1,200,000원
```

**What We Have**:
```
Insurer  | payout_limit.value | Usable for Ranking?
---------|--------------------|--------------------|
Samsung  | 20000 (amount)     | ❌ (all have same amount)
Meritz   | 20000 (amount)     | ❌
KB       | 20000 (amount)     | ❌
```

**Ranking Failure**: All insurers have same daily amount → no differentiation possible.

---

## Forbidden Actions (SSOT Policy)

**Q11 Directive**:
> "금지: 담보명 문자열 포함 여부로 임의 추정, 문서 전체(global) 값 사용"

**BLOCKED Actions**:
1. ❌ Extract "90일" from evidence text without coverage attribution
2. ❌ Use payout_limit.value (20000) as if it were duration limit
3. ❌ Infer limit from coverage title patterns (e.g., "Ⅱ" suffix)
4. ❌ Parse FOUND_GLOBAL value "1, 11, 10" without schema
5. ❌ Rank by daily amount (customer asked for **limit**, not amount)

---

## Required Fix (Out of Scope for Q11)

**Step3 Evidence Resolver Enhancement Needed**:

### Option 1: Split payout_limit into Two Slots
- **New slots**:
  - `payout_amount`: Daily/per-event amount (원/일, 원/회)
  - `payout_frequency_limit`: Duration/frequency limit (일, 회)
- **Scope**: Modify Step1 slot schema + Step3 extraction logic
- **Estimated Effort**: 3-5 days (requires slot schema redesign)

### Option 2: Add Structured Limit Subfield
- **Schema**:
  ```json
  {
    "payout_limit": {
      "value": {
        "amount": 20000,
        "unit": "원/일",
        "duration_limit": 90,
        "duration_unit": "일"
      },
      "status": "FOUND"
    }
  }
  ```
- **Scope**: Modify slot value schema + Step3 parsing logic
- **Estimated Effort**: 4-6 days (requires re-extraction for all coverages)

### Option 3: Evidence-Level Limit Extraction
- **Approach**: Extract limit from evidence text using NLP
- **Challenge**: Attribution problem (same as Q5 G5 Gate failure)
- **Estimated Effort**: 5-7 days (requires G5 Gate enhancement)

**Recommendation**: Pursue Option 1 (split slots) for clearest semantics.

---

## Comparison with Q3/Q5 Blockers

| Aspect | Q3 (의무담보) | Q5 (감액/면책) | Q11 (한도) |
|--------|---------------|----------------|-----------|
| **Slot Exists?** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Evidence Extracted?** | ❌ No | ✅ Yes | ✅ Yes |
| **Problem** | No data at all | Attribution failure | **Semantic mismatch** |
| **Data Availability** | 0% FOUND | 12.5% FOUND | 85.7% FOUND (wrong semantic) |
| **Root Cause** | Missing extraction | G5 Gate rejection | Slot contains amount, not limit |
| **Fix Required** | Product-structure analysis | G5 Gate enhancement | **Slot schema redesign** |
| **Estimated Effort** | 5-7 days | 2-3 days | 3-5 days |

**Q11 is UNIQUE**: Data exists and is extractable, but **slot semantics don't match customer question**.

---

## Alternative Approach: Pivot to Daily Amount Comparison

### Option A: Answer Different Question (NOT RECOMMENDED)

**Reinterpret Customer Question**:
- Original: "보장한도가 다른 상품" (duration limit comparison)
- Pivoted: "암직접입원비 일당 금액이 다른 상품" (daily amount comparison)

**Implementation**:
- Use payout_limit.value (20000) as daily amount
- Rank by daily amount (higher = better)

**Problem**:
- ❌ **All 6 insurers have same daily amount** (20,000원)
- ❌ No differentiation possible → useless ranking
- ❌ Violates customer intent (asked for "한도", not "금액")

**Verdict**: **DO NOT IMPLEMENT** — misleading and unhelpful.

### Option B: Show "Data Type Mismatch" Error

**Implementation**:
- Detect A6200 query
- Return structured error:
  ```json
  {
    "classification": "UNKNOWN",
    "reason": "SLOT_SEMANTIC_MISMATCH",
    "notes": "payout_limit slot contains daily amount (20,000원), not duration limit. Customer asked for '보장한도' (limit) comparison, which requires duration data not currently available."
  }
  ```

**Verdict**: Honest, but doesn't help customer.

---

## Customer Communication (Phase 3)

Per **STEP NEXT-P2-Q11** and **Phase 1-3 Plan**:

**Q11 is Phase 2, but BLOCKED** → Moves to **Phase 3 (설명 대상)**

**Customer Message** (for WHY_SOME_QUESTIONS_UNAVAILABLE.md):

```markdown
### Q11: 암직접입원비 보장한도 비교

**질문**: "암직접입원비 담보 중 보장한도가 다른 상품을 비교해줘."

**현재 상태**: 제공 불가

**이유**:
암직접입원비는 "하루 입원당 2만원" 같은 **일당 금액**과
"연간 최대 90일" 같은 **기간 한도**가 모두 중요합니다.

현재 시스템은:
- ✅ 일당 금액 정보: 확보됨 (대부분 2만원으로 동일)
- ❌ 기간 한도 정보: 미확보 (약관 문서에는 존재하나 추출 실패)

**구체적인 문제**:
1. **데이터 구조 불일치**
   - 보험 데이터 저장 방식이 "한도" 질문에 최적화되지 않음
   - "일당 금액"과 "기간 한도"가 구분되지 않음

2. **추출 실패**
   - 약관에 "90일한도", "120일한도" 문구는 존재
   - 하지만 여러 담보의 한도가 혼재된 페이지에서 정확한 추출 불가

**필요한 개선**:
- 데이터 저장 구조 개선 (금액 vs 한도 분리)
- 담보별 한도 추출 로직 강화

**대안**:
- 보험사 상담 센터에서 "암직접입원비 담보의 연간 지급 한도(일수)" 직접 문의
- 약관 원문에서 "암직접치료입원일당" 특약의 "보장한도" 항목 확인
```

---

## Phase 2 Status Summary

| Question | Status | Blocker | Data Availability |
|----------|--------|---------|-------------------|
| Q5 (감액/면책) | ❌ BLOCKED | Attribution failure | 12.5% (1/8 FOUND) |
| Q3 (의무담보) | ❌ BLOCKED | No SSOT | 0% (0/8 FOUND) |
| Q11 (한도) | ❌ BLOCKED | Semantic mismatch | 85.7% (6/7 FOUND wrong data) |

**Phase 2 Result**: 0/3 implemented, 3/3 BLOCKED

**Common Pattern**:
- All Phase 2 questions require **coverage-level SSOT** from compare_rows_v1.jsonl
- All face **extraction or attribution failures** preventing structured comparison
- All require **Step3 Evidence Resolver enhancements** (different types)

---

## Next Actions

### Immediate (2026-01-12)
1. ✅ Document Q11 BLOCKER (this file)
2. ⏳ Add Q11 entry to customer explanation (WHY_SOME_QUESTIONS_UNAVAILABLE.md)
3. ⏳ Update STATUS.md: Q11 marked as **BLOCKED**
4. ⏳ Report to user: Phase 2 complete (0/3 implemented, all BLOCKED)

### Future (When Slot Schema Redesign is Ready)
1. Split payout_limit into amount + frequency_limit slots
2. Re-run Step3 Evidence Resolver with new schema
3. Verify duration limit extraction success rate > 80%
4. Re-attempt Q11 implementation

---

**Document Version**: 1.0
**Status**: 🔒 **LOCKED** (BLOCKER EVIDENCE)
**Last Updated**: 2026-01-12
**Review Trigger**: Slot schema redesign completion
