# STEP NEXT-66: Coverage Semantics Extraction (Implementation Summary)

**Date**: 2026-01-08
**Scope**: Step1 Extractor V3 Enhancement
**Constitution**: ACTIVE_CONSTITUTION.md

---

## Objective

Extract semantic components from coverage names to preserve metadata critical for evidence pipeline.

**Problem Solved**:
- "최초1회" was being extracted as standalone coverage (❌)
- Parenthetical metadata (exclusions, limits, renewal) was lost (❌)
- Fragments from parsing errors were classified as P3 instead of P1 (❌)

---

## Implementation

### STEP NEXT-66-A: Coverage Semantics Extractor

**File**: `pipeline/step1_summary_first/coverage_semantics.py`

**Features**:
1. **Rule-based extraction** (no LLM, deterministic)
2. **Semantic components extracted**:
   - `coverage_title`: Core coverage name (without metadata)
   - `exclusions`: List of excluded conditions
   - `payout_limit_type`: "per_policy", "annual", "per_accident"
   - `payout_limit_count`: Number of payouts allowed
   - `renewal_type`: Renewal period (e.g., "10년")
   - `renewal_flag`: True if (갱신형) present
   - `coverage_modifiers`: Other modifiers (감액없음, etc.)

**Example**:

```
Input:  "다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"

Output: {
  "coverage_title": "다빈치로봇 암수술비",
  "exclusions": ["갑상선암", "전립선암"],
  "payout_limit_type": "per_policy",
  "payout_limit_count": 1,
  "renewal_type": null,
  "renewal_flag": true,
  "coverage_modifiers": [],
  "fragment_detected": false,
  "parent_coverage_hint": null
}
```

---

### STEP NEXT-66-B: Fragment Detection

**Patterns detected**:
- `최초1회`, `연간1회` (standalone)
- Unclosed parenthesis: `다빈치로봇 암수술비(`
- Starts with parenthesis: `(갑상선암...`

**Fragment output**:

```json
{
  "coverage_title": "최초1회",
  "exclusions": [],
  "payout_limit_type": null,
  "payout_limit_count": null,
  "renewal_type": null,
  "renewal_flag": false,
  "coverage_modifiers": [],
  "fragment_detected": true,
  "parent_coverage_hint": null
}
```

**KB Fragment examples**:
- `최초1회` → fragment_detected=True
- `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(` → fragment_detected=True, parent_hint="다빈치로봇 수술"

---

### STEP NEXT-66-C: Evidence Requirements

**Function**: `get_evidence_requirements()`

**Mapping**:
- `payout_limit`: ["최초", "연간", "매"]
- `exclusion_clause`: ["제외"]
- `renewal_condition`: ["갱신형"]
- `reduction_clause`: ["감액"]
- `facility_restriction`: ["요양병원제외", "요양제외"]

**Example**:

```python
coverage_name = "다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
requirements = get_evidence_requirements(coverage_name)
# → ["payout_limit", "exclusion_clause", "renewal_condition"]
```

---

### STEP NEXT-66-D: Extractor Integration

**Modified**: `pipeline/step1_summary_first/extractor_v3.py`

**Changes**:
1. Import `coverage_semantics` module
2. Call `extract_coverage_semantics()` in `_extract_fact_from_row()`
3. Call `get_evidence_requirements()` in `_extract_fact_from_row()`
4. Include new fields in `proposal_facts`:
   - `coverage_semantics` (dict)
   - `evidence_requirements` (list)

**Output schema**:

```json
{
  "insurer_key": "kb",
  "coverage_name_raw": "다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)",
  "proposal_facts": {
    "coverage_amount_text": "1천만원",
    "premium_text": "260",
    "period_text": "10년/10년갱신(갱신종료:100세)",
    "coverage_semantics": {
      "coverage_title": "다빈치로봇 암수술비",
      "exclusions": ["갑상선암", "전립선암"],
      "payout_limit_type": "per_policy",
      "payout_limit_count": 1,
      "renewal_type": null,
      "renewal_flag": true,
      "coverage_modifiers": [],
      "fragment_detected": false,
      "parent_coverage_hint": null
    },
    "evidence_requirements": ["payout_limit", "exclusion_clause", "renewal_condition"],
    "evidences": [...]
  }
}
```

