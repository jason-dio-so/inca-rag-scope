# CLAUDE Context – inca-rag-scope

# EXECUTION BASELINE (SSOT)

This file defines the **current reality** of the system.
Any output that contradicts this baseline is considered a **bug or hallucination**.

---

## 1. Active Architecture (as of STEP NEXT-79)

### Primary Data
- coverage_cards_slim.jsonl  ← **Primary comparison input**
- proposal_detail_store.jsonl ← 가입설계서 DETAIL 원문 저장소
- evidence_store.jsonl        ← 근거 스니펫 저장소

### Access Rule
- All DETAIL / EVIDENCE access is **ref-based only**
  - PD:{insurer}:{coverage_code}
  - EV:{insurer}:{coverage_code}:{idx}

❌ No direct raw text embedding in cards  
❌ No full coverage_cards.jsonl usage

---

## 2. Data Flow (Authoritative)

Step5 (Slim Cards + refs)
 → Store Loader (in-memory)
 → API (lazy load by ref)
 → UI (modal / toggle)

---

## 3. KPI Implementation (COMPLETE)

### KPI Summary (STEP NEXT-74)
- payment_type (정액형 / 일당형 / 건별 / 실손 / UNKNOWN)
- limit_summary
- kpi_evidence_refs

### KPI Condition (STEP NEXT-76)
- exclusion_condition
- waiting_period
- reduction_condition
- renewal_type

Rules:
- Deterministic only (regex-based)
- Priority: Proposal DETAIL → Evidence
- UNKNOWN must be explicit, never inferred

---

## 4. /chat API Rules

- /chat MUST operate on Slim Cards output
- Judgment is based on:
  - customer_view
  - kpi_summary
  - kpi_condition
- raw_text is **supplementary only**

### STEP NEXT-77: EX3_COMPARE Response Schema Lock

- **SSOT**: `docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md`
- **Composer**: `apps/api/response_composers/ex3_compare_composer.py`
- **MessageKind**: `EX3_COMPARE` (added to `chat_vm.py`)
- **Rules**:
  - ❌ NO raw text in response body (refs only)
  - ✅ All refs use `PD:` or `EV:` prefix
  - ✅ KPI section (optional) with refs
  - ✅ Table rows with `meta.proposal_detail_ref` + `meta.evidence_refs`
  - ✅ Deterministic only (NO LLM)

### STEP NEXT-78: Intent Router Lock + EX2_LIMIT_FIND

- **SSOT**: `docs/ui/INTENT_ROUTER_RULES.md`
- **Composer**: `apps/api/response_composers/ex2_limit_find_composer.py`
- **MessageKind**: `EX2_LIMIT_FIND` (added to `chat_vm.py`)
- **Intent Separation** (Anti-Confusion Gates):
  - EX2_LIMIT_FIND: 보장한도/조건 **값 차이 비교** (NO O/X)
  - EX4_ELIGIBILITY: 질병 하위개념 **보장 가능 여부** (O/X/△)
- **Routing Priority**:
  1. Explicit kind (100%)
  2. Category (100%)
  3. Anti-confusion gates (100%)
  4. Pattern matching (fallback)
- **Rules**:
  - ❌ NO O/X/△ in EX2_LIMIT_FIND output
  - ✅ Disease subtypes (제자리암, 유사암, etc.) → EX4_ELIGIBILITY
  - ✅ "보장한도 다른" → EX2_LIMIT_FIND
  - ✅ Intent is LOCKED (cannot be overridden)

### STEP NEXT-79: EX4_ELIGIBILITY Overall Evaluation Lock

- **SSOT**: `docs/audit/STEP_NEXT_79_EX4_OVERALL_EVALUATION_LOCK.md`
- **Composer**: `apps/api/response_composers/ex4_eligibility_composer.py`
- **MessageKind**: `EX4_ELIGIBILITY` (already in `chat_vm.py`)

