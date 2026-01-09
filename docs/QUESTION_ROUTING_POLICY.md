# Question → Card Routing Policy (HARD LOCK)

**Version:** 1.0
**Status:** 🔒 LOCKED
**Date:** 2026-01-09

---

## 0. Purpose

Define **which explanation cards are allowed** for each customer question (Q1-Q14), preventing misuse, exaggeration, and inappropriate combinations.

**Core Principle:**
> **"One question → One allowed card type"**
>
> No arbitrary card combinations. No numeric direct comparison. Customer-facing output = Balanced Explanation Cards (v2, STEP NEXT-M) only.

---

## 1. Card Type Taxonomy

### 1.1 Available Card Types

| Card Type | File | Structure | Gates Applied | Status |
|-----------|------|-----------|---------------|--------|
| **BALANCED_EXPLAIN** | `recommend_explain_cards_v2.jsonl` | WHY ≥1 + WHY-NOT ≥1 | G5, G6, G7, G8 | ✅ Active |
| **NUMERIC_COMPARE** | (forbidden for customer-facing) | Direct value comparison | N/A | ❌ Forbidden |
| **WHY_ONLY** | `recommend_explain_cards_v1.jsonl` | WHY only, no WHY-NOT | G5, G6 | ❌ Deprecated (v1) |
| **RAW_SLOTS** | `compare_rows_v1.jsonl` | Direct slot values | G5 only | ❌ Internal only |

---

### 1.2 Customer-Facing Layer Rules

**ALLOWED for customer:**
- ✅ **BALANCED_EXPLAIN** only (v2, STEP NEXT-M)

**FORBIDDEN for customer:**
- ❌ NUMERIC_COMPARE (direct value comparison → misunderstanding risk)
- ❌ WHY_ONLY (v1, promotional bias)
- ❌ RAW_SLOTS (slot JSON → confusion risk)

---

## 2. Question Routing Map (Q1-Q14)

### 2.1 Single-Insurer Questions (Q1-Q11)

**Pattern:** "보험사 X의 담보 Y에서 슬롯 Z는?"

| Question | Allowed Card | Min WHY | Min WHY-NOT | Forbidden |
|----------|--------------|---------|-------------|-----------|
| Q1 (보장금액) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q2 (유병자) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q3 (단독가입) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q4 (재발지급) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q5 (면책기간) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q6 (감액) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q7 (가입나이) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q8 (업계누적) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q9 (보장개시일) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q10 (면책사항) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |
| Q11 (일수구간) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |

**Rationale:**
- Single-insurer questions present **one product's constraints**
- WHY + WHY-NOT provides balanced view (not promotional)
- No cross-insurer comparison → no numeric comparison needed

---

### 2.2 Multi-Insurer Comparison (Q12)

**Pattern:** "삼성 vs 메리츠 암진단비 비교 + 추천"

| Question | Allowed Card | Min WHY | Min WHY-NOT | Forbidden |
|----------|--------------|---------|-------------|-----------|
| Q12 (회사간 비교+추천) | BALANCED_EXPLAIN | 1 | 1 | WHY_ONLY, RAW_NUMERIC |

**Special Rules:**
1. **Per-insurer cards:**
   - Each insurer gets own BALANCED_EXPLAIN card
   - WHY: relative advantages
   - WHY-NOT: constraints (not "worse than")

2. **No direct numeric output:**
   - ❌ Forbidden: "삼성 3,000만원 vs 메리츠 5,000만원"
   - ✅ Allowed: "지급 한도가 상대적으로 유리함" + evidence

3. **Recommendation logic:**
   - Use STEP NEXT-74/75 Rule Catalog
   - No free-text judgment
   - Evidence-based only

4. **Premium requirement (STEP NEXT-R, G10 Gate):**
   - Q12 비교 테이블에 `premium_monthly` row 반드시 포함
   - Premium 출처: `product_premium_quote_v2` (SSOT only)
   - Premium 누락 시 Q12 고객용 출력 FAIL (hard block)
   - Premium 출력 조건: age, sex, plan_variant, as_of_date, baseDt 포함

