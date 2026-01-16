# CHUNKGEN PROVENANCE (A4210)

**Date:** 2026-01-16
**Investigation:** 10 minutes
**Conclusion:** 옵션 B 실패 - chunk 생성 경로 재현 불가능

## 조사 결과

### 1) 코드베이스 검색
```bash
grep -r "INSERT INTO coverage_chunk" → No files found
grep -r "coverage_chunk" *.py → Only in tools/run_db_only_coverage.py (SELECT only)
```

### 2) A4210 Chunk 현황 (DB)
```
coverage_code: A4210
Total chunks: 5,219
Created: 2026-01-16 02:13:10 (all rows same timestamp)

Breakdown:
- N01 (메리츠): 2,910 chunks (약관 2,507 + 사업방법서 403)
- N08 (삼성): 2,309 chunks (약관 1,927 + 사업방법서 382)

Source PDF pattern:
- {insurer_name}_{doc_type}.pdf (파일명만, 경로 없음)
- 예: "메리츠_약관.pdf", "삼성_사업설명서.pdf"
```

### 3) 코드 흔적
- tools/ 디렉토리: run_db_only_coverage.py, coverage_profiles.py만 존재
- PDF 파싱 코드: 없음 (pdfplumber import는 방금 추가됨)
- Git history: chunk 생성 커밋 없음

### 4) 결론

**A4210 chunk 생성 방법:**
- ❓ Unknown - 코드로 재현 불가능
- 가능성 1: 이전 세션에서 SQL 직접 INSERT (스크립트 삭제됨)
- 가능성 2: 외부 도구/수동 생성
- 가능성 3: 삭제된 레거시 pipeline

**Timestamp 분석:**
- 모든 chunk가 동일 시각 (2026-01-16 02:13:10)
- Batch INSERT로 생성됨 (단일 트랜잭션)
- 이전 세션 작업으로 추정

### 5) 옵션 B 평가

**실패 사유:**
- 검증된 chunkgen 경로 없음
- 재현 가능한 도구/스크립트 없음
- 코드베이스에 chunk 생성 로직 없음

**다음 단계:**
→ **옵션 A로 진행**: 3-stage chunkgen을 run_db_only_coverage.py에 구현
