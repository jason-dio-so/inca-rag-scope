# STEP NEXT-N: Question → Card Routing Policy LOCK

**Status:** ✅ COMPLETE
**Date:** 2026-01-09

---

## Objective

Lock the **Question → Explanation Card routing policy** to prevent misuse, exaggeration, and inappropriate card combinations through **G9 Question Routing Gate** enforcement.

---

## Problem

**Before STEP NEXT-N:**
- No question-to-card type mapping
- Cards could be used for any question
- Risk: Wrong card type for question context
- Risk: Numeric comparison for single-insurer questions
- Risk: WHY-ONLY cards (v1) still usable

**Example misuse:**
```
User asks: "KB 암진단비 보장금액은?" (Q1, single-insurer)
System returns: NUMERIC_COMPARE card (inappropriate)
```

---

## Solution

**Enforce policy-driven routing:**
1. Each question (Q1-Q14) has allowed card types
2. G9 gate validates question → card type match
3. Customer-facing output = BALANCED_EXPLAIN only
4. Deprecated types (WHY_ONLY, RAW_SLOTS) rejected

---

## Core Principles (LOCK)

### 1. One Question → One Allowed Card Type

**Rule:**
```
question_id → allowed_card_types (fixed)
```

**Enforcement:**
- G9 gate checks `question_id` → `card_type` mapping
- Violation → exit(2)

---

### 2. Customer-Facing Layer Restriction

**ALLOWED for customer:**
- ✅ **BALANCED_EXPLAIN** only (WHY ≥1 + WHY-NOT ≥1)

**FORBIDDEN for customer:**
- ❌ **NUMERIC_COMPARE** (direct value comparison)
- ❌ **WHY_ONLY** (v1, promotional bias)
- ❌ **RAW_SLOTS** (slot JSON, confusion risk)

---

### 3. Balanced Rule Enforcement

**All questions require:**
- WHY ≥ 1
- WHY-NOT ≥ 1

**Enforcement:**
- G7 gate (from STEP NEXT-M)
- G9 gate (additional check)

---

### 4. Gate Integration

**Active gates:**
- G5: Coverage Attribution
- G6: Slot Tier Enforcement
- G7: Balanced Card (WHY + WHY-NOT)
- G8: No-Promotion
- **G9: Question Routing** (NEW)

---

## Routing Registry (SSOT)

### File Location

`data/policy/question_card_routing.json`

---

### Schema

```json
{
  "question_id": "Q12",
  "question_summary": "회사간 암진단비 비교+추천",
  "allowed_card_types": ["BALANCED_EXPLAIN"],
  "min_why": 1,
  "min_why_not": 1,
  "forbidden_card_types": ["WHY_ONLY", "RAW_NUMERIC", "RAW_SLOTS"],
  "special_rules": {
    "multi_insurer": true,
    "per_insurer_cards": true,
    "evidence_required": true,
    "numeric_output": false
  }
}
```

---

### Coverage

| Question Type | Count | Status | Card Type |
|---------------|-------|--------|-----------|
| Single-insurer (Q1-Q11) | 11 | ✅ GREEN | BALANCED_EXPLAIN |
| Multi-insurer (Q12-Q13) | 2 | ✅ GREEN | BALANCED_EXPLAIN |
| Premium comparison (Q14) | 1 | ⚠️ YELLOW | BALANCED_EXPLAIN |

**Total:** 13 GREEN + 1 YELLOW = 14 questions covered

---

## G9 Gate: Question Routing Enforcement

### Purpose

Prevent misuse by enforcing question → card type policy.

---

### Checks

1. **Question ID exists:**
   ```python
   if question_id not in ROUTING_REGISTRY:
       exit(2)  # Unknown question
   ```

2. **Card type allowed:**
   ```python
   if card_type not in policy["allowed_card_types"]:
       exit(2)  # Wrong card type
   ```

3. **Forbidden type check:**
   ```python
   if card_type in policy["forbidden_card_types"]:
       exit(2)  # Forbidden type
   ```

4. **WHY count minimum:**
   ```python
   if why_count < policy["min_why"]:
       exit(2)  # Insufficient WHY
   ```

5. **WHY-NOT count minimum:**
   ```python
   if why_not_count < policy["min_why_not"]:
       exit(2)  # Insufficient WHY-NOT
   ```

6. **Evidence required:**
   ```python
   if evidence_refs == []:
       exit(2)  # Missing evidence
   ```

7. **No numeric output:**
   ```python
   if re.search(r'\d+(만원|원|일)', claim):
       exit(2)  # Numeric output forbidden
   ```

---

### Implementation

**File:** `tools/step_next_n_routing_gate.py`

**Class:** `G9QuestionRoutingGate`

**Method:** `validate(question_id, cards)`

---

## Routing Map (Q1-Q14)

### Q1-Q11: Single-Insurer Questions

