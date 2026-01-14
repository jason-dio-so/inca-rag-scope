# Pipeline String Matching Ban Scan (Decision Logic)

**Date**: 2026-01-14
**Task**: STEP PIPELINE-FACT-MAP-01
**Status**: ✅ COMPLETE (FACT ONLY)

---

## Purpose

Scan Step1-4 pipeline for instances where **담보명 문자열 비교/포함/정규식/fuzzy**가 **결정 로직**에 영향을 미치는 지점.

Focus: DECISION LOGIC ONLY (not display/logging)

Decision logic includes:
- Coverage code assignment (mapping)
- Coverage filtering (drop/keep)
- Evidence search (which evidence to extract)
- Slot value extraction (which value to assign)

NO inference. CODE only.

---

## Scan Methodology

### Search Patterns

**Fields to track**:
- `coverage_name_raw`
- `coverage_name_normalized`
- `canonical_name`
- `담보명(가입설계서)` (from Excel)

**Operations to flag**:
- `==`, `!=` (equality comparison)
- `in`, `not in` (substring check)
- `startswith`, `endswith` (prefix/suffix check)
- `re.search`, `re.match`, `re.sub` (regex matching)
- `fuzz.ratio`, `fuzz.partial_ratio` (fuzzy matching)

**Scope**: Step1-4 pipeline only (`pipeline/step1_*`, `step2_*`, `step3_*`, `step4_*`)

---

## Step1: PDF Extraction

**File**: `pipeline/step1_summary_first/extractor_v3.py`

### No String Matching Decision Logic

**Fact**: Step1 extracts coverage_name_raw from PDF text directly.

**No comparison** - coverage_name_raw is simply extracted, not compared to any reference list.

**Verdict**: ✅ CLEAN (no string matching decision logic)

---

## Step2-a: Sanitization

**File**: `pipeline/step2_sanitize_scope/sanitize.py`

### String Normalization (Not Decision Logic)

**Purpose**: Remove whitespace, special characters

**Does NOT** filter/drop/assign coverage_code

**Verdict**: ✅ CLEAN (normalization only, no decision logic)

---

## Step2-b: Canonical Mapping

**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py`

### ⚠️ CRITICAL: String Matching Determines coverage_code

**Total violations**: 4 decision points

#### Violation 1: Exact Match on Canonical Name

**Line**: 82-87

**Code**:
```python
# 1. 신정원코드명으로 exact match
self.mapping_dict[coverage_name_canonical] = {
    'coverage_code': coverage_code,
    'coverage_name_canonical': coverage_name_canonical,
    'match_type': 'exact'
}
```

**Decision impact**: ⚠️ CRITICAL - If coverage_name_raw == canonical_name → assign coverage_code

**String operation**: Dict key lookup (exact string match)

#### Violation 2: Normalized Match on Canonical Name

**Line**: 89-96

**Code**:
```python
# 2. 신정원코드명 normalized match
normalized_canonical = self._normalize(coverage_name_canonical)
if normalized_canonical:
    self.mapping_dict[normalized_canonical] = {
        'coverage_code': coverage_code,
        'coverage_name_canonical': coverage_name_canonical,
        'match_type': 'normalized'
    }
```

**Decision impact**: ⚠️ CRITICAL - If normalize(coverage_name_raw) == normalize(canonical_name) → assign coverage_code

**String operation**: Normalization + dict key lookup

**Normalization** (lines 31-45):
```python
def _normalize(self, text: str) -> str:
    text = re.sub(r'\s+', '', text)  # Remove whitespace
    text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)  # Remove special chars
    return text.lower()
```

#### Violation 3: Exact Match on Insurer Alias

**Line**: 98-104

**Code**:
```python
# 3. 보험사별 담보명(가입설계서)으로 exact match
if coverage_name_insurer:
    self.mapping_dict[coverage_name_insurer] = {
        'coverage_code': coverage_code,
        'coverage_name_canonical': coverage_name_canonical,
        'match_type': 'alias'
    }
