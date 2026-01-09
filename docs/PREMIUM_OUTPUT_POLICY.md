# Premium Output Policy (G10 Gate LOCK)

**Version:** 1.0
**Status:** 🔒 LOCKED
**Date:** 2026-01-09

---

## 0. Purpose

Define **absolute rules** for premium output in Q12 comparison, preventing estimation, interpolation, and non-SSOT premium values.

**Core Principle:**
> **"Premium = SSOT only. No LLM. No estimation. No averaging."**
>
> Premium 출력은 `product_premium_quote_v2` 테이블만 사용. LLM 추정/보간/평균 절대 금지.

---

## 1. Premium Slot Definition

### 1.1 Slot Identity

**Slot Key:** `premium_monthly`

**Scope:** Q12 비교 테이블 전용 (최상단/고정 row)

**Value Format:**
```json
{
  "amount": 157021,
  "plan_variant": "NO_REFUND",
  "currency": "KRW"
}
```

---

### 1.2 Source Classification

Premium은 "Evidence"가 아니라 **"SSOT Reference"**

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `source_kind` | `"PREMIUM_SSOT"` | ✅ | Fixed (not "DOC_EVIDENCE") |
| `premium_source` | Object | ✅ | G10 gate output |
| `premium_conditions` | Object | ✅ | Age, sex, plan_variant, etc. |
| `confidence` | Object | ✅ | Always HIGH (SSOT 확정값) |

---

## 2. G10 Premium SSOT Gate

### 2.1 Gate Rules (ZERO TOLERANCE)

**G10 checks:**
1. Premium values ONLY from `product_premium_quote_v2` table
2. NO LLM estimation/interpolation/averaging
3. Q12 output FAILS if `premium_monthly` is missing for ANY insurer
4. Premium output MUST include:
   - `premium_source`: `{table, as_of_date, baseDt, api_calSubSeq}`
   - `premium_conditions`: `{age, sex, smoke, pay_term_years, ins_term_years, plan_variant}`
   - `confidence`: Always `{"level": "HIGH", "basis": "Premium SSOT"}`

---

### 2.2 Failure Conditions

**G10 FAIL scenarios:**

| Scenario | Action | Reason |
|----------|--------|--------|
| DB 조회 결과 0건 | Q12 output FAIL | Premium SSOT 누락 |
| DB 조회 결과 2건 이상 | Q12 output FAIL | Ambiguous premium (다중 행) |
| `premium_monthly` NULL | Q12 output FAIL | Invalid SSOT value |
| `as_of_date` 누락 | Q12 output FAIL | Traceability 누락 |
| `plan_variant` 불일치 | Q12 output FAIL | Conditions mismatch |

**Violation → exit(2)** (hard fail, no fallback)

---

### 2.3 Implementation

**File:** `pipeline/step4_compare_model/gates.py`

**Class:** `PremiumSSOTGate`

**Methods:**
1. `fetch_premium(insurer_key, product_id, age, sex, plan_variant, ...)` → Premium data + validation
2. `validate_q12_premium_requirement(insurer_premium_results)` → ALL insurers check

---

## 3. Premium Row Injection (Q12)

### 3.1 Injection Logic

**Trigger:** `question_id == "Q12"`

**Process:**
1. Load CompareRow instances from Step4
2. Call `CompareBuilder.inject_premium_for_q12(rows, question_id="Q12", age=40, sex="M", plan_variant="NO_REFUND")`
3. For each insurer:
   - Fetch premium via `PremiumSSOTGate.fetch_premium()`
   - If G10 PASS: Inject `premium_monthly` slot into ALL rows for that insurer
   - If G10 FAIL: Log warning, mark Q12 as FAIL

---

### 3.2 Premium Slot Structure

```json
{
  "premium_monthly": {
    "status": "FOUND",
    "value": {
      "amount": 157021,
      "plan_variant": "NO_REFUND",
      "currency": "KRW"
    },
    "evidences": [],
    "notes": null,
    "confidence": {
      "level": "HIGH",
      "basis": "Premium SSOT (product_premium_quote_v2)"
    },
    "source_kind": "PREMIUM_SSOT"
  }
}
```

