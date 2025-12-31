# STEP NEXT-28 — KB Scope Recovery

**Recovery Date**: 2025-12-30
**Method**: Regenerate KB scope.csv from proposal PDF + Re-apply STEP NEXT-27 suffix-normalized matching

---

## 1. Problem Statement

**STEP NEXT-27 Result**: KB showed 0 / 2 VALID_CASE instances recovered

**Hypothesis**: Root cause is NOT logic failure, but **corrupted KB scope.csv** (input file collapse)

**Goal**: Prove hypothesis + recover KB raw scope + re-apply STEP NEXT-27 to KB

---

## 2. Evidence Snapshot (BEFORE)

### 2.1 File Line Counts

```bash
$ wc -l data/scope/kb_scope.csv data/scope/kb_scope_mapped.csv data/scope/kb_scope_mapped.sanitized.csv
       4 data/scope/kb_scope.csv
       4 data/scope/kb_scope_mapped.csv
       3 data/scope/kb_scope_mapped.sanitized.csv
      11 total
```

**Verdict**: ❌ KB scope.csv is **collapsed** (only 4 lines, including header = 3 data rows)

---

### 2.2 KB scope.csv Content

```bash
$ head -20 data/scope/kb_scope.csv
coverage_name_raw,insurer,source_page
,kb,2
(갱신보장:),kb,4
환급률 : .%,kb,4
```

**Verdict**: ❌ All 3 rows are **garbage** (empty string, parentheses-only, premium rate)

**No meaningful coverage names** in KB scope.csv

---

### 2.3 KB File Sizes

```bash
$ ls -lh data/scope/*kb* | head -5
-rw-r--r--  1 cheollee  staff   100K Dec 30 14:15 data/scope/kb_filtered_out.jsonl
-rw-r--r--  1 cheollee  staff   132B Dec 30 18:52 data/scope/kb_scope_filtered_out.jsonl
-rw-r--r--  1 cheollee  staff   204B Dec 30 18:51 data/scope/kb_scope_mapped.csv
-rw-r--r--  1 cheollee  staff   165B Dec 30 18:52 data/scope/kb_scope_mapped.sanitized.csv
-rw-r--r--  1 cheollee  staff    89B Dec 30 14:15 data/scope/kb_scope.csv
```

**Verdict**: kb_scope.csv = 89 bytes (minimal file size confirms corruption)

---

### 2.4 Target Coverages in coverage_cards.jsonl (SSOT)

```bash
$ grep -n "혈전용해치료비" data/compare/kb_coverage_cards.jsonl | head -2
35:{"insurer": "kb", "coverage_name_raw": "혈전용해치료비Ⅱ(최초1회한)(뇌졸중)", "coverage_code": null, "coverage_name_canonical": null, "mapping_status": "unmatched", ...}
36:{"insurer": "kb", "coverage_name_raw": "혈전용해치료비Ⅱ(최초1회한)(특정심장질환)", "coverage_code": null, "coverage_name_canonical": null, "mapping_status": "unmatched", ...}
```

**Verdict**: ✅ Target coverages **exist** in coverage_cards.jsonl (SSOT)

**Implication**: KB data was successfully generated **upstream** (Step1/2/5 in past), but current kb_scope.csv is corrupted

---

### 2.5 Target Coverages in kb_scope*.csv (INPUT files)

```bash
$ grep -n "혈전용해치료비" data/scope/kb_scope*.csv 2>/dev/null | head -10
(no output)
```

**Verdict**: ❌ Target coverages **NOT FOUND** in any kb_scope*.csv file

---

## 3. KB Scope Producer Identification

### 3.1 Code Search for Scope Producer

```bash
$ rg -n "scope\.csv.*output|output.*scope\.csv|to_csv.*scope" pipeline
/Users/cheollee/inca-rag-scope/pipeline/step1_extract_scope/run.py:132:        output_path = self.output_dir / f"{self.insurer}_scope.csv"
```

**Producer Identified**: `pipeline/step1_extract_scope/run.py`

**Entry Point**: Line 132 — `save_to_csv()` method writes to `data/scope/{insurer}_scope.csv`

**CLI Command**:
```bash
python -m pipeline.step1_extract_scope.run --insurer kb
```

---

### 3.2 Verify KB Proposal PDF Exists

```bash
$ find data/sources/insurers/kb -name "*.pdf" 2>/dev/null
data/sources/insurers/kb/상품요약서/KB_상품요약서.pdf
data/sources/insurers/kb/약관/KB_약관.pdf
data/sources/insurers/kb/사업방법서/KB_사업방법서.pdf
data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf
```

**Verdict**: ✅ KB proposal PDF exists at `data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf`

**Implication**: KB scope regeneration is **feasible** (input file exists)

---

## 4. KB Scope Regeneration (EXECUTION)

### 4.1 Run Step1 Extract Scope

**Command**:
```bash
python -m pipeline.step1_extract_scope.run --insurer kb
```

