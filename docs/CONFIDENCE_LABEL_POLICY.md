# Confidence Label Policy (HARD LOCK)

**SSOT for Confidence Level Assignment**

Version: 1.0
Status: LOCKED
Last Updated: 2026-01-09

---

## Purpose

Communicate **trust level** (not accuracy) of slot values to customers.

**Goal:**
- ❌ NOT: Increase value count
- ✅ YES: Show "how much to trust this value"

---

## Core Principles (HARD)

1. **If value exists → confidence must exist**
2. **If value is UNKNOWN → NO confidence label**
3. **Confidence is evidence-based only (no inference)**
4. **NO LLM, NO probability, NO scoring (rule-based only)**

---

## Confidence Level Taxonomy

### Level Definitions (SSOT)

| Level | Label | Definition | Basis |
|-------|-------|------------|-------|
| **HIGH** | 🟢 높음 | Coverage-specific mention in proposal or terms | 가입설계서 OR 약관 |
| **MEDIUM** | 🟡 보통 | Coverage-specific mention in summary/method docs | 상품요약서 OR 사업방법서 |
| **NONE** | (no label) | Value is UNKNOWN or Tier-C | N/A |

**FORBIDDEN Levels:**
- ❌ LOW / 낮음
- ❌ 추정 / estimated
- ❌ 가능성 / probable
- ❌ Percentage (90%, 0.8, etc.)

---

## Scope

### Applicable Slots (Tier-A ONLY)

**✅ Confidence labeling applies to:**
- `payout_limit`
- `waiting_period`
- `reduction`
- `exclusions`

**❌ NO confidence labeling for:**
- Tier-B slots (`entry_age`, `start_date`, `mandatory_dependency`)
- Tier-C slots (`underwriting_condition`, `payout_frequency`, `industry_aggregate_limit`)
- UNKNOWN values

**Rationale:**
- Tier-A: Coverage-anchored → confidence matters
- Tier-B: Product-level → already labeled with `(상품 기준)`
- Tier-C: Not shown in comparison → no label needed

---

## Assignment Rules (Rule-Based)

### Rule 1: Document Type Mapping

**Evidence Source Priority:**

| Document Type | Confidence Level | Reason |
|---------------|------------------|--------|
| 가입설계서 (Proposal) | HIGH | Coverage-specific, customer-facing |
| 약관 (Terms) | HIGH | Legal definition, coverage-specific |
| 상품요약서 (Summary) | MEDIUM | Product-level, may lack coverage detail |
| 사업방법서 (Method) | MEDIUM | Business rules, may be product-level |

**Implementation:**
```python
def get_confidence_level(doc_type: str) -> str:
    if doc_type in ["가입설계서", "약관"]:
        return "HIGH"
    elif doc_type in ["상품요약서", "사업방법서"]:
        return "MEDIUM"
    else:
        return None  # No confidence
```

---

### Rule 2: Multi-Evidence Handling

**When multiple evidences exist:**
- ✅ Take **highest** confidence level
- ❌ DO NOT average or combine

**Example:**
```json
{
  "evidences": [
    {"doc_type": "가입설계서", "excerpt": "..."},
    {"doc_type": "상품요약서", "excerpt": "..."}
  ]
}
```
**Result:** `HIGH` (가입설계서 has highest confidence)

**Rationale:**
- If proposal mentions it → coverage-specific confirmation exists
- Lower-confidence sources don't reduce trust

---

### Rule 3: UNKNOWN Handling

**If slot status is UNKNOWN:**
- ✅ `value: null`
- ✅ `confidence: null` (or omit field)
- ❌ DO NOT assign any confidence level

**Example:**
```json
{
  "payout_limit": {
    "status": "UNKNOWN",
    "value": null,
    "confidence": null
  }
}
```

**Customer View:** `❓ 정보 없음` (no confidence label)

---

### Rule 4: Tier-C Exclusion

**Tier-C slots are excluded from comparison:**
- ❌ NO confidence labeling needed
- Slots not shown → no trust level required

---

## Output Schema

### JSON Structure

```json
{
  "payout_limit": {
    "status": "FOUND",
    "value": "3000, 4200001, 100",
    "confidence": {
      "level": "HIGH",
      "basis": "가입설계서"
    },
    "evidences": [...]
  }
}
```

**Fields:**
- `level`: "HIGH" | "MEDIUM" | null
- `basis`: Document type that determined the level

---

### Customer-Facing Display

