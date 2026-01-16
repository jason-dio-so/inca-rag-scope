# SSOT_PDF_JSON_BASELINE

**Date**: 2026-01-16
**Status**: ✅ COMPLETED
**Purpose**: PDF → JSON SSOT 1회성 변환 완료 기록

---

## 실행 결과

| 항목 | 결과 |
|------|------|
| DB | localhost:5433/inca_ssot |
| 테이블 | document_page_ssot |
| 총 rows | 14,849 |
| 보험사 | 8/8 ✅ |
| PDFs | 38개 |
| Pages 처리 | 14,846 |
| Paragraphs 생성 | 14,849 |
| 실행 시간 | ~33분 (15:26 - 15:59) |

---

## 보험사별 현황

| ins_cd | 보험사 | doc_types | rows | PDFs |
|--------|--------|-----------|------|------|
| N01 | 메리츠 | 4 | 2,474 | 4 |
| N02 | 한화 | 4 | 1,504 | 4 |
| N03 | DB | 4 | 1,447 | 5 |
| N05 | 흥국 | 4 | 1,534 | 4 |
| N08 | 삼성 | 4 | 1,900 | 5 |
| N09 | 현대 | 4 | 1,547 | 4 |
| N10 | KB | 4 | 1,150 | 4 |
| N13 | 롯데 | 4 | 3,293 | 8 |

**전체**: 8개 보험사, 38개 PDF, 14,849 rows

---

## 문서유형별 분포

| doc_type | rows | 비율 |
|----------|------|------|
| 약관 | 11,956 | 80.5% |
| 사업방법서 | 1,618 | 10.9% |
| 요약서 | 1,128 | 7.6% |
| 가입설계서 | 147 | 1.0% |

---

## 테이블 스키마

```sql
CREATE TABLE document_page_ssot (
    id SERIAL PRIMARY KEY,
    ins_cd VARCHAR(10) NOT NULL,
    doc_type VARCHAR(50) NOT NULL,
    source_pdf VARCHAR(255) NOT NULL,
    page_start INT NOT NULL,
    page_end INT NOT NULL,
    section_title TEXT,
    raw_text TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_page_ssot_ins_cd_doc_type ON document_page_ssot(ins_cd, doc_type);
CREATE INDEX idx_document_page_ssot_content_hash ON document_page_ssot(content_hash);
CREATE INDEX idx_document_page_ssot_source_pdf ON document_page_ssot(source_pdf);
```

---

## 변환 원칙

1. **Coverage-agnostic**: 담보 코드 무관, 보험사 × 문서유형 단위
2. **One-time read**: 각 PDF는 단 1회만 읽음
3. **Raw text**: 요약/해석/분류 없음, 원문 그대로 저장
4. **Paragraph split**: 이중 줄바꿈 기준 문단 분리
5. **NUL byte sanitization**: PostgreSQL 오류 방지 (0x00 제거)
6. **Deduplication**: content_hash (SHA256) 기반 중복 제거

---

## 검증 결과

### ✅ VERIFICATION PASSED

1. **총 row count > 0**: 14,849 rows ✅
2. **보험사 8개 모두 데이터 존재**: 8/8 ✅
3. **각 보험사 ≥ 4 doc_types**: 모두 4종 ✅

---

## 실행 스크립트

**위치**: `tools/pdf_to_json_ssot.py`

**실행 명령**:
```bash
python3 tools/pdf_to_json_ssot.py > /tmp/pdf_to_json_ssot.log 2>&1
```

**로그**: `/tmp/pdf_to_json_ssot.log`

---

## 조회 예시

### 보험사별 데이터 확인
```sql
SELECT ins_cd, doc_type, COUNT(*) as rows
FROM document_page_ssot
GROUP BY ins_cd, doc_type
ORDER BY ins_cd, doc_type;
```

### 암진단비 관련 텍스트 검색
```sql
SELECT ins_cd, doc_type, source_pdf, page_start,
       LEFT(raw_text, 200) as preview
FROM document_page_ssot
WHERE raw_text LIKE '%암진단비%'
LIMIT 10;
```

### 특정 보험사 약관 조회
```sql
SELECT source_pdf, page_start, section_title,
       LENGTH(raw_text) as text_length
FROM document_page_ssot
WHERE ins_cd = 'N08' AND doc_type = '약관'
ORDER BY page_start
LIMIT 20;
```

---

## 주요 특이사항

1. **롯데 (N13)**: 남/여 구분으로 8개 PDF (다른 보험사 4-5개)
2. **DB (N03)**: 가입설계서 2개 (40세이하/41세이상)
3. **삼성 (N08)**: 요약서 2개 (상품요약서/쉬운요약서) → 모두 doc_type='요약서'
4. **NUL byte 처리**: 일부 PDF 페이지에서 0x00 문자 발견, sanitize_text()로 제거
5. **페이지 누락**: 일부 PDF에서 추출 실패 페이지 존재 (오류 로그 기록)

---

## 다음 단계 (NOT NOW)

1. 모든 담보는 이 SSOT 데이터 재사용
2. PDF 직접 재파싱 금지
3. Coverage-specific 파이프라인은 document_page_ssot 기반으로 재설계

---

## 실행 로그 요약

```
2026-01-16 15:26:44 [INFO] PDF → JSON SSOT: Full Reset Phase
2026-01-16 15:26:44 [INFO] Clearing existing 4128 rows from document_page_ssot...
2026-01-16 15:26:44 [INFO] ✅ Table cleared

[N01 메리츠] 4 PDFs, 2476 pages → 2474 paragraphs
[N02 한화] 4 PDFs, 1504 pages → 1504 paragraphs
[N03 DB] 5 PDFs, 1435 pages → 1447 paragraphs
[N05 흥국] 4 PDFs, 1534 pages → 1534 paragraphs
[N08 삼성] 5 PDFs, 1910 pages → 1900 paragraphs
[N09 현대] 4 PDFs, 1540 pages → 1547 paragraphs
[N10 KB] 4 PDFs, 1154 pages → 1150 paragraphs
[N13 롯데] 8 PDFs, 3293 pages → 3293 paragraphs

2026-01-16 15:59:55 [INFO] CONVERSION SUMMARY
2026-01-16 15:59:55 [INFO] Insurers processed: 8/8
2026-01-16 15:59:55 [INFO] PDFs processed: 38
2026-01-16 15:59:55 [INFO] Pages processed: 14846
2026-01-16 15:59:55 [INFO] Paragraphs inserted: 14849
2026-01-16 15:59:55 [INFO] ✅ VERIFICATION PASSED
2026-01-16 15:59:55 [INFO] ✅ PIPELINE COMPLETED
```

---

**STATUS**: SSOT 구축 완료 (PDF → JSON 1회성 변환)

**REASON**: INPUT STRUCTURE REDESIGN 완료

**NEXT**: 담보별 파이프라인 재설계 시 이 SSOT 재사용
