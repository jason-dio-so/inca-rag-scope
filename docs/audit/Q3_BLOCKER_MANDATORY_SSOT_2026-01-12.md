# Q3 BLOCKER: Mandatory Coverage SSOT Missing

**Date**: 2026-01-12
**Task**: STEP NEXT-P2-Q3
**Status**: ❌ **BLOCKED**
**Blocker Type**: No Mandatory Coverage SSOT

---

## Executive Summary

**Q3 Implementation CANNOT proceed** due to missing mandatory coverage SSOT in Step4 Compare Model output.

**Customer Question**: "의무담보를 최소화한 상품을 추천해줘. (기본 계약만으로 구성된 저렴한 상품을 찾고 싶어.)"

**Required Data**:
- Coverage-level mandatory/optional classification
- Mandatory coverage identification across all insurers
- Premium breakdown by mandatory vs optional coverages

**Current Status**:
- ❌ 100% of mandatory_dependency slots are UNKNOWN (340/340 rows)
- ❌ No coverage-level mandatory classification exists
- ❌ No alternative mandatory coverage indicators found

---

## Data Reality Check (2026-01-12)

### Source
`data/compare_v1/compare_rows_v1.jsonl` (Step4 Compare Model output)

### Mandatory Coverage SSOT Status

```
Slot Name            | UNKNOWN | FOUND | Total
---------------------|---------|-------|-------
mandatory_dependency | 340     | 0     | 340
```

**100% attribution failure** — No SSOT available for any insurer.

---

## Root Cause Analysis

### 1. mandatory_dependency Slot Completely Empty

**Schema Check**:
```json
{
  "slots": {
    "mandatory_dependency": {
      "status": "UNKNOWN",
      "value": null,
      "evidences": []
    }
  }
}
```

**Status Across All Rows**:
- ✅ Slot exists in schema
- ❌ All 340 rows have status: "UNKNOWN"
- ❌ All 340 rows have value: null
- ❌ No evidences found

### 2. No Alternative Mandatory Indicators

**Checked Fields**:
1. Coverage title keywords ("기본계약", "주계약", "의무", "필수"): 0 matches
2. Row-level mandatory flags: None exist
3. Meta fields with "mandatory/basic/base": None exist

**Conclusion**: Step3 Evidence Resolver did not extract mandatory coverage information from documents.

### 3. Why Step3 Failed to Extract

**Possible Reasons**:
1. **Slot Not Defined in Step1 Schema**: mandatory_dependency may not have extraction rules
2. **Document Structure Issue**: Mandatory coverage info may be in product-level sections, not coverage-level
3. **No Explicit Keyword Patterns**: Documents may use implicit language (e.g., "주계약에 부가" without listing which is 주계약)
4. **Out of Scope for Step3**: Mandatory/optional classification may require product-structure analysis, not document text extraction

---

## Q3 Requirements (Cannot Be Met)

### From STEP NEXT-P2-Q3 Directive

**Input Requirements**:
> "compare_rows_v1.jsonl 내 mandatory/basic/기본계약/주계약/의무 관련 슬롯/플래그를 사용"

**Current Reality**:
- ❌ No "mandatory" slot with data
- ❌ No "basic/기본계약" slot exists
- ❌ No "주계약/의무" flags available

**Directive for Missing SSOT**:
> "없으면 '의무담보 SSOT 없음'으로 처리하고 Q3는 BLOCKED 처리(추정 금지)"

**Decision**: ✅ Follow directive — Mark Q3 as BLOCKED with "의무담보 SSOT 없음"

---

## Forbidden Actions (SSOT Policy)

**Q3 Directive Explicitly Forbids**:
1. ❌ "의무담보를 코드/이름 패턴으로 추정 금지"
2. ❌ Inferring mandatory status from coverage codes (e.g., A1300 = 상해사망)
3. ❌ Using product-level assumptions (e.g., "CI products always have A4200_1 as mandatory")
4. ❌ Estimating mandatory premium by filtering "common" coverages

**Why These Are Forbidden**:
- Different insurers have different mandatory coverage structures
- Same coverage code may be mandatory in one product, optional in another
- Product-level mandatory definitions vary by insurer policy
- Cannot guarantee accuracy without explicit SSOT

---

## Required Fix (Out of Scope for Q3)

**Step3 Evidence Resolver Enhancement Needed**:

### Option 1: Add mandatory_dependency Slot Extraction
- **Scope**: Modify Step1 slot schema to define mandatory_dependency extraction rules
- **Challenge**: Documents may not explicitly state "이 담보는 의무입니다"
- **Estimated Effort**: 3-5 days (requires document pattern research)

### Option 2: Product-Structure Analysis
- **Scope**: Create new pipeline step to analyze product-coverage relationships
- **Data Source**: Use "주계약/특약" hierarchy in documents
- **Estimated Effort**: 5-7 days (new pipeline step)

### Option 3: Manual SSOT Creation
- **Scope**: Manually review all 8 insurers' product structures
- **Output**: Create `data/manual_ssot/mandatory_coverages.json`
- **Estimated Effort**: 2-3 days (manual work)
- **Problem**: Not reproducible, breaks automation

**Recommendation**: Pursue Option 2 (product-structure analysis) for scalable solution.

---

## Q3 Classification Logic (Cannot Implement)

