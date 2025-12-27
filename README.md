# inca-rag-scope

보험 가입설계서 담보 분석 시스템 - Scope-First 접근

## Working Directory
```
/Users/cheollee/inca-rag-scope
```

## Quickstart
```bash
# 테스트 실행
pytest -q

# 파이프라인 실행 (예: 삼성화재)
python -m pipeline.step1_load_scope.load_scope --insurer samsung       # 1. Scope 로드
python -m pipeline.step2_pdf_extract.extract_all --insurer samsung     # 2. PDF 추출
python -m pipeline.step3_search.search_coverage --insurer samsung      # 3. 담보 검색
python -m pipeline.step4_evidence.build_evidence --insurer samsung     # 4. 증거 구축
python -m pipeline.step5_validation.validate_evidence --insurer samsung # 5. 검증
python -m pipeline.step6_report.generate_report --insurer samsung      # 6. 보고서 생성
python -m pipeline.step7_compare.compare_insurers --insurers samsung,meritz,db # 7. 보험사 비교
```

## 프로젝트 목적

가입설계서 요약 장표에 포함된 **30~40개 담보만을 범위(scope)**로 하여, 이들 담보에 대한 정확한 표준화와 근거 문서 매칭을 수행한다.

## Scope-First 접근법

### 핵심 원칙

1. **Canonical Source 단일화**
   - `data/sources/mapping/담보명mapping자료.xlsx`만이 유일한 정규 담보 목록
   - 모든 담보 표준화는 이 파일 기준

2. **범위 제한**
   - 가입설계서에 명시된 담보만 처리
   - 약관/상품설명서의 모든 담보를 저장하지 않음

3. **근거 문서의 역할**
   - 약관, 상품설명서, 사업방법서는 scope 담보의 evidence 탐색용
   - 전체 파싱이 아닌 targeted 검색

### 기존 방식과의 차이

| 항목 | 기존 (inca-rag) | 신규 (inca-rag-scope) |
|------|----------------|---------------------|
| 담보 범위 | 약관 전체 담보 파싱 | 가입설계서 30~40개만 |
| Canonical | 약관에서 생성 | mapping 엑셀 ONLY |
| LLM 역할 | 담보 생성/수정 | 근거 문서 탐색만 |
| DB 저장 | 모든 담보 | scope 내 담보만 |

## 디렉토리 구조

```
inca-rag-scope/
├── README.md
├── schema/
│   └── 010_canonical.sql          # coverage_standard, coverage_alias
├── core/
│   └── scope_gate.py              # scope 검증 로직
├── pipeline/
│   └── step1_extract_scope/
│       └── run.py                 # 가입설계서에서 scope 추출
└── data/
    ├── sources/
    │   └── mapping/
    │       └── 담보명mapping자료.xlsx
    └── scope/
        └── {INSURER}_scope.csv    # 추출된 scope 담보 목록
```

## 워크플로우

1. **Scope 추출** (`step1_extract_scope`)
   - 가입설계서 PDF → scope CSV 생성
   - 출력: coverage_name_raw, insurer, source_page

2. **Scope Gate** (`scope_gate.py`)
   - 이후 모든 단계에서 scope CSV 기준 검증
   - scope 외 담보는 즉시 reject

3. **Canonical 매칭** (추후)
   - scope 담보 → mapping 엑셀 매칭
   - coverage_code 할당

4. **Evidence 수집** (추후)
   - scope 담보에 대해서만 약관/설명서 검색
   - 근거 문장 추출

## Absolute Rules

1. Canonical coverage source는 `data/sources/mapping/담보명mapping자료.xlsx` ONLY
2. 약관/상품설명서/사업방법서는 scope 담보의 근거(evidence) 탐색용으로만 사용
3. Scope에 없는 담보는 어떤 단계에서도 처리/저장/추론 금지
4. LLM은 사용하더라도 canonical 생성/수정에는 관여하지 않는다
