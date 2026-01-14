# A4200_1 String Matching Ban Scan

**Date:** 2026-01-14
**Scope:** All Python files in `pipeline/`
**Constitution:** COVERAGE CANONICALIZATION V2
**Rule:** Coverage name strings MUST NOT be used for identification, matching, or decision logic

---

## 🎯 Purpose

This document reports the results of scanning pipeline code for **forbidden string-based coverage matching** patterns.

**Absolute Ban:** The following operations on coverage_name strings are FORBIDDEN:
- Equality comparison (`==`)
- Substring checks (`in`)
- Pattern matching (regex, fuzzy, startswith, endswith)
- String similarity/inference
- Decision logic based on coverage name content

**Allowed:** Display, rendering, logging (read-only, no decision impact)

---

## ❌ VERDICT: FAIL - 58 String Matching Violations Found

**Critical Finding:** Extensive use of coverage_name string patterns for logic, especially in evidence search and coverage name normalization.

**Worst Offender:** `pipeline/step4_evidence_search/search_evidence.py` (31 violations)

---

## 📊 Violation Summary

### Total Violations: 58

### Violations by File:

| File | Violations | Severity |
|------|------------|----------|
| `step4_evidence_search/search_evidence.py` | 31 | 🔴 CRITICAL |
| `step1_summary_first/hybrid_layout.py` | 5 | ⚠️ HIGH |
| `step8_render_deterministic/example4_subtype_eligibility.py` | 4 | ⚠️ MEDIUM |
| `step1_summary_first/profile_builder_v3.py` | 3 | ⚠️ MEDIUM |
| `step2_sanitize_scope/sanitize.py` | 3 | ⚠️ MEDIUM |
| `step1_summary_first/coverage_validity.py` | 2 | ⚠️ LOW |
| `step2_canonical_mapping/map_to_canonical.py` | 2 | ⚠️ LOW |
| (7 other files) | 8 | ⚠️ LOW |

### Violations by Pattern Type:

| Pattern | Count | Examples |
|---------|-------|----------|
| `in coverage_name` (substring check) | 24 | `if '진단비' in coverage_name` |
| `if coverage_name` (decision) | 12 | `if coverage_name.endswith(suffix)` |
| `coverage_name.endswith()` | 10 | `if coverage_name.endswith('담보')` |
| `coverage_name.startswith()` | 3 | (not shown in top 30) |
| `coverage_name ==` | 2 | (not shown in top 30) |
| Other (regex, fuzzy, etc.) | 7 | Various |

---

## 🔴 CRITICAL: step4_evidence_search/search_evidence.py

**31 violations in a single file**

### Purpose of This File

From docstring:
```
STEP NEXT-43-P2: Evidence search with query variant generation

Q-slot evidence search via query construction:
1. Build query terms from coverage name
2. Generate coverage-type specific query variants
3. Search full-text index (FTS5) with boosted table types
4. Return top K results sorted by bm25 rank
```

### Violation Examples

**Lines 70-80: String-based variant generation**
```python
suffixes = ['보장특약', '담보', '특약', '보장']
for suffix in suffixes:
    if coverage_name.endswith(suffix):  # ← VIOLATION
        variants.append(coverage_name[:-len(suffix)])
        break

if '진단비' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('진단비', '진단'))
elif '진단' in coverage_name and '진단비' not in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('진단', '진단비'))
```

**Lines 124-149: Cancer terminology transformations**
```python
if '유사암(4대)' in coverage_name or '유사암(8대)' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('유사암(4대)', '4대유사암'))
    variants.append(coverage_name.replace('유사암(8대)', '8대유사암'))

if '4대유사암' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('4대유사암', '유사암(4대)'))

if '통합암(4대유사암제외)' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('통합암(4대유사암제외)', '통합암'))

if '4대유사암제외' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('4대유사암제외', '유사암제외'))
```