---

## Verification Results

### KB Extraction Test

**Command**: `python -m pipeline.step1_summary_first.extractor_v3 --insurer kb`

**Results**:
- ✅ Extracted: 63 facts
- ✅ Da Vinci robot surgery semantics correctly extracted
- ✅ Fragment detection working:
  - `최초1회` → fragment_detected=True
  - `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(` → fragment_detected=True
  - `다빈치로봇 갑상선암 및 전립선암수술비(` → fragment_detected=True

**Sample output**:

```bash
$ grep "다빈치로봇" data/scope_v3/kb_step1_raw_scope_v3.jsonl | jq '.coverage_name_raw, .proposal_facts.coverage_semantics'

"206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
{
  "coverage_title": "206. 다빈치로봇 암수술비",
  "exclusions": ["갑상선암", "전립선암"],
  "payout_limit_type": "per_policy",
  "payout_limit_count": 1,
  "renewal_type": null,
  "renewal_flag": true,
  ...
}

"최초1회"
{
  "coverage_title": "최초1회",
  "fragment_detected": true,
  "parent_coverage_hint": null,
  ...
}
```

---

## STEP NEXT-64 Policy Lock Update (Pending)

### KB Fragment Reclassification

**Current** (STEP NEXT-64):
| coverage_name | policy | reason |
|---------------|--------|--------|
| 최초1회 | P3 | Fragment from parsing metadata |
| 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)( | P3 | Fragment from parsing error |
| 다빈치로봇 갑상선암 및 전립선암수술비( | P3 | Fragment from parsing error |

**Updated** (STEP NEXT-66):
| coverage_name | policy | reason |
|---------------|--------|--------|
| 최초1회 | **P1** | Step1 extraction bug: `(최초1회한)` parsed as separate coverage |
| 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)( | **P1** | Step1 extraction bug: incomplete coverage name due to parenthesis mismatch |
| 다빈치로봇 갑상선암 및 전립선암수술비( | **P1** | Step1 extraction bug: incomplete coverage name due to parenthesis mismatch |

**Action Required**:
- Update `docs/audit/STEP_NEXT_64_POLICY_LOCK.md`
- Recount: P1=3, P2=46, P3=11, P4=2

---

## Constitutional Compliance

✅ **Constitution §8**: No LLM-based inference (rule-based only)
✅ **Reproducibility**: Same input → Same output
✅ **Semantic preservation**: No deletion of conditions/limits/frequency/renewal
✅ **STEP NEXT-66-A**: Coverage semantics extracted
✅ **STEP NEXT-66-B**: Fragment detection implemented
✅ **STEP NEXT-66-C**: Evidence requirements mapped

---

## Downstream Impact

### Step2-a (Sanitize) - NO CHANGE
- Still uses `coverage_name_raw` for normalization
- `coverage_semantics` is preserved but not used

### Step2-b (Canonical Mapping) - NO CHANGE
- Still uses `coverage_name_normalized` for mapping
- `coverage_semantics` is preserved but not used

### Evidence Pipeline (Future) - READY
- `coverage_semantics.exclusions` → Evidence for exclusion clauses
- `coverage_semantics.payout_limit_count` → Evidence for payout limits
- `coverage_semantics.renewal_flag` → Evidence for renewal conditions
- `evidence_requirements` → List of evidence types needed

---

## Next Steps

1. ✅ **STEP NEXT-66-A**: Coverage semantics extraction (COMPLETE)
2. ✅ **STEP NEXT-66-B**: Fragment detection (COMPLETE)
3. ✅ **STEP NEXT-66-C**: Evidence requirements mapping (COMPLETE)
4. ⏳ **STEP NEXT-66-E**: Update STEP_NEXT_64_POLICY_LOCK.md (P3 → P1 reclassification)
5. ⏳ **STEP NEXT-66-F**: Run all insurers and verify semantics extraction

---

**Implementation Date**: 2026-01-08
**Constitution Version**: ACTIVE_CONSTITUTION.md (2026-01-08)
**Extractor Version**: extractor_v3.py (STEP NEXT-66 enhanced)
