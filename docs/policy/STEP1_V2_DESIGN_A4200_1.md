# Step1 V2 Design: Targeted Extraction (A4200_1 Example)

**Date**: 2026-01-14
**Task**: STEP PIPELINE-REDESIGN-CONSTITUTION-02 (Step1 V2 Detailed Design)
**Target**: A4200_1 (암진단비·유사암제외) - 메리츠, 한화
**Status**: ✅ COMPLETE (DESIGN SPEC)

---

## Constitutional Premise (IMMUTABLE)

1. ❌ **PDF에서 담보를 '찾지' 마라** - Discovery 금지
2. ✅ **coverage_code는 SSOT에서 주어진다** - Input, not output
3. ✅ **PDF에서는 proposal_facts만 추출** - 보험금, 기간, 보험료
4. ❌ **SSOT target과 매칭 안되면 무시** - Unmatched row는 skip
5. ❌ **coverage_name_raw는 식별자로 사용 금지** - coverage_code only

---

## Part 1: Input Schema

### Input 1: SSOT Target List

**Source**: `data/sources/insurers/담보명mapping자료.xlsx`

**Filter**: A4200_1 rows only

**Loaded data** (example):

```json
[
  {
    "coverage_code": "A4200_1",
    "canonical_name": "암진단비(유사암제외)",
    "ins_cd": "N01",
    "insurer_coverage_name": "암진단비(유사암제외)"
  },
  {
    "coverage_code": "A4200_1",
    "canonical_name": "암진단비(유사암제외)",
    "ins_cd": "N02",
    "insurer_coverage_name": "암(4대유사암제외)진단비"
  }
]
```

**Key fields**:
- `coverage_code` - Coverage identifier (A4200_1)
- `canonical_name` - Canonical coverage name
- `insurer_coverage_name` - Insurer-specific name (from 담보명(가입설계서) column)
- `ins_cd` - Insurer code (N01 = 메리츠, N02 = 한화) **← ONLY identifier from SSOT**

**Critical**: `coverage_code` is INPUT, not OUTPUT (from SSOT, not derived)

---

### Input 2: PDF Files

**Source**: 가입설계서 PDF (summary table on page 3)

**Example PDF rows** (메리츠):

| 분류 | 번호 | 담보명 | 가입금액 | 보험료 | 보험기간/납입기간 |
|------|------|--------|----------|--------|------------------|
| 3대진단 | 8 | 암진단비(유사암제외) | 3천만원 | 30,480 | 20년 / 100세 |

**Example PDF rows** (한화):

| 번호 | 담보명 | 가입금액 | 보험료 | 보험기간/납입기간 |
|------|--------|----------|--------|------------------|
| 45 | 암(4대유사암제외)진단비 | 3,000만원 | 34,230원 | 100세만기 / 20년납 |

**Key observation**:
- 메리츠 PDF: "암진단비(유사암제외)" (exact match with SSOT)
- 한화 PDF: "암(4대유사암제외)진단비" (differs from SSOT "암진단비(유사암제외)")

---

### Input 3: Profile JSON

**Source**: `profiles/{insurer}.json` (PDF structure metadata)

**Purpose**: Define summary table location, column mappings

**Example** (meritz):
```json
{
  "summary_pages": [3],
  "summary_columns": {
    "coverage_name": 2,
    "coverage_amount": 3,
    "premium": 4,
    "period": 5
  }
}
```

---

## Part 2: Step1 V2 Logic (4 Phases)

### Phase 1: Load SSOT Targets

**Function**: `load_ssot_targets(ins_cd: str) -> List[CoverageTarget]`

**Logic**:
```python
def load_ssot_targets(ins_cd: str) -> List[CoverageTarget]:
    """
    Load SSOT coverage targets for this insurer.

    Args:
        ins_cd: Insurer code from SSOT (N01, N02, ...)

    Returns:
        List of CoverageTarget with coverage_code, canonical_name, insurer_coverage_name
    """
    # Read SSOT Excel
    df = pd.read_excel('data/sources/insurers/담보명mapping자료.xlsx')

    # Filter by ins_cd (from SSOT)
    insurer_rows = df[df['ins_cd'] == ins_cd]

    # Convert to CoverageTarget list
    targets = []
    for _, row in insurer_rows.iterrows():
        targets.append(CoverageTarget(
            coverage_code=row['cre_cvr_cd'],  # A4200_1
            canonical_name=row['신정원코드명'],  # 암진단비(유사암제외)
            insurer_coverage_name=row['담보명(가입설계서)'],  # N01: "암진단비(유사암제외)", N02: "암(4대유사암제외)진단비"
            ins_cd=row['ins_cd']  # N01, N02, ... (from SSOT)
        ))

    return targets
```

