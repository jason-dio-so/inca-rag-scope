# STEP NEXT-10 완료 보고서

## 날짜
2025-12-28

## 목적
STEP NEXT-9/9.1에서 고정된 API Contract를 기준으로 Mock API Server를 실제 Backend API 구현으로 교체

## 완료 항목

### 1. Production API Server 구현
- **파일**: `apps/api/server.py`
- **프레임워크**: FastAPI
- **포트**: 8001
- **엔드포인트**:
  - `GET /health`: Health check (DB 연결 상태 포함)
  - `POST /compare`: Main comparison endpoint
  - `GET /`: API info

### 2. Query Compiler (Deterministic)
- **클래스**: `QueryCompiler`
- **기능**: Request → Query Plan 변환 (rule-based, 결정론적)
- **Intent 라우팅**:
  - `PRODUCT_SUMMARY` → 9개 core coverage (EXAMPLE3_CORE_9)
  - `COVERAGE_CONDITION_DIFF` → 단일 coverage, 5개 조건 비교
  - `COVERAGE_AVAILABILITY` → O/X 테이블
  - `PREMIUM_REFERENCE` → 보험료 참고 정보 (premium_notice=true)

### 3. Intent Handlers (4개)
- **ProductSummaryHandler**: Example 3 처리
- **CoverageConditionDiffHandler**: Example 2 처리
- **CoverageAvailabilityHandler**: Example 4 처리
- **PremiumReferenceHandler**: Example 1 처리

### 4. Database 연동
- **DB**: PostgreSQL (inca_rag_scope)
- **Connection**: psycopg2
- **사용 테이블**:
  - `insurer`, `product`, `product_variant`, `document` (metadata)
  - `coverage_canonical` (Excel 기준)
  - `coverage_instance`, `evidence_ref`, `amount_fact` (facts)

### 5. Evidence 규칙 준수
- **모든 값에 evidence 필수**:
  - `status: found` → `source`, `snippet` 포함
  - `status: not_found` → 값 출력 금지 ("확인 불가"로 표현)

### 6. API Contract 검증
- **테스트**: `tests/test_api_contract.py`
- **결과**: 21/21 PASSED (100%)
  - Request Schema Validation: PASS
  - Response Schema Validation: PASS
  - Forbidden Phrase Test: 0건
  - Evidence Rule Test: PASS

### 7. UI 통합 검증
- **Web Prototype**: http://localhost:8000
- **API 연결**: http://localhost:8001
- **설정**: `apps/web-prototype/index.html` (line 481: `API_BASE_URL = 'http://localhost:8001'`)
- **상태**: ✅ UI가 Production API로 정상 동작

## 불변 규칙 준수 현황

### ✅ API Contract 변경 없음
- Request Schema: CompareRequest (4개 intent 지원)
- Response Schema: 5-block View Model (meta, query_summary, comparison, notes, limitations)

### ✅ View Model 구조 고정
- meta: query_id, timestamp, intent, compiler_version
- query_summary: targets, coverage_scope, premium_notice
- comparison: type (COVERAGE_TABLE, OX_TABLE, PREMIUM_LIST), columns, rows
- notes: title, content, evidence_refs
- limitations: 고정 문구 배열

### ✅ 금지 사항 준수
- ❌ LLM 호출 없음
- ❌ 추천/판단/해석/추론 없음
- ❌ Evidence 없는 값 출력 없음
- ❌ 임의 정렬/필터링 없음

### ✅ Evidence 규칙 준수
- 모든 값에 evidence 객체 포함
- `status: found` → source + snippet 필수
- `status: not_found` → value_text 출력 금지

## 실행 방법

### 1. DB 데이터 로드 (최초 1회)
```bash
python -m apps.loader.step9_loader --mode reset_then_load
```

### 2. Production API 서버 시작
```bash
uvicorn apps.api.server:app --host 127.0.0.1 --port 8001 --reload
```

### 3. Web Prototype 시작
```bash
cd apps/web-prototype
python3 -m http.server 8000
```

### 4. 브라우저 접속
```
http://localhost:8000
```

## 테스트 결과

### API Contract Tests
```bash
pytest tests/test_api_contract.py -v
# 21 passed in 0.10s
```

### API Health Check
```bash
curl http://127.0.0.1:8001/health
# {"status": "ok", "version": "1.0.0", "database": "ok"}
```

### Sample API Request
```bash
curl -X POST http://127.0.0.1:8001/compare \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "PRODUCT_SUMMARY",
    "insurers": ["SAMSUNG", "HANWHA"],
    "products": [
      {"insurer": "SAMSUNG", "product_name": "삼성생명 무배당 New 원더풀 암보험"},
      {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
    ]
  }'
```

## 데이터 현황

### DB 테이블 Row Counts
```sql
SELECT COUNT(*) FROM coverage_canonical;  -- 48 rows
SELECT COUNT(*) FROM coverage_instance;   -- 297 rows
SELECT COUNT(*) FROM evidence_ref;        -- 747 rows
```

## 제한 사항 (Known Limitations)

### 1. 조건 비교 데이터 부족
- **COVERAGE_CONDITION_DIFF** (Example 2): 5개 조건 중 "보장 여부"만 DB에서 조회 가능
- 나머지 4개 조건(보장 금액, 대기기간, 감액기간, 제외 암종)은 evidence 파싱 필요
- **현재 상태**: "확인 불가"로 반환 (추론 방지)

### 2. 보험료 데이터 미구현
- **PREMIUM_REFERENCE** (Example 1): 가입설계서에서 보험료 추출 로직 미구현
- **현재 상태**: "확인 불가 (참고용)"로 반환

### 3. 일부 보험사 데이터 부족
- DB에 일부 보험사 데이터만 로드됨
- 미등록 보험사 요청 시 "확인 불가" 반환

## 다음 단계 제안

### STEP NEXT-11 (선택 사항)
1. **Evidence Parsing 고도화**
   - 조건 비교(대기기간, 감액기간, 제외 암종) 구조화 추출
   - 보험료 정보 추출

2. **보험사 데이터 확장**
   - 전체 보험사 scope_mapped.csv 로드
   - evidence_pack.jsonl 데이터 보강

3. **성능 최적화**
   - DB 쿼리 인덱싱
   - Connection pooling

4. **에러 핸들링 강화**
   - 보험사/상품 미등록 시 명확한 에러 메시지
   - 타임아웃 처리

## 성공 기준 달성 여부

### ✅ UI가 Mock API 없이 실제 API로 정상 동작
- Production API 서버 구동: ✅
- UI 연결 확인: ✅

### ✅ 고객 예제 1~4 화면 변경 없음
- Response View Model 구조 고정: ✅
- 5-block 구조 유지: ✅

### ✅ API Contract 변경 0
- Request Schema: 변경 없음 ✅
- Response Schema: 변경 없음 ✅

### ✅ 테스트 100% PASS
- API Contract Tests: 21/21 PASSED ✅

## 결론

**STEP NEXT-10 완료**

Mock API Server를 Production API로 성공적으로 교체했습니다.
- API Contract 변경 없음
- 테스트 100% PASS
- UI 통합 정상 동작
- Evidence 기반 사실 비교 유지

일부 데이터 부족(조건 비교, 보험료)은 STEP NEXT-11에서 해결 가능합니다.
