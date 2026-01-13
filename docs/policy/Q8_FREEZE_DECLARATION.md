# Q8 Freeze Declaration

**Date**: 2026-01-13
**Status**: 🔒 FROZEN
**Type**: TYPE B - Overlay (Evidence-First)

---

## Problem Statement (Fixed)

**Q8**: "질병 수술비(1~5종) 담보에서 '연간 1회 지급'인지, '매회(회당) 반복 지급'인지가 문서에 어떻게 명시되어 있는지를 보험사별로 비교해준다."

**Scope**: Document-stated repeat payment frequency policy for 질병수술비(1~5종) coverage **ONLY**.

**Prohibited**:
- ❌ Specific surgery attribution (e.g., "대장용종 제거")
- ❌ Premium ranking ("가장 큰 금액")
- ❌ Surgery recommendations
- ❌ Cross-coverage inference
- ❌ LLM estimation

---

## SSOT Location

**Primary SSOT**:
```
data/compare_v1/q8_surgery_repeat_policy_v1.jsonl
```

**SHA256**:
```
945dc2f27121d5371f8dc9c8e881fb734ce7009b83d138c897a3d64a70440000
```

**Record Schema**:
```json
{
  "insurer_key": "samsung",
  "repeat_payment_policy": "PER_EVENT | ANNUAL_LIMIT | UNKNOWN",
  "display_text": "매회 지급 | 연간 1회한 | 확인 불가 (근거 없음)",
  "evidence_refs": [
    {
      "doc_type": "약관",
      "page": 32,
      "excerpt": "질병수술비는 수술 1회당 지급합니다."
    }
  ]
}
```

---

## Implementation Status

### ✅ Definition of Done (Completed)

1. **Evidence Resolver Created**
   - ✅ `pipeline/step3_evidence_resolver/surgery_repeat_policy_resolver.py`
   - ✅ Strict keyword matching: "매회"/"회당" vs "연간 1회"/"연 1회한"
   - ✅ Context validation: Must mention "질병수술비"
   - ✅ Evidence-first: UNKNOWN when no explicit policy found

2. **SSOT Generated**
   - ✅ 10 insurers processed
   - ✅ Distribution: 5 PER_EVENT, 3 ANNUAL_LIMIT, 2 UNKNOWN
   - ✅ All records include evidence_refs (when FOUND)

3. **API Endpoint Implemented**
   - ✅ `GET /q8` endpoint active
   - ✅ Insurer filtering supported (`?insurers=kb,hanwha`)
   - ✅ Response includes evidence sample (first occurrence)
   - ✅ Returns 10 items by default

4. **Core Model Integrity Verified**
   - ✅ compare_rows_v1.jsonl unchanged (SHA256: f3935d6ffdb790da9fe1aa88bd0017244b9117b9ef84aadc81a6b1cb6d3c4914)
   - ✅ compare_tables_v1.jsonl unchanged (SHA256: 4a4a3f6e2060b8ad72f3f22773cdd3116bf5ea592b46af11b494f781cef7f70a)
   - ✅ No core slots created or modified
   - ✅ Regression tests passed

5. **Documentation Complete**
   - ✅ Policy document: `docs/policy/Q8_SURGERY_REPEAT_POLICY_OVERLAY.md`
   - ✅ Fact snapshot: `docs/audit/Q8_FACT_SNAPSHOT_2026-01-13.md`
   - ✅ Freeze declaration: This document
   - ✅ All documents include SHA256 verification

---

## API Response Sample

**Endpoint**: `GET /q8?insurers=hanwha,heungkuk`

**Response**:
```json
{
  "query_id": "Q8",
  "items": [
    {
      "insurer_key": "hanwha",
      "repeat_payment_policy": "ANNUAL_LIMIT",
      "display_text": "연간 1회한",
      "evidence_count": 1,
      "evidence": {
        "doc_type": "약관",
        "page": 340,
        "excerpt": "분\" 당 \"관혈수술\" 또는 \"비관혈수술\"별 각각 연간 1회를 초과하여 지급하지 않습니다."
      }
    },
    {
      "insurer_key": "heungkuk",
      "repeat_payment_policy": "PER_EVENT",
      "display_text": "매회 지급",
      "evidence_count": 2,
      "evidence": {
        "doc_type": "약관",
        "page": 363,
        "excerpt": "때에는 수술1회당 아래의 금액을 지급"
      }
    }
  ]
}
```

---

## Freeze Rules

### After Freeze - ALLOWED ✅

1. **SSOT Regeneration**
   - Same evidence resolver logic
   - When new documents added
   - Must maintain schema compatibility

2. **UI/UX Improvements**
   - Display text formatting
   - Visual presentation
   - Sorting/filtering options

