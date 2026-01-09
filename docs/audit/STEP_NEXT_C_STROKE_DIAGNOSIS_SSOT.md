# STEP NEXT-C: Stroke Diagnosis Coverage Registry SSOT Pilot

**Date:** 2026-01-09
**Status:** COMPLETED
**Scope:** Samsung + KB stroke diagnosis coverage ONLY

---

## 🎯 Objective

Apply the Diagnosis Coverage Registry + Coverage Attribution Gate (G5) structure established for cancer diagnosis to **뇌졸중 진단비** (stroke diagnosis coverage).

**Goal:** Make structural contamination impossible by:
- ❌ Excluding treatment/surgery/admission/rehabilitation coverages
- ❌ Preventing definition-based confusion
- ❌ Eliminating inter-company comparison errors due to varying definitions

---

## 📦 Scope (HARD LOCK)

- **Insurers:** Samsung, KB ONLY
- **Coverage Type:** 뇌졸중 '진단비' ONLY
- **Excluded:**
  - ❌ Q2/Q9/Q12 execution
  - ❌ Comparison/recommendation/ranking
  - ❌ Step3 Evidence logic changes

---

## 🔍 Identification Process

### Input Data (SSOT)
- Step2-b Canonical Mapping output
- Existing Diagnosis Coverage Registry (v1.0)
- Coverage mapping Excel: `data/sources/mapping/담보명mapping자료.xlsx`

### Stroke Diagnosis Coverage Candidates

**Coverage Code:** A4103
**Canonical Name:** 뇌졸중진단비

**Identified Instances:**
- Samsung: "뇌졸중 진단비(1년50%)" → A4103
- KB: "93. 뇌졸중진단비" → A4103

### Inclusion Criteria (ALL must be met)
- ✅ Coverage name contains "뇌졸중"
- ✅ Payout trigger is "진단확정 시" (diagnosis confirmation)
- ✅ Evidence excerpt confirms diagnosis-based payout

### Immediate Exclusion Criteria (ANY fails)
- ❌ 수술비 (surgery)
- ❌ 치료비 (treatment)
- ❌ 입원일당 (daily hospitalization)
- ❌ 혈관중재술 (vascular intervention)
- ❌ 시술 (procedures)
- ❌ 재활 (rehabilitation)
- ❌ 혈전용해 (thrombolysis)

---

## 📋 Registry Extension

### Added Entry: A4103

```json
{
  "coverage_code": "A4103",
  "canonical_name": "뇌졸중진단비",
  "coverage_kind": "diagnosis_benefit",
  "diagnosis_type": "stroke",
  "trigger": "진단 확정 시 지급",
  "included_subtypes": ["stroke"],
  "excluded_subtypes": [],
  "usable_for_questions": ["Q1", "Q2", "Q3", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q13", "Q14"],
  "usable_for_comparison": true,
  "usable_for_recommendation": true,
  "exclusion_keywords": [
    "수술비",
    "입원일당",
    "치료비",
    "혈관중재술",
    "재활",
    "시술",
    "혈전용해"
  ],
  "insurers": ["samsung", "kb"],
  "notes": "뇌졸중으로 진단확정 시 지급되는 정액 진단비만 허용",
  "lock_version": "v1.0"
}
```

---

## ✅ Validation Results

### Coverage Attribution Gate (G5) Verification

**Allowed Payout Conditions (ALL must be met):**
- ✅ Evidence excerpt contains "뇌졸중으로 진단확정시" or equivalent
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
✅ Pattern validation PASSED (27 patterns checked)
✅ Enum validation PASSED
✅ Scope Coverage PASSED
  - A4103: 뇌졸중진단비 (10 occurrences)
✅ FIX-2 Consistency PASSED
✅ ALL VALIDATIONS PASSED
```

**Key Findings:**
- Registered diagnosis benefits: 5 (A4200_1, A4209, A4210, A4299_1, A4103)
- Unregistered coverage_codes: 29 (expected - treatment/admission/surgery)
- No treatment/surgery/admission coverages in registry
- Diagnosis trigger validated for all entries

---

## 📦 Deliverables (LOCKED)

1. ✅ `data/registry/diagnosis_coverage_registry.json` (stroke entry added)
2. ✅ `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` (human-readable updated)
3. ✅ `docs/audit/STEP_NEXT_C_STROKE_DIAGNOSIS_SSOT.md` (this document)
4. ✅ Validation log (PASS)

---

## 🚫 Absolute Prohibitions (ENFORCED)

- ❌ 뇌혈관질환 / 허혈성 inclusion
- ❌ Expansion beyond Samsung/KB
- ❌ Step3 Evidence changes
- ❌ Q1-Q14 re-execution
- ❌ Comparison table generation

---

## ✅ Completion Criteria (DoD)

- ✅ Samsung + KB stroke diagnosis coverage registered
- ✅ Non-diagnosis coverages excluded (0 violations)
- ✅ Validation PASSED
- ✅ Same structure/rules as cancer diagnosis maintained

---

## 🔙 Return State

**Returned to:** STEP NEXT-B (Diagnosis Coverage Registry SSOT Lock)

**Next Steps Enabled:**
- STEP NEXT-D: 허혈성심장질환진단비 Pilot
- STEP NEXT-83: 전 진단비 확장 (all diagnosis types)

---

## 📊 Impact Summary

### Before STEP NEXT-C
- Diagnosis coverage registry: 4 entries (cancer only)
- Stroke diagnosis: unmapped/ambiguous

### After STEP NEXT-C
- Diagnosis coverage registry: 5 entries (cancer + stroke)
- Stroke diagnosis: A4103 registered (Samsung + KB)
- Structure validated: same rules as cancer diagnosis
- Coverage Attribution Gate (G5): ready for stroke diagnosis

---

## 🔒 Final Declaration

**STEP NEXT-C 완료**
- Stroke Diagnosis Coverage Registry updated (Samsung + KB)
- diagnosis_benefit only
- Validation PASS
- Returned to STEP NEXT-B (SSOT state)

---

## References

- `data/registry/diagnosis_coverage_registry.json` - Machine-readable registry
- `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` - Human-readable documentation
- `tools/validate_diagnosis_registry.py` - Validation script
- `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` - Cancer diagnosis SSOT
