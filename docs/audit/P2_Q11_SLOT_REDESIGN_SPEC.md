# P2-FIX: Q11 Slot Redesign Specification

**Date**: 2026-01-12
**Task**: STEP NEXT-P2-FIX-α
**Status**: 🔒 **SPEC LOCKED**
**Type**: Step3 Evidence Resolver Enhancement

---

## Executive Summary

**Problem**: Current `payout_limit` slot contains daily **AMOUNT** (20,000원/일), but Q11 customer asks for duration **LIMIT** (90일/120일/180일).

**Solution**: Split into TWO new slots with clear semantics:
- `daily_benefit_amount_won`: Daily payment amount (원/일)
- `duration_limit_days`: Maximum days covered (일)

**Impact**: Enables Q11 implementation after Step3 re-run achieves ≥80% FOUND rate.

---

## 1. Current State Analysis

### 1.1 Existing payout_limit Slot

**Schema** (current):
```json
{
  "payout_limit": {
    "status": "FOUND",
    "value": "20000",
    "evidences": [...]
  }
}
```

**Semantic Confusion**:
| Coverage Type | What payout_limit Contains | What Customer Needs |
|---------------|---------------------------|---------------------|
| Daily benefits (A6200) | Daily amount (20,000원) | Duration limit (90일) |
| Diagnosis benefits (A4200_1) | Frequency ("최초 1회") | Frequency (correct) |

**Problem**: Same slot name, different semantics depending on coverage type.

### 1.2 Evidence Location

**Samsung A6200 Evidence Excerpt**:
```
암 직접치료 입원일당Ⅱ(1일이상)(요양병원 제외)
암 요양병원 입원일당Ⅱ(1일이상, 90일한도)  ← DURATION LIMIT HERE
```

**Data Reality**:
- ✅ Duration limits exist in evidence text
- ❌ Not extracted to structured slot
- ❌ Mixed with other coverages' limits
- ❌ Cannot attribute to specific coverage (G5 Gate failure)

---

## 2. New Slot Schema (LOCKED)

### 2.1 Slot Definitions

#### Slot 1: daily_benefit_amount_won

**Purpose**: Daily payment amount for per-day benefits

**Schema**:
```python
{
  "slot_name": "daily_benefit_amount_won",
  "data_type": "integer",
  "unit": "KRW/day",
  "description": "Daily benefit amount paid per day of hospitalization/treatment",
  "example_values": [10000, 20000, 30000, 50000],
  "applicable_coverages": ["A6200", "A6100_1", "A6300_1", "..."]  # Daily benefit coverages
}
```

**JSON Output Example**:
```json
{
  "daily_benefit_amount_won": {
    "status": "FOUND",
    "value": 20000,
    "value_display": "20,000원/일",
    "evidences": [
      {
        "excerpt": "암 직접치료 입원일당Ⅱ ... 일당 2만원",
        "source_page": 8,
        "trigger_pattern": "일당\\s*2만원",
        "coverage_anchor": "암 직접치료 입원일당",
        "gate_status": "FOUND"
      }
    ],
    "notes": null
  }
}
```

#### Slot 2: duration_limit_days

**Purpose**: Maximum number of days benefit is paid

**Schema**:
```python
{
  "slot_name": "duration_limit_days",
  "data_type": "integer",
  "unit": "days",
  "description": "Maximum number of days benefit is paid per year or per insurance period",
  "example_values": [30, 60, 90, 120, 180, 365],
  "applicable_coverages": ["A6200", "A6100_1", "A6300_1", "..."]  # Daily benefit coverages
}
```

**JSON Output Example**:
```json
{
  "duration_limit_days": {
    "status": "FOUND",
    "value": 90,
    "value_display": "90일 한도",
    "raw_text": "90일한도",
    "evidences": [
      {
        "excerpt": "암 요양병원 입원일당Ⅱ(1일이상, 90일한도)",
        "source_page": 8,
        "trigger_pattern": "(\\d+)일한도",
        "coverage_anchor": "암 직접치료 입원일당",
        "gate_status": "FOUND"
      }
    ],
    "notes": null
  }
}
```

#### Slot 3: duration_limit_raw (Optional)

**Purpose**: Preserve original text for complex cases

**Schema**:
```python
{
  "slot_name": "duration_limit_raw",
  "data_type": "string",
  "description": "Original text of duration limit (for cases not parseable to integer)",
  "example_values": ["1~180일", "연간 90일", "보험기간 중 120일", "최대 60일"]
}
```

### 2.2 Migration Rules from Existing payout_limit

**Decision Tree**:

