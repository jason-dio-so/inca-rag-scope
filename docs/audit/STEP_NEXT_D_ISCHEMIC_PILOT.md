# STEP NEXT-D: Ischemic Heart Disease Diagnosis Coverage SSOT Pilot

**Date:** 2026-01-09
**Status:** COMPLETED
**Scope:** Samsung + KB ischemic heart disease diagnosis coverage ONLY

---

## 🎯 Objective

Extend the Diagnosis Coverage Registry to include **허혈성심장질환 '진단비'** (ischemic heart disease diagnosis benefit) following the same structure established for cancer and stroke diagnosis.

**Goal:** Prevent contamination by:
- ❌ Excluding treatment/surgery/admission/outpatient coverages
- ❌ Preventing definition-based confusion
- ❌ Eliminating inter-company comparison errors

---

## 📦 Scope (HARD LOCK)

- **Insurers:** Samsung, KB ONLY
- **Coverage Type:** 허혈성심장질환 '진단비' ONLY
- **Focus:** diagnosis_benefit identification and registry lock

---

## 🔍 Identification Process

### Input Data (SSOT)
- Step2-b Canonical Mapping output
- Existing Diagnosis Coverage Registry (v1.0)
- Coverage mapping Excel: `data/sources/mapping/담보명mapping자료.xlsx`

### Ischemic Heart Disease Diagnosis Coverage Candidates

**Coverage Code:** A4105
**Canonical Name:** 허혈성심장질환진단비

**Identified Instances:**
- Samsung: "허혈성심장질환 진단비(1년50%)" → A4105
- KB: "101. 허혈성심장질환진단비" → A4105

### Inclusion Criteria (ALL must be met)
- ✅ Coverage name contains "허혈성심장질환" or "허혈심장질환"
- ✅ Coverage name contains "진단"
- ✅ Payout trigger is "진단확정 시" (diagnosis confirmation)
- ✅ Evidence excerpt confirms diagnosis-based payout

### Immediate Exclusion Criteria (ANY fails)
- ❌ 수술비 (surgery)
- ❌ 치료비 (treatment)
- ❌ 입원일당 (daily hospitalization)
- ❌ 통원비 (outpatient)
- ❌ 관상동맥우회술 (CABG)
- ❌ 혈관성형술 (angioplasty)
- ❌ 스텐트 (stent)
- ❌ 시술 (procedures)

---

## 📋 Registry Extension

### Added Entry: A4105

```json
{
  "coverage_code": "A4105",
  "canonical_name": "허혈성심장질환진단비",
  "coverage_kind": "diagnosis_benefit",
  "diagnosis_type": "ischemic_heart_disease",
  "trigger": "진단 확정 시 지급",
  "included_subtypes": ["ischemic_heart_disease"],
  "excluded_subtypes": [],
  "usable_for_questions": ["Q1", "Q2", "Q3", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q13", "Q14"],
  "usable_for_comparison": true,
  "usable_for_recommendation": true,
  "exclusion_keywords": [
    "수술비",
    "입원일당",
    "치료비",
    "통원비",
    "관상동맥우회술",
    "혈관성형술",
    "스텐트",
    "시술"
  ],
  "insurers": ["samsung", "kb"],
  "notes": "허혈성심장질환으로 진단확정 시 지급되는 정액 진단비만 허용",
  "lock_version": "v1.0"
}
```

---

## ✅ Validation Results

### Evidence Verification

**Samsung A4105:**
- Coverage name: "허혈성심장질환 진단비(1년50%)"
- Evidence excerpt: "허혈성심장질환 진단비(1년50%)," + "진단 확정된 경우"
- ✅ Diagnosis trigger confirmed
- ✅ No exclusion patterns found

**KB A4105:**
- Coverage name: "101. 허혈성심장질환진단비"
- Evidence excerpt: "보험기간 중 허혈성심장질환(약관참조)으로 진단확정된 경우 (최초1회한, 계약일로부터 1년미만시 보험가입금액의 50%지급)"
- ✅ Diagnosis trigger confirmed: "진단확정"
- ✅ No exclusion patterns found

### Coverage Attribution Gate (G5) Verification

