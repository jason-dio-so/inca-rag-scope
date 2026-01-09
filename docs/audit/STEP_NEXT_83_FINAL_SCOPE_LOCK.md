# STEP NEXT-83: Diagnosis Coverage Scope Final LOCK

**Date:** 2026-01-09
**Status:** COMPLETED
**Purpose:** Finalize and lock the diagnosis coverage scope definition

---

## 🎯 Objective

Establish the **final, absolute definition** of diagnosis coverage scope for comparison, ranking, and recommendation.

**Goal:**
- End definition debates
- Lock implementation-ready scope
- Prevent future ambiguity

---

## 📋 Work Completed

### 1. Diagnosis Coverage Scope Declaration (HARD LOCK)

**Created:** `docs/DIAGNOSIS_COVERAGE_SCOPE.md`

**Content:**
- Registry-based definition (SSOT)
- Included coverage types (6 diagnosis benefits)
- Excluded coverage types (bundled, AMI, etc.)
- Output rules (ABSOLUTE)
- Registry expansion process

### 2. Included Diagnosis Benefits (Final List)

| Coverage Code | Canonical Name | Diagnosis Type | Insurers | Status |
|---------------|----------------|----------------|----------|--------|
| A4200_1 | 암진단비(유사암제외) | cancer | Samsung, KB, Meritz | ✅ LOCKED |
| A4209 | 고액암진단비 | cancer_expensive | Samsung, KB | ✅ LOCKED |
| A4210 | 유사암진단비 | similar_cancer | Samsung, KB, Meritz | ✅ LOCKED |
| A4299_1 | 재진단암진단비 | cancer_rediagnosis | Samsung, KB | ✅ LOCKED |
| A4103 | 뇌졸중진단비 | stroke | Samsung, KB | ✅ LOCKED |
| A4105 | 허혈성심장질환진단비 | ischemic_heart_disease | Samsung, KB | ✅ LOCKED |

**Total:** 6 diagnosis benefits

### 3. Explicitly Excluded Coverages

#### A4104_1 (심장질환진단비) - BUNDLED COVERAGE
- **Reason:** Bundled coverage (includes multiple heart diseases)
- **Variants:**
  - 심장질환(특정Ⅰ) 진단비
  - 심장질환(특정Ⅱ) 진단비 (includes AMI + others)
  - 특정3대심장질환 진단비
  - 심근병증진단비
  - 심장판막협착증진단비
- **Decision:** ❌ NOT REGISTERED (violates single-disease principle)

#### 급성심근경색진단비 - DOES NOT EXIST
- **Finding (STEP NEXT-E):** No standalone AMI diagnosis benefit found
- **Status:** ❌ DOES NOT EXIST as standalone product
- **Impact:** Cannot be compared/recommended

### 4. Output Rules (LOCKED)

#### Rule 1: Registry-Based Comparison ONLY

**For Q2, Q9, Q12 (diagnosis comparison/ranking):**

✅ **Allowed:**
- Coverage codes in Diagnosis Coverage Registry
- Numeric values (coverage amount, premium, limits)
- Ranking, comparison tables
- Recommendation scores

❌ **Forbidden:**
- Coverage codes NOT in registry
- Bundled coverages (A4104_1)
- Unregistered diagnosis benefits

**Enforcement:**
```python
if coverage_code not in DIAGNOSIS_REGISTRY:
    return {
        "status": "NOT_COMPARABLE",
        "message": "Registry 미등재 담보는 비교 불가"
    }
```

#### Rule 2: Explanation-Only for Unregistered

**For unregistered diagnosis coverages:**

✅ **Allowed:**
- Text description
- Coverage existence confirmation
- Referral to insurer documentation

❌ **Forbidden:**
- Numeric amounts
- Premium values
- Ranking
- Comparison with registered coverages
- Recommendation

### 5. Customer Question Coverage Update

**Updated:** `docs/CUSTOMER_QUESTION_COVERAGE.md`

**Added common footer for Q2, Q9, Q12:**

```
📌 본 시스템에서 비교 가능한 진단비:
- 암진단비 (유사암 제외)
- 고액암진단비
- 유사암진단비
- 재진단암진단비
- 뇌졸중진단비
- 허혈성심장질환진단비

급성심근경색은 단독 진단비 상품이 없어
본 시스템의 진단비 비교 대상에 포함되지 않습니다.
```

---

## ✅ Validation Results

