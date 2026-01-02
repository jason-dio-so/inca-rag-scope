# STEP NEXT-68C Phase C-3: Profile Gaps & Extractor Generalization Analysis

**Generated**: 2026-01-02 (Auto-generated)

## Executive Summary

**Root Cause**: 6 out of 10 axes have `detail_table.exists=false` in their profiles, preventing Step5's `customer_view` builder from extracting proposal DETAIL descriptions.

**Impact**:
- Samsung: 93.5% ✅ (has detail_table)
- Hanwha: 81.2% ✅ (has detail_table)
- DB under40/over41: 70.0% ⚠️ (has detail_table, but 9 missing)
- **Heungkuk, Hyundai, KB, Lotte (M/F), Meritz: 0.0% ❌ (NO detail_table)**

---

## Current State Matrix

| Axis | detail_table.exists | KPI-1 (%) | Status | Action Required |
|------|---------------------|-----------|--------|-----------------|
| samsung | ✅ true | 93.5 | ✅ PASS | None |
| hanwha | ✅ true | 81.2 | ✅ PASS | None |
| db_under40 | ✅ true | 70.0 | ⚠️ FAIL | Phase B (deep-dive 9 missing) |
| db_over41 | ✅ true | 70.0 | ⚠️ FAIL | Phase B (deep-dive 9 missing) |
| heungkuk | ❌ false | 0.0 | ❌ FAIL | **Profile rebuild + extractor** |
| hyundai | ❌ false | 0.0 | ❌ FAIL | **Profile rebuild + extractor** |
| kb | ❌ false | 0.0 | ❌ FAIL | **Profile rebuild + extractor** |
| lotte_male | ❌ false | 0.0 | ❌ FAIL | **Profile rebuild + extractor** |
| lotte_female | ❌ false | 0.0 | ❌ FAIL | **Profile rebuild + extractor** |
| meritz | ❌ false | 0.0 | ❌ FAIL | **Profile rebuild + extractor** |

---

## Profile Patterns Analysis

### Pattern 1: DB-style (exists, working at 70%)

**Profile schema**:
```json
{
  "detail_table": {
    "exists": true,
    "pages": [7, 8, 9],
    "columns": {
      "coverage_name_and_desc": ["가입담보[만기/납기]"],
      "coverage_amount": ["가입금액(만원)"],
      "premium": ["보험료(원)"],
      "description": ["보장(보상)내용"]
    },
    "structure": {
      "row_count": "19-24 rows per page",
      "col_count": "4 columns",
      "header_pattern": "가입담보[만기/납기] | 가입금액(만원) | 보험료(원) | 보장(보상)내용"
    }
  }
}
```

**Characteristics**:
- Explicit `description` column ("보장(보상)내용")
- Clean 4-column table
- Coverage name in col 0, description in col 3
- Works with current extractor

**Current issues** (db_under40/over41):
- 9 out of 30 coverages missing (30%)
- Failure pattern: "A1100 (질병사망)", "A1300 (상해사망)", "A3300_1", "A4200_1 (암진단비)", "A4210 (유사암진단비)", etc.
- All failures show: "Evidence snippets contain TOC/lists, not descriptive benefit text"
- **Hypothesis**: These 9 coverages exist in a DIFFERENT table structure (possibly summary table on p.4) that doesn't have "보장(보상)내용" column

### Pattern 2: Samsung-style (exists, working at 93.5%)

**Profile schema**:
```json
{
  "detail_table": {
    "exists": true,
    "pages": [5, 6],
    "table_name_candidates": ["담보명", "보장내용"],
    "columns": {
      "coverage_name": ["담보명"],
      "description": ["보장내용"]
    },
    "structure": {
      "type": "merged_header_multi_col",
      "header_spans_2_cols": true,
      "data_in_col_plus_1": true
    }
  }
}
```

**Characteristics**:
- Header spans 2-3 columns (Samsung pattern)
- "담보명" + "보장내용" merged headers
- Requires special parsing (merged cell handling)

### Pattern 3: Hanwha-style (exists, working at 81.2%)

**Profile schema** (similar to Samsung, multi-row headers):
```json
{
  "detail_table": {
    "exists": true,
    "pages": [8, 9, 10],
    "columns": {
      "coverage_name": ["담보명"],
      "description": ["보장내용"]
    },
    "structure": {
      "type": "multi_row_header",
      "header_rows": 2,
      "merged_cells": true
    }
  }
}
```

**Characteristics**:
- Multi-row header + merged cells
- 6 failures are all `A4210 (유사암진단비)` variants (likely missing from detail table entirely)

### Pattern 4: Missing profile (0% coverage)

**Current state** (heungkuk/hyundai/kb/lotte/meritz):
```json
{
  "detail_table": {
    "exists": false,
    "pages": []
  }
}
```

**Required action**:
1. Manually inspect PDF to locate detail tables
2. Build profile schema for each insurer
3. Extend detail_extractor to handle new patterns

---

## Generalization Strategy (Constitutional Rule: Profile-Driven)

### Rule 1: NO insurer-specific `if` branches in extractor

**Allowed**:
```python
# Extractor reads profile-driven config
if profile.detail_table.structure.type == "merged_header_multi_col":
    # Apply merged-header parsing logic
elif profile.detail_table.structure.type == "explicit_description_column":
    # Apply 4-column DB-style parsing
```

**Prohibited**:
```python
# NEVER DO THIS:
if insurer == "heungkuk":
    # Heungkuk-specific logic
```

### Rule 2: Profile schema extensions needed

