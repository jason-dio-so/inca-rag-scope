# P2-FIX: G5 Gate Attribution Upgrade Specification

**Date**: 2026-01-12
**Task**: STEP NEXT-P2-FIX-α
**Status**: 🔒 **SPEC LOCKED**
**Type**: Step3 Evidence Resolver Enhancement

---

## Executive Summary

**Problem**: G5 Gate currently allows `FOUND_GLOBAL` status, which causes evidence attribution failures for Q5 (면책/감액) and Q11 (한도).

**Solution**: Enforce strict coverage-specific attribution requirements:
1. **Coverage anchor** must exist in evidence
2. **Trigger pattern** must exist in same proximity range
3. **NO FOUND_GLOBAL** allowed in coverage slots

**Impact**: After implementation, Q5/Q11 FOUND rates target ≥80% with verified attribution.

---

## 1. Current G5 Gate Problems

### 1.1 FOUND_GLOBAL Status Issue

**Example** (Samsung A4200_1 waiting_period):
```json
{
  "waiting_period": {
    "status": "UNKNOWN",
    "evidences": [
      {
        "excerpt": "보장명 ...면책기간... [갱신형] 암 요양병원 입원일당Ⅱ...",
        "gate_status": "FOUND_GLOBAL"
      }
    ],
    "notes": "G5 Gate: 다른 담보 값 혼입"
  }
}
```

**Problem**:
- Evidence found at **product-level** (table listing multiple coverages)
- Cannot confirm **"90일" applies to A4200_1 specifically**
- G5 Gate marked as FOUND_GLOBAL → Rejected from slot
- Result: Slot status = UNKNOWN (correct rejection, but no FOUND alternative)

### 1.2 Multi-Coverage Evidence Mixing

**Example** (Samsung A6200 evidence excerpt):
```
암 직접치료 입원일당Ⅱ(1일이상)(요양병원 제외)
암 요양병원 입원일당Ⅱ(1일이상, 90일한도)  ← Which coverage?
암 직접치료 통원일당(상급종합병원)(연간10회한)
```

**Problem**:
- **3 different coverages** in same excerpt
- "90일한도" could belong to:
  - 암 직접치료 입원일당Ⅱ (A6200)?
  - 암 요양병원 입원일당Ⅱ (different coverage)?
- Current G5 Gate: Marks as FOUND_GLOBAL or REJECT_MIXED
- Correct behavior: Need **coverage-specific anchoring**

---

## 2. New G5 Gate Rules (LOCKED)

### 2.1 Attribution Requirements (ALL must be satisfied)

**Rule G5-1: Coverage Anchor Proximity**
```
IF slot extraction triggered
THEN coverage anchor MUST exist within ±N lines of trigger
WHERE coverage anchor = coverage_code OR coverage_alias term
```

**Rule G5-2: Trigger-Anchor Co-location**
```
IF trigger pattern matched (e.g., "90일 면책")
THEN coverage anchor MUST be in SAME chunk OR within ±8 lines
```

**Rule G5-3: FOUND_GLOBAL Prohibition**
```
IF gate_status == "FOUND_GLOBAL"
THEN slot.status = UNKNOWN (reject from coverage slot)
AND notes = "Evidence found at product-level, cannot attribute to specific coverage"
```

**Rule G5-4: Mixed Coverage Rejection**
```
IF multiple coverage anchors exist in same proximity range
AND trigger pattern could belong to ANY of them
THEN slot.status = UNKNOWN
AND notes = "Multiple coverage anchors detected (REJECT_MIXED)"
```

### 2.2 Proximity Range Definition (LOCKED)

**Default Proximity**: ±8 lines from trigger pattern

**Rationale**:
- Insurance proposal PDFs typically describe one coverage per paragraph
- Paragraphs average 5-10 lines
- ±8 lines captures single coverage context while avoiding cross-contamination

**Override Conditions** (require ADR):
- Document structure analysis shows different optimal range
- Validation shows significant false positives/negatives at ±8

**Configuration**:
```python
# File: pipeline/step3_evidence_resolver/config.py

G5_GATE_CONFIG = {
    "proximity_lines": 8,  # ±8 lines from trigger
    "allow_found_global_in_slots": False,  # LOCKED: must be False
    "require_coverage_anchor": True,  # LOCKED: must be True
    "reject_mixed_anchors": True,  # LOCKED: must be True
}
```

---

## 3. Coverage Anchor Definitions

### 3.1 Q5: A4200_1 (암진단비)

**Coverage Code**: `A4200_1`

**Coverage Anchor Terms** (any of these must appear):
```python
A4200_1_ANCHORS = [
    "암진단비",
    "암 진단비",
    "암진단급여금",
    "일반암진단비",
    "암(일반암)진단비",
]
```