**HIGH Confidence:**
```
지급 한도: 3,000만원 (신뢰도: 높음)
근거: 가입설계서
```

**MEDIUM Confidence:**
```
대기 기간: 90일 (신뢰도: 보통)
근거: 상품요약서
```

**NO Confidence (UNKNOWN):**
```
지급 한도: ❓ 정보 없음
```

---

## Forbidden Practices (ZERO TOLERANCE)

### 1. NO Numerical Scoring

❌ **FORBIDDEN:**
```json
{
  "confidence": {
    "score": 0.85,
    "percentage": "85%"
  }
}
```

✅ **ALLOWED:**
```json
{
  "confidence": {
    "level": "HIGH"
  }
}
```

**Rationale:**
- Scores imply precision that doesn't exist
- Customers misinterpret numbers (85% = "almost certain"?)

---

### 2. NO Evidence Count Scoring

❌ **FORBIDDEN:**
```python
if len(evidences) >= 3:
    confidence = "HIGH"
elif len(evidences) >= 2:
    confidence = "MEDIUM"
```

✅ **ALLOWED:**
```python
confidence = max(get_confidence_level(ev.doc_type) for ev in evidences)
```

**Rationale:**
- More evidences ≠ higher confidence
- 3 product summaries < 1 coverage-specific proposal

---

### 3. NO Mixed-Document Upgrade

❌ **FORBIDDEN:**
```python
if "가입설계서" in sources and "약관" in sources:
    confidence = "VERY_HIGH"  # Invented level
```

✅ **ALLOWED:**
```python
confidence = "HIGH"  # Already highest level
```

**Rationale:**
- HIGH is the maximum
- Agreement doesn't increase trust beyond "coverage-specific"

---

### 4. NO UNKNOWN Confidence

❌ **FORBIDDEN:**
```json
{
  "payout_limit": {
    "status": "UNKNOWN",
    "value": null,
    "confidence": {
      "level": "LOW"
    }
  }
}
```

✅ **ALLOWED:**
```json
{
  "payout_limit": {
    "status": "UNKNOWN",
    "value": null,
    "confidence": null
  }
}
```

**Rationale:**
- No value = no trust level to assess
- "LOW confidence" implies value exists but is uncertain

---

## Integration with Existing Gates

### G5 Coverage Attribution Gate

**Relationship:**
- G5 validates **attribution** (correct coverage)
- Confidence labels **trust level** (document quality)

**Flow:**
1. G5 checks coverage attribution → PASS/FAIL
2. If PASS → Confidence labeler assigns level
3. If FAIL → UNKNOWN → No confidence

**Example:**
```
G5 PASS + 가입설계서 → HIGH confidence
G5 PASS + 상품요약서 → MEDIUM confidence
G5 FAIL → UNKNOWN → No confidence
```

---

### G6 Slot Tier Enforcement Gate

**Relationship:**
- G6 filters **which slots** to show
- Confidence labels **trust level** of shown values

**Flow:**
1. G6 filters Tier-C slots → Excluded
2. Tier-A/B slots → Confidence applied to Tier-A only
3. Tier-B gets `(상품 기준)` suffix (not confidence)

**Example:**
```
Tier-A (payout_limit) → Confidence: HIGH
Tier-B (entry_age) → Suffix: (상품 기준), NO confidence
Tier-C (underwriting_condition) → Excluded, NO confidence
```

---

## Customer Understanding Validation

### Scenario 1: HIGH Confidence Value

**Data:**
```json
{
  "payout_limit": {
    "value": "3000, 4200001, 100",
    "confidence": {
      "level": "HIGH",
      "basis": "가입설계서"
    }
  }
}
```

**Customer View:**
```
지급 한도: 3,000만원 (신뢰도: 높음)
```

**Customer Understanding:**
- ✅ "This value is from the proposal, I can trust it"
- ✅ "Not estimated or inferred"

---

### Scenario 2: MEDIUM Confidence Value

**Data:**
```json
{
  "waiting_period": {
    "value": "90, 3",
    "confidence": {
      "level": "MEDIUM",
      "basis": "상품요약서"
    }
  }
}
```

**Customer View:**
```
대기 기간: 90일 (신뢰도: 보통)
```

**Customer Understanding:**
- ✅ "This is from summary, might be product-level"
- ✅ "Should verify in detailed documents"

---

### Scenario 3: UNKNOWN (No Confidence)

**Data:**
```json
{
  "payout_limit": {
    "status": "UNKNOWN",
    "value": null,
    "confidence": null
  }
}
```