Add to `detail_table` schema:
```json
{
  "detail_table": {
    "exists": true,
    "pages": [7, 8],
    "structure": {
      "type": "explicit_description_column" | "merged_header_multi_col" | "multi_row_header" | "coverage_name_and_desc_single_cell",
      "description_extraction_mode": "dedicated_column" | "merged_cell_next_token" | "same_cell_after_name"
    },
    "columns": {
      "coverage_name": ["담보명", "가입담보"],
      "coverage_name_and_desc": ["가입담보[만기/납기]"],  // for DB-style
      "description": ["보장내용", "보장(보상)내용"],
      "coverage_amount": ["가입금액", "가입금액(만원)"],
      "premium": ["보험료", "보험료(원)"]
    },
    "fallback_strategy": {
      "if_description_empty": "search_next_cell_same_row",
      "if_description_is_toc": "filter_out",
      "if_description_too_short": "search_adjacent_rows"
    }
  }
}
```

---

## Phase C-4 Execution Plan (Profile Rebuild + Extractor Extension)

### Step C-4-1: Manual PDF inspection (required for 6 axes)

**For each axis** (heungkuk, hyundai, kb, lotte_male, lotte_female, meritz):

1. Open `data/sources/insurers/{insurer}/가입설계서/*.pdf`
2. Locate detail table pages (search for "보장내용", "보장(보상)내용", "담보명")
3. Identify table structure:
   - Column count
   - Header row(s)
   - Coverage name column index
   - Description column index (or merged cell pattern)
4. Document in profile

**Expected output**: Updated `data/profile/{insurer}_proposal_profile_v3.json` with `detail_table.exists=true`

### Step C-4-2: Extend detail_extractor.py (generalized patterns)

**File**: `pipeline/step1_summary_first/detail_extractor.py`

**Add pattern handlers**:

1. **Pattern: explicit_description_column** (DB-style, already working)
   - Column 3 = "보장(보상)내용"
   - Extract as-is

2. **Pattern: merged_header_multi_col** (Samsung-style, already working)
   - Header spans 2+ cols
   - Description in col+1 or col+2

3. **Pattern: multi_row_header** (Hanwha-style, already working)
   - Header rows = 2+
   - Merged cells in header

4. **NEW Pattern: coverage_name_and_desc_single_cell** (potential for some insurers)
   - Coverage name and description in same cell
   - Description follows name (possibly after newline or specific token)
   - Requires cell-internal splitting logic

5. **NEW Pattern: no_description_column** (fallback)
   - No explicit description column found
   - Search adjacent cells, or skip with "명시 없음"

**Filter rules** (apply AFTER extraction):
- Drop if description matches TOC patterns: `^\d+[-\.]\d+`, `^특별약관$`, `^담보명$`, `^보장내용$`, `^\d+\.$`
- Drop if description length < 10 chars (likely noise)
- Drop if description == coverage_name (duplicate)

### Step C-4-3: Rebuild profiles for 6 missing axes

**Command** (for each axis):
```bash
python -m pipeline.step1_summary_first.profile_builder_v3 \
  --manifest data/sources/proposal/MANIFEST.yaml \
  --insurer heungkuk \
  --rebuild-detail-table
```

**Note**: `--rebuild-detail-table` flag may need to be added to profile_builder_v3.py to force manual profile editing assistance.

Alternatively, manually edit profiles based on PDF inspection (C-4-1).

### Step C-4-4: Test with single axis (heungkuk)

```bash
# Step1: Extract with new profile
python -m pipeline.step1_summary_first.extractor_v3 \
  --manifest data/sources/proposal/MANIFEST.yaml \
  --insurer heungkuk

# Step2: Canonical mapping
python -m pipeline.step2_canonical_mapping.run --insurer heungkuk

# Step5: Build cards
python -m pipeline.step5_build_cards.build_cards --insurer heungkuk

# Verify KPI
python tools/report_detail_kpi_all.py
# Expected: heungkuk KPI-1 > 0% (ideally 80%+)
```

---

## DB Deep-Dive (Phase B) - Separate Track

**Separate from C-4**: DB axes already have `detail_table.exists=true`, but 30% fail rate.

**Root cause hypothesis**:
- The 9 missing coverages (A1100, A1300, A3300_1, A4200_1, A4210, A4299_1, A4301_1, A5300) may be in:
  1. Summary table (p.4) with NO description column
  2. Different detail table with different structure
  3. Actually missing from detail tables (only exist in summary)

**Action** (Phase B):
1. Check db_under40 PDF pages 4, 7, 8, 9 manually
2. Identify where A1100 (질병사망) appears
3. If it's in summary table (p.4) with no description → expected behavior (Step5 should fall back to "명시 없음")
4. If it's in a DIFFERENT detail table → extend profile to multi-table support

---

## DoD (Phase C-3 Complete)

✅ **Completed**:
1. KPI audit report generated (`STEP_NEXT_68C_DETAIL_COVERAGE_TABLE.md`)
2. Root cause identified: 6 axes missing `detail_table` profiles
3. Profile pattern analysis documented (4 patterns identified)
4. Generalization strategy defined (profile-driven, no insurer-specific branches)
5. Phase C-4 execution plan written

**Next**: Phase C-4 (profile rebuild + extractor extension)

---

## References

- KPI Report: `docs/audit/STEP_NEXT_68C_DETAIL_COVERAGE_TABLE.md`
- Profiles: `data/profile/*_proposal_profile_v3.json`
- Extractor: `pipeline/step1_summary_first/detail_extractor.py`
- Builder: `pipeline/step1_summary_first/profile_builder_v3.py`