**Output** (for A4200_1 target):
```python
[
    CoverageTarget(
        coverage_code="A4200_1",
        canonical_name="암진단비(유사암제외)",
        insurer_coverage_name="암진단비(유사암제외)",  # 메리츠
        ins_cd="N01"  # ← ONLY identifier (from SSOT)
    )
]
```

**Critical**: This function provides coverage_code as INPUT to Step1 V2 (not output)

---

### Phase 2: Parse PDF Summary Table

**Function**: `parse_pdf_summary(pdf_path: str, profile: dict) -> List[PDFRow]`

**Logic** (same as current Step1):
```python
def parse_pdf_summary(pdf_path: str, profile: dict) -> List[PDFRow]:
    """
    Parse PDF summary table to extract coverage rows.

    Args:
        pdf_path: Path to PDF file
        profile: Profile JSON with summary_pages, summary_columns

    Returns:
        List of PDFRow with coverage_name_raw, proposal_facts
    """
    # Parse PDF using pdfplumber
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in profile['summary_pages']:
            page = pdf.pages[page_num - 1]
            table = page.extract_table()

            # Extract coverage rows
            for row in table:
                coverage_name = row[profile['summary_columns']['coverage_name']]
                amount = row[profile['summary_columns']['coverage_amount']]
                premium = row[profile['summary_columns']['premium']]
                period = row[profile['summary_columns']['period']]

                rows.append(PDFRow(
                    coverage_name_raw=coverage_name,
                    proposal_facts=ProposalFacts(
                        coverage_amount_text=amount,
                        premium_text=premium,
                        period_text=period
                    )
                ))

    return rows
```

**Output** (메리츠 example):
```python
[
    PDFRow(
        coverage_name_raw="암진단비(유사암제외)",
        proposal_facts=ProposalFacts(
            coverage_amount_text="3천만원",
            premium_text="30,480",
            period_text="20년 / 100세"
        )
    ),
    # ... other coverages
]
```

**Key**: coverage_name_raw is extracted but NOT used as identifier (only for matching)

---

### Phase 3: Match PDF Rows to SSOT Targets (NEW - Critical Phase)

**Function**: `match_pdf_to_ssot(pdf_rows: List[PDFRow], ssot_targets: List[CoverageTarget]) -> List[MatchedFact]`

**Logic**:
```python
def match_pdf_to_ssot(
    pdf_rows: List[PDFRow],
    ssot_targets: List[CoverageTarget]
) -> List[MatchedFact]:
    """
    Match PDF rows to SSOT targets.

    Matching strategy:
    1. Exact match: coverage_name_raw == insurer_coverage_name
    2. Normalized match: normalize(coverage_name_raw) == normalize(insurer_coverage_name)
    3. If no match → skip row (SSOT target not found in PDF)
    4. If multiple matches → use first match (or flag ambiguous)

    CRITICAL: This is NOT coverage_code assignment (Step2-b role).
    This is PDF row → SSOT target lookup only.

    Args:
        pdf_rows: List of rows from PDF
        ssot_targets: List of SSOT coverage targets

    Returns:
        List of MatchedFact with coverage_code (from SSOT) + proposal_facts (from PDF)
    """
    matched_facts = []

    for pdf_row in pdf_rows:
        # Try to find SSOT target matching this PDF row
        target = find_best_match(pdf_row.coverage_name_raw, ssot_targets)

        if target:
            # Match found → create MatchedFact
            matched_facts.append(MatchedFact(
                coverage_code=target.coverage_code,  # ← FROM SSOT (A4200_1)
                canonical_name=target.canonical_name,  # ← FROM SSOT
                coverage_name_raw=pdf_row.coverage_name_raw,  # ← FROM PDF (for audit)
                proposal_facts=pdf_row.proposal_facts,  # ← FROM PDF
                ssot_match_status="FOUND",
                match_method="exact"  # or "normalized"
            ))
        else:
            # No match → skip row (or log warning)
            logger.warning(f"PDF coverage not in SSOT: {pdf_row.coverage_name_raw}")
            # OPTION 1: Drop entirely (strict SSOT mode)
            # OPTION 2: Emit with ssot_match_status="NOT_FOUND" (for debugging)

    return matched_facts


def find_best_match(
    coverage_name_raw: str,
    ssot_targets: List[CoverageTarget]
) -> Optional[CoverageTarget]:
    """
    Find best matching SSOT target for PDF row.

    Matching rules:
    1. Exact match: coverage_name_raw == target.insurer_coverage_name
    2. Normalized match: normalize(coverage_name_raw) == normalize(target.insurer_coverage_name)
    3. No match: return None

    Returns:
        Matching CoverageTarget or None
    """
    # Try exact match first
    for target in ssot_targets:
        if coverage_name_raw == target.insurer_coverage_name:
            return target

    # Try normalized match
    normalized_input = normalize(coverage_name_raw)
    for target in ssot_targets:
        normalized_target = normalize(target.insurer_coverage_name)
        if normalized_input == normalized_target:
            return target

    # No match
    return None


def normalize(text: str) -> str:
    """
    Normalize text for matching.

    Rules:
    - Remove whitespace
    - Remove special chars: (), [], -, Ⅱ, 담보, etc.
    - Lowercase (if applicable)

    Example:
        "암진단비(유사암제외)" → "암진단비유사암제외"
        "암(4대유사암제외)진단비" → "암4대유사암제외진단비"
    """
    text = text.replace(" ", "")
    text = text.replace("(", "").replace(")", "")
    text = text.replace("[", "").replace("]", "")
    text = text.replace("-", "")
    text = text.replace("Ⅱ", "2")
    text = text.replace("Ⅲ", "3")
    text = text.replace("담보", "")
    return text
```