### STEP NEXT-86/96: EX2_DETAIL Lock (담보 설명 전용 모드 + Customer-First Ordering)

- **SSOT**:
  - `docs/ui/STEP_NEXT_86_EX2_LOCK.md` (Base lock)
  - `docs/ui/STEP_NEXT_96_EX2_CUSTOMER_FIRST_ORDER.md` (Customer-first ordering)
- **Composer**: `apps/api/response_composers/ex2_detail_composer.py`
- **Handler**: `apps/api/chat_handlers_deterministic.py::Example2DetailHandlerDeterministic`
- **MessageKind**: `EX2_DETAIL` (added to `chat_vm.py`)
- **Intent Routing**:
  - `insurers = 1` → **EX2_DETAIL** (설명 전용)
  - `insurers ≥ 2` + "차이/비교" → **EX2_LIMIT_FIND** or **EX3_COMPARE**
- **Rules**:
  - ❌ NO comparison / recommendation / judgment
  - ❌ NO coverage_code exposure (e.g., "A4200_1") in UI
  - ❌ NO raw text in bubble_markdown
  - ✅ 4-section bubble_markdown (핵심요약, 보장요약, 조건요약, 근거안내)
  - ✅ refs MUST use `PD:` / `EV:` prefix
  - ✅ "표현 없음" / "근거 없음" when missing data
  - ✅ Deterministic only (NO LLM)
- **STEP NEXT-96: Customer-First KPI Ordering**:
  - **보장 요약 순서**: 보장금액 (NEW) → 보장한도 → 지급유형
  - **보장금액** displayed FIRST (when available)
  - Answers customer question "얼마 받나요?" immediately
  - View layer ONLY (NO business logic change)
  - Fallback: No amount → original order (보장한도부터)
- **Definition**:
  > EX2_DETAIL = "고객 질문에 바로 답하는 담보 설명"
  > 비교·추천·판단은 EX3 / EX4 전용
- **Contract Tests**:
  - `tests/test_ex2_bubble_contract.py` (7 tests, base contract)
  - `tests/test_step_next_96_customer_first_order.py` (8 tests, ordering)

### STEP NEXT-94/95: Coverage Grouping UX (담보 군집화) Lock

- **SSOT**: `docs/audit/STEP_NEXT_94_COVERAGE_GROUPING_LOCK.md`
- **Runtime Proof**: `docs/audit/STEP_NEXT_95_GROUPING_RUNTIME_PROOF.md`
- **Utility**: `apps/api/response_composers/utils.py::assign_coverage_group()`
- **Applied to**: EX4_ELIGIBILITY bubble_markdown ONLY
- **NOT Applied to**: EX2_DETAIL, EX2_LIMIT_FIND, EX3_COMPARE (단일 담보 설계)

**Core Rules**:
- ❌ NO business logic change (view layer ONLY)
- ❌ NO LLM usage (deterministic keyword matching)
- ❌ NO grouping in judgment/comparison logic
- ✅ 3 groups max: "진단 관련 담보", "치료/수술 관련 담보", "기타 담보"
- ✅ Single group → NO header, Multiple groups → show headers
- ✅ Group label is display text ONLY (not used in statistics/judgment)

**Grouping Priority**:
1. Name keyword (explicit) > Trigger (inferred)
2. "진단비", "진단급여" → 진단 관련 담보
3. "수술비", "치료비", "입원", "통원" → 치료/수술 관련 담보
4. Fallback → 기타 담보

**Constitutional Guarantees**:
- ✅ Judgment results unchanged (O/△/X preserved)
- ✅ Decision unchanged (RECOMMEND/NOT_RECOMMEND/NEUTRAL)
- ✅ NO coverage_code/Unknown/raw_text exposure
- ✅ Tests: 21 tests (14 contract + 7 runtime proof, all PASSED)

### STEP NEXT-97: Customer Demo UX Stabilization (UI/Flow ONLY)