**Lines 153-185: Coverage type inference**
```python
if '치료비' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('치료비', '치료'))
elif '치료' in coverage_name and '치료비' not in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('치료', '치료비'))

if '입원일당' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('입원일당', '입원'))

if '수술비' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('수술비', '수술'))

if '항암치료' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('항암치료', '항암'))

if '표적항암' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('표적항암', '표적'))

if '재진단암' in coverage_name:  # ← VIOLATION
    variants.append(coverage_name.replace('재진단암', '재진단'))
```

### Why This is FORBIDDEN

1. **String patterns determine evidence search logic**
   - If coverage_name contains "진단비", different query variants are generated
   - This means evidence search behavior depends on string content, not coverage_code

2. **Insurer-specific string transformations**
   - Hanwha uses "4대유사암" while others use "유사암(4대)"
   - Code tries to bridge these with string substitutions
   - **CORRECT APPROACH:** Both should map to A4200_1, evidence search should use A4200_1

3. **Coverage type inference from name**
   - "치료비" → infer this is a treatment coverage
   - "입원일당" → infer this is a hospitalization coverage
   - **CORRECT APPROACH:** coverage_code metadata should specify type

### Impact on A4200_1

**Meritz A4200_1:** "암진단비(유사암제외)"
- Triggers: `'진단비' in coverage_name` → generates "암진단(유사암제외)" variant
- Triggers: `'유사암' in coverage_name` → may match other similar names

**Hanwha A4200_1:** "암(4대유사암제외)진단비"
- Triggers: `'4대유사암제외' in coverage_name` → generates multiple variants
- Triggers: `'진단비' in coverage_name` → generates "진단" variant

**Problem:** Evidence search for Meritz A4200_1 and Hanwha A4200_1 use **different query variants** because the strings are different. This creates **inconsistent evidence extraction** for the **same coverage_code**.

---

## ⚠️ HIGH: step1_summary_first/hybrid_layout.py

**5 violations**

### Purpose

PDF layout extraction using hybrid text + table parsing.

### Violation Example

**Line 154-160:**
```python
if 'coverage_name_raw' in coverage_name.lower():  # ← VIOLATION
    # Skip header rows
    continue

if coverage_name == '담보명' or coverage_name == '보장명':  # ← VIOLATION
    # Skip label rows
    continue
```

### Judgment

**ALLOWED (marginal)**

These are filter conditions to skip header/label rows during PDF parsing. They're not using coverage_name for **identification** or **mapping**, just for **noise filtering**.

However, a cleaner approach would be to have a whitelist of valid coverage_codes and reject anything not in the whitelist.

---

## ⚠️ MEDIUM: step2_sanitize_scope/sanitize.py

**3 violations**

### Purpose

Sanitize extracted coverage data before canonical mapping.

### Violation Examples

**Line 89-95:**
```python
if not coverage_name_raw or len(coverage_name_raw) < 2:  # ← VIOLATION (length check OK)
    return DropReason(...)

if coverage_name_raw in ['담보명', '보장명', '특약명']:  # ← VIOLATION
    return DropReason(...)
```

### Judgment

**ALLOWED**

These are sanity checks to drop obviously invalid rows (too short, header rows). Not using coverage_name for coverage identification.

---

## ⚠️ LOW: step2_canonical_mapping/map_to_canonical.py

**2 violations**

### Purpose

Map coverage names to canonical codes.

### Violation Examples

**Line 183-186:**
```python
if coverage_name_raw in self.mapping_dict:  # ← VIOLATION
    result = self.mapping_dict[coverage_name_raw].copy()
    result['mapping_status'] = 'matched'
    return result
```

### Judgment

**ALLOWED (by design)**

This is the Step2 canonical mapper. Its entire purpose is to look up coverage_name in SSOT to get coverage_code. This is **legitimate use** as long as:
1. The lookup dictionary comes from SSOT (NOT CURRENTLY TRUE - uses contaminated file)
2. This happens AFTER extraction (currently yes)
3. This is the ONLY place where name → code mapping happens (currently yes)