```

**Decision impact**: ⚠️ CRITICAL - If coverage_name_raw == 담보명(가입설계서) → assign coverage_code

**String operation**: Dict key lookup (exact string match)

**Example**: Meritz "암진단비(유사암제외)" == Excel "암진단비(유사암제외)" → coverage_code = "A4200_1"

#### Violation 4: Normalized Match on Insurer Alias

**Line**: 106-113

**Code**:
```python
# 4. 보험사별 담보명 normalized match
normalized_insurer = self._normalize(coverage_name_insurer)
if normalized_insurer:
    self.mapping_dict[normalized_insurer] = {
        'coverage_code': coverage_code,
        'coverage_name_canonical': coverage_name_canonical,
        'match_type': 'normalized_alias'
    }
```

**Decision impact**: ⚠️ CRITICAL - If normalize(coverage_name_raw) == normalize(담보명) → assign coverage_code

**String operation**: Normalization + dict key lookup

### Suffix Removal (String Pattern Matching)

**Line**: 115-173

**Function**: `_remove_suffix_patterns(text: str) -> Optional[str]`

**Patterns**:
```python
# Pattern 1: Period/occurrence metadata
pattern_period = r'\((?:\d+년\d+%?|\d+년주기|최초\d+회한)\)$'

# Pattern 2: Duration range
pattern_duration = r'\(\d+일-\d+일\)$'

# Pattern 3: Renewal metadata
pattern_renewal = r'\(갱신형_\d+년\)$'

# Pattern 4: Condition specifier
pattern_condition = r'\((특정심장질환|뇌졸중|중증치매|...)\)$'
```

**Decision impact**: ⚠️ MEDIUM - If suffix removed → retry mapping with base name

**String operation**: Regex matching and substitution

**Example**: "암진단비(최초1회한)" → remove "(최초1회한)" → "암진단비" → retry mapping

---

## Step3: Evidence Resolution

**File**: `pipeline/step3_evidence_resolver/resolver.py`

### ⚠️ CRITICAL: String Matching Determines Evidence Search

**Total violations**: 1 decision point (but affects all evidence extraction)

#### Violation 5: Evidence Search Keyword from coverage_name_raw

**Line**: 74, 108

**Code**:
```python
# Line 74
coverage_name = coverage.get("coverage_name_raw", "")

# Line 108
slot_result = self._resolve_slot(
    coverage_name,  # ← Used as search keyword
    pattern,
    documents,
    coverage_code
)
```

**Decision impact**: ⚠️ CRITICAL - coverage_name_raw determines which documents/excerpts are searched

**String operation**: coverage_name_raw used as keyword in document search

**Issue**: Different coverage_name_raw for same coverage_code (across insurers) → different evidence search results

**Example**:
- Meritz A4200_1: Search for "암진단비(유사암제외)"
- Hanwha A4200_1: Search for "암(4대유사암제외)진단비"
- Lotte A4200_1: Search for "일반암진단비Ⅱ"
→ Same coverage_code, DIFFERENT search keywords → inconsistent evidence

---

## Step3: Evidence Patterns

**File**: `pipeline/step3_evidence_resolver/evidence_patterns.py`

### String Pattern Matching for Slot Extraction

**Total violations**: Not counted (pattern-based extraction is expected for evidence, but noted for completeness)

**Patterns** (examples):
- `start_date`: Keywords like "보장개시일", "암보장개시일"
- `payout_limit`: Keywords like "회한", "최초", "지급"
- `waiting_period`: Keywords like "면책기간", "보장제외기간"

**Decision impact**: ⚠️ HIGH - Determines slot value extraction

**String operation**: Keyword matching, regex patterns

**Note**: This is expected behavior for evidence extraction, but flagged because it's string-based pattern matching.

---

## Step4: Compare Model

**File**: `pipeline/step4_compare_model/model.py`

### String Matching for Coverage Title Extraction

**Total violations**: 2 (both display-focused, LOW impact)

#### Violation 6: Coverage Title Extraction

**Line**: 23-25 (extract_coverage_title)

**Code**:
```python
def extract_coverage_title(coverage_name_raw: str) -> str:
    """
    Extract coverage title by removing metadata suffixes.

    Examples:
    - "암진단비(유사암제외)" → "암진단비"
    - "암진단비(최초1회한)" → "암진단비"
    """
    # Remove trailing parentheses (metadata suffix)
    # Pattern: (유사암제외), (최초1회한), (1년50%), etc.
    return re.sub(r'\(.*?\)$', '', coverage_name_raw).strip()