---

### 2.3 Subtype Coverage Matrix (Q13)

**Pattern:** "제자리암/경계성종양 O/X 비교"

| Question | Allowed Card | Min WHY | Min WHY-NOT | Forbidden |
|----------|--------------|---------|-------------|-----------|
| Q13 (Subtype O/X) | BALANCED_EXPLAIN | 1 | 1 | NUMERIC_COMPARE |

**Special Rules:**
1. **O/X display:**
   - Show evidence for both O and X
   - WHY: coverages included (O cases)
   - WHY-NOT: exclusions exist (X cases)

2. **No inference:**
   - O = explicit inclusion in document
   - X = no explicit inclusion (conservative)

---

### 2.4 Premium Comparison (Q14)

**Pattern:** "보험료 가성비 Top 4"

| Question | Allowed Card | Min WHY | Min WHY-NOT | Status |
|----------|--------------|---------|-------------|--------|
| Q14 (보험료 가성비) | BALANCED_EXPLAIN | 1 | 1 | ⚠️ Conditional |

**Conditional Requirements:**
1. External data:
   - `premium_table` (월납/총납)
   - `rate_example.xlsx` (일반/무해지 비율)

2. Calculation formula:
   - Deterministic (code-based, no manual adjustment)
   - Evidence = formula + data source version

3. Card structure:
   - WHY: "보험료 부담이 상대적으로 낮음"
   - WHY-NOT: "특정 조건에서는 할증 가능"

---

## 3. Forbidden Combinations

### 3.1 Cross-Question Card Mixing

❌ **Forbidden:**
```json
{
  "question": "Q1+Q5",
  "cards": [
    {"type": "BALANCED_EXPLAIN", "question_id": "Q1"},
    {"type": "BALANCED_EXPLAIN", "question_id": "Q5"}
  ]
}
```

✅ **Allowed:**
```json
{
  "question": "Q1",
  "cards": [
    {"type": "BALANCED_EXPLAIN", "question_id": "Q1"}
  ]
}
```

**Rationale:** Mixing questions = context confusion

---

### 3.2 Numeric Superiority Claims

❌ **Forbidden:**
```json
{
  "claim": "삼성이 메리츠보다 2,000만원 더 많음",
  "direction": "WHY"
}
```

✅ **Allowed:**
```json
{
  "claim": "지급 한도가 상대적으로 유리함",
  "direction": "WHY",
  "evidence_refs": ["가입설계서:p4"]
}
```

---

### 3.3 WHY-ONLY Cards (v1 deprecated)

❌ **Forbidden:**
```json
{
  "bullets": [
    {"direction": "WHY", "claim": "..."},
    {"direction": "WHY", "claim": "..."},
    {"direction": "WHY", "claim": "..."}
  ]
}
```

✅ **Required:**
```json
{
  "bullets": [
    {"direction": "WHY", "claim": "..."},
    {"direction": "WHY", "claim": "..."},
    {"direction": "WHY_NOT", "claim": "..."}
  ]
}
```

---

## 4. G9 Gate: Question Routing Enforcement

### 4.1 Gate Rules

**G9 checks:**
1. Question ID must be provided
2. Card type must match allowed type for question
3. WHY ≥ 1 AND WHY-NOT ≥ 1 (for all questions)
4. No forbidden card types in output
5. **Q12: Premium requirement (G10 gate)**

**Failure condition:**
```python
if question_id not in ROUTING_REGISTRY:
    exit(2)  # Unknown question

if card_type not in ROUTING_REGISTRY[question_id]["allowed"]:
    exit(2)  # Wrong card type

if why_count == 0 or why_not_count == 0:
    exit(2)  # Unbalanced (G7 violation)

# STEP NEXT-R: G10 Premium Gate for Q12
if question_id == "Q12":
    if not all_insurers_have_premium():
        exit(2)  # G10 violation (Premium SSOT missing)
```

