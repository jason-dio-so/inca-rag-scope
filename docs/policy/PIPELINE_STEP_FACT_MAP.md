# Pipeline Step Fact Map (Step1-4)

**Date**: 2026-01-14
**Task**: STEP PIPELINE-FACT-MAP-01
**Status**: ✅ COMPLETE (FACT ONLY)

---

## Purpose

Document the ACTUAL behavior of Step1-4 pipeline based on CODE and DATA ONLY (NO inference).

Each step's:
- Input/Output contracts
- Coverage targeting logic
- coverage_code handling
- coverage_name usage
- Evidence handling
- Failure/drop conditions

---

## Step Entry Points

| Step | Entry Point | Primary Module | Output Pattern |
|------|-------------|----------------|----------------|
| Step1 | `pipeline/step1_summary_first/extractor_v3.py` | ExtractorV3 class | `data/scope_v3/{INSURER}_{VARIANT?}_step1_raw_scope_v3.jsonl` |
| Step2-a | `pipeline/step2_sanitize_scope/sanitize.py` | (intermediate) | `*_step2_sanitized_scope_v1.jsonl` |
| Step2-b | `pipeline/step2_canonical_mapping/map_to_canonical.py` | CanonicalMapper class | `*_step2_canonical_scope_v1.jsonl` |
| Step3 | `pipeline/step3_evidence_resolver/resolver.py` | CoverageEvidenceResolver class | `*_step3_evidence_enriched_v1.jsonl` |
| Step4 | `pipeline/step4_compare_model/builder.py` | CompareRowBuilder + CompareTableBuilder | `data/compare_v1/compare_rows_v1.jsonl`, `compare_tables_v1.jsonl` |

---

## Step1: PDF Extraction

**Module**: `pipeline/step1_summary_first/extractor_v3.py`

### Input Contract

**Source**: PDF files (per insurer)
- 가입설계서 (proposal document)
- 상품요약서 (product summary)
- 사업방법서 (business method)
- 약관 (terms and conditions)

**Profile**: `{INSURER}_{VARIANT?}_profile_v3.json`
- Contains: PDF fingerprint, summary page ranges, column mappings

### Output Contract

**File**: `data/scope_v3/{INSURER}_{VARIANT?}_step1_raw_scope_v3.jsonl`

**Fields** (evidence from actual data):
```json
{
  "coverage_name_raw": "암진단비(유사암제외)",
  "ins_cd": "M01",
  "insurer_key": "meritz",
  "product": {
    "product_name_raw": "(무) 알파Plus보장보험2511 (해약환급금미지급형(납입후50%))(보험료 납입면제형)",
    "product_name_normalized": "무알파Plus보장보험2511보험료납입면제형",
    "product_key": "meritz__무알파Plus보장보험2511보험료납입면제형"
  },
  "proposal_facts": { /* extracted from 가입설계서 summary table */ },
  "proposal_detail_facts": { /* extracted from detail pages */ },
  "proposal_context": { /* metadata */ },
  "variant": "default"
}
```

**Critical**: NO `coverage_code` field in Step1 output.

### Coverage Targeting

**Logic**: Extract ALL coverages found in PDF summary table.

**No filtering** at this stage (except noise removal: totals, disclaimers).

**Trigger**: PDF summary table rows where coverage_name_raw is not empty.

### Coverage Code Handling

**Status**: ❌ coverage_code DOES NOT EXIST in Step1.

**Source**: coverage_name_raw is extracted from PDF text (column in summary table).

**Code location**: `extractor_v3.py:240-289` (`_extract_from_summary()`)

```python
# Line 54-57
@dataclass
class ProposalFact:
    """Proposal fact (raw text only, no inference)"""
    coverage_name_raw: str  # ← FROM PDF, NO coverage_code
    proposal_facts: Dict[str, Any]
```

### Coverage Name Usage

**coverage_name_raw**:
- Extracted from: PDF summary table (coverage name column)
- Used for: Identifying coverage (ONLY identifier at this stage)
- Normalization: None (raw text preserved)

**Decision Impact**: ⚠️ HIGH - coverage_name_raw is the ONLY way to identify coverages in Step1.

### Evidence Handling

**Evidence Source**: `proposal_facts` dict contains:
- Premium amount
- Coverage amount (가입금액)
- Payment frequency
- Period/maturity

**Evidence Attribution**: Embedded in coverage record.

**Locator**: Page number from PDF summary table (implicit).

### Failure/Drop Conditions

