# STEP NEXT-55: Samsung Profile Column Detection Bug + Profile Lock Mechanism

**Date**: 2026-01-01
**Status**: ✅ **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

**Problem**: Samsung Step1 extraction produces only **17 coverages** instead of expected **40-45** (historical baseline).

**Root Cause**: Profile Builder V3 incorrectly detected `column_map.coverage_name = 0`, when the actual coverage name column is `1`.

**Impact**:
- **62% coverage loss**: 17/45 rows extracted (28 rows filtered out)
- Rows with empty/category labels in column 0 are skipped by extractor's row filters

**Solution**: Profile Builder needs category column detection + signature lock mechanism to prevent regression.

---

## Evidence Trail

### 1. Historical Baseline

| Source | Date | Samsung Coverage Count |
|--------|------|------------------------|
| STEP NEXT-44B Quality Report | 2025-12-31 | 61/62 (98.4%) |
| STEP NEXT-41S SSOT Snapshot | 2025-12-31 | 42 |
| INSURER_CODE_AUDIT.md | 2025 | 40 |
| Current Step1 Output | 2026-01-01 | **17** ❌ |

**Regression**: 40-42 → 17 (58% loss)

### 2. Profile Analysis

**File**: `data/profile/samsung_proposal_profile_v3.json`

**Signature 1** (Page 2, Table 0):
```json
{
  "page": 2,
  "table_index": 0,
  "row_count": 31,
  "col_count": 5,
  "header_row_index": 1,
  "column_map": {
    "coverage_name": 0,  // ❌ WRONG!
    "coverage_amount": 2,
    "premium": 3,
    "period": 4
  },
  "evidence": {
    "sample_rows": [
      "진단 | 보험료 납입면제대상Ⅱ | 10만원 | 189 | 20년납 100세만기",
      " | 암 진단비(유사암 제외) | 3,000만원 | 40,620 | 20년납 100세만기",
      " | 유사암 진단비(기타피부암)(1년50%) | 600만원 | 1,440 | 20년납 100세만기"
    ]
  }
}
```

**Analysis**:
- Column 0: `"진단"`, `" "`, `" "` → Category label / empty cells
- Column 1: `"보험료 납입면제대상Ⅱ"`, `"암 진단비(유사암 제외)"`, ... → **Actual coverage names**

**Correct column_map**:
```json
{
  "category_column": 0,       // NEW: Category label column (optional)
  "coverage_name": 1,          // ✅ CORRECT
  "coverage_amount": 2,
  "premium": 3,
  "period": 4
}
```

### 3. Extraction Impact

**Current Extraction** (coverage_name from column 0):

```python
# Row 1: col[0] = "진단" → length=2, but category keyword → SKIPPED (if we had category filter)
# Row 2: col[0] = " " → empty → SKIPPED
# Row 3: col[0] = " " → empty → SKIPPED
# Row 4: col[0] = "수술" → category → SKIPPED
# ...
# Result: 28/45 rows skipped (empty or category labels in column 0)
```

**Expected Extraction** (coverage_name from column 1):

```python
# Row 1: col[1] = "보험료 납입면제대상Ⅱ" → valid coverage name → EXTRACTED ✅
# Row 2: col[1] = "암 진단비(유사암 제외)" → valid coverage name → EXTRACTED ✅
# Row 3: col[1] = "유사암 진단비(기타피부암)(1년50%)" → valid coverage name → EXTRACTED ✅
# ...
# Result: ~45 rows extracted
```

### 4. Step1 Output Verification

**First 5 extracted coverage names** (from column 1, not 0!):
```
1. 보험료 납입면제대상Ⅱ
2. 기타 심장부정맥 진단비(1년50%)
3. 특정3대심장질환 진단비(1년50%)
4. 골절 진단비(치아파절(깨짐, 부러짐) 제외)
5. 화상 진단비
```

**Observation**: These names are NOT from column 0 (which has category labels). They're from column 1.

**Question**: How did these 17 rows get extracted if column_map says coverage_name=0?

**Hypothesis**:
1. Extractor reads column 0 (category labels)
2. Most rows have empty/short values → SKIPPED
3. A few rows have longer category labels (e.g., `"기타심장부정맥"`) → PASS min_length filter
4. **OR** — extractor has fallback logic that tries other columns when column 0 is empty?

Let me verify by checking the extractor code.

---

## Code-Level Root Cause

### File: `pipeline/step1_summary_first/profile_builder_v3.py`

**Function**: `_detect_column_map()` (Line 489-547)

