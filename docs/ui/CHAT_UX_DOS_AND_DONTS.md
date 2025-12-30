# Chat UX Dos and Don'ts (Anti-Pattern Guide)

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-15

---

## 🎯 Purpose

This document provides **concrete anti-patterns** for Chat UX implementation.

**Audience**:
- Developers (Frontend/Backend)
- Product Managers
- QA Engineers
- Designers (Figma/UI)

**Usage**: Reference this during code review, QA testing, and design validation.

---

## 📋 How to Use This Document

Each section follows this structure:

```
❌ DON'T: [Anti-pattern description]
   Example: [Bad example]
   Violation: [Which rule is broken]

✅ DO: [Correct pattern]
   Example: [Good example]
   Justification: [Why this is correct]
```

---

## 1. Summary Sentences

### ❌ DON'T: Use Evaluative or Conclusive Language

**Example**:
```
"삼성화재와 메리츠화재의 암진단비를 비교한 결과, 다음과 같습니다."
```

**Violation**: "결과" implies conclusion/judgment

---

### ✅ DO: Use Factual, Neutral Statements

**Example**:
```
"2개 보험사의 암진단비를 비교합니다."
```

**Justification**: Describes action without implying outcome or evaluation

---

### ❌ DON'T: Use Formal Service Language

**Example**:
```
"암진단비 비교 결과를 안내드립니다."
```

**Violation**: "안내드립니다" is too formal/service-oriented (not ChatGPT-style)

---

### ✅ DO: Use Conversational Tone (But Factual)

**Example**:
```
"삼성화재와 메리츠화재의 암진단비를 비교합니다."
```

**Justification**: Natural tone, fact-based, no unnecessary formality

---

## 2. Comparison Tables

### ❌ DON'T: Sort by Amount Value

**Example**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │  ← Highest
│ 메리츠화재     │ 2천만원      │
│ KB손해보험     │ 1천만원      │  ← Lowest
└────────────────┴──────────────┘
```

**Violation**: Sorting by amount implies ranking → recommendation

---

### ✅ DO: Preserve Input Order

**Example** (User said: "메리츠, KB, 삼성 비교"):
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 메리츠화재     │ 2천만원      │  ← Input order
│ KB손해보험     │ 1천만원      │
│ 삼성화재       │ 3천만원      │
└────────────────┴──────────────┘
```

**Justification**: Order reflects user's query, not system's judgment

**Alternative** (If no explicit order): Use coverage_code or insurer alphabetical order (NOT amount)

---

### ❌ DON'T: Use Color Coding for Amount Ranking

**Example**:
```html
<td style="color: green; font-weight: bold">3천만원</td>  ← Max
<td style="color: orange">2천만원</td>
<td style="color: red">1천만원</td>  ← Min
```

**Violation**: Color implies "better/worse" judgment

---

### ✅ DO: Use Status-Based Styling ONLY

**Example**:
```html
<td class="amount-confirmed">3천만원</td>  ← Normal (CONFIRMED)
<td class="amount-unconfirmed">금액 명시 없음</td>  ← Italic + gray
<td class="amount-not-available">해당 담보 없음</td>  ← Strikethrough + light gray
```

**Justification**: Styling reflects data availability status, not value judgment

**Reference**: `docs/ui/AMOUNT_PRESENTATION_RULES.md`

---

### ❌ DON'T: Hide Missing Data

**Example** (User asked for "삼성, KB, 메리츠"):
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │
│ 메리츠화재     │ 2천만원      │
└────────────────┴──────────────┘

※ KB손해보험은 데이터가 없어 제외했습니다.
```

**Violation**: Hiding requested insurer → loses transparency

---

### ✅ DO: Show All Requested Insurers with Status

**Example**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │
│ KB손해보험     │ 해당 담보 없음 │  ← Shown with status
│ 메리츠화재     │ 2천만원      │
└────────────────┴──────────────┘
```

**Justification**: User asked for KB → Must show KB with NOT_AVAILABLE status

---

### ❌ DON'T: Use Ambiguous Placeholders

