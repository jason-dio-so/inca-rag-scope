# SSOT Targeting Impact Analysis

**Date**: 2026-01-14
**Task**: STEP PIPELINE-FACT-MAP-01
**Status**: ✅ COMPLETE (STRUCTURAL ANALYSIS ONLY)

---

## Purpose

Analyze the STRUCTURAL impact of transitioning from current "PDF Discovery → String Matching" approach to "SSOT-First Targeting" approach.

NO implementation details. NO improvement proposals. STRUCTURAL analysis only.

Focus:
- What role does each Step currently play?
- What would each Step's role become under SSOT targeting?
- What becomes necessary/unnecessary/replaceable?

---

## Current Architecture (String-First)

### Flow

```
PDF Files (per insurer)
  ↓
Step1: Extract ALL coverages from PDF → coverage_name_raw
  ↓
Step2-a: Normalize coverage_name_raw
  ↓
Step2-b: Match coverage_name_raw to SSOT Excel → coverage_code (string matching)
  ↓ (if match fails → no coverage_code)
Step3: Search evidence using coverage_name_raw keyword
  ↓
Step4: Group by coverage_code (if exists)
  ↓
API Output: Compare tables grouped by coverage_code
```

### Key Characteristics

**Discovery-based**: Step1 discovers coverages from PDF (no prior target list)

**String matching gates**: coverage_code assignment depends on string matching success

**coverage_name_raw as primary key**: Used for evidence search, not coverage_code

**Late binding**: coverage_code only appears in Step2-b (after extraction)

---

## New Requirement (SSOT-First)

### Definition

> "작업 대상 담보는 (insurer_key, coverage_code) SSOT 쌍으로만 정의"

> "담보명 문자열 비교로 매핑/선택/필터가 발생하면 즉시 FAIL"

### Implications

**Target-driven**: SSOT defines what to extract BEFORE processing PDFs

**No string matching**: coverage_code is given, not derived

**coverage_code as primary key**: Used for all operations (extraction, evidence, comparison)

**Early binding**: coverage_code known from start (Step0 or pre-Step1)

---

## Impact Analysis by Step

### Step1: PDF Extraction

#### Current Role

**Responsibility**: Discover ALL coverages in PDF summary table

**Input**: PDF files (no prior knowledge of which coverages exist)

**Output**: List of ALL coverages with coverage_name_raw

**Logic**:
- Parse summary table rows
- Extract coverage_name_raw from each row
- No filtering (except noise removal)

**Decision**: What coverages exist in this PDF?

#### New Role (SSOT-First)

**Responsibility**: Extract facts for SSOT-defined (insurer, coverage_code) pairs ONLY

**Input**:
1. PDF files
2. **SSOT target list**: `[(insurer_key, coverage_code)]`

**Output**: List of SSOT-defined coverages with extracted facts

**Logic**:
- For each SSOT (insurer, coverage_code) pair:
  - Search PDF for this coverage's facts
  - Extract proposal_facts, detail_facts
- Coverages NOT in SSOT are IGNORED (not extracted)

**Decision**: What facts exist in PDF for THIS coverage_code?

#### Structural Change

| Aspect | Current | New (SSOT-First) |
|--------|---------|------------------|
| Input knowledge | None (blank slate) | Target list from SSOT |
| Coverage source | PDF discovery | SSOT definition |
| Coverage count | Variable (all found in PDF) | Fixed (SSOT count) |
| Filtering | None (extract all) | SSOT-driven (extract only targets) |
| coverage_code | ❌ Does not exist | ✅ Exists from start |
| Primary key | coverage_name_raw | coverage_code |

**Necessity**: ✅ REQUIRED (but logic changes from "discovery" to "targeted extraction")

**Role shift**: From **coverage discovery** to **fact extraction for known coverages**

---

### Step2-a: Sanitization

#### Current Role

**Responsibility**: Normalize coverage_name_raw (whitespace, special chars)

**Input**: Step1 output (coverage_name_raw)

**Output**: Normalized coverage_name_raw

**Decision**: None (normalization only)

#### New Role (SSOT-First)

