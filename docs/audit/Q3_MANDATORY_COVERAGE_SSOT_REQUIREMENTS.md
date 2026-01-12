# Q3: Mandatory Coverage SSOT Requirements

**Date**: 2026-01-12
**Task**: STEP NEXT-P2-FIX-α
**Status**: 🔒 **REQUIREMENTS LOCKED** (Implementation NOT Started)
**Type**: New SSOT Definition (Out of Scope for P2-FIX)

---

## Executive Summary

**Q3 Status**: ❌ **BLOCKED** (100% UNKNOWN mandatory_dependency slots)

**Why Not Implemented in P2-FIX**: Q3 requires a **NEW extraction pipeline step** for product-structure analysis, NOT just slot/gate improvements. This is fundamentally different from Q5/Q11 (which have evidence but need better attribution).

**This Document**: Defines **what SSOT is required** to unblock Q3, but does NOT implement it.

---

## 1. Q3 Customer Question

> **"의무담보를 최소화한 상품을 추천해줘. 기본 계약만으로 구성된 저렴한 상품을 찾고 싶어."**

**Customer Intent**:
- Compare products by **mandatory coverage** requirements
- Identify products with minimal "forced" coverages
- Find cheapest "base contract only" options

**Required Data**:
- List of mandatory coverages per product
- List of optional coverages per product
- Premium breakdown (mandatory vs optional)

---

## 2. Current State (2026-01-12)

### 2.1 Data Availability

**Source**: `data/compare_v1/compare_rows_v1.jsonl` (340 rows)

**Slot**: `mandatory_dependency`

**Status**:
```
Total rows: 340
mandatory_dependency.status == "FOUND": 0 (0%)
mandatory_dependency.status == "UNKNOWN": 340 (100%)
```

**Verdict**: **NO SSOT EXISTS** for mandatory coverage classification.

### 2.2 Why mandatory_dependency is Empty

**Root Cause**: Step3 Evidence Resolver does not extract product-structure information.

**What Step3 Currently Extracts**:
- Coverage-level conditions (면책, 감액, 한도, etc.)
- Coverage-level facts from약관 text

**What Step3 Does NOT Extract**:
- Product-level hierarchy (주계약 vs 특약)
- Coverage dependency relationships
- Mandatory vs optional classification

**Missing Capability**: **Product-structure analysis** (not just coverage-level extraction)

---

## 3. Required SSOT Definition

### 3.1 SSOT Table Schema (Proposed)

**Table Name**: `product_coverage_structure`

**Purpose**: Store mandatory/optional classification for each coverage in each product

**Schema** (DDL):
```sql
CREATE TABLE IF NOT EXISTS product_coverage_structure (
    structure_id SERIAL PRIMARY KEY,

    -- Product Identity
    insurer_key TEXT NOT NULL,
    product_id TEXT NOT NULL,
    as_of_date DATE NOT NULL,

    -- Coverage Identity
    coverage_code TEXT NOT NULL,
    coverage_title TEXT NOT NULL,

    -- Coverage Classification (SSOT)
    coverage_type TEXT NOT NULL,  -- MANDATORY | OPTIONAL | CONDITIONAL
    coverage_category TEXT NOT NULL,  -- BASE_CONTRACT | RIDER | ADDON

    -- Dependency Rules
    mandatory_reason TEXT,  -- Why this coverage is mandatory (e.g., "주계약", "기본 담보")
    optional_conditions TEXT,  -- Conditions for optional selection (if any)

    -- Evidence
    evidence_source TEXT NOT NULL,  -- Document section reference
    evidence_excerpt TEXT,  -- Text supporting classification
    extraction_method TEXT NOT NULL,  -- DOCUMENT_STRUCTURE | PROPOSAL_TABLE | MANUAL

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_coverage_type CHECK (coverage_type IN ('MANDATORY', 'OPTIONAL', 'CONDITIONAL')),
    CONSTRAINT chk_coverage_category CHECK (coverage_category IN ('BASE_CONTRACT', 'RIDER', 'ADDON')),
    CONSTRAINT chk_extraction_method CHECK (extraction_method IN ('DOCUMENT_STRUCTURE', 'PROPOSAL_TABLE', 'MANUAL')),
    CONSTRAINT uq_product_coverage UNIQUE (insurer_key, product_id, coverage_code, as_of_date)
);

CREATE INDEX idx_product_coverage_structure_lookup
    ON product_coverage_structure(insurer_key, product_id, coverage_type);

CREATE INDEX idx_product_coverage_structure_code
    ON product_coverage_structure(coverage_code);
```

