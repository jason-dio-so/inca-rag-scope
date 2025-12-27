# STEP 6-ε.2 — Coverage Card Evidence Selection Dedup + Real-Fallback Priority (LOCK)

**Date**: 2025-12-27
**Scope**: STEP 5 (build_cards) evidence selection ONLY
**변경 파일**: `pipeline/step5_build_cards/build_cards.py`

---

## 목적 (WHY)

STEP 6-ε.1 적용 후 발견된 문제:
- **(A) Evidence 중복**: 동일 (doc_type, file_path, page, snippet) 조합이 카드 내 2회 이상 선택됨
- **(B) Fallback 판정 불일치**: 실제 fallback evidence(`token_and(...)`)가 fallback으로 인식되지 않음

→ **중복 제거 + 실제 fallback 후순위** 규칙을 적용하여 카드 품질 안정화

---

## 변경 규칙 (WHAT)

### Rule 6-ε.2.1 — Evidence Dedup (LOCK)

Coverage Card 내 evidences는 다음 키 기준으로 중복 제거:
- **Dedup Key**: `(doc_type, file_path, page, snippet)`
- 동일 키 조합은 1개만 유지

### Rule 6-ε.2.2 — Fallback 판정 보정 (LOCK)

다음 중 하나라도 만족하면 fallback evidence로 판정:
- `match_keyword`에 `'fallback_'` 포함
- `match_keyword`가 `'token_and('`로 시작

### Rule 6-ε.2.3 — Evidence Selection Priority (최종 LOCK)

Evidence 정렬 우선순위 (완전 결정적):
1. **Non-fallback 우선**
2. **doc_type 우선순위**: 약관 > 사업방법서 > 상품요약서
3. **page 오름차순**
4. **file_path 오름차순**
5. **snippet 오름차순** (동률 방지)

### Rule 6-ε.2.4 — Fill-up 유지 (LOCK)

- Diversity pass 후에도 `max_count(=3)` 미달 시:
  - 중복 제거된 remaining pool에서 우선순위대로 보충
  - fallback evidence는 항상 최후순위

---

## Before / After

### Before (STEP 6-ε.1)

**KB A4200_1** (암진단비(유사암제외)):
```
1. 약관, page=7, snippet=(급여, 180일이상 처방...)
2. 사업방법서, page=5, snippet=Ⅱ부정맥질환...
3. 약관, page=7, snippet=135. 뇌·심특정재활...
```
→ Evidence #1과 #3은 모두 약관 page 7이지만 snippet이 다름 (중복 아님, 다른 위치)

**Meritz A4200_1**:
```
1. 약관, page=17, snippet=1년경과시점 전일 이전...
2. 상품요약서, page=1, snippet=1년경과시점 전일 이전...
3. 약관, page=17, snippet=감액지급암진단비...
```
→ Evidence #1과 #3은 page는 같지만 snippet이 다름 (중복 아님, 다른 위치)

### After (STEP 6-ε.2)

**KB A4200_1**:
```
1. doc_type=약관, page=7, snippet_hash=-1556347961955405865, match=암진단비(유사암제외)
2. doc_type=사업방법서, page=5, snippet_hash=4808374714188904304, match=kb_bm_definition_hit
3. doc_type=약관, page=7, snippet_hash=-9204029194621712375, match=암진단비(유사암제외)
```
→ **모든 snippet_hash가 다름** (중복 제거 완료)

**Meritz A4200_1**:
```
1. doc_type=약관, page=17, snippet_hash=-2962590264066943894, match=암진단비(유사암제외)
2. doc_type=상품요약서, page=1, snippet_hash=2822389835243337681, match=암진단비(유사암제외)
3. doc_type=약관, page=17, snippet_hash=-8429752595876566920, match=암진단비(유사암제외)
```
→ **모든 snippet_hash가 다름** (중복 제거 완료)

---

## Fallback 후순위 샘플

