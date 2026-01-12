# Q5 BLOCKER: Evidence Attribution Failure

**Date**: 2026-01-12
**Task**: STEP NEXT-P2-Q5
**Status**: ❌ **BLOCKED**
**Blocker Type**: Insufficient Attributable Evidence

---

## Executive Summary

**Q5 Implementation CANNOT proceed** due to evidence attribution failure in Step3 Evidence Resolver.

**Customer Question**: "암 진단 시 90일 면책 직후 100% 지급 vs 1년/2년 감액(50%) 존재 상품을 구분해줘."

**Required Slots**:
- `waiting_period` (면책기간)
- `reduction` (감액 기간/지급률)

**Current Status**:
- ✅ Evidence **exists** in documents (Step3 extracted evidence)
- ❌ Evidence **attribution FAILED** (G5 Gate: 담보 귀속 확인 불가)
- ❌ Slots marked **UNKNOWN** for 7/8 insurers (waiting_period) and 6/8 insurers (reduction)

---

## Data Reality Check (2026-01-12)

### Source
`data/compare_v1/compare_rows_v1.jsonl` (Step4 Compare Model output)

### A4200_1 (암진단비) Slot Status

```
Insurer       | Waiting Period | Reduction  | Evidence Exists?
--------------|----------------|------------|------------------
db            | UNKNOWN        | UNKNOWN    | ✅ Yes (FOUND_GLOBAL)
hanwha        | UNKNOWN        | UNKNOWN    | ✅ Yes
heungkuk      | UNKNOWN        | FOUND      | ✅ Yes
hyundai       | UNKNOWN        | UNKNOWN    | ✅ Yes
kb            | UNKNOWN        | FOUND      | ✅ Yes
lotte         | UNKNOWN        | UNKNOWN    | ✅ Yes
meritz        | FOUND          | FOUND      | ✅ Yes
samsung       | UNKNOWN        | UNKNOWN    | ✅ Yes (FOUND_GLOBAL)
```

**Summary**:
- **Waiting Period**: 1 FOUND / 7 UNKNOWN (87.5% attribution failure)
- **Reduction**: 3 FOUND / 5 UNKNOWN (62.5% attribution failure)

---

## Root Cause Analysis

### 1. G5 Gate Failure

**What is G5 Gate?**
- Step3 Evidence Resolver applies GATE rules to ensure evidence is attributable to specific coverage
- G5 Gate checks: "Does this evidence belong to the current coverage or a different one?"

**Failure Modes Observed**:
1. **"G5 Gate: 담보 귀속 확인 불가"** (Cannot confirm coverage attribution)
   - Evidence found in document
   - But cannot determine if it applies to A4200_1 specifically

2. **"G5 Gate: 다른 담보 값 혼입"** (Evidence mixed from other coverages)
   - Evidence extracted from document section that mentions multiple coverages
   - Example: Samsung A4200_1 reduction evidence came from "유사암 진단비" section

### 2. FOUND_GLOBAL Status

**Definition**: Evidence found at document/product level, not coverage-specific

**Example** (Samsung A4200_1):
```json
{
  "waiting_period": {
    "status": "UNKNOWN",
    "evidences": [
      {
        "excerpt": "보장명 ...면책기간... [갱신형] 암 요양병원 입원일당Ⅱ...",
        "gate_status": "FOUND_GLOBAL"
      }
    ],
    "notes": "G5 Gate: 다른 담보 값 혼입"
  }
}
```

**Problem**: Evidence is from a **table** that lists multiple coverages' waiting periods. The "90일" applies to multiple cancer coverages, but Step3 couldn't attribute it specifically to A4200_1.

### 3. Evidence Exists But Cannot Be Used

**All 8 insurers** have waiting_period/reduction evidence in their documents:
- ✅ Evidence extracted successfully
- ✅ Keyword patterns matched ("면책기간", "감액", "90일", "50%")
- ❌ Attribution to A4200_1 failed (gate rejection)

**Policy Violation if Proceeded**:
- ❌ Cannot use FOUND_GLOBAL evidence without coverage-specific attribution
- ❌ Cannot infer from document-level patterns
- ❌ Cannot assume "90일" applies to A4200_1 without explicit linkage

---

## Q5 Classification Logic (Cannot Implement)

**Decision Table** (from STEP NEXT-P2-Q5 directive):

| Classification | Criteria | Evidence Required |
|----------------|----------|-------------------|
| WAIT90_FULL100 | 90일 면책 + NO 감액 + 100% 지급 근거 | ✅ waiting_period=90일<br>✅ reduction=없음<br>✅ "100% 지급" quote |
| WAIT90_REDUCE_1Y_50 | 90일 면책 + 1년 감액 + 50% | ✅ waiting_period=90일<br>✅ reduction=1년<br>✅ "50%" quote |
| WAIT90_REDUCE_2Y_50 | 90일 면책 + 2년 감액 + 50% | ✅ waiting_period=90일<br>✅ reduction=2년<br>✅ "50%" quote |
| OTHER | 다른 조건 존재 | ✅ 근거 문장 |
| UNKNOWN | 슬롯/evidence 부족 | ❌ 사유 필수 |

**Actual Available Data**:
- 7/8 insurers: waiting_period = UNKNOWN → **Cannot classify** (missing required field)
- 5/8 insurers: reduction = UNKNOWN → **Cannot classify** (missing required field)