**Output** (메리츠 A4200_1 example):
```python
MatchedFact(
    coverage_code="A4200_1",  # ← FROM SSOT (input)
    canonical_name="암진단비(유사암제외)",  # ← FROM SSOT
    coverage_name_raw="암진단비(유사암제외)",  # ← FROM PDF (exact match)
    proposal_facts=ProposalFacts(
        coverage_amount_text="3천만원",
        premium_text="30,480",
        period_text="20년 / 100세"
    ),
    ssot_match_status="FOUND",
    match_method="exact"
)
```

**Output** (한화 A4200_1 example):
```python
MatchedFact(
    coverage_code="A4200_1",  # ← FROM SSOT (input)
    canonical_name="암진단비(유사암제외)",  # ← FROM SSOT
    coverage_name_raw="암(4대유사암제외)진단비",  # ← FROM PDF (differs from SSOT)
    proposal_facts=ProposalFacts(
        coverage_amount_text="3,000만원",
        premium_text="34,230원",
        period_text="100세만기 / 20년납"
    ),
    ssot_match_status="FOUND",
    match_method="normalized"  # ← Normalized match (not exact)
)
```

**Critical difference from Step2-b**:
- ❌ Step2-b: String match → CREATE coverage_code (assignment)
- ✅ Step1 V2: String match → LOOKUP coverage_code (from SSOT, already exists)

**String matching justification**:
- String matching is UNAVOIDABLE for PDF row → SSOT target lookup
- BUT: This is NOT coverage_code assignment (constitutional violation)
- This is PDF text → SSOT target identification (necessary for extraction)

---

### Phase 4: Clean Proposal Facts (Merge from Step2-a)

**Function**: `clean_proposal_facts(matched_facts: List[MatchedFact]) -> List[MatchedFact]`

**Logic**:
```python
def clean_proposal_facts(matched_facts: List[MatchedFact]) -> List[MatchedFact]:
    """
    Clean and normalize proposal_facts.

    Cleaning rules:
    - Parse coverage_amount_text: "3천만원" → 30000000 (int)
    - Parse premium_text: "30,480" → 30480 (int)
    - Parse period_text: "20년 / 100세" → {"payment": 20, "maturity": 100}

    Args:
        matched_facts: List of MatchedFact with raw proposal_facts

    Returns:
        List of MatchedFact with cleaned proposal_facts
    """
    for fact in matched_facts:
        # Parse amount
        amount_text = fact.proposal_facts.coverage_amount_text
        fact.proposal_facts.coverage_amount = parse_amount(amount_text)

        # Parse premium
        premium_text = fact.proposal_facts.premium_text
        fact.proposal_facts.premium = parse_premium(premium_text)

        # Parse period
        period_text = fact.proposal_facts.period_text
        fact.proposal_facts.period = parse_period(period_text)

    return matched_facts


def parse_amount(text: str) -> int:
    """
    Parse coverage amount text to integer.

    Examples:
        "3천만원" → 30000000
        "3,000만원" → 30000000
        "1억원" → 100000000
    """
    text = text.replace(",", "").replace(" ", "")

    if "억" in text:
        amount = int(text.replace("억원", "").replace("억", "")) * 100000000
    elif "천만" in text:
        amount = int(text.replace("천만원", "").replace("천만", "")) * 10000000
    elif "만" in text:
        amount = int(text.replace("만원", "").replace("만", "")) * 10000
    else:
        amount = int(text.replace("원", ""))

    return amount


def parse_premium(text: str) -> int:
    """
    Parse premium text to integer.

    Examples:
        "30,480" → 30480
        "34,230원" → 34230
    """
    text = text.replace(",", "").replace("원", "").replace(" ", "")
    return int(text)


def parse_period(text: str) -> dict:
    """
    Parse period text to structured dict.

    Examples:
        "20년 / 100세" → {"payment_years": 20, "maturity_age": 100}
        "100세만기 / 20년납" → {"payment_years": 20, "maturity_age": 100}
    """
    parts = text.split("/")

    payment = None
    maturity = None

    for part in parts:
        if "년" in part:
            payment = int(part.replace("년", "").replace("납", "").strip())
        if "세" in part:
            maturity = int(part.replace("세", "").replace("만기", "").strip())

    return {
        "payment_years": payment,
        "maturity_age": maturity
    }
```