---

### 4.2 Implementation

**File:** `pipeline/step5_recommendation/gates.py`

**Function:** `validate_g9_question_routing(question_id, card_type, bullets)`

**Returns:** `None` if pass, raises `GateViolationError` if fail

---

## 5. Routing Registry (Machine-Readable)

### 5.1 Schema

```json
{
  "question_id": "Q12",
  "question_summary": "회사간 암진단비 비교+추천",
  "allowed_card_types": ["BALANCED_EXPLAIN"],
  "min_why": 1,
  "min_why_not": 1,
  "forbidden_card_types": ["WHY_ONLY", "NUMERIC_COMPARE", "RAW_SLOTS"],
  "special_rules": {
    "per_insurer_cards": true,
    "evidence_required": true,
    "numeric_output": false
  }
}
```

---

### 5.2 File Location

`data/policy/question_card_routing.json`

---

## 6. Integration with Card Builder

### 6.1 Modified Builder Interface

**Old (STEP NEXT-M):**
```python
builder.build(step4_rows)
```

**New (STEP NEXT-N):**
```python
builder.build(step4_rows, question_id="Q12")
```

---

### 6.2 Builder Logic

```python
def build(self, step4_rows, question_id):
    # G9 GATE: Load routing policy
    routing = load_routing_registry()

    if question_id not in routing:
        raise ValueError(f"Unknown question: {question_id}")

    policy = routing[question_id]

    # Generate cards
    cards = self._generate_cards(step4_rows)

    # G9 GATE: Validate
    for card in cards:
        if not self._validate_g9(card, policy):
            raise GateViolationError("G9: Routing violation")

    return cards
```

---

## 7. Validation Criteria (DoD)

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| 질문-카드 불일치 | 0건 | G9 gate check |
| WHY-NOT 누락 | 0건 | G7 gate check (min_why_not ≥ 1) |
| 숫자/과장 표현 | 0건 | G8 gate check |
| 임의 카드 조합 | 0건 | G9 gate check (allowed_card_types) |
| Deterministic | Same input → Same output | Hash validation |

---

## 8. Examples

### 8.1 Q1 (Single-Insurer, Single Slot)

**Question:** "KB 암진단비의 보장금액은?"

**Allowed Card:**
```json
{
  "question_id": "Q1",
  "insurer_key": "kb",
  "bullets": [
    {
      "direction": "WHY",
      "claim": "지급 한도가 상대적으로 유리함",
      "evidence_refs": ["가입설계서:p4"],
      "confidence": "HIGH"
    },
    {
      "direction": "WHY_NOT",
      "claim": "지급 조건에 제약이 명시됨",
      "evidence_refs": ["약관:p38"],
      "confidence": "HIGH"
    }
  ]
}
```

---

### 8.2 Q12 (Multi-Insurer Comparison)

**Question:** "삼성 vs 메리츠 암진단비 비교 + 추천"

**Allowed Cards (per insurer):**

**Samsung:**
```json
{
  "question_id": "Q12",
  "insurer_key": "samsung",
  "bullets": [
    {
      "direction": "WHY",
      "claim": "지급 제외 범위가 좁음",
      "evidence_refs": ["가입설계서:p4"],
      "confidence": "HIGH"
    },
    {
      "direction": "WHY_NOT",
      "claim": "초기 보장에 제한 조건이 존재함",
      "evidence_refs": ["약관:p20"],
      "confidence": "HIGH"
    }
  ]
}
```

**Meritz:**
```json
{
  "question_id": "Q12",
  "insurer_key": "meritz",
  "bullets": [
    {
      "direction": "WHY",
      "claim": "지급 한도가 상대적으로 유리함",
      "evidence_refs": ["가입설계서:p5"],
      "confidence": "HIGH"
    },
    {
      "direction": "WHY_NOT",
      "claim": "특정 기간 내 지급 제한 조건이 존재함",
      "evidence_refs": ["약관:p45"],
      "confidence": "HIGH"
    }
  ]
}
```

