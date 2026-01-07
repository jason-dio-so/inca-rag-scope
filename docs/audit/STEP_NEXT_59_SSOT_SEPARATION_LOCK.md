# STEP NEXT-59: Unmapped Status Report SSOT Separation (LOCKED)

**Date**: 2026-01-07
**Status**: ✅ COMPLETE
**Constitutional Lock**: SSOT-based reporting, NO contamination between Step2-a and Step2-b

---

## Problem Definition

The previously generated "Company-by-Company Unmapped Summary Report" had **structural contamination**:

1. **Fragment Logic Applied to Step2-b**: Attempted to re-classify Step2-b unmapped items as "fragments" using `is_fragment()` logic
   - **Impossibility**: Step2-b unmapped items CANNOT be fragments (fragments are removed by Step2-a)
   - **Result**: KB/HYUNDAI items like "2. 일반상해후유장해...", "105. 부정맥질환..." incorrectly labeled as fragments

2. **Field Selection Error**: Used `coverage_name_raw` without proper priority fallback
   - Previous issue: `.coverage_name` null values (now avoided)
   - Need: Deterministic field priority (`coverage_name_normalized` > `coverage_name_raw` > `coverage_name`)

3. **SSOT Confusion**: Mixed Step2-a dropped items with Step2-b unmapped items in same "fragments" category
   - **Expected**: Step2-a dropped = noise/fragments, Step2-b unmapped = legitimate unmapped
   - **Actual**: Both mixed together, numbers mismatched

---

## Constitutional Rules (LOCKED)

### 1. SSOT Separation (ABSOLUTE)
```
Group A (Step2-a dropped) ≠ Group B (Step2-b unmapped)
```

- **Group A**: `data/scope_v3/*_step2_dropped.jsonl` (fragments/noise removed by Step2-a)
- **Group B**: `data/scope_v3/*_step2_mapping_report.jsonl` where `mapping_method=="unmapped"` (legitimate unmapped)

### 2. No Fragment Logic on Step2-b (ABSOLUTE)
```
❌ FORBIDDEN: Apply is_fragment() to Step2-b unmapped items
✅ REQUIRED: Step2-b unmapped = legitimate unmapped (NOT fragments)
```

**Rationale**: Fragments are removed by Step2-a sanitization. If an item exists in Step2-b, it passed sanitization and is NOT a fragment.

### 3. Field Priority (LOCKED)
```python
def get_display_name(entry: Dict) -> Optional[str]:
    for field in ['coverage_name_normalized', 'coverage_name_raw', 'coverage_name']:
        if field in entry and entry[field] and entry[field].strip():
            return entry[field].strip()
    return None  # Invalid, exclude from report
```

### 4. Overview = Step2-b SSOT (LOCKED)
```
Total/Mapped/Unmapped/Rate → ONLY from *_step2_mapping_report.jsonl
Dropped → ONLY from *_step2_dropped.jsonl (separate column)
```

### 5. No LLM / No Logic Change (ABSOLUTE)
```
❌ FORBIDDEN: LLM usage, inference, guessing
❌ FORBIDDEN: Modify Step2-a sanitize.py or Step2-b canonical_mapper.py
✅ REQUIRED: Report logic only (view layer)
```

---

## Solution Implementation

### New Script: `tools/audit/unmapped_status_by_company.py`

**Key Functions**:

1. **`get_display_name(entry)`**: Field priority enforcement
2. **`load_step2b_summary(mapping_report_path)`**: SSOT for overview numbers
3. **`load_group_b_unmapped(mapping_report_path)`**: Step2-b unmapped items
4. **`load_group_a_dropped(dropped_path)`**: Step2-a dropped items
5. **`generate_report(scope_v3_dir, output_path)`**: SSOT-separated report generation

**Separation Logic**:
```python
# Group B: Step2-b unmapped (legitimate unmapped)
if entry.get('mapping_method') == 'unmapped':
    display_name = get_display_name(entry)
    if display_name:
        unmapped_items.append(display_name)

# Group A: Step2-a dropped (fragments/noise)
with open(dropped_path) as f:
    for line in f:
        entry = json.loads(line)
        display_name = get_display_name(entry)
        if display_name:
            dropped_items.append(display_name)
            drop_reasons.append(entry.get('drop_reason', 'UNKNOWN'))
```

---

## Verification Results

### KB Verification (PASS ✅)
```bash
Step2-b total: 42
Step2-b mapped: 30
Step2-b unmapped: 12
Step2-a dropped: 21

Report shows:
- Total: 42 ✅
- Mapped: 30 (71.4%) ✅
- Unmapped: 12 ✅
- Dropped: 21 ✅
```

### HYUNDAI Verification (PASS ✅)
```bash
Step2-b total: 36
Step2-b mapped: 25
Step2-b unmapped: 11
Step2-a dropped: 11

Report shows:
- Total: 36 ✅
- Mapped: 25 (69.4%) ✅
- Unmapped: 11 ✅
- Dropped: 11 ✅
```

### Overall Statistics (PASS ✅)
```
10 companies, 333 items (Step2-b)
- Mapped: 278 (83.5%)
- Group B (unmapped): 55
- Group A (dropped): 37
```

---

## Key Fixes

### Before (Contaminated)
```
KB:
- Total: 42
- Unmapped: 12
- Fragments (GROUP-1): 10 ❌ (incorrectly classified)
- Legit Variants (GROUP-2): 2 ❌ (incomplete)
```

