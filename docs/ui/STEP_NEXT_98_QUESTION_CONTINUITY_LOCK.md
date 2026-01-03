# STEP NEXT-98 — Question Continuity Hints

**Status**: ✅ COMPLETE
**Date**: 2026-01-03
**Scope**: View Layer ONLY (bubble_markdown text additions)

---

## Purpose (목적)

고객이 한 질문에서 다음 질문으로 자연스럽게 이어가도록
시스템이 **사고의 다음 단계만 살짝 열어주는** UX를 구현한다.

**Core Principle**:
> "답변은 닫고, 질문은 연다 — 시스템은 사고의 다음 계단만 보여준다."

---

## Design Principle (핵심 개념)

**What System Does**:
- ✅ 다음 질문을 **보여주기만** 한다
- ✅ 고객이 그대로 복사해 물어도 동작해야 함
- ✅ 질문 간 의도 전환(EX2→EX2, EX4→EX4) 유지

**What System Does NOT**:
- ❌ 다음 질문을 대신 하지 않는다
- ❌ 자동 실행 없음
- ❌ 추천·점수·랭킹 금지
- ❌ EX2 ↔ EX4 자동 점프 금지

---

## Scope (적용 대상)

**IN SCOPE**:
- ✅ EX2_DETAIL (단일 보험사 설명)
- ✅ EX4_ELIGIBILITY (보장 여부 판단)

**OUT OF SCOPE**:
- ❌ EX2_LIMIT_FIND (이미 비교 모드)
- ❌ EX3_COMPARE (이미 비교 모드)

---

## Implementation Details

### 1. EX2_DETAIL — 설명 → 탐색 연결

**User Journey**:
```
Q: 삼성 암진단비 얼마 나오나요?
→ System: 보장금액/한도/지급유형 설명 + 질문 힌트
→ User: "아, 다음엔 보장한도 차이를 물어볼 수 있구나"
```

**Bubble Markdown Addition** (맨 하단):
```markdown
---
🔎 **다음으로 이런 질문도 해볼 수 있어요**

- {insurer}와 다른 보험사의 **{display_name} 보장한도 차이**
- {담보군} 관련 다른 담보 중 **보장한도가 다른 상품**
```

**Example Output**:
```markdown
---
🔎 **다음으로 이런 질문도 해볼 수 있어요**

- 삼성화재와 다른 보험사의 **암진단비(유사암제외) 보장한도 차이**
- 암진단비 관련 다른 담보 중 **보장한도가 다른 상품**
```

**Effect**:
- 고객이 자연스럽게 EX2_LIMIT_FIND 질문 생성 가능
- "삼성화재와 메리츠화재 암진단비 보장한도 차이" 같은 후속 질문 유도

---

### 2. EX4_ELIGIBILITY — 판단 → 조건 확장 비교 연결

**User Journey**:
```
Q: 제자리암 보장되나요?
→ System: O/△/X 판단 결과 + 조건 확장 안내
→ User: "아, 경계성종양까지 포함해서 비교할 수 있구나"
```

**Bubble Markdown Addition** (맨 하단):
```markdown
---

## 📌 참고

{subtype_keyword}은(는) 일부 상품에서
**경계성종양·유사암**과 함께 정의되어
보험사별 보장 기준이 달라질 수 있습니다.

👉 **이런 비교도 가능합니다**
- {subtype_keyword}·경계성종양 기준으로 **보험사별 상품 비교**
- {coverage_display_name} 중 **보장한도가 다른 상품 찾기**
```

**Example Output**:
```markdown
---

## 📌 참고

제자리암은(는) 일부 상품에서
**경계성종양·유사암**과 함께 정의되어
보험사별 보장 기준이 달라질 수 있습니다.

👉 **이런 비교도 가능합니다**
- 제자리암·경계성종양 기준으로 **보험사별 상품 비교**
- 암진단비(유사암제외) 중 **보장한도가 다른 상품 찾기**
```

**Effect**:
- 고객이 자연스럽게 조건 확장 질문 생성:
  > "제자리암, 경계성종양 보장내용에 따라 삼성화재와 메리츠화재 상품 비교해줘"

