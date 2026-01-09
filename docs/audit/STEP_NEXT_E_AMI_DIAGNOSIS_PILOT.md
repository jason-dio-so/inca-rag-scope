# STEP NEXT-E: Acute Myocardial Infarction Diagnosis Coverage Pilot

**Date:** 2026-01-09
**Status:** INVESTIGATION COMPLETED - NO STANDALONE AMI DIAGNOSIS BENEFIT FOUND
**Scope:** Samsung + KB acute myocardial infarction diagnosis coverage search

---

## 🎯 Objective

Identify and register **급성심근경색증 '진단비'** (acute myocardial infarction diagnosis benefit) in the Diagnosis Coverage Registry for Samsung and KB.

---

## 🔍 Investigation Process

### Search Methodology

**Input Data (SSOT):**
- Step2-b Canonical Mapping output
- Existing Diagnosis Coverage Registry (v1.0)
- Coverage mapping Excel: `data/sources/mapping/담보명mapping자료.xlsx`

**Search Keywords:**
- 급성심근경색, 급성 심근경색증
- Coverage name containing "진단비"

### Search Results

**Mapping Excel:**
- ❌ No coverage with canonical name "급성심근경색진단비"
- ❌ No standalone AMI diagnosis benefit found

**Samsung Step2-b canonical scope:**
- ❌ No coverage named "급성심근경색진단비"
- ⚠️  Found: "특정3대심장질환 진단비(1년50%)" (Code: A4104_1)

**KB Step2-b canonical scope:**
- ❌ No coverage named "급성심근경색진단비"
- ⚠️  Found: "심장질환(특정Ⅱ) 진단비" (Code: A4104_1)

---

## 📋 Findings

### A4104_1 (심장질환진단비) - BUNDLED COVERAGE

Both Samsung and KB offer coverages that **include** acute myocardial infarction as **part of a broader bundle**, but NOT as a standalone diagnosis benefit.

#### Samsung: "특정3대심장질환 진단비(1년50%)"
- **Coverage code:** A4104_1
- **Canonical name:** 심장질환진단비
- **Coverage type:** Bundled heart disease diagnosis
- **Included conditions:** Multiple heart diseases (not AMI-specific)
- **Premium:** 1,681원 (100만원 coverage)

#### KB: "심장질환(특정Ⅱ) 진단비"
- **Coverage code:** A4104_1
- **Canonical name:** 심장질환진단비
- **Coverage type:** Bundled heart disease diagnosis
- **Included conditions (from evidence):**
  - 급성 심근경색증 ✅
  - 후속 심근경색증
  - 급성 심근경색증 후 특정 현존 합병증
  - 인공소생에 성공한 심장정지
- **Premium:** 356원 (1백만원 coverage)

---

## ❌ Why A4104_1 Cannot Be Registered as AMI Diagnosis Benefit

### Reason 1: Not AMI-Specific

A4104_1 is a **bundled coverage** that includes:
- Acute myocardial infarction (급성 심근경색증)
- Subsequent myocardial infarction (후속 심근경색증)
- Complications after AMI
- Successful resuscitation from cardiac arrest
- Other heart diseases (varies by insurer)

**Registry principle violation:**
- Diagnosis Coverage Registry requires **single-disease diagnosis benefits**
- Bundled coverages create ambiguity in comparison
- Cannot guarantee "AMI-only" diagnosis trigger

### Reason 2: Canonical Name Mismatch

- **Canonical name:** 심장질환진단비 (heart disease diagnosis benefit)
- **Expected for AMI:** 급성심근경색진단비 (acute myocardial infarction diagnosis benefit)
- **Diagnosis type ambiguity:** Cannot classify as pure "acute_myocardial_infarction"

### Reason 3: Coverage Attribution Gate (G5) Failure

**Required trigger:** "급성심근경색으로 진단확정 시"
**Actual trigger:** "심장질환(특정Ⅱ)으로 진단확정 시"

- Trigger is **broader** than AMI alone
- Evidence shows **multiple conditions** trigger payout
- Does not meet "diagnosis_benefit only for AMI" requirement

---

## 🚫 Decision: Do Not Register A4104_1

### Rationale

1. **Violates SSOT principle:**
   - A4104_1 is **not** an AMI-specific diagnosis benefit
   - Canonical name is "심장질환진단비", not "급성심근경색진단비"

2. **Violates comparison integrity:**
   - Bundled coverages cannot be compared fairly
   - Different insurers may include different conditions in bundles

3. **Violates registry purpose:**
   - Registry exists to identify **single-disease diagnosis benefits**
   - Bundled coverages belong to a different category

4. **No standalone AMI diagnosis benefit exists:**
   - Neither Samsung nor KB offers pure "급성심근경색진단비"
   - Both offer bundled heart disease diagnosis (A4104_1)

---

## ✅ Conclusion

### Finding Summary

- ❌ **No standalone acute myocardial infarction diagnosis benefit** found in Samsung or KB
- ⚠️  **Bundled coverage exists** (A4104_1) but does not meet registry criteria
- ✅ **Registry integrity maintained** by not registering ambiguous bundled coverage

### Recommendation

**Do NOT add A4104_1 to Diagnosis Coverage Registry**

**Reasons:**
1. A4104_1 is a bundled coverage, not AMI-specific
2. Canonical name is "심장질환진단비", not "급성심근경색진단비"
3. Diagnosis trigger is broader than AMI alone
4. Would violate single-disease diagnosis benefit principle

### Future Action

If a standalone "급성심근경색진단비" becomes available:
1. Verify it is AMI-specific (not bundled)
2. Verify canonical name matches
3. Verify diagnosis trigger is "급성심근경색으로 진단확정 시"
4. Add to registry with diagnosis_type: "acute_myocardial_infarction"

---

## 📦 Deliverables

1. ✅ `docs/audit/STEP_NEXT_E_AMI_DIAGNOSIS_PILOT.md` (this document)
2. ❌ No registry update (no eligible coverage found)
3. ❌ No validation needed (no changes made)

---

## 🔙 Return State

**Returned to:** STEP NEXT-B (Diagnosis Coverage Registry SSOT Lock)

**Current registry status:**
- Registered diagnosis benefits: 6
  - A4200_1: 암진단비(유사암제외)
  - A4209: 고액암진단비
  - A4210: 유사암진단비
  - A4299_1: 재진단암진단비
  - A4103: 뇌졸중진단비
  - A4105: 허혈성심장질환진단비

**Next Steps:**
- STEP NEXT-83: Consider full diagnosis benefit expansion strategy
- Consider whether bundled coverages (A4104_1) should have separate registry category

---

## 🔒 Final Declaration

**STEP NEXT-E 조사 완료**
- No standalone acute myocardial infarction diagnosis benefit found
- Samsung + KB offer bundled heart disease diagnosis (A4104_1) only
- Registry integrity maintained (no ambiguous bundled coverage added)
- Returned to STEP NEXT-B (SSOT state)

---

## References

- `data/registry/diagnosis_coverage_registry.json` - Machine-readable registry (unchanged)
- `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` - Human-readable documentation (unchanged)
- `docs/audit/STEP_NEXT_D_ISCHEMIC_PILOT.md` - Ischemic heart disease diagnosis SSOT
- `docs/audit/STEP_NEXT_C_STROKE_DIAGNOSIS_SSOT.md` - Stroke diagnosis SSOT
- `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` - Cancer diagnosis SSOT
