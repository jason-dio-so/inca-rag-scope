# CLAUDE Context – inca-rag-scope

## Project Purpose
가입설계서 30~40개 보장 scope에 대한 **근거 자료 자동 수집 + 사실 비교** 파이프라인.
보험사별 약관/사업방법서/상품요약서에서 "scope 내 담보"만 검색 → 원문 추출 → 보험사 간 사실 대조표 생성.

## Input Contract (Canonical Truth for Mapping)
**`data/sources/mapping/담보명mapping자료.xlsx`**
- 담보명 매핑의 단일 출처 (INPUT contract)
- 이 파일에 없는 담보는 처리 금지
- 수동 편집은 허용, 코드로 생성/변경 금지
- **주의**: 이는 INPUT이며, SSOT(Single Source of Truth)가 아님

## Scope Gate (철칙)
1. **Scope 내 담보만 처리**: mapping 파일에 정의된 담보만
2. **보험사 확장 전 scope 검증**: 신규 보험사 추가 시 mapping 파일 먼저 확인
3. **Scope 밖 요청 거부**: "전체 담보", "추가 보장", "유사 상품" 같은 확장 요청 즉시 차단

## Evidence (증거 자료) 원칙
- **3가지 문서 타입 독립 검색**: 약관(policy), 사업방법서(business), 상품요약서(summary)
- **hits_by_doc_type 필수**: 각 담보별로 어느 문서에서 나왔는지 기록
- **policy_only 플래그 유지**: 약관에만 존재하는 담보 구분
- 검색 결과는 원문 그대로 보존 (요약/해석 금지)

## SSOT (Single Source of Truth) — FINAL CONTRACT

**Coverage SSOT**:
```
data/compare/*_coverage_cards.jsonl
```
- 담보별 카드 (mapping_status, evidence_status, amount)
- 모든 coverage 관련 검증의 기준

**Audit Aggregate SSOT**:
```
docs/audit/AMOUNT_STATUS_DASHBOARD.md
```
- KPI 집계 및 품질 검증의 기준

---

## Input/Intermediate Files (NOT SSOT)

**Sanitized Scope (INPUT)**:
```
data/scope/{insurer}_scope_mapped.sanitized.csv
```
- Pipeline INPUT contract (sanitized)
- SSOT가 아님 (coverage_cards가 SSOT)

**Stats (보조)**:
```
data/compare/*.json
```
- 통계 보조 파일 (SSOT 아님)

**Status Tracking**:
```
STATUS.md
```
- 진행 상황 기록 (historical log)

---

## DEPRECATED (완전 제거됨 / _deprecated로 이동)

**❌ DO NOT USE** (STEP NEXT-31-P2: Moved to _deprecated/):
- `reports/*.md` — STEP NEXT-18X-SSOT에서 완전 제거
- `data/evidence_pack/` — Step5+에서 coverage_cards로 통합
- `_deprecated/pipeline/step0_scope_filter/` — Canonical pipeline 미사용
- `_deprecated/pipeline/step7_compare/` — 비교는 API layer에서 수행
- `_deprecated/pipeline/step8_multi_compare/` — 비교는 API layer에서 수행
- `_deprecated/pipeline/step8_single_coverage/` — 조회는 API layer에서 수행
- `_deprecated/pipeline/step10_audit/` — 보고서 생성은 tools/audit에서 수행
- `pipeline/step6_build_report/` — 제거됨
- `pipeline/step9_single_compare/` — 제거됨
- `pipeline/step10_multi_single_compare/` — 제거됨

## 금지 사항
- LLM 요약/추론/생성
- Embedding/벡터DB 사용
- 담보명 자동 매칭/추천
- Scope 외 데이터 처리
- 보고서에 "추천", "제안", "결론" 삽입

## 실행 기본 명령 (Canonical Pipeline)
```bash
# 테스트
pytest -q

# Canonical Pipeline 실행 (예: Hanwha)
python -m pipeline.step1_extract_scope.run --insurer hanwha
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer hanwha
python -m pipeline.step1_sanitize_scope.run --insurer hanwha
python -m pipeline.step3_extract_text.run --insurer hanwha
python -m pipeline.step4_evidence_search.search_evidence --insurer hanwha
python -m pipeline.step5_build_cards.build_cards --insurer hanwha

# Amount enrichment (optional)
python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer hanwha

# 현재 상태 확인
git status -sb
ls data/scope | head
```

## Pipeline Architecture (Canonical Steps - STEP NEXT-31-P2)

**Canonical Pipeline** (정식 실행 순서):
1. **step1_extract_scope**: 가입설계서 PDF → raw scope CSV
2. **step2_canonical_mapping**: raw scope → canonical coverage codes (mapping)
3. **step1_sanitize_scope**: mapped scope → sanitized scope (INPUT contract)
4. **step3_extract_text**: PDF → evidence text (약관/사업방법서/상품요약서)
5. **step4_evidence_search**: sanitized scope + text → evidence_pack.jsonl
6. **step5_build_cards**: sanitized scope + evidence_pack → coverage_cards.jsonl (SSOT)
7. **step7_amount_extraction** (optional): coverage_cards + PDF → amount enrichment

**Constitutional Enforcement** (STEP NEXT-31-P1):
- Step4 MUST use sanitized CSV (hard gate: RuntimeError if unsanitized)
- Step5 join-rate gate: 95% threshold (RuntimeError if < 95%)
- Step4 and Step5 use identical scope snapshot via `resolve_scope_csv()`

**Audit Tools** (외부, pipeline 아님):
- `tools/audit/run_step_next_17b_audit.py`: AMOUNT_STATUS_DASHBOARD.md 생성

**DEPRECATED Steps** (STEP NEXT-31-P2: Moved to _deprecated/):
- ~~step0_scope_filter~~ → _deprecated/pipeline/step0_scope_filter/
- ~~step2_extract_pdf~~ → removed (ghost directory)
- ~~step6_build_report~~ → removed
- ~~step7_compare~~ → _deprecated/pipeline/step7_compare/
- ~~step8_multi_compare~~ → _deprecated/pipeline/step8_multi_compare/
- ~~step8_single_coverage~~ → _deprecated/pipeline/step8_single_coverage/
- ~~step9_single_compare~~ → removed
- ~~step10_multi_single_compare~~ → removed
- ~~step10_audit~~ → _deprecated/pipeline/step10_audit/

## Working Directory
`/Users/cheollee/inca-rag-scope`

## Session Start Protocol
매 세션 시작 시:
1. `docs/SESSION_HANDOFF.md` 읽기
2. `STATUS.md` 최신 상태 확인
3. `git status -sb` + `pytest -q` 실행
4. 요청 사항이 scope 내인지 검증 후 진행