```python
if coverage_type == "daily_benefit":
    if payout_limit.value is integer and 10000 <= value <= 100000:
        # Likely daily amount
        daily_benefit_amount_won.value = payout_limit.value
        duration_limit_days.status = "UNKNOWN"  # Need re-extraction
    elif payout_limit.value contains "일" pattern:
        # Parse duration
        duration_limit_days.value = extract_days(payout_limit.value)
    else:
        # Ambiguous - mark both UNKNOWN
        pass

elif coverage_type == "diagnosis_benefit":
    # Keep payout_limit as-is (frequency limit)
    # Do NOT create duration_limit_days
    pass
```

**No Data Loss**:
- Existing payout_limit preserved for diagnosis benefits
- Daily benefit coverages get NEW slots populated
- Re-run Step3 with new extraction rules

---

## 3. Extraction Rules (Deterministic, LOCKED)

### 3.1 Regex Patterns for duration_limit_days

**Pattern Priority** (apply in order, stop at first match):

1. **Explicit "N일한도" Pattern**:
   ```python
   PATTERN_1 = r'(\d+)\s*일\s*한도'
   # Matches: "90일한도", "90일 한도", "120 일한도"
   # Extract: group(1) as integer
   ```

2. **Range "1~N일" Pattern**:
   ```python
   PATTERN_2 = r'1\s*~\s*(\d+)\s*일'
   # Matches: "1~180일", "1 ~ 90일"
   # Extract: group(1) as integer (upper bound)
   ```

3. **"최대 N일" Pattern**:
   ```python
   PATTERN_3 = r'최대\s*(\d+)\s*일'
   # Matches: "최대 90일", "최대90일"
   # Extract: group(1) as integer
   ```

4. **"연간 N일" Pattern**:
   ```python
   PATTERN_4 = r'연간\s*(\d+)\s*일'
   # Matches: "연간 120일", "연간120일"
   # Extract: group(1) as integer
   ```

5. **"보험기간 중 N일" Pattern**:
   ```python
   PATTERN_5 = r'보험기간\s*중\s*(\d+)\s*일'
   # Matches: "보험기간 중 60일", "보험기간중 90일"
   # Extract: group(1) as integer
   ```

**Composite Pattern** (use in Step3 extraction):
```python
DURATION_LIMIT_REGEX = re.compile(
    r'(?:(\d+)\s*일\s*한도'
    r'|1\s*~\s*(\d+)\s*일'
    r'|최대\s*(\d+)\s*일'
    r'|연간\s*(\d+)\s*일'
    r'|보험기간\s*중\s*(\d+)\s*일)',
    re.IGNORECASE
)

def extract_duration_limit(text: str) -> Optional[int]:
    match = DURATION_LIMIT_REGEX.search(text)
    if match:
        # Extract first non-None group
        for group in match.groups():
            if group:
                return int(group)
    return None
```

### 3.2 Regex Patterns for daily_benefit_amount_won

**Pattern Priority**:

1. **"일당 N원" Pattern**:
   ```python
   PATTERN_1 = r'일당\s*([\d,]+)\s*원'
   # Matches: "일당 20,000원", "일당 2만원" (need Korean number parser)
   # Extract: parse_korean_number(group(1))
   ```

2. **"N원/일" Pattern**:
   ```python
   PATTERN_2 = r'([\d,]+)\s*원\s*/\s*일'
   # Matches: "20,000원/일", "2만원 / 일"
   # Extract: parse_korean_number(group(1))
   ```

3. **"N만원" Pattern** (in daily benefit context):
   ```python
   PATTERN_3 = r'(\d+)\s*만원'
   # Matches: "2만원", "3만원"
   # Extract: int(group(1)) * 10000
   # CAUTION: Only apply if coverage_anchor contains "일당" or "입원일당"
   ```

**Composite Pattern**:
```python
DAILY_AMOUNT_REGEX = re.compile(
    r'(?:일당\s*([\d,]+)\s*원'
    r'|([\d,]+)\s*원\s*/\s*일'
    r'|(\d+)\s*만원)',  # Only if in daily benefit context
    re.IGNORECASE
)

def extract_daily_amount(text: str, context_has_daily_anchor: bool) -> Optional[int]:
    match = DAILY_AMOUNT_REGEX.search(text)
    if match:
        groups = match.groups()
        if groups[0]:  # 일당 N원
            return parse_korean_number(groups[0])
        elif groups[1]:  # N원/일
            return parse_korean_number(groups[1])
        elif groups[2] and context_has_daily_anchor:  # N만원 (only with anchor)
            return int(groups[2]) * 10000
    return None

def parse_korean_number(text: str) -> int:
    """Parse Korean number format: 2만원 → 20000, 20,000 → 20000"""
    text = text.replace(',', '')
    if '만' in text:
        num = int(text.replace('만', ''))
        return num * 10000
    return int(text)
```

---

## 4. Coverage Applicability