**Problem**: "2. 일반상해후유장해...", "105. 부정맥질환..." labeled as fragments due to `starts_with_connector` pattern.

### After (Corrected)
```
KB:
- Total: 42 (Step2-b SSOT)
- Mapped: 30
- Group B (unmapped): 12 ✅ (includes "2. 일반상해후유장해...")
- Group A (dropped): 21 ✅ (from Step2-a dropped.jsonl)
```

**Fix**: Step1 raw prefix (e.g., "2.") is NOT a fragment indicator in Step2-b. These are legitimate unmapped items that passed sanitization.

---

## Report Structure (LOCKED)

### Overview Table
```markdown
| Company | Total | Mapped | Unmapped | Rate | Dropped (Step2-a) |
|---------|-------|--------|----------|------|-------------------|
```

### Per-Company Sections
```markdown
## {INSURER}

**Total Coverage Items**: {total}
**Mapped**: {mapped} ({rate}%)
**Unmapped**: {unmapped}
**Dropped (Step2-a)**: {dropped_count}

### Group B: Step2-b Unmapped (Legitimate Unmapped)
**Count**: {unmapped_count}
**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.
**All Items** (or Sample if > 30):
- `{coverage_name}`

### Group A: Step2-a Dropped (Fragments/Noise)
**Count**: {dropped_count}
**Description**: Items removed by Step2-a sanitization (deterministic pattern matching).
**Drop Reasons**:
- `{reason}`: {count}
**All Items** (or Sample if > 30):
- `{coverage_name}`
```

---

## Files

### Created
- ✅ `tools/audit/unmapped_status_by_company.py` (corrected SSOT-separated generator)
- ✅ `docs/audit/UNMAPPED_STATUS_BY_COMPANY.md` (corrected report)
- ✅ `docs/audit/STEP_NEXT_59_SSOT_SEPARATION_LOCK.md` (this document)

### Deleted
- ❌ `tools/audit/unmapped_company_summary.py` (contaminated version)
- ❌ `docs/audit/UNMAPPED_COMPANY_SUMMARY.md` (contaminated version)

### Modified
- ✅ `STATUS.md` (STEP NEXT-59 entry added)

---

## Action Items

### Group A (Step2-a Dropped)
- **Status**: ✅ Already handled by Step2-a sanitize logic
- **Action**: None required (deterministic drops are correct)

### Group B (Step2-b Unmapped)
- **Status**: ⏳ Requires manual review
- **Action**:
  1. Review Group B items per company (55 items total)
  2. Add missing canonical names to `data/sources/mapping/담보명mapping자료.xlsx`
  3. Re-run Step2-b canonical mapping
  4. Verify mapping rate improvement

**Priority Companies** (by Group B count):
1. meritz: 9 unmapped
2. kb: 12 unmapped (includes numbered items - check if normalization helps)
3. hyundai: 11 unmapped (심혈관질환 variants - Excel gaps identified)
4. lotte_female: 5 unmapped
5. lotte_male: 5 unmapped

---

## Definition of Success

> **"Overview 수치가 Step2-b mapping_report와 100% 일치. Group A/B가 SSOT 파일 기준으로 분리. Step1 raw 형태가 Group B에 정상 노출 (fragments 아님)."**

**Verification Checklist**:
- ✅ Overview numbers match Step2-b mapping_report exactly
- ✅ Group A = Step2-a dropped.jsonl ONLY
- ✅ Group B = Step2-b unmapped ONLY
- ✅ No `is_fragment()` logic applied to Group B
- ✅ Field priority enforced (no null display names in report)
- ✅ "2. 일반상해후유장해..." appears in Group B (NOT Group A)
- ✅ Step2-a/Step2-b logic unchanged (0 lines modified)

---

## Regression Prevention

### Forbidden Patterns
```python
# ❌ FORBIDDEN: Apply fragment logic to Step2-b unmapped
for entry in step2b_unmapped:
    is_frag, reason = is_fragment(entry['coverage_name_raw'])  # WRONG!
```

### Required Patterns
```python
# ✅ REQUIRED: Separate SSOT sources
step2b_summary = load_step2b_summary(mapping_report_path)  # Group B
group_a_data = load_group_a_dropped(dropped_path)          # Group A
```

### SSOT Verification
```bash
# Always verify report numbers match source data
KB_UNMAPPED=$(jq 'select(.mapping_method=="unmapped")' data/scope_v3/kb_step2_mapping_report.jsonl | wc -l)
KB_DROPPED=$(wc -l < data/scope_v3/kb_step2_dropped.jsonl)

# Report MUST show: unmapped={KB_UNMAPPED}, dropped={KB_DROPPED}
```

---

## Summary

**STEP NEXT-59** fixes the fundamental contamination in unmapped reporting by enforcing **SSOT separation**:
- **Group A** (Step2-a dropped) and **Group B** (Step2-b unmapped) are structurally different and must not be mixed
- **Fragment logic** applies ONLY to Step2-a (sanitization phase), NEVER to Step2-b (mapping phase)
- **Field priority** prevents null values and ensures consistent display names
- **Overview numbers** are 100% SSOT-compliant with Step2-b mapping_report.jsonl

This establishes the correct foundation for understanding mapping gaps and prioritizing Excel additions.