**Output**:
```
[Step 1] Processing: KB_가입설계서.pdf
  - Extracted 45 coverages (unique: 45)

[Step 1] Initial extraction: 45 coverages

[Step 1] Final result:
  - Total PDFs processed: 1
  - Unique coverages: 45
  - Pages: [2, 3, 4]
  - Output: /Users/cheollee/inca-rag-scope/data/scope/kb_scope.csv

✓ OK: insurer=kb extracted=45 declared=N/A pages=[2, 3, 4]
```

**Result**: ✅ **SUCCESS** — KB scope regenerated with **45 coverages** (up from 3 garbage rows)

---

### 4.2 Verify Regenerated kb_scope.csv

**Line Count**:
```bash
$ wc -l data/scope/kb_scope.csv
      46 data/scope/kb_scope.csv
```

**Result**: ✅ **46 lines** (45 coverages + 1 header) — **10x increase** from 4 lines

---

### 4.3 Verify Target Coverages in Regenerated Scope

```bash
$ grep -n "혈전용해치료비" data/scope/kb_scope.csv
34:혈전용해치료비Ⅱ(최초1회한)(특정심장질환),kb,3
35:혈전용해치료비Ⅱ(최초1회한)(뇌졸중),kb,3
```

**Result**: ✅ **Both target coverages found** in regenerated kb_scope.csv (lines 34-35)

---

## 5. Re-apply STEP NEXT-27 to KB

### 5.1 Run Step2 Canonical Mapping

**Command**:
```bash
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer kb
```

**Output**:
```
[Step 2] Canonical Mapping
[Step 2] Input: /Users/cheollee/inca-rag-scope/data/scope/kb_scope.csv
[Step 2] Mapping source: /Users/cheollee/inca-rag-scope/data/sources/mapping/담보명mapping자료.xlsx
[Step 2] Output: /Users/cheollee/inca-rag-scope/data/scope/kb_scope_mapped.csv

[Step 2] Mapping completed:
  - Matched: 27
  - Unmatched: 18
  - Total: 45

✓ Output: /Users/cheollee/inca-rag-scope/data/scope/kb_scope_mapped.csv
```

**Result**: ✅ **27 matched** (up from 0 matched with corrupted scope)

---

### 5.2 Verify suffix_normalized Matches

```bash
$ grep -E "suffix_normalized" data/scope/kb_scope_mapped.csv
혈전용해치료비Ⅱ(최초1회한)(특정심장질환),kb,3,A9640_1,혈전용해치료비,matched,suffix_normalized
혈전용해치료비Ⅱ(최초1회한)(뇌졸중),kb,3,A9640_1,혈전용해치료비,matched,suffix_normalized
```

**Result**: ✅ **Both KB VALID_CASE instances recovered** with:
- Coverage code: `A9640_1`
- Canonical: `혈전용해치료비`
- Match type: `suffix_normalized`

---

### 5.3 Run Step1 Sanitize

**Command**:
```bash
python -m pipeline.step1_sanitize_scope.run --insurer kb
```

**Output**:
```
[KB]
  Input: 45 rows
  Kept: 36 rows (80.0%)
  Dropped: 9 rows (20.0%)
  Dropped examples:
    - [PREMIUM_WAIVER] 보험료납입면제대상보장(8대기본)
    - [CONDITION_TIME] 일반상해80%이상후유장해시
    - [CONDITION_TIME] 질병80%이상후유장해시
  ✅ VERIFIED: No condition sentences
```

**Result**: ✅ 36 clean coverages (including both target coverages with `suffix_normalized` preserved)

---

### 5.4 Run Step5 Build Coverage Cards

**Command**:
```bash
python -m pipeline.step5_build_cards.build_cards --insurer kb
```

**Output**:
```
[Step 5] Coverage cards created:
  - Total coverages: 36
  - Matched: 27
  - Unmatched: 9
  - Evidence found: 31
  - Evidence not found: 5

✓ Cards: /Users/cheollee/inca-rag-scope/data/compare/kb_coverage_cards.jsonl
```

**Result**: ✅ KB coverage_cards.jsonl regenerated with 36 coverages

---

### 5.5 Verify Target Coverages in coverage_cards.jsonl

```bash
$ cat data/compare/kb_coverage_cards.jsonl | jq -r 'select(.coverage_name_raw | contains("혈전용해치료비")) | "\(.coverage_name_raw),\(.coverage_code),\(.mapping_status)"'
혈전용해치료비Ⅱ(최초1회한)(특정심장질환),A9640_1,matched
혈전용해치료비Ⅱ(최초1회한)(뇌졸중),A9640_1,matched
```

**Result**: ✅ **Both target coverages now have coverage_code** in coverage_cards.jsonl (SSOT)

**Before**:
- `"coverage_code": null, "mapping_status": "unmatched"`

**After**:
- `"coverage_code": "A9640_1", "mapping_status": "matched"`

---

