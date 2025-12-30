# Chat UX Scenarios (Production Specification)

**Version**: 1.1.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-15 (Updated: NEXT-17)

---

## 🎯 Purpose

This document defines **production-level UX scenarios** for the Chat interface.

**CRITICAL**: This is NOT a demo specification. This is the **Single Source of Truth** for:
- Customer-facing UX behavior
- Frontend/Figma implementation
- QA/acceptance testing

All chat interactions MUST follow these locked scenarios.

---

## 🔒 Absolute Constraints (Non-Negotiable)

The following are **IMMUTABLE** across all scenarios:

| Constraint | Enforcement |
|------------|-------------|
| ❌ Insurance recommendations | BLOCKED by `forbidden_language.py` |
| ❌ Superiority judgments (better/worse) | BLOCKED by `forbidden_language.py` |
| ❌ Amount calculations (average/sum/difference) | NO calculation code in pipeline |
| ❌ Sorting by amount | Order preserved from input |
| ❌ Color coding for ranking | Status-based styling ONLY |
| ❌ LLM inference responses | Deterministic pipeline ONLY |
| ✅ Fact-based presentations | Template-based responses |

---

## 📋 Scenario Coverage

| Scenario | Description | User Expectation |
|----------|-------------|------------------|
| **S1** | Normal comparison query (Happy Path) | Clear comparison table + explanations |
| **S2** | Incomplete query (missing info) | Polite clarification request |
| **S3** | Partial data availability | Show available + mark unavailable |
| **S4** | Valid query but system limitation | Graceful constraint explanation |
| **S5** | Follow-up query (context retention) | Context-aware response |

---

## S1. Normal Comparison Query (Happy Path)

### 🎯 Scenario Goal
User provides sufficient information for comparison → System returns structured comparison.

---

### 📥 User Input Examples

```
"삼성화재랑 메리츠 암진단비 비교해줘"
"KB손해보험이랑 한화손해보험 암 직접입원비 알려줘"
"현대해상, DB손해보험 암 수술비 보장금액 확인"
```

---

### 📤 System Response Structure (LOCKED)

Response MUST follow this **exact order**:

```
1. Summary sentence (factual statement ONLY)
2. Comparison table (status-based display)
3. Per-insurer explanation blocks (parallel, not comparative)
4. Common notes / Disclaimers
5. Evidence accordion (expandable)
```

---

### 📝 Example Response (Full)

**User Input**:
```
"삼성화재랑 메리츠 암진단비 비교해줘"
```

**System Response**:

```markdown
2개 보험사의 암진단비를 비교합니다.

┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 메리츠화재     │ 2천만원          │
└────────────────┴──────────────────┘

**보험사별 설명**

**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.

**메리츠화재**
메리츠화재의 암진단비는 가입설계서에 2천만원으로 명시되어 있습니다.

**유의사항**
- 금액은 가입설계서 기준이며, 실제 계약 조건에 따라 달라질 수 있습니다.
- 보장 범위 및 지급 조건은 약관을 참조하시기 바랍니다.

▼ 근거 자료 (Evidence)
  [Click to expand]

  **삼성화재**
  - 출처: 가입설계서 3페이지
  - 발췌: "암진단비: 가입금액 3천만원"

  **메리츠화재**
  - 출처: 가입설계서 2페이지
  - 발췌: "암 진단 시 보험가입금액 2천만원 지급"
```

---

### ✅ UX Requirements (S1)

- [x] **Summary sentence**: Factual only (e.g., "2개 보험사를 비교합니다")
- [x] **Table order**: Preserve input order (삼성 → 메리츠)
- [x] **No sorting**: NEVER sort by amount value
- [x] **Parallel explanations**: Each insurer gets independent explanation
- [x] **No comparisons**: NEVER use "더", "보다", "반면"
- [x] **Evidence collapse**: Default collapsed, user can expand
- [x] **Status styling**: Use locked CSS from `AMOUNT_PRESENTATION_RULES.md`

---