**Exclusion Anchors** (if these appear, REJECT):
```python
A4200_1_EXCLUSIONS = [
    "유사암",
    "소액암",
    "갑상선암",
    "기타피부암",
]
```

**Trigger Patterns** (from Q5 BLOCKER analysis):
```python
# For waiting_period slot
WAITING_PERIOD_TRIGGERS = [
    r'(\d+)\s*일\s*면책',
    r'면책\s*기간\s*(\d+)\s*일',
    r'보장\s*개시\s*일\s*(\d+)\s*일',
]

# For reduction slot
REDUCTION_TRIGGERS = [
    r'(\d+)\s*년.*?(\d+)\s*%',  # "1년 50%"
    r'감액.*?(\d+)\s*%',  # "감액 50%"
    r'(\d+)\s*%\s*지급',  # "50% 지급"
]
```

### 3.2 Q11: A6200 (암직접치료입원일당)

**Coverage Code**: `A6200`

**Coverage Anchor Terms**:
```python
A6200_ANCHORS = [
    "암직접치료입원일당",
    "암 직접치료 입원일당",
    "암직접입원비",
    "암직접치료 입원비",
    "암입원일당",  # Generic, use with caution
]
```

**Exclusion Anchors** (if these appear, REJECT):
```python
A6200_EXCLUSIONS = [
    "요양병원",  # Different coverage (암 요양병원 입원일당)
    "통원",  # Different coverage (암직접치료 통원일당)
    "수술",  # Different coverage
]
```

**Trigger Patterns** (from Q11 slot redesign spec):
```python
# For duration_limit_days slot
DURATION_LIMIT_TRIGGERS = [
    r'(\d+)\s*일\s*한도',
    r'1\s*~\s*(\d+)\s*일',
    r'최대\s*(\d+)\s*일',
    r'연간\s*(\d+)\s*일',
]

# For daily_benefit_amount_won slot
DAILY_AMOUNT_TRIGGERS = [
    r'일당\s*([\d,]+)\s*원',
    r'([\d,]+)\s*원\s*/\s*일',
    r'(\d+)\s*만원',  # Only with "일당" anchor
]
```

---

## 4. G5 Gate Implementation Logic

### 4.1 Pseudo-code (Deterministic)

```python
def apply_g5_gate_attribution(
    coverage_code: str,
    slot_name: str,
    evidence: Evidence,
    trigger_match: Match
) -> GateResult:
    """
    Apply G5 Gate attribution check.

    Returns:
        GateResult with status: FOUND | FOUND_GLOBAL | REJECT_MIXED | REJECT_NO_ANCHOR
    """

    # Get coverage-specific anchor terms
    anchors = get_coverage_anchors(coverage_code)
    exclusions = get_coverage_exclusions(coverage_code)

    # Extract context window around trigger
    trigger_line_num = get_line_number(evidence.excerpt, trigger_match)
    context_start = max(0, trigger_line_num - G5_GATE_CONFIG["proximity_lines"])
    context_end = trigger_line_num + G5_GATE_CONFIG["proximity_lines"]
    context_lines = evidence.excerpt_lines[context_start:context_end+1]
    context_text = "\n".join(context_lines)

    # Check Rule G5-1: Coverage anchor exists in context
    anchor_found = any(anchor in context_text for anchor in anchors)
    if not anchor_found:
        return GateResult(
            status="REJECT_NO_ANCHOR",
            notes=f"No coverage anchor ({anchors}) within ±8 lines of trigger"
        )

    # Check Rule G5-4: Exclusion anchors
    exclusion_found = any(excl in context_text for excl in exclusions)
    if exclusion_found:
        return GateResult(
            status="REJECT_MIXED",
            notes=f"Exclusion anchor detected: {exclusions}"
        )

    # Check Rule G5-4: Multiple coverage anchors (REJECT_MIXED)
    other_coverage_anchors = get_all_other_coverage_anchors(coverage_code)
    other_anchors_found = [
        anchor for anchor in other_coverage_anchors
        if anchor in context_text
    ]
    if other_anchors_found:
        return GateResult(
            status="REJECT_MIXED",
            notes=f"Multiple coverage anchors: {other_anchors_found}"
        )

    # Check Rule G5-3: Product-level evidence (FOUND_GLOBAL)
    if evidence.source_level == "product":  # Not coverage-specific chunk
        return GateResult(
            status="FOUND_GLOBAL",
            notes="Evidence from product-level section, not coverage-specific"
        )

    # All checks passed
    return GateResult(
        status="FOUND",
        notes=f"Coverage anchor '{anchors[0]}' confirmed within ±8 lines"
    )
```

### 4.2 Integration Points

**File**: `pipeline/step3_evidence_resolver/gates.py`