**Column Detection Logic** (Line 528-533):
```python
# Coverage name column
if any(kw in cell_normalized for kw in self.COVERAGE_KEYWORDS):
    # Apply offset for KB case
    if column_map['has_row_number_column'] and idx == 0:
        # This is the row-number column header, skip
        continue
    column_map['coverage_name'] = idx  # ❌ First match wins
```

**Samsung Header Row**:
```python
["담보가입현황", "", "가입금액", "보험료(원)", "납입기간/보험기간"]
```

**Detection Result**:
- Column 0: `"담보가입현황"` contains `"담보"` (COVERAGE_KEYWORD) → **coverage_name = 0** ❌

**Issue**:
- The header keyword `"담보가입현황"` is a section title, not a column header
- The actual coverage name column (1) has an empty header `""` → not detected

**Why This Happens**:
- Samsung's table has a **merged cell** layout:
  - Column 0: Category column (no header, or merged header)
  - Column 1: Coverage name column (empty header cell after merge)
- Profile builder detects the merged header `"담보가입현황"` as the coverage name column

---

## Why 17 Rows Were Extracted (Mystery Solved)

Let me check if the extractor has fallback logic:

**File**: `pipeline/step1_summary_first/extractor_v3.py`

**Function**: `_extract_fact_from_row()` (Line 425-466)

**Line 433-440**:
```python
# Get coverage name (accounting for row-number column)
coverage_col = column_map.get("coverage_name")
if coverage_col is None or coverage_col >= len(row):
    return None

coverage_name_raw = str(row[coverage_col]).strip() if row[coverage_col] else ""
if not coverage_name_raw:
    return None
```

**No fallback logic**. Extractor strictly uses `column_map.coverage_name`.

**Then how did 17 rows get extracted with column 0?**

Let me check the actual column 0 values in the Samsung PDF table:

```python
# Sample row data (from profile evidence):
# Row 1: ["진단", "보험료 납입면제대상Ⅱ", "10만원", "189", "20년납 100세만기"]
# Row 2: [" ", "암 진단비(유사암 제외)", "3,000만원", "40,620", "20년납 100세만기"]
# Row 3: [" ", "유사암 진단비(기타피부암)(1년50%)", "600만원", "1,440", "20년납 100세만기"]
```

**Wait!** Looking at the actual extracted coverage names again:
```
보험료 납입면제대상Ⅱ
기타 심장부정맥 진단비(1년50%)
특정3대심장질환 진단비(1년50%)
```

These are definitely from **column 1**, not column 0.

**Hypothesis 2**: The column map is wrong in the profile, but the extractor is somehow using column 1?

**Let me check if there's a hybrid extraction path for Samsung**.

**Samsung Profile**:
```json
"variant_signatures": []  // Empty!
```

So Samsung uses `primary_signatures` → `standard_first` mode (not hybrid).

**But wait** — Samsung might auto-trigger hybrid if >30% empty coverage names!

Let me check the extractor's auto-trigger logic:

**File**: `extractor_v3.py` Line 208-252

```python
def _should_trigger_hybrid(self, signatures: List[Dict]) -> bool:
    """Check if we should trigger hybrid extraction based on empty coverage ratio"""
    with pdfplumber.open(self.pdf_path) as pdf:
        total_data_rows = 0
        empty_coverage_rows = 0

        for sig in signatures:
            coverage_col = column_map.get("coverage_name")
            if coverage_col is None:
                continue

            data_rows = table[header_row_idx + 1:]
            for row in data_rows:
                if coverage_col < len(row):
                    total_data_rows += 1
                    coverage_text = str(row[coverage_col]).strip() if row[coverage_col] else ""
                    if not coverage_text or coverage_text.lower() in ["none", "null", ""]:
                        empty_coverage_rows += 1

        # Auto-trigger: if >30% coverage names are empty in raw table data
        if total_data_rows > 0:
            empty_ratio = empty_coverage_rows / total_data_rows
            return empty_ratio > 0.30
```

**For Samsung**:
- column_map.coverage_name = 0
- Column 0 has many empty cells (category column, only first row of each category has label)
- Empty ratio = ~60-70% (way above 30%)
- **Auto-trigger: YES** → switches to hybrid extraction!

**Mystery solved!**

The extractor:
1. Tries standard extraction with coverage_name=0
2. Detects >30% empty → auto-triggers hybrid
3. Hybrid extractor reads text blocks from PDF → extracts coverage names correctly (from column 1 position)
4. But hybrid only returns rows with complete data (amount + premium + period)
5. Result: 17 rows with complete data, 28 rows missing premium/amount → SKIPPED by hybrid

---

