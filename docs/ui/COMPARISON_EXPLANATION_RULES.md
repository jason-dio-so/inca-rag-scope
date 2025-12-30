# Comparison Explanation Rules

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-12

---

## 🎯 Purpose

This document defines **immutable rules** for comparison explanation layer.

**CRITICAL**: This is a **FACT-FIRST, NON-RECOMMENDATION** layer.

- NO comparisons (better/worse)
- NO evaluations (유리/불리)
- NO calculations (합계/평균/차이)
- NO sorting by amount
- NO visual emphasis (색상/아이콘/그래프)

---

## 📋 Constitutional Rules (Absolute Prohibitions)

### ❌ FORBIDDEN Operations

| Category | Prohibited | Example |
|----------|-----------|---------|
| **Recommendation** | better/worse/유리/불리/적합 | ❌ "삼성이 더 유리합니다" |
| **Evaluation** | 높다/낮다/많다/적다 | ❌ "KB가 더 높습니다" |
| **Calculation** | 합계/평균/차이/비율 | ❌ "평균 5천만원" |
| **Sorting** | 금액 기준 정렬 | ❌ Amount-based ranking |
| **Visual Comparison** | 색상/아이콘/그래프 강조 | ❌ Green for max, red for min |
| **Inference** | Snippet 재검색/보정 | ❌ Re-extracting from snippets |
| **Status Violation** | UNCONFIRMED → CONFIRMED | ❌ Treating "금액 명시 없음" as fact |

### ❌ FORBIDDEN Words

These words **MUST NOT** appear in explanation sentences:

```
더, 보다, 반면, 그러나, 하지만
유리, 불리, 높다, 낮다, 많다, 적다
차이, 비교, 우수, 열등, 좋, 나쁜
가장, 최고, 최저, 평균, 합계
추천, 제안, 권장, 선택, 판단
```

**Enforcement**: `ExplanationDTO.explanation` field has validator to reject these patterns.

---

## 📊 Input Contract (From STEP NEXT-11)

### Input Source

Explanation layer receives **AmountDTO** from STEP NEXT-11:

```typescript
interface AmountDTO {
  status: "CONFIRMED" | "UNCONFIRMED" | "NOT_AVAILABLE";
  value_text: string | null;
  source_doc_type: string | null;
  evidence: AmountEvidenceDTO | null;
  notes: string[];
}
```

### Status Semantics (LOCKED)

| Status | Meaning | Source |
|--------|---------|--------|
| **CONFIRMED** | Amount explicitly stated in proposal | `amount_fact.value_text` |
| **UNCONFIRMED** | Coverage exists but amount not stated | Coverage exists, no amount |
| **NOT_AVAILABLE** | Coverage doesn't exist for insurer | No coverage_instance |

**CRITICAL**: Status semantics are **IMMUTABLE**. Do NOT reinterpret.

---

## 🔨 Output Schema (Explanation View Model)

### InsurerExplanationDTO

```typescript
interface InsurerExplanationDTO {
  insurer: string;          // e.g., "삼성화재"
  status: AmountStatus;     // CONFIRMED | UNCONFIRMED | NOT_AVAILABLE
  explanation: string;      // Rule-based sentence
  value_text: string | null; // For CONFIRMED only
}
```

### CoverageComparisonExplanationDTO

```typescript
interface CoverageComparisonExplanationDTO {
  coverage_code: string;           // e.g., "A4200_1"
  coverage_name: string;           // e.g., "암진단비"
  comparison_explanation: InsurerExplanationDTO[];  // Parallel explanations
  audit: AmountAuditDTO | null;
}
```

### ExplanationResponseDTO

```typescript
interface ExplanationResponseDTO {
  query_id: UUID;
  timestamp: DateTime;
  coverages: CoverageComparisonExplanationDTO[];
  audit: AmountAuditDTO | null;
}
```

---

## 📝 Explanation Templates (LOCKED)

### Template Registry

Explanation sentences are generated from **LOCKED templates** (NOT LLM):

```python
class ExplanationTemplateRegistry:
    # CONFIRMED
    CONFIRMED_TEMPLATE = "{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."

    # UNCONFIRMED
    UNCONFIRMED_TEMPLATE = "{insurer}의 {coverage_name}는 가입설계서에 금액이 명시되어 있지 않습니다."

    # NOT_AVAILABLE
    NOT_AVAILABLE_TEMPLATE = "{insurer}에는 해당 담보가 존재하지 않습니다."
```

**MODIFICATION POLICY**: Template changes require:
- Code review
- Test update
- Version lock update

---

## ✅ Valid Explanation Examples

### Example 1: CONFIRMED Status

**Input**:
```json
{
  "insurer": "삼성화재",
  "coverage_name": "암진단비",
  "amount_dto": {
    "status": "CONFIRMED",
    "value_text": "3천만원"
  }
}
```

**Output**:
```json
{
  "insurer": "삼성화재",
  "status": "CONFIRMED",
  "explanation": "삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.",
  "value_text": "3천만원"
}
```