**Output** (메리츠 A4200_1 with cleaned facts):
```python
MatchedFact(
    coverage_code="A4200_1",
    canonical_name="암진단비(유사암제외)",
    coverage_name_raw="암진단비(유사암제외)",
    proposal_facts=ProposalFacts(
        coverage_amount_text="3천만원",  # ← Raw (kept for audit)
        coverage_amount=30000000,  # ← Cleaned (int)
        premium_text="30,480",  # ← Raw
        premium=30480,  # ← Cleaned (int)
        period_text="20년 / 100세",  # ← Raw
        period={"payment_years": 20, "maturity_age": 100}  # ← Cleaned (dict)
    ),
    ssot_match_status="FOUND",
    match_method="exact"
)
```

**Key**: Both raw and cleaned values are kept for audit trail

---

## Part 3: Output Schema

### Step1 V2 Output Format

**File**: `data/scope_v3/{INS_CD}_step1_targeted_v2.jsonl` (e.g., `N01_step1_targeted_v2.jsonl`)

**Schema** (per line):
```json
{
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "ins_cd": "N01",
  "product": {
    "product_name_raw": "(무) 알파Plus보장보험2511 (해약환급금미지급형(납입률50%))(보험료 납입면제형)",
    "product_name_normalized": "무알파Plus보장보험2511보험료납입면제형"
  },
  "variant": {
    "variant_key": "default",
    "variant_axis": [],
    "variant_values": {}
  },
  "coverage_name_raw": "암진단비(유사암제외)",
  "proposal_facts": {
    "coverage_amount_text": "3천만원",
    "coverage_amount": 30000000,
    "premium_text": "30,480",
    "premium": 30480,
    "period_text": "20년 / 100세",
    "period": {
      "payment_years": 20,
      "maturity_age": 100
    },
    "evidences": [
      {
        "doc_type": "가입설계서",
        "page": 3,
        "row_index": 7,
        "raw_row": ["3대진단", "8", "암진단비(유사암제외)", "3천만원", "30,480", "20년 / 100세"]
      }
    ]
  },
  "ssot_match_status": "FOUND",
  "match_method": "exact"
}
```

**Key fields**:
- ✅ `coverage_code` - FROM SSOT (input, not derived)
- ✅ `canonical_name` - FROM SSOT
- ✅ `ins_cd` - FROM SSOT (ONLY insurer identifier)
- ⚠️ `coverage_name_raw` - FROM PDF (kept for audit, NOT identifier)
- ✅ `proposal_facts` - FROM PDF (extracted + cleaned)
- ✅ `ssot_match_status` - Match status (FOUND | NOT_FOUND | AMBIGUOUS)
- ✅ `match_method` - Match method (exact | normalized)

**Removed fields** (from legacy Step1):
- ❌ `insurer_key` - DEPRECATED (use ins_cd only)
- ❌ `product_key` - DEPRECATED (derived from insurer_key)

**Critical difference from current Step1**:
- ✅ NEW: `coverage_code` field exists (from SSOT)
- ✅ NEW: `canonical_name` field exists (from SSOT)
- ✅ NEW: `ssot_match_status` field (match quality indicator)
- ✅ NEW: Both raw and cleaned proposal_facts
- ✅ NEW: File path uses ins_cd (N01, N02, ...) not insurer_key

---

## Part 4: Comparison with Current Step1

### Architectural Differences

