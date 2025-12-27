# Session Handoff – inca-rag-scope

## 현재 완료된 STEP 요약 (STATUS.md 기준)

**STEP 1 (삼성화재)**: 완료
- Scope 추출: 41개 담보 (`samsung_scope.csv`)
- Canonical 매핑: 33개 matched, 8개 unmatched
- Scope gate 테스트: 11 passed

**진행 중인 보험사**: 삼성화재, 메리츠화재, DB손해보험 (일부 완료)
- 각 보험사별 scope.csv, evidence_pack.jsonl 생성
- 비교 보고서 생성 완료

**검증 완료**: pytest 전체 PASS

## 다음에 할 일 (우선순위)

1. **전체 보험사 확장**: 한화, 흥국, 현대, KB, 롯데 등 나머지 보험사 파이프라인 실행
2. **삼성생명 파일명 정규화**: `삼성생명_scope.csv` → `samsung_scope.csv` 통일 검토
3. **Compare 보고서 고도화**: 3개 이상 보험사 비교 시 테이블 포맷 개선

## 실행 전 확인 커맨드 (매 세션 필수)

```bash
# 1. 위치 확인
pwd
# Expected: /Users/cheollee/inca-rag-scope

# 2. Git 상태
git status -sb
# Clean working tree or intentional changes only

# 3. Scope 파일 확인
ls data/scope | head
# 보험사별 *_scope.csv 존재 확인

# 4. 테스트 실행
pytest -q
# All tests must PASS

# 5. Pipeline 도움말 확인
python -m pipeline.step7_compare.compare_insurers --help
# 사용 가능한 옵션 확인
```

## 파이프라인 실행 템플릿 (신규 보험사)

```bash
# 예: 한화생명 처리
INSURER="hanwha"

python -m pipeline.step1_load_scope.load_scope --insurer $INSURER
python -m pipeline.step2_pdf_extract.extract_all --insurer $INSURER
python -m pipeline.step3_search.search_coverage --insurer $INSURER
python -m pipeline.step4_evidence.build_evidence --insurer $INSURER
python -m pipeline.step5_validation.validate_evidence --insurer $INSURER
python -m pipeline.step6_report.generate_report --insurer $INSURER

# 비교 생성 (기존 보험사 포함)
python -m pipeline.step7_compare.compare_insurers --insurers samsung,meritz,db,$INSURER
```

## 체크포인트

- [ ] `CLAUDE.md` 읽음
- [ ] `STATUS.md` 최신 상태 확인
- [ ] `pytest -q` PASS 확인
- [ ] 요청 사항이 scope 내인지 검증
- [ ] 작업 완료 후 STATUS.md 갱신
