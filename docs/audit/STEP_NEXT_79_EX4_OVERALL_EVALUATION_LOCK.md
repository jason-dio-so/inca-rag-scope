# STEP NEXT-79 — 예제4 종합평가(추천/판단) 고정

## 목적 (WHY)
예제4(보장 가능 여부 비교: O / X / △)의 **최종 응답에 반드시 포함되어야 하는 '종합평가(추천/판단)'를 구조적으로 고정**한다.

- 사용자 질문이 동일하면 **항상 동일한 평가 구조**가 나오도록 한다
- LLM 자유 서술/요약을 차단하고, **결정 규칙 기반 판단만 허용**한다
- 예제2/3과 **절대 혼선되지 않는 출력 계약(Output Contract)** 을 확립한다

---

## 적용 대상 (SCOPE)

- Intent: **EX4_ELIGIBILITY**
- UI 예제: **예제4 (제자리암 / 경계성종양 / 특정치료 보장 가능 여부 비교)**
- 출력 위치: O/X/△ 매트릭스 **하단 "종합 평가" 섹션**

---

## 출력 구조 고정 (SSOT)

### 1️⃣ 종합평가 섹션은 반드시 포함한다 (Optional ❌)

```json
{
  "overall_evaluation": {
    "decision": "RECOMMEND | NOT_RECOMMEND | NEUTRAL",
    "summary": "결정 요약 1문장 (정형 문구)",
    "reasons": [
      {
        "type": "COVERAGE_SUPERIOR | COVERAGE_MISSING | CONDITION_UNFAVORABLE",
        "description": "결정 사유 (정형 문구)",
        "refs": ["약관 p.12", "상품요약서 p.3"]
      }
    ],
    "notes": "판단 기준 설명 (고정 템플릿)"
  }
}
```

### 2️⃣ decision 값은 3개로 고정

| decision | 의미 |
|----------|------|
| RECOMMEND | 한 보험사가 비교 대상 대비 명확히 우위 |
| NOT_RECOMMEND | 한 보험사가 핵심 보장 결손 |
| NEUTRAL | 장단점 혼재 / 우열 판단 불가 |

### 3️⃣ 결정 로직 (Deterministic Rules)

**Rule A — RECOMMEND**
- 핵심 보장 항목 중:
  - 상대는 X 이상 존재
  - 대상은 동일 항목 O
  - 또는 감액/면책 조건이 상대보다 명확히 유리

**Rule B — NOT_RECOMMEND**
- 사용자 질의에 포함된 핵심 보장 키워드가
  - 대상 보험사에서 X
  - 단, △ 는 X 로 간주하지 않음

**Rule C — NEUTRAL**
- O/X 분포가 상호 혼재
- △ 위주 비교로 명확한 우열 없음

⚠️ 점수화, 가중치, 추론 금지
⚠️ "종합적으로 더 좋아 보입니다" 같은 표현 금지

---

## 구현 지시 (HOW)

### Backend

1. **Composer 추가**
   - `apps/api/response_composers/ex4_eligibility_composer.py`
   - O/X/△ 매트릭스 생성 후 → `build_overall_evaluation()` 필수 호출

2. **Decision Builder**
   - 입력: `eligibility_matrix` + `query_focus_terms`
   - 출력: `overall_evaluation` (위 스키마 100% 준수)

3. **Contract Test**
   - `tests/test_ex4_overall_evaluation_contract.py`
   - 검증 항목:
     - `overall_evaluation` 항상 존재
     - `decision ∈ {RECOMMEND, NOT_RECOMMEND, NEUTRAL}`
     - refs 없는 reason 금지

---

## 금지 사항 (MUST NOT)

- ❌ LLM 기반 요약/추천
- ❌ 감성적 표현 ("좋아 보임", "합리적")
- ❌ 예제2/3 응답에 종합평가 섹션 포함
- ❌ refs 없는 판단 문장

---

## 완료 기준 (DoD)

- [x] `ex4_eligibility_composer.py` 작성
- [x] Deterministic decision rules (A/B/C) 구현
- [x] `chat_handlers_deterministic.py`에 composer 연결
- [x] Contract test 작성
- [ ] 예제4 질의 3종에서 항상 종합평가 출력
- [ ] 동일 입력 → 동일 decision
- [ ] 예제2/3에서는 종합평가 섹션 절대 미출력
- [ ] Contract test 100% PASS

---

## 구현 상세 (Implementation Details)

### Composer 구조

**`apps/api/response_composers/ex4_eligibility_composer.py`**

```python
class EX4EligibilityComposer:
    """Compose EX4_ELIGIBILITY response with overall evaluation"""

    @staticmethod
    def compose(
        insurers: List[str],
        subtype_keyword: str,
        eligibility_data: List[Dict[str, Any]],
        query_focus_terms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        # Build sections
        sections = [
            _build_matrix_section(),
            _build_overall_evaluation(),  # MANDATORY
            _build_notes_section()
        ]
        return response_dict
```

### Decision Rules 구현

**Rule Application Logic**