**Example**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │
│ 한화손해보험   │ -            │  ← Ambiguous
│ 메리츠화재     │ N/A          │  ← Ambiguous
└────────────────┴──────────────┘
```

**Violation**: "-" and "N/A" are ambiguous (UNCONFIRMED vs NOT_AVAILABLE?)

---

### ✅ DO: Use Locked Status Text

**Example**:
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 한화손해보험   │ 금액 명시 없음   │  ← UNCONFIRMED (clear)
│ 메리츠화재     │ 해당 담보 없음   │  ← NOT_AVAILABLE (clear)
└────────────────┴──────────────────┘
```

**Justification**: Unambiguous status text per locked templates

**Reference**: `docs/ui/COMPARISON_EXPLANATION_RULES.md`

---

## 3. Explanations

### ❌ DON'T: Use Comparative Language Across Insurers

**Example**:
```
**삼성화재**
삼성화재의 암진단비는 3천만원으로, 메리츠화재보다 1천만원 더 높습니다.
```

**Violation**: "보다", "더" → Forbidden comparative words

---

### ✅ DO: Use Parallel, Independent Explanations

**Example**:
```
**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.

**메리츠화재**
메리츠화재의 암진단비는 가입설계서에 2천만원으로 명시되어 있습니다.
```

**Justification**: Each explanation stands alone, no cross-references

---

### ❌ DON'T: Use Contrastive Conjunctions

**Example**:
```
**삼성화재**
삼성화재의 암진단비는 3천만원입니다.

**메리츠화재**
반면, 메리츠화재의 암진단비는 2천만원입니다.
```

**Violation**: "반면" (whereas) → Implies comparison/contrast

---

### ✅ DO: Use Identical Template for All Insurers

**Example**:
```
**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.

**메리츠화재**
메리츠화재의 암진단비는 가입설계서에 2천만원으로 명시되어 있습니다.
```

**Justification**: Same template → Guaranteed parallel structure

**Reference**: `docs/ui/COMPARISON_EXPLANATION_RULES.md` (locked templates)

---

### ❌ DON'T: Add Evaluative Context

**Example**:
```
**삼성화재**
삼성화재의 암진단비는 3천만원으로 유리한 조건입니다.
```

**Violation**: "유리한" → Forbidden evaluative word

---

### ✅ DO: State Facts Only

**Example**:
```
**삼성화재**
삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.
```

**Justification**: Factual statement, no evaluation

---

### ❌ DON'T: Infer or Summarize from Evidence

**Example**:
```
**한화손해보험**
한화손해보험의 암진단비는 가입설계서에 명시되지 않았으나, 약관을 보면 1천만원으로 추정됩니다.
```

**Violation**: "추정" → Inference not allowed, evidence must be explicit

---

### ✅ DO: Use Locked Template for UNCONFIRMED

**Example**:
```
**한화손해보험**
한화손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.
```

**Justification**: If not in proposal → UNCONFIRMED (no inference)

---

## 4. Incomplete Queries

### ❌ DON'T: Auto-Select Insurers or Coverages

**Example** (User: "암보험 비교해줘"):
```
삼성화재, 메리츠화재, KB손해보험의 암진단비를 기본으로 선택했습니다.

(... comparison table ...)
```

**Violation**: System selected insurers without user consent

---

### ✅ DO: Request Clarification

**Example**:
```
암보험 비교를 위해 보험사 정보가 필요합니다.

비교하실 보험사를 선택해주세요:
- 삼성화재
- 메리츠화재
- KB손해보험
(... 기타 scope 내 보험사 ...)

예시: "삼성화재랑 메리츠 암진단비 비교해줘"
```

**Justification**: User makes explicit choice, no auto-assumption

---

### ❌ DON'T: Suggest "Recommended" or "Popular" Options

**Example** (User: "암보험 비교해줘"):
```
다음은 인기 있는 보험사 조합입니다:
- 추천: 삼성, 메리츠, KB
- 가성비: 한화, DB

어떤 조합으로 비교하시겠습니까?
```