- **SSOT**: `docs/ui/STEP_NEXT_97_DEMO_UX_STABILIZATION.md`
- **Modified Files**:
  - `apps/web/components/ChatPanel.tsx` (auto-scroll + context lock)
  - `apps/web/components/SidebarCategories.tsx` (collapsible sidebar)
  - `apps/web/lib/normalize/table.ts` (kpi_condition type fix)
- **Rules**:
  - ✅ Left sidebar collapsed by default (12px, demo mode)
  - ✅ Auto-scroll on new bubble (only if user near bottom, threshold 100px)
  - ✅ Conversation context lock (insurer selector disabled after first message)
  - ✅ Visual indicator: "현재 대화 조건: 삼성화재 · 메리츠화재"
  - ✅ "조건 변경" button → confirm → page reload
  - ❌ NO backend/API/business logic change
  - ❌ NO LLM usage
  - ❌ NO data structure change
- **Definition of Success**:
  > "고객이 설명 없이 1분 안에 써보고 '아, 이렇게 쓰는 거구나' 라고 말하면 성공"

### STEP NEXT-98: Question Continuity Hints (View Layer Text ONLY)

- **SSOT**: `docs/ui/STEP_NEXT_98_QUESTION_CONTINUITY_LOCK.md`
- **Modified Files**:
  - `apps/api/response_composers/ex2_detail_composer.py` (question hints in bubble_markdown)
  - `apps/api/response_composers/ex4_eligibility_composer.py` (subtype expansion hints in bubble_markdown)
- **Rules**:
  - ✅ EX2_DETAIL: 설명 → 탐색 연결 (보장한도 차이 질문 힌트)
  - ✅ EX4_ELIGIBILITY: 판단 → 조건 확장 비교 연결 (subtype 확장 힌트)
  - ✅ 순수 텍스트 힌트만 (NO 버튼, NO 자동 실행)
  - ✅ 고객이 그대로 복사해 물어도 동작
  - ❌ NO 자동 질문 실행
  - ❌ NO 추천/점수/랭킹
  - ❌ NO EX2 ↔ EX4 자동 점프
  - ❌ NO LLM usage
  - ❌ NO business logic change
- **Definition of Success**:
  > "답변은 닫고, 질문은 연다 — 시스템은 사고의 다음 계단만 보여준다"
- **Tests**: 19 contract tests PASS (7 EX2 + 12 EX4, all PASSED)

### STEP NEXT-99: 고객 데모용 대표 질문 시나리오 LOCK (Docs ONLY)

- **SSOT**: `docs/ui/STEP_NEXT_99_DEMO_QUESTION_FLOW.md`
- **Audit**: `docs/audit/STEP_NEXT_99_DEMO_LOCK.md`
- **Scope**: Demo Flow / Docs / Example UX ONLY (NO code changes)
- **3 Locked Scenarios**:
  - **Scenario A**: EX2 → EX3 → EX2 (설명 → 직접 비교 → 탐색 확장)
  - **Scenario B**: EX4 → EX3 → EX2 (판단 → 비교 → 구조 이해)
  - **Scenario C**: EX3 단독 (비교 핵심 강조)
- **Rules**:
  - ✅ EX3 positioned as central step (비교가 핵심)
  - ✅ All scenarios use single coverage × multiple insurers (EX3 constitutional lock)
  - ✅ Demo scripts for 1-min / 3-min / 5-min presentations
  - ✅ Frontend example buttons already aligned
  - ❌ NO functional changes (ZERO code modified)
  - ❌ NO auto-execution / buttons / recommendations
  - ❌ NO LLM usage
  - ❌ NO Intent boundary violations
- **Definition of Success**:
  > "EX2(설명) → EX3(비교) → EX4(판단), 3가지 Intent가 자연스럽게 이어지는 질문 흐름이 곧 제품의 핵심 UX다"
- **Code Changes**: ZERO (documentation only)
- **Tests**: 19/19 PASS (unchanged)