| Aspect | Current Step1 | Step1 V2 |
|--------|--------------|----------|
| **Paradigm** | Discovery (find all coverages) | Targeted (extract SSOT-defined only) |
| **Input** | PDF only | SSOT + PDF |
| **Coverage source** | PDF (discovered) | SSOT (pre-defined) |
| **coverage_code** | ❌ Does NOT exist | ✅ Exists from start (SSOT input) |
| **Insurer identifier** | insurer_key ("meritz") + ins_cd (M01) | ins_cd (N01) ONLY |
| **Identifier** | coverage_name_raw (string) | coverage_code (SSOT) |
| **Filtering** | None (extract all rows) | SSOT-driven (extract only targets) |
| **String matching** | None (Step2-b does it) | Yes (PDF → SSOT lookup) |
| **Unmatched rows** | Extracted anyway | Skipped (or flagged) |
| **Output count** | ~100 coverages (all PDF rows) | ~30 coverages (SSOT count) |
| **Output filename** | `meritz_step1_raw_scope_v3.jsonl` | `N01_step1_targeted_v2.jsonl` |
| **Step2-b dependency** | CRITICAL (creates coverage_code) | OPTIONAL (coverage_code already exists) |

---

### Data Flow Comparison

**Current Step1 → Step2-b flow**:
```
PDF
  → Step1: Extract ALL rows
    → coverage_name_raw (identifier)
    → NO coverage_code
  → Step2-b: Match coverage_name_raw → SSOT
    → CREATE coverage_code (string matching)
  → Output: coverage_code + proposal_facts
```

**Step1 V2 flow**:
```
SSOT
  → Load target list
    → coverage_code + metadata (INPUT)
PDF
  → Step1 V2: Parse rows
    → Match rows to SSOT targets (lookup)
    → Extract proposal_facts for matched rows
  → Output: coverage_code (from SSOT) + proposal_facts (from PDF)
```

**Critical difference**:
- ❌ OLD: coverage_code is OUTPUT (created by Step2-b)
- ✅ NEW: coverage_code is INPUT (from SSOT)

---

### Code Location Changes

| Component | Current Step1 | Step1 V2 |
|-----------|--------------|----------|
| **File** | `pipeline/step1_summary_first/extractor_v3.py` | `pipeline/step1_targeted_v2/extractor.py` (NEW) |
| **SSOT loader** | None | `load_ssot_targets(ins_cd)` (NEW) |
| **PDF parser** | `_extract_from_summary()` (line 240-289) | `parse_pdf_summary()` (same logic) |
| **Matcher** | None (Step2-b does it) | `match_pdf_to_ssot()` (NEW) |
| **Cleaner** | Step2-a does it | `clean_proposal_facts()` (merged into Step1 V2) |
| **Output file** | `{insurer_key}_step1_raw_scope_v3.jsonl` (e.g., `meritz_...`) | `{ins_cd}_step1_targeted_v2.jsonl` (e.g., `N01_...`) |
| **Insurer param** | `insurer_key` ("meritz") | `ins_cd` (N01) |

---

## Part 5: A4200_1 Extraction Example (Step-by-Step)

### Step-by-Step: 메리츠 A4200_1

**Phase 1: Load SSOT Targets**

Input: `ins_cd="N01"`

Output:
```python
CoverageTarget(
    coverage_code="A4200_1",
    canonical_name="암진단비(유사암제외)",
    insurer_coverage_name="암진단비(유사암제외)",
    ins_cd="N01"  # ← ONLY identifier (from SSOT)
)
# ... + 29 other coverage targets for N01 (메리츠)
```

---

**Phase 2: Parse PDF Summary Table**

Input: PDF page 3, row 7

PDF table:
```
| 3대진단 | 8 | 암진단비(유사암제외) | 3천만원 | 30,480 | 20년 / 100세 |
```

Output:
```python
PDFRow(
    coverage_name_raw="암진단비(유사암제외)",
    proposal_facts=ProposalFacts(
        coverage_amount_text="3천만원",
        premium_text="30,480",
        period_text="20년 / 100세"
    )
)
```

---

**Phase 3: Match PDF Row to SSOT Target**

Input:
- `pdf_row.coverage_name_raw` = "암진단비(유사암제외)"
- `ssot_target.insurer_coverage_name` = "암진단비(유사암제외)"

Matching:
```python
# Try exact match
if "암진단비(유사암제외)" == "암진단비(유사암제외)":
    return target  # ✅ MATCH FOUND (exact)
```

Output:
```python
MatchedFact(
    coverage_code="A4200_1",  # ← FROM SSOT
    canonical_name="암진단비(유사암제외)",  # ← FROM SSOT
    coverage_name_raw="암진단비(유사암제외)",  # ← FROM PDF
    proposal_facts=...,
    ssot_match_status="FOUND",
    match_method="exact"
)
```

---

**Phase 4: Clean Proposal Facts**

Input:
```python
proposal_facts=ProposalFacts(
    coverage_amount_text="3천만원",
    premium_text="30,480",
    period_text="20년 / 100세"
)
```

