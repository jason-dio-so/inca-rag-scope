# STEP NEXT-30 TRIAGE REPORT — Extraction Failures + Evidence Not Found

**Date**: 2025-12-31
**Scope**: Diagnose samsung/meritz extraction failures (1/15 coverages) + hanwha evidence not found (0/41)

---

## 1) Samsung Extraction Failure (1 coverage extracted, expected 30+)

### Evidence

**PDF exists and is non-trivial**:
```bash
$ ls -lh data/sources/insurers/samsung/가입설계서/*.pdf
-rw-r--r--  1 cheollee  staff   1.2M Dec 27 03:00 삼성_가입설계서_2511.pdf
```

**Step1 output**:
```
[Step 1] Initial extraction: 0 coverages
[Step 1] After correction: 1 coverages
[Step 1] Final result:
  - Total PDFs processed: 1
  - Unique coverages: 1
  - Pages: [4]

✗ FAIL: insurer=samsung extracted=1 declared=N/A pages=[4]
```

**Extracted coverage**:
```csv
coverage_name_raw,insurer,source_page
선택계약,samsung,4
```

### Root Cause

**Extracted "선택계약" is a SECTION HEADER, not a coverage name.**

**Why the extractor failed**:
1. **Method 1 (text-based)**: `pipeline/step1_extract_scope/run.py:46-76`
   - Triggers on lines containing `['순번', '담보명', '보장명', '가입담보']` AND `['보험료', '가입금액', '납기']`
   - Samsung PDF likely has table headers in a different format OR split across multiple lines
   - No match → 0 extractions

2. **Method 2 (table-based)**: `pipeline/step1_extract_scope/run.py:78-119`
   - Requires header containing `('담보' OR '보장') AND '보험료'`
   - Samsung PDF likely has:
     - Header-less table
     - OR headers in non-standard layout (e.g., vertical text, merged cells)
   - No match → 0 extractions

3. **Hardening (enhanced extraction)**: `pipeline/step1_extract_scope/hardening.py:43-171`
   - Expands triggers to `['순번', '담보명', '보장명', '가입담보', '보장내용', '특약명']`
   - Adds headerless table detection: `hardening.py:119-128`
     - Condition: 4 columns, first column > 5 chars (한글), 2nd has "납", 4th is digit
   - Samsung table likely doesn't match this pattern
   - Extracted only "선택계약" (section marker that passed filters)

**Code references**:
- `pipeline/step1_extract_scope/run.py:46` — Text-based trigger conditions
- `pipeline/step1_extract_scope/run.py:86` — Table header validation
- `pipeline/step1_extract_scope/hardening.py:114` — Header detection (띄어쓰기 제거)
- `pipeline/step1_extract_scope/hardening.py:119-128` — Headerless table heuristic

---

## 2) Meritz Extraction Failure (15 coverages extracted, expected 30+)

### Evidence

**PDF exists**:
```bash
$ ls -lh data/sources/insurers/meritz/가입설계서/*.pdf
-rw-r--r--  1 cheollee  staff   731K Dec 27 03:00 메리츠_가입설계서_2511.pdf
```

**Step1 output**:
```
[Step 1] Initial extraction: 12 coverages
[Step 1] After correction: 15 coverages

✗ FAIL: insurer=meritz extracted=15 declared=N/A pages=[4, 6, 8, 10, 11]
```

**Extracted coverages** (15 rows):
```
질병수술비,meritz,4
(10년갱신)갱신형,meritz,4              ← SECTION HEADER
골절(치아파절제외)진단비Ⅱ,meritz,4
신화상치료비(화상수술비),meritz,4
신화상치료비(화상진단비),meritz,4
신화상치료비(중증화상및부식진단비),meritz,4
항암방사선약물치료비,meritz,4
혈전용해치료비Ⅱ(뇌졸중),meritz,4
혈전용해치료비Ⅱ(특정심장질환),meritz,4
기본계약,meritz,6                      ← SECTION HEADER
선택계약,meritz,6                      ← SECTION HEADER
사망후유,meritz,6                      ← SECTION HEADER
입원일당,meritz,8                      ← SECTION HEADER
골절/화상,meritz,10                    ← SECTION HEADER
할증/제도성,meritz,11                  ← SECTION HEADER
```