**Decision Table** (from STEP NEXT-P2-Q3 directive):

| Classification | Criteria | Data Required |
|----------------|----------|---------------|
| MINIMAL_MANDATORY | 의무담보만 + 최저 보험료 | ✅ mandatory coverage list<br>✅ mandatory premium sum |
| OPTIONAL_HEAVY | 의무+선택 혼합 + 고보험료 | ✅ optional coverage list<br>✅ total premium breakdown |
| UNKNOWN | SSOT 부족 | ❌ No mandatory SSOT |

**Actual Available Data**:
- ❌ Cannot identify mandatory coverages → Cannot classify any product
- ❌ Cannot calculate mandatory premium sum → Cannot rank by "minimal mandatory"
- ❌ Cannot distinguish mandatory vs optional → Cannot compare products

**Decision**: All 8 insurers classified as **UNKNOWN** with reason:
```json
{
  "insurer_key": "samsung",
  "classification": "UNKNOWN",
  "mandatory_coverages": null,
  "mandatory_premium_sum": null,
  "reason": "MANDATORY_COVERAGE_SSOT_MISSING",
  "notes": "Step3 did not extract mandatory_dependency slot data. All 340 coverage rows have UNKNOWN status. Requires product-structure analysis or manual SSOT."
}
```

---

## Alternative Approach (NOT RECOMMENDED)

### Option A: Infer from Coverage Codes (POLICY VIOLATION)
- Use A1300 (상해사망) as proxy for "mandatory coverage"
- **Problem**: Violates "추정 금지" directive

### Option B: Use Common Coverages (UNRELIABLE)
- Classify coverages present in 8/8 insurers as "mandatory"
- **Problem**: No guarantee of mandatory status

### Option C: Partial Implementation with Disclaimer (MISLEADING)
- Implement for 1-2 manually verified insurers
- Output UNKNOWN for others
- **Problem**: Incomplete user experience (6-7/8 insurers = "데이터 없음")

**Recommendation**: **DO NOT IMPLEMENT Q3 until mandatory coverage SSOT is created.**

---

## Customer Communication (Phase 3)

Per **STEP NEXT-P2-Q3** directive:

**Q3 is Phase 2, but BLOCKED** → Moves to **Phase 3 (설명 대상)**

**Customer Message** (for WHY_SOME_QUESTIONS_UNAVAILABLE.md):

```markdown
### Q3: 의무담보 최소화 추천

**질문**: "의무담보를 최소화한 상품을 추천해줘. 기본 계약만으로 구성된 저렴한 상품을 찾고 싶어."

**현재 상태**: 제공 불가

**이유**:
보험 상품의 "의무담보(기본 계약)"와 "선택담보(특약)"를 구분하는 정보가
현재 시스템에 등록되어 있지 않습니다.

약관 문서에는 담보별 조건이 상세히 기재되어 있으나,
"이 담보가 필수인지, 선택 가능한지"에 대한 명시적 표시가 부족합니다.

**필요한 개선**:
- 보험사별 상품 구조 분석 (주계약/특약 구분)
- 의무담보 목록 추출 로직 개발
- 담보별 필수/선택 속성 SSOT 구축

**대안**:
- 보험사 홈페이지에서 "간편 가입" 또는 "기본형" 상품 조회
- 설계사에게 "의무담보만으로 구성된 최저 보험료" 견적 요청
- 비교 사이트에서 "특약 제외" 옵션 사용 (일부 사이트 제공)
```

---

## Comparison with Q5 BLOCKER

| Aspect | Q5 (감액/면책) | Q3 (의무담보) |
|--------|----------------|---------------|
| **Slot Exists?** | ✅ Yes | ✅ Yes |
| **Evidence Extracted?** | ✅ Yes (documents have 면책기간) | ❌ No (no mandatory info in documents) |
| **Problem** | Attribution failure (G5 Gate) | Extraction failure (no data at all) |
| **Data Availability** | 12.5% FOUND (1/8) | 0% FOUND (0/8) |
| **Root Cause** | Evidence exists but cannot attribute to coverage | Evidence does not exist in extracted data |
| **Fix Required** | Improve G5 Gate logic | Add product-structure analysis |
| **Estimated Effort** | 2-3 days (Step3 enhancement) | 5-7 days (new pipeline step) |

**Conclusion**: Q3 is MORE BLOCKED than Q5 — no data at all vs. attribution failure.

---

## Next Actions

### Immediate (2026-01-12)
1. ✅ Document Q3 BLOCKER (this file)
2. ⏳ Update STATUS.md: Q3 marked as **BLOCKED**
3. ⏳ Add Q3 entry to customer explanation (WHY_SOME_QUESTIONS_UNAVAILABLE.md)
4. ⏳ Report to user: Q3 BLOCKED, Phase 2 has 0/3 implementable (Q5, Q3 blocked; Q11 remains)

### Future (When Product-Structure Analysis is Ready)
1. Design product-structure analysis pipeline step
2. Extract 주계약/특약 hierarchy from documents
3. Create mandatory_coverages SSOT
4. Re-attempt Q3 implementation

---

**Document Version**: 1.0
**Status**: 🔒 **LOCKED** (BLOCKER EVIDENCE)
**Last Updated**: 2026-01-12
**Review Trigger**: Product-structure analysis pipeline completion