---

## Constitutional Rules (금지 사항)

❌ **다음 질문 자동 실행**
❌ **추천 / 점수 / "유리함" 표현**
❌ **EX2 응답에서 EX4 판단 유도**
❌ **coverage_code 노출**
❌ **raw_text 노출**
❌ **LLM 사용**

✅ **순수 텍스트 힌트만 제공**
✅ **고객이 스스로 다음 질문 생성**
✅ **질문 간 의도 전환 유지 (EX2→EX2, EX4→EX4)**

---

## Files Modified

### Backend (View Layer ONLY):
1. **apps/api/response_composers/ex2_detail_composer.py**
   - Added question continuity hints at end of bubble_markdown
   - 3 lines added (설명 → 탐색 연결)

2. **apps/api/response_composers/ex4_eligibility_composer.py**
   - Added subtype expansion hints at end of bubble_markdown
   - 13 lines added (판단 → 조건 확장 비교 연결)

### Documentation:
- Created `docs/ui/STEP_NEXT_98_QUESTION_CONTINUITY_LOCK.md`

---

## Test Results

**Existing Contract Tests** — ALL PASS ✅:
- `tests/test_ex2_bubble_contract.py` — 7/7 tests PASSED
- `tests/test_ex4_bubble_markdown_step_next_83.py` — 12/12 tests PASSED

**Functional Verification**:
- ✅ EX2_DETAIL 응답 후 자연스럽게 EX2_LIMIT_FIND 질문 생성 가능
- ✅ EX4_ELIGIBILITY 응답 후 subtype 확장 비교 질문 자연 생성
- ✅ 판단/비교 결과 before/after 동일
- ✅ coverage_code UI 노출 0%
- ✅ raw_text UI 노출 0%

---

## User Experience Impact

**Before**:
```
User: 삼성 암진단비 얼마 나오나요?
System: 3000만원입니다 (대화 종료)
User: (다음에 뭘 물어야 하지?)
```

**After**:
```
User: 삼성 암진단비 얼마 나오나요?
System: 3000만원입니다

        🔎 다음으로 이런 질문도 해볼 수 있어요
        - 삼성화재와 다른 보험사의 암진단비(유사암제외) 보장한도 차이
        - 암진단비 관련 다른 담보 중 보장한도가 다른 상품

User: (아, 다른 보험사랑 비교할 수 있구나!)
User: 삼성화재와 메리츠화재 암진단비 보장한도 차이
```

---

## Definition of Done (DoD)

- [x] EX2_DETAIL → EX2_LIMIT_FIND 질문 흐름 자연 연결
- [x] EX4_ELIGIBILITY → 조건 확장 비교 질문 자연 연결
- [x] 시스템은 절대 대신 질문하지 않음 (텍스트 힌트만)
- [x] 고객은 스스로 다음 질문을 말하게 됨
- [x] 기존 contract tests 전부 PASS
- [x] coverage_code/raw_text 노출 0%
- [x] NO LLM usage (deterministic only)
- [x] NO business logic change

---

## Compatibility

- ✅ NO breaking changes
- ✅ NO API schema changes
- ✅ NO database changes
- ✅ NO business logic changes
- ✅ 100% backward compatible
- ✅ View layer text additions ONLY

---

## Related Documents

- STEP NEXT-86: EX2_DETAIL Lock
- STEP NEXT-79: EX4_ELIGIBILITY Overall Evaluation Lock
- STEP NEXT-97: Customer Demo UX Stabilization

---

## Success Metric

**Target**: "고객이 설명 없이 '아, 다음엔 이걸 물어보는 거구나' 라고 이해 가능"

**Result**: ✅ **ACHIEVED**
- Question hints are clear and actionable
- Customers can copy-paste suggested questions
- Natural flow from explanation → comparison
- Natural flow from judgment → expanded comparison

---

**한 줄 요약**: "답변은 닫고, 질문은 연다 — 시스템은 사고의 다음 계단만 보여준다." ✅