### ❌ Forbidden Patterns (S1)

```markdown
❌ "삼성화재가 메리츠화재보다 1천만원 더 높습니다"
   → Violates: Comparative language ("보다", "더")

❌ "삼성화재 3천만원, 메리츠화재 2천만원으로 평균 2천5백만원입니다"
   → Violates: Calculation ("평균")

❌ [Table sorted by amount DESC: 삼성 3천만원, 메리츠 2천만원]
   → Violates: Sorting by amount (should preserve input order)

❌ "삼성화재가 더 유리한 조건입니다"
   → Violates: Recommendation ("유리한")
```

---

## S2. Incomplete Query (Missing Information)

### 🎯 Scenario Goal
User query lacks sufficient information → System requests clarification.

---

### 📥 User Input Examples

```
"암보험 비교해줘"
   → Missing: Which insurers?

"입원비 알려줘"
   → Missing: Which insurers? Which coverage (암 직접입원비? 질병 입원비?)

"삼성이랑 KB 보장금액 확인"
   → Missing: Which coverage?
```

---

### 📤 System Response Structure (LOCKED)

```
1. Acknowledgment (received query)
2. Reason for insufficiency (factual)
3. Options to choose from (bullets or buttons)
4. NO guessing or auto-completion
```

---

### 📝 Example Response (Missing Insurers)

**User Input**:
```
"암진단비 비교해줘"
```

**System Response**:

```markdown
암진단비 비교를 위해 보험사 정보가 필요합니다.

비교하실 보험사를 선택해주세요:
- 삼성화재
- 메리츠화재
- 현대해상
- KB손해보험
- 한화손해보험
- DB손해보험
- 흥국화재
- 롯데손해보험

예시: "삼성화재랑 메리츠 암진단비 비교해줘"
```

**UX Notes**:
- ✅ Simple, direct language
- ✅ List all available insurers (from scope)
- ✅ Provide example query
- ❌ NO auto-selection (e.g., "top 3" insurers)
- ❌ NO recommendations

---

### 📝 Example Response (Missing Coverage)

**User Input**:
```
"삼성이랑 KB 보장금액 알려줘"
```

**System Response**:

```markdown
삼성화재와 KB손해보험의 비교를 위해 담보 정보가 필요합니다.

확인하실 담보를 선택해주세요:
- 암진단비
- 암 직접입원비
- 암 수술비
- 질병입원비
- 질병수술비
(... 기타 scope 내 담보)

예시: "삼성화재랑 KB 암진단비 비교해줘"
```

**UX Notes**:
- ✅ Show scope-covered coverages ONLY
- ❌ NO "recommended" or "popular" coverages
- ❌ NO multi-select auto-expansion

---

### ✅ UX Requirements (S2)

- [x] **Clear reason**: Why is query insufficient?
- [x] **Scope-based options**: Show ONLY scope-covered insurers/coverages
- [x] **Example query**: Provide 1-2 valid examples
- [x] **NO estimation**: Do NOT guess missing parameters
- [x] **NO auto-selection**: Do NOT default to "all insurers" or "top 3"

---

### ❌ Forbidden Patterns (S2)

```markdown
❌ "암보험 비교를 위해 삼성, 메리츠, KB를 기본으로 선택했습니다"
   → Violates: Auto-selection without user consent

❌ "인기 있는 암진단비와 암 직접입원비를 비교합니다"
   → Violates: Auto-expansion + "인기 있는" (recommendation)

❌ "아마도 암진단비를 원하시는 것 같습니다"
   → Violates: Inference / guessing
```

---

## S3. Partial Data Availability (Some Insurers Missing Data)

### 🎯 Scenario Goal
User requests comparison, but some insurers lack data → Show available + mark unavailable.

---

### 📥 User Input Examples

```
"삼성, 메리츠, KB 암진단비 비교"
   → 삼성: CONFIRMED (3천만원)
   → 메리츠: CONFIRMED (2천만원)
   → KB: NOT_AVAILABLE (no coverage)
```