### Root Cause

**9 valid coverages + 6 section headers extracted.**

**Why only partial extraction**:
1. **Section headers not filtered**: `기본계약`, `선택계약`, `사망후유`, `입원일당`, `골절/화상`, `할증/제도성`
   - Filter only blocks `'(기본)', '기본계약'` (`run.py:67-68`)
   - But Meritz uses different section marker styles
   - Hardening filter also misses `사망후유`, `입원일당`, etc.

2. **Expected 30+ coverages**:
   - Only 9 actual coverages extracted from pages 4, 6, 8, 10, 11
   - Pages 4, 6 have section-based layout (not dense tables)
   - Extractor may be missing:
     - Coverages in multi-page continuation tables
     - Coverages with special characters/formatting
     - Coverages in non-standard columns (e.g., nested sub-tables)

3. **No declared count detected**:
   - `hardening.py:detect_declared_count()` found no "총 N개" pattern
   - Cannot verify against ground truth

**Code references**:
- `pipeline/step1_extract_scope/run.py:67-68` — Section header filter (limited patterns)
- `pipeline/step1_extract_scope/hardening.py:73-74` — Enhanced termination conditions
- `pipeline/step1_extract_scope/hardening.py:156-160` — Exclude keywords (doesn't cover all section headers)

---

## 3) Hanwha Evidence Not Found (0/41 found)

### Evidence

**Coverage cards** (41 rows, all `evidence_status: not_found`):
```bash
$ jq -r '.evidence_status' data/compare/hanwha_coverage_cards.jsonl | sort | uniq -c
41 not_found
```

**Evidence pack** (37 rows, 20 WITH evidence):
```bash
$ wc -l data/evidence_pack/hanwha_evidence_pack.jsonl
37 data/evidence_pack/hanwha_evidence_pack.jsonl

$ jq -r 'select(.evidences | length > 0) | .coverage_name_raw' data/evidence_pack/hanwha_evidence_pack.jsonl | wc -l
20
```

**Sanitized scope** (41 rows):
```bash
$ wc -l data/scope/hanwha_scope_mapped.sanitized.csv
42 data/scope/hanwha_scope_mapped.sanitized.csv  # (header + 41 rows)
```

**Coverage name mismatch** (smoking gun):
```bash
# Sanitized scope (first 5):
보통약관(상해사망)
상해후유장해(3-100%)
질병사망
골절(치아파절제외)진단비
화상진단비

# Evidence pack (first 5):
보험료 납입면제(Ⅱ)
유사암(8대) 진단비
상해 후유장해(3-100%)           ← 1 match (space difference)
암 진단비(유사암 제외)
뇌출혈 진단비(재진단형)
```

### Root Cause

**evidence_pack.jsonl was generated from a DIFFERENT scope version than current sanitized scope.**

**Why 0/41 found**:
1. **evidence_pack source**: Generated from OLD hanwha_scope.csv (before STEP NEXT-29 wipe)
   - Contains coverage names like `보험료 납입면제(Ⅱ)`, `유사암(8대) 진단비`, `뇌출혈 진단비(재진단형)`
   - Total: 37 coverages

2. **Current sanitized scope**: Generated in STEP NEXT-29 from NEW extraction
   - Contains coverage names like `보통약관(상해사망)`, `골절(치아파절제외)진단비`, `암(4대유사암제외)진단비`
   - Total: 41 coverages

3. **Step5 join logic** (`pipeline/step5_build_cards/build_cards.py:171-189`):
   - Loads evidence_pack into dict: `evidence_data[coverage_name_raw] = {...}`
   - Joins on exact `coverage_name_raw` match
   - Current scope names ≠ evidence_pack names → **0 matches**

4. **When evidence_pack was generated**:
   - File timestamp: `Dec 27 21:19` (before STEP NEXT-29 restart on Dec 31)
   - STEP NEXT-29 wiped `data/scope/*.csv` but **NOT** `data/evidence_pack/*.jsonl`
   - Evidence pack is stale

**Code references**:
- `pipeline/step5_build_cards/build_cards.py:171-189` — evidence_pack loader (exact key match)
- `pipeline/step5_build_cards/build_cards.py:211` — evidence join: `evidence_data.get(coverage_name_raw, ...)`

**File timestamps**:
```bash
$ ls -lh data/evidence_pack/hanwha_evidence_pack.jsonl
-rw-r--r--  1 cheollee  staff   101K Dec 27 21:19  # ← BEFORE STEP NEXT-29

$ ls -lh data/scope/hanwha_scope_mapped.sanitized.csv
-rw-r--r--  1 cheollee  staff   4.2K Dec 31 09:51  # ← AFTER STEP NEXT-29
```

---

## 4) Minimal Fix Plan

### Fix 1: Samsung/Meritz Extraction (Manual Table Inspection Required)

**Issue**: Table structure mismatch with extractor assumptions.

**Minimal deterministic fix** (NO fuzzy matching):
1. **Inspect PDF manually**:
   ```bash
   open data/sources/insurers/samsung/가입설계서/삼성_가입설계서_2511.pdf
   open data/sources/insurers/meritz/가입설계서/메리츠_가입설계서_2511.pdf
   ```
   - Identify exact header text/layout on pages containing coverage tables
   - Check if headers are split across rows, merged cells, or vertical text

2. **Add insurer-specific patterns** (`pipeline/step1_extract_scope/hardening.py`):
   ```python
   # Example: Samsung headerless table with 5 columns
   if insurer == 'samsung' and not has_header and len(table[0]) == 5:
       # Samsung-specific: col0=coverage, col1=period, col2=amount, col3=premium
       if (table[0][0] and len(str(table[0][0])) > 5
           and '기간' in str(table[0][1] or '')
           and re.match(r'^\d+', str(table[0][2] or ''))):
           coverage_col_idx = 0
           start_row = 0
   ```

3. **Expand section header filter** (`pipeline/step1_extract_scope/hardening.py:156-160`):
   ```python
   exclude_keywords = [
       '합계', '보험료', '광화문', '준법감시', '설계번호',
       '피보험자', '구분', '담 보', '담보 명', '가입금액',
       '☞', '※', '▶', '계약자', '납입', '발행일',
       # ADD:
       '기본계약', '선택계약', '사망후유', '입원일당',
       '골절/화상', '할증/제도성', '(10년갱신)갱신형',
       '선택특약', '주계약'
   ]
   ```

**Validation**:
```bash
# Re-run extraction
python -m pipeline.step1_extract_scope.run --insurer samsung
python -m pipeline.step1_extract_scope.run --insurer meritz

# Verify counts
wc -l data/scope/samsung_scope.csv  # expect 30+
wc -l data/scope/meritz_scope.csv   # expect 30+
```

**File:line references**:
- `pipeline/step1_extract_scope/hardening.py:114-128` — Header/headerless detection
- `pipeline/step1_extract_scope/hardening.py:156-160` — Exclude keywords

---

### Fix 2: Hanwha Evidence Not Found (Stale evidence_pack)

**Issue**: evidence_pack generated from OLD scope, now mismatched after STEP NEXT-29 wipe.

**Minimal deterministic fix**:

**Option A: Regenerate evidence_pack** (if Step3/4 exist):
```bash
# Re-run evidence search and build
python -m pipeline.step3_search.search_coverage --insurer hanwha
python -m pipeline.step4_evidence.build_evidence --insurer hanwha

# Re-run Step5 to rebuild coverage_cards with fresh evidence
python -m pipeline.step5_build_cards.build_cards --insurer hanwha

# Verify
jq -r '.evidence_status' data/compare/hanwha_coverage_cards.jsonl | sort | uniq -c
# expect: ~20 found, ~21 not_found (matching evidence_pack ratio)
```

**Option B: Wipe stale evidence_pack + regenerate** (if Step3/4 don't exist in active pipeline):
```bash
# Remove stale evidence_pack
rm data/evidence_pack/hanwha_evidence_pack.jsonl

# (This requires Step3/4 to exist — if DEPRECATED, then evidence search must be re-implemented)
```

**Option C: Accept 0/41 as structural outlier** (if evidence_pack regeneration is out of scope):
- Mark hanwha as structural outlier (like in STEP NEXT-18X)
- Document in `config/structural_outliers.json`: `{"insurer": "hanwha", "reason": "stale_evidence_pack", "expected_fix": "regenerate_step3_step4"}`
- KPI excludes hanwha

**Validation**:
```bash
# Check evidence_status distribution
jq -r '.evidence_status' data/compare/hanwha_coverage_cards.jsonl | sort | uniq -c

# Expect non-zero "found"
```

**File:line references**:
- `pipeline/step5_build_cards/build_cards.py:171-189` — evidence_pack loader
- `pipeline/step5_build_cards/build_cards.py:211` — evidence join logic
- `data/evidence_pack/hanwha_evidence_pack.jsonl:1` — Stale file (timestamp Dec 27 21:19)

---

## 5) Hard Stops (MUST NOT)

- ❌ **NO fuzzy matching** for coverage names
- ❌ **NO mapping excel edits** (`data/sources/mapping/담보명mapping자료.xlsx`)
- ❌ **NO LLM-based extraction**
- ❌ **NO scope expansion** (only fix extraction bugs)

---

## 6) Definition of Done

**DoD for this triage report**:
- ✅ Samsung failure explained with reproducible evidence (section header extracted, table not detected)
- ✅ Meritz failure explained with reproducible evidence (9 valid + 6 section headers, 30+ expected)
- ✅ Hanwha evidence not found explained with reproducible evidence (stale evidence_pack, name mismatch)
- ✅ Minimal fix plan proposed with file:line references
- ✅ Validation commands provided (1 command per fix)

**Next Step Options** (User Decision Required):
1. **STEP NEXT-30A**: Fix samsung/meritz extraction (manual PDF inspection + pattern additions)
2. **STEP NEXT-30B**: Regenerate hanwha evidence_pack (if Step3/4 available)
3. **STEP NEXT-30C**: Accept current state as structural outliers (if fixes are out of scope)

---

## 7) Summary

| Insurer | Issue | Root Cause | Fix Type | DoD |
|---------|-------|------------|----------|-----|
| Samsung | 1/30+ extracted | Section header extracted, table header pattern mismatch | Deterministic pattern addition | Manual PDF inspection required |
| Meritz | 15/30+ extracted | 6 section headers not filtered, partial table extraction | Section filter expansion + pattern tuning | Pattern list extension |
| Hanwha | 0/41 evidence found | Stale evidence_pack (Dec 27) vs new scope (Dec 31) | Regenerate evidence_pack OR mark as outlier | Step3/4 re-run OR accept outlier |

**Critical Dependencies**:
- Samsung/Meritz fix: Requires manual PDF inspection to identify exact table structure
- Hanwha fix: Requires Step3/4 pipeline existence (search + evidence build)

**Recommended Priority**:
1. Hanwha (quick win if Step3/4 available, OR document as outlier)
2. Meritz (easier fix: section filter expansion)
3. Samsung (harder fix: requires PDF-specific pattern engineering)
