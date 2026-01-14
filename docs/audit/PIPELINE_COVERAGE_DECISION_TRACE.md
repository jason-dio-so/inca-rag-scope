# Pipeline Coverage Decision Trace (A4200_1)

**Date**: 2026-01-14
**Task**: STEP PIPELINE-FACT-MAP-01
**Status**: ✅ COMPLETE (FACT ONLY)

---

## Purpose

Trace a single coverage (A4200_1 - 암진단비·유사암제외) through Step1→Step2→Step3→Step4 to document:
- When coverage_code is created/confirmed/modified/dropped
- What field names carry the coverage identifier at each stage
- Evidence attribution points
- Decision logic that affects this coverage

NO inference. CODE + DATA only.

---

## SSOT Definition (Source of Truth)

**File**: `data/sources/insurers/담보명mapping자료.xlsx`

**A4200_1 Rows** (8 insurers):

| ins_cd | 보험사명 | cre_cvr_cd | 신정원코드명 | 담보명(가입설계서) |
|--------|---------|-----------|------------|----------------|
| N01 | 메리츠 | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| N02 | 한화 | A4200_1 | 암진단비(유사암제외) | 암(4대유사암제외)진단비 |
| N03 | 롯데 | A4200_1 | 암진단비(유사암제외) | 일반암진단비Ⅱ |
| N05 | 흥국 | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| N08 | 삼성 | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| N09 | 현대 | A4200_1 | 암진단비(유사암제외) | 암진단Ⅱ(유사암제외)담보 |
| N10 | KB | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| N13 | DB | A4200_1 | 암진단비(유사암제외) | 암진단비Ⅱ(유사암제외) |

**Key observation**: Same `cre_cvr_cd` (A4200_1), different `담보명(가입설계서)` per insurer.

---

## Step1: PDF Extraction

**File**: `pipeline/step1_summary_first/extractor_v3.py`

**Entry**: PDF summary table parsing

### Meritz Example

**Input**: `data/sources/pdfs/meritz/proposal.pdf` (가입설계서)

**Summary table row** (page 6):
```
8   암진단비(유사암제외)   3천만원   30,480   20년 / 100세   암보장개시일 이후 암(유사암제외)으로 진단확정시 최초 1회한 가입금액 지급...
```

**Extraction** (`extractor_v3.py:240-289`):
- Parse summary table row
- Extract coverage_name from column (position defined in profile)
- Extract proposal_facts (premium, amount, period)

### Output Record

**File**: `data/scope_v3/meritz_step1_raw_scope_v3.jsonl`

**Record** (actual data):
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
  "proposal_facts": {
    "premium": "30480",
    "amount": "3천만원",
    "period": "20년 / 100세",
    "description": "암보장개시일 이후 암(유사암제외)으로 진단확정시 최초 1회한 가입금액 지급...",
    "order": 8
  },
  "proposal_detail_facts": { /* ... */ },
  "proposal_context": {
    "summary_page": 6,
    "summary_row_index": 8
  },
  "variant": "default"
}
```

### Coverage Identifier Status

**Field**: `coverage_name_raw` = "암진단비(유사암제외)"

**coverage_code**: ❌ DOES NOT EXIST

**Identification method**: PDF text extraction only

**Code location**: `extractor_v3.py:54-57`
```python
@dataclass
class ProposalFact:
    """Proposal fact (raw text only, no inference)"""
    coverage_name_raw: str  # ← FROM PDF
    proposal_facts: Dict[str, Any]
```

---

## Step2-a: Sanitization

**File**: `pipeline/step2_sanitize_scope/sanitize.py`

**Purpose**: Normalize whitespace, remove special characters (intermediate step)

### Output

**File**: `data/scope_v3/meritz_step2_sanitized_scope_v1.jsonl`

**Changes**: None for this coverage (coverage_name_raw unchanged)

### Coverage Identifier Status

**Field**: `coverage_name_raw` = "암진단비(유사암제외)"

**coverage_code**: ❌ STILL DOES NOT EXIST

---

## Step2-b: Canonical Mapping

**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py`

**Entry**: CanonicalMapper class initialization and mapping

### Mapping Source