**Even with FOUND slots (meritz, heungkuk, kb)**:
- Need to parse `reduction.value` (e.g., "3, 6, 4") to extract period/rate
- Need to parse `waiting_period.value` (e.g., "90, 1, 50") to extract days
- Values are **tokenized fragments**, not structured (no schema)

---

## Forbidden Actions (SSOT Policy)

**Q5 Directive**:
> "만약 evidence/slot이 부족하면: output UNKNOWN + reason, and STOP (do not guess)."

**BLOCKED Actions**:
1. ❌ Use FOUND_GLOBAL evidence as if coverage-specific
2. ❌ Infer waiting_period/reduction from document-level patterns
3. ❌ Assume "90일" applies to A4200_1 without explicit attribution
4. ❌ Parse tokenized fragments ("90, 1, 50") without schema
5. ❌ Build classifier with 7/8 UNKNOWN inputs

---

## Required Fix (Out of Scope for Q5)

**Step3 Evidence Resolver Enhancement Needed**:

### Fix 1: Improve G5 Gate Logic
- **Current**: Rejects evidence if coverage ambiguity detected
- **Needed**: Context-aware attribution (e.g., "암진단비" section → A4200_1)
- **Scope**: Modify `pipeline/step3_evidence_resolver/gates.py`

### Fix 2: Add Coverage-Specific Anchoring
- **Current**: Slot extraction uses keyword patterns only
- **Needed**: Require coverage name proximity (e.g., "암 진단비...90일")
- **Scope**: Modify `pipeline/step3_evidence_resolver/resolver.py`

### Fix 3: Structure Slot Values
- **Current**: Values stored as tokenized strings ("90, 1, 50")
- **Needed**: Structured schema (e.g., `{days: 90, rate: 50, period: 1}`)
- **Scope**: Define `pipeline/step1_summary_first/extended_slot_schema.py`

**Estimated Effort**: 2-3 days (requires re-running Step3 for all insurers)

---

## Q5 Implementation Decision

**Status**: ❌ **BLOCKED - CANNOT PROCEED**

**Reason**:
- 87.5% of insurers have UNKNOWN waiting_period
- 62.5% of insurers have UNKNOWN reduction
- SSOT policy forbids inference/estimation

**Output**: All 8 insurers classified as **UNKNOWN** with reason:

```json
{
  "insurer_key": "samsung",
  "classification": "UNKNOWN",
  "waiting_period": null,
  "reduction": null,
  "reason": "SLOT_EVIDENCE_ATTRIBUTION_FAILED",
  "notes": "Evidence exists in documents but Step3 G5 Gate rejected coverage-specific attribution. Requires Step3 resolver enhancement."
}
```

---

## Alternative Approach (NOT RECOMMENDED)

### Option A: Use FOUND_GLOBAL Evidence (POLICY VIOLATION)
- Extract "90일" from product-level evidence
- Assume applies to A4200_1
- **Problem**: Violates SSOT "NO INFERENCE" rule

### Option B: Manual Evidence Mapping (UNSUSTAINABLE)
- Manually review each insurer's documents
- Create coverage-specific evidence map
- **Problem**: Not reproducible, breaks automation

### Option C: Partial Implementation (MISLEADING)
- Implement Q5 for 1-3 insurers with FOUND slots only
- Output UNKNOWN for others
- **Problem**: Incomplete user experience (7/8 insurers = "데이터 없음")

**Recommendation**: **DO NOT IMPLEMENT Q5 until Step3 fix is complete.**

---

## Customer Communication (Phase 3)

Per **STEP NEXT-P2-Q5** and **Phase 1-3 Plan**:

**Q5 is Phase 2, but BLOCKED** → Moves to **Phase 3 (설명 대상)**

**Customer Message** (for WHY_SOME_QUESTIONS_UNAVAILABLE.md):

```markdown
### Q5: 감액/면책 기간 상세 비교

**질문**: "암 진단 시 90일 면책 직후 100% 지급 vs 1년/2년 감액(50%) 존재 상품을 구분해줘."

**현재 상태**: 제공 불가

**이유**:
보험 약관에서 면책기간과 감액 조건에 대한 문구를 발견했으나,
해당 조건이 암진단비 담보에만 적용되는지 확인할 수 없습니다.

약관 문서에는 여러 담보의 조건이 혼재되어 있으며,
현재 시스템은 담보별 귀속 판정 기준이 불충분하여
잘못된 정보를 제공할 위험이 있습니다.

**필요한 개선**:
- 약관 문서 내 담보별 구조화 분석 강화
- 면책/감액 조건의 담보 귀속 확인 로직 보완

**대안**:
- 보험사별 약관 원문 열람 (직접 확인)
- 보험사 상담 센터 문의
```

---

## Next Actions

### Immediate (2026-01-12)
1. ✅ Document Q5 BLOCKER (this file)
2. ✅ Update STATUS.md: Q5 remains **BLOCKED** (no status change)
3. ✅ Create customer explanation entry (WHY_SOME_QUESTIONS_UNAVAILABLE.md)
4. ✅ Report to user: Q5 BLOCKED, proceed to Q3

### Future (When Step3 Fix is Ready)
1. Implement G5 Gate enhancement
2. Re-run Step3 Evidence Resolver (all insurers)
3. Verify waiting_period/reduction FOUND rate > 80%
4. Re-attempt Q5 implementation

---

**Document Version**: 1.0
**Status**: 🔒 **LOCKED** (BLOCKER EVIDENCE)
**Last Updated**: 2026-01-12
**Review Trigger**: Step3 resolver enhancement completion