**Example Row**:
```json
{
  "insurer_key": "samsung",
  "product_id": "CI_NO_REFUND_2025",
  "coverage_code": "A1300",
  "coverage_title": "상해사망",
  "coverage_type": "MANDATORY",
  "coverage_category": "BASE_CONTRACT",
  "mandatory_reason": "보험 약관 상 주계약(기본 담보)으로 분류",
  "evidence_source": "사업방법서 > 담보 구성표",
  "evidence_excerpt": "[주계약] 상해사망 (가입금액: 필수)",
  "extraction_method": "DOCUMENT_STRUCTURE"
}
```

### 3.2 Coverage Type Definitions (LOCKED)

**MANDATORY**:
- Coverage CANNOT be excluded when purchasing product
- Must be included in all proposals
- Premium contribution is required

**OPTIONAL**:
- Coverage CAN be excluded
- Customer can choose to add or remove
- Premium contribution is voluntary

**CONDITIONAL**:
- Mandatory IF certain conditions met
- Example: "A 담보 가입 시 B 담보 필수"
- Requires dependency rule specification

---

## 4. Required Document Sources

### 4.1 Primary Source: 사업방법서 (Business Method Document)

**Document Type**: Insurance company's official product structure document

**Location**: Submitted to금융감독원 (Financial Supervisory Service)

**Key Sections**:
1. **담보 구성표** (Coverage Structure Table)
   - Lists all coverages
   - Marks 주계약/특약 distinction
   - May indicate "필수" (mandatory) or "선택" (optional)

2. **상품 구조도** (Product Structure Diagram)
   - Visual hierarchy of coverages
   - Shows base contract vs riders

3. **가입 규정** (Subscription Rules)
   - States which coverages are mandatory
   - Lists optional rider selection rules

**Availability**: ❓ **NOT CONFIRMED** if we have these documents in current data

### 4.2 Secondary Source: 가입설계서 (Proposal Document)

**Document Type**: Product proposal generated for customer

**Key Sections**:
1. **담보 선택 표** (Coverage Selection Table)
   - Checkboxes indicate optional vs mandatory
   - Some proposals use "[필수]" tag
   - Some proposals separate 주계약 vs 특약 sections

2. **보험료 산출 내역** (Premium Calculation Details)
   - May list "기본 보험료" (base premium) separately
   - Optional riders listed individually

**Availability**: ✅ **CONFIRMED** we have proposal PDFs in `data/sources/`

**Challenge**: Proposal format varies significantly by insurer

### 4.3 Tertiary Source: 약관 (Policy Terms)

**Document Type**: Insurance policy약관 document

**Key Sections**:
1. **특별약관 목차** (Special Terms Table of Contents)
   - Some insurers mark "[주계약]" or "[특약]" in TOC
   - Not standardized across insurers

2. **보험료 납입** (Premium Payment) Section
   - May state which coverages are included in base premium

**Availability**: ✅ **CONFIRMED** we have약관 PDFs

**Challenge**: Most약관 do NOT explicitly state mandatory/optional

---

## 5. Extraction Strategy (Proposed)

### 5.1 Three-Tier Extraction Approach

#### Tier 1: Document Structure Analysis (Automated)

**Method**: Parse document structure to identify coverage hierarchy

**Target Indicators**:
```python
MANDATORY_INDICATORS = [
    "[주계약]",
    "[기본계약]",
    "필수",
    "기본 담보",
    "주 담보",
]

OPTIONAL_INDICATORS = [
    "[특약]",
    "[선택약관]",
    "선택",
    "추가 담보",
]
```