---

### 📤 System Response Structure (LOCKED)

```
1. Summary sentence (mention data availability)
2. Comparison table (include all requested insurers)
3. Per-insurer explanations (including NOT_AVAILABLE)
4. Note about missing data (factual)
5. Evidence accordion
```

---

### 📝 Example Response (Partial Availability)

**User Input**:
```
"삼성, 메리츠, KB 암진단비 비교해줘"
```

**System Response**:

```markdown
3개 보험사의 암진단비를 비교합니다.

┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 메리츠화재     │ 2천만원          │
│ KB손해보험     │ 해당 담보 없음   │  ← Strikethrough, gray
└────────────────┴──────────────────┘

**보험사별 설명**

**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.

**메리츠화재**
메리츠화재의 암진단비는 가입설계서에 2천만원으로 명시되어 있습니다.

**KB손해보험**
KB손해보험에는 해당 담보가 존재하지 않습니다.

**유의사항**
- KB손해보험의 경우 가입설계서 기준으로 해당 담보를 확인할 수 없습니다.
- 보장 여부는 상품에 따라 다를 수 있으므로, 정확한 내용은 약관을 참조하시기 바랍니다.
```

**UX Notes**:
- ✅ Include KB in table (do NOT hide missing insurers)
- ✅ Use status-based styling: strikethrough + gray for "해당 담보 없음"
- ✅ Provide factual explanation for KB ("존재하지 않습니다")
- ❌ NO "KB는 제외합니다" → MUST show all requested insurers
- ❌ NO "삼성과 메리츠만 비교합니다" → Include KB with NOT_AVAILABLE status

---

### 📝 Example Response (UNCONFIRMED Status - Type C Insurer)

**User Input**:
```
"삼성, 한화 암진단비 비교"
```

**System Response**:

```markdown
2개 보험사의 암진단비를 비교합니다.

┌────────────────┬──────────────────────────┐
│ 보험사         │ 암진단비                  │
├────────────────┼──────────────────────────┤
│ 삼성화재       │ 3천만원                  │
│ 한화손해보험   │ 금액 미기재              │
│                │ (보험가입금액 기준)      │  ← Italic, gray
└────────────────┴──────────────────────────┘

**보험사별 설명**

**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.

**한화손해보험**
한화손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.

**유의사항**
- 한화손해보험의 경우 '보험가입금액' 구조를 사용합니다.
- 이 경우 담보별 금액이 개별적으로 명시되지 않으며, 가입설계서에는 '보험가입금액 지급' 형태로만 표기됩니다.
- 정확한 보장 금액은 약관 또는 담당자를 통해 확인하시기 바랍니다.
```

**UX Notes**:
- ✅ Use two-line display for Type C UNCONFIRMED: "금액 미기재" + "(보험가입금액 기준)"
- ✅ Do NOT show actual amount numbers (e.g., ❌ "5,000만원")
- ✅ Add Type C structure explanation in **유의사항** section
- ✅ Do NOT hide UNCONFIRMED insurers
- ❌ NO inference or amount extraction from "보험가입금액"

---

### ✅ UX Requirements (S3)