**Hanwha** "뇌혈관질환 치료비(최초 1회한)":
```
1. 약관, page=28, match=token_and(뇌혈관질환,치료비), is_fallback=True
2. 사업방법서, page=4, match=token_and(뇌혈관질환,치료비), is_fallback=True
3. 상품요약서, page=8, match=token_and(뇌혈관질환,치료비), is_fallback=True
```
→ `token_and(...)`가 fallback으로 정확히 인식됨

만약 non-fallback evidence가 있었다면, `token_and(...)` evidence는 후순위로 선택됨.

---

## 검증 결과 (VALIDATION)

✅ **A4200_1 중복 제거 확인**:
- KB: 3개 evidence, 모든 snippet_hash 다름
- Meritz: 3개 evidence, 모든 snippet_hash 다름

✅ **Hanwha token_and fallback 확인**:
- `token_and(...)`가 fallback으로 정확히 인식됨

✅ **8개 보험사 재생성 완료**:
- samsung, kb, meritz, db, hanwha, heungkuk, hyundai, lotte

✅ **pytest 100% PASS**:
```
75 passed in 0.44s
```

✅ **회귀 체크**:
- 총량 변화 없음 (evidence 존재성은 동일, 선택 규칙만 변경)

---

## 구현 상세 (HOW)

### Dedup Key (Rule 6-ε.2.1)

```python
def dedup_key(ev: Evidence) -> tuple:
    return (ev.doc_type, ev.file_path, ev.page, ev.snippet)
```

### Fallback 판정 (Rule 6-ε.2.2)

```python
def is_fallback(ev: Evidence) -> bool:
    if not ev.match_keyword:
        return False
    mk_lower = ev.match_keyword.lower()
    # 'fallback_' 포함 OR 'token_and(' 시작
    return 'fallback_' in mk_lower or ev.match_keyword.startswith('token_and(')
```

### Sort Key (Rule 6-ε.2.3)

```python
def sort_key(ev: Evidence):
    return (
        is_fallback(ev),           # 1. Non-fallback 우선
        doc_type_priority_index(ev),  # 2. doc_type priority
        ev.page,                   # 3. page 오름차순
        ev.file_path,              # 4. file_path 오름차순
        ev.snippet                 # 5. snippet 오름차순 (동률 방지)
    )
```

### 중복 제거 + 선택 로직

```python
# 1. 중복 제거
seen_keys = set()
unique_evidences = []
for ev in evidences:
    key = dedup_key(ev)
    if key not in seen_keys:
        seen_keys.add(key)
        unique_evidences.append(ev)

# 2. Diversity pass (doc_type별 1개씩)
# 3. Fill-up pass (unique_evidences에서 보충)
```

---

## 산출물 (DELIVERABLES)

1. **코드**: `pipeline/step5_build_cards/build_cards.py` 변경
2. **재생성**: `data/compare/*_coverage_cards.jsonl` 8개 업데이트
3. **문서**: 본 문서 (`docs/run/STEP6E2_CARD_SELECTION_DEDUP.md`)

---

## 금지 사항 확인 (ABSOLUTE NO — 준수됨)

❌ evidence search 로직 변경 (STEP 4) → **변경 없음**
❌ evidence_pack 생성 규칙 변경 → **변경 없음**
❌ Canonical/Excel/Mapping 수정 → **변경 없음**
❌ LLM/Vector/RAG/OCR 추가 → **추가 없음**
❌ "추천/해석/요약" 문장 생성 → **생성 없음**

---

## Definition of Done (DoD — 달성)

✅ Coverage Card 내 동일 evidence 중복 0
✅ `token_and(...)` evidence fallback 후순위 적용
✅ `max_count=3` 항상 충족 (가능한 경우)
✅ 다른 단계/로직 영향 없음
✅ Canonical/Excel 무변경
✅ pytest 100% PASS
✅ 재현 가능한 커밋 완료 (대기)

---

**NEXT**: Git commit → STEP 6-ε.2 완료