**Violation**: "인기", "추천", "가성비" → All forbidden (recommendation)

---

### ✅ DO: List All Scope Options Neutrally

**Example**:
```
암보험 비교를 위해 보험사 정보가 필요합니다.

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

**Justification**: Neutral list, no ranking or recommendation

---

### ❌ DON'T: Guess Missing Parameters

**Example** (User: "입원비 비교해줘"):
```
아마도 암 직접입원비를 원하시는 것 같습니다.

(... proceeds with 암 직접입원비 ...)
```

**Violation**: "아마도" → Inference/guessing not allowed

---

### ✅ DO: Ask for Specific Coverage

**Example**:
```
입원비 비교를 위해 담보 정보가 필요합니다.

확인하실 담보를 선택해주세요:
- 암 직접입원비
- 질병입원비
- 상해입원비
(... 기타 scope 내 입원비 관련 담보 ...)

예시: "삼성화재랑 메리츠 암 직접입원비 비교해줘"
```

**Justification**: User makes explicit choice

---

## 5. System Limitations

### ❌ DON'T: Use Apologetic or Defensive Tone

**Example** (User: "제일 좋은 보험 추천해줘"):
```
죄송합니다. 현재 시스템의 한계로 추천 기능은 제공하지 못합니다.
향후 업데이트를 통해 개선하겠습니다.
```

**Violation**: "죄송합니다", "한계", "향후 업데이트" → Defensive + empty promise

---

### ✅ DO: State Constraint Neutrally + Offer Alternative

**Example**:
```
보험 상품의 추천 및 우열 비교는 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 비교 (사실 기반)
- 담보별 가입설계서 명시 내용
- 보장 범위 및 조건 (약관 기준)

예시: "삼성화재랑 메리츠 암진단비 비교해줘"
```

**Justification**: Neutral tone, actionable alternative, no apology

---

### ❌ DON'T: Leave User with No Action

**Example** (User: "평균 금액은?"):
```
평균 계산 기능은 제공하지 않습니다.
```

**Violation**: No alternative offered → Dead end

---

### ✅ DO: Redirect to Available Functionality

**Example**:
```
보장금액의 평균, 합계 등 계산 기능은 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 (가입설계서 기준)
- 담보별 비교 테이블

예시: "삼성, 메리츠, KB 암진단비 비교해줘"
```

**Justification**: User knows what IS available

---

### ❌ DON'T: Expose Technical Errors

**Example** (Internal server error):
```
Error 500: NoneType object has no attribute 'value_text'
Stack trace: ...
```

**Violation**: Technical error exposed to user

---

### ✅ DO: Show User-Friendly Error Message

**Example**:
```
일시적으로 응답을 제공할 수 없습니다.
잠시 후 다시 시도해주시기 바랍니다.
```

**Justification**: Non-technical, actionable

**Note**: Log full error internally for debugging

---

## 6. Follow-Up Queries

### ❌ DON'T: Auto-Expand Scope Without Consent

**Example**:

**Previous**: "삼성화재랑 메리츠 암진단비"

**User**: "KB도 추가"

**System** (WRONG):
```
KB손해보험, 현대해상, 한화손해보험을 추가하여 비교합니다.

(... shows 5 insurers ...)
```

**Violation**: User asked for KB → System added 현대, 한화 without consent

---

### ✅ DO: Honor Explicit Request Only

**Example**:
```
3개 보험사의 암진단비를 비교합니다.

┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │
│ 메리츠화재     │ 2천만원      │
│ KB손해보험     │ 해당 담보 없음│
└────────────────┴──────────────┘

(... explanations ...)
```

**Justification**: User said "KB" → Only add KB (not 현대, 한화)

---

### ❌ DON'T: Perform Blocked Operations on Follow-Up

**Example**:

**Previous**: "삼성화재랑 메리츠 암진단비"

**User**: "이거 평균은?"

**System** (WRONG):
```
삼성화재 3천만원, 메리츠화재 2천만원의 평균은 2천5백만원입니다.
```

**Violation**: Calculation forbidden (even in follow-up context)

---

### ✅ DO: Apply S4 Rules (System Limitation)

**Example**:
```
보장금액의 평균 계산은 제공하지 않습니다.

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 (가입설계서 기준)
- 담보별 비교 테이블