**Current G5 Gate** (likely exists, need to modify):
```python
# BEFORE (permissive):
def g5_gate_check(evidence, trigger):
    if trigger_found:
        return "FOUND" or "FOUND_GLOBAL"  # Too permissive

# AFTER (strict):
def g5_gate_check_v2(coverage_code, slot_name, evidence, trigger):
    result = apply_g5_gate_attribution(
        coverage_code, slot_name, evidence, trigger
    )

    if result.status == "FOUND":
        return result  # Allow into slot

    else:  # FOUND_GLOBAL, REJECT_MIXED, REJECT_NO_ANCHOR
        # Do NOT populate slot, mark as UNKNOWN
        return GateResult(status="UNKNOWN", notes=result.notes)
```

---

## 5. Evidence Quality Requirements

### 5.1 FOUND Evidence Checklist

**ALL must be satisfied for slot.status = FOUND**:

```
✅ Coverage anchor exists within ±8 lines of trigger
✅ No exclusion anchors in same range
✅ No other coverage anchors in same range
✅ Evidence source is coverage-specific (NOT product-level table)
✅ Trigger pattern extracted valid value
✅ Value passes sanity check (e.g., 0 < days < 365)
```

### 5.2 UNKNOWN Evidence Categories

**Category 1: REJECT_NO_ANCHOR**
- Trigger found, but no coverage anchor in proximity
- Example: "90일 면책" found, but "암진단비" term not within ±8 lines

**Category 2: REJECT_MIXED**
- Multiple coverage anchors in same context
- Cannot determine which coverage the trigger belongs to

**Category 3: FOUND_GLOBAL**
- Evidence from product-level summary table
- Not coverage-specific

**Category 4: REJECT_EXCLUSION**
- Exclusion anchor detected (e.g., "유사암" when looking for "암진단비")

---

## 6. Validation Queries

### 6.1 Post-Implementation G5 Gate Audit

**Check for FOUND_GLOBAL in slots** (should be ZERO):

```python
import json

with open('data/compare_v1/compare_rows_v1.jsonl', 'r') as f:
    rows = [json.loads(line) for line in f]

found_global_count = 0
for row in rows:
    for slot_name, slot_data in row.get('slots', {}).items():
        evidences = slot_data.get('evidences', [])
        for ev in evidences:
            if ev.get('gate_status') == 'FOUND_GLOBAL':
                found_global_count += 1
                print(f"❌ FOUND_GLOBAL in slot: {row['identity']['insurer_key']} "
                      f"{row['identity']['coverage_code']} {slot_name}")

if found_global_count == 0:
    print("✅ PASS: No FOUND_GLOBAL in any slot")
else:
    print(f"❌ FAIL: {found_global_count} slots have FOUND_GLOBAL evidence")
```

**Save as**: `tools/audit/validate_g5_gate_upgrade.py`

### 6.2 Coverage Anchor Proximity Check

**Verify anchor exists in FOUND evidence**:

```python
import json
import re

def check_anchor_proximity(coverage_code, slot_name, evidence, anchors):
    """Check if coverage anchor exists in evidence."""
    excerpt = evidence.get('excerpt', '')
    for anchor in anchors:
        if anchor in excerpt:
            return True, anchor
    return False, None

# Run check
a4200_anchors = ["암진단비", "암 진단비"]
a6200_anchors = ["암직접치료입원일당", "암직접입원비"]

missing_anchor_count = 0

for row in rows:
    code = row['identity'].get('coverage_code')
    slots = row.get('slots', {})

    # Check A4200_1 slots
    if code == 'A4200_1':
        for slot_name in ['waiting_period', 'reduction']:
            if slot_name in slots and slots[slot_name].get('status') == 'FOUND':
                evidences = slots[slot_name].get('evidences', [])
                for ev in evidences:
                    has_anchor, anchor = check_anchor_proximity(
                        code, slot_name, ev, a4200_anchors
                    )
                    if not has_anchor:
                        missing_anchor_count += 1
                        print(f"❌ Missing anchor: {row['identity']['insurer_key']} "
                              f"{slot_name}")

    # Check A6200 slots
    if code == 'A6200':
        for slot_name in ['duration_limit_days', 'daily_benefit_amount_won']:
            if slot_name in slots and slots[slot_name].get('status') == 'FOUND':
                evidences = slots[slot_name].get('evidences', [])
                for ev in evidences:
                    has_anchor, anchor = check_anchor_proximity(
                        code, slot_name, ev, a6200_anchors
                    )
                    if not has_anchor:
                        missing_anchor_count += 1
                        print(f"❌ Missing anchor: {row['identity']['insurer_key']} "
                              f"{slot_name}")

if missing_anchor_count == 0:
    print("✅ PASS: All FOUND slots have coverage anchors")
else:
    print(f"❌ FAIL: {missing_anchor_count} FOUND slots missing coverage anchors")
```