## 6. DoD (Definition of Done) Verification

### Checklist

- [x] **KB scope.csv line count increased**
  - Before: 4 lines (3 garbage rows)
  - After: 46 lines (45 valid coverages)
  - Evidence: `wc -l data/scope/kb_scope.csv` → 46

- [x] **Target coverages exist in KB raw scope.csv**
  - `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)` — Line 34
  - `혈전용해치료비Ⅱ(최초1회한)(뇌졸중)` — Line 35
  - Evidence: `grep -n "혈전용해치료비" data/scope/kb_scope.csv`

- [x] **suffix_normalized match type in Step2 result**
  - Both KB VALID_CASE instances: `match_type = suffix_normalized`
  - Coverage code: `A9640_1`
  - Evidence: `grep -E "suffix_normalized" data/scope/kb_scope_mapped.csv`

- [x] **coverage_code assigned in coverage_cards.jsonl**
  - Before: `coverage_code: null`
  - After: `coverage_code: A9640_1`
  - Evidence: `jq` query on kb_coverage_cards.jsonl

- [x] **All results documented with command + output snippet**
  - See sections 2-5 above (every step with command + output)

- [x] **Zero code changes**
  - No code files modified (only data regeneration)
  - Only existing pipeline steps executed (Step1/Step2/Step1/Step5)

---

## 7. Summary

### Root Cause

**KB scope.csv corruption** (4 lines, 3 garbage rows, 89 bytes file size)

**Cause**: Unknown (likely historical data loss or incomplete extraction)

**Impact**: Step2 canonical mapping had **no valid input** → 0 matches

---

### Resolution

**Method**: Regenerate KB scope from proposal PDF using existing pipeline

**Steps**:
1. Execute `python -m pipeline.step1_extract_scope.run --insurer kb`
2. Re-run Step2 canonical mapping (with STEP NEXT-27 suffix-normalized logic)
3. Re-run Step1 sanitize
4. Re-run Step5 build coverage_cards

**Result**: **2 / 2 KB VALID_CASE instances recovered** (100% success rate for KB)

---

### Final STEP NEXT-27 Results (Updated)

| Insurer | VALID_CASE Count | Recovered | Recovery Rate |
|---------|------------------|-----------|---------------|
| Samsung | 5 | 5 | 100% |
| Lotte | 1 | 1 | 100% |
| Heungkuk | 1 | 1 | 100% |
| KB | 2 | 2 | **100%** ← **STEP NEXT-28** |
| **Total** | **9** | **9** | **100%** |

**STEP NEXT-27 + STEP NEXT-28 Combined Result**: **9 / 9 VALID_CASE instances recovered (100%)**

---

## 8. Evidence Audit Trail

### Before (KB Corrupted)

**File**: `data/scope/kb_scope.csv`
- **Lines**: 4
- **Valid Coverages**: 0
- **Garbage Rows**: 3 (`""`, `"(갱신보장:)"`, `"환급률 : .%"`)
- **Target Coverage Present**: ❌ NO

**Step2 Result**:
- **Matched**: 0
- **Unmatched**: 3
- **suffix_normalized**: 0

---

### After (KB Recovered)

**File**: `data/scope/kb_scope.csv`
- **Lines**: 46
- **Valid Coverages**: 45
- **Target Coverage Present**: ✅ YES (Lines 34-35)

**Step2 Result**:
- **Matched**: 27
- **Unmatched**: 18
- **suffix_normalized**: **2** (both target coverages)

**coverage_cards.jsonl** (SSOT):
- `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)`: `coverage_code = A9640_1, mapping_status = matched`
- `혈전용해치료비Ⅱ(최초1회한)(뇌졸중)`: `coverage_code = A9640_1, mapping_status = matched`

---

## 9. Lessons Learned

### Input Integrity Critical

**Observation**: STEP NEXT-27 logic was **correct**, but **input file corruption** blocked KB recovery.

**Implication**: Always verify input file integrity before debugging pipeline logic.

---

### KB Scope Producer

**Identified**: `pipeline/step1_extract_scope/run.py` (Line 132)

**Entry Command**:
```bash
python -m pipeline.step1_extract_scope.run --insurer kb
```

**Input**: `data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf`

**Output**: `data/scope/kb_scope.csv`

---

### Recovery Feasibility

**Condition**: Input PDF exists + Step1 extract_scope functional

**Result**: Full recovery possible without code changes

**Evidence**: KB recovered from 3 garbage rows → 45 valid coverages in single command execution

---

## End of Document

**STEP NEXT-28 Status**: ✅ **COMPLETE**

**KB Recovery**: 2 / 2 VALID_CASE instances (100%)

**Combined STEP NEXT-27 + STEP NEXT-28**: **9 / 9 VALID_CASE instances recovered (100%)**

**Code Changes**: 0 (data regeneration only)

**Documentation**: This file (STEP_NEXT_28_KB_SCOPE_RECOVERY.md)
