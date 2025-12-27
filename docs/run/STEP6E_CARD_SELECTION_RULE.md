# STEP 6-ε — Coverage Card Evidence Selection Rule LOCK

**Date**: 2025-12-27
**Scope**: All 8 insurers, All coverages
**Target**: STEP 5 Coverage Card 생성 단계

---

## 목적

Evidence Pack은 충분하나, Coverage Card에 노출되는 최대 3개 evidence의 선택 기준이 비결정적이었다. 본 STEP은 evidence 개수(≤3)를 유지하면서, 어떤 3개를 고르는지 규칙을 LOCK한다.

---

## 문제 정의

**BEFORE (STEP 6-δ.1)**:
- Evidence pack에는 doc_type별 다수 evidence 존재
- Coverage card는 `evidences[:3]` (앞에서 3개만)
- Doc-type 편중 발생 가능 (예: 약관만 3개)
- KB A4200_1: 약관 3개 저장 (사업방법서 evidence는 4번째라 누락)

**문제점**:
- Doc-type diversity 보장 없음
- 사업방법서/상품요약서 evidence가 있어도 coverage card에 미포함 가능

---

## 선택 규칙 (Rule 6-ε)

### Rule 6-ε.1 — Doc-Type Diversity 우선

Coverage Card evidence는 아래 순서로 선택:
1. 약관 1개
2. 사업방법서 1개
3. 상품요약서 1개

※ 해당 doc_type에 evidence가 없으면 skip

### Rule 6-ε.2 — 동일 doc_type 내 우선순위

동일 doc_type에 여러 evidence가 있을 경우:
1. page 번호가 가장 앞선 것
2. snippet 길이 과도하지 않은 것 (≤500자, 기존 규칙 유지)
3. fallback evidence는 후순위 (match_keyword에 "fallback" 포함 시)

### Rule 6-ε.3 — 최대 개수 고정

- 최대 3개 유지 (절대 초과 금지)
- Doc-type 2종만 있으면 2개
- 1종만 있으면 1개

---

## 구현

**변경 파일**: `pipeline/step5_build_cards/build_cards.py`

**추가 함수**: `_select_diverse_evidences()` (build_cards.py:26-70)
```python
def _select_diverse_evidences(evidences: List[Evidence], max_count: int = 3) -> List[Evidence]:
    # Doc-type별로 그룹화
    # 각 doc_type 내에서 정렬 (page 우선, fallback 후순위)
    # Doc-type diversity 순서로 선택 (약관 → 사업방법서 → 상품요약서)
```

**변경 위치**: build_cards.py:122
```python
# BEFORE
evidences=evidences[:3],

# AFTER
selected_evidences = _select_diverse_evidences(evidences, max_count=3)
evidences=selected_evidences,
```

---

## Before / After

### KB A4200_1

| Status | Evidence Count | Doc Types |
|--------|---------------|-----------|
| BEFORE | 3 | 약관 × 3 |
| AFTER | 2 | 약관 × 1, 사업방법서 × 1 |

**AFTER evidences**:
1. 약관 (page 7) - 암진단비(유사암제외)
2. 사업방법서 (page 5) - kb_bm_definition_hit

### Meritz A4200_1

| Status | Evidence Count | Doc Types |
|--------|---------------|-----------|
| BEFORE | 3 | 약관 × 3 |
| AFTER | 2 | 약관 × 1, 상품요약서 × 1 |

**AFTER evidences**:
1. 약관 (page 17) - 암진단비(유사암제외)
2. 상품요약서 (page 1) - 암진단비(유사암제외)

---

## Validation

### pytest
```
75 passed in 0.45s
```
✅ All tests pass

### A4200_1 Verification
- ✅ KB: 약관 + 사업방법서 (diversity 달성)
- ✅ Meritz: 약관 + 상품요약서 (diversity 달성)

### Coverage Cards Regenerated
- ✅ samsung_coverage_cards.jsonl
- ✅ meritz_coverage_cards.jsonl
- ✅ db_coverage_cards.jsonl
- ✅ hanwha_coverage_cards.jsonl
- ✅ lotte_coverage_cards.jsonl
- ✅ kb_coverage_cards.jsonl
- ✅ hyundai_coverage_cards.jsonl
- ✅ heungkuk_coverage_cards.jsonl

### Regression
- ✅ Evidence pack 변화 없음
- ✅ hits_by_doc_type 변화 없음
- ✅ Evidence count ≤ 3 유지

---

## 산출물

1. **Code**: `pipeline/step5_build_cards/build_cards.py` (_select_diverse_evidences 추가)
2. **Coverage Cards**: 8개 보험사 전체 재생성
3. **Documentation**: `docs/run/STEP6E_CARD_SELECTION_RULE.md`

---

## DoD Checklist

- ✅ Coverage Card evidence ≤ 3 유지
- ✅ Doc-type diversity 규칙 명시
- ✅ KB / Meritz 케이스 설명 가능
- ✅ 8개 보험사 regression 0
- ✅ Fact-only 유지
- ✅ pytest PASS
- ✅ 재현 가능한 변경 완료

---

## 결론

Coverage Card evidence 선택 규칙이 명시적으로 고정되었다. Doc-type diversity 우선 원칙으로 약관/사업방법서/상품요약서 각 1개씩 선택하며, KB A4200_1과 같이 사업방법서 evidence가 있는 경우에도 정상적으로 coverage card에 포함된다. 모든 보험사 및 담보에 일관되게 적용되며, 재현 가능하다.