**Forbidden:**
```json
{
  "comparison": {
    "samsung_payout": "3,000만원",
    "meritz_payout": "5,000만원",
    "winner": "meritz"
  }
}
```

---

### 8.3 Q13 (Subtype O/X)

**Question:** "제자리암 진단비 보장 여부 비교"

**Allowed Card (per insurer):**
```json
{
  "question_id": "Q13",
  "insurer_key": "kb",
  "bullets": [
    {
      "direction": "WHY",
      "claim": "제자리암 진단비 보장이 포함됨",
      "evidence_refs": ["가입설계서:p3"],
      "confidence": "HIGH"
    },
    {
      "direction": "WHY_NOT",
      "claim": "일부 암 유형은 보장에서 제외됨",
      "evidence_refs": ["약관:p66"],
      "confidence": "HIGH"
    }
  ]
}
```

---

## 9. Migration Path (v1 → v2 + N)

### 9.1 Before (STEP NEXT-L, v1)

- WHY-ONLY cards allowed
- No question routing
- Promotional bias risk

---

### 9.2 After STEP NEXT-M (v2)

- BALANCED cards enforced (G7)
- Still no question routing

---

### 9.3 After STEP NEXT-N (v2 + routing)

- BALANCED cards enforced (G7)
- Question routing enforced (G9)
- Misuse prevented

---

## 10. Forbidden Scenarios

### 10.1 Cross-Question Mixing

❌ **User asks Q1, system returns Q5 card**

**Prevention:** G9 gate checks `question_id` match

---

### 10.2 Numeric Comparison for Single-Insurer

❌ **User asks Q1 (single-insurer), system shows numeric comparison**

**Prevention:** `allowed_card_types` excludes `NUMERIC_COMPARE`

---

### 10.3 WHY-ONLY Card After M-Step

❌ **System generates v1 card after STEP NEXT-M**

**Prevention:** Builder only generates v2 (BALANCED_EXPLAIN)

---

## 11. Determinism

### 11.1 Routing Determinism

**Same question + same input → same card type**

```python
assert routing["Q12"]["allowed_card_types"] == ["BALANCED_EXPLAIN"]
```

---

### 11.2 Card Determinism

**Same question + same step4_rows → same bullets**

- No LLM randomness
- No time-dependent logic
- Template-based only

---

## 12. Future Extensions

### 12.1 New Questions

**To add Q15:**
1. Define in `CUSTOMER_QUESTION_COVERAGE.md`
2. Add to `question_card_routing.json`
3. Update G9 gate logic
4. Re-run validation

---

### 12.2 New Card Types

**To add new card type (e.g., EVIDENCE_LINK):**
1. Implement card generator
2. Apply G7/G8 gates
3. Update routing registry
4. Document in this policy

---

## 13. Declaration (LOCK)

**This policy is LOCKED for STEP NEXT-N.**

**Principles:**
1. ✅ One question → One allowed card type
2. ✅ Customer-facing = BALANCED_EXPLAIN only
3. ✅ G9 gate enforces routing
4. ✅ No numeric direct comparison
5. ✅ No arbitrary card combinations

**Approval:**
- Engineering: ✅ To be implemented
- Product: ✅ Validated
- Compliance: ✅ Approved

---

## 14. References

- `docs/CUSTOMER_QUESTION_COVERAGE.md`: Q1-Q14 definitions
- `docs/SLOT_TIER_POLICY.md`: Tier-A/B/C rules
- `docs/CONFIDENCE_LABEL_POLICY.md`: Confidence levels
- `docs/audit/STEP_NEXT_M_BALANCED_CARD_LOCK.md`: Balanced card spec

---

**End of QUESTION_ROUTING_POLICY.md**
