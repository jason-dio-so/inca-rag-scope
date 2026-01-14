# Q11 Duration Calculation Path Trace

**Date**: 2026-01-14
**Task**: STEP DEMO-Q11-BACKEND-FIX-02 (Part 1)
**Status**: ✅ PATH CONFIRMED, ISSUE IDENTIFIED

---

## Problem Statement

Q11 endpoint returns `heungkuk.duration_limit_days.status = "UNKNOWN"` and `value = null` despite evidence containing "1일-180일" / "180일 한도" patterns.

---

## Data Flow Path (FACT-ONLY)

### Path 1: Step3 Evidence Resolver → Step4 Compare Model → Q11 Endpoint

```
[Step3] evidence_patterns.py (parser)
   ↓ extracts duration from text patterns
[Step3 Output] heungkuk_step3_evidence_enriched_v1_gated.jsonl
   ↓ contains duration_limit_days.value
[Step4] builder.py (reads step3 output)
   ↓ aggregates into compare model
[Step4 Output] compare_tables_v1.jsonl
   ↓ contains duration_limit_days slot
[Q11 Endpoint] server.py:1106-1303
   ↓ reads compare_tables_v1.jsonl directly
[Q11 Response] JSON with duration_limit_days
```

### Q11 Endpoint Code (server.py:1159-1252)

**Key Points**:
1. Q11 does **NO parsing or extraction**
2. Q11 reads `compare_tables_v1.jsonl` directly (line 1160)
3. Q11 extracts `slots.duration_limit_days` from coverage_rows (line 1181)
4. Q11 applies SSOT normalization: `FOUND + NULL → UNKNOWN` (lines 1185-1186)

```python
# Line 1160: Load data source
data_path = "data/compare_v1/compare_tables_v1.jsonl"

# Lines 1169-1181: Extract slots
for row in table_data.get('coverage_rows', []):
    slots = row.get('slots', {})
    days_slot = slots.get('duration_limit_days', {})

    # Lines 1185-1186: SSOT Normalization
    if days_slot.get('status') == 'FOUND' and days_slot.get('value') is None:
        days_slot = {'status': 'UNKNOWN', 'evidences': []}

    # Lines 1239-1242: Build response item
    "duration_limit_days": {
        "status": days_slot.get('status', 'UNKNOWN'),
        "value": int(days_value) if days_value and str(days_value).isdigit() else None,
        "evidences": days_evidences
    }
```

---

## Current State Verification

### Step3 Output (heungkuk_step3_evidence_enriched_v1_gated.jsonl)

```json
{
  "coverage_code": "A6200",
  "duration_limit_days": {
    "status": null,
    "value": null,
    "evidences": []
  }
}
```

**Analysis**: Step3 output shows `duration_limit_days = null` with **0 evidences**.

### Step4 Output (compare_tables_v1.jsonl)

```json
{
  "identity": {
    "insurer_key": "heungkuk",
    "coverage_code": "A6200"
  },
  "slots": {
    "duration_limit_days": {
      "status": "FOUND",
      "value": null,
      "evidences": [
        {"page": 8, "excerpt": "..."},
        {"page": 9, "excerpt": "..."}
      ]
    }
  }
}
```

**Analysis**: Step4 output shows `status="FOUND"` but `value=null`. This triggers Q11's SSOT normalization → UNKNOWN.

### Q11 Response

```json
{
  "insurer_key": "heungkuk",
  "duration_limit_days": {
    "status": "UNKNOWN",
    "value": null,
    "evidences": []
  }
}
```

**Analysis**: Q11 converted `FOUND + null → UNKNOWN` (line 1186), and cleared evidences array.

---

## Root Cause

**FACT**: Step3 regeneration was **NEVER executed** after the parser fix in `evidence_patterns.py`.

### Timeline