```

**Decision impact**: ⚠️ LOW - Display only (used for table grouping title)

**String operation**: Regex substitution

#### Violation 7: Coverage Title Normalization

**Line**: 32-42 (normalize_coverage_title)

**Code**:
```python
def normalize_coverage_title(title: str) -> str:
    """
    Normalize coverage title for comparison.

    - Remove spaces
    - Lowercase
    """
    title = re.sub(r'\s+', '', title)
    return title.lower()
```

**Decision impact**: ⚠️ LOW - Used for grouping/comparison in UI (not critical path)

**String operation**: Regex + lowercase

---

## Step4: Builder

**File**: `pipeline/step4_compare_model/builder.py`

### No String Matching Decision Logic

**Fact**: Step4 builder uses coverage_code for grouping, NOT coverage_name comparison.

**Grouping** (line 111):
```python
coverage_code = coverage.get("coverage_code")
```

**No string comparison** for decision logic.

**Verdict**: ✅ CLEAN (no string matching decision logic)

---

## Summary of Violations

| # | File | Line | Function | Decision Impact | String Operation |
|---|------|------|----------|----------------|------------------|
| 1 | `step2_canonical_mapping/map_to_canonical.py` | 82-87 | `_load_mapping` | ⚠️ CRITICAL | Exact match on canonical_name → coverage_code assignment |
| 2 | `step2_canonical_mapping/map_to_canonical.py` | 89-96 | `_load_mapping` | ⚠️ CRITICAL | Normalized match on canonical_name → coverage_code assignment |
| 3 | `step2_canonical_mapping/map_to_canonical.py` | 98-104 | `_load_mapping` | ⚠️ CRITICAL | Exact match on insurer alias → coverage_code assignment |
| 4 | `step2_canonical_mapping/map_to_canonical.py` | 106-113 | `_load_mapping` | ⚠️ CRITICAL | Normalized match on insurer alias → coverage_code assignment |
| 5 | `step3_evidence_resolver/resolver.py` | 74, 108 | `resolve` | ⚠️ CRITICAL | coverage_name_raw as search keyword → evidence extraction |
| 6 | `step4_compare_model/model.py` | 23-25 | `extract_coverage_title` | ⚠️ LOW | Regex suffix removal → display title |
| 7 | `step4_compare_model/model.py` | 32-42 | `normalize_coverage_title` | ⚠️ LOW | Normalization → display comparison |

**Total**: 7 violations (5 CRITICAL, 2 LOW)

---

## Critical Path Violations

### Violation Group A: coverage_code Assignment (Step2-b)

**Impact**: If coverage_name_raw doesn't match any Excel entry → no coverage_code → unanchored

**Files**: `map_to_canonical.py`

**Violations**: #1, #2, #3, #4

**Risk**: HIGH - Coverage may not be recognized if:
- Excel lacks this coverage name variant
- PDF has typo/spacing difference
- Normalization doesn't cover edge case

**Example failure scenario**:
- Excel has: "암진단비(유사암제외)"
- PDF has: "암진단비 (유사암 제외)" (extra spaces inside parentheses)
- Normalized match: "암진단비유사암제외" vs "암진단비유사암제외" → still matches ✅
- But if PDF has: "암진단비(4대유사암제외)" (variant not in Excel) → no match → no coverage_code ❌

### Violation Group B: Evidence Search (Step3)

**Impact**: Inconsistent evidence extraction across insurers for same coverage_code

**Files**: `resolver.py`

**Violations**: #5

**Risk**: HIGH - Evidence contamination:
- Meritz A4200_1 searches for "암진단비(유사암제외)"
- Hanwha A4200_1 searches for "암(4대유사암제외)진단비"
- If document contains both strings in nearby text → may extract wrong evidence

**Example failure scenario**:
- Document text: "유사암진단비 6백만원 ... 암진단비(유사암제외) 3천만원"
- Search keyword: "암진단비" (broad match)
- May extract "유사암진단비 6백만원" for A4200_1 (wrong coverage) ❌

**Evidence from previous audit**: Meritz A4200_1 evidence contains "유사암진단비" text (A4210)

---

## Non-Critical Path Violations

### Violation Group C: Display/Grouping (Step4)

**Impact**: LOW - Only affects UI display, not data correctness

**Files**: `model.py`

**Violations**: #6, #7

**Risk**: LOW - Display inconsistency only

---

## Scan Verification

### Files Scanned

```bash
find pipeline/step{1,2,3,4}_* -name "*.py" | grep -E "(extractor|map_to_canonical|resolver|builder|model)" | wc -l
```

**Result**: 10 core files scanned

### Pattern Search

```bash
grep -rn "coverage_name_raw" pipeline/step{1,2,3,4}_* --include="*.py" | wc -l
```

**Result**: 58 occurrences (all reviewed)

### Decision Logic Filter

**Criteria**: Only flagged if string comparison AFFECTS:
1. coverage_code assignment
2. Coverage filtering (drop/keep)
3. Evidence search/extraction
4. Slot value determination

**Excluded**: Logging, display-only formatting, debugging output

---

## Constitutional Violation Assessment

### New Requirement (SSOT-First)

> "담보명 문자열 비교로 매핑/선택/필터가 발생하면 즉시 FAIL"

### Verdict by Violation

| # | Violates New Requirement? | Reason |
|---|--------------------------|--------|
| 1 | ✅ YES | coverage_name_raw string match → coverage_code assignment |
| 2 | ✅ YES | Normalized coverage_name_raw string match → coverage_code assignment |
| 3 | ✅ YES | coverage_name_raw string match → coverage_code assignment |
| 4 | ✅ YES | Normalized coverage_name_raw string match → coverage_code assignment |
| 5 | ✅ YES | coverage_name_raw string → evidence search keyword |
| 6 | ❌ NO | Display only (coverage title extraction) |
| 7 | ❌ NO | Display only (title normalization) |

**Total constitutional violations**: 5 out of 7

---

## Impact on SSOT Targeting

### Current Flow (String-First)

```
Step1: Extract coverage_name_raw from PDF (no SSOT reference)
  ↓