3. **API Format Changes**
   - Response structure modifications
   - Field renaming (with migration)
   - As long as data semantics unchanged

4. **Documentation Updates**
   - Clarifications
   - Examples
   - Cross-references

### After Freeze - PROHIBITED ❌

1. **Core Model Modifications**
   - ❌ Creating/modifying slots in compare_rows_v1.jsonl
   - ❌ Changing compare_tables_v1.jsonl
   - ❌ Adding fields to Step3 evidence_pack

2. **Evidence Inference/Backfill**
   - ❌ Inferring policy from coverage names
   - ❌ Using proposal_facts data
   - ❌ LLM-based estimation
   - ❌ Cross-coverage assumptions

3. **Scope Expansion**
   - ❌ Adding specific surgery attribution logic
   - ❌ Implementing premium ranking
   - ❌ Surgery recommendations
   - ❌ Interpreting "대장용종" or other specific surgery names

4. **Cross-Q Contamination**
   - ❌ Modifying results of Q5, Q7, Q11, Q13
   - ❌ Changing API contracts of other endpoints
   - ❌ Sharing mutable state across queries

---

## Regression Test Results

**Test Command**: `python3 test_q8_regression.py`

**Results**:
```
[1/6] ✅ compare_rows_v1.jsonl: 340 lines (unchanged)
[2/6] ✅ Q5 SSOT exists with 10 records
[3/6] ✅ Q7 SSOT exists with 10 records
[4/6] ✅ Q8 SSOT exists with 10 records (5 PER_EVENT, 3 ANNUAL_LIMIT, 2 UNKNOWN)
[5/6] ✅ compare_tables_v1.jsonl: 1 record
[6/6] ✅ Documentation complete (policy + audit)

ALL REGRESSION CHECKS PASSED
```

---

## Evidence-First Principles (Applied)

1. **No Evidence → UNKNOWN**
   - hyundai: No explicit policy found → UNKNOWN
   - samsung: No explicit policy found → UNKNOWN

2. **Keyword Matching Only**
   - "매회" / "회당" / "수술 1회당" → PER_EVENT
   - "연간 1회" / "연 1회한" → ANNUAL_LIMIT
   - No fuzzy matching or interpretation

3. **Context Validation**
   - Must mention "질병수술비" in surrounding text
   - Coverage name mentions (like "연간1회한" in title) excluded

4. **Conflicting Evidence**
   - More restrictive policy wins (ANNUAL_LIMIT > PER_EVENT)
   - All evidence recorded in evidence_refs

---

## Related Documents

1. **Policy**:
   - `docs/policy/Q8_SURGERY_REPEAT_POLICY_OVERLAY.md` - Complete policy specification
   - `docs/policy/QUESTION_TYPE_REGISTRY.md` - TYPE B classification

2. **Audit**:
   - `docs/audit/Q8_FACT_SNAPSHOT_2026-01-13.md` - Evidence snapshot with SHA256 hashes
   - `docs/audit/Q12_REGRESSION_CHECKLIST.md` - Regression test procedures

3. **Implementation**:
   - `pipeline/step3_evidence_resolver/surgery_repeat_policy_resolver.py` - Core resolver
   - `pipeline/step3_evidence_resolver/generate_q8_surgery_repeat_policy.py` - SSOT generator
   - `apps/api/overlays/q8/` - API overlay module

---

## Freeze Justification

**Why Freeze Q8?**

1. **Evidence Complete**: All 10 insurers processed with documented policy or justified UNKNOWN
2. **API Functional**: GET /q8 endpoint tested and operational
3. **Scope Bounded**: Clear in/out of scope definition prevents future drift
4. **Core Integrity**: SHA256 verification proves no Core Model contamination
5. **Regression Clean**: All existing Q results unchanged

**Risk of NOT Freezing**:
- Scope creep: Adding "대장용종" interpretation
- Cross-Q contamination: Modifying compare_rows for Q8
- Evidence backfill: Inferring policy from coverage names
- LLM hallucination: Generating unsupported policy values

---

## Declaration

> **As of 2026-01-13, Q8 Surgery Repeat Payment Policy Overlay is FROZEN.**
>
> **Any modification violating the above rules SHALL BE CONSIDERED A REGRESSION BUG.**
>
> **SHA256 hashes lock Core Model state. Evidence-first principles lock implementation logic.**
>
> **No scope expansion. No inference. No backfill. No cross-contamination.**

---

**Freeze Authority**: STEP NEXT-Q8-DEMO-SNAPSHOT-β
**Freeze Witness**: SHA256 verification + Regression test suite
**Freeze Date**: 2026-01-13

---

**END OF DECLARATION**