예시: "삼성화재랑 메리츠 암 직접입원비도 비교해줘"
```

**Justification**: Follow-up does NOT bypass constraints

---

### ❌ DON'T: Add Unnecessary Preamble

**Example**:

**User**: "암 직접입원비도 같이 봐줘"

**System** (WRONG):
```
이전 질문에서 삼성화재와 메리츠화재를 비교하셨으므로,
동일한 보험사로 암 직접입원비를 추가로 비교하겠습니다.

(... comparison table ...)
```

**Violation**: Verbose preamble (user knows context)

---

### ✅ DO: Proceed Directly with Context

**Example**:
```
2개 보험사의 암 직접입원비를 비교합니다.

┌────────────────┬──────────────────┐
│ 보험사         │ 암 직접입원비     │
├────────────────┼──────────────────┤
│ 삼성화재       │ 1일당 10만원     │
│ 메리츠화재     │ 1일당 5만원      │
└────────────────┴──────────────────┘

(... explanations ...)
```

**Justification**: Context is implicit, no need to re-state

---

## 7. Evidence / Disclaimers

### ❌ DON'T: Summarize or Paraphrase Evidence

**Example**:
```
▼ 근거 자료

**삼성화재**
- 출처: 가입설계서
- 요약: 암 진단 시 3천만원 지급 (요약됨)
```

**Violation**: "요약됨" → Evidence must be original snippet

---

### ✅ DO: Show Original Snippet

**Example**:
```
▼ 근거 자료

**삼성화재**
- 출처: 가입설계서 3페이지
- 발췌: "암진단비: 가입금액 3천만원. 암으로 진단 확정 시 1회 지급."
```

**Justification**: Verbatim snippet → User can verify

---

### ❌ DON'T: Omit Disclaimers for UNCONFIRMED/NOT_AVAILABLE

**Example** (한화: UNCONFIRMED):
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 한화손해보험   │ 금액 명시 없음   │
└────────────────┴──────────────────┘

(... no disclaimer about 한화 ...)
```

**Violation**: Missing context for "금액 명시 없음" → User may be confused

---

### ✅ DO: Add Contextual Disclaimer

**Example**:
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 한화손해보험   │ 금액 명시 없음   │
└────────────────┴──────────────────┘

**유의사항**
- 금액은 가입설계서 기준이며, 실제 계약 조건에 따라 달라질 수 있습니다.
- 한화손해보험의 경우 담보는 존재하나 가입설계서에 금액이 명시되지 않았습니다.
- 정확한 보장 금액은 약관 또는 담당자를 통해 확인하시기 바랍니다.
```

**Justification**: User understands why "금액 명시 없음" appears

---

## 8. Visual Design (Figma/Frontend)

### ❌ DON'T: Use Visual Emphasis for Amount Ranking

**Example**:
```html
<!-- ❌ WRONG -->
<tr>
  <td>삼성화재</td>
  <td style="background: yellow; font-weight: bold">
    3천만원 ⭐ 최고
  </td>
</tr>
<tr>
  <td>메리츠화재</td>
  <td>2천만원</td>
</tr>
<tr>
  <td>KB손해보험</td>
  <td style="background: lightgray; color: #999">
    1천만원 (최저)
  </td>
</tr>
```

**Violation**: Yellow highlight + "최고" → Ranking/recommendation

---

### ✅ DO: Use Status-Based Styling Only

**Example**:
```html
<!-- ✅ CORRECT -->
<tr>
  <td>삼성화재</td>
  <td class="amount-confirmed">3천만원</td>
</tr>
<tr>
  <td>메리츠화재</td>
  <td class="amount-unconfirmed">금액 명시 없음</td>