Cleaning:
```python
parse_amount("3천만원") → 30000000
parse_premium("30,480") → 30480
parse_period("20년 / 100세") → {"payment_years": 20, "maturity_age": 100}
```

Output:
```python
proposal_facts=ProposalFacts(
    coverage_amount_text="3천만원",  # ← Raw (kept)
    coverage_amount=30000000,  # ← Cleaned
    premium_text="30,480",
    premium=30480,
    period_text="20년 / 100세",
    period={"payment_years": 20, "maturity_age": 100}
)
```

---

**Final Output** (메리츠 A4200_1):
```json
{
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "ins_cd": "N01",
  "coverage_name_raw": "암진단비(유사암제외)",
  "proposal_facts": {
    "coverage_amount_text": "3천만원",
    "coverage_amount": 30000000,
    "premium_text": "30,480",
    "premium": 30480,
    "period_text": "20년 / 100세",
    "period": {"payment_years": 20, "maturity_age": 100}
  },
  "ssot_match_status": "FOUND",
  "match_method": "exact"
}
```

---

### Step-by-Step: 한화 A4200_1

**Phase 1: Load SSOT Targets**

Input: `ins_cd="N02"`

Output:
```python
CoverageTarget(
    coverage_code="A4200_1",
    canonical_name="암진단비(유사암제외)",
    insurer_coverage_name="암(4대유사암제외)진단비",  # ← Differs from N01
    ins_cd="N02"  # ← ONLY identifier (from SSOT)
)
```

---

**Phase 2: Parse PDF Summary Table**

Input: PDF page 3, row 8

PDF table:
```
| 45 | 암(4대유사암제외)진단비 | 3,000만원 | 34,230원 | 100세만기 / 20년납 |
```

Output:
```python
PDFRow(
    coverage_name_raw="암(4대유사암제외)진단비",
    proposal_facts=ProposalFacts(
        coverage_amount_text="3,000만원",
        premium_text="34,230원",
        period_text="100세만기 / 20년납"
    )
)
```

---

**Phase 3: Match PDF Row to SSOT Target**

Input:
- `pdf_row.coverage_name_raw` = "암(4대유사암제외)진단비"
- `ssot_target.insurer_coverage_name` = "암(4대유사암제외)진단비"

Matching:
```python
# Try exact match
if "암(4대유사암제외)진단비" == "암(4대유사암제외)진단비":
    return target  # ✅ MATCH FOUND (exact)
```

Output:
```python
MatchedFact(
    coverage_code="A4200_1",  # ← FROM SSOT (same as 메리츠)
    canonical_name="암진단비(유사암제외)",  # ← FROM SSOT (same as 메리츠)
    coverage_name_raw="암(4대유사암제외)진단비",  # ← FROM PDF (differs from 메리츠)
    proposal_facts=...,
    ssot_match_status="FOUND",
    match_method="exact"
)
```

**Key observation**:
- Same `coverage_code` (A4200_1) across insurers
- Different `coverage_name_raw` (PDF text differs)
- Same `canonical_name` (SSOT standard name)

---

**Phase 4: Clean Proposal Facts**

Input:
```python
proposal_facts=ProposalFacts(
    coverage_amount_text="3,000만원",
    premium_text="34,230원",
    period_text="100세만기 / 20년납"
)
```

Cleaning:
```python
parse_amount("3,000만원") → 30000000
parse_premium("34,230원") → 34230
parse_period("100세만기 / 20년납") → {"payment_years": 20, "maturity_age": 100}
```

Output:
```python
proposal_facts=ProposalFacts(
    coverage_amount_text="3,000만원",
    coverage_amount=30000000,
    premium_text="34,230원",
    premium=34230,
    period_text="100세만기 / 20년납",
    period={"payment_years": 20, "maturity_age": 100}
)
```

---

**Final Output** (한화 A4200_1):
```json
{
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "ins_cd": "N02",
  "coverage_name_raw": "암(4대유사암제외)진단비",
  "proposal_facts": {
    "coverage_amount_text": "3,000만원",
    "coverage_amount": 30000000,
    "premium_text": "34,230원",
    "premium": 34230,
    "period_text": "100세만기 / 20년납",
    "period": {"payment_years": 20, "maturity_age": 100}
  },
  "ssot_match_status": "FOUND",
  "match_method": "exact"
}
```

**Key observation**:
- Same `coverage_code` (A4200_1) across insurers
- Different `coverage_name_raw` (PDF text differs: N01 vs N02)
- Same `canonical_name` (SSOT standard name)
- ✅ ONLY ins_cd used as identifier (no insurer_key)

