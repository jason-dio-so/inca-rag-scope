# EX3_COMPARE Bubble Markdown Format Reference

**SSOT**: This document defines the canonical bubble_markdown format for EX3_COMPARE responses
**Version**: STEP NEXT-82
**Date**: 2026-01-02

---

## Format (LOCKED)

```markdown
## 핵심 요약
- 선택한 보험사: {insurer1}, {insurer2}
- 비교 대상 담보: {coverage_display_name}
- 기준 문서: 가입설계서

## 한눈에 보는 결론

- 보장금액: {공통/상이} ({details})
- 지급유형: {정액형/일당형/혼합 등}
- 주요 차이: {있음/없음} ({summary})

## 세부 비교 포인트

- {insurer1}: {feature1, feature2, feature3}
- {insurer2}: {feature1, feature2, feature3}

## 유의사항

- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

---

## Data Binding Rules

### Section 1: 핵심 요약

| Field | Data Source | Example |
|-------|-------------|---------|
| 선택한 보험사 | `insurers` parameter | "samsung, meritz" |
| 비교 대상 담보 | `display_coverage_name(coverage_name, coverage_code)` | "암진단비(유사암 제외)" |
| 기준 문서 | Static | "가입설계서" |

**Rules**:
- ❌ NEVER expose `coverage_code` (e.g., A4200_1)
- ✅ Use `display_coverage_name()` helper (auto-sanitizes)
- ✅ List insurers in order (comma-separated)

---

### Section 2: 한눈에 보는 결론

#### 보장금액

| Condition | Output Format | Example |
|-----------|---------------|---------|
| `amount1 == amount2` | `공통 ({amount})` | "공통 (3000만원)" |
| `amount1 != amount2` | `상이 ({insurer1} {amount1}, {insurer2} {amount2})` | "상이 (samsung 3000만원, meritz 5000만원)" |

**Data Source**: `comparison_data[insurer]["amount"]`

#### 지급유형

| Condition | Output Format | Example |
|-----------|---------------|---------|
| `payment1 == payment2` | `{payment_type}` | "정액형" |
| `payment1 != payment2` | `혼합 ({insurer1} {payment1}, {insurer2} {payment2})` | "혼합 (samsung 정액형, meritz 일당형)" |
| `payment == "UNKNOWN"` | `표현 없음` | "표현 없음" |

**Data Source**: `comparison_data[insurer]["payment_type"]` (or `kpi_summary.payment_type`)

**Rules**:
- ❌ NEVER display "UNKNOWN" to users
- ✅ Convert "UNKNOWN" → "표현 없음"

#### 주요 차이

| Condition | Output Format | Example |
|-----------|---------------|---------|
| Differences found | `있음 ({item1, item2} 차이 확인)` | "있음 (감액조건, 대기기간 차이 확인)" |
| No differences | `없음 (동일 조건)` | "없음 (동일 조건)" |

**Data Source**: `kpi_condition` comparison
- Check: `waiting_period`, `reduction_condition`, `exclusion_condition`
- Max 2 items shown (+ "등" if more)

**Rules**:
- ✅ Count differences across all condition fields
- ✅ Show max 2 items for brevity
- ✅ Append " 등" if 3+ differences

---

### Section 3: 세부 비교 포인트

**Format**: `- {insurer}: {feature1, feature2, feature3}`

**Features** (priority order, max 3):
1. `amount` (if not "명시 없음"): `보장금액 {amount}`
2. `payment_type` (if not "UNKNOWN"): `{payment_type}`
3. `limit_summary` (if exists): `{limit_summary}`

**Fallback**: If no features → `가입설계서 기준 보장`

**Example**:
```markdown
- samsung: 보장금액 3000만원, 정액형, 1회한 지급
- meritz: 보장금액 5000만원, 일당형, 연간 5회 한도
```

**Data Sources**:
- `comparison_data[insurer]["amount"]`
- `comparison_data[insurer]["payment_type"]`
- `comparison_data[insurer]["kpi_summary"]["limit_summary"]`

**Rules**:
- ✅ Show max 3 features per insurer
- ✅ Skip "명시 없음" and "UNKNOWN" values
- ✅ Use concise feature names (NO long sentences)

---

### Section 4: 유의사항

**Fixed content** (do not modify):
```markdown
- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Purpose**:
- Disclaimer for contract terms
- Direct users to table for detailed comparison

---

## Constitutional Rules (Hard Stop)

1. ❌ **NO coverage_code exposure**
   - Forbidden: "A4200_1", "A1234_0", etc.
   - Use: `display_coverage_name()` helper