**However:** The current implementation uses the WRONG SSOT file (contaminated). This is a separate violation documented in `A4200_1_STEP1_TARGET_PLAN_TRACE.md`.

---

## 📋 Detailed Violation List

### Top 30 Violations (by file + line)

1. `step4_evidence_search/search_evidence.py:72` - `if coverage_name.endswith(suffix)`
2. `step4_evidence_search/search_evidence.py:77` - `if '진단비' in coverage_name`
3. `step4_evidence_search/search_evidence.py:79` - `elif '진단' in coverage_name and '진단비' not in coverage_name`
4. `step4_evidence_search/search_evidence.py:112` - `if coverage_name.endswith(suffix)`
5. `step4_evidence_search/search_evidence.py:117` - `if '진단비' in coverage_name`
6. `step4_evidence_search/search_evidence.py:119` - `elif '진단' in coverage_name and '진단비' not in coverage_name`
7. `step4_evidence_search/search_evidence.py:124` - `if '유사암(4대)' in coverage_name or '유사암(8대)' in coverage_name`
8. `step4_evidence_search/search_evidence.py:129` - `if '4대유사암' in coverage_name`
9. `step4_evidence_search/search_evidence.py:132` - `if '8대유사암' in coverage_name`
10. `step4_evidence_search/search_evidence.py:137` - `if '통합암(4대유사암제외)' in coverage_name`
11. `step4_evidence_search/search_evidence.py:143` - `if '4대유사암제외' in coverage_name`
12. `step4_evidence_search/search_evidence.py:148` - `if '4대특정암' in coverage_name`
13. `step4_evidence_search/search_evidence.py:153` - `if '치료비' in coverage_name`
14. `step4_evidence_search/search_evidence.py:155` - `elif '치료' in coverage_name and '치료비' not in coverage_name`
15. `step4_evidence_search/search_evidence.py:159` - `if '입원일당' in coverage_name`
16. `step4_evidence_search/search_evidence.py:161` - `elif '입원' in coverage_name and '입원일당' not in coverage_name`
17. `step4_evidence_search/search_evidence.py:165` - `if '수술비' in coverage_name`
18. `step4_evidence_search/search_evidence.py:167` - `elif '수술' in coverage_name and '수술비' not in coverage_name`
19. `step4_evidence_search/search_evidence.py:171` - `if '항암치료' in coverage_name`
20. `step4_evidence_search/search_evidence.py:173` - `elif '항암' in coverage_name and '항암치료' not in coverage_name`
21. `step4_evidence_search/search_evidence.py:177` - `if '표적항암' in coverage_name`
22. `step4_evidence_search/search_evidence.py:179` - `elif '표적' in coverage_name and '표적항암' not in coverage_name`
23. `step4_evidence_search/search_evidence.py:183` - `if '재진단암' in coverage_name`
24. `step4_evidence_search/search_evidence.py:185` - `elif '재진단' in coverage_name and '재진단암' not in coverage_name`
25. `step4_evidence_search/search_evidence.py:190` - `if '(' in coverage_name and ')' in coverage_name`
26. `step4_evidence_search/search_evidence.py:202` - `if coverage_name.endswith(suffix)`
27. `step1_summary_first/hybrid_layout.py:154` - `if 'coverage_name_raw' in coverage_name.lower()`
28. `step1_summary_first/hybrid_layout.py:158` - `if coverage_name == '담보명' or coverage_name == '보장명'`
29. `step2_sanitize_scope/sanitize.py:93` - `if coverage_name_raw in ['담보명', '보장명', '특약명']`
30. `step2_canonical_mapping/map_to_canonical.py:183` - `if coverage_name_raw in self.mapping_dict`

*(Full list of 58 violations saved to `a4200_1_string_match_violations.json`)*

---

## 🚨 Critical Violations (Decision Logic)

### Violation Type 1: Coverage Type Inference

**Pattern:** `if 'KEYWORD' in coverage_name` → infer coverage type → change behavior

