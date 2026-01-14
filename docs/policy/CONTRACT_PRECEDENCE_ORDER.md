# Contract Precedence Order

**Date**: 2026-01-14
**Task**: STEP PIPELINE-CONTRACT-INVENTORY-01
**Status**: ✅ COMPLETE (FACT ONLY)

---

## Purpose

Document the ACTUAL precedence order that the code follows when multiple contracts could apply.

NO ideal/should/recommended order. FACT-BASED ONLY (what the code actually does).

---

## Overall Precedence Hierarchy

Based on code analysis, the system follows this precedence (highest to lowest):

```
1. Frozen SSOT (Q11_references_v1.jsonl)
2. Overlay SSOT (q5/q7/q8_policy_v1.jsonl)
3. Compare Model Output (compare_tables_v1.jsonl)
4. Step3 Evidence (evidence_enriched_v1.jsonl)
5. Step2 Mapping (canonical_scope_v1.jsonl, uses mapping Excel)
6. Step1 Facts (step1_raw_scope_v3.jsonl)
7. Policy Documents (documentation only, no runtime precedence)
```

---

## Detailed Precedence Rules

### Rule 1: Frozen SSOT Overrides All

**Evidence**: `apps/api/server.py:1420-1422`

```python
# Load references from q11_references_v1.jsonl (SSOT: business method only)
# FROZEN: This is the single source of truth for Q11, DO NOT BACKFILL
references_path = "data/compare_v1/q11_references_v1.jsonl"
```

**Behavior**:
- Q11 endpoint reads `q11_references_v1.jsonl` directly
- Does NOT use `compare_tables_v1.jsonl`
- Does NOT use Step3/Step4 output

**Precedence**: Frozen SSOT > Compare Model > Step3 Evidence

**Impact**: ⚠️ CRITICAL - Q11 completely bypasses pipeline

---

### Rule 2: Overlay SSOT Overrides Compare Model (for specific questions)

**Evidence**: `apps/api/server.py:903, 988, 1066`

```python
# Q5
policies = load_q5_waiting_policy(insurers_filter=insurers_filter)
# Does NOT use compare_tables_v1.jsonl for Q5

# Q7
policies = load_q7_waiver_policy(insurers_filter=insurers_filter)
# Uses overlay first, compare model for other data

# Q8
policies = load_q8_surgery_repeat_policy(insurers_filter=insurers_filter)
# Uses overlay first, compare model for other data
```

**Behavior**:
- Q5/Q7/Q8 endpoints load overlay SSOT first
- For Q5: ONLY overlay (no compare model used)
- For Q7/Q8: Overlay + compare model (merged)

**Precedence**: Overlay SSOT > Compare Model (for policy fields)

**Impact**: ⚠️ HIGH - Question-specific data overrides general data

---

### Rule 3: Compare Model Overrides Step3 Evidence (for Q1, Q13)

**Evidence**: `apps/api/server.py:1196`

```python
# Load data from compare_tables_v1.jsonl (has coverage_code)
data_path = "data/compare_v1/compare_tables_v1.jsonl"
```

**Behavior**:
- Q1, Q13 endpoints read `compare_tables_v1.jsonl`
- Do NOT read `step3_evidence_enriched_v1.jsonl` directly
- Compare model is already processed Step3 data

**Precedence**: Compare Model > Step3 Evidence (Step4 output used, not Step3)

**Impact**: ⚠️ HIGH - API always uses processed data, not raw evidence

---

### Rule 4: Step3 Evidence Overrides Step2 Mapping (during build)

**Evidence**: `pipeline/step4_compare_model/builder.py:67-109`

```python
def build_row(self, step3_coverage: Dict) -> CompareRow:
    """
    Build CompareRow from Step3 gated coverage.
    """
    # Extract identity (uses Step2 coverage_code)
    identity = self._build_identity(step3_coverage)

    # Extract slots (uses Step3 evidence_slots)
    slots = self._build_slots(step3_coverage)
```

**Behavior**:
- Step4 builder reads Step3 output (`step3_evidence_enriched_v1.jsonl`)
- Step3 output contains both Step2 fields (coverage_code) and Step3 fields (evidence_slots)
- If conflict, Step3 evidence_slots override Step2 facts

**Precedence**: Step3 Evidence > Step2 Fields (for slot values)

**Impact**: ⚠️ HIGH - Evidence-based values override extracted facts

---

### Rule 5: Step2 Mapping Creates coverage_code (no override)

**Evidence**: `pipeline/step2_canonical_mapping/map_to_canonical.py:75-114`

```python
# 1. 신정원코드명으로 exact match
self.mapping_dict[coverage_name_canonical] = {
    'coverage_code': coverage_code,
    ...
}

# 2-4. Normalized/alias matches
# (creates coverage_code if match found)
```

**Behavior**:
- Step2-b creates coverage_code field
- Step1 does NOT have coverage_code
- Once created, coverage_code is never modified (immutable through pipeline)

**Precedence**: Step2 coverage_code > Step1 coverage_name_raw (coverage_code is new, not override)

**Impact**: ⚠️ CRITICAL - coverage_code assignment is one-time, irreversible

---

### Rule 6: Step1 Facts Are Baseline (no override)

**Evidence**: `pipeline/step1_summary_first/extractor_v3.py:240-289`

```python
def _extract_from_summary():
    # Extract coverage_name_raw from PDF
    # Extract proposal_facts from PDF
    ...
```

**Behavior**:
- Step1 extracts facts from PDF
- No precedence conflict (baseline data)

**Precedence**: N/A (baseline, not override)

**Impact**: ⚠️ HIGH - All pipeline data originates from Step1

---

## Precedence by Data Type

### Coverage Code Assignment