**Algorithm**:
```python
def classify_coverage_from_structure(coverage_title, document_section):
    """
    Classify coverage as MANDATORY/OPTIONAL based on document structure.

    Returns:
        ("MANDATORY" | "OPTIONAL" | "UNKNOWN", evidence_excerpt)
    """

    # Check for explicit tags
    if any(tag in coverage_title for tag in MANDATORY_INDICATORS):
        return "MANDATORY", coverage_title

    if any(tag in document_section for tag in OPTIONAL_INDICATORS):
        return "OPTIONAL", document_section[:100]

    # Check section header
    if "주계약" in document_section_header:
        return "MANDATORY", document_section_header

    if "특약" in document_section_header:
        return "OPTIONAL", document_section_header

    return "UNKNOWN", None
```

**Expected Success Rate**: 40-60% (depends on document quality)

#### Tier 2: Proposal Table Parsing (Semi-Automated)

**Method**: Extract "담보 선택 표" from proposal PDFs

**Target Table Columns**:
- Coverage name
- Selection checkbox (checked = selected, unchecked = optional)
- "[필수]" tag or similar marker

**Algorithm**:
```python
def extract_mandatory_from_proposal_table(proposal_pdf):
    """
    Parse proposal coverage selection table.

    Returns:
        List of (coverage_name, is_mandatory, evidence)
    """

    tables = extract_tables_from_pdf(proposal_pdf)

    for table in tables:
        if "담보" in table.header and ("선택" in table.header or "가입" in table.header):
            for row in table.rows:
                coverage_name = row['coverage_name']
                has_checkbox = row['has_checkbox']
                has_mandatory_tag = "[필수]" in coverage_name or "필수" in row['notes']

                if has_mandatory_tag:
                    yield (coverage_name, True, row_text)
                elif not has_checkbox:
                    # No checkbox = mandatory (cannot deselect)
                    yield (coverage_name, True, "No checkbox in proposal table")
                else:
                    yield (coverage_name, False, "Checkbox present (optional)")
```

**Expected Success Rate**: 50-70% (depends on proposal table standardization)

#### Tier 3: Manual Classification (Last Resort)

**Method**: Manually review documents when automated extraction fails

**Process**:
1. Identify products with 0% MANDATORY coverage extracted
2. Manually review사업방법서 or proposal
3. Record classification in CSV/JSON
4. Load into SSOT table with `extraction_method = 'MANUAL'`

**Expected Need**: 20-40% of products

---

## 6. Implementation Roadmap (NOT for P2-FIX)

### Phase 1: Document Acquisition & Assessment (2-3 days)

**Tasks**:
1. Inventory existing documents
   - ✅ Proposals: Check `data/sources/proposals/`
   - ❓사업방법서: Check if available
   - ✅ 약관: Check `data/sources/contracts/`

2. Assess document quality
   - Count insurers with clear mandatory indicators
   - Identify standardized vs non-standardized formats

3. Select primary document source
   - If사업방법서 available → Tier 1 (structure analysis)
   - If only proposals available → Tier 2 (table parsing)
   - If neither standardized → Tier 3 (manual)

**Deliverable**: Document assessment report with extraction strategy decision

### Phase 2: Extraction Pipeline Development (3-5 days)

**Tasks**:
1. Create new pipeline step: `step2c_product_structure/`
   - Input: Documents from `data/sources/`
   - Output: `product_coverage_structure` table (DB or JSONL)

2. Implement chosen extraction tier
   - Tier 1: Structure parser + regex patterns
   - Tier 2: PDF table extractor + column parser
   - Tier 3: Manual classification template

3. Run extraction for all 8 insurers

**Deliverable**: `product_coverage_structure` table with ≥60% coverage

### Phase 3: Validation & Gap Filling (2-3 days)

**Tasks**:
1. Validate extraction quality
   - Manual spot-check 20% of rows
   - Cross-reference with known product structures

2. Fill gaps with Tier 3 (manual)
   - Target: 100% coverage for at least 5/8 insurers

3. Create evidence documentation

**Deliverable**: Complete `product_coverage_structure` SSOT

### Phase 4: Q3 Implementation (2-3 days)

**Tasks**:
1. Join `product_coverage_structure` with `coverage_premium_quote`
2. Calculate mandatory premium sum per product/segment
3. Rank products by mandatory premium (lowest = best)
4. Create Q3 UI spec and evidence document

**Deliverable**: Q3 fully implemented (unblocked)

**Total Estimated Effort**: 9-14 days

---

## 7. Success Criteria (DoD)

### For SSOT Creation:

