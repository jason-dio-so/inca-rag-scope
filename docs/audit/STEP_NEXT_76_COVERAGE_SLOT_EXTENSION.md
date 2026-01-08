# STEP NEXT-76: Coverage Slot Extension + Capability Boundary

**Status:** ✅ COMPLETED
**Date:** 2026-01-08
**Constitutional Compliance:** ✅ Evidence-based ONLY (No LLM, No inference)

---

## 🎯 Objective

**76-A**: Extend coverage slots to answer customer questions 1-5, 8 without LLM/inference
**76-B**: Create capability boundary document to align customer·sales·planning expectations

---

## 📦 STEP NEXT-76-A: Slot Extension

### New Extended Slots (4 slots added)

#### 1. `underwriting_condition` (유병자 인수 조건)
**Customer Question**: "고혈압/당뇨 있어도 가입 가능한가?"

**Keywords**:
- 유병자, 고혈압, 당뇨, 당뇨병
- 인수 가능, 가입 가능, 건강고지
- 특별조건, 할증, 인수 조건

**Doc Priority**: 사업방법서 > 가입설계서 > 약관

#### 2. `mandatory_dependency` (필수 가입 조건)
**Customer Question**: "이 특약만 단독 가입 가능한가?"

**Keywords**:
- 주계약 필수, 필수 가입
- 최소 가입금액, 동시 가입
- 의무 가입, 단독가입, 특약만

**Doc Priority**: 약관 > 가입설계서

#### 3. `payout_frequency` (지급 빈도)
**Customer Question**: "여러 번 재발해도 계속 받을 수 있나?"

**Keywords**:
- 1회한, 최초 1회한
- 연간, 연 1회, 매년, 평생
- 재발, 재진단, 반복지급
- 회수 제한, 지급회수

**Doc Priority**: 약관 > 상품요약서

#### 4. `industry_aggregate_limit` (업계 누적 한도)
**Customer Question**: "다른 보험사 가입도 영향 주나?"

**Keywords**:
- 업계 누적, 타사 가입
- 합산, 총 한도, 전체 한도
- 다른 보험사, 타 보험사
- 누적한도, 통산한도

**Doc Priority**: 사업방법서 > 약관

---

### Slot Status (Same as Core Slots)
- **FOUND**: Evidence from coverage-specific section
- **FOUND_GLOBAL**: Evidence from global/common section
- **CONFLICT**: Multiple conflicting evidences
- **UNKNOWN**: No evidence found

---

### Implementation

**Files Created/Modified**:
1. `pipeline/step1_summary_first/extended_slot_schema.py` (NEW)
   - Extended slot dataclass definitions
   - Slot registry
   - Excluded slots documentation

2. `pipeline/step3_evidence_resolver/evidence_patterns.py` (MODIFIED)
   - Added 4 new EvidencePattern entries
   - Keywords for each extended slot
   - Context lines and table priority

3. `pipeline/step4_compare_model/model.py` (MODIFIED)
   - Added 4 new SlotValue fields to CompareRow
   - Updated to_dict() to include extended slots

4. `docs/ACTIVE_CONSTITUTION.md` (MODIFIED)
   - Section 10: Coverage Slot Extensions
   - Slot taxonomy (core + extended)
   - Extension rules
   - Excluded slots (intentional)

---

### Excluded Slots (Intentional)

❌ **NOT supported** (out of scope):
- `discount` (할인) - Marketing policy
- `refund_rate` (환급률) - Savings feature
- `family_discount` (가족결합) - Marketing
- `marketing_phrases` (홍보 문구) - Subjective

**Reason**: No evidence-based comparison possible

---

## 📋 STEP NEXT-76-B: Capability Boundary Document

### Purpose
Prevent expectation mismatch between customers, sales, and planning teams.

### Document Location
`docs/CAPABILITY_BOUNDARY.md`

### Question Categories

#### 🟢 GREEN (Immediately Answerable)
- Core slots active (start_date, exclusions, payout_limit, reduction, entry_age, waiting_period)
- Evidence-based with FOUND/FOUND_GLOBAL status
- Examples:
  - "암 진단비 보장 한도는?"
  - "면책기간/감액기간은?"
  - "재발 시에도 지급되나?"