1. **STEP DEMO-Q11-FIX-HEUNGKUK-DURATION-01** (2026-01-14):
   - Parser fix applied to `pipeline/step3_evidence_resolver/evidence_patterns.py:338`
   - Added hyphen range pattern: `r'1\s*일?\s*-\s*(\d+)\s*일'`
   - Tested: Pattern correctly extracts 180 from "1일-180일"
   - **BUT**: Regeneration marked as "📋 PENDING (requires 25+ minutes runtime)"

2. **Step4 rebuild** (user report):
   - Step4 was rebuilt and compare_tables/rows hash changed
   - **BUT**: Step4 read the OLD step3 output (which still had null values)
   - Result: New compare_tables_v1.jsonl still contains `duration_limit_days.value = null`

3. **Q11 endpoint**:
   - Reads compare_tables_v1.jsonl (which has null values)
   - Applies SSOT normalization: FOUND + null → UNKNOWN
   - Returns UNKNOWN to UI

---

## Why Step4 Rebuild Didn't Fix It

**Key Insight**: Step4 is a **pure aggregator**. It does NOT parse or extract evidence. It only:
1. Reads step3 output files (`*_step3_evidence_enriched_v1_gated.jsonl`)
2. Aggregates data into compare model format
3. Writes `compare_tables_v1.jsonl` and `compare_rows_v1.jsonl`

**Therefore**: Rebuilding step4 WITHOUT regenerating step3 will produce the SAME output (null values).

---

## Solution

### Required Actions

1. **Run Step3 Regeneration** (~25 minutes):
   ```bash
   cd /Users/cheollee/inca-rag-scope
   python3 pipeline/step3_evidence_resolver/run.py
   ```
   - This will apply the NEW parser (with hyphen range pattern)
   - Regenerate all `*_step3_evidence_enriched_v1_gated.jsonl` files
   - Heungkuk A6200 will have `duration_limit_days.value = 180`

2. **Run Step4 Rebuild** (~2 minutes):
   ```bash
   cd /Users/cheollee/inca-rag-scope
   python -m pipeline.step4_compare_model.run --insurers \
     heungkuk kb samsung meritz hyundai db_over41 db_under40 hanwha lotte_female lotte_male
   ```
   - This will read the NEW step3 output (with value=180)
   - Generate NEW compare_tables_v1.jsonl with `duration_limit_days.value = 180`

3. **Verify Q11 Response**:
   ```bash
   curl -s http://127.0.0.1:8000/q11 | \
     jq '.items[] | select(.insurer_key=="heungkuk") | .duration_limit_days'
   ```
   - Expected: `status="FOUND", value=180, evidences=[...]`

---

## Files Involved

| File | Role | Current State |
|------|------|---------------|
| `pipeline/step3_evidence_resolver/evidence_patterns.py:338` | Duration parser | ✅ Fixed (hyphen pattern added) |
| `data/scope_v3/heungkuk_step3_evidence_enriched_v1_gated.jsonl` | Step3 output | ❌ OLD (null value, 0 evidences) |
| `data/compare_v1/compare_tables_v1.jsonl` | Step4 output | ❌ OLD (null value despite status=FOUND) |
| `apps/api/server.py:1106-1303` | Q11 endpoint | ✅ Working (reads compare_tables_v1.jsonl) |

---

## Constitutional Compliance

- ✅ **Evidence-first**: Parser extracts from actual text patterns
- ✅ **No inference**: Regex-based extraction only
- ✅ **Fact-only**: No LLM, no estimation
- ✅ **SSOT Integrity**: Q11 enforces semantic integrity (FOUND must have value)

---

## Conclusion

**Q11 duration calculation path**:
- Q11 does NOT calculate duration
- Q11 reads duration from compare_tables_v1.jsonl
- compare_tables_v1.jsonl is generated by Step4
- Step4 reads data from Step3 output
- Step3 parses duration using evidence_patterns.py

**Issue**: Step3 was never regenerated after parser fix → Step4 rebuilt with OLD data → Q11 shows UNKNOWN.

**Fix**: Run step3 regeneration (25 min) + step4 rebuild (2 min).

---

**END OF TRACE DOCUMENT**