**Fingerprint gate** (line 81-99):
- If PDF fingerprint doesn't match profile → **EXIT 2** (hard failure)

**Coverage drop**:
- Empty coverage_name_raw → dropped
- Total rows / disclaimers → dropped (heuristic filtering)

---

## Step2-a: Sanitization (Intermediate)

**Module**: `pipeline/step2_sanitize_scope/sanitize.py`

### Input Contract

**File**: `*_step1_raw_scope_v3.jsonl`

### Output Contract

**File**: `*_step2_sanitized_scope_v1.jsonl`

**Added fields**:
- `sanitized`: bool (whether sanitization was applied)
- `normalization_applied`: list of normalization types

**Purpose**: Remove special characters, normalize whitespace.

**Coverage Targeting**: No filtering (all Step1 coverages pass through).

---

## Step2-b: Canonical Mapping

**Module**: `pipeline/step2_canonical_mapping/map_to_canonical.py`

### Input Contract

**File**: `*_step2_sanitized_scope_v1.jsonl`

**Required fields**: `coverage_name_raw`, `ins_cd`, `insurer_key`

### Output Contract

**File**: `*_step2_canonical_scope_v1.jsonl`

**Fields** (evidence from actual data):
```json
{
  "coverage_name_raw": "암진단비(유사암제외)",
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "mapping_method": "exact",
  "mapping_confidence": "HIGH",
  "coverage_name_normalized": "암진단비유사암제외",
  "normalization_applied": [],
  "sanitized": false,
  ... /* all Step1 fields preserved */
}
```

**Critical**: `coverage_code` is FIRST CREATED in Step2-b.

### Coverage Targeting

**Logic**: Attempt to map ALL Step1 coverages to coverage_code.

**Filtering**: If mapping FAILS → coverage is DROPPED (or marked with `drop_reason`).

**Success rate**: Depends on mapping Excel completeness.

### Coverage Code Handling

**Status**: ✅ coverage_code CREATED here.

**Source**: `data/sources/mapping/담보명mapping자료.xlsx`

⚠️ **CONTAMINATED PATH**: Should be `data/sources/insurers/담보명mapping자료.xlsx`

**Code location**: `map_to_canonical.py:12`

```python
# Line 12 (WRONG PATH!)
mapping_excel_path = "data/sources/mapping/담보명mapping자료.xlsx"
```

**Mapping algorithm** (lines 75-114):

1. **Exact match** on `신정원코드명` (canonical name)
2. **Normalized match** on normalized canonical name
3. **Alias match** on `담보명(가입설계서)` (insurer-specific name)
4. **Normalized alias match** on normalized insurer name

**Normalization** (lines 31-45):
- Remove whitespace: `\s+` → ``
- Remove special characters: `[^가-힣a-zA-Z0-9]` → ``
- Lowercase

**Matching logic** (lines 47-114):
- Creates in-memory dict: `{coverage_name: {coverage_code, canonical_name, match_type}}`
- Lookup coverage_name_raw → coverage_code

### Coverage Name Usage

**coverage_name_raw**:
- Used as: Lookup KEY for mapping
- Decision impact: ⚠️ CRITICAL - determines if coverage gets coverage_code

**canonical_name**:
- Assigned from: Mapping Excel `신정원코드명` column
- Used as: Display name (no decision logic dependency)

**coverage_name_normalized**:
- Created by: `_normalize()` function
- Used as: Fallback lookup key

**⚠️ STRING MATCHING**: Entire Step2-b is based on string matching (exact/normalized/alias).

### Evidence Handling

**Preservation**: All Step1 evidence (proposal_facts, proposal_detail_facts) is PRESERVED.

**No new evidence** added at this stage.

### Failure/Drop Conditions

**Mapping failure**:
- coverage_name_raw not found in mapping dict → `coverage_code = null` or record dropped
- Output: `*_step2_dropped.jsonl` (if dropped) or `drop_reason` field

**Suffix removal attempt** (lines 115-173):
- If exact match fails, remove suffix patterns and retry
- Patterns: `(1년50%)`, `(최초1회한)`, `(갱신형_10년)`, etc.

---

## Step3: Evidence Resolution

**Module**: `pipeline/step3_evidence_resolver/resolver.py`

### Input Contract

**File**: `*_step2_canonical_scope_v1.jsonl`

**Required fields**: `coverage_name_raw`, `coverage_code`, `canonical_name`, `ins_cd`

**Documents**: PDF documents (same as Step1 input)

### Output Contract

**File**: `*_step3_evidence_enriched_v1.jsonl`