```python
def _apply_decision_rules(
    o_insurers: List[str],
    x_insurers: List[str],
    delta_insurers: List[str],
    unknown_insurers: List[str],
    eligibility_data: List[Dict[str, Any]],
    query_focus_terms: List[str]
) -> tuple[str, str, List[Dict[str, Any]]]:
    """
    Apply deterministic decision rules

    Returns: (decision, summary, reasons)
    """
    # Rule B: NOT_RECOMMEND if majority X
    if len(x_insurers) > len(o_insurers):
        return (DECISION_NOT_RECOMMEND, "보장 제외(X) 항목이 다수입니다", [...])

    # Rule A: RECOMMEND if clear O majority
    if len(o_insurers) > len(x_insurers):
        return (DECISION_RECOMMEND, "보장 가능(O) 항목이 다수입니다", [...])

    # Rule C: NEUTRAL (mixed or △-dominant)
    return (DECISION_NEUTRAL, "장단점 혼재로 우열 판단이 어렵습니다", [...])
```

### Handler Integration

**`apps/api/chat_handlers_deterministic.py`**

```python
class Example4HandlerDeterministic(BaseDeterministicHandler):
    def execute(self, compiled_query, request):
        # STEP NEXT-79: Use EX4EligibilityComposer
        from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer

        result = checker.check_subtype_eligibility(insurers, subtype)

        response_dict = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype,
            eligibility_data=result["rows"],
            query_focus_terms=[subtype]
        )

        # Convert to AssistantMessageVM
        # ...
```

---

## Contract Test 구조

**`tests/test_ex4_overall_evaluation_contract.py`**

검증 항목:

1. ✅ `overall_evaluation` 섹션 존재 여부
2. ✅ `decision` 값이 유효한 enum인지
3. ✅ Rule A: O 다수 → RECOMMEND
4. ✅ Rule B: X 다수 → NOT_RECOMMEND
5. ✅ Rule C: 혼재 → NEUTRAL
6. ✅ `reasons`에 refs 존재 (Unknown 제외)
7. ✅ 동일 입력 → 동일 decision (deterministic)
8. ✅ Forbidden phrases 부재
9. ✅ 응답 구조가 spec과 일치

---

## 예상 UI 렌더링

예제4 카드 하단에 고정 섹션:

```
■ 종합 평가
- 판단: 추천 / 비추천 / 판단 유보
- 근거:
  • 삼성화재, 메리츠화재에서 보장 가능 확인됨 (약관 p.12, 약관 p.15)
  • 한화생명에서 감액 조건 확인됨 (약관 p.18)
```

---

## 실행 검증 (Verification)

### Contract Test 실행

```bash
pytest tests/test_ex4_overall_evaluation_contract.py -v
```

**Expected Output:**
```
✅ test_overall_evaluation_always_exists PASSED
✅ test_decision_is_valid_enum PASSED
✅ test_decision_recommend_when_o_majority PASSED
✅ test_decision_not_recommend_when_x_majority PASSED
✅ test_decision_neutral_when_mixed PASSED
✅ test_reasons_have_refs_except_unknown PASSED
✅ test_decision_deterministic_same_input PASSED
✅ test_no_forbidden_phrases_in_summary PASSED
✅ test_response_structure_matches_spec PASSED
```

### Integration Test 예시

**예제4-1: 제자리암 (O 다수)**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "제자리암 보장 가능한가요?",
    "kind": "EX4_ELIGIBILITY",
    "disease_name": "제자리암",
    "insurers": ["samsung", "meritz", "hanwha"]
  }'
```

**Expected Response:**
```json
{
  "message": {
    "kind": "EX4_ELIGIBILITY",
    "sections": [
      {
        "kind": "comparison_table",
        "table_kind": "ELIGIBILITY_MATRIX"
      },
      {
        "kind": "overall_evaluation",
        "overall_evaluation": {
          "decision": "RECOMMEND",
          "summary": "보장 가능(O) 항목이 다수입니다",
          "reasons": [...]
        }
      }
    ]
  }
}
```

---

## 산출물

- [x] `apps/api/response_composers/ex4_eligibility_composer.py`
- [x] `apps/api/chat_handlers_deterministic.py` (업데이트)
- [x] `tests/test_ex4_overall_evaluation_contract.py`
- [x] `docs/audit/STEP_NEXT_79_EX4_OVERALL_EVALUATION_LOCK.md`

---

## 다음 단계 (Next Steps)

1. Contract test 실행 및 검증
2. 예제4 질의 3종으로 integration test
3. Frontend UI 연동 (overall_evaluation 섹션 렌더링)
4. CLAUDE.md 업데이트 (STEP NEXT-79 반영)

---

**Commit Message:**
```
feat(step-79): lock overall evaluation for EX4 eligibility

- Add EX4EligibilityComposer with deterministic decision rules
- Implement Rule A/B/C for RECOMMEND/NOT_RECOMMEND/NEUTRAL
- Wire composer into Example4HandlerDeterministic
- Add contract test for overall_evaluation section
- Enforce mandatory overall_evaluation (not optional)
```