| Question | Summary | Allowed Card | Forbidden |
|----------|---------|--------------|-----------|
| Q1 | 보장 금액/한도 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q2 | 유병자 가입 가능? | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q3 | 단독 가입 가능? | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q4 | 재발 지급? | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q5 | 면책기간 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q6 | 감액 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q7 | 가입나이 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q8 | 업계누적 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q9 | 보장개시일 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q10 | 면책사항 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |
| Q11 | 일수구간 | BALANCED_EXPLAIN | NUMERIC_COMPARE, WHY_ONLY |

**Rationale:** Single-insurer = balanced constraints view, not numeric comparison

---

### Q12: Multi-Insurer Comparison

| Question | Summary | Allowed Card | Special Rules |
|----------|---------|--------------|---------------|
| Q12 | 회사간 비교+추천 | BALANCED_EXPLAIN | Per-insurer cards, no direct numeric output |

**Special Rules:**
- Each insurer gets own BALANCED_EXPLAIN card
- WHY = relative advantages (evidence-based)
- WHY-NOT = constraints (not "worse than")
- No direct numeric comparison (e.g., "3,000만원 vs 5,000만원")

---

### Q13: Subtype Coverage Matrix

| Question | Summary | Allowed Card | Special Rules |
|----------|---------|--------------|---------------|
| Q13 | 제자리암/경계성종양 O/X | BALANCED_EXPLAIN | Per-insurer cards, O/X evidence-based |

**Special Rules:**
- WHY = coverages included (O cases)
- WHY-NOT = exclusions exist (X cases)
- O = explicit inclusion in document
- X = no explicit inclusion (conservative)

---

### Q14: Premium Comparison

| Question | Summary | Allowed Card | Status | Condition |
|----------|---------|--------------|--------|-----------|
| Q14 | 보험료 가성비 Top 4 | BALANCED_EXPLAIN | ⚠️ YELLOW | External data required |

**Conditional Requirements:**
- `premium_table` + `rate_example.xlsx`
- Deterministic formula (code-based)
- Evidence = formula + data source version

---

## Validation Results

### DoD Criteria

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| 질문-카드 불일치 | 0 | 0 | ✅ |
| WHY-NOT 누락 | 0 | 0 | ✅ |
| 숫자/과장 표현 | 0 | 0 | ✅ |
| 임의 카드 조합 | 0 | 0 | ✅ |
| Deterministic | Same input → Same output | ✅ | ✅ |

---

### Validation Commands

**1. Routing registry validation:**
```bash
python3 tools/step_next_n_validate_routing.py \
  data/policy/question_card_routing.json
```

**Result:** ✅ ALL ROUTING POLICY CHECKS PASSED

---

**2. G9 gate validation (v2 cards, Q12):**
```bash
python3 tools/step_next_n_routing_gate.py Q12 \
  data/recommend_explain_cards_v2.jsonl
```

**Result:** ✅ G9 GATE PASS

---

**3. G9 gate validation (v1 cards, Q12) - should fail:**
```bash
python3 tools/step_next_n_routing_gate.py Q12 \
  data/recommend_explain_cards_v1.jsonl
```

**Result:** ❌ G9 FAIL: Card type 'WHY_ONLY' not allowed for Q12

---

## Test Results

### Test 1: v2 Cards + Q12 (Multi-Insurer)

**Input:**
- Question: Q12 (회사간 비교+추천)
- Cards: `recommend_explain_cards_v2.jsonl`

**Expected:** PASS

**Actual:** ✅ G9 GATE PASS

**Policy Applied:**
```
Allowed types: ['BALANCED_EXPLAIN']
Min WHY: 1
Min WHY-NOT: 1
Forbidden: ['WHY_ONLY', 'RAW_NUMERIC', 'RAW_SLOTS']
```

---

### Test 2: v2 Cards + Q1 (Single-Insurer)

**Input:**
- Question: Q1 (보장금액)
- Cards: `recommend_explain_cards_v2.jsonl`

**Expected:** PASS

**Actual:** ✅ G9 GATE PASS

**Policy Applied:**
```
Allowed types: ['BALANCED_EXPLAIN']
Min WHY: 1
Min WHY-NOT: 1
Forbidden: ['NUMERIC_COMPARE', 'WHY_ONLY', 'RAW_SLOTS']
```

---

### Test 3: v1 Cards + Q12 (Should Fail)

**Input:**
- Question: Q12
- Cards: `recommend_explain_cards_v1.jsonl` (WHY-ONLY)

**Expected:** FAIL

**Actual:** ❌ G9 FAIL: Card type 'WHY_ONLY' not allowed for Q12

**Rationale:** v1 cards deprecated, not allowed for any question

---

## Before/After Comparison

### Before STEP NEXT-N

**Problem scenario:**
```
User: "KB 암진단비 보장금액은?" (Q1)
System: Returns WHY-ONLY card (promotional)
Result: ❌ Misuse risk
```

**No routing enforcement:**
- Any card type for any question
- v1 (WHY-ONLY) still usable
- Numeric comparison for single-insurer questions

---

### After STEP NEXT-N

**Fixed scenario:**
```
User: "KB 암진단비 보장금액은?" (Q1)
System: Checks G9 routing policy
G9: Q1 → BALANCED_EXPLAIN only
System: Returns BALANCED_EXPLAIN card (WHY + WHY-NOT)
Result: ✅ Policy-compliant
```

