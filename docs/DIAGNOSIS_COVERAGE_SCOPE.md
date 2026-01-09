# Diagnosis Coverage Scope - Final Definition (LOCKED)

**Version:** v1.0
**Status:** LOCKED
**Date:** 2026-01-09

---

## 🔒 Absolute Declaration

**본 시스템에서 "진단비"로 인정되는 담보는**
**Diagnosis Coverage Registry에 등재된 `coverage_code`만을 의미한다.**

**Registry 미등재 담보는 진단비 비교·추천에서 절대 제외된다.**

---

## 📦 Current Diagnosis Coverage Scope

### ✅ Registered Diagnosis Benefits (비교·추천 가능)

| Coverage Code | Canonical Name | Diagnosis Type | Insurers | Status |
|---------------|----------------|----------------|----------|--------|
| A4200_1 | 암진단비(유사암제외) | cancer | Samsung, KB, Meritz | ✅ LOCKED |
| A4209 | 고액암진단비 | cancer_expensive | Samsung, KB | ✅ LOCKED |
| A4210 | 유사암진단비 | similar_cancer | Samsung, KB, Meritz | ✅ LOCKED |
| A4299_1 | 재진단암진단비 | cancer_rediagnosis | Samsung, KB | ✅ LOCKED |
| A4103 | 뇌졸중진단비 | stroke | Samsung, KB | ✅ LOCKED |
| A4105 | 허혈성심장질환진단비 | ischemic_heart_disease | Samsung, KB | ✅ LOCKED |

**Total:** 6 diagnosis benefits

---

## ❌ Explicitly Excluded

### Bundled Heart Disease Diagnosis (A4104_1)

**Coverage Code:** A4104_1
**Canonical Name:** 심장질환진단비
**Reason for Exclusion:**
- Bundled coverage (includes multiple heart diseases)
- Not single-disease diagnosis benefit
- Violates registry single-disease principle

**Examples of A4104_1 variants:**
- 심장질환(특정Ⅰ) 진단비
- 심장질환(특정Ⅱ) 진단비 (includes AMI + others)
- 특정3대심장질환 진단비
- 심근병증진단비
- 심장판막협착증진단비

**Status:** ❌ NOT REGISTERED (bundled coverage)

### Acute Myocardial Infarction (AMI) Diagnosis

**Expected Coverage:** 급성심근경색진단비
**Status:** ❌ DOES NOT EXIST as standalone product

**Finding (STEP NEXT-E):**
- No standalone AMI diagnosis benefit found in Samsung or KB
- AMI is included in bundled coverage A4104_1 only
- Bundled coverage does not meet registry criteria

**Impact:**
- AMI diagnosis cannot be compared/recommended
- AMI diagnosis questions receive explanation only (no numeric output)

---

## 🚦 Output Rules (ABSOLUTE)

### Rule 1: Registry-Based Comparison

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

### Rule 2: Explanation-Only for Unregistered

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

**Example output:**
```
급성심근경색진단비는 단독 진단비 상품이 없어
본 시스템의 진단비 비교 대상에 포함되지 않습니다.
```

### Rule 3: Gate Enforcement

**When user asks for diagnosis comparison:**

1. Load Diagnosis Coverage Registry
2. Filter coverage_codes by registry membership
3. If no registered codes → return explanation message
4. If mixed (registered + unregistered) → compare registered only, note unregistered

**Gate violation handling:**
- Exit with informative message
- Never output unregistered coverage values
- Never infer diagnosis_benefit from coverage name

---

## 📋 Customer Question Coverage

### Q2, Q9, Q12: Diagnosis Comparison Questions

**Common footer message:**

```
📌 진단비 비교 범위 안내

본 시스템에서 비교 가능한 진단비:
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

## 🔧 Registry Expansion Process

### How to Add New Diagnosis Benefit

**Required conditions (ALL must be met):**

1. **Single-disease diagnosis benefit**
   - One disease per coverage
   - No bundled coverages

2. **Diagnosis trigger only**
   - Payout on "진단 확정 시" only
   - No treatment/surgery/admission triggers

3. **Canonical name matches**
   - Coverage code exists in mapping Excel
   - Canonical name is diagnosis-specific

4. **Evidence validation**
   - Evidence excerpt confirms diagnosis trigger
   - No exclusion patterns (치료비, 수술비, 입원비, etc.)

5. **Multi-insurer availability**
   - At least 2 insurers offer the coverage
   - Ensures fair comparison

**Process:**
1. Identify coverage code candidates
2. Validate with Coverage Attribution Gate (G5)
3. Add to `diagnosis_coverage_registry.json`
4. Update `DIAGNOSIS_COVERAGE_REGISTRY.md`
5. Run `validate_diagnosis_registry.py` → MUST PASS
6. Update this document (DIAGNOSIS_COVERAGE_SCOPE.md)
7. Create audit document

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

## 📊 Current Status Summary

### Registered Coverage Types

| Type | Count | Examples |
|------|-------|----------|
| Cancer diagnosis | 4 | A4200_1, A4209, A4210, A4299_1 |
| Stroke diagnosis | 1 | A4103 |
| Ischemic heart disease | 1 | A4105 |
| **Total** | **6** | |

### Investigated but Not Registered

| Coverage | Reason | Status |
|----------|--------|--------|
| 급성심근경색진단비 | Does not exist as standalone | NOT FOUND |
| A4104_1 (심장질환진단비) | Bundled coverage | EXCLUDED |

### Unregistered but Comparable (Future)

| Coverage Type | Priority | Notes |
|---------------|----------|-------|
| 뇌출혈진단비 | Medium | Single-disease, exists in scope |
| 급성심근경색증진단비 | Low | Does not exist as standalone |
| 뇌혈관질환진단비 | Low | May be bundled, requires investigation |

---

## 🔒 Lock Declaration

**This document represents the final, absolute definition of diagnosis coverage scope.**

**No diagnosis benefit may be used in comparison, recommendation, or ranking**
**unless it is registered in the Diagnosis Coverage Registry.**

**Any violation of this principle is a HARD FAILURE.**

---

## 변경 이력

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-09 | v1.0 | Initial scope lock: 6 diagnosis benefits (cancer, stroke, ischemic heart disease) |

---

## References

- `data/registry/diagnosis_coverage_registry.json` - Machine-readable SSOT
- `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` - Human-readable registry documentation
- `docs/CUSTOMER_QUESTION_COVERAGE.md` - Customer question coverage mapping
- `docs/audit/STEP_NEXT_E_AMI_DIAGNOSIS_PILOT.md` - AMI investigation results
- `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` - Initial cancer diagnosis lock