**Allowed Payout Conditions (ALL must be met):**
- ✅ Evidence excerpt contains "허혈성심장질환으로 진단확정" or equivalent
- ✅ No excluded_patterns match

**Violation Handling:**
```json
{
  "status": "UNKNOWN",
  "gate_violation": "attribution_failed"
}
```

### Registry Validation Script

**Command:** `python3 tools/validate_diagnosis_registry.py`

**Results:**
```
✅ Format validation PASSED
✅ Pattern validation PASSED (35 patterns checked)
✅ Enum validation PASSED
✅ Scope Coverage PASSED
  - A4105: 허혈성심장질환진단비 (8 occurrences)
✅ FIX-2 Consistency PASSED
✅ ALL VALIDATIONS PASSED
```

**Key Findings:**
- Registered diagnosis benefits: 6 (A4200_1, A4209, A4210, A4299_1, A4103, A4105)
- Unregistered coverage_codes: 28 (expected - treatment/admission/surgery)
- No treatment/surgery/admission coverages in registry
- Diagnosis trigger validated for all entries

---

## 📦 Deliverables (LOCKED)

1. ✅ `data/registry/diagnosis_coverage_registry.json` (ischemic entry added)
2. ✅ `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` (human-readable updated)
3. ✅ `docs/audit/STEP_NEXT_D_ISCHEMIC_PILOT.md` (this document)
4. ✅ Validation log (PASS)

---

## 🚫 Absolute Prohibitions (ENFORCED)

- ❌ Treatment/surgery/admission coverage inclusion
- ❌ Expansion beyond Samsung/KB
- ❌ Step3 Evidence changes
- ❌ Q1-Q14 re-execution
- ❌ Comparison table generation

---

## 🔬 Decision Points

### A4104_1 (심장질환진단비) - NOT INCLUDED

**Reason:** Broader "heart disease" category, not specifically ischemic heart disease
- A4104_1 includes: 심근병증, 심장판막협착증, 심장염증질환, etc.
- These are separate from ischemic heart disease
- Requires separate evaluation and registry entry if needed

**Coverage codes in scope but NOT registered:**
- A4104_1: 심장질환진단비 (24 occurrences)
  - Includes: 심근병증진단비, 심장질환(특정Ⅰ), 심장질환(특정Ⅱ)
  - Not ischemic heart disease specific
  - Intentionally excluded from this pilot

---

## ✅ Completion Criteria (DoD)

- ✅ Samsung + KB ischemic heart disease diagnosis coverage registered
- ✅ Non-diagnosis coverages excluded (0 violations)
- ✅ Validation PASSED
- ✅ Same structure/rules as cancer and stroke diagnosis maintained
- ✅ Treatment/surgery contamination: 0 cases

---

## 🔙 Return State

**Returned to:** STEP NEXT-B (Diagnosis Coverage Registry SSOT Lock)

**Next Steps Enabled:**
- STEP NEXT-E: 급성심근경색증진단비 Pilot
- STEP NEXT-83: 전 진단비 확장 (all diagnosis types)

---

## 📊 Impact Summary

### Before STEP NEXT-D
- Diagnosis coverage registry: 5 entries (cancer + stroke)
- Ischemic heart disease diagnosis: unmapped/ambiguous

### After STEP NEXT-D
- Diagnosis coverage registry: 6 entries (cancer + stroke + ischemic)
- Ischemic heart disease diagnosis: A4105 registered (Samsung + KB)
- Structure validated: same rules as cancer and stroke diagnosis
- Coverage Attribution Gate (G5): ready for ischemic heart disease diagnosis

---

## 🔒 Final Declaration

**STEP NEXT-D 완료**
- Ischemic Heart Disease Diagnosis Coverage Registry updated (Samsung + KB)
- diagnosis_benefit only
- Validation PASS
- Returned to STEP NEXT-B (SSOT state)

---

## References

- `data/registry/diagnosis_coverage_registry.json` - Machine-readable registry
- `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` - Human-readable documentation
- `tools/validate_diagnosis_registry.py` - Validation script
- `docs/audit/STEP_NEXT_C_STROKE_DIAGNOSIS_SSOT.md` - Stroke diagnosis SSOT
- `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` - Cancer diagnosis SSOT