## Root Cause Summary

| Step | Issue | Result |
|------|-------|--------|
| **Profile Builder** | Detects merged header `"담보가입현황"` → coverage_name=0 ❌ | Wrong column map |
| **Extractor (Standard)** | Tries column 0 → 60% empty → Auto-triggers hybrid ✅ | Switches to hybrid mode |
| **Extractor (Hybrid)** | Parses text blocks → extracts coverages correctly ✅ | Gets coverage names right |
| **Hybrid Filter** | Only rows with amount/premium pattern → PASS | **17/45 rows** (rows without premium skipped) |

**Final Root Cause**:
1. **Profile Builder Bug**: Detects wrong coverage_name column (0 instead of 1)
2. **Hybrid Row Loss**: Hybrid extractor filters out rows without amount/premium patterns

---

## Why This Causes 40 → 17 Regression

Looking at Samsung's table structure:

```
| 진단 | 보험료 납입면제대상Ⅱ | 10만원 | 189 | 20년납 100세만기 | ← Has premium → EXTRACTED
|      | 암 진단비(유사암 제외) | 3,000만원 | 40,620 | 20년납 100세만기 | ← Has premium → EXTRACTED
|      | 유사암 진단비(기타피부암)(1년50%) | 600만원 | 1,440 | 20년납 100세만기 | ← Has premium → EXTRACTED
| 수술 | 기타피부암 수술비 | 30만원 | 52 | 20년납 100세만기 | ← Has premium → EXTRACTED
|      | 제자리암 수술비 | 30만원 |  |  | ← NO premium → SKIPPED ❌
|      | 경계성종양 수술비 | 30만원 |  |  | ← NO premium → SKIPPED ❌
```

**Pattern**:
- Some rows have amount but **no premium** (e.g., grouped coverages with shared premium)
- Hybrid's `parse_summary_row_text()` requires both amount AND premium in pattern:
  ```python
  pattern = r"^(\d+)?\s*(.+?)\s+(\d+[천백만억]*원)\s+([\d,]+)\s+(.+)$"
  #                                            Amount ^^^^   Premium ^^^^
  ```

**Result**:
- Rows with premium (17) → EXTRACTED
- Rows without premium (28) → SKIPPED

---

## Fix Strategy

### Fix 1: Profile Builder Category Column Detection

**Add logic to detect category columns** (columns with repetitive short labels):

```python
def _is_category_column(self, table: List[List[Any]], col_idx: int) -> bool:
    """
    Detect if a column is a category column (repetitive labels like '진단', '수술', '입원')

    Heuristics:
    1. >50% of cells are empty
    2. Non-empty cells are short (≤4 chars)
    3. High repetition rate (≤10 unique values in 20+ rows)
    """
    data_rows = table[3:]  # Skip header rows
    col_values = [str(row[col_idx]).strip() if col_idx < len(row) and row[col_idx] else "" for row in data_rows]

    if not col_values:
        return False

    # Criterion 1: >50% empty
    empty_count = sum(1 for v in col_values if not v)
    empty_ratio = empty_count / len(col_values)

    # Criterion 2: Non-empty cells are short
    non_empty = [v for v in col_values if v]
    avg_length = sum(len(v) for v in non_empty) / len(non_empty) if non_empty else 0

    # Criterion 3: High repetition
    unique_count = len(set(non_empty))
    repetition_ratio = unique_count / len(non_empty) if non_empty else 1

    is_category = (
        empty_ratio > 0.5 and
        avg_length <= 4 and
        repetition_ratio < 0.5  # <50% unique (high repetition)
    )

    return is_category
```

**Apply in `_detect_column_map()`**:

```python
# Coverage name column
if any(kw in cell_normalized for kw in self.COVERAGE_KEYWORDS):
    # Check if this is a category column
    if self._is_category_column(table, idx):
        logger.debug(f"Column {idx} looks like category column, skipping")
        continue

    column_map['coverage_name'] = idx
```

### Fix 2: Profile Signature Lock

To prevent **regression** (results changing across runs), implement signature lock:

**Add to profile schema**:

```json
{
  "locked_signature": {
    "page": 2,
    "table_index": 0,
    "bbox_hash": "sha1(x0,y0,x1,y1)",
    "column_map_hash": "sha1(coverage_name:1,amount:2,premium:3)",
    "extraction_mode": "standard_first",
    "mode_lock": true
  },
  "signature_lock_reason": "STEP NEXT-55: Samsung table structure confirmed"
}
```

**Extractor enforcement**:

```python
if profile.get("signature_lock_reason"):
    locked_sig = profile["locked_signature"]

    # Verify signature match
    if current_page != locked_sig["page"] or current_table_idx != locked_sig["table_index"]:
        raise RuntimeError(
            f"{insurer}: Profile signature mismatch. "
            f"Expected page={locked_sig['page']}, table={locked_sig['table_index']}, "
            f"but current extraction found different signature. "
            f"Run profile_builder_v3 to regenerate profile."
        )

    # Enforce extraction mode
    if locked_sig["mode_lock"]:
        extraction_mode = locked_sig["extraction_mode"]
        # Do NOT auto-trigger hybrid if mode_lock=true
```

### Fix 3: Hybrid Extractor Row Pattern (Optional)

To handle rows without premium, relax hybrid pattern:

**Current**:
```python
pattern = r"^(\d+)?\s*(.+?)\s+(\d+[천백만억]*원)\s+([\d,]+)\s+(.+)$"
# Requires: amount AND premium AND period
```

**Relaxed**:
```python
pattern = r"^(\d+)?\s*(.+?)\s+(\d+[천백만억]*원)(?:\s+([\d,]+))?(?:\s+(.+))?$"
# Requires: amount only (premium and period are optional)
```

**Issue**: This may introduce false positives (fragments with just amount).

**Better approach**: Keep strict pattern, but allow missing premium if previous row had premium (grouped coverage logic).

---

## Recommended Fix Priority

1. **P0: Fix Profile Builder** — Category column detection (Fix 1)
   - Impact: Samsung profile regenerated with correct column_map
   - Timeline: Immediate

2. **P1: Implement Signature Lock** — Prevent regression (Fix 2)
   - Impact: Samsung extraction result stable across runs
   - Timeline: Before next insurer addition

3. **P2: Hybrid Pattern Relaxation** — Optional (Fix 3)
   - Impact: Recover rows without premium (if needed)
   - Timeline: Only if P0+P1 don't fully recover 40+ rows

---

## Impact Assessment

### Before Fix

| Metric | Value |
|--------|-------|
| Profile column_map.coverage_name | 0 (wrong) |
| Extraction mode | hybrid (auto-triggered) |
| Rows extracted | 17 |
| Expected rows | 40-45 |
| Coverage loss | 58% |

### After Fix (Estimated)

| Metric | Value |
|--------|-------|
| Profile column_map.coverage_name | 1 (correct) |
| Extraction mode | standard (no auto-trigger) |
| Rows extracted | 42-45 ✅ |
| Expected rows | 40-45 |
| Coverage loss | 0% |

---

## Reproducibility

### Current Behavior

```bash
# 1. Check current profile
jq '.summary_table.primary_signatures[0].column_map.coverage_name' \
  data/profile/samsung_proposal_profile_v3.json
# Output: 0 (wrong)

# 2. Check extraction count
wc -l data/scope_v3/samsung_step1_raw_scope_v3.jsonl
# Output: 17

# 3. Check expected count
jq '.summary_table.primary_signatures[0].row_count' \
  data/profile/samsung_proposal_profile_v3.json
# Output: 31 (page 2)
jq '.summary_table.primary_signatures[1].row_count' \
  data/profile/samsung_proposal_profile_v3.json
# Output: 18 (page 3)
# Expected data rows: (31-2) + (18-2) = 45
```

---

## Definition of Done

- [x] Root cause identified: Profile builder detects wrong column (0 vs 1)
- [x] Regression cause identified: Hybrid auto-trigger + row filtering
- [x] Fix strategy defined: Category column detection + signature lock
- [ ] Code fix implemented (profile_builder_v3.py)
- [ ] Profile regenerated for Samsung
- [ ] Step1 re-run for Samsung
- [ ] Verification: 40+ rows extracted
- [ ] Signature lock implemented
- [ ] Test case: Samsung stability test (3 identical runs)

---

## Next Steps

1. Implement category column detection in profile_builder_v3.py
2. Regenerate Samsung profile
3. Re-run Step1 extraction for Samsung
4. Verify output: 40+ coverage rows
5. Implement signature lock mechanism
6. Run Samsung stability test (3 runs, verify identical results)

---

## Audit Trail

- **Issue Discovery**: 2026-01-01 (17 rows vs 40+ expected)
- **Root Cause Analysis**: 2026-01-01 (this document)
- **Profile Analysis**: samsung_proposal_profile_v3.json (column_map.coverage_name=0 wrong)
- **Code Analysis**: profile_builder_v3.py `_detect_column_map()`, extractor_v3.py `_should_trigger_hybrid()`
- **Fix Implementation**: TBD