**Responsibility**: Same (normalize fields for display/comparison)

**Input**: Step1 output (coverage_code + facts)

**Output**: Normalized fields (if needed for display)

**Decision**: None

#### Structural Change

| Aspect | Current | New (SSOT-First) |
|--------|---------|------------------|
| Necessity | Optional (helps string matching) | Optional (helps display consistency) |
| Impact | Affects Step2-b matching success | No impact on coverage_code (already known) |

**Necessity**: ⚠️ OPTIONAL (useful for display, not critical path)

**Role shift**: None (still normalization, but no decision impact)

---

### Step2-b: Canonical Mapping

#### Current Role

**Responsibility**: Assign coverage_code via string matching on coverage_name_raw

**Input**:
1. Step2-a output (coverage_name_raw, normalized)
2. SSOT Excel (mapping table)

**Output**: coverage_code (if match found)

**Logic**:
- Load Excel into dict: `{coverage_name: coverage_code}`
- Lookup coverage_name_raw → coverage_code
- Match types: exact, normalized, alias, normalized_alias

**Decision**: What coverage_code does this coverage_name_raw map to?

#### New Role (SSOT-First)

**Responsibility**: ❌ OBSOLETE (coverage_code already from SSOT)

**Input**: N/A (not needed)

**Output**: N/A

**Logic**: N/A

**Decision**: N/A

#### Structural Change

| Aspect | Current | New (SSOT-First) |
|--------|---------|------------------|
| Necessity | ✅ CRITICAL (creates coverage_code) | ❌ OBSOLETE (coverage_code already exists) |
| Impact | Determines which coverages get coverage_code | No impact (all SSOT coverages have coverage_code) |
| String matching | 5 violations (exact/normalized/alias) | 0 violations (no string matching) |

**Necessity**: ❌ OBSOLETE

**Role shift**: From **coverage_code assignment** to **NOT NEEDED**

**Alternative use**: Could be repurposed for:
- Field normalization (e.g., premium format standardization)
- Display name enrichment (if needed)
- But NOT for coverage_code assignment

---

### Step3: Evidence Resolution

#### Current Role

**Responsibility**: Find evidence for each coverage using coverage_name_raw as search keyword

**Input**:
1. Step2-b output (coverage_code + coverage_name_raw)
2. PDF documents (same as Step1 input)

**Output**: Evidence for each slot (start_date, payout_limit, etc.)

**Logic**:
- For each coverage:
  - Use coverage_name_raw as document search keyword
  - For each slot, search documents for patterns
  - Extract evidence with locators

**Decision**: Which document excerpts are evidence for this coverage?

#### New Role (SSOT-First)

**Responsibility**: Find evidence for each coverage using coverage_code metadata (not coverage_name_raw)

**Input**:
1. Step1 output (coverage_code + facts)
2. PDF documents
3. **SSOT metadata** (search strategy per insurer+coverage_code)

**Output**: Evidence for each slot

**Logic**:
- For each coverage:
  - Use coverage_code to look up search strategy in SSOT
  - Search documents using SSOT-defined keywords (consistent across insurers)
  - Extract evidence with locators

**Decision**: Which document excerpts are evidence for this coverage_code?

#### Structural Change

| Aspect | Current | New (SSOT-First) |
|--------|---------|------------------|
| Search keyword source | coverage_name_raw (varies per insurer) | SSOT metadata (consistent per coverage_code) |
| Consistency | ❌ Inconsistent (different keywords for same coverage_code) | ✅ Consistent (same strategy for same coverage_code) |
| Evidence contamination risk | ⚠️ HIGH (broad keyword matching) | ⚠️ LOWER (controlled search strategy) |
| String matching | 1 violation (coverage_name_raw as keyword) | 0 violations (coverage_code-based search) |

**Necessity**: ✅ REQUIRED (but logic changes from "coverage_name_raw-based" to "coverage_code-based")

**Role shift**: From **coverage_name-driven evidence search** to **coverage_code-driven evidence search**

**Requirement**: SSOT must provide search strategy per (insurer, coverage_code) pair

---

### Step4: Comparison Model