**Precedence**: Step2 Mapping Excel > (no other source)

**Evidence**:
- Step2-b: `map_to_canonical.py:12` loads `담보명mapping자료.xlsx`
- No other code creates or modifies coverage_code
- Immutable after Step2-b

**Impact**: ⚠️ CRITICAL - Mapping Excel is sole authority for coverage_code

---

### Evidence (Slot Values)

**Precedence**: Frozen SSOT (Q11) > Overlay SSOT (Q5/Q7/Q8) > Step3 Evidence > Step1 Facts

**Evidence**:
- Q11: `server.py:1422` reads `q11_references_v1.jsonl` (frozen, overrides all)
- Q5/Q7/Q8: `overlays/*/loader.py` reads overlay SSOT (overrides Step3 for policy fields)
- Q1/Q13: `server.py:1196` reads `compare_tables_v1.jsonl` (processed Step3 evidence)
- Step1: `proposal_facts` (baseline, lowest precedence)

**Impact**: ⚠️ CRITICAL - Evidence precedence varies by question type

---

### Product Metadata

**Precedence**: contract_meta_v1.jsonl > Step1 product facts

**Evidence**:
- API: `server.py:1178-1193` loads `contract_meta_v1.jsonl`
- If not found, falls back to Step1 `product` field

**Impact**: ⚠️ MEDIUM - Contract meta overrides Step1 product names

---

### Gate Validation

**Precedence**: Step4 Gates > Step3 Gates > (no validation)

**Evidence**:
- Step4: `builder.py:65` instantiates `SlotGateValidator`, `SlotTierEnforcementGate`
- Step3: `resolver.py:53` instantiates `EvidenceGates`
- Step4 gates re-validate Step3 gate results

**Impact**: ⚠️ HIGH - Multiple validation layers, Step4 has final say

---

## Conflict Resolution Rules

### Conflict 1: Step3 Evidence vs Step1 Facts

**Scenario**: Step1 has `proposal_facts.amount = "3천만원"`, Step3 extracts `payout_limit = "30000000"`

**Resolution**: Step3 evidence preferred (more specific slot extraction)

**Code evidence**: `builder.py:83-84` uses `_build_slots(step3_coverage)` which prioritizes `evidence_slots` over `proposal_facts`

---

### Conflict 2: Overlay SSOT vs Compare Model

**Scenario**: Q7 overlay says waiver_policy = "WAIVE_ON_CANCER", compare model has different value

**Resolution**: Overlay SSOT preferred (question-specific override)

**Code evidence**: `server.py:988` loads overlay first, uses it for policy field, ignores compare model policy field

---

### Conflict 3: Frozen SSOT vs Everything Else

**Scenario**: Q11 frozen reference has value, compare model has different value

**Resolution**: Frozen SSOT preferred (absolute authority)

**Code evidence**: `server.py:1422` only reads frozen SSOT, never reads compare model for Q11

---

### Conflict 4: Multiple Evidence Sources (Step3 G3 Gate)

**Scenario**: 가입설계서 says "180일", 약관 says "120일"

**Resolution**: CONFLICT status (not resolved, flagged to user)

**Code evidence**: `gates.py` (Step3) G3 gate detects conflict, sets `status = "CONFLICT"`

---

## Precedence Violations (Code vs Policy)

### Violation 1: Mapping Excel Path

**Policy**: `COVERAGE_MAPPING_SSOT.md` declares `data/sources/insurers/담보명mapping자료.xlsx` as SSOT

**Code**: `map_to_canonical.py:12` uses `data/sources/mapping/담보명mapping자료.xlsx` (CONTAMINATED)

**Actual Precedence**: CONTAMINATED path > SSOT path (code wins, policy ignored)

**Impact**: ⚠️ CRITICAL - Code violates policy document

---

### Violation 2: Q11 Backfill

**Policy**: `Q11_FREEZE_DECLARATION.md` says "DO NOT BACKFILL from Step3/Step4"

**Code**: `server.py:1422` reads only frozen SSOT, never backfills

**Actual Precedence**: Frozen SSOT > ALL (code follows policy) ✅

**Impact**: None (code compliant)

---

## Precedence Order Summary Table

| Data Type | Highest Precedence | 2nd | 3rd | Lowest |
|-----------|-------------------|-----|-----|--------|
| Coverage Code | Step2 Mapping Excel | - | - | - |
| Q11 Evidence | Frozen SSOT (q11_references) | - | - | - |
| Q5/Q7/Q8 Policy | Overlay SSOT | Compare Model | Step3 Evidence | Step1 Facts |
| Q1/Q13 Evidence | Compare Model (Step4) | Step3 Evidence | Step1 Facts | - |
| Product Metadata | contract_meta_v1.jsonl | Step1 product | - | - |
| Gate Validation | Step4 Gates | Step3 Gates | - | - |

---

## Immutability Rules

### Immutable After Creation

1. **coverage_code** (created in Step2-b, never modified)
2. **evidence_slots** (created in Step3, never modified by Step4 - only re-validated)
3. **proposal_facts** (created in Step1, never modified - only supplemented)

### Mutable/Replaced

1. **evidence_status** (Step3 creates, Step4 re-validates)
2. **slot confidence levels** (Step4 tier gate overrides Step3)
3. **unanchored flag** (Step4 calculates, not in Step3)

---

## DoD Checklist

- [✅] Actual precedence order documented (7 levels)
- [✅] Code evidence provided for each rule
- [✅] Conflict resolution rules documented
- [✅] Precedence violations identified (1 critical)
- [✅] Precedence summary table created
- [✅] Immutability rules documented
- [✅] NO ideal/should recommendations (FACT ONLY)

---

**END OF PRECEDENCE DOCUMENT**