</tr>
<tr>
  <td>KB손해보험</td>
  <td class="amount-not-available">해당 담보 없음</td>
</tr>
```

**CSS**:
```css
.amount-confirmed {
  color: inherit;
  font-weight: normal;
}

.amount-unconfirmed {
  color: #666666;
  font-style: italic;
}

.amount-not-available {
  color: #999999;
  text-decoration: line-through;
  background: #f5f5f5;
}
```

**Justification**: Styling reflects data status (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE), not value

**Reference**: `docs/ui/AMOUNT_PRESENTATION_RULES.md`

---

### ❌ DON'T: Add Charts or Graphs for Comparison

**Example**:
```
삼성화재 ████████ 3천만원
메리츠화재 █████ 2천만원
KB손해보험 ██ 1천만원
```

**Violation**: Bar chart implies visual comparison → ranking

---

### ✅ DO: Use Table Layout Only

**Example**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │
│ 메리츠화재     │ 2천만원      │
│ KB손해보험     │ 1천만원      │
└────────────────┴──────────────┘
```

**Justification**: Table shows facts without visual ranking

---

## 9. Response Generation (Backend/LLM)

### ❌ DON'T: Use LLM Inference for Explanations

**Example**:
```python
# ❌ WRONG
explanation = llm.generate(
    f"Explain {insurer}'s {coverage_name} amount: {value_text}"
)
```

**Violation**: LLM may generate forbidden language (non-deterministic)

---

### ✅ DO: Use Locked Templates Only

**Example**:
```python
# ✅ CORRECT
from apps.api.policy.forbidden_language import validate_text

template = "{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."

explanation = template.format(
    insurer="삼성화재",
    coverage_name="암진단비",
    value_text="3천만원"
)

# Validate (enforced)
validate_text(explanation)
```

**Justification**: Template-based → Guaranteed to pass validation

**Reference**: `docs/ui/COMPARISON_EXPLANATION_RULES.md`

---

### ❌ DON'T: Calculate or Aggregate Amounts

**Example**:
```python
# ❌ WRONG
amounts = [3000, 2000, 1000]  # 천만원 단위
average = sum(amounts) / len(amounts)
summary = f"평균 보장금액은 {average}천만원입니다."
```

**Violation**: Calculation forbidden

---

### ✅ DO: Present Individual Amounts Only

**Example**:
```python
# ✅ CORRECT
for insurer, amount_dto in insurer_amounts:
    explanation = generate_explanation(insurer, amount_dto)
    # Each explanation is independent (no aggregation)
```

**Justification**: Parallel presentation, no calculation

---

### ❌ DON'T: Sort Results by Amount Value

**Example**:
```python
# ❌ WRONG
insurer_amounts = [
    ("삼성화재", "3천만원", 3000),
    ("메리츠화재", "2천만원", 2000),
    ("KB손해보험", "1천만원", 1000)
]

# Sort by numeric value (descending)
insurer_amounts.sort(key=lambda x: x[2], reverse=True)
```

**Violation**: Sorting by amount → ranking

---

### ✅ DO: Preserve Input Order or Use Canonical Order

**Example**:
```python
# ✅ CORRECT (Option 1: Preserve input order)
insurer_amounts = request.insurers  # User's order

# ✅ CORRECT (Option 2: Use canonical order if no input order)
insurer_amounts.sort(key=lambda x: x[0])  # Alphabetical by insurer name

# ❌ NEVER sort by amount value
```

**Justification**: Order is neutral (not value-based)

---

## 10. Validation & Testing

### ❌ DON'T: Skip Forbidden Language Validation

**Example**:
```python
# ❌ WRONG (bypasses validation)
explanation = build_explanation(insurer, amount)
return explanation  # No validation
```

**Violation**: Forbidden words may slip through

---

### ✅ DO: Validate All User-Facing Text

**Example**:
```python
# ✅ CORRECT
from apps.api.policy.forbidden_language import validate_text

explanation = build_explanation(insurer, amount)

# Enforce validation
validate_text(explanation)  # Raises ValueError if forbidden

return explanation
```