**Added fields**:
```json
{
  "evidence": [
    {
      "doc_type": "가입설계서",
      "page": 6,
      "excerpt": "...",
      "locator": { "keyword": "회한", "line_num": 66, "is_table": false },
      "gate_status": "FOUND"
    }
  ],
  "evidence_slots": {
    "start_date": { "status": "UNKNOWN", "value": null, "reason": "..." },
    "payout_limit": { "status": "FOUND", "value": "30000000", ... }
  },
  "evidence_status": {
    "start_date": "UNKNOWN",
    "payout_limit": "FOUND",
    ...
  }
}
```

### Coverage Targeting

**Logic**: Process ALL Step2 coverages that have `coverage_code != null`.

**Filtering**: Coverages without coverage_code are skipped (or have evidence_status = UNKNOWN for all slots).

### Coverage Code Handling

**Status**: ✅ coverage_code PRESERVED from Step2.

**Usage**: Passed to gate validators (lines 76, 111).

**Code location**: `resolver.py:76`

```python
# Line 76
coverage_code = coverage.get("coverage_code")
```

**Decision impact**: ⚠️ MEDIUM - Used for G5 gate validation (coverage attribution).

### Coverage Name Usage

**coverage_name_raw**:
- Used for: **DOCUMENT SEARCH** (line 74, 108)
- Decision impact: ⚠️ CRITICAL - Determines which evidence is found

**Code location**: `resolver.py:74`

```python
# Line 74
coverage_name = coverage.get("coverage_name_raw", "")
```

**Evidence search**:
- Search documents for keywords related to coverage_name_raw
- Pattern matching on document text

**⚠️ STRING MATCHING**: Evidence search uses coverage_name_raw string patterns.

### Evidence Handling

**Evidence slots** (defined in `evidence_patterns.py`):
- `start_date` (보장개시일)
- `exclusions` (면책사항)
- `payout_limit` (지급한도/횟수)
- `reduction` (감액기간/비율)
- `entry_age` (가입나이)
- `waiting_period` (면책기간)
- `underwriting_condition` (STEP NEXT-76-A)
- `mandatory_dependency`
- `payout_frequency`
- `industry_aggregate_limit`
- `daily_benefit_amount_won` (P2-FIX: Q11)
- `duration_limit_days` (P2-FIX: Q11)

**Search order** (line 84):
1. 가입설계서 (highest priority)
2. 상품요약서
3. 사업방법서
4. 약관 (lowest priority)

**Evidence locator**:
- `doc_type`: Document type
- `page`: Page number
- `excerpt`: Text snippet (200 chars)
- `locator`: { keyword, line_num, is_table }

**Slot resolution** (lines 102-118):
- For each slot, search documents for pattern
- If found: `status = "FOUND"`, extract value
- If not found: `status = "UNKNOWN"`
- If conflicting: `status = "CONFLICT"`

### Failure/Drop Conditions

**No evidence found**:
- All slots → `status = "UNKNOWN"`
- Record is NOT dropped (preserved for Step4)

**Gate failures**:
- G3: Conflicting values → `status = "CONFLICT"`
- G5: Evidence attribution failure → `notes` field warning

**Document unavailable**:
- No documents → all slots `status = "UNKNOWN"`, `reason = "No documents available"`

---

## Step4: Comparison Model

**Module**: `pipeline/step4_compare_model/builder.py`

### Input Contract

**File**: `*_step3_evidence_enriched_v1_gated.jsonl`

**Required fields**: All Step3 fields (coverage_code, evidence_slots, etc.)

### Output Contract

**Files**:
1. `compare_rows_v1.jsonl` - Individual coverage rows
2. `compare_tables_v1.jsonl` - Grouped by coverage_code

**Structure** (compare_rows_v1.jsonl):
```json
{
  "identity": {
    "insurer_key": "meritz",
    "product_key": "meritz__...",
    "variant_key": "default",
    "coverage_code": "A4200_1",
    "coverage_title": "암진단비",
    "coverage_name_raw": "암진단비(유사암제외)"
  },
  "slots": {
    "start_date": { "status": "UNKNOWN", "value": null, "evidences": [...] },
    "payout_limit": { "status": "FOUND", "value": "30000000", "evidences": [...] }
  },
  "meta": {
    "slot_status_summary": { "FOUND": 13, "CONFLICT": 1 },
    "has_conflict": true,
    "unanchored": false
  }
}
```