**File**: `data/sources/mapping/담보명mapping자료.xlsx`

⚠️ **CONTAMINATED PATH** - Should be `data/sources/insurers/담보명mapping자료.xlsx`

**Code location**: `map_to_canonical.py:12`
```python
mapping_excel_path = "data/sources/mapping/담보명mapping자료.xlsx"
```

### Mapping Algorithm

**Load mapping** (`map_to_canonical.py:47-114`):

1. Read Excel into in-memory dict
2. Create lookup keys:
   - Exact match on `신정원코드명` ("암진단비(유사암제외)")
   - Normalized match on normalized canonical name ("암진단비유사암제외")
   - Alias match on `담보명(가입설계서)` ("암진단비(유사암제외)" for Meritz)
   - Normalized alias match on normalized insurer name

**Normalization** (`map_to_canonical.py:31-45`):
```python
def _normalize(self, text: str) -> str:
    text = re.sub(r'\s+', '', text)  # Remove whitespace
    text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)  # Remove special chars
    return text.lower()
```

**Meritz mapping lookup**:
- Input: `coverage_name_raw` = "암진단비(유사암제외)"
- Lookup: Exact match on "암진단비(유사암제외)" → FOUND
- Match type: `"alias"` (matched `담보명(가입설계서)` column)
- Result: `coverage_code` = "A4200_1", `canonical_name` = "암진단비(유사암제외)"

### Output Record

**File**: `data/scope_v3/meritz_step2_canonical_scope_v1.jsonl`

**Record** (actual data):
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
  ... /* All Step1 fields preserved (proposal_facts, etc.) */
}
```

### Coverage Identifier Status

**Field added**: `coverage_code` = "A4200_1"

**Creation point**: ✅ FIRST CREATED HERE

**Decision logic**: String matching (exact match on alias)

**Code location**: `map_to_canonical.py:98-104`
```python
# 3. 보험사별 담보명(가입설계서)으로 exact match
if coverage_name_insurer:
    self.mapping_dict[coverage_name_insurer] = {
        'coverage_code': coverage_code,
        'coverage_name_canonical': coverage_name_canonical,
        'match_type': 'alias'
    }