**Key Differences from DOC_EVIDENCE:**
- ✅ `source_kind`: `"PREMIUM_SSOT"` (not `"DOC_EVIDENCE"`)
- ✅ `evidences`: Empty list (no document excerpts)
- ✅ `confidence.basis`: References SSOT table, not document type

---

## 4. Q12 Output Policy

### 4.1 Hard Requirements

**Q12 비교 테이블 출력 시:**

1. **Premium row MUST exist** at row[0] (최상단 고정)
2. **ALL insurers MUST have premium** (하나라도 누락 → Q12 FAIL)
3. **Premium value format:**
   - Display: `₩157,021 (무해지)` or `₩xxx (일반)`
   - Plan variant 표시 필수
   - Currency symbol: `₩` (KRW)

---

### 4.2 Forbidden Actions

❌ **Absolutely FORBIDDEN:**

1. **LLM 추정/보간:**
   - ❌ "다른 연령대 보험료로부터 추정"
   - ❌ "평균값 계산"
   - ❌ "유사 상품 보험료 사용"

2. **다른 상품/플랜 대체:**
   - ❌ "일반형 보험료를 무해지형으로 사용"
   - ❌ "다른 product_id 값 가져오기"

3. **감정 표현 결합 (기존 G8 유지):**
   - ❌ "보험료가 매우 저렴함!" (과장)
   - ❌ "보험료 부담이 크지 않음" (추측)
   - ✅ "월 보험료: ₩157,021 (무해지, 40세/남/비흡연 기준)" (사실 진술)

---

## 5. Premium Conditions (Transparency)

### 5.1 Required Fields

Premium 출력 시 반드시 포함:

```json
"premium_conditions": {
  "age": 40,
  "sex": "M",
  "smoke": "NA",
  "plan_variant": "NO_REFUND",
  "pay_term_years": 20,
  "ins_term_years": 100
}
```

---

### 5.2 Source Traceability

Premium SSOT 참조 정보 포함:

```json
"premium_source": {
  "table": "product_premium_quote_v2",
  "as_of_date": "2025-12-15",
  "baseDt": "20251201",
  "api_calSubSeq": "001"
}
```

**Purpose:** Audit trail for premium calculation verification

---

## 6. Display Format (Customer-Facing)

### 6.1 Comparison Table Row

**Row ID:** `premium_monthly` (row[0], 최상단)

**Column Values (per insurer):**

| Insurer | Premium Display |
|---------|-----------------|
| KB | ₩157,021 (무해지) |
| Samsung | ₩162,500 (무해지) |
| Meritz | ❓ 정보 없음 |

**Missing Premium:**
- Display: `❓ 정보 없음`
- Q12 output: FAIL (전체 비교 차단)

---

### 6.2 Conditions Annotation

**Full Display (with conditions):**
```
월 보험료: ₩157,021 (무해지)
조건: 40세/남/비흡연, 20년납/100세만기
기준일: 2025-12-15
```

---

## 7. Integration with Routing Policy

### 7.1 Q12 Routing Rules (Updated)

**From:** `docs/QUESTION_ROUTING_POLICY.md`

**Q12 Special Rules (4번 추가):**
```markdown
4. **Premium requirement (STEP NEXT-R, G10 Gate):**
   - Q12 비교 테이블에 `premium_monthly` row 반드시 포함
   - Premium 출처: `product_premium_quote_v2` (SSOT only)
   - Premium 누락 시 Q12 고객용 출력 FAIL (hard block)
   - Premium 출력 조건: age, sex, plan_variant, as_of_date, baseDt 포함
```

---

### 7.2 G9 Gate Extension (G10 추가)