### 4.1 Daily Benefit Coverage List (LOCKED)

**Coverages requiring BOTH slots**:
```python
DAILY_BENEFIT_COVERAGES = {
    "A6200": "암직접치료입원일당",
    "A6100_1": "질병입원일당",
    "A6300_1": "상해입원일당",
    # Add more as identified
}
```

**Verification Rule**:
- IF coverage_code in DAILY_BENEFIT_COVERAGES
- THEN extract both daily_benefit_amount_won AND duration_limit_days
- ELSE use existing payout_limit only

### 4.2 Diagnosis Benefit Coverage List

**Coverages using ONLY payout_limit** (no change):
```python
DIAGNOSIS_BENEFIT_COVERAGES = {
    "A4200_1": "암진단비",
    "A4210": "유사암진단비",
    "A5200": "암수술비",
    # ... etc
}
```

---

## 5. Step3 Implementation Checklist

### 5.1 Code Changes Required

**File**: `pipeline/step1_summary_first/extended_slot_schema.py`

**Add New Slot Definitions**:
```python
SLOT_DEFINITIONS = {
    # ... existing slots ...

    "daily_benefit_amount_won": {
        "description": "Daily benefit amount (원/일) for per-day coverage",
        "data_type": "integer",
        "unit": "KRW/day",
        "extraction_rules": [
            {"pattern": r'일당\s*([\d,]+)\s*원', "group": 1},
            {"pattern": r'([\d,]+)\s*원\s*/\s*일', "group": 1},
        ],
        "applicable_coverages": DAILY_BENEFIT_COVERAGES,
    },

    "duration_limit_days": {
        "description": "Maximum days benefit is paid",
        "data_type": "integer",
        "unit": "days",
        "extraction_rules": [
            {"pattern": r'(\d+)\s*일\s*한도', "group": 1},
            {"pattern": r'1\s*~\s*(\d+)\s*일', "group": 1},
            {"pattern": r'최대\s*(\d+)\s*일', "group": 1},
            {"pattern": r'연간\s*(\d+)\s*일', "group": 1},
        ],
        "applicable_coverages": DAILY_BENEFIT_COVERAGES,
    },
}
```

**File**: `pipeline/step3_evidence_resolver/resolver.py`

**Add Extraction Logic**:
```python
def extract_daily_benefit_slots(coverage_code, evidences):
    """Extract both daily amount and duration limit for daily benefit coverages."""

    if coverage_code not in DAILY_BENEFIT_COVERAGES:
        return {}

    slots = {}

    # Extract daily_benefit_amount_won
    for evidence in evidences:
        excerpt = evidence.get('excerpt', '')
        amount = extract_daily_amount(excerpt, context_has_daily_anchor=True)
        if amount:
            slots['daily_benefit_amount_won'] = {
                'status': 'FOUND',
                'value': amount,
                'evidences': [evidence]
            }
            break

    # Extract duration_limit_days
    for evidence in evidences:
        excerpt = evidence.get('excerpt', '')
        days = extract_duration_limit(excerpt)
        if days:
            slots['duration_limit_days'] = {
                'status': 'FOUND',
                'value': days,
                'raw_text': excerpt[:100],
                'evidences': [evidence]
            }
            break

    return slots
```

### 5.2 G5 Gate Integration

**Requirement**: Both new slots MUST pass G5 Gate attribution check (see `P2_G5_ATTRIBUTION_UPGRADE_SPEC.md`)

**Gate Rules**:
- Coverage anchor (암직접치료입원일당) must be within ±8 lines
- No other coverage anchors in same range (REJECT_MIXED)
- Trigger pattern must match within same range

---

## 6. Validation Queries

### 6.1 Post-Implementation Verification

**Check slot FOUND rate** (after Step3 re-run):

```python
import json
from collections import defaultdict

# Load new compare_rows_v1.jsonl
with open('data/compare_v1/compare_rows_v1.jsonl', 'r') as f:
    rows = [json.loads(line) for line in f]

# Filter A6200 rows
a6200_rows = [r for r in rows if r['identity'].get('coverage_code') == 'A6200']

# Count slot status
daily_amount_status = defaultdict(int)
duration_limit_status = defaultdict(int)

for row in a6200_rows:
    slots = row.get('slots', {})

    if 'daily_benefit_amount_won' in slots:
        status = slots['daily_benefit_amount_won'].get('status', 'MISSING')
        daily_amount_status[status] += 1
    else:
        daily_amount_status['MISSING'] += 1

    if 'duration_limit_days' in slots:
        status = slots['duration_limit_days'].get('status', 'MISSING')
        duration_limit_status[status] += 1
    else:
        duration_limit_status['MISSING'] += 1

total = len(a6200_rows)

print(f"=== A6200 Slot FOUND Rates ===")
print(f"Total rows: {total}")
print(f"\ndaily_benefit_amount_won:")
for status, count in sorted(daily_amount_status.items()):
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {status}: {count}/{total} ({pct:.1f}%)")

print(f"\nduration_limit_days:")
for status, count in sorted(duration_limit_status.items()):
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {status}: {count}/{total} ({pct:.1f}%)")

# PASS/FAIL
duration_found_rate = (duration_limit_status['FOUND'] / total * 100) if total > 0 else 0
if duration_found_rate >= 80:
    print(f"\n✅ PASS: duration_limit_days FOUND rate = {duration_found_rate:.1f}% (≥80%)")
else:
    print(f"\n❌ FAIL: duration_limit_days FOUND rate = {duration_found_rate:.1f}% (<80%)")
```