Step2: Match coverage_name_raw to SSOT via string comparison
  ↓ (if match fails → no coverage_code)
Step3: Search evidence using coverage_name_raw keyword
  ↓ (different keywords for same coverage_code across insurers)
Step4: Group by coverage_code (if exists)
```

### New Flow (SSOT-First)

```
SSOT: Load (insurer, coverage_code) pairs from Excel FIRST
  ↓
Step1: For each SSOT pair, extract facts from PDF (target plan)
  ↓ (no string matching - SSOT defines what to look for)
Step2: NOT NEEDED (coverage_code already from SSOT)
  ↓
Step3: Search evidence using coverage_code metadata (not coverage_name_raw)
  ↓ (same search strategy for all insurers with this coverage_code)
Step4: Group by coverage_code (guaranteed to exist)
```

**Key difference**: No string matching decision points in new flow.

---

## Recommendations (FACT-Based)

### For SSOT Targeting Transition

**Violation Group A (Step2-b)**:
- Current: String matching determines coverage_code
- New: SSOT defines (insurer, coverage_code) pairs upfront
- **Impact**: Step2-b mapping logic becomes OBSOLETE (or reduced to field normalization only)

**Violation Group B (Step3)**:
- Current: coverage_name_raw determines evidence search
- New: Need coverage_code-based evidence search (or SSOT-defined search keywords per insurer)
- **Impact**: Evidence search logic requires redesign (cannot rely on coverage_name_raw)

**Violation Group C (Step4)**:
- Current: Display-only string operations
- New: No change needed (coverage_code already available from SSOT)
- **Impact**: None

---

## DoD Checklist

- [✅] All Step1-4 files scanned for string matching patterns
- [✅] Decision logic violations identified (5 CRITICAL)
- [✅] Non-decision logic violations noted (2 LOW)
- [✅] Each violation documented with file/line/code snippet
- [✅] Decision impact assessed (coverage_code assignment, evidence search)
- [✅] Constitutional violation assessment completed
- [✅] Impact on SSOT targeting analyzed (FACT-based)

---

**END OF SCAN DOCUMENT**