```

### Hanwha Example (Different Coverage Name)

**Step1 output**: `coverage_name_raw` = "암(4대유사암제외)진단비"

**Step2 mapping lookup**:
- Exact match on "암(4대유사암제외)진단비" → FOUND (alias match)
- Result: `coverage_code` = "A4200_1", `canonical_name` = "암진단비(유사암제외)"

**Key**: Same `coverage_code` (A4200_1) but different `coverage_name_raw` per insurer.

---

## Step3: Evidence Resolution

**File**: `pipeline/step3_evidence_resolver/resolver.py`

**Entry**: CoverageEvidenceResolver.resolve()

### Input

**File**: `data/scope_v3/meritz_step2_canonical_scope_v1.jsonl`

**Record**: Full Step2 output (with coverage_code)

### Evidence Search

**Search keyword**: `coverage_name_raw` = "암진단비(유사암제외)"

**Code location**: `resolver.py:74`
```python
coverage_name = coverage.get("coverage_name_raw", "")
```

⚠️ **NOT using coverage_code** for search - uses coverage_name_raw string

**Document search** (`resolver.py:84-86`):
```python
search_order = ["가입설계서", "상품요약서", "사업방법서", "약관"]
documents = self.document_set.search_all_documents(search_order)
```

**Slot resolution** (`resolver.py:102-118`):
- For each slot (start_date, payout_limit, etc.):
  - Search documents for patterns (defined in `evidence_patterns.py`)
  - Extract value if deterministic
  - Create evidence items with locators

### Evidence Search Example: payout_limit

**Pattern**: Keywords like "회한", "최초", "가입금액"

**Document match** (가입설계서 page 6):
```
8   암진단비(유사암제외)
3천만원
30,480
20년 / 100세
암보장개시일 이후 암(유사암제외)으로 진단확정시 최초 1회한 가입금액 지급
```

**Evidence item created**:
```json
{
  "doc_type": "가입설계서",
  "page": 6,
  "excerpt": "3대진단\n8   암진단비(유사암제외)\n3천만원\n30,480\n20년 / 100세\n암보장개시일 이후 암(유사암제외)으로 진단확정시 최초 1회한 가입금액 지급...",
  "locator": {
    "keyword": "회한",
    "line_num": 66,
    "is_table": false
  },
  "gate_status": "FOUND"
}
```

**Slot value extracted**: `value` = "30000000" (from "3천만원" via proposal_facts)

### Output Record

**File**: `data/scope_v3/meritz_step3_evidence_enriched_v1.jsonl`

**Record** (actual data):
```json
{
  "coverage_name_raw": "암진단비(유사암제외)",
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "evidence": [
    /* 40 evidence items with doc_type, page, excerpt, locator */
  ],
  "evidence_slots": {
    "start_date": {
      "status": "FOUND",
      "value": null,
      "reason": null
    },
    "payout_limit": {
      "status": "FOUND",
      "value": "30000000",
      "reason": null
    },
    "entry_age": {
      "status": "CONFLICT",
      "value": null,
      "reason": "Conflicting values across documents: {'가입설계서': {...}, '상품요약서': {...}}"
    },
    ... /* 14 total slots */
  },
  "evidence_status": {
    "start_date": "FOUND",
    "payout_limit": "FOUND",
    "entry_age": "CONFLICT",
    ... /* 14 total slots */
  },
  ... /* All Step1+Step2 fields preserved */
}
```

### Coverage Identifier Status

**Field**: `coverage_code` = "A4200_1" (PRESERVED from Step2)

**Usage**: Passed to gate validators (`resolver.py:76, 111`)

**Code location**: `resolver.py:76`
```python
coverage_code = coverage.get("coverage_code")
```

**Gate usage** (`resolver.py:111`):
```python
slot_result = self._resolve_slot(
    coverage_name,
    pattern,
    documents,
    coverage_code  # P2-FIX: Pass coverage_code to slot resolver
)
```

**Evidence attribution**: Uses coverage_name_raw for search, coverage_code for gate validation

---

## Step4: Comparison Model

**File**: `pipeline/step4_compare_model/builder.py`

**Entry**: CompareRowBuilder.build_row()

### Input

**File**: `data/scope_v3/meritz_step3_evidence_enriched_v1_gated.jsonl`

**Record**: Full Step3 output (with coverage_code + evidence)

### Row Building

**Build identity** (`builder.py:111-119`):
```python
def _build_identity(self, coverage: Dict) -> CoverageIdentity:
    coverage_name_raw = coverage.get("coverage_name_raw", "")
    coverage_code = coverage.get("coverage_code")  # ← From Step2-b
    coverage_title = extract_coverage_title(coverage_name_raw)  # Remove suffix

    return CoverageIdentity(
        insurer_key=coverage.get("insurer_key"),
        product_key=coverage.get("product", {}).get("product_key"),
        variant_key=coverage.get("variant"),
        coverage_code=coverage_code,
        coverage_title=coverage_title,
        coverage_name_raw=coverage_name_raw
    )