#### 🟡 YELLOW (Conditionally Answerable)
- Extended slots needed (STEP NEXT-76-A)
- Additional customer info required
- Examples:
  - "고혈압 있어도 가입 가능?" (underwriting_condition)
  - "다른 보험사 가입 영향?" (industry_aggregate_limit)
  - "특약 단독 가입 가능?" (mandatory_dependency)

#### 🔴 RED (Intentionally Unsupported)
- No evidence base in insurance documents
- Marketing/savings features
- Examples:
  - "결합 할인 받을 수 있나?" ❌
  - "만기 환급금은?" ❌
  - "고객 평가는 어떤가?" ❌

---

### Fixed Customer Communication

**UI Display Message**:
```
본 시스템은 보험 '보장 조건'만을 약관 근거로 비교·추천합니다.

✅ 가능: 보장 내용, 지급 조건, 제외 사항 비교
❌ 불가: 할인, 환급, 마케팅 요소

모든 비교 결과는 약관/상품요약서 근거와 함께 제공됩니다.
```

**Chatbot Initial Message**:
```
안녕하세요! 보험 보장 조건 비교 시스템입니다.

이 시스템은:
• 보장 내용, 지급 조건을 약관 근거로 비교합니다
• 각 항목마다 약관 페이지/문구를 함께 보여드립니다
• 할인/환급/마케팅 요소는 포함하지 않습니다

어떤 보장 조건을 비교하고 싶으신가요?
```

---

## 🚦 Constitutional Compliance

### Slot Extension Rules (from ACTIVE_CONSTITUTION Section 10)

✅ **MUST**:
- Evidence-based ONLY (약관/요약서/사업방법서)
- Step3 Evidence Resolver fills slots
- Same GATE rules as existing slots

❌ **MUST NOT**:
- NO LLM calls
- NO inference/calculation
- NO marketing/savings features

---

## 📊 Impact

### Pipeline Stages

**Step1**:
- Extended slot schema defined (`extended_slot_schema.py`)
- Slots remain empty (placeholders)

**Step3**:
- Evidence patterns extended (4 new patterns)
- Evidence Resolver will populate extended slots
- Same gates apply (G1-Evidence, G2-Status, G3-Conflict)

**Step4**:
- CompareRow model extended (4 new SlotValue fields)
- to_dict() includes extended slots
- Backward compatible (extended slots optional)

**Step5**:
- Extended slots accessible in rule catalog
- Can create rules based on extended slots
- Example: "유병자 가입 가능한 상품 추천"

---

## 🔧 Next Steps (Future)

### Phase 2 Extensions (Conditional)
- Insurance premium table integration → premium calculation
- Customer existing policy info → aggregate limit calculation
- Health info input → underwriting eligibility check

### Intentionally Excluded (Forever)
- ❌ Discount/refund features (conflicts with system identity)
- ❌ Marketing elements (no evidence base)

---

## ✅ Definition of Done

- [x] Extended slot schema defined (4 slots)
- [x] Evidence patterns extended (Step3)
- [x] CompareRow model updated (Step4)
- [x] Step5 can access extended slots
- [x] Capability boundary document created
- [x] ACTIVE_CONSTITUTION updated (Section 10)
- [x] Customer communication messages defined
- [x] Excluded slots documented

---

## 📝 Files Modified/Created

### Created
1. `pipeline/step1_summary_first/extended_slot_schema.py`
2. `docs/CAPABILITY_BOUNDARY.md`
3. `docs/audit/STEP_NEXT_76_COVERAGE_SLOT_EXTENSION.md`

### Modified
1. `pipeline/step3_evidence_resolver/evidence_patterns.py`
2. `pipeline/step4_compare_model/model.py`
3. `docs/ACTIVE_CONSTITUTION.md`

---

## 🎯 Key Takeaways

1. **Slot Extension is Conservative**
   - Only 4 slots added (not 10+)
   - Each slot addresses specific customer question
   - No speculative features

2. **Capability Boundary is Explicit**
   - Clear GREEN/YELLOW/RED categories
   - Fixed customer communication messages
   - Prevents expectation mismatch

3. **Constitutional Compliance Maintained**
   - Evidence-based ONLY
   - No LLM, no inference
   - Same gates as core slots

4. **Backward Compatible**
   - Extended slots are optional
   - Core slots unchanged
   - Existing pipelines unaffected

---

**STEP NEXT-76 COMPLETE** ✅

Extended slots are ready for Step3 Evidence Resolver to populate.
Capability boundary document ready for customer/sales/planning alignment.
