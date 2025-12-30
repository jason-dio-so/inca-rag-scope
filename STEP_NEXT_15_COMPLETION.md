# STEP NEXT-15 Completion Report

**날짜**: 2025-12-29
**버전**: STEP NEXT-15 (Chat UX Scenarios Lock)
**상태**: ✅ **COMPLETE**

---

## 🎯 Mission

실서비스 기준 UX 시나리오 고정 (Production-Level Chat UX Specification)

**목적**: 고객이 실제 서비스에서 경험하게 될 Chat UX 시나리오를 고정하고, 이를 Frontend/Figma/개발 구현의 단일 기준(Single Source of Truth)으로 확립

---

## 📦 Deliverables

### 1. CHAT_UX_SCENARIOS.md ✅

**경로**: `docs/ui/CHAT_UX_SCENARIOS.md`

**내용**:
- **S1. Normal Comparison Query (Happy Path)**
  - 사용자 입력 예시: "삼성화재랑 메리츠 암진단비 비교해줘"
  - 응답 구조 (5단계 고정):
    1. Summary sentence (factual)
    2. Comparison table (status-based)
    3. Per-insurer explanations (parallel)
    4. Common notes / Disclaimers
    5. Evidence accordion (collapsed)
  - 전체 예시 응답 (실제 출력 수준)

- **S2. Incomplete Query (Missing Information)**
  - 사용자 입력: "암보험 비교해줘" (보험사 누락)
  - 시스템 응답: 명확한 재질문 (옵션 제시)
  - 금지사항: 추정, 자동 보정, "인기" 옵션

- **S3. Partial Data Availability**
  - 사용자 입력: "삼성, 메리츠, KB 암진단비 비교"
  - 시스템 응답: 모든 요청 보험사 표시 (NOT_AVAILABLE 포함)
  - 금지사항: 데이터 없는 보험사 숨기기

- **S4. System Limitation (Blocked Request)**
  - 사용자 입력: "제일 좋은 보험 추천해줘"
  - 시스템 응답: 중립적 제약 설명 + 대안 제시
  - 금지사항: 사과/변명 톤, "시스템 한계"

- **S5. Follow-up Query (Context Retention)**
  - 사용자 입력: "암 직접입원비도 같이 봐줘"
  - 시스템 응답: 이전 context 유지 (보험사 동일)
  - 금지사항: 암묵적 추론, auto-expansion

**특징**:
- ChatGPT 스타일 UX 형태 차용 (의미는 다름)
- 모든 응답은 deterministic pipeline 기반
- LLM inference 절대 금지
- Forbidden language validation 적용

---

### 2. CHAT_UX_DOS_AND_DONTS.md ✅

**경로**: `docs/ui/CHAT_UX_DOS_AND_DONTS.md`

**내용**: Anti-pattern guide (개발/QA/디자인 공통 기준)

**섹션별 구성**:

1. **Summary Sentences**
   - ❌ DON'T: "비교한 결과, 다음과 같습니다" (conclusive)
   - ✅ DO: "2개 보험사의 암진단비를 비교합니다" (factual)

2. **Comparison Tables**
   - ❌ DON'T: Sort by amount value (ranking 암시)
   - ✅ DO: Preserve input order

3. **Explanations**
   - ❌ DON'T: "삼성이 메리츠보다 더 높습니다" (comparative)
   - ✅ DO: Parallel, independent explanations

4. **Incomplete Queries**
   - ❌ DON'T: Auto-select insurers (e.g., "top 3")
   - ✅ DO: Request clarification with options

5. **System Limitations**
   - ❌ DON'T: "죄송합니다. 시스템 한계로..." (defensive)
   - ✅ DO: Neutral constraint + actionable alternative

6. **Follow-up Queries**
   - ❌ DON'T: Auto-expand scope ("KB도" → "KB, 현대, 한화")
   - ✅ DO: Honor explicit request only

7. **Evidence / Disclaimers**
   - ❌ DON'T: Summarize evidence snippets
   - ✅ DO: Show original snippet verbatim

8. **Visual Design**
   - ❌ DON'T: Color coding for "best value" (green for max)
   - ✅ DO: Status-based styling only

9. **Response Generation**
   - ❌ DON'T: LLM inference for explanations
   - ✅ DO: Locked templates only

10. **Validation & Testing**
    - ❌ DON'T: Skip forbidden language validation
    - ✅ DO: Validate all user-facing text

**특징**:
- 각 anti-pattern마다 구체적 예시
- Violation 이유 명시
- Correct pattern 제시
- 10개 섹션, 40+ 예시

---

## 🔒 Absolute Constraints (Hard Lock)

다음 사항은 모든 시나리오에서 절대 불가:

