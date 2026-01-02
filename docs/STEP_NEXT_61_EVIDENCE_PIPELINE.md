# 🧱 STEP NEXT-61

Evidence-Based Comparison Pipeline (Step3–Step7)

**Status**: ACTIVE
**Scope**: Step3–Step7 ONLY
**Step1 / Step2**: 🔒 LOCKED (절대 수정 금지)

⸻

## 0. Executive Summary

### Design Philosophy
- ❌ NO LLM (판단/생성/보정에 사용 금지)
- ❌ NO OCR
- ❌ NO Embedding
- ✅ Deterministic, Rule-Based, Reproducible
- ✅ Evidence-First, Scope-First

### What We Are Building
- 이미 확정된 Scope + Canonical 담보를 입력으로
- 약관/설명서/사업방법서에서 **근거 문장(evidence)**만 추출
- Coverage Card → 비교 테이블 → 요약 리포트 생성

👉 고객이 실제로 보는 비교 화면의 근거 엔진

⸻

## 1. Constitutional Rules (절대 규칙)

### 🔒 LOCKED
- ❌ Step1 코드 수정 금지
- ❌ Step2 구조/로직 수정 금지
- ❌ Canonical Dictionary 자동 수정 금지
- ❌ data/scope_v3 외 경로 사용 금지

### ✅ ALLOWED
- Step3–Step7 신규 파일 완전 신규 생성
- Deterministic string matching
- Rule-based query expansion
- Evidence diversity selection

⸻

## 2. Input Contract (SSOT)

### Primary Input
```
data/scope_v3/*_step2_canonical_scope_v1.jsonl
```

Each row guarantees:
- `insurer`
- `coverage_code` (신정원 통일코드)
- `coverage_name_raw` / `normalized`
- `proposal_facts` (금액은 이미 Step1에서 확보됨)

⚠️ Scope에 없는 담보는 이후 단계에서 즉시 REJECT

⸻

## 3. STEP 3 — PDF Text Extraction

### 목적
- Evidence 검색을 위한 텍스트 인덱스 생성
- 전면 파싱 ❌ → page-by-page linear extraction

### 방식
- Tool: PyMuPDF
- Output:
```
data/text/{insurer}/{doc_type}/page_{n}.txt
```

### Gate
- **GATE-3-1**: 페이지 수 = PDF 페이지 수
- **GATE-3-2**: 동일 PDF 재실행 시 checksum 동일

⸻

## 4. STEP 4 — Evidence Search (Deterministic)

### Core Strategy
- Coverage-centric search
- Canonical 담보 1개당 N개의 query variant 생성

### Query Expansion (예시)
- Hyundai: 4 variants
- Hanwha: 6 variants
- KB: 정의 기반 fallback (BM definition)

### Matching Rules
1. Exact string
2. Token-AND
3. Synonym-normalized AND

### Gate
- **GATE-4-1**: Evidence 없는 담보는 명시적으로 EMPTY 처리 (추론 금지)

⸻

## 5. STEP 5 — Coverage Card Building

### Card Definition
Coverage 1개 = Evidence N개 묶음

### Diversity Selection
- doc_type priority (약관 > 사업방법서 > 설명서)
- 동일 문장 중복 제거
- page 분산 보장

### Output
```
data/cards/{insurer}/{coverage_code}.json
```

### Gate
- **GATE-5-1**: Coverage 수 = Step2 canonical coverage 수
- **GATE-5-2**: Join rate ≥ 95%

⸻

## 6. STEP 7 — Amount Enrichment (Read-Only)

⚠️ **중요**
- 금액은 이미 Step1에서 추출됨
- Step7은 재계산/보정 금지
- Evidence와 연결만 수행

### Output
- `coverage_code`
- `payout_amount`
- `premium`
- `period`
- `evidence_refs`

⸻

## 7. Comparison Model (Final Output)

### Comparison Axes
- Coverage existence (O/X)
- Payout amount
- Conditions / exclusions (evidence-based)
- Evidence source transparency

### Output
```
data/compare/{insurer_a}_vs_{insurer_b}.json
```

⸻

## 8. Data Flow Diagram (Textual)

```
Step2 Canonical Scope
        ↓
[STEP 3] PDF Text
        ↓
[STEP 4] Evidence Search
        ↓
[STEP 5] Coverage Cards
        ↓
[STEP 7] Amount Enrichment
        ↓
Comparison View
```

⸻

## 9. Explicit Non-Goals (이번 STEP에서 안 함)
- ❌ Step1 Amount 구조 변경
- ❌ NEW-RUN 정책 도입
- ❌ Embedding / Vector DB
- ❌ 자동 Canonical 확장
- ❌ 추천/의견 생성

⸻

## 10. DoD (Definition of Done)

| 항목 | 기준 |
|------|------|
| Step1/2 변경 | ❌ 없음 |
| Step3–7 신규 파일 | ✅ 생성 |
| Evidence 기반 | ✅ 모든 판단 근거 있음 |
| 재현성 | ✅ 재실행 동일 결과 |
| 고객 화면 설명 가능 | ✅ |

⸻

## 종료 선언

"Scope와 Canonical이 고정된 상태에서
Evidence 기반 비교 파이프라인이 완성되었다.
이후 개선은 정확도 보강이지 구조 변경이 아니다."

⸻

## 다음 행동 (선택 1)
- 👉 이 문서를 `docs/STEP_NEXT_61_EVIDENCE_PIPELINE.md`로 저장
- 👉 Claude에게 "이 지시문 그대로 Step3 구현 시작" 지시
