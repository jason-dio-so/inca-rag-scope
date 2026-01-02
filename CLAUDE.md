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

## Output SSOT (Single Source of Truth) — STEP NEXT-49

**ALL pipeline outputs are in `data/scope_v3/`** (SSOT enforced):
```
data/scope_v3/{insurer}_step1_raw_scope_v3.jsonl          # Step1 output
data/scope_v3/{insurer}_step2_sanitized_scope_v1.jsonl    # Step2-a output
data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl    # Step2-b output
data/scope_v3/{insurer}_step2_dropped.jsonl               # Step2-a audit
data/scope_v3/{insurer}_step2_mapping_report.jsonl        # Step2-b audit
```

**Run Metadata** (reproducibility):
```
data/scope_v3/LATEST                    # Current run ID
data/scope_v3/_RUNS/{run_id}/           # Run-specific metadata
  ├── manifest.yaml                     # Input manifest (if used)
  ├── profiles_sha.txt                  # Profile checksums
  ├── outputs_sha.txt                   # Output checksums
  └── SUMMARY.md                        # Execution counts
```

**Constitutional Rule** (STEP NEXT-52-HK enforced):
1. **Step1/Step2 outputs** → `data/scope_v3/` ONLY
2. **Step3+ inputs** → `data/scope_v3/` ONLY
3. **NEVER read or write** to `data/scope/` (legacy, archived)

**SSOT Enforcement Guardrails** (STEP NEXT-52-HK):
- Code-level validation: Step2-a and Step2-b reject non-`scope_v3/` paths (exit 2)
- Test suite: `tests/test_scope_ssot_no_legacy_step2_outputs.py` fails if any Step2 outputs exist in `data/scope/`
- Physical archive: Legacy Step2 outputs moved to `archive/scope_legacy/run_20260101_step_next_52_hk/`

**Legacy directories** (archived, DO NOT USE):
- `data/scope/` → Legacy only (see `data/scope/README.md`)
- `data/scope_v2/` → `archive/scope_v2_legacy/`

---

## Input/Intermediate Files (NOT SSOT)

**Canonical Mapping Source (INPUT)**:
```
data/sources/mapping/담보명mapping자료.xlsx
```
- 신정원 통일코드 매핑의 단일 출처
- 이 파일에 없는 담보는 처리 금지

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

## 실행 기본 명령 (Canonical Pipeline - STEP NEXT-46)

### Step1: Extract Scope (Raw Extraction)
```bash
# Step1a: Build profile (run once per insurer, or when PDF changes)
python -m pipeline.step1_summary_first.profile_builder_v3 \
  --manifest data/sources/proposal/MANIFEST.yaml \
  --insurer hanwha

# Step1b: Extract raw scope from proposal PDF
python -m pipeline.step1_summary_first.extractor_v3 \
  --manifest data/sources/proposal/MANIFEST.yaml \
  --insurer hanwha

# Output: data/scope_v3/hanwha_step1_raw_scope_v3.jsonl (SSOT)
```

### Step2-a: Sanitize Scope (Fragment/Noise Removal)
```bash
# Step2-a: Sanitize raw extraction (deterministic pattern matching)
python -m pipeline.step2_sanitize_scope.run --insurer hanwha

# Input:  data/scope_v3/hanwha_step1_raw_scope_v3.jsonl
# Output: data/scope_v3/hanwha_step2_sanitized_scope_v1.jsonl (SSOT)
#         data/scope_v3/hanwha_step2_dropped.jsonl (audit trail)
```

### Step2-b: Canonical Mapping (신정원 통일코드)
```bash
# Step2-b: Map to canonical coverage codes (deterministic only)
python -m pipeline.step2_canonical_mapping.run --insurer hanwha

# Input:  data/scope_v3/hanwha_step2_sanitized_scope_v1.jsonl
# Output: data/scope_v3/hanwha_step2_canonical_scope_v1.jsonl (SSOT)
#         data/scope_v3/hanwha_step2_mapping_report.jsonl
```

### Step3+: Downstream Pipeline (STEP NEXT-61 Compliant)
```bash
# Step3: Extract evidence text
python -m pipeline.step3_extract_text.run --insurer hanwha

# Step4: Search evidence (STEP NEXT-61: reads from data/scope_v3/)
python -m pipeline.step4_evidence_search.search_evidence --insurer hanwha

# Step5: Build coverage cards (SSOT)
python -m pipeline.step5_build_cards.build_cards --insurer hanwha

# Step7 (optional): Amount enrichment
python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer hanwha
```

### Quick Start (All Steps)
```bash
# Run all steps for single insurer
INSURER=hanwha

# Step1: Extract raw scope
python -m pipeline.step1_summary_first.profile_builder_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer $INSURER
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer $INSURER

# Step2-a: Sanitize
python -m pipeline.step2_sanitize_scope.run --insurer $INSURER

# Step2-b: Canonical mapping
python -m pipeline.step2_canonical_mapping.run --insurer $INSURER

# Step3+: Downstream
python -m pipeline.step3_extract_text.run --insurer $INSURER
python -m pipeline.step4_evidence_search.search_evidence --insurer $INSURER
python -m pipeline.step5_build_cards.build_cards --insurer $INSURER
```

### Health Check
```bash
# 테스트
pytest -q

# 현재 상태 확인
git status -sb
ls data/scope | head
```

## Pipeline Architecture (Canonical Steps - STEP NEXT-46)

**Canonical Pipeline** (정식 실행 순서):
1. **step1_summary_first** (v3): 가입설계서 PDF → raw scope JSONL (`*_step1_raw_scope.jsonl`)
   - FROZEN: NO sanitization / filtering / judgment logic
   - Output: Raw extraction with proposal_facts + evidences
2. **step2_sanitize_scope** (Step2-a): raw scope → sanitized scope JSONL (`*_step2_sanitized_scope_v1.jsonl`)
   - Deterministic pattern matching (NO LLM)
   - Drops: fragments, clauses, premium waiver targets, sentence-like noise
   - Audit trail: `*_step2_dropped.jsonl`
3. **step2_canonical_mapping** (Step2-b): sanitized scope → canonical scope JSONL (`*_step2_canonical_scope_v1.jsonl`)
   - Maps to 신정원 unified coverage codes (deterministic only)
   - NO row reduction (anti-contamination gate)
   - Unmapped when ambiguous (no guessing)
   - Audit trail: `*_step2_mapping_report.jsonl`
4. **step3_extract_text**: PDF → evidence text (약관/사업방법서/상품요약서)
5. **step4_evidence_search**: canonical scope + text → evidence_pack.jsonl
6. **step5_build_cards**: canonical scope + evidence_pack → coverage_cards.jsonl (SSOT)
7. **step7_amount_extraction** (optional): coverage_cards + PDF → amount enrichment

**Constitutional Enforcement** (STEP NEXT-47):
- Step1 is FROZEN (no further filtering/sanitization logic allowed)
- Step2-a handles ALL sanitization (fragments, clauses, variants)
- Step2-b maps to canonical codes (deterministic only, NO LLM, NO guessing)
- Step2-b MUST preserve row count (anti-reduction gate)
- Step4 MUST use canonical scope input (hard gate: RuntimeError if wrong input)
- Step5 join-rate gate: 95% threshold (RuntimeError if < 95%)

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