**G9 checks (updated):**
```python
# Existing G9 checks
if question_id not in ROUTING_REGISTRY:
    exit(2)

if card_type not in allowed_card_types:
    exit(2)

if why_count == 0 or why_not_count == 0:
    exit(2)

# STEP NEXT-R: G10 Premium Gate for Q12
if question_id == "Q12":
    if not all_insurers_have_premium():
        exit(2)  # G10 violation
```

---

## 8. Validation Criteria (DoD)

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| (D1) Premium row exists for Q12 | 100% | Check `premium_monthly` in slots |
| (D2) `source_kind == "PREMIUM_SSOT"` | 100% | No "DOC_EVIDENCE" allowed |
| (D3) G10 FAIL → Q12 output FAIL | 100% | Gate check (exit 2) |
| (D4) Conditions + source included | 100% | Schema validation |
| (D5) No LLM estimation | 0건 | Code review |

---

## 9. Error Messages

### 9.1 G10 FAIL (Missing Premium)

```
⚠️  G10 FAIL: Q12 requires premium for ALL insurers.
Missing: meritz

Reason: No premium data for meritz/meritz__메리츠 무배당 간편건강보험

Action: Q12 customer output BLOCKED.
```

---

### 9.2 G10 FAIL (Multiple Rows)

```
⚠️  G10 FAIL: Ambiguous premium data.

Query returned 2 rows for kb/kb__KB 무배당 간편건강보험
Expected: EXACTLY 1 row

Action: Q12 customer output BLOCKED.
```

---

### 9.3 G10 FAIL (Invalid Value)

```
⚠️  G10 FAIL: Invalid premium_monthly.

Value: NULL (expected: positive integer)
Insurer: samsung
Product: samsung__삼성 무배당 간편건강보험

Action: Q12 customer output BLOCKED.
```

---

## 10. Migration Path

### 10.1 Before STEP NEXT-R

**Q12 comparison table:**
- Premium row: ❌ 없음
- Premium 언급: 텍스트로만 언급 (비정형)
- Premium SSOT: ❌ 미연결

---

### 10.2 After STEP NEXT-R

**Q12 comparison table:**
- Premium row: ✅ `premium_monthly` (row[0])
- Premium source: ✅ `product_premium_quote_v2` (G10 gate)
- Premium conditions: ✅ 명시적 조건 표시
- G10 enforcement: ✅ 누락 시 Q12 FAIL

---

## 11. Future Extensions

### 11.1 Additional Premium Variants

**To support GENERAL plan variant:**
1. Add `plan_variant="GENERAL"` parameter to `inject_premium_for_q12()`
2. Query `product_premium_quote_v2` with `plan_variant='GENERAL'`
3. Apply same G10 gate rules (no changes)

---

### 11.2 Premium Comparison (Q14)

**Q14 (보험료 가성비 Top 4):**
- Same G10 gate
- Additional ranking logic (deterministic formula)
- Reference: `docs/QUESTION_ROUTING_POLICY.md` § 2.4

---

## 12. References

- **G10 Gate Implementation:** `pipeline/step4_compare_model/gates.py` (PremiumSSOTGate)
- **Premium Injection:** `pipeline/step4_compare_model/builder.py` (inject_premium_for_q12)
- **Schema:** `schema/020_premium_quote.sql`
- **Routing Policy:** `docs/QUESTION_ROUTING_POLICY.md`
- **Question Registry:** `data/policy/question_card_routing.json`

---

## 13. Declaration (LOCK)

**This policy is LOCKED for STEP NEXT-R.**

**Principles:**
1. ✅ Premium = SSOT only (no LLM, no estimation)
2. ✅ Q12 requires premium for ALL insurers (G10 hard gate)
3. ✅ Premium output includes conditions + source (transparency)
4. ✅ source_kind = "PREMIUM_SSOT" (not "DOC_EVIDENCE")
5. ✅ G10 FAIL → Q12 output FAIL (no fallback)

**Approval:**
- Engineering: ✅ Implemented (STEP NEXT-R)
- Product: ✅ Validated
- Compliance: ✅ Approved

---

**End of PREMIUM_OUTPUT_POLICY.md**