---

## Part 6: How Step1 V2 Satisfies Q1/Q12/Q13

### Q1: Coverage Comparison (가성비 Top3)

**Q1 Requirements**:
1. `coverage_code` - Coverage identifier ✅
2. `premium_monthly` - Monthly premium (from DB, not Step1)
3. `payout_limit` - Coverage amount ✅ (from Step1 V2 proposal_facts)
4. `product_name` - Product name ✅ (from Step1 V2 product field)

**How Step1 V2 satisfies Q1**:
- ✅ `coverage_code` exists (from SSOT) → Q1 can group by coverage_code
- ✅ `proposal_facts.coverage_amount` → Step3 extracts as `payout_limit` slot → Step4 embeds in compare model → Q1 reads
- ✅ `product` field → Q1 reads for product_name

**Data flow** (Step1 V2 → Q1):
```
Step1 V2
  → coverage_code (A4200_1) + proposal_facts.coverage_amount (30000000)
Step3
  → Extract payout_limit slot from PDF detail pages (using coverage_code metadata)
  → payout_limit.value = 30000000
Step4
  → Aggregate Step3 evidence into compare model
  → compare_tables_v1.jsonl: { coverage_code: "A4200_1", slots: { payout_limit: 30000000 } }
Q1 API
  → Read compare_tables_v1.jsonl
  → Group by coverage_code (A4200_1)
  → Compare payout_limit across insurers
```

**Critical**: Step1 V2 provides coverage_code (from SSOT) → Q1 can group correctly

---

### Q12: Product Recommendation (삼성 vs 메리츠)

**Q12 Requirements**:
1. `coverage_code` - Coverage identifier ✅
2. `premium_monthly` - Monthly premium (from DB, not Step1)
3. `payout_limit` - Coverage amount ✅ (from Step1 V2 proposal_facts)
4. `coverage_exists` - Boolean (implicit if row exists)
5. `product_name` - Product name ✅

**How Step1 V2 satisfies Q12**:
- ✅ `coverage_code` exists → Q12 can filter by coverage_code
- ✅ `proposal_facts.coverage_amount` → Step3 extracts payout_limit → Step4 embeds → Q12 reads
- ✅ Coverage existence → If Step1 V2 output exists for (insurer, coverage_code), coverage exists

**Data flow** (Step1 V2 → Q12):
```
Step1 V2
  → coverage_code (A4200_1) + proposal_facts (amount, premium, period)
Step3
  → Extract payout_limit, waiting_period, etc. (using coverage_code metadata)
Step4
  → Aggregate into compare model
Q12 API
  → Read compare_tables_v1.jsonl
  → Filter by coverage_code (per Q12 rules)
  → Compare premium + payout_limit across insurers
  → Recommend cheaper option
```

**Critical**: Step1 V2 provides coverage_code → Q12 rules can filter by coverage_code (not coverage_name_raw)

---

### Q13: Subtype Coverage Matrix (제자리암/경계성종양)

**Q13 Requirements**:
1. `coverage_code` - Coverage identifier ✅
2. `subtype_coverage_map` - O/X per subtype (from Step3 evidence, not Step1)
3. `product_name` - Product name ✅

**How Step1 V2 satisfies Q13**:
- ✅ `coverage_code` exists (A4200_1) → Q13 can group by coverage_code
- ✅ Step3 extracts `subtype_coverage_map` slot (using coverage_code metadata) → Step4 embeds → Q13 reads
- ✅ `product` field → Q13 reads for product_name

**Data flow** (Step1 V2 → Q13):
```
Step1 V2
  → coverage_code (A4200_1)
Step3
  → Extract subtype_coverage_map slot from PDF detail pages (using coverage_code metadata)
  → subtype_coverage_map = { "제자리암": "O", "경계성종양": "O", ... }
Step4
  → Aggregate into compare model
  → compare_tables_v1.jsonl: { coverage_code: "A4200_1", slots: { subtype_coverage_map: {...} } }
Q13 API
  → Read compare_tables_v1.jsonl
  → Group by coverage_code (A4200_1)
  → Create matrix: rows=insurers, cols=subtypes, cells=O/X
```

**Critical**: Step1 V2 provides coverage_code → Q13 can group correctly (not by coverage_name_raw)

---

### Summary: Q1/Q12/Q13 Satisfaction

