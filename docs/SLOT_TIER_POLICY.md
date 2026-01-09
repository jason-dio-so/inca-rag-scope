# Slot Tier Policy (HARD LOCK)

**SSOT for Slot Classification and Output Policy**

Version: 1.0
Status: LOCKED
Last Updated: 2026-01-09

---

## Purpose

This document defines the **immutable slot tier classification** and **output policy** for the insurance comparison system.

**This is NOT about improving extraction.**
**This IS about defining responsibility boundaries.**

---

## Fundamental Principle

> **"모르는 것은 숨기고, 확실한 것만 보여준다"**

The system prioritizes **zero customer confusion** over **high coverage percentage**.

---

## Slot Tier Taxonomy

### Tier-A: Coverage-Anchored Slots

**Definition:** Slots that require precise coverage attribution.

**Slots:**
- `payout_limit` (지급 한도)
- `waiting_period` (대기 기간)
- `reduction` (감액 조건)
- `exclusions` (면책 조건)

**Output Conditions (ALL required):**
1. ✅ Step1 coverage anchor match
2. ✅ Step3 evidence exists
3. ✅ G5 Attribution Gate PASS

**Failure Handling:**
- Display: `❓ 정보 없음`
- Recommendation logic: ❌ EXCLUDED
- Comparison table: ❌ NO VALUE OUTPUT

---

### Tier-B: Product-Level Slots

**Definition:** Slots that apply to the entire product, not individual coverages.

**Slots:**
- `entry_age` (가입 연령)
- `start_date` (보장 개시일)
- `mandatory_dependency` (필수 가입 조건)

**Output Conditions:**
1. ✅ Step3 evidence exists
2. ✅ G5 relaxed rules allowed (product-level attribution)

**Display Rule:**
- Value output: ✅ ALLOWED
- Suffix required: **(상품 기준)**
- Example: `0-80세 (상품 기준)`

---

### Tier-C: Descriptive / Conditional Slots

**Definition:** Slots that provide context but cannot be reliably attributed or compared.

**Slots:**
- `underwriting_condition` (유병자 인수 조건)
- `payout_frequency` (지급 빈도)
- `industry_aggregate_limit` (업계 누적 한도)

**Output Policy:**
- Comparison table: ❌ EXCLUDED (column not shown)
- Explanation area: ✅ ALLOWED (sentence + evidence link)
- Recommendation logic: ❌ EXCLUDED (cannot be input for scoring)

**Rationale:**
- These slots are **condition-dependent** or **non-standardized**
- Cannot be reliably compared across products
- Useful for customer understanding, not for automated comparison

---

## Output Policy (HARD CONSTRAINTS)

### 1. Comparison Table Rules

**Tier-A Slots:**
- ✅ Show column
- ❌ If G5 FAIL → Display `❓ 정보 없음`

**Tier-B Slots:**
- ✅ Show column
- ✅ Value + `(상품 기준)` suffix

**Tier-C Slots:**
- ❌ **DO NOT SHOW COLUMN**
- Explanation area only

---

### 2. UNKNOWN Handling (ABSOLUTE)

**When to Display `❓ 정보 없음`:**
- Tier-A slot + G5 FAIL
- Tier-A slot + SEARCH_FAIL
- Tier-A slot + evidence exists but coverage anchor mismatch

**FORBIDDEN Phrases:**
- ❌ "값 정규화 실패"
- ❌ "근거 있음"
- ❌ "추출 실패"
- ❌ Raw numbers without attribution (e.g., `90, 1, 50`)

**Allowed Display:**
- ✅ `❓ 정보 없음`
- ✅ `데이터 없음`

---

### 3. Recommendation Logic Rules

**Tier-A:**
- ✅ ALLOWED as input (only if value is valid)

**Tier-B:**
- ⚠️ ALLOWED with caution (product-level only)

**Tier-C:**
- ❌ **FORBIDDEN**

**Enforcement:** G6 Gate (see below)

---

## Gate Rules

### G6: Slot Tier Enforcement Gate

**Purpose:** Prevent misuse of Tier-C slots and unattributed Tier-A values.

**Rules:**

1. **Tier-C in Comparison/Recommendation:**
   - IF Tier-C slot used as input to recommendation scoring
   - THEN `exit 2` (hard fail)

2. **Tier-A without Attribution:**
   - IF Tier-A slot has value AND G5 status != `PASS`
   - THEN `exit 2` (hard fail)