- [x] **Include all requested insurers**: NEVER hide NOT_AVAILABLE or UNCONFIRMED
- [x] **Status-based styling**: See `AMOUNT_PRESENTATION_RULES.md`
  - CONFIRMED: Normal text, inherit color
  - UNCONFIRMED (Type A/B): Italic, gray (#666666), "금액 명시 없음"
  - UNCONFIRMED (Type C): Italic, gray (#666666), "금액 미기재" + "(보험가입금액 기준)"
  - NOT_AVAILABLE: Strikethrough, light gray (#999999), "해당 담보 없음"
- [x] **Factual explanations**: No "데이터 부족", use locked templates
- [x] **Disclaimer note**: Explain missing data context
- [x] **Type C structure note**: Add explanation about "보험가입금액 구조" when Type C insurer is present

---

### ❌ Forbidden Patterns (S3)

```markdown
❌ "KB는 데이터가 없어서 제외했습니다"
   → Violates: Hiding requested insurer

❌ "삼성과 메리츠만 비교 가능합니다"
   → Violates: Excluding KB without showing NOT_AVAILABLE

❌ "한화는 정보 부족으로 확인 불가"
   → Violates: Ambiguous status (use "금액 미기재")

❌ [Table shows only 삼성, 메리츠 without KB row]
   → Violates: Must show all requested insurers with status

❌ "한화손해보험: 5,000만원 (보험가입금액 기준)"
   → Violates: NEVER show inferred amounts for Type C insurers

❌ "한화손해보험: 보험가입금액"
   → Violates: Ambiguous - use "금액 미기재 (보험가입금액 기준)" instead
```

---

## S4. Valid Query but System Limitation

### 🎯 Scenario Goal
User asks valid question but system cannot answer due to policy constraints → Graceful explanation.

---

### 📥 User Input Examples

```
"이 중에 제일 좋은 보험 추천해줘"
"어디가 더 유리해?"
"암보험 가성비 순위 알려줘"
"평균 보장금액은 얼마야?"
```

---

### 📤 System Response Structure (LOCKED)

```
1. Acknowledge request (received)
2. Explain constraint (factual, no apology tone)
3. Offer alternative (what system CAN do)
4. Example query
```

---

### 📝 Example Response (Recommendation Request)

**User Input**:
```
"이 중에 제일 좋은 보험 추천해줘"
```

**System Response**:

```markdown
보험 상품의 추천 및 우열 비교는 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 비교 (사실 기반)
- 담보별 가입설계서 명시 내용
- 보장 범위 및 조건 (약관 기준)

예시: "삼성화재랑 메리츠 암진단비 비교해줘"
```

**UX Notes**:
- ✅ Neutral, factual tone (NOT "죄송합니다" or "안타깝지만")
- ✅ Explain constraint briefly (1 sentence)
- ✅ Offer concrete alternatives
- ❌ NO "시스템 한계로..." (sounds defensive)
- ❌ NO long apology or explanation

---

### 📝 Example Response (Calculation Request)

**User Input**:
```
"평균 보장금액은 얼마야?"
```

**System Response**:

```markdown
보장금액의 평균, 합계 등 계산 기능은 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 (가입설계서 기준)
- 담보별 비교 테이블

예시: "삼성, 메리츠, KB 암진단비 비교해줘"
```

---

### 📝 Example Response (Ranking Request)

**User Input**:
```
"암보험 가성비 순위 알려줘"
```

**System Response**:

```markdown
보험 상품의 순위 및 가성비 평가는 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 비교
- 담보별 가입설계서 명시 내용

예시: "삼성화재랑 메리츠 암진단비 비교해줘"
```

---

### ✅ UX Requirements (S4)

- [x] **Neutral tone**: NOT "죄송합니다", NOT "불가능합니다"
- [x] **Brief constraint explanation**: 1 sentence max
- [x] **Actionable alternatives**: Show what user CAN do
- [x] **Example query**: Provide valid query example
- [x] **NO defensive language**: Avoid "시스템 한계", "아직 지원 안 됨"

---

### ❌ Forbidden Patterns (S4)

```markdown
❌ "죄송하지만 추천 기능은 아직 지원하지 않습니다. 향후 업데이트 예정입니다."
   → Violates: Apologetic + future promise (not factual)

❌ "시스템의 한계로 평균 계산은 불가능합니다"
   → Violates: Defensive tone ("한계")

❌ "비교는 가능하지만 추천은 안 됩니다. 혹시 다른 질문 있으세요?"
   → Violates: Vague + filler question

❌ [No alternative offered, just rejection]
   → Violates: Must provide actionable alternative
```

---

## S5. Follow-up Query (Context Retention)

### 🎯 Scenario Goal
User asks follow-up question based on previous context → System retains context and responds.

---

### 📥 User Input Examples

**Previous Query**:
```
"삼성화재랑 메리츠 암진단비 비교해줘"
```

**Follow-up Queries**:
```
"그럼 암 직접입원비도 같이 봐줘"
   → Add coverage to existing insurer pair

"삼성만 자세히 알려줘"
   → Drill down on single insurer

"KB도 추가해서 비교해줘"
   → Add insurer to existing query

"이거 평균은?"
   → BLOCKED (calculation not allowed)
```

---

### 📤 System Response Structure (LOCKED)

```
1. Acknowledge context (optional, brief)
2. Execute new query with context
3. Response follows S1/S2/S3/S4 rules
```

---

### 📝 Example Response (Add Coverage)

**Previous Query**:
```
"삼성화재랑 메리츠 암진단비 비교해줘"
```

**Follow-up**:
```
"암 직접입원비도 같이 봐줘"
```

**System Response**:

```markdown
삼성화재와 메리츠화재의 암 직접입원비를 비교합니다.

┌────────────────┬──────────────────┐
│ 보험사         │ 암 직접입원비     │
├────────────────┼──────────────────┤
│ 삼성화재       │ 1일당 10만원     │
│ 메리츠화재     │ 1일당 5만원      │
└────────────────┴──────────────────┘

(... 보험사별 설명, 유의사항, 근거 자료 ...)
```

**UX Notes**:
- ✅ Context retained: Same insurers (삼성, 메리츠)
- ✅ New coverage added: 암 직접입원비
- ❌ NO "이전 질문에 이어서..." (unnecessary)
- ❌ NO combining multiple coverages in one table (unless user explicitly asks)

---

### 📝 Example Response (Add Insurer)

**Previous Query**:
```
"삼성화재랑 메리츠 암진단비 비교해줘"
```

**Follow-up**:
```
"KB도 추가해서 비교해줘"
```

**System Response**:

```markdown
3개 보험사의 암진단비를 비교합니다.

┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 메리츠화재     │ 2천만원          │
│ KB손해보험     │ 해당 담보 없음   │
└────────────────┴──────────────────┘

(... 보험사별 설명, 유의사항, 근거 자료 ...)
```

**UX Notes**:
- ✅ Context retained: Same coverage (암진단비)
- ✅ New insurer added: KB
- ✅ KB shows NOT_AVAILABLE (per S3 rules)

---

### 📝 Example Response (Drill Down on Single Insurer)

**Previous Query**:
```
"삼성화재랑 메리츠 암진단비 비교해줘"
```

**Follow-up**:
```
"삼성만 자세히 알려줘"
```

**System Response**:

```markdown
삼성화재의 암진단비 정보입니다.

**보장금액**
3천만원

**출처**
가입설계서 3페이지

**근거 원문**
"암진단비: 가입금액 3천만원. 암으로 진단 확정 시 1회 지급."

**유의사항**
- 금액은 가입설계서 기준입니다.
- 실제 지급 조건은 약관을 참조하시기 바랍니다.
```

**UX Notes**:
- ✅ Context retained: 삼성화재, 암진단비
- ✅ Single insurer view (NOT comparison)
- ✅ Show more detail: Evidence snippet inline

---

### 📝 Example Response (Blocked Follow-up)

**Previous Query**:
```
"삼성화재랑 메리츠 암진단비 비교해줘"
```

**Follow-up**:
```
"이거 평균은?"
```

**System Response**:

```markdown
보장금액의 평균 계산은 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 (가입설계서 기준)
- 담보별 비교 테이블

예시: "삼성화재랑 메리츠 암 직접입원비도 비교해줘"
```

**UX Notes**:
- ✅ Follow S4 rules (system limitation)
- ✅ Provide alternative (re-query with more coverages)

---

### ✅ UX Requirements (S5)

- [x] **Context retention**: Remember insurers/coverages from previous query
- [x] **Explicit context**: If ambiguous, ask for clarification
- [x] **NO implicit inference**: Do NOT guess missing context
- [x] **Follow S1-S4 rules**: All responses follow locked structure
- [x] **Context timeout**: (Optional) Clear context after N minutes or explicit user reset

---

### ❌ Forbidden Patterns (S5)

```markdown
❌ "이전 질문에 이어서 암 직접입원비를 추가로 비교합니다"
   → Violates: Unnecessary preamble (just show result)

❌ [User says "KB도 추가" → System auto-expands to "KB, 현대, DB"]
   → Violates: Auto-expansion beyond user request

❌ [User says "평균은?" → System calculates and shows]
   → Violates: Calculation forbidden (must follow S4)

❌ [After 10 minutes → System forgets context without notice]
   → Violates: Should notify or ask for re-confirmation if context expired
```

---

## 🎨 Response Component Specifications

### 1. Summary Sentence (Template-Based)

**Templates** (LOCKED):

```python
# Single coverage, N insurers
"{N}개 보험사의 {coverage_name}를 비교합니다."

# Multiple coverages, N insurers
"{N}개 보험사의 {coverage_count}개 담보를 비교합니다."

# Single insurer, single coverage
"{insurer}의 {coverage_name} 정보입니다."
```

**Examples**:
```
✅ "2개 보험사의 암진단비를 비교합니다."
✅ "3개 보험사의 5개 담보를 비교합니다."
✅ "삼성화재의 암진단비 정보입니다."

❌ "삼성화재와 메리츠화재의 암진단비를 비교한 결과, 다음과 같습니다."
   → Too verbose, "결과" implies conclusion

❌ "암진단비 비교 결과를 안내드립니다."
   → "안내드립니다" is too formal/service-oriented
```

---

### 2. Comparison Table (HTML/Markdown)

**Structure** (LOCKED):

```markdown
┌────────────────┬──────────────────┬──────────────────┐
│ 보험사         │ 담보1            │ 담보2            │
├────────────────┼──────────────────┼──────────────────┤
│ 보험사A        │ value_text       │ value_text       │
│ 보험사B        │ value_text       │ 금액 명시 없음   │
│ 보험사C        │ 해당 담보 없음   │ value_text       │
└────────────────┴──────────────────┴──────────────────┘
```

**Styling Rules**:
- CONFIRMED: Normal text, inherit color
- UNCONFIRMED: Italic, gray (#666666)
- NOT_AVAILABLE: Strikethrough, light gray (#999999)

**Forbidden**:
- ❌ Sorting by amount
- ❌ Color coding for "best value"
- ❌ Bold for max/min
- ❌ Icons for ranking

**See**: `docs/ui/AMOUNT_PRESENTATION_RULES.md` for full CSS specs

---

### 3. Per-Insurer Explanation Blocks (Parallel)

**Structure** (LOCKED):

```markdown
**{insurer}**
{explanation_sentence}
```

**Templates** (from `COMPARISON_EXPLANATION_RULES.md`):

```python
# CONFIRMED
"{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."

# UNCONFIRMED
"{insurer}의 {coverage_name}는 가입설계서에 금액이 명시되어 있지 않습니다."

# NOT_AVAILABLE
"{insurer}에는 해당 담보가 존재하지 않습니다."
```

**Example**:

```markdown
**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.

**메리츠화재**
메리츠화재의 암진단비는 가입설계서에 2천만원으로 명시되어 있습니다.

**KB손해보험**
KB손해보험에는 해당 담보가 존재하지 않습니다.
```

**Forbidden**:
- ❌ Cross-insurer references (e.g., "삼성은 메리츠보다...")
- ❌ Comparative conjunctions ("반면", "그러나")
- ❌ Evaluative language ("유리", "높다")

---

### 4. Common Notes / Disclaimers

**Template** (LOCKED):

```markdown
**유의사항**
- 금액은 가입설계서 기준이며, 실제 계약 조건에 따라 달라질 수 있습니다.
- 보장 범위 및 지급 조건은 약관을 참조하시기 바랍니다.
[Optional: Additional context for UNCONFIRMED/NOT_AVAILABLE cases]
```

**Example (with UNCONFIRMED)**:

```markdown
**유의사항**
- 금액은 가입설계서 기준이며, 실제 계약 조건에 따라 달라질 수 있습니다.
- 한화손해보험의 경우 담보는 존재하나 가입설계서에 금액이 명시되지 않았습니다.
- 정확한 보장 금액은 약관 또는 담당자를 통해 확인하시기 바랍니다.
```

---

### 5. Evidence Accordion (Expandable)

**Structure** (LOCKED):

```markdown
▼ 근거 자료 (Evidence)
  [Click to expand]

  **{insurer}**
  - 출처: {doc_type} {page_number}페이지
  - 발췌: "{snippet}"

  **{insurer}**
  - 출처: {doc_type} {page_number}페이지
  - 발췌: "{snippet}"
```

**Example**:

```markdown
▼ 근거 자료 (Evidence)

  **삼성화재**
  - 출처: 가입설계서 3페이지
  - 발췌: "암진단비: 가입금액 3천만원. 암으로 진단 확정 시 1회 지급."

  **메리츠화재**
  - 출처: 가입설계서 2페이지
  - 발췌: "암 진단 시 보험가입금액 2천만원 지급. 단, 갑상선암 등 소액암 제외."
```

**UX Notes**:
- ✅ Default: Collapsed (user must click to expand)
- ✅ Show original snippet (NO summarization)
- ✅ Include doc type + page number
- ❌ NO highlighting or emphasis on specific evidence
- ❌ NO re-ordering by "best evidence"

---

## 🚫 Universal Forbidden Patterns (All Scenarios)

The following patterns are **BLOCKED** across ALL scenarios:

| Category | Pattern | Example | Enforcement |
|----------|---------|---------|-------------|
| **Recommendation** | "추천", "권장", "제안" | "삼성을 추천합니다" | `forbidden_language.py` |
| **Superiority** | "유리", "불리", "우수" | "메리츠가 유리합니다" | `forbidden_language.py` |
| **Comparative** | "더", "보다", "반면" | "A가 B보다 높다" | `forbidden_language.py` |
| **Evaluation** | "높다", "낮다", "많다", "적다" | "3천만원으로 높습니다" | `forbidden_language.py` |
| **Calculation** | "평균", "합계", "차이" | "평균 2천5백만원" | No calculation code |
| **Ranking** | "가장", "최고", "최저" | "가장 좋은 조건" | `forbidden_language.py` |
| **Sorting** | Amount-based order | Sort by value DESC | Order preserved from input |
| **Visual Ranking** | Color/icon for best/worst | Green for max, red for min | Status-based styling ONLY |

**Validation**: All response texts pass through `apps/api/policy/forbidden_language.py` before rendering.

---

## 🧪 Testing Scenarios

Each scenario MUST pass the following tests:

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

| Document | Purpose | Path |
|----------|---------|------|
| Comparison Explanation Rules | Explanation templates + forbidden words | `docs/ui/COMPARISON_EXPLANATION_RULES.md` |
| Amount Presentation Rules | CSS/HTML styling for status-based display | `docs/ui/AMOUNT_PRESENTATION_RULES.md` |
| Forbidden Language Policy | Single source for language validation | `apps/api/policy/forbidden_language.py` |
| Amount Read Contract | AmountDTO schema + status semantics | `docs/api/AMOUNT_READ_CONTRACT.md` |
| Chat UX Dos and Don'ts | Anti-patterns + examples | `docs/ui/CHAT_UX_DOS_AND_DONTS.md` |

---

## 🔐 Contract Lock

**This specification is LOCKED as of STEP NEXT-15.**

Any changes to:
- Scenario structure
- Response templates
- Forbidden patterns
- Status semantics

Require **version bump** and **documentation update**.

**Enforcement**:
- QA tests validate each scenario
- `forbidden_language.py` blocks violations at runtime
- Code review checklist includes UX compliance

---

**Lock Owner**: Product Team + Pipeline Team + UI Team
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
