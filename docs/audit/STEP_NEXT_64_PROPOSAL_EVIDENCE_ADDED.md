# STEP NEXT-64: Proposal Evidence Added (가입설계서 근거 최우선 편입)

## 목적

가입설계서(Proposal)를 고객 관점에서 "가장 중요한 근거"로 인식하여, Step5 coverage_cards의 evidences 목록에 **가입설계서 detail을 최우선 근거로 포함**시킵니다.

## 변경 사항

### 1. Evidence Priority 확장 (Step5)

**파일**: `pipeline/step5_build_cards/build_cards.py`

**변경 전**:
```python
doc_type_priority_map = {
    '약관': 0,
    '사업방법서': 1,
    '상품요약서': 2
}

doc_type_priority = ['약관', '사업방법서', '상품요약서']
```

**변경 후**:
```python
doc_type_priority_map = {
    '가입설계서': -1,  # STEP NEXT-64: Proposal evidence 최우선
    '약관': 0,
    '사업방법서': 1,
    '상품요약서': 2
}

doc_type_priority = ['가입설계서', '약관', '사업방법서', '상품요약서']
```

### 2. Proposal Evidence 생성 로직 추가

**파일**: `pipeline/step5_build_cards/build_cards.py:324-367`

**추가 기능**:
1. `proposal_facts.evidences[]`를 Evidence 객체로 변환
2. Snippet 구성: `담보명 + 가입금액 + 보험료 + 납입기간`
3. 가입설계서 evidence를 `all_evidences`의 맨 앞에 추가
4. Diversity selection 시 가입설계서가 최우선 선택

**코드**:
```python
# STEP NEXT-64: Convert proposal_facts.evidences to Evidence objects (최우선)
proposal_evidences = []
if proposal_facts and proposal_facts.get('evidences'):
    for pf_ev in proposal_facts['evidences']:
        raw_row = pf_ev.get('raw_row', [])
        snippet_parts = []
        if len(raw_row) > 1:
            snippet_parts.append(f"담보명: {raw_row[1]}")
        if len(raw_row) > 2 and raw_row[2]:
            snippet_parts.append(f"가입금액: {raw_row[2]}")
        if len(raw_row) > 3 and raw_row[3]:
            snippet_parts.append(f"보험료: {raw_row[3]}")
        if len(raw_row) > 4 and raw_row[4]:
            snippet_parts.append(f"납입기간: {raw_row[4]}")

        proposal_evidence = Evidence(
            doc_type='가입설계서',
            file_path='proposal_table',  # 가상 경로
            page=pf_ev.get('page', 0),
            snippet='\n'.join(snippet_parts),
            match_keyword='proposal_table_row'
        )
        proposal_evidences.append(proposal_evidence)

# STEP NEXT-64: 가입설계서 evidence를 맨 앞에 추가
all_evidences = proposal_evidences + evidences
```

## 검증 결과 (A4200_1)

### Before (STEP NEXT-64 이전)
```
A4200_1 evidences:
  1. doc_type=약관, page=5
  2. doc_type=사업방법서, page=7
  3. doc_type=상품요약서, page=5
```

### After (STEP NEXT-64 이후)
```
A4200_1 evidences:
  1. doc_type=가입설계서, page=2  ← 최우선!
  2. doc_type=약관, page=5
  3. doc_type=사업방법서, page=7
```

**가입설계서 Evidence Snippet 예시** (A4200_1):
```
담보명: 암 진단비(유사암 제외)
가입금액: 3,000만원
보험료: 40,620
납입기간: 20년납 100세만기\nZD8
```

## 영향 범위

### 1. Step5 Build Cards
- ✅ 모든 coverage에 가입설계서 evidence 추가 (proposal_facts가 있는 경우)
- ✅ Evidence diversity selection 시 가입설계서 최우선
- ✅ Evidence status: 가입설계서도 evidence로 인정 (`evidence_status="found"`)

### 2. Step4 Evidence Search
- ❌ **변경 없음** (약관/사업방법서/상품요약서 검색 유지)
- ✅ Step5에서만 가입설계서 evidence 추가

### 3. Coverage Cards SSOT
- ✅ `evidences[]`: 가입설계서 → 약관 → 사업방법서 → 상품요약서 순서
- ✅ `proposal_facts`: 그대로 유지 (기존 필드 보존)

## 통계 (삼성 카드)

**재생성 결과**:
```
[Step 5] Coverage cards created:
  - Total coverages: 31
  - Matched: 27
  - Unmatched: 4
  - Evidence found: 31  ← 100% (가입설계서 포함)
  - Evidence not found: 0
```

**가입설계서 Evidence 추가율**:
- 전체 31개 coverage 중 31개에 가입설계서 evidence 추가 (100%)

## 향후 작업

### STEP 2-2: Customer View Schema 확장
- `customer_view` 필드 추가 (`benefit_structure`, `definitions`, `notes`)
- 가입설계서 evidence를 기반으로 `proposal_summary` 구성

### STEP 2-3: UI 연결
- Step8 렌더러가 가입설계서 evidence를 최우선 표시
- "지급유형/한도/조건" 섹션에 가입설계서 값 반영

## 결론

✅ **STEP 2-1 완료**: 가입설계서 detail이 coverage_cards의 evidences에 최우선 근거로 포함되었습니다. 이제 고객이 실제로 본 가입설계서 정보가 비교 UI에서 최우선으로 표시됩니다.
