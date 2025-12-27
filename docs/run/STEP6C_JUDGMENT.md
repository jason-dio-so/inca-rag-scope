# STEP 6-γ Doc-Type Hit Rule Verification

**Coverage**: A4200_1 (암진단비(유사암제외))
**Insurers**: KB, Meritz
**Date**: 2025-12-27

---

## A. Doc-Type Hit Rule 요약

- **Hit 정의**: 해당 doc_type 문서에서 coverage_name 기반 직접 snippet 추출 성공 시 hit 카운트 증가
- **검색 방식**: coverage_name(raw/canonical) 정규화 후 텍스트 내 phrase 매칭
- **Snippet 기준**: 키워드 포함 라인 + 전후 2줄 context
- **독립 검색**: 각 doc_type(약관/사업방법서/상품요약서) 독립 검색, 문서별 max 3건
- **Hits 집계**: `hits_by_doc_type[doc_type] += len(doc_type_evidences)` (search_evidence.py:467)

---

## B. KB 판정

### Evidence 존재 여부
- 약관: 3건 (page 7)
- 사업방법서: 0건
- 상품요약서: 0건

### Doc-type 구조
- **사업방법서**: 28 pages contain "암진단비" term → individual coverage entries exist
- **상품요약서**: 14 pages overview/table format only → "암진단비(유사암제외)" as individual entry: **0 pages**

### 판정
**상품요약서**: NORMAL
- KB 상품요약서는 담보 목록을 표 형식으로만 제공 (구 분/보험기간/납입기간)
- 개별 담보명 "암진단비(유사암제외)" 형식 문구 자체가 문서 구조상 존재하지 않음
- 현 규칙(phrase match)으로 탐지 불가는 정상

**사업방법서**: ABNORMAL
- KB 사업방법서에 "암진단비" 관련 내용 28 pages 존재
- 개별 담보 형식 가능성 존재하나 phrase match 실패
- 동일 규칙 적용 시 Samsung(18 pages hit), DB(9 pages hit) 대비 불일치

---

## C. Meritz 판정

### Evidence 존재 여부
- 약관: 3건 (page 17)
- 사업방법서: 0건
- 상품요약서: 3건

### Doc-type 구조
- **사업방법서**: 65 pages contain "암진단비" term → overview/table format only
- Individual coverage "암진단비(유사암제외)" format: **0 pages**

### 판정
**NORMAL**
- Meritz 사업방법서는 담보 목록을 표 형식(순번/보장/보험기간)으로만 제공
- 개별 담보명 구조로 기술되지 않음 (Samsung 18 pages individual format과 대조)
- 현 규칙(phrase match) 하에서 0 hit은 문서 구조 반영 결과로 정상

---

## D. 결론 테이블

| Insurer | Doc-Type Issue | Status |
|---------|----------------|--------|
| KB | 사업방법서 | ABNORMAL |
| KB | 상품요약서 | NORMAL |
| Meritz | 사업방법서 | NORMAL |

---

## Q1. 규칙 일관성 (동일 규칙 적용 시)

**No**
- Samsung 사업방법서: 18 pages individual format → hit
- DB 사업방법서: 9 pages individual format → hit
- KB 사업방법서: 28 pages with "암진단비" term, 0 hit → 불일치
- Meritz 사업방법서: 0 pages individual format → consistent with rule

---

## Q2. 정의상 정상 여부

**KB policy_only**: ABNORMAL (사업방법서 content 존재하나 미탐지)
**Meritz 사업방법서 0 hit**: NORMAL (문서 구조상 개별 담보 형식 부재)