### STEP NEXT-100: Frontend Payload Bug Fix (View Layer ONLY)

- **SSOT**: `docs/audit/STEP_NEXT_100_PAYLOAD_FIX.md`
- **Modified Files**: `apps/web/app/page.tsx` (3 changes)
- **Root Cause**:
  1. Clarification 선택 후 UI state (`selectedInsurers`, `coverageInput`) 미업데이트
  2. `undefined` 값이 `JSON.stringify`에서 자동 제거됨
- **Fixes**:
  - ✅ `handleClarificationSelect`: UI state 동기화 (setCoverageInput, setSelectedInsurers)
  - ✅ `handleSend`: Request payload builder SSOT (state capture before async)
  - ✅ Auto-retry 로직: `need_more_info` 반환 시 클라이언트 값으로 1회 자동 재시도
- **Rules**:
  - ❌ NO backend/API change
  - ❌ NO LLM usage
  - ✅ View layer ONLY (frontend only)
  - ✅ Auto-retry 최대 1회 (무한 루프 방지)
- **Tests**: 3/3 PASS (manual_test_step_next_100_payload.py)
- **Definition of Success**:
  > "Payload에 insurers/coverage_names 누락 = 0회, 고객 데모에서 추가 정보 필요 오판 노출 = 0회"

### STEP NEXT-101: Conversation Context Carryover (Frontend) + Example Sync Lock

- **SSOT**: `docs/audit/STEP_NEXT_101_CONTEXT_CARRYOVER.md`
- **Modified Files**: `apps/web/app/page.tsx` (5 changes)
- **Root Cause**:
  - Example button은 payload에 값 주입하지만 UI state 미업데이트
  - Follow-up 질문 시 state 비어있음 → payload 누락 → need_more_info 오발생
- **Fixes**:
  - ✅ `ConversationContext` state 추가 (lockedInsurers, lockedCoverageNames, isLocked)
  - ✅ `buildChatPayload` SSOT 함수 (우선순위: override → UI state → locked context)
  - ✅ `handleSendWithKind`: Example button 클릭 시 UI state 동기화 + context locking
  - ✅ `handleSend`: buildChatPayload 사용 + 간소화 + context locking
  - ✅ `handleClarificationSelect`: context locking 추가
- **Context Lock Trigger**: 첫 성공 응답 (`need_more_info=false` + `insurers` 존재)
- **Context Unlock**: "조건 변경" 버튼 → page reload
- **Rules**:
  - ❌ NO backend change
  - ❌ NO LLM usage
  - ✅ View layer ONLY (state/payload/UX)
  - ✅ Payload builder는 단일 함수 (SSOT)
  - ✅ Context 유지 (사용자가 unlock하기 전까지)
- **Definition of Success**:
  > "Example button → 답변 → Follow-up 타이핑 → 전송 흐름이 추가 정보 패널 없이 자연스럽게 연결"

### STEP NEXT-102: EX2 Context Continuity Lock (Frontend) — Insurer Switch + LIMIT_FIND Validation

- **SSOT**: `docs/ui/STEP_NEXT_102_EX2_CONTEXT_CONTINUITY_LOCK.md`
- **Modified Files**:
  - `apps/web/lib/contextUtils.ts` (NEW): 4 deterministic pattern matchers
  - `apps/web/app/page.tsx` (3 changes)
- **Root Cause**:
  1. Insurer switch 미지원 ("메리츠는?" → 삼성 유지)
  2. LIMIT_FIND 단일 보험사 오류 (2사 필요한데 1사만 context에 존재)
  3. Clarification handler 덮어쓰기 (삼성 → 메리츠 replace, 원하는 동작: merge)