**Structure** (compare_tables_v1.jsonl):
```json
{
  "coverage_code": "A4200_1",
  "coverage_title": "암진단비",
  "rows": [
    { /* CompareRow for Meritz */ },
    { /* CompareRow for Hanwha */ },
    ...
  ],
  "common_slots": {
    "start_date": { "values": [...] },
    "payout_limit": { "values": [...] }
  }
}
```

### Coverage Targeting

**Logic**: Process ALL Step3 coverages.

**Grouping**: Group by `coverage_code` into tables.

**Filtering**:
- Coverages without coverage_code → `unanchored = true` (marked but not dropped)

### Coverage Code Handling

**Status**: ✅ coverage_code PRESERVED from Step3.

**Usage**:
1. Build `CoverageIdentity` (line 111-119)
2. Group coverages into tables (by coverage_code)
3. Determine `unanchored` status (line 99)

**Code location**: `builder.py:99`

```python
# Line 99
unanchored = not bool(identity.coverage_code)
```

**Decision impact**: ⚠️ HIGH - Determines if coverage can be compared across insurers.

### Coverage Name Usage

**coverage_name_raw**:
- Preserved in `identity.coverage_name_raw`
- Used for: Display only (NO decision logic)

**coverage_title**:
- Extracted from coverage_name_raw (remove suffix patterns)
- Used for: Grouping display name

**Code location**: `model.py:23-25` (extract_coverage_title)

```python
# Extract coverage_title by removing metadata suffixes
def extract_coverage_title(coverage_name_raw: str) -> str:
    # Remove (1년50%), (최초1회한), etc.
    return re.sub(r'\(.*?\)$', '', coverage_name_raw).strip()
```

### Evidence Handling

**Evidence preservation**: ALL evidence from Step3 is embedded in `slots.{slot_name}.evidences`.

**Evidence structure** (per slot):
```json
{
  "status": "FOUND",
  "value": "30000000",
  "evidences": [
    {
      "doc_type": "가입설계서",
      "page": 6,
      "excerpt": "...",
      "locator": { ... },
      "gate_status": "FOUND"
    }
  ],
  "notes": null,
  "source_kind": "DOC_EVIDENCE",
  "confidence": { "level": "HIGH", "basis": "가입설계서" }
}
```

**Slot gates** (lines 64-65):
- SlotGateValidator: Validates slot-level trust
- SlotTierEnforcementGate: Enforces tier hierarchy

### Failure/Drop Conditions

**No drop conditions** at this stage.

**Warning flags**:
- `unanchored = true`: Coverage has no coverage_code
- `has_conflict = true`: At least one slot has CONFLICT status

**Table grouping**:
- Only coverages with same coverage_code are grouped into same table
- Unanchored coverages are NOT grouped (each forms separate table)

---

## Data Flow Summary (A4200_1 Example)

### Step1 Output (Meritz)

```json
{
  "coverage_name_raw": "암진단비(유사암제외)",
  "ins_cd": "M01",
  "insurer_key": "meritz",
  "product": { ... },
  "proposal_facts": { ... }
}
```

**Key**: NO coverage_code

### Step2 Output (Meritz)

```json
{
  "coverage_name_raw": "암진단비(유사암제외)",
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "mapping_method": "exact",
  "mapping_confidence": "HIGH",
  ... /* Step1 fields preserved */
}
```

**Key**: coverage_code ADDED via string matching on coverage_name_raw

### Step3 Output (Meritz)

```json
{
  "coverage_name_raw": "암진단비(유사암제외)",
  "coverage_code": "A4200_1",
  "evidence": [ /* 40+ evidence items */ ],
  "evidence_slots": {
    "start_date": { "status": "UNKNOWN", ... },
    "payout_limit": { "status": "FOUND", "value": "30000000", ... }
  },
  "evidence_status": { ... },
  ... /* Step1+Step2 fields preserved */
}
```

**Key**: Evidence added via document search using coverage_name_raw

### Step4 Output (Meritz)

```json
{
  "identity": {
    "insurer_key": "meritz",
    "coverage_code": "A4200_1",
    "coverage_title": "암진단비",
    "coverage_name_raw": "암진단비(유사암제외)"
  },
  "slots": {
    "payout_limit": {
      "status": "FOUND",
      "value": "30000000",
      "evidences": [ /* from Step3 */ ]
    }
  },
  "meta": {
    "unanchored": false,
    "has_conflict": true
  }
}
```

**Key**: Restructured, evidence embedded in slots, grouped by coverage_code

---

## Coverage Code Decision Path

### Creation Point