**Justification**: Single source of truth for language policy

**Reference**: `apps/api/policy/forbidden_language.py`

---

### ❌ DON'T: Assume Templates are Safe

**Example**:
```python
# ❌ WRONG (template may change, bypass validation)
template = "{insurer}가 {other_insurer}보다 유리합니다."  # FORBIDDEN
explanation = template.format(insurer="삼성", other_insurer="메리츠")
return explanation  # Not validated
```

**Violation**: Template itself contains forbidden word ("유리")

---

### ✅ DO: Lock Templates + Validate at Runtime

**Example**:
```python
# ✅ CORRECT (locked template + validation)
CONFIRMED_TEMPLATE = "{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."

explanation = CONFIRMED_TEMPLATE.format(...)
validate_text(explanation)  # Enforced

return explanation
```

**Justification**: Template is locked + runtime validation ensures safety

---

## 📚 Quick Reference: Forbidden Words Checklist

Use this checklist during code review / QA:

| Category | Forbidden Words | Allowed Alternatives |
|----------|-----------------|----------------------|
| **Comparative** | 더, 보다, 반면, 그러나 | (None - use parallel structure) |
| **Evaluative** | 유리, 불리, 높다, 낮다, 많다, 적다 | "명시되어 있습니다" (fact) |
| **Recommendation** | 추천, 권장, 제안, 선택 | "확인할 수 있습니다" |
| **Ranking** | 가장, 최고, 최저, 우수, 열등 | (None - no ranking) |
| **Calculation** | 평균, 합계, 총합, 차이 계산 | "개별 금액을 비교합니다" |
| **Judgment** | 판단, 결론, 좋다, 나쁘다 | "정보를 표시합니다" |
| **Contrast** | 반면, 그러나, 하지만 | (None - use parallel blocks) |

**Validation Function**: `apps/api/policy/forbidden_language.validate_text()`

**Full List**: See `apps/api/policy/forbidden_language.py`

---

## 🧪 Testing Checklist

Use this during QA testing:

### Visual Checks
- [ ] Table order is NOT sorted by amount value
- [ ] Color/styling is status-based (not value-based)
- [ ] No green/red for max/min
- [ ] No bold for "best value"
- [ ] No charts/graphs for comparison

### Content Checks
- [ ] Summary sentence contains no forbidden words
- [ ] Explanations are parallel (no cross-references)
- [ ] No "더", "보다", "반면" in explanations
- [ ] UNCONFIRMED shows "금액 명시 없음" (not "-" or "N/A")
- [ ] NOT_AVAILABLE shows "해당 담보 없음" (not hidden)
- [ ] Evidence is verbatim (not summarized)

### Interaction Checks
- [ ] Incomplete query → Clarification (not auto-selection)
- [ ] Missing data → Shown with status (not hidden)
- [ ] Blocked request → Alternative offered (not just "NO")
- [ ] Follow-up → Context retained (not guessed)

### Runtime Validation
- [ ] All response texts pass `forbidden_language.validate_text()`
- [ ] No calculation code executed
- [ ] Templates are locked (not LLM-generated)

---

## 📚 Related Documents

| Document | Purpose | Path |
|----------|---------|------|
| Chat UX Scenarios | Full scenario specifications (S1-S5) | `docs/ui/CHAT_UX_SCENARIOS.md` |
| Comparison Explanation Rules | Locked templates + forbidden words | `docs/ui/COMPARISON_EXPLANATION_RULES.md` |
| Amount Presentation Rules | CSS/HTML styling rules | `docs/ui/AMOUNT_PRESENTATION_RULES.md` |
| Forbidden Language Policy | Single source validation | `apps/api/policy/forbidden_language.py` |

---

## 🔐 Lock Policy

**This document is LOCKED as of STEP NEXT-15.**

Any violations of these patterns in production code are **rejected** via:
- Code review (manual)
- Runtime validation (`forbidden_language.py`)
- QA testing (checklist above)

**Enforcement Owner**: Product Team + Pipeline Team + QA Team

---

**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