---

## 7. Execution Instructions (Copy-Paste Ready)

### Step 1: Update G5 Gate Logic

**File**: `pipeline/step3_evidence_resolver/gates.py`

1. Add coverage anchor definitions (section 3)
2. Implement `apply_g5_gate_attribution()` (section 4.1)
3. Replace existing G5 Gate checks with new v2 logic
4. Set `allow_found_global_in_slots = False` in config

### Step 2: Re-run Step3 Pipeline

```bash
# Standard pipeline execution
python3 tools/run_pipeline.py --stage step3

# Verify execution
cat docs/audit/run_receipt.json | jq '.step3_status'
```

### Step 3: Validate G5 Gate Quality

```bash
# Copy validation scripts to tools/audit/
# (content from section 6)

# Run G5 Gate audit
python3 tools/audit/validate_g5_gate_upgrade.py

# Expected output:
# ✅ PASS: No FOUND_GLOBAL in any slot
# ✅ PASS: All FOUND slots have coverage anchors
```

### Step 4: Check FOUND Rates

```bash
# Q5 waiting_period FOUND rate
cat data/compare_v1/compare_rows_v1.jsonl | \
  jq -r 'select(.identity.coverage_code == "A4200_1") |
         .slots.waiting_period.status' | \
  sort | uniq -c

# Q11 duration_limit_days FOUND rate
cat data/compare_v1/compare_rows_v1.jsonl | \
  jq -r 'select(.identity.coverage_code == "A6200") |
         .slots.duration_limit_days.status' | \
  sort | uniq -c
```

### Step 5: Commit Changes

```bash
git add pipeline/step3_evidence_resolver/gates.py \
        data/compare_v1/compare_rows_v1.jsonl \
        tools/audit/validate_g5_gate_upgrade.py

git commit -m "feat(step3): G5 Gate attribution upgrade - enforce coverage anchors

- Prohibit FOUND_GLOBAL in coverage slots
- Require coverage anchor within ±8 lines of trigger
- Add REJECT_MIXED for multi-coverage contexts
- Add REJECT_NO_ANCHOR for missing anchors

Evidence:
- Q5 waiting_period FOUND rate: XX.X%
- Q11 duration_limit_days FOUND rate: XX.X%
- Zero FOUND_GLOBAL in slots"
```

---

## 8. Success Criteria (DoD)

**G5 Gate Quality**:
- ✅ Zero FOUND_GLOBAL status in any coverage slot
- ✅ All FOUND evidence has coverage anchor verified
- ✅ No false positives (wrong coverage attribution)

**Q5 Targets** (A4200_1):
- ✅ `waiting_period` FOUND rate ≥ 80%
- ✅ `reduction` FOUND rate ≥ 80%

**Q11 Targets** (A6200):
- ✅ `duration_limit_days` FOUND rate ≥ 80%
- ✅ `daily_benefit_amount_won` FOUND rate ≥ 80%

**FAIL Conditions**:
- ❌ FOUND_GLOBAL exists in slots → G5 Gate not enforced
- ❌ FOUND rate < 80% → Document blockers with 10 evidence samples
- ❌ False positives detected → Tighten proximity range or add exclusions

---

## 9. Common Failure Modes & Solutions

### 9.1 Problem: Anchor too generic

**Symptom**: "암입원일당" matches both A6200 AND 요양병원입원일당

**Solution**: Add specificity to anchors
```python
A6200_ANCHORS = [
    "암직접치료입원일당",  # More specific
    "암직접치료 입원일당",
]
# Remove generic "암입원일당"
```

### 9.2 Problem: Proximity too narrow

**Symptom**: Coverage anchor is 10 lines away, rejected by ±8 rule

**Solution**: Adjust proximity (requires ADR)
```python
G5_GATE_CONFIG = {
    "proximity_lines": 12,  # Increase to ±12 if justified by data
}
```

### 9.3 Problem: Exclusion too aggressive

**Symptom**: "암진단비 (유사암 제외)" rejected by 유사암 exclusion

**Solution**: Add context-aware exclusion check
```python
# Only reject if exclusion is in SUBJECT position, not as exclusion clause
if "제외" not in context_around_exclusion:
    # Reject
```

---

## 10. Monitoring & Maintenance

**Quarterly Review**:
- Re-validate FOUND rates for Q5/Q11
- Check for new coverage types requiring anchors
- Review REJECT_MIXED cases for pattern improvements

**Update Triggers**:
- New insurance products added
- Document structure changes
- FOUND rate drops below 80%

---

**Document Version**: 1.0
**Status**: 🔒 **LOCKED SPEC** (Ready for Implementation)
**Last Updated**: 2026-01-12
**Next Action**: Modify gates.py + run Step3 pipeline