| Q | Required from Step1 V2 | Provided? | How? |
|---|----------------------|-----------|------|
| Q1 | coverage_code | ✅ YES | From SSOT (input) |
| Q1 | payout_limit | ✅ YES | From proposal_facts.coverage_amount (→ Step3 → Step4) |
| Q1 | product_name | ✅ YES | From product field |
| Q12 | coverage_code | ✅ YES | From SSOT (input) |
| Q12 | payout_limit | ✅ YES | From proposal_facts.coverage_amount (→ Step3 → Step4) |
| Q12 | coverage_exists | ✅ YES | Implicit (if Step1 V2 output exists) |
| Q13 | coverage_code | ✅ YES | From SSOT (input) |
| Q13 | subtype_coverage_map | ⚠️ INDIRECT | Step3 extracts using coverage_code metadata |
| Q13 | product_name | ✅ YES | From product field |

**All Q1/Q12/Q13 requirements are satisfied by Step1 V2.**

---

## Part 7: Benefits of Step1 V2

### Benefit 1: Constitutional Compliance

**Current Step1**: Violates "Coverage-Code-First" (coverage_code does NOT exist, coverage_name_raw is identifier)

**Step1 V2**: Complies (coverage_code is SSOT input, immutable from start)

**Impact**: ✅ Architectural alignment with constitutional principle

---

### Benefit 2: No Discovery Overhead

**Current Step1**: Extracts ALL PDF rows (~100 coverages) → Most dropped later (unanchored)

**Step1 V2**: Extracts ONLY SSOT-defined coverages (~30 coverages) → 70% reduction

**Impact**: ✅ Faster extraction, smaller output files

---

### Benefit 3: Unanchored Coverages Become Impossible

**Current Step1**: No coverage_code → Step2-b may fail to map → unanchored → dropped

**Step1 V2**: coverage_code from SSOT → ALL coverages anchored (by definition)

**Impact**: ✅ Structural elimination of unanchored risk

---

### Benefit 4: Step2-b Becomes Optional

**Current Step1**: Step2-b REQUIRED (creates coverage_code)

**Step1 V2**: Step2-b OPTIONAL (coverage_code already exists)

**Impact**: ✅ Step2-b can be deleted (constitutional violation eliminated)

---

### Benefit 5: Shadow Contract Elimination

**Current Step1**: Step2-b uses contaminated path (`data/sources/mapping/`)

**Step1 V2**: Uses SSOT path (`data/sources/insurers/`)

**Impact**: ✅ Shadow contract violation resolved

---

## Part 8: Limitations of Step1 V2

### Limitation 1: String Matching Still Required

**Fact**: Step1 V2 STILL uses string matching (exact/normalized) for PDF → SSOT lookup

**Justification**: Unavoidable (no other way to identify which PDF row corresponds to which SSOT target)

**Difference from Step2-b**:
- ❌ Step2-b: String match → CREATE coverage_code (constitutional violation)
- ✅ Step1 V2: String match → LOOKUP coverage_code (from SSOT, already exists)

**Impact**: ⚠️ String matching for lookup (not assignment) is acceptable

---

### Limitation 2: SSOT Completeness Assumption

**Fact**: Step1 V2 assumes SSOT is 100% complete (no missing coverages)

**Risk**: If SSOT lacks a coverage → NOT extracted → invisible

**Mitigation**: Validate SSOT completeness BEFORE migration (compare Step1 V1 vs Step1 V2 coverage counts)

**Impact**: ⚠️ Coverage loss if SSOT incomplete

---

### Limitation 3: PDF Text Variance

**Fact**: If PDF uses different text than SSOT `담보명(가입설계서)` column → match may fail

**Example**:
- SSOT: "암진단비(유사암제외)"
- PDF: "암진단비 (유사암 제외)" (extra spaces)

**Mitigation**: Normalized matching (same as Step2-b: remove whitespace, special chars)

**Impact**: ⚠️ Match rate may be lower than Step2-b (if normalization insufficient)

---

### Limitation 4: No Coverage Discovery

**Fact**: Step1 V2 does NOT discover new coverages (SSOT-only)

**Implication**: If new coverage appears in PDF but NOT in SSOT → NOT extracted

**Mitigation**: Update SSOT before processing new PDF

**Impact**: ⚠️ SSOT must be kept up-to-date

---

## DoD Checklist

- [✅] Step1 V2 input schema documented (SSOT + PDF + Profile)
- [✅] Step1 V2 logic documented (4 phases)
- [✅] Step1 V2 output schema documented
- [✅] Comparison with current Step1 (architectural differences table)
- [✅] A4200_1 extraction example (메리츠, 한화 step-by-step)
- [✅] Q1/Q12/Q13 satisfaction explained (data flow + requirements mapping)
- [✅] Benefits documented (5 benefits)
- [✅] Limitations documented (4 limitations)

---

**END OF STEP1 V2 DESIGN (A4200_1 EXAMPLE)**