#### Current Role

**Responsibility**: Group coverages by coverage_code into comparison tables

**Input**: Step3 output (coverage_code + evidence)

**Output**: CompareRow per coverage, CompareTable per coverage_code

**Logic**:
- For each coverage:
  - Build identity (coverage_code, coverage_name_raw, etc.)
  - Build slots (start_date, payout_limit, etc.)
  - Determine unanchored status (no coverage_code → unanchored = true)
- Group by coverage_code into tables

**Decision**: How to group coverages for comparison?

#### New Role (SSOT-First)

**Responsibility**: Same (group coverages by coverage_code)

**Input**: Step3 output (coverage_code + evidence)

**Output**: CompareRow per coverage, CompareTable per coverage_code

**Logic**: Same (no change needed)

**Decision**: Same

#### Structural Change

| Aspect | Current | New (SSOT-First) |
|--------|---------|------------------|
| Necessity | ✅ REQUIRED | ✅ REQUIRED |
| Logic change | None | None |
| `unanchored` flag | Possible (if coverage_code = null) | ❌ Impossible (all coverages have coverage_code from SSOT) |

**Necessity**: ✅ REQUIRED (no change)

**Role shift**: None (still grouping by coverage_code)

**Simplification**: `unanchored = true` case becomes structurally impossible (all coverages have coverage_code)

---

## Step Necessity Summary

| Step | Current Necessity | SSOT-First Necessity | Role Change |
|------|------------------|---------------------|-------------|
| Step1 | ✅ REQUIRED (discovery) | ✅ REQUIRED (targeted extraction) | **MAJOR**: From discovery to target-driven extraction |
| Step2-a | ⚠️ OPTIONAL (normalization) | ⚠️ OPTIONAL (normalization) | None |
| Step2-b | ✅ CRITICAL (coverage_code assignment) | ❌ OBSOLETE | **ELIMINATED**: coverage_code from SSOT, not string matching |
| Step3 | ✅ REQUIRED (evidence search) | ✅ REQUIRED (evidence search) | **MEDIUM**: From coverage_name-based to coverage_code-based search |
| Step4 | ✅ REQUIRED (grouping) | ✅ REQUIRED (grouping) | None |

---

## Data Flow Comparison

### Current Flow (String-First)

```
┌─────────────────────┐
│ PDF Files           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Step1: Discovery    │
│ Extract ALL         │
│ coverage_name_raw   │
└──────────┬──────────┘
           │ coverage_name_raw (NO coverage_code)
           ▼
┌─────────────────────┐
│ Step2-a: Normalize  │
│ coverage_name_raw   │
└──────────┬──────────┘
           │ coverage_name_raw (normalized)
           ▼
┌─────────────────────┐    ┌──────────────────┐
│ Step2-b: Mapping    │◄───┤ SSOT Excel       │
│ String match →      │    │ (late reference) │
│ coverage_code       │    └──────────────────┘
└──────────┬──────────┘
           │ coverage_code (if match succeeds)
           │ ❌ May be null (if match fails)
           ▼
┌─────────────────────┐
│ Step3: Evidence     │
│ Search by           │
│ coverage_name_raw   │
└──────────┬──────────┘
           │ coverage_code + evidence
           ▼
┌─────────────────────┐
│ Step4: Grouping     │
│ Group by            │
│ coverage_code       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ API Output          │
└─────────────────────┘
```

### New Flow (SSOT-First)