✅ **Valid**: Uses template, shows value_text, no comparisons

---

### Example 2: UNCONFIRMED Status

**Input**:
```json
{
  "insurer": "KB손해보험",
  "coverage_name": "암진단비",
  "amount_dto": {
    "status": "UNCONFIRMED",
    "value_text": null
  }
}
```

**Output**:
```json
{
  "insurer": "KB손해보험",
  "status": "UNCONFIRMED",
  "explanation": "KB손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.",
  "value_text": null
}
```

✅ **Valid**: Fixed text, no value_text, fact-only

---

### Example 3: NOT_AVAILABLE Status

**Input**:
```json
{
  "insurer": "현대해상",
  "coverage_name": "특수담보X",
  "amount_dto": {
    "status": "NOT_AVAILABLE",
    "value_text": null
  }
}
```

**Output**:
```json
{
  "insurer": "현대해상",
  "status": "NOT_AVAILABLE",
  "explanation": "현대해상에는 해당 담보가 존재하지 않습니다.",
  "value_text": null
}
```

✅ **Valid**: Fixed text, no value_text

---

### Example 4: Multi-Insurer Comparison (Parallel)

**Input**:
```json
{
  "coverage_code": "A4200_1",
  "coverage_name": "암진단비",
  "insurer_amounts": [
    ("삼성화재", AmountDTO(status="CONFIRMED", value_text="3천만원")),
    ("KB손해보험", AmountDTO(status="UNCONFIRMED", value_text=null)),
    ("현대해상", AmountDTO(status="CONFIRMED", value_text="2천만원"))
  ]
}
```

**Output**:
```json
{
  "coverage_code": "A4200_1",
  "coverage_name": "암진단비",
  "comparison_explanation": [
    {
      "insurer": "삼성화재",
      "status": "CONFIRMED",
      "explanation": "삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.",
      "value_text": "3천만원"
    },
    {
      "insurer": "KB손해보험",
      "status": "UNCONFIRMED",
      "explanation": "KB손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.",
      "value_text": null
    },
    {
      "insurer": "현대해상",
      "status": "CONFIRMED",
      "explanation": "현대해상의 암진단비는 가입설계서에 2천만원으로 명시되어 있습니다.",
      "value_text": "2천만원"
    }
  ]
}
```

✅ **Valid**:
- Parallel explanations (NOT comparative)
- No "더 높습니다", "차이가 있습니다"
- Order preserved from input
- Each explanation is independent

---

## ❌ INVALID Examples (Contract Violations)

### ❌ INVALID: Comparative Language

```json
{
  "explanation": "삼성화재의 암진단비는 3천만원으로, KB손해보험보다 더 높습니다."
}
```

**Error**: FORBIDDEN word "더", cross-insurer comparison

---

### ❌ INVALID: Evaluation Language

```json
{
  "explanation": "삼성화재의 암진단비 3천만원은 유리한 조건입니다."
}
```

**Error**: FORBIDDEN word "유리한"

---

### ❌ INVALID: Calculation

```json
{
  "explanation": "암진단비 평균은 2천5백만원입니다."
}
```

**Error**: FORBIDDEN word "평균", calculation across insurers

---

### ❌ INVALID: CONFIRMED without value_text

```json
{
  "status": "CONFIRMED",
  "explanation": "삼성화재의 암진단비는 가입설계서에 명시되어 있습니다.",
  "value_text": null
}
```

**Error**: CONFIRMED requires actual value_text

---

### ❌ INVALID: UNCONFIRMED with value_text

```json
{
  "status": "UNCONFIRMED",
  "explanation": "KB손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.",
  "value_text": "3천만원"
}
```

**Error**: UNCONFIRMED should NOT have value_text

---

## 🔨 Implementation Rules

### Rule 1: Template-Based Generation ONLY

```python
# ✅ CORRECT
explanation = ExplanationTemplateRegistry.generate_explanation(
    insurer="삼성화재",
    coverage_name="암진단비",
    status="CONFIRMED",
    value_text="3천만원"
)

# ❌ WRONG (LLM-based)
explanation = llm.generate(
    f"Explain amount for {insurer} {coverage_name}"
)
```

---

### Rule 2: Status Determines Template

```python
# Status → Template mapping is LOCKED
if status == "CONFIRMED":
    template = CONFIRMED_TEMPLATE
elif status == "UNCONFIRMED":
    template = UNCONFIRMED_TEMPLATE
elif status == "NOT_AVAILABLE":
    template = NOT_AVAILABLE_TEMPLATE
```

**NO conditional logic** beyond status check.

---

### Rule 3: Parallel Explanations (NOT Comparative)

```python
# ✅ CORRECT (parallel, independent)
explanations = [
    builder.build_explanation(insurer1, amount1),
    builder.build_explanation(insurer2, amount2),
    builder.build_explanation(insurer3, amount3),
]

# ❌ WRONG (comparative)
if amount1 > amount2:
    explanation = f"{insurer1}이 {insurer2}보다 높습니다"
```