**Step2-b**: `map_to_canonical.py:75-114`

**Trigger**: coverage_name_raw lookup in mapping Excel

**Deterministic**: YES (dict lookup, no LLM)

### Validation Points

**Step3**: `resolver.py:76` - Passed to gate validators

**Step4**: `builder.py:99` - Used to determine `unanchored` status

### Modification Points

**NONE** - coverage_code is NEVER modified after Step2-b creation

### Drop Conditions

**Step2-b**: If mapping fails → record may be dropped (or `coverage_code = null`)

**Step3/Step4**: Records with `coverage_code = null` are processed but marked as `unanchored = true`

---

## String Matching Decision Points

### Step2-b: Mapping

**File**: `map_to_canonical.py:31-45, 75-114`

**Usage**: coverage_name_raw → coverage_code mapping

**Impact**: ⚠️ CRITICAL - Determines if coverage gets coverage_code

**Patterns**:
- Exact match: `coverage_name_raw == mapping_key`
- Normalized match: `normalize(coverage_name_raw) == normalize(mapping_key)`
- Alias match: `coverage_name_raw == insurer_specific_name`

### Step3: Evidence Search

**File**: `resolver.py:74, 108`

**Usage**: coverage_name_raw → document search keyword

**Impact**: ⚠️ CRITICAL - Determines which evidence is found

**Patterns**: (defined in `evidence_patterns.py`)
- Keyword search: coverage_name_raw substring in document text
- Regex patterns for slot-specific keywords

### Step4: Coverage Title Extraction

**File**: `model.py:23-25`

**Usage**: coverage_name_raw → coverage_title (display)

**Impact**: ⚠️ LOW - Display only, no decision logic

**Pattern**: Remove suffix `\(.*?\)$`

---

## Evidence Attribution

### Step3: Creation

**Locator**: Per-evidence item
```json
{
  "doc_type": "가입설계서",
  "page": 6,
  "excerpt": "...",
  "locator": { "keyword": "회한", "line_num": 66, "is_table": false }
}
```

**Attribution method**:
1. Search documents for coverage_name_raw keywords
2. For each slot, search for slot-specific patterns (e.g., "보장개시일", "지급한도")
3. Extract text snippets with locators

**Issue**: Evidence search uses coverage_name_raw, NOT coverage_code → can match wrong coverage if names are similar

### Step4: Preservation

**Locator**: Embedded in `slots.{slot_name}.evidences`

**Structure**: All Step3 evidence preserved, no modification

---

## Known Issues (FACT ONLY)

### Issue 1: Contaminated Mapping Path

**Step**: Step2-b

**File**: `map_to_canonical.py:12`

**Fact**: Uses `data/sources/mapping/담보명mapping자료.xlsx` (264 rows)

**SSOT**: Should use `data/sources/insurers/담보명mapping자료.xlsx` (264 rows)

**Impact**: Unknown if they differ (not verified in this analysis)

### Issue 2: String-Based Evidence Search

**Step**: Step3

**File**: `resolver.py:74, 108`

**Fact**: Evidence search uses coverage_name_raw as keyword

**Issue**: If two coverages have similar names (e.g., "암진단비(유사암제외)" vs "유사암진단비"), evidence may cross-contaminate

**Evidence**: A4200_1_EVIDENCE_ATTRIBUTION_AUDIT.md documented Meritz A4200_1 evidence containing "유사암진단비" text (A4210)

### Issue 3: Coverage Code Assignment Depends on String Matching

**Step**: Step2-b

**File**: `map_to_canonical.py:75-114`

**Fact**: coverage_code assignment is determined by string matching (exact/normalized/alias)

**Issue**: If mapping Excel lacks a coverage name variant, coverage will not get coverage_code → unanchored

**Example**: If Excel has "암진단비(유사암제외)" but PDF has "암진단비 (유사암제외)" (extra space), normalized match may still work, but exact match fails

---

## DoD Checklist

- [✅] Step1-4 entry points identified
- [✅] Input/Output contracts documented with actual field examples
- [✅] Coverage targeting logic documented (who decides which coverages to process)
- [✅] coverage_code creation/validation/modification points traced
- [✅] coverage_name_raw usage documented (where it's used, what it decides)
- [✅] Evidence handling documented (creation, preservation, attribution)
- [✅] Failure/drop conditions documented
- [✅] A4200_1 example traced through all steps
- [✅] String matching decision points identified
- [✅] Known issues listed (FACT ONLY, no inference)

---

**END OF FACT MAP**