```
┌──────────────────┐
│ SSOT Excel       │
│ (insurer,        │
│  coverage_code)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ Step0: Target Planning   │
│ Load SSOT list           │
│ [(insurer, coverage_code)]│
└────────┬─────────────────┘
         │ Target list + coverage_code
         │ ✅ coverage_code exists from start
         ▼
┌──────────────────────────┐    ┌─────────────────┐
│ Step1: Targeted Extract  │◄───┤ PDF Files       │
│ For each SSOT pair:      │    └─────────────────┘
│ Extract facts from PDF   │
└────────┬─────────────────┘
         │ coverage_code + facts
         ▼
┌──────────────────────────┐
│ Step2-a: Normalize       │
│ (optional, display only) │
└────────┬─────────────────┘
         │ coverage_code + normalized facts
         ▼
┌──────────────────────────┐
│ ❌ Step2-b: OBSOLETE     │
│ (coverage_code already   │
│  known, no mapping needed│
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐    ┌─────────────────┐
│ Step3: Evidence          │◄───┤ SSOT Metadata   │
│ Search by coverage_code  │    │ (search strategy│
│ (SSOT-defined strategy)  │    │  per coverage)  │
└────────┬─────────────────┘    └─────────────────┘
         │ coverage_code + evidence
         ▼
┌──────────────────────────┐
│ Step4: Grouping          │
│ Group by coverage_code   │
│ (all have coverage_code) │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ API Output               │
└──────────────────────────┘
```

---

## Key Differences

### 1. SSOT Reference Point

**Current**: SSOT referenced in Step2-b (late, after extraction)

**New**: SSOT referenced in Step0/pre-Step1 (early, before extraction)

**Impact**: coverage_code available from start, not derived

---

### 2. Coverage Discovery vs Targeting

**Current**: Step1 discovers what exists in PDF

**New**: SSOT defines what to look for in PDF

**Impact**: Step1 logic changes from "extract all" to "extract these specific coverages"

**Example**:
- Current: PDF has 100 coverages → Step1 extracts all 100 → Step2-b maps 80 → 20 dropped
- New: SSOT has 80 coverages → Step1 extracts only those 80 → 0 dropped

---

### 3. String Matching Gate

**Current**: String matching in Step2-b determines coverage_code assignment (gate)

**New**: No string matching gate (coverage_code from SSOT)

**Impact**: Eliminates 5 string matching violations in Step2-b

---

### 4. Evidence Search Consistency

**Current**: coverage_name_raw varies per insurer → different search keywords for same coverage_code

**New**: SSOT provides search strategy per coverage_code → consistent search across insurers

**Impact**: Eliminates evidence contamination risk

**Example** (A4200_1):
- Current: Meritz searches "암진단비(유사암제외)", Hanwha searches "암(4대유사암제외)진단비" → inconsistent
- New: Both search using SSOT-defined strategy for A4200_1 → consistent

---

### 5. Unanchored Coverages

**Current**: Possible (if Step2-b mapping fails)

**New**: Structurally impossible (all SSOT coverages have coverage_code)

**Impact**: Simplifies Step4 logic (no unanchored case)

---

## SSOT Requirements (for New Flow)

### Minimum Requirements

**Current SSOT** (data/sources/insurers/담보명mapping자료.xlsx):
- `ins_cd`: Insurer code
- `cre_cvr_cd`: coverage_code
- `신정원코드명`: Canonical name
- `담보명(가입설계서)`: Insurer-specific display name

**New SSOT Requirements**:
1. ✅ `ins_cd` + `cre_cvr_cd`: Target list (already exists)
2. ⚠️ **Search strategy** per (ins_cd, cre_cvr_cd): How to find this coverage in PDF
3. ⚠️ **Slot extraction rules** per coverage_code: What slots to extract, what patterns to use

**Missing in current SSOT**:
- Search strategy (how to locate coverage in PDF for each insurer)
- Slot extraction rules (per coverage_code, not per coverage_name_raw)

---

### Extended SSOT Structure (Hypothetical)

```
ins_cd | cre_cvr_cd | 신정원코드명 | 담보명(가입설계서) | search_keywords | slot_rules
-------|-----------|------------|--------------|----------------|------------
N01    | A4200_1   | 암진단비(유사암제외) | 암진단비(유사암제외) | ["암진단비", "유사암제외"] | {payout_limit: {...}}
N02    | A4200_1   | 암진단비(유사암제외) | 암(4대유사암제외)진단비 | ["암진단비", "4대유사암"] | {payout_limit: {...}}
```

**Note**: This is HYPOTHETICAL (not implemented). Shown only to illustrate SSOT requirements for new flow.

---

## Structural Impact Summary

### Step Elimination

**Step2-b (Canonical Mapping)**: ❌ OBSOLETE