**Minimum Viable**:
- ✅ `product_coverage_structure` table populated
- ✅ ≥5/8 insurers have 100% coverage classification
- ✅ ≥3/8 insurers have evidence for all mandatory coverages

**Ideal**:
- ✅ 8/8 insurers have 100% coverage classification
- ✅ All MANDATORY classifications have evidence excerpt
- ✅ ≥80% extracted via Tier 1 or Tier 2 (automated)

### For Q3 Implementation:

**Pass Conditions**:
- ✅ Can rank products by mandatory premium for ≥5/8 insurers
- ✅ All UNKNOWN cases have documented reason
- ✅ Evidence for each mandatory coverage list

---

## 8. Risks & Mitigation

### Risk 1: Documents Not Available

**Risk**: 사업방법서 not in current data

**Mitigation**:
- Use proposal PDFs (Tier 2)
- If needed, manually classify from약관 (Tier 3)
- Accept 60-80% coverage rate instead of 100%

### Risk 2: Non-Standardized Formats

**Risk**: Each insurer uses different proposal format

**Mitigation**:
- Build insurer-specific parsers (8 variants)
- Use Tier 3 (manual) for difficult cases
- Accept longer timeline (14 days instead of 9)

### Risk 3: Ambiguous Classifications

**Risk**: Some coverages may be "conditionally mandatory"

**Mitigation**:
- Use CONDITIONAL coverage_type
- Document dependency rules in `optional_conditions` field
- For Q3 ranking, treat CONDITIONAL as OPTIONAL

---

## 9. Why This is NOT in P2-FIX Scope

**P2-FIX Scope**: Improve slot extraction quality for Q5/Q11
- Fix: G5 Gate attribution rules
- Fix: Slot schema redesign
- Target: Evidence that EXISTS but needs better attribution

**Q3 Requirement**: Create NEW SSOT from scratch
- Need: Parse product-structure documents
- Need: Build new extraction pipeline step
- Target: Data that DOESN'T EXIST in current pipeline

**Decision**: Q3 remains BLOCKED until product-structure pipeline created

---

## 10. Next Actions

**Immediate** (this commit):
- ✅ Document Q3 requirements (this file)
- ✅ Keep Q3 as BLOCKED in STATUS.md
- ✅ Update customer explanation with Q3 blocker reason

**Future Sprint** (separate from P2-FIX):
- Phase 1: Document assessment (2-3 days)
- Phase 2: Extraction pipeline (3-5 days)
- Phase 3: Validation (2-3 days)
- Phase 4: Q3 implementation (2-3 days)

**Total**: 9-14 days (separate project)

---

## 11. Copy-Paste Execution Commands (For Future Implementation)

### Step 1: Document Inventory

```bash
# Check proposal availability
ls -lh data/sources/proposals/ | grep -i ".pdf"

# Check사업방법서 availability
find data/sources/ -iname "*사업방법서*" -o -iname "*business_method*"

# Check약관 availability
ls -lh data/sources/contracts/ | grep -i ".pdf"
```

### Step 2: Create Pipeline Step

```bash
# Create new pipeline directory
mkdir -p pipeline/step2c_product_structure

# Create main script
touch pipeline/step2c_product_structure/run.py
touch pipeline/step2c_product_structure/structure_extractor.py

# Add to run_pipeline.py
# (manual code modification needed)
```

### Step 3: Run Extraction

```bash
# Standard pipeline execution
python3 tools/run_pipeline.py --stage step2c

# Verify output
cat data/product_structure/product_coverage_structure.jsonl | wc -l
cat data/product_structure/product_coverage_structure.jsonl | jq -r '.coverage_type' | sort | uniq -c
```

### Step 4: Validate Results

```bash
# Check mandatory coverage rate by insurer
cat data/product_structure/product_coverage_structure.jsonl | \
  jq -r '"\(.insurer_key),\(.coverage_type)"' | \
  sort | uniq -c

# Expected output (target):
#   15 samsung,MANDATORY
#   25 samsung,OPTIONAL
#   12 meritz,MANDATORY
#   ...
```

---

**Document Version**: 1.0
**Status**: 🔒 **REQUIREMENTS LOCKED** (Implementation Pending)
**Last Updated**: 2026-01-12
**Estimated Implementation Effort**: 9-14 days
