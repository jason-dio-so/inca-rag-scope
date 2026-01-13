# Q11 Freeze Declaration

**Document Type:** Policy - Freeze State
**Date:** 2026-01-13
**Status:** 🔒 FROZEN
**Phase:** STEP NEXT-Q11-FREEZE-γ

---

## Scope

**Query:** Q11 (암직접치료입원일당 비교)

**Coverage Code:** A6200 ONLY

**Slots:**
- `duration_limit_days`
- `daily_benefit_amount_won`

---

## SSOT (Single Source of Truth)

### Primary SSOT

**File:** `data/scope_v3/*_step3_evidence_enriched_v1_gated.jsonl`

**Selection:** Records where `coverage_code == "A6200"`

**Authoritative Fields:**
- `evidence_pack` (array of evidence objects)
- `slots.duration_limit_days`
- `slots.daily_benefit_amount_won`

### Derived SSOT

**File:** `data/compare_v1/compare_tables_v1.jsonl`

**Selection:** `.coverage_rows[] | select(.identity.coverage_code == "A6200")`

**Constraint:** Values in compare_tables_v1 MUST derive from Step3 evidence_pack only. No other sources permitted.

---

## Frozen State Definition

### What "FROZEN" Means

1. **Evidence-First Principle:** Q11 slot values come ONLY from Step3 evidence_pack
2. **No Backfilling:** Prohibited sources:
   - `proposal_facts.coverage_amount_text`
   - `coverage_name_raw` parsing
   - Step4 inference/estimation
   - Higher-level concept mapping (e.g., "질병입원" → "암입원")
3. **UNKNOWN is Final:** If Step3 evidence_pack is empty, slot status is UNKNOWN (no exceptions)

### SSOT Rules

**Rule 1: evidence_pack Length Determines Status**
```python
if len(evidence_pack) == 0:
    slot_status = "UNKNOWN"
    slot_value = None
```

**Rule 2: FOUND Requires Evidence**
```python
if slot_status == "FOUND":
    assert len(slot_evidences) > 0, "FOUND requires evidence"
    assert slot_value is not None, "FOUND requires value"
```

**Rule 3: Unit-Guard for daily_benefit**
```python
if slot_key == "daily_benefit_amount_won" and status == "FOUND":
    assert "일당" in evidence_excerpt or "1일당" in evidence_excerpt
    assert not is_total_amount_pattern(evidence_excerpt, value)
```

---

## Allowed Changes

### 1. SSOT Regeneration

**Permitted:**
- Pipeline re-run: `python tools/run_pipeline.py --stage all`
- Result update with SAME evidence-first rules

**Conditions:**
- Must follow Step3 → Step4 → compare_tables flow
- No manual value injection
- Unit-guard validation applied

### 2. UI/UX Improvements

**Permitted:**
- Update UNKNOWN explanation text
- Add evidence availability indicators
- Improve empty state messaging

**Forbidden:**
- Changing UNKNOWN to FOUND via UI logic
- Hiding UNKNOWN status
- Implying values exist when evidence_pack is empty

### 3. Documentation Updates

**Permitted:**
- Fact clarification (with evidence)
- Process documentation
- Error analysis reports

**Forbidden:**
- Speculation about missing evidence
- Recommendations to infer values
- Policy changes without SSOT update

---

## Forbidden Changes

### ❌ Value Backfilling

**Prohibited:**
```python
# FORBIDDEN EXAMPLE
if slot_status == "UNKNOWN":
    # Try to extract from coverage_name_raw
    if "180일" in coverage_name_raw:
        slot_value = "180"  # ❌ VIOLATION
```

**Rationale:** Evidence-First principle. coverage_name_raw is NOT evidence.

### ❌ Inference from Concepts

**Prohibited:**
```python
# FORBIDDEN EXAMPLE
if "질병입원" in higher_level_concept:
    # Assume same limits apply to A6200
    duration_limit_days = disease_hospitalization_limit  # ❌ VIOLATION
```

**Rationale:** Coverage-specific evidence required. No cross-coverage inference.

### ❌ Silent Status Changes

**Prohibited:**
- Changing Q11 results during Q1/Q5/Q13 work
- "Fixing" UNKNOWN to FOUND without evidence
- Modifying compare_tables_v1 directly

**Enforcement:** Regression tests must verify Q11 results unchanged.

---

## Definition of Done (DoD)

### D1: Step3 Evidence Pack Integrity

**Check:**
```bash
python3 gather_q11_facts.py
```

**Expected:**
- heungkuk/hyundai/meritz/db: `evidence_pack_len: 0`
- If len=0, then compare_tables must show UNKNOWN

### D2: Unit-Guard for daily_benefit

**Check:**
```python
if daily_status == "FOUND" and daily_value is not None:
    assert has_daily_context(evidence_excerpt)
    assert not is_total_amount(evidence_excerpt, daily_value)
```

**Expected:**
- All FOUND daily_benefit have "일당" keyword in evidence
- No total amount contamination (e.g., 3,000,000)

### D3: Zero Regression on Other Queries

**Check:**
```bash
# Q1: Cancer diagnosis
curl -s http://localhost:8000/api/v1/compare/cancer-diagnosis | jq '.items | length'

# Q5: Waiting periods (when implemented)
# Q13: Cancer hospitalization subtypes
curl -s http://localhost:8000/api/v1/compare/cancer-hospitalization-subtypes | jq '.items | length'
```

**Expected:** Item counts unchanged from before Q11 freeze.

### D4: Documentation Complete

**Required Files:**
- ✅ `docs/audit/Q11_FACT_SNAPSHOT_2026-01-13.md`
- ✅ `docs/policy/Q11_COVERAGE_CODE_LOCK.md` (with Evidence-First Rules)
- ✅ `docs/policy/Q11_FREEZE_DECLARATION.md` (this document)

---

## Unfreezing Conditions

Q11 may be unfrozen ONLY if:

1. **New Evidence Source Added**
   - Example: Step3 now searches additional document types
   - Example: Evidence extraction patterns improved
   - Condition: Must maintain evidence-first principle

2. **SSOT Schema Change**
   - Example: Step3 output format changed
   - Example: New gate validation rules
   - Condition: Must update freeze declaration

3. **Evidence Gap Identified as Bug**
   - Example: Step3 pattern matcher has bug preventing A6200 extraction
   - Example: Gate incorrectly rejects valid evidence
   - Condition: Bug must be proven with evidence, not assumed

**Process:**
1. Create unfreeze proposal document
2. Show evidence of condition met
3. Update freeze declaration with new rules
4. Re-run verification (DoD)

---

## Version History

| Date | Version | Change |
|------|---------|--------|
| 2026-01-13 | 1.0 | Initial freeze declaration (FREEZE-γ) |

---

**Status:** 🔒 FROZEN - Evidence-First Only

**Related Documentation:**
- Fact record: `docs/audit/Q11_FACT_SNAPSHOT_2026-01-13.md`
- Policy lock: `docs/policy/Q11_COVERAGE_CODE_LOCK.md`
- Decontamination: `docs/audit/Q11_DECONTAMINATION_REPORT_2026-01-13.md`