**Reason**: coverage_code from SSOT, not string matching

**Savings**: ~114 lines of mapping logic, 5 string matching violations removed

---

### Step Transformation

**Step1 (PDF Extraction)**:
- Current: "Discover all coverages in PDF"
- New: "Extract facts for SSOT-defined coverages only"
- **Impact**: Requires SSOT target list as input

**Step3 (Evidence Resolution)**:
- Current: "Search evidence using coverage_name_raw"
- New: "Search evidence using coverage_code metadata"
- **Impact**: Requires SSOT search strategy per coverage_code

---

### Step Preservation

**Step2-a (Sanitization)**: Optional in both flows (display normalization)

**Step4 (Comparison Model)**: No change (still group by coverage_code)

---

### Data Quality Impact

**Consistency**: ✅ IMPROVED
- Same coverage_code → same evidence search strategy → consistent results

**Completeness**: ⚠️ DEPENDS ON SSOT
- Current: May extract coverages not in SSOT (but unanchored)
- New: Only extracts SSOT-defined coverages (none others)

**Correctness**: ✅ IMPROVED
- No string matching errors (coverage_code given, not derived)
- Lower evidence contamination risk (controlled search strategy)

---

## Migration Path (Structural)

### Phase 0: Preparation

**Task**: Enrich SSOT with search strategy metadata

**Current SSOT**: Has (ins_cd, cre_cvr_cd, display names)

**Needed**: Add search keywords, slot extraction rules per (ins_cd, cre_cvr_cd)

**No code changes** yet

---

### Phase 1: Step1 Transformation

**Task**: Change Step1 from "discovery" to "targeted extraction"

**Input**: SSOT target list `[(insurer_key, coverage_code)]`

**Output**: Same format as current Step1, but only SSOT-defined coverages

**Step2-b**: Still exists (for backward compatibility)

**Impact**: Step1 output has coverage_code field (new)

---

### Phase 2: Step3 Transformation

**Task**: Change Step3 from "coverage_name_raw-based" to "coverage_code-based" evidence search

**Input**: Step1 output (coverage_code + facts) + SSOT search strategy

**Output**: Same format as current Step3

**Impact**: Evidence search more consistent across insurers

---

### Phase 3: Step2-b Elimination

**Task**: Remove Step2-b (no longer needed)

**Input**: Step1 output already has coverage_code

**Output**: Step1 → Step3 (skip Step2-b)

**Impact**: Eliminate 114 lines of mapping logic, 5 string matching violations

---

### Phase 4: Verification

**Task**: Verify no regressions (evidence quality, coverage completeness)

**Method**: Compare old vs new Step3/Step4 output for sample coverages

**Impact**: None (verification only)

---

## Risks and Constraints

### Risk 1: SSOT Incompleteness

**Current**: If coverage not in SSOT → extracted but unanchored (still visible)

**New**: If coverage not in SSOT → NOT extracted (invisible)

**Mitigation**: Ensure SSOT completeness BEFORE transition

---

### Risk 2: Search Strategy Definition

**Current**: coverage_name_raw from PDF is search keyword (automatic)

**New**: SSOT must provide search strategy (manual effort)

**Mitigation**: Start with default strategy (use canonical name as keyword), refine per insurer

---

### Risk 3: Step1 Logic Complexity

**Current**: Step1 is simple (extract all rows)

**New**: Step1 must match PDF rows to SSOT targets (more complex)

**Mitigation**: Design robust matching logic (not string-based!)

---

## DoD Checklist

- [✅] Current architecture documented (Step1-4 roles)
- [✅] New requirement defined (SSOT-first targeting)
- [✅] Impact per step analyzed (necessity, role change)
- [✅] Data flow comparison created (current vs new)
- [✅] Key differences identified (5 major changes)
- [✅] SSOT requirements documented (minimum + extended)
- [✅] Structural impact summarized (elimination, transformation, preservation)
- [✅] Migration path outlined (4 phases)
- [✅] Risks identified (3 major risks)
- [✅] NO implementation details (structural analysis only)

---

**END OF IMPACT ANALYSIS**