2. ❌ **NO raw_text in bubble**
   - Forbidden: Direct quotes from DETAIL/EVIDENCE
   - Use: refs only (PD:/EV:)

3. ❌ **NO LLM usage**
   - Forbidden: Inference, summarization, generation
   - Use: Deterministic pattern matching only

4. ❌ **NO UNKNOWN display**
   - Forbidden: "UNKNOWN", "NULL", "None"
   - Use: "표현 없음", "명시 없음"

5. ✅ **4 sections MANDATORY**
   - Required: 핵심 요약, 한눈에 보는 결론, 세부 비교 포인트, 유의사항
   - Order: Fixed (do not reorder)

6. ✅ **Customer-facing language**
   - Use: Natural Korean, short sentences
   - Avoid: Technical jargon, internal codes

---

## Example Outputs

### Example 1: Same Amount, Different Conditions

**Input**:
```python
insurers = ["samsung", "meritz"]
coverage_name = "암진단비(유사암 제외)"
comparison_data = {
    "samsung": {
        "amount": "3000만원",
        "payment_type": "정액형",
        "kpi_summary": {"limit_summary": "1회한 지급"},
        "kpi_condition": {"waiting_period": "90일"}
    },
    "meritz": {
        "amount": "3000만원",
        "payment_type": "정액형",
        "kpi_summary": {"limit_summary": "1회한 지급"},
        "kpi_condition": {"waiting_period": "90일", "reduction_condition": "1년 50%"}
    }
}
```

**Output**:
```markdown
## 핵심 요약
- 선택한 보험사: samsung, meritz
- 비교 대상 담보: 암진단비(유사암 제외)
- 기준 문서: 가입설계서

## 한눈에 보는 결론

- 보장금액: 공통 (3000만원)
- 지급유형: 정액형
- 주요 차이: 있음 (감액조건 차이 확인)

## 세부 비교 포인트

- samsung: 보장금액 3000만원, 정액형, 1회한 지급
- meritz: 보장금액 3000만원, 정액형, 1회한 지급

## 유의사항

- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

---

### Example 2: Different Amount, Same Type

**Input**:
```python
insurers = ["hanwha", "kb"]
coverage_name = "골절진단비"
comparison_data = {
    "hanwha": {
        "amount": "100만원",
        "payment_type": "정액형",
        "kpi_summary": {"payment_type": "정액형"}
    },
    "kb": {
        "amount": "200만원",
        "payment_type": "정액형",
        "kpi_summary": {"payment_type": "정액형"}
    }
}
```

**Output**:
```markdown
## 핵심 요약
- 선택한 보험사: hanwha, kb
- 비교 대상 담보: 골절진단비
- 기준 문서: 가입설계서

## 한눈에 보는 결론

- 보장금액: 상이 (hanwha 100만원, kb 200만원)
- 지급유형: 정액형
- 주요 차이: 없음 (동일 조건)

## 세부 비교 포인트

- hanwha: 보장금액 100만원, 정액형
- kb: 보장금액 200만원, 정액형

## 유의사항

- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

---

### Example 3: Mixed Payment Types

**Input**:
```python
insurers = ["lotte", "heungkuk"]
coverage_name = "입원급여금"
comparison_data = {
    "lotte": {
        "amount": "1일당 5만원",
        "payment_type": "일당형",
        "kpi_summary": {"payment_type": "일당형", "limit_summary": "연간 120일 한도"}
    },
    "heungkuk": {
        "amount": "3000만원",
        "payment_type": "정액형",
        "kpi_summary": {"payment_type": "정액형", "limit_summary": "1회한 지급"}
    }
}
```

**Output**:
```markdown
## 핵심 요약
- 선택한 보험사: lotte, heungkuk
- 비교 대상 담보: 입원급여금
- 기준 문서: 가입설계서

## 한눈에 보는 결론

- 보장금액: 상이 (lotte 1일당 5만원, heungkuk 3000만원)
- 지급유형: 혼합 (lotte 일당형, heungkuk 정액형)
- 주요 차이: 없음 (동일 조건)

## 세부 비교 포인트

- lotte: 보장금액 1일당 5만원, 일당형, 연간 120일 한도
- heungkuk: 보장금액 3000만원, 정액형, 1회한 지급

## 유의사항

- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

---

## Implementation Reference

**Composer**: `apps/api/response_composers/ex3_compare_composer.py:360-501`
**Method**: `EX3CompareComposer._build_bubble_markdown()`
**Tests**: `tests/test_ex3_bubble_markdown_step_next_82.py`

---

**Version**: STEP NEXT-82
**Status**: SSOT LOCKED
**Last Updated**: 2026-01-02