| Category | Forbidden | Enforcement |
|----------|-----------|-------------|
| Recommendation | "추천", "권장", "제안" | `forbidden_language.py` |
| Superiority | "유리", "불리", "우수" | `forbidden_language.py` |
| Comparative | "더", "보다", "반면" | `forbidden_language.py` |
| Evaluation | "높다", "낮다", "많다", "적다" | `forbidden_language.py` |
| Calculation | "평균", "합계", "차이" | No calculation code |
| Ranking | "가장", "최고", "최저" | `forbidden_language.py` |
| Sorting | Amount-based order | Order preserved |
| Visual Ranking | Color for best/worst | Status-based ONLY |

---

## ✅ Gate Compliance Verification

### 1. COMPARISON_EXPLANATION_RULES.md 일치성 ✅

- Explanation templates 재사용 (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)
- Forbidden words 목록 일치
- Parallel explanation 규칙 준수

### 2. AMOUNT_PRESENTATION_RULES.md 일치성 ✅

- Status-based styling 규칙 참조
- CONFIRMED: Normal text, inherit color
- UNCONFIRMED: Italic, gray (#666666)
- NOT_AVAILABLE: Strikethrough, light gray (#999999)

### 3. forbidden_language.py 일치성 ✅

- All response texts pass `validate_text()`
- ALLOWLIST_PHRASES 존중 ("비교합니다", "확인합니다")
- EVALUATIVE_FORBIDDEN_PATTERNS 차단

### 4. STEP_NEXT_14B_PRODUCTION_GATE_REPORT.md 일치성 ✅

- ViewModel 구조 준수 (AssistantMessageVM)
- Section kinds 매핑 (comparison_table, insurer_explanations, common_notes, evidence_accordion)
- 금지언어 정책 적용 범위 일치

### 5. Step7 Type-Aware Guardrails 일치성 ✅

- Type C (Hanwha, Hyundai, KB) UNCONFIRMED 70-90% 정상 인정
- "보험가입금액" 복사 금지
- Inference 금지

### 6. STEP7_AMOUNT_AUDIT_LOCK.md 일치성 ✅

- Step7 amount extraction logic 수정 금지
- Audit PASS 후 DB 로드만 허용
- Frozen audit reports 보존

---

## 🎨 Response Component Specifications (Locked)

### 1. Summary Sentence Templates

```python
# Single coverage, N insurers
"{N}개 보험사의 {coverage_name}를 비교합니다."

# Multiple coverages, N insurers
"{N}개 보험사의 {coverage_count}개 담보를 비교합니다."

# Single insurer, single coverage
"{insurer}의 {coverage_name} 정보입니다."
```

### 2. Comparison Table

- Structure: Markdown table or HTML `<table>`
- Order: Preserve input order (NOT sorted by amount)
- Styling: Status-based CSS classes ONLY

### 3. Per-Insurer Explanation Blocks

- Template: From `COMPARISON_EXPLANATION_RULES.md`
- Structure: Parallel (독립 블럭)
- Forbidden: Cross-insurer references

### 4. Common Notes / Disclaimers

```markdown
**유의사항**
- 금액은 가입설계서 기준이며, 실제 계약 조건에 따라 달라질 수 있습니다.
- 보장 범위 및 지급 조건은 약관을 참조하시기 바랍니다.
[Optional: UNCONFIRMED/NOT_AVAILABLE context]
```

### 5. Evidence Accordion

- Default: Collapsed
- Content: Verbatim snippet (NO summarization)
- Format: doc_type + page_number + snippet

---

## 🧪 Testing Scenarios

### S1 Tests (Happy Path)
- [x] Summary sentence contains no forbidden words
- [x] Table order matches input order (not sorted by amount)
- [x] Explanations are parallel (no cross-insurer references)
- [x] Evidence is collapsed by default
- [x] Status styling matches `AMOUNT_PRESENTATION_RULES.md`

### S2 Tests (Incomplete Query)
- [x] System does NOT auto-select insurers/coverages
- [x] Options list is scope-based (no "popular" or "recommended")
- [x] Example query is valid and executable

### S3 Tests (Partial Availability)
- [x] All requested insurers appear in table (including NOT_AVAILABLE)
- [x] UNCONFIRMED shows "금액 명시 없음" (not "-" or "N/A")
- [x] NOT_AVAILABLE shows "해당 담보 없음" (not hidden)
- [x] Disclaimer explains missing data context

### S4 Tests (System Limitation)
- [x] Constraint explanation is factual (no "죄송합니다")
- [x] Alternative is provided (actionable)
- [x] No defensive language ("시스템 한계")

### S5 Tests (Follow-up)
- [x] Context is retained correctly
- [x] Ambiguous context triggers clarification (not auto-inference)
- [x] Blocked requests follow S4 rules

### Universal Tests (All Scenarios)
- [x] `forbidden_language.validate_text()` passes for all response texts
- [x] No amount calculations performed
- [x] No sorting by amount value
- [x] Status-based styling only (no value-based coloring)

---

## 📚 Related Documents

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/ui/CHAT_UX_SCENARIOS.md` | S1-S5 scenario specs | 🔒 LOCKED |
| `docs/ui/CHAT_UX_DOS_AND_DONTS.md` | Anti-pattern guide | 🔒 LOCKED |
| `docs/ui/COMPARISON_EXPLANATION_RULES.md` | Explanation templates | 🔒 LOCKED (STEP NEXT-12) |
| `docs/ui/AMOUNT_PRESENTATION_RULES.md` | CSS/HTML styling | 🔒 LOCKED (STEP NEXT-11) |
| `apps/api/policy/forbidden_language.py` | Language validation | 🔒 LOCKED (STEP NEXT-14-β) |
| `docs/api/AMOUNT_READ_CONTRACT.md` | AmountDTO schema | 🔒 LOCKED (STEP NEXT-11) |
| `docs/STEP_NEXT_14B_PRODUCTION_GATE_REPORT.md` | Production gate | ✅ PASS |

---

## 🎯 DoD (Definition of Done) Checklist

- [x] **S1~S5 모든 시나리오 문서화**
  - S1: Happy Path (full example response)
  - S2: Incomplete Query (clarification)
  - S3: Partial Availability (show all with status)
  - S4: System Limitation (neutral + alternative)
  - S5: Follow-up (context retention)

- [x] **Anti-pattern guide 작성**
  - 10개 섹션, 40+ 예시
  - ❌/✅ 패턴 명시
  - Violation 이유 설명

- [x] **기존 Gate 문서와 충돌 없음**
  - COMPARISON_EXPLANATION_RULES.md ✅
  - AMOUNT_PRESENTATION_RULES.md ✅
  - forbidden_language.py ✅
  - STEP_NEXT_14B_PRODUCTION_GATE_REPORT.md ✅
  - Step7 Type-Aware Guardrails ✅
  - STEP7_AMOUNT_AUDIT_LOCK.md ✅

- [x] **"추천/판단 UX"로 오해될 여지 0**
  - All forbidden patterns explicitly blocked
  - Status-based styling ONLY
  - No LLM inference
  - Fact-based presentation

- [x] **Figma 단계로 넘겨도 되는 수준**
  - Response component specs 상세 정의
  - CSS/HTML examples 제공
  - UI integration rules documented
  - Validation checklist 포함

---

## 🔐 Lock Status

**STEP NEXT-15 산출물은 🔒 LOCKED 상태입니다.**

### Lock Scope

| Document | Version | Lock Date |
|----------|---------|-----------|
| `docs/ui/CHAT_UX_SCENARIOS.md` | 1.0.0 | 2025-12-29 |
| `docs/ui/CHAT_UX_DOS_AND_DONTS.md` | 1.0.0 | 2025-12-29 |

### Modification Policy

다음 항목 변경 시 **version bump** + **documentation update** 필요:

- Scenario structure (S1-S5 구조 변경)
- Response templates (요약 문장, 설명 템플릿)
- Forbidden patterns (금지 패턴 추가/삭제)
- Status semantics (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE 의미)
- Component specifications (Response component 규격)

### Enforcement

- **QA tests**: Validate each scenario
- **Runtime validation**: `forbidden_language.py` blocks violations
- **Code review**: UX compliance checklist

---

## 🚀 Next Steps (STEP NEXT-16)

**제안**: Figma 프로토타입 구현 (Optional)

**목표**: 본 UX 시나리오를 Figma로 시각화

**산출물**:
1. `docs/ui/CHAT_FIGMA_PROTOTYPE.md` (Figma 링크 + 화면별 설명)
2. Figma 파일 (5개 시나리오 × 주요 화면)

**기준**:
- `CHAT_UX_SCENARIOS.md` 준수
- `CHAT_UX_DOS_AND_DONTS.md` anti-pattern 회피
- Status-based styling 적용

**완료 조건**:
- 개발자가 Figma 보고 바로 구현 가능
- QA가 Figma 기준으로 acceptance test 가능

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Total Scenarios | 5 (S1-S5) |
| Total Anti-Patterns | 40+ |
| Total Examples | 60+ |
| Forbidden Words | 15+ patterns |
| Test Cases | 25+ |
| Related Documents | 7 |
| Lines of Documentation | ~2,500 |

---

## ✅ Conclusion

**STEP NEXT-15 완료.**

- ✅ 실서비스 UX 시나리오 5개 고정 (S1-S5)
- ✅ Anti-pattern guide 작성 (10개 섹션, 40+ 예시)
- ✅ 기존 Gate 문서와 충돌 없음 (6개 문서 검증)
- ✅ Figma 단계로 전달 가능 수준

**본 문서는 Frontend/Figma/개발 구현의 Single Source of Truth입니다.**

**Lock Owner**: Product Team + Pipeline Team + UI Team
**Status**: 🔒 **LOCKED**
**Last Updated**: 2025-12-29