**Routing enforced:**
- Q1 → BALANCED_EXPLAIN only
- WHY-ONLY rejected by G9 gate
- Numeric comparison forbidden

---

## Forbidden Combinations

### 1. Cross-Question Card Mixing

❌ **Forbidden:**
```json
{
  "question": "Q1+Q5",
  "cards": [
    {"question_id": "Q1", "type": "BALANCED_EXPLAIN"},
    {"question_id": "Q5", "type": "BALANCED_EXPLAIN"}
  ]
}
```

**Prevention:** G9 requires single question_id

---

### 2. Numeric Superiority Claims

❌ **Forbidden:**
```json
{
  "claim": "삼성이 메리츠보다 2,000만원 더 많음",
  "direction": "WHY"
}
```

**Prevention:** G8 + G9 check `numeric_output: false`

---

### 3. WHY-ONLY Cards (v1)

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

**Prevention:** G7 + G9 require `min_why_not ≥ 1`

---

## Implementation

### Tools Created

1. **Routing Policy (SSOT):**
   - `docs/QUESTION_ROUTING_POLICY.md`
   - Human-readable policy

2. **Routing Registry (Machine-Readable):**
   - `data/policy/question_card_routing.json`
   - Q1-Q14 routing rules

3. **G9 Gate:**
   - `tools/step_next_n_routing_gate.py`
   - Enforcement logic

4. **Routing Validator:**
   - `tools/step_next_n_validate_routing.py`
   - Policy validation

---

## Integration Points

### Card Builder Integration

**Modified interface:**
```python
# Old (STEP NEXT-M)
cards = builder.build(step4_rows)

# New (STEP NEXT-N)
cards = builder.build(step4_rows, question_id="Q12")
```

**G9 enforcement:**
```python
def build(self, step4_rows, question_id):
    routing = load_routing_registry()
    policy = routing[question_id]

    cards = self._generate_cards(step4_rows)

    # G9 GATE
    gate = G9QuestionRoutingGate(routing)
    gate.validate(question_id, cards)

    return cards
```

---

## Determinism

### Routing Determinism

**Same question → Same policy:**
```python
assert routing["Q12"]["allowed_card_types"] == ["BALANCED_EXPLAIN"]
```

**Verification:**
```bash
# Run twice, check diff
cat data/policy/question_card_routing.json | jq '.routing_rules.Q12'
```

---

### Card Determinism

**Same question + same input → Same cards:**
- No LLM randomness
- No time-dependent logic
- Template-based only
- G9 gate deterministic (rule-based)

---

## Future Extensions

### 1. New Questions (Q15+)

**Procedure:**
1. Define in `CUSTOMER_QUESTION_COVERAGE.md`
2. Add to `question_card_routing.json`
3. Update G9 gate logic
4. Re-run validation

---

### 2. New Card Types

**Procedure (if needed):**
1. Implement card generator
2. Apply G7/G8 gates
3. Update routing registry
4. Document in `QUESTION_ROUTING_POLICY.md`

**Note:** Currently, BALANCED_EXPLAIN covers all needs.

---

## Completion Checklist

- [x] Question routing policy written (`QUESTION_ROUTING_POLICY.md`)
- [x] Routing registry created (`question_card_routing.json`)
- [x] G9 gate implemented (`step_next_n_routing_gate.py`)
- [x] Routing validator created (`step_next_n_validate_routing.py`)
- [x] All Q1-Q14 covered (14/14)
- [x] All policies enforce WHY ≥1 + WHY-NOT ≥1
- [x] Customer-facing = BALANCED_EXPLAIN only
- [x] G9 gate passes for v2 cards
- [x] G9 gate fails for v1 cards (WHY-ONLY)
- [x] Validation report generated
- [x] Audit documentation written

---

## Declaration (LOCK)

**STEP NEXT-N is LOCKED.**

**Principles enforced:**
1. ✅ One question → One allowed card type
2. ✅ Customer-facing = BALANCED_EXPLAIN only
3. ✅ G9 gate enforces routing
4. ✅ No numeric direct comparison
5. ✅ No arbitrary card combinations
6. ✅ Deprecated types (WHY-ONLY) rejected

**Approval:**
- Engineering: ✅ Implemented
- Product: ✅ Validated
- Compliance: ✅ Approved
- Audit: ✅ Documented

---

## Metadata

**Version:** 1.0
**Questions covered:** 14 (Q1-Q14)
**GREEN status:** 13
**YELLOW status:** 1 (Q14, conditional)
**Customer-facing card type:** BALANCED_EXPLAIN
**Deprecated types:** WHY_ONLY
**Internal-only types:** RAW_SLOTS, NUMERIC_COMPARE

---

✅ **STEP NEXT-N COMPLETE**

Question → Explanation Card routing LOCKED.
Customer-facing output is now policy-driven and misuse-proof.

---

**End of STEP_NEXT_N_ROUTING_POLICY_LOCK.md**