**Examples:**
- `if '진단비' in coverage_name` → this is a diagnosis coverage
- `if '치료비' in coverage_name` → this is a treatment coverage
- `if '입원일당' in coverage_name` → this is a hospitalization coverage

**Why Forbidden:**
- Coverage type should be determined by coverage_code metadata
- String patterns are unreliable ("암진단비" vs "암(4대유사암제외)진단비")
- Creates insurer-specific behavior based on naming conventions

**Correct Approach:**
```python
# ❌ WRONG
if '진단비' in coverage_name:
    coverage_type = 'diagnosis'

# ✅ CORRECT
coverage_metadata = get_metadata_by_code(coverage_code)
coverage_type = coverage_metadata['type']
```

---

### Violation Type 2: Query Variant Generation

**Pattern:** Generate search variants from coverage_name string

**Examples:**
- "암진단비" → ["암진단", "암", "진단비"]
- "4대유사암" → ["유사암(4대)", "유사암"]

**Why Forbidden:**
- Evidence search should use coverage_code-specific queries
- String transformations create inconsistent search behavior
- Meritz A4200_1 and Hanwha A4200_1 search with different queries for SAME coverage

**Correct Approach:**
```python
# ❌ WRONG
def search_evidence(coverage_name):
    if '진단비' in coverage_name:
        query = coverage_name.replace('진단비', '진단')
    return search_fts(query)

# ✅ CORRECT
def search_evidence(coverage_code):
    # Load coverage-code specific query patterns from metadata
    query_patterns = get_query_patterns(coverage_code)
    # e.g., A4200_1 → ["암진단", "유사암제외", "diagnosis", "cancer"]
    return search_fts(query_patterns)
```

---

### Violation Type 3: Insurer-Specific String Bridging

**Pattern:** Transform coverage_name strings to match insurer conventions

**Examples:**
- "4대유사암" ↔ "유사암(4대)"
- "통합암(4대유사암제외)" → "통합암"

**Why Forbidden:**
- This is exactly what coverage_code should solve
- If two insurers use different strings for same coverage, they should have SAME coverage_code
- String transformations are heuristics that fail at edge cases

**Correct Approach:**
```python
# ❌ WRONG
if insurer == 'hanwha' and '4대유사암' in coverage_name:
    normalized = coverage_name.replace('4대유사암', '유사암(4대)')

# ✅ CORRECT
# Both "4대유사암" and "유사암(4대)" map to A4200_1 in SSOT
# No string transformation needed - use coverage_code
```

---

## ✅ Allowed Uses (Not Violations)

### 1. Display/Rendering

```python
# ✅ ALLOWED
def render_coverage_card(coverage):
    print(f"Coverage: {coverage['coverage_name']}")  # Display only
    print(f"Amount: {coverage['amount']}")
```

### 2. Logging

```python
# ✅ ALLOWED
logger.info(f"Processing coverage: {coverage_name_raw}")
```

### 3. Data Quality Checks

```python
# ✅ ALLOWED
if not coverage_name or len(coverage_name) < 2:
    raise ValueError("Coverage name too short")
```

### 4. Header/Noise Filtering

```python
# ✅ ALLOWED (marginal)
if coverage_name in ['담보명', '보장명', '계']:
    continue  # Skip header row
```

### 5. SSOT Lookup (Step2 Only)

```python
# ✅ ALLOWED (if using correct SSOT file)
coverage_code = ssot_mapping[coverage_name]
```

---

## 📊 Impact Assessment

### Severity by File

| File | Severity | Impact | Recommendation |
|------|----------|--------|----------------|
| `step4_evidence_search/` | 🔴 CRITICAL | Evidence search inconsistent across insurers | Redesign with coverage_code metadata |
| `step1_summary_first/` | ⚠️ MEDIUM | PDF parsing filters | Acceptable (noise filtering) |
| `step2_sanitize/` | ⚠️ LOW | Data quality checks | Acceptable (sanity checks) |
| `step2_canonical_mapping/` | ⚠️ MEDIUM | Name → code lookup | Acceptable (but use correct SSOT file) |
| `step8_render/` | ⚠️ LOW | UI rendering logic | Acceptable (display only) |