### Registry Consistency Check

**Command:** `python3 tools/validate_diagnosis_registry.py`

**Results:**
```
✅ Format validation PASSED
✅ Exclusion Patterns PASSED (35 patterns checked)
✅ Enum validation PASSED
✅ Scope Coverage PASSED
  - Registered diagnosis benefits: 6
  - Unregistered coverage_codes: 28 (expected)
✅ FIX-2 Consistency PASSED
✅ ALL VALIDATIONS PASSED
```

**Key Findings:**
- 6 diagnosis benefits registered
- 28 unregistered codes (expected - treatment/admission/surgery)
- 0 inconsistencies between registry and output rules
- All Q12 coverage_codes are registered diagnosis_benefit

---

## 📦 Deliverables

1. ✅ `docs/DIAGNOSIS_COVERAGE_SCOPE.md` - Final scope definition (LOCKED)
2. ✅ `docs/CUSTOMER_QUESTION_COVERAGE.md` - Updated with AMI note
3. ✅ `docs/audit/STEP_NEXT_83_FINAL_SCOPE_LOCK.md` - This document
4. ✅ Registry validation PASS

---

## 🚫 Absolute Prohibitions

### Never Register These

❌ **Bundled coverages**
- Example: A4104_1 (심장질환진단비)
- Reason: Multiple diseases in one coverage

❌ **Treatment-trigger coverages**
- Example: 표적항암약물허가치료비
- Reason: Payout on treatment, not diagnosis

❌ **Surgery-trigger coverages**
- Example: 허혈성심장질환수술비
- Reason: Payout on surgery, not diagnosis

❌ **Admission-based coverages**
- Example: 암 입원일당
- Reason: Payout on admission, not diagnosis

❌ **String-inferred coverages**
- Never register based on coverage name alone
- Must have canonical code + evidence validation

---

## 🔒 Lock Declaration

**This document represents the final, absolute definition of diagnosis coverage scope.**

**No diagnosis benefit may be used in comparison, recommendation, or ranking**
**unless it is registered in the Diagnosis Coverage Registry.**

**Any violation of this principle is a HARD FAILURE.**

---

## 📊 Impact Summary

### Before STEP NEXT-83
- Diagnosis benefits: 6 (cancer, stroke, ischemic)
- Scope definition: Implicit, scattered
- AMI status: Unclear
- Output rules: Not enforced

### After STEP NEXT-83
- Diagnosis benefits: 6 (unchanged, now LOCKED)
- Scope definition: Explicit, centralized (DIAGNOSIS_COVERAGE_SCOPE.md)
- AMI status: ❌ Does not exist as standalone (documented)
- Output rules: Enforced by gate (registry-based ONLY)
- Customer questions: Updated with scope notice

---

## 🔙 Return State

**Returned to:** STEP NEXT-B (Diagnosis Coverage Registry SSOT Lock)

**Current Status:**
- Diagnosis Coverage Registry: LOCKED (6 benefits)
- Diagnosis Coverage Scope: LOCKED (definition complete)
- Output rules: LOCKED (registry-based enforcement)

**Next Steps:**
- STEP NEXT-F: Bundled Diagnosis Policy (if needed)
- Implementation: Use locked registry for comparison/recommendation

---

## 🔒 Final Declaration

**STEP NEXT-83 완료**
- Diagnosis coverage scope finalized and LOCKED
- 6 diagnosis benefits confirmed (cancer, stroke, ischemic heart disease)
- AMI standalone diagnosis: Does not exist (documented)
- Output rules enforced: Registry-based comparison ONLY
- Customer questions updated with scope notice
- Returned to STEP NEXT-B (SSOT state)

---

## References

- `docs/DIAGNOSIS_COVERAGE_SCOPE.md` - Final scope definition (NEW)
- `docs/CUSTOMER_QUESTION_COVERAGE.md` - Updated customer question coverage
- `data/registry/diagnosis_coverage_registry.json` - Machine-readable SSOT
- `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` - Human-readable registry
- `docs/audit/STEP_NEXT_E_AMI_DIAGNOSIS_PILOT.md` - AMI investigation results
- `docs/audit/STEP_NEXT_D_ISCHEMIC_PILOT.md` - Ischemic heart disease pilot
- `docs/audit/STEP_NEXT_C_STROKE_DIAGNOSIS_SSOT.md` - Stroke diagnosis pilot
- `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` - Initial cancer diagnosis lock