3. **Tier-A in Comparison Table:**
   - IF Tier-A slot displayed with numeric value AND G5 FAIL
   - THEN `exit 2` (hard fail)

**Location:**
- `pipeline/step4_compare_model/gates.py` (G6 function)
- Called by: `pipeline/step4_compare_model/builder.py`

---

## Slot-to-Tier Mapping (SSOT)

| Slot Name                  | Tier | Coverage-Anchored? | Product-Level? | Comparison? | Recommendation? |
|----------------------------|------|---------------------|----------------|-------------|------------------|
| `payout_limit`             | A    | ✅                  | ❌             | ✅          | ✅               |
| `waiting_period`           | A    | ✅                  | ❌             | ✅          | ✅               |
| `reduction`                | A    | ✅                  | ❌             | ✅          | ✅               |
| `exclusions`               | A    | ✅                  | ❌             | ✅          | ✅               |
| `entry_age`                | B    | ❌                  | ✅             | ✅          | ⚠️               |
| `start_date`               | B    | ❌                  | ✅             | ✅          | ⚠️               |
| `mandatory_dependency`     | B    | ❌                  | ✅             | ✅          | ⚠️               |
| `underwriting_condition`   | C    | ❌                  | ❌             | ❌          | ❌               |
| `payout_frequency`         | C    | ❌                  | ❌             | ❌          | ❌               |
| `industry_aggregate_limit` | C    | ❌                  | ❌             | ❌          | ❌               |

**Legend:**
- ✅ = ALLOWED
- ⚠️ = ALLOWED WITH RESTRICTIONS
- ❌ = FORBIDDEN

---

## Implementation Checklist

### Step 4: Compare Model Builder

**File:** `pipeline/step4_compare_model/builder.py`

**Changes:**
1. ✅ Filter Tier-C slots from comparison table columns
2. ✅ Apply `❓ 정보 없음` for Tier-A + G5 FAIL
3. ✅ Add `(상품 기준)` suffix for Tier-B values
4. ✅ Call G6 gate before output

### Step 5: Recommendation Model (Future)

**Changes:**
1. ✅ Accept only Tier-A slots as input
2. ✅ Reject Tier-C slots with exit 2

---

## Validation Criteria (DoD)

### Zero Tolerance Rules:

1. ❌ **Coverage-unattributed numeric values in output:** 0 occurrences
2. ❌ **Tier-C slots in recommendation input:** 0 occurrences
3. ✅ **"정보 없음" display consistency:** 100%
4. ✅ **Customer confusion scenarios:** 0 occurrences

### Audit Evidence:

- `docs/audit/STEP_NEXT_I_SLOT_TIER_LOCK.md`
  - Before/After comparison
  - Customer confusion scenario testing
  - G6 gate validation logs

---

## Rationale (Non-Negotiable)

### Why Tier-C Exists

**Reality:**
- Insurance proposals have **different structures** across insurers
- Step3 evidence is **descriptive context**, not coverage attribution guarantee
- Some slots are **conditionally accurate** (e.g., payout_frequency depends on diagnosis type)

**Goal:**
- NOT: "Extract everything with 100% FOUND rate"
- YES: "Show only what we can trust, hide everything else"

### Why Tier-B Has Suffix

**Problem:**
- `entry_age: 0-80세` could mean:
  - This specific coverage
  - The entire product

**Solution:**
- Always append `(상품 기준)` for Tier-B slots
- Customer knows it's not coverage-specific

---

## Future Expansion

### Adding New Slots

**Decision Tree:**

1. **Is coverage attribution guaranteed by Step1 anchor?**
   - YES → Consider Tier-A
   - NO → Go to 2

2. **Is this a product-level rule?**
   - YES → Consider Tier-B
   - NO → Go to 3

3. **Is this descriptive/conditional?**
   - YES → Tier-C

**Approval Required:**
- Any Tier-A addition requires G5 validation proof
- Any Tier-B addition requires product-level evidence confirmation

---

## Declaration (LOCK)

> **본 시스템은 "모르는 것은 숨기고, 확실한 것만 보여준다"를 최우선 원칙으로 한다.**

This policy is **LOCKED** and cannot be modified without explicit approval from:
- Product Owner
- Engineering Lead
- Audit Team

---

End of SLOT_TIER_POLICY.md