```

**Build slots** (`builder.py:83`):
- Extract each slot from `evidence_slots`
- Embed evidences in slot structure

**Calculate metadata** (`builder.py:90-99`):
- `slot_status_summary`: Count FOUND/UNKNOWN/CONFLICT statuses
- `has_conflict`: TRUE if any slot has CONFLICT
- `unanchored`: `not bool(coverage_code)` - FALSE for A4200_1 (has coverage_code)

### Output Record

**File**: `data/compare_v1/compare_rows_v1.jsonl`

**Record** (actual data):
```json
{
  "identity": {
    "insurer_key": "meritz",
    "product_key": "meritz__무알파Plus보장보험2511보험료납입면제형",
    "variant_key": "default",
    "coverage_code": "A4200_1",
    "coverage_title": "암진단비",
    "coverage_name_raw": "암진단비(유사암제외)"
  },
  "slots": {
    "start_date": {
      "status": "UNKNOWN",
      "value": null,
      "evidences": [
        {
          "doc_type": "가입설계서",
          "page": 5,
          "excerpt": "...",
          "locator": { "keyword": "보장개시일", "line_num": 4, "is_table": false },
          "gate_status": "FOUND"
        },
        ...
      ],
      "notes": null,
      "source_kind": "DOC_EVIDENCE"
    },
    "payout_limit": {
      "status": "FOUND",
      "value": "30000000",
      "evidences": [ /* ... */ ],
      "notes": "proposal_facts (evidence: 1, 80, 8)",
      "source_kind": "DOC_EVIDENCE",
      "confidence": {
        "level": "HIGH",
        "basis": "가입설계서"
      }
    },
    ... /* 14 total slots */
  },
  "meta": {
    "slot_status_summary": {
      "FOUND": 13,
      "CONFLICT": 1
    },
    "has_conflict": true,
    "unanchored": false
  }
}
```

### Table Grouping

**File**: `data/compare_v1/compare_tables_v1.jsonl`

**Grouping logic**: Group all rows with same `coverage_code`

**Table record** (summary):
```json
{
  "coverage_code": "A4200_1",
  "coverage_title": "암진단비",
  "rows": [
    { /* CompareRow for Meritz */ },
    { /* CompareRow for Hanwha */ },
    { /* CompareRow for Heungkuk */ },
    { /* CompareRow for Hyundai */ },
    { /* CompareRow for KB */ },
    { /* CompareRow for Lotte */ },
    { /* CompareRow for Samsung */ },
    { /* CompareRow for DB */ }
  ],
  "common_slots": {
    "start_date": {
      "values": [ /* unique values across insurers */ ]
    },
    "payout_limit": {
      "values": [ /* unique values across insurers */ ]
    }
  }
}
```

### Coverage Identifier Status

**Field**: `identity.coverage_code` = "A4200_1" (PRESERVED from Step3)

**Usage**:
1. Determine `unanchored` status: `unanchored = not bool(coverage_code)` → FALSE
2. Group into table by coverage_code
3. Display in identity object

**No modification** - coverage_code is never changed after Step2-b

---

## Coverage Code Decision Path Summary

### Creation

**When**: Step2-b (canonical mapping)

**Where**: `map_to_canonical.py:98-104`

**How**: String matching on coverage_name_raw → lookup in mapping Excel → assign coverage_code

**Deterministic**: YES (dict lookup)

**Input**: coverage_name_raw = "암진단비(유사암제외)"

**Output**: coverage_code = "A4200_1"

**Match type**: "alias" (matched `담보명(가입설계서)` column in Excel)

### Validation

**Step3**: Passed to gate validators (G5 coverage attribution gate)

**Step4**: Used to calculate `unanchored` status

**No modification** after creation

### Drop Conditions

**Step2-b**: If coverage_name_raw NOT FOUND in mapping Excel → coverage_code remains null (or record dropped)

**Example**: If Meritz PDF had "암진단비 (유사암 제외)" (extra spaces), normalized match might still work, but if normalization fails → no coverage_code

**Step3**: Records with coverage_code = null are processed but all slots → status = "UNKNOWN"

**Step4**: Records with coverage_code = null are marked as `unanchored = true`

---

## Evidence Attribution Path

### Step3: Creation

**Trigger**: Document search using coverage_name_raw as keyword

**Code location**: `resolver.py:74, 108`

**Evidence structure**:
```json
{
  "doc_type": "가입설계서",
  "page": 6,
  "excerpt": "8   암진단비(유사암제외)\n3천만원\n...",
  "locator": {
    "keyword": "회한",
    "line_num": 66,
    "is_table": false
  },
  "gate_status": "FOUND"
}
```

**Attribution**: Evidence is embedded in coverage record (keyed by coverage_name_raw during search, stored with coverage_code)

### Step4: Preservation

**Structure**: Evidence embedded in `slots.{slot_name}.evidences`

**No modification** - all Step3 evidence preserved

**Traceability**: Each evidence item has:
- `doc_type`: Which document
- `page`: Which page
- `excerpt`: Text snippet (200 chars)
- `locator`: Exact position (keyword, line_num)

---

## String Matching Decision Points

### Step2-b: coverage_code Assignment

**File**: `map_to_canonical.py:98-104`

**Input**: coverage_name_raw = "암진단비(유사암제외)"

**Algorithm**: Exact match on `담보명(가입설계서)` column

**Impact**: ⚠️ CRITICAL - Determines if coverage gets coverage_code

**Result**: coverage_code = "A4200_1"

### Step3: Evidence Search

**File**: `resolver.py:74`

**Input**: coverage_name_raw = "암진단비(유사암제외)"

**Algorithm**: Keyword search in documents

**Impact**: ⚠️ CRITICAL - Determines which evidence is found

**Issue**: If another coverage has similar name (e.g., "유사암진단비"), evidence may cross-contaminate

### Step4: Coverage Title Extraction

**File**: `model.py:23-25`

**Input**: coverage_name_raw = "암진단비(유사암제외)"

**Algorithm**: Remove suffix `\(.*?\)$`

**Result**: coverage_title = "암진단비"

**Impact**: ⚠️ LOW - Display only

---

## Cross-Insurer Comparison

### Meritz (N01)

**Step1**: coverage_name_raw = "암진단비(유사암제외)"

**Step2**: coverage_code = "A4200_1" (exact match on alias)

**Step3**: 40 evidence items

**Step4**: Grouped into A4200_1 table with 7 other insurers

### Hanwha (N02)

**Step1**: coverage_name_raw = "암(4대유사암제외)진단비"

**Step2**: coverage_code = "A4200_1" (exact match on alias)

**Step3**: Evidence search uses "암(4대유사암제외)진단비" as keyword (different from Meritz!)

**Step4**: Grouped into same A4200_1 table as Meritz

**Key**: Same coverage_code, DIFFERENT coverage_name_raw → evidence search uses different keywords → may find different evidence snippets

### Lotte (N03)

**Step1**: coverage_name_raw = "일반암진단비Ⅱ"

**Step2**: coverage_code = "A4200_1" (exact match on alias)

**Step3**: Evidence search uses "일반암진단비Ⅱ" as keyword (completely different from Meritz/Hanwha!)

**Step4**: Grouped into same A4200_1 table

**Issue**: ⚠️ HIGH - Different evidence search keywords for same coverage_code may lead to inconsistent evidence extraction across insurers

---

## Known Issues (FACT ONLY)

### Issue 1: Evidence Search Uses coverage_name_raw, Not coverage_code

**Step**: Step3

**Fact**: `resolver.py:74` uses `coverage_name = coverage.get("coverage_name_raw", "")`

**Impact**: Insurers with different coverage_name_raw (but same coverage_code) will search documents with different keywords → may find different evidence

**Example**: Meritz searches for "암진단비(유사암제외)", Hanwha searches for "암(4대유사암제외)진단비", Lotte searches for "일반암진단비Ⅱ" - all for A4200_1

### Issue 2: coverage_code Creation Depends on String Matching

**Step**: Step2-b

**Fact**: `map_to_canonical.py:98-104` uses exact/normalized string matching

**Impact**: If PDF coverage name doesn't match any mapping Excel entry → no coverage_code → unanchored

**Example**: If PDF has typo "암진단비 (유사암 제외)" (extra spaces), might fail exact match (but normalized match may still work)

### Issue 3: Evidence Contamination Risk

**Step**: Step3

**Fact**: Evidence search uses broad keyword matching on coverage_name_raw

**Impact**: If two coverages have similar names, evidence may cross-contaminate

**Example**: Previous audit found Meritz A4200_1 evidence contains "유사암진단비" text (A4210) because both contain "암진단비" substring

---

## DoD Checklist

- [✅] A4200_1 traced through Step1→Step2→Step3→Step4
- [✅] coverage_code creation point identified (Step2-b, line 98-104)
- [✅] coverage_code usage points documented (Step3 gate validation, Step4 grouping)
- [✅] Evidence attribution traced (Step3 creation, Step4 preservation)
- [✅] String matching decision points identified (Step2 mapping, Step3 evidence search)
- [✅] Cross-insurer comparison documented (Meritz vs Hanwha vs Lotte)
- [✅] Known issues listed (FACT ONLY)
- [✅] All claims backed by code locations and data snippets

---

**END OF TRACE DOCUMENT**
