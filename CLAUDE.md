# CLAUDE Context – inca-rag-scope

## Project Purpose
가입설계서 30~40개 보장 scope에 대한 **근거 자료 자동 수집 + 사실 비교** 파이프라인.
보험사별 약관/사업방법서/상품요약서에서 "scope 내 담보"만 검색 → 원문 추출 → 보험사 간 사실 대조표 생성.

## Canonical Truth (절대 기준)
**`data/sources/mapping/담보명mapping자료.xlsx`** ONLY
- 모든 담보명, 보험사별 표기, scope 판정의 단일 출처
- 이 파일에 없는 담보는 처리 금지
- 수동 편집은 허용, 코드로 생성/변경 금지

## Scope Gate (철칙)
1. **Scope 내 담보만 처리**: mapping 파일에 정의된 담보만
2. **보험사 확장 전 scope 검증**: 신규 보험사 추가 시 mapping 파일 먼저 확인
3. **Scope 밖 요청 거부**: "전체 담보", "추가 보장", "유사 상품" 같은 확장 요청 즉시 차단

## Evidence (증거 자료) 원칙
- **3가지 문서 타입 독립 검색**: 약관(policy), 사업방법서(business), 상품요약서(summary)
- **hits_by_doc_type 필수**: 각 담보별로 어느 문서에서 나왔는지 기록
- **policy_only 플래그 유지**: 약관에만 존재하는 담보 구분
- 검색 결과는 원문 그대로 보존 (요약/해석 금지)

## 산출물 고정 경로
```
data/scope/{insurer}_scope.csv           # 보험사별 scope 담보 목록
data/evidence_pack/{insurer}_pack.jsonl  # 담보별 원문 증거
data/compare/*.jsonl                     # 보험사 간 비교 데이터
reports/{timestamp}_*.md                 # 사실 비교 보고서
STATUS.md                                # 진행 상황 (매 STEP 갱신)
```

## 금지 사항
- LLM 요약/추론/생성
- Embedding/벡터DB 사용
- 담보명 자동 매칭/추천
- Scope 외 데이터 처리
- 보고서에 "추천", "제안", "결론" 삽입

## 실행 기본 명령
```bash
# 테스트
pytest -q

# Pipeline 실행 (예: 삼성생명)
python -m pipeline.step1_load_scope.load_scope --insurer samsung
python -m pipeline.step2_pdf_extract.extract_all --insurer samsung
python -m pipeline.step3_search.search_coverage --insurer samsung
python -m pipeline.step4_evidence.build_evidence --insurer samsung
python -m pipeline.step5_validation.validate_evidence --insurer samsung

# 비교 생성 (보험사 2개 이상)
python -m pipeline.step7_compare.compare_insurers --insurers samsung,meritz,db

# 현재 상태 확인
git status -sb
ls data/scope | head
```

## Architecture (7 STEP)
1. **load_scope**: mapping → scope.csv
2. **pdf_extract**: PDF → 페이지 텍스트
3. **search**: 담보명 검색 → 매칭 페이지
4. **evidence**: 원문 추출 → pack.jsonl
5. **validation**: 증거 품질 체크
6. **report**: 보험사별 단일 보고서
7. **compare**: 보험사 간 대조표

## Working Directory
`/Users/cheollee/inca-rag-scope`

## Session Start Protocol
매 세션 시작 시:
1. `docs/SESSION_HANDOFF.md` 읽기
2. `STATUS.md` 최신 상태 확인
3. `git status -sb` + `pytest -q` 실행
4. 요청 사항이 scope 내인지 검증 후 진행