**Customer View:**
```
지급 한도: ❓ 정보 없음
```

**Customer Understanding:**
- ✅ "No data available"
- ✅ "No trust level because no value"

---

## Implementation Checklist

### Step 4: Compare Model Builder

**File:** `pipeline/step4_compare_model/gates.py`

**Add:**
1. `ConfidenceLabeler` class
2. `assign_confidence(evidences, slot_status)` method

**File:** `pipeline/step4_compare_model/builder.py`

**Modify:**
1. `_build_slots()` method
2. Add confidence field to `SlotValue` model

---

## Validation Criteria (DoD)

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Tier-A + FOUND 값 중 confidence 누락 | 0건 | `jq 'select(.slots.payout_limit.status == "FOUND" and .slots.payout_limit.confidence == null)'` |
| UNKNOWN 값에 confidence 표시 | 0건 | `jq 'select(.slots.payout_limit.status == "UNKNOWN" and .slots.payout_limit.confidence != null)'` |
| 고객 혼동 시나리오 | 0건 | Manual customer view testing |
| 기존 G5/G6 결과 변화 | 0건 | Compare before/after value counts |

---

## Example Output (Full)

```json
{
  "identity": {
    "insurer_key": "samsung",
    "coverage_code": "A4300_5",
    "coverage_title": "유사암 진단비"
  },
  "slots": {
    "payout_limit": {
      "status": "FOUND",
      "value": "600, 8200010, 100",
      "confidence": {
        "level": "HIGH",
        "basis": "가입설계서"
      },
      "evidences": [
        {
          "doc_type": "가입설계서",
          "page": 5,
          "excerpt": "유사암 진단비(기타피부암) 600만원"
        }
      ]
    },
    "waiting_period": {
      "status": "UNKNOWN",
      "value": null,
      "confidence": null
    },
    "entry_age": {
      "status": "FOUND_GLOBAL",
      "value": "30, 1 (상품 기준)"
    }
  }
}
```

**Customer View:**
```
유사암 진단비

지급 한도: 600만원 (신뢰도: 높음) 📋 근거 보기
대기 기간: ❓ 정보 없음
가입 연령: 30세~1세 (상품 기준)
```

---

## Rationale (Non-Negotiable)

### Why Only HIGH/MEDIUM (No LOW)?

**Problem:**
- "LOW confidence" implies "unreliable data"
- Customer thinks: "Why show me unreliable data?"

**Solution:**
- If confidence is LOW → Don't show value (make it UNKNOWN)
- Only show values we can defend (HIGH or MEDIUM)

---

### Why Document Type (Not Evidence Count)?

**Problem:**
- 5 product summaries ≠ more trustworthy than 1 proposal
- Count-based scoring is arbitrary

**Solution:**
- Document type reflects **specificity level**
- Proposal = coverage-specific = HIGH
- Summary = product-level = MEDIUM

---

### Why No Confidence for Tier-B?

**Problem:**
- `entry_age` is product-level (already labeled with `(상품 기준)`)
- Adding confidence is redundant

**Solution:**
- Tier-B suffix already communicates scope
- Confidence is for **coverage-specific values only** (Tier-A)

---

## Future Considerations

### 1. Evidence Transparency Link

**Enhancement:**
```
지급 한도: 600만원 (신뢰도: 높음)
📋 근거 보기 → 가입설계서 p.5 "유사암 진단비(기타피부암) 600만원"
```

**Status:** Future feature (not STEP NEXT-K scope)

---

### 2. Confidence-Based Filtering

**Use Case:**
- User preference: "Only show HIGH confidence values"
- Filter table to exclude MEDIUM confidence rows

**Status:** Future feature (requires UI integration)

---

### 3. Confidence Trend Reporting

**Use Case:**
- System health metric: % of HIGH confidence values over time
- Goal: Increase HIGH % by improving document structure

**Status:** Future analytics (not customer-facing)

---

## Declaration (LOCK)

**This policy is LOCKED and enforces:**

1. ✅ Confidence = trust level (not accuracy)
2. ✅ Rule-based only (no LLM, no scoring)
3. ✅ HIGH/MEDIUM only (no LOW or percentages)
4. ✅ Tier-A only (no Tier-B/C)
5. ✅ UNKNOWN = no confidence

**Approval:**
- Engineering: ✅ To be implemented
- Product: ✅ Validated
- Audit: ✅ Documented

---

End of CONFIDENCE_LABEL_POLICY.md