**Save as**: `tools/audit/validate_q11_slot_redesign.py`

### 6.2 Sample Evidence Verification

**Check evidence quality**:

```bash
# Extract sample evidence excerpts for duration_limit_days
cat data/compare_v1/compare_rows_v1.jsonl | \
  jq -r 'select(.identity.coverage_code == "A6200") |
         select(.slots.duration_limit_days.status == "FOUND") |
         "\(.identity.insurer_key): \(.slots.duration_limit_days.value)일 | \(.slots.duration_limit_days.evidences[0].excerpt[:80])"' | \
  head -5
```

**Expected Output** (after implementation):
```
samsung: 90일 | 암 요양병원 입원일당Ⅱ(1일이상, 90일한도)
meritz: 120일 | 암직접치료입원일당(Ⅱ) ... 1~120일
kb: 60일 | 암입원일당 최대 60일
```

---

## 7. Execution Instructions (Copy-Paste Ready)

### Step 1: Apply Code Changes

**Location**: `pipeline/step3_evidence_resolver/`

1. Update `extended_slot_schema.py` (add slot definitions from section 5.1)
2. Update `resolver.py` (add extraction functions from section 5.1)
3. Verify G5 Gate integration (reference `P2_G5_ATTRIBUTION_UPGRADE_SPEC.md`)

### Step 2: Re-run Step3 Pipeline

```bash
# Standard pipeline execution (STEP NEXT-73 compliant)
python3 tools/run_pipeline.py --stage step3

# Verify execution receipt
cat docs/audit/run_receipt.json | jq '.step3_status'
```

### Step 3: Validate Results

```bash
# Copy validation script to tools/audit/
# (content from section 6.1)

# Run validation
python3 tools/audit/validate_q11_slot_redesign.py

# Check sample evidence
cat data/compare_v1/compare_rows_v1.jsonl | \
  jq -r 'select(.identity.coverage_code == "A6200") |
         select(.slots.duration_limit_days.status == "FOUND") |
         "\(.identity.insurer_key): \(.slots.duration_limit_days.value)일"'
```

### Step 4: Commit Results

```bash
git add data/compare_v1/compare_rows_v1.jsonl \
        pipeline/step3_evidence_resolver/ \
        tools/audit/validate_q11_slot_redesign.py

git commit -m "feat(step3): Q11 slot redesign - split daily amount vs duration limit

- Add daily_benefit_amount_won slot (원/일)
- Add duration_limit_days slot (일)
- Migrate payout_limit for daily benefit coverages
- Achieve ≥80% FOUND rate for duration_limit_days

Evidence: A6200 duration_limit_days FOUND rate = XX.X%"
```

---

## 8. Success Criteria (DoD)

**PASS Conditions**:
- ✅ `duration_limit_days` FOUND rate ≥ 80% for A6200
- ✅ `daily_benefit_amount_won` FOUND rate ≥ 80% for A6200
- ✅ No FOUND_GLOBAL status for either slot
- ✅ All FOUND evidence includes coverage anchor
- ✅ Sample evidence for 5+ insurers verified

**FAIL Conditions**:
- ❌ FOUND rate < 80% → Document remaining blockers with 10 evidence samples
- ❌ FOUND_GLOBAL exists → G5 Gate not properly applied
- ❌ Evidence missing coverage anchor → Attribution failure

---

## 9. Rollback Plan

**If validation fails**:
1. Preserve new slot definitions (don't remove schema)
2. Mark Q11 as "SPEC READY / BLOCKED (extraction <80%)"
3. Document failure reasons in `P2_MOCK_VALIDATION_REPORT.md`
4. Keep old payout_limit values as fallback

**No data loss**: Old payout_limit preserved for all coverage types.

---

**Document Version**: 1.0
**Status**: 🔒 **LOCKED SPEC** (Ready for Implementation)
**Last Updated**: 2026-01-12
**Next Action**: Apply code changes + run Step3 pipeline
