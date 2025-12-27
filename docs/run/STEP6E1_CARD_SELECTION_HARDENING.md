# STEP 6-ε.1 — Coverage Card Evidence Selection Hardening

**Date**: 2025-12-27
**Scope**: STEP 5 (build_cards) evidence selection logic ONLY
**변경 파일**: `pipeline/step5_build_cards/build_cards.py`

---

## 목적 (WHY)

STEP 6-ε에서 doc-type 다양성 선택 규칙은 도입됐지만:
- **(A) 개수 부족 문제**: doc_type이 1~2개만 존재하는 경우 카드 evidence가 2개/1개로 감소
- **(B) fallback 판정 불명확**: match_keyword 문자열 의존으로 누락 가능성

→ **deterministic fill-up + 엄격한 fallback 판정**을 추가하여 재현 가능한 일관성 확보

---

## 변경 규칙 (WHAT)

### Rule 6-ε.1 — "항상 max_count까지 채우기 (Fill-up)"

`_select_diverse_evidences(evidences, max_count)`는:
1. **1차 선택 (diversity pass)**: 약관/사업방법서/상품요약서에서 가능한 한 각 1개씩
2. **2차 보충 (fill-up pass)**: 선택 개수가 `max_count` 미만이면,
   - 남은 evidence pool을 정렬 후 상위부터 추가
   - 최대 `max_count`까지 채움
3. **결과**: `0 <= len(selected) <= max_count` 보장
   - evidence가 충분하면 `len(selected) == max_count` 달성

### Rule 6-ε.2 — Evidence 정렬 우선순위 (Deterministic)

모든 선택에서 evidence 우선순위:
1. **Non-fallback 우선**
2. **doc_type priority**: 약관 > 사업방법서 > 상품요약서
3. **page 오름차순** (앞 페이지 우선)
4. **(동률) file_path 문자열 오름차순** (완전결정성 확보용)

### Rule 6-ε.3 — Fallback 판정 (엄격)

fallback 판정: `match_keyword`에 `fallback_` 포함 시 `True`
- 예: `fallback_token_and(...)` → fallback
- 예: `token_and(...)` → non-fallback

---

## Before / After

### Before (STEP 6-ε)

KB A4200_1 (암진단비(유사암제외)):
- Evidence: **2개** (약관 1개, 사업방법서 1개)
- doc_type이 2개만 존재하여 3개 미만 선택

Meritz A4200_1:
- Evidence: **2개** (약관 1개, 상품요약서 1개)
- doc_type이 2개만 존재하여 3개 미만 선택

### After (STEP 6-ε.1)

KB A4200_1:
```
1. doc_type=약관, page=7, match_keyword=암진단비(유사암제외)
2. doc_type=사업방법서, page=5, match_keyword=kb_bm_definition_hit
3. doc_type=약관, page=7, match_keyword=암진단비(유사암제외)
```
→ **3개** (약관 1개, 사업방법서 1개, 약관 추가 1개로 fill-up)

Meritz A4200_1:
```
1. doc_type=약관, page=17, match_keyword=암진단비(유사암제외)
2. doc_type=상품요약서, page=1, match_keyword=암진단비(유사암제외)
3. doc_type=약관, page=17, match_keyword=암진단비(유사암제외)
```
→ **3개** (약관 1개, 상품요약서 1개, 약관 추가 1개로 fill-up)

---

## Fallback 후순위 샘플

현재 8개 보험사 evidence pack에는 `fallback_` prefix가 실제로 존재하지 않음.
하지만 로직은 다음과 같이 구현됨:

**Fallback 판정 로직** (`build_cards.py:51-52`):
```python
def is_fallback(ev: Evidence) -> bool:
    return bool(ev.match_keyword and 'fallback_' in ev.match_keyword.lower())
```

**정렬 우선순위** (`build_cards.py:65-71`):
```python
def sort_key(ev: Evidence):
    return (
        is_fallback(ev),           # 1. Non-fallback 우선 (False < True)
        doc_type_priority_index(ev),  # 2. doc_type priority
        ev.page,                   # 3. page 오름차순
        ev.file_path               # 4. file_path 오름차순
    )
```

→ 만약 `match_keyword='fallback_token_and(...)'`인 evidence가 있다면,
동일 doc_type/page 조건에서 non-fallback이 우선 선택됨.

---

## 검증 결과 (VALIDATION)

✅ **8개 보험사 모두 재생성 완료**:
- samsung, kb, meritz, db, hanwha, heungkuk, hyundai, lotte

✅ **A4200_1 샘플 체크**:
- KB: 3개 evidence (약관 2개, 사업방법서 1개)
- Meritz: 3개 evidence (약관 2개, 상품요약서 1개)

✅ **pytest 100% PASS**:
```
75 passed in 0.44s
```

✅ **회귀 체크**:
- 총량 변화 없음 (evidence 존재성은 동일, 선택 규칙만 변경)

---

## 산출물 (DELIVERABLES)

1. **코드**: `pipeline/step5_build_cards/build_cards.py` 변경
2. **재생성**: `data/compare/*_coverage_cards.jsonl` 8개 업데이트
3. **문서**: 본 문서 (`docs/run/STEP6E1_CARD_SELECTION_HARDENING.md`)

---

## 금지 사항 확인 (ABSOLUTE NO — 준수됨)

❌ evidence search 로직 변경 (STEP 4) → **변경 없음**
❌ evidence_pack 생성 규칙 변경 → **변경 없음**
❌ Canonical/Excel/Mapping 수정 → **변경 없음**
❌ LLM/Vector/RAG/OCR 추가 → **추가 없음**
❌ "추천/해석/요약" 문장 생성 → **생성 없음**

---

## Definition of Done (DoD — 달성)

✅ `_select_diverse_evidences()`가 가능한 경우 항상 `max_count(3)`까지 채움
✅ fallback(`'fallback_'`) evidence는 동일 조건에서 후순위로 선택됨
✅ KB A4200_1 / Meritz A4200_1 각각 evidence 최대 3개가 카드에 들어감
✅ 8개 보험사 카드 재생성 완료
✅ pytest 100% PASS
✅ 변경 파일 1개 + 문서 1개 + 커밋 대기
✅ 재현 가능 로그/경로 유지

---

**NEXT**: Git commit → STEP 6-ε.1 완료