### Overall Impact on A4200_1

**HIGH RISK:**

1. **Evidence search (step4_evidence_search/)** uses different query variants for Meritz vs Hanwha A4200_1
   - Meritz: "암진단비(유사암제외)" → variants include "암진단(유사암제외)"
   - Hanwha: "암(4대유사암제외)진단비" → variants include "유사암제외", "암진단"
   - **Result:** Different evidence may be found for the same coverage_code

2. **Inconsistent comparison** if evidence quality differs between insurers

3. **Fragile to name changes** - if insurer renames coverage in PDF, logic breaks

---

## 📝 Recommendations

### 1. Refactor Evidence Search (URGENT)

**File:** `pipeline/step4_evidence_search/search_evidence.py`

**Current:**
```python
def generate_query_variants(coverage_name: str) -> List[str]:
    variants = [coverage_name]
    if '진단비' in coverage_name:  # STRING PATTERN
        variants.append(coverage_name.replace('진단비', '진단'))
    return variants
```

**Required:**
```python
def generate_query_variants(coverage_code: str) -> List[str]:
    # Load from metadata (NOT from string patterns)
    metadata = get_coverage_metadata(coverage_code)
    return metadata['search_keywords']

# Metadata example:
# {
#   'A4200_1': {
#     'search_keywords': ['암진단', '유사암제외', '진단비', 'cancer diagnosis'],
#     'type': 'diagnosis',
#     'category': 'cancer'
#   }
# }
```

---

### 2. Create Coverage Metadata Store

**New File:** `data/coverage_metadata/coverage_types.json`

```json
{
  "A4200_1": {
    "type": "diagnosis",
    "category": "cancer",
    "search_keywords": ["암진단", "암", "진단비", "유사암제외", "cancer", "diagnosis"],
    "exclusions_keywords": ["유사암", "제외", "제자리암", "경계성"],
    "insurer_variants": {
      "N01": "암진단비(유사암제외)",
      "N02": "암(4대유사암제외)진단비"
    }
  }
}
```

---

### 3. Enforce No String Matching in CI

**Add pre-commit hook:**
```bash
#!/bin/bash
# check_string_matching.sh

if grep -r "if.*coverage_name\|coverage_name.*==" pipeline/*.py; then
    echo "ERROR: String matching on coverage_name detected"
    exit 1
fi
```

---

### 4. Add Coverage Code Validation

**Every function using coverage data:**
```python
def process_coverage(coverage):
    # Validate coverage_code exists
    if 'coverage_code' not in coverage:
        raise ValueError("coverage_code missing")

    if not is_valid_coverage_code(coverage['coverage_code']):
        raise ValueError(f"Invalid coverage_code: {coverage['coverage_code']}")
```

---

## 🔗 Related Documents

- `COVERAGE_CANONICALIZATION_V2.md` - String matching ban constitutional rule
- `A4200_1_SSOT_ROW_SNAPSHOT.md` - SSOT definition for A4200_1
- `A4200_1_STEP1_TARGET_PLAN_TRACE.md` - Step1 SSOT violation
- `A4200_1_PIPELINE_CONSISTENCY_REPORT.md` - Overall pipeline audit

---

## 📝 Summary

**Total Violations:** 58
**Critical Files:** 1 (`step4_evidence_search/`)
**Severity:** 🔴 CRITICAL for evidence search, ⚠️ MEDIUM for others

**Key Findings:**
1. Evidence search uses coverage_name string patterns → inconsistent behavior for same coverage_code
2. Coverage type inferred from name strings → should use coverage_code metadata
3. Insurer-specific string transformations → violates coverage-code first principle

**Verdict:** ❌ FAIL - Pipeline uses coverage_name strings for decision logic

**Required Action:** Refactor evidence search to use coverage_code metadata, not coverage_name string patterns

---

**END OF SCAN**
