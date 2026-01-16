# Q11 UI 사용 방법

## 개요
Q11 질문("암직접입원비 담보 중 보장한도가 다른 상품 찾아줘")에 대한 차이 중심 비교 화면입니다.

## 실행 조건
1. **API 서버 실행 필수**
   ```bash
   python3 -m uvicorn apps.api.server:app --host 0.0.0.0 --port 8000
   ```

2. **SSOT 데이터 준비 완료**
   - coverage_code: A6200
   - table_id: 22
   - insurers: N01, N03, N05, N08, N09, N10, N13
   - FOUND=21/21, contamination=0

## 사용 방법

### 1. 브라우저에서 열기
```bash
# macOS
open reports/q11_coverage_limit_diff.html

# Linux
xdg-open reports/q11_coverage_limit_diff.html

# Windows
start reports/q11_coverage_limit_diff.html
```

또는 브라우저 주소창에 직접 입력:
```
file:///Users/cheollee/inca-rag-scope/reports/q11_coverage_limit_diff.html
```

### 2. 화면 구성

#### 상단 요약 카드
- **차이 있음**: 빨간색 배경, "DIFFERENCE FOUND" 배지
- **차이 없음**: 초록색 배경, "UNIFORM" 배지

#### 차이 포인트 섹션 (🔴)
- **입원일수 한도 차이**: N03 (120일) vs Others (180일 or unspecified)
- 차이가 있는 항목만 표시
- 각 값별로 해당 보험사 목록 표시

#### 공통 조건 섹션 (🔵)
- **요양병원 제외 여부**: 모두 "제외" (UNIFORM)
- **최소 입원일수**: 모두 "1일 이상" (UNIFORM)
- 차이가 없는 항목만 표시

#### 보험사별 비교 테이블 (📊)
| 보험사 | 상품명 | 최대 입원일수 | 요양병원 | 최소 입원일수 |
|--------|--------|---------------|----------|---------------|
| N01 | ... | **1일이상 (한도 미명시)** | 제외 | 1일 이상 |
| N03 | ... | **120일** | 제외 | 1일 이상 |
| N05 | ... | 180일 | 제외 | 1일 이상 |
| ... | ... | ... | ... | ... |

차이가 있는 셀은 노란색으로 하이라이트됩니다.

## 데이터 출처

### API Endpoint
```
GET http://localhost:8000/compare_v2?coverage_code=A6200&as_of_date=2025-11-26&ins_cds=N01,N03,N05,N08,N09,N10,N13
```

### SSOT 기준
- **document_page_ssot**: as_of_date=2025-11-26
- **evidence_slot**: FOUND=21/21 (7사 × 3 slots)
- **compare_table_v2**: table_id=22

### 보험사별 상품명 매핑
```javascript
{
  'N01': '암직접치료입원일당(Ⅱ)(요양병원제외,1일이상)',
  'N03': '암직접치료입원비(요양병원제외)(1-120일)',
  'N05': '암직접치료입원비(요양병원제외)(1일-180일)',
  'N08': '암 직접치료 입원일당Ⅱ(1일이상)(요양병원 제외)',
  'N09': '암직접치료입원일당(1-180일,요양병원제외)담보',
  'N10': '암직접치료입원일당(요양제외,1일이상180일한도)',
  'N13': '암직접치료입원일당Ⅱ(요양병원제외)(1일이상180일한도)'
}
```

## 파싱 로직

### 입원일수 한도 (parseLimitDays)
1. `(1-120일)` → "120일"
2. `(1-180일)` → "180일"
3. `180일한도` → "180일"
4. `1일이상180일한도` → "180일"
5. `1일이상` (한도 미명시) → "1일이상 (한도 미명시)"

### 요양병원 규칙 (parseNursingHospital)
- `요양병원제외` or `요양제외` → "제외"
- `요양병원포함` or `요양포함` → "포함"

### 최소 입원일수 (parseMinAdmission)
- `1일이상`, `2일이상`, `3일이상` → "N일 이상"
- excerpt에 "90일", "면책", "보장개시" 포함 → "1일 이상 (면책기간 있음)"

## 차이 탐지 로직

각 항목별로 unique 값의 개수를 세어 차이 여부를 판정합니다:

```javascript
const limitDays = [...new Set(insurers.map(ins => ins.limitDays))];
const limitDaysDiff = limitDays.length > 1; // true if difference exists
```

## 예상 결과 (A6200 7사 기준)

### 차이 포인트
- ✅ **입원일수 한도 차이 있음**
  - 120일: 1개 보험사 (N03)
  - 180일: 4개 보험사 (N05, N09, N10, N13)
  - 1일이상 (한도 미명시): 2개 보험사 (N01, N08)

### 공통 조건
- ✅ **요양병원**: 모두 제외
- ✅ **최소 입원일수**: 모두 1일 이상

## 절대 금지 사항 (준수 확인)
- ✅ PDF 재파싱 없음
- ✅ LLM 추론/요약 없음
- ✅ 보장 의미 해석 없음
- ✅ q11_report 생성 시도 없음
- ✅ evidence_slot excerpt 기반 fact-only
- ✅ 차이가 없으면 "차이 없음" 명시
- ✅ 데이터 없는 경우 "정보 없음" 표시

## DoD 검증

### Q11 질문 1회 입력 → 차이 요약 + 표 동시 출력
✅ HTML 파일 열기 즉시 자동 로딩

### DB(120일) vs 타사(180일) 차이 명확히 표시
✅ 차이 포인트 섹션에 명확히 표시
✅ 비교 테이블에서 노란색 하이라이트

### SSOT 데이터 외 참조 없음
✅ API `/compare_v2` 엔드포인트만 사용
✅ evidence_slot 데이터 기반
✅ 하드코딩된 상품명 매핑은 coverage_mapping_ssot 출처

## 트러블슈팅

### 오류: "데이터 로딩 중..." 무한 로딩
**원인**: API 서버가 실행되지 않음
**해결**:
```bash
python3 -m uvicorn apps.api.server:app --host 0.0.0.0 --port 8000
```

### 오류: "API Error: 404"
**원인**: table_id=22 데이터가 없음
**해결**:
```bash
# A6200 파이프라인 재실행
python3 tools/run_db_only_coverage.py --coverage_code A6200 --as_of_date 2025-11-26 --ins_cds N01,N03,N05,N08,N09,N10,N13 --stage all
```

### 오류: CORS 에러
**원인**: 브라우저 보안 정책
**해결**: 브라우저 콘솔에서 확인, 필요시 API 서버에 CORS 설정 추가

## 파일 구조
```
reports/
├── q11_coverage_limit_diff.html  # 메인 UI 파일
└── Q11_USAGE.md                  # 이 파일
```

## 참고 문서
- 요구사항: STEP Q11-UI-REFRESH (SSOT 기준)
- 데이터 출처: `docs/audit/RUN_RECEIPT_A6200_Q11_7INS_FREEZE.md`
- API 서버: `apps/api/server.py`
- 프로필 설정: `tools/coverage_profiles.py::A6200_Q11_PROFILE_V1`