- **Fixes**:
  - ✅ `isInsurerSwitchUtterance()`: "메리츠는?" 감지 (deterministic regex)
  - ✅ `extractInsurerFromSwitch()`: 보험사명 → code 변환
  - ✅ `isLimitFindPattern()`: "다른 담보", "한도 차이" 감지 (keyword combination)
  - ✅ `handleSend`: Insurer switch 감지 → context update (보험사만 전환, 담보 유지)
  - ✅ `handleSend`: LIMIT_FIND 감지 → 2사 미만이면 clarification 패널 표시
  - ✅ `handleClarificationSelect`: Insurer merge 로직 (기존 + 신규, replace 금지)
- **Demo Flow**:
  1. EX2 버튼 (삼성 암진단비) → EX2_DETAIL
  2. "메리츠는?" → insurer switch → EX2_DETAIL (meritz)
  3. "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" → LIMIT_FIND 감지 → 1사만 존재 → 보험사 추가 UI → 삼성 선택 → 자동 재전송 (samsung + meritz) → EX2_LIMIT_FIND 표 출력
- **Rules**:
  - ❌ NO LLM usage (deterministic only)
  - ❌ NO backend change
  - ❌ NO coverage_code UI 노출
  - ✅ Insurer switch는 frontend pattern matching
  - ✅ LIMIT_FIND는 2사 이상 보장
  - ✅ Clarification은 merge (not replace)
- **Definition of Success**:
  > "삼성 EX2 → 메리츠는? → LIMIT_FIND 흐름이 추가 정보 패널 없이 자연스럽게 이어진다"

### STEP NEXT-103: EX2 Insurer Switch Payload Override + EX2_DETAIL Display Name Lock

- **SSOT**: `docs/audit/STEP_NEXT_103_EX2_SWITCH_PAYLOAD_PROOF.md`
- **Modified Files**:
  - `apps/web/app/page.tsx` (payload override in handleSend)
  - `apps/api/response_composers/ex2_detail_composer.py` (display name usage)
- **Root Cause**:
  1. Frontend: "메리츠는?" 감지 후 state 업데이트만 하고 payload는 이전 값 전송
  2. Backend: EX2_DETAIL title/summary에서 insurer code (samsung, meritz) 노출
- **Fixes**:
  - ✅ Frontend: Insurer switch 감지 시 `effectiveInsurers`/`effectiveKind` 우선 적용 (payload SSOT)
  - ✅ Backend: `format_insurer_name()` 사용하여 display name (삼성화재, 메리츠화재) 통일
  - ✅ Question hints도 display name 사용 ("삼성화재와 다른 보험사의...")
- **Rules**:
  - ❌ NO insurer code in title/summary/bubble_markdown (samsung, meritz, kb 등)
  - ❌ NO coverage_code exposure (A4200_1 등)
  - ✅ Display names ONLY (삼성화재, 메리츠화재, KB손해보험, 한화손해보험, 현대해상, 롯데손해보험, DB손해보험, 흥국화재)
  - ✅ Insurer codes OK in refs (PD:samsung:, EV:meritz: 등)
  - ✅ Deterministic only (NO LLM)
- **Contract Tests**:
  - `tests/test_ex2_detail_display_name_no_code.py` (7 tests, all PASS)
  - Regression: `tests/test_ex2_bubble_contract.py` (7 tests, all PASS)
  - Regression: `tests/test_step_next_96_customer_first_order.py` (8 tests, all PASS)
- **Definition of Success**:
  > "고객 데모에서 '메리츠는?'를 입력하면 즉시 메리츠 데이터로 전환되고, 응답 타이틀에 '메리츠화재'가 표시된다. 추가 설명 없이 자연스럽다."

❌ Do NOT assume PostgreSQL as SSOT
❌ DB connection errors are out-of-scope

---

## 5. Forbidden Assumptions (Hard Stop)

- coverage_cards.jsonl (full) is deprecated
- Vector DB / LLM inference is NOT used for KPI
- “명시 없음” is allowed **only if**
  - DETAIL does not exist structurally

---

If unsure, ASK. Do not guess.

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