---

### Rule 4: Order Preservation

```python
# Input order MUST be preserved
insurer_amounts = [
    ("삼성화재", amount1),
    ("KB손해보험", amount2),
    ("현대해상", amount3)
]

# ❌ WRONG (sorting by amount)
insurer_amounts.sort(key=lambda x: x[1].value_text)

# ✅ CORRECT (preserve input order)
for insurer, amount in insurer_amounts:
    explanations.append(build_explanation(insurer, amount))
```

---

## 🎨 UI/Frontend Integration Rules

### Display Rules

| Element | Rule |
|---------|------|
| **Layout** | Independent blocks per insurer |
| **Order** | Input order preserved (NO sorting) |
| **Emphasis** | Status-based ONLY (see below) |
| **Recombination** | FORBIDDEN (display as-is) |
| **Abbreviation** | FORBIDDEN (full text only) |
| **Summarization** | FORBIDDEN (fact-first) |

---

### Status-Based Styling (Minimal)

| Status | Text Style | Color | Tooltip |
|--------|-----------|-------|---------|
| **CONFIRMED** | Normal | Inherit | "가입설계서에 명시된 금액입니다" |
| **UNCONFIRMED** | Italic | #666666 (gray) | "문서상 금액이 명시되지 않았습니다" |
| **NOT_AVAILABLE** | Strikethrough | #999999 (light gray) | "해당 보험사에 이 담보가 없습니다" |

**FORBIDDEN Styles**:
- ❌ Green/red for better/worse
- ❌ Bold for max/min
- ❌ Icons for ranking
- ❌ Charts/graphs for comparison

---

### UI Component Example (React)

```tsx
// ✅ CORRECT (fact-only display)
const ExplanationDisplay = ({ explanation }) => {
  const styleMap = {
    CONFIRMED: { fontStyle: 'normal', color: 'inherit' },
    UNCONFIRMED: { fontStyle: 'italic', color: '#666666' },
    NOT_AVAILABLE: { textDecoration: 'line-through', color: '#999999' }
  };

  return (
    <div style={styleMap[explanation.status]}>
      {explanation.explanation}
    </div>
  );
};

// ❌ WRONG (comparative emphasis)
const ExplanationDisplay = ({ explanations }) => {
  const maxAmount = Math.max(...explanations.map(e => parseAmount(e.value_text)));

  return explanations.map(e => (
    <div style={{ color: parseAmount(e.value_text) === maxAmount ? 'green' : 'black' }}>
      {e.explanation}
    </div>
  ));
};
```

---

## 🧪 Validation & Testing

### Validation Rules

```python
class ExplanationValidator:
    """
    Validates explanation output against contract
    """

    def validate_explanation(explanation: InsurerExplanationDTO) -> bool:
        # 1. Check forbidden words
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in explanation.explanation:
                raise ValueError(f"FORBIDDEN pattern: {pattern}")

        # 2. Validate status-specific rules
        if explanation.status == "CONFIRMED":
            if not explanation.value_text:
                raise ValueError("CONFIRMED requires value_text")

        if explanation.status in ["UNCONFIRMED", "NOT_AVAILABLE"]:
            if explanation.value_text:
                raise ValueError("UNCONFIRMED/NOT_AVAILABLE should not have value_text")

        # 3. Check for cross-insurer references
        # (simplified: other insurer names should not appear)

        return True
```

---

### Required Test Cases

1. **CONFIRMED → value_text 포함**
2. **UNCONFIRMED → "금액 명시 없음" 고정**
3. **NOT_AVAILABLE → "해당 담보 없음" 고정**
4. **Two CONFIRMED insurers → NO comparative words**
5. **Forbidden word validation → Reject**
6. **audit_run_id → Present**
7. **Order preservation → Input order maintained**
8. **Cross-insurer reference → Detected and rejected**

---

## 🔐 Contract Lock

**This contract is LOCKED as of STEP NEXT-12.**

Any changes to:
- Templates
- Status semantics
- Validation rules
- Forbidden words

Require **version bump** and **documentation update**.

**Enforcement**:
- Template changes → Code review required
- Forbidden words → Validator blocks at runtime
- Status changes → Contract violation (rejected)

---

## 📞 References

| Document | Purpose | Path |
|----------|---------|------|
| Amount Read Contract | Input DTO specification | `docs/api/AMOUNT_READ_CONTRACT.md` |
| Amount Presentation Rules | UI display guidelines | `docs/ui/AMOUNT_PRESENTATION_RULES.md` |
| Explanation DTO | Output schema | `apps/api/explanation_dto.py` |
| Explanation Handler | Implementation | `apps/api/explanation_handler.py` |

---

## 🎯 Completion Checklist

- ✅ Templates LOCKED (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)
- ✅ Forbidden words enforced
- ✅ Validation rules implemented
- ✅ UI integration rules documented
- ✅ Test cases specified
- ✅ Contract locked

---

**Lock Owner**: Pipeline Team + API Team
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
