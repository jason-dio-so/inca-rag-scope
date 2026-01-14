# A4200_1 Step1 Target Plan Trace

**Date:** 2026-01-14
**Target coverage_code:** A4200_1
**Target insurers:** Meritz (N01), Hanwha (N02)
**Constitution:** COVERAGE CANONICALIZATION V2 + STEP A4200_1-PIPELINE-SSOT-ENFORCE-V2

---

## 🎯 Purpose

This document traces how Step1 determines **which coverages to extract** and verifies whether it follows the SSOT-first principle.

**Required Behavior:** Step1 MUST load SSOT first, create a target plan, and extract ONLY coverages in the plan.

**Forbidden Behavior:** Step1 MUST NOT discover coverages from PDFs, infer coverages, or process coverages not in SSOT.

---

## ❌ VERDICT: FAIL - Step1 Violates SSOT-First Principle

**Critical Finding:** Step1 currently uses a **"PDF-first discovery"** approach, not an **"SSOT-first targeting"** approach.

**Violation:** Coverage names are **discovered from PDFs**, then **mapped to codes in Step2**. This is the reverse of the required flow.

---

## 🔍 Current Step1 Implementation Analysis

### Step1 Architecture

**Directory:** `pipeline/step1_summary_first/`

**Main Entry Point:** `extractor_v3.py`

**Purpose (from docstring):**
```
STEP NEXT-45-D: Extractor V3 with Fingerprint Gate

Profile-based summary-first extractor + fingerprint gate (45-D)
```

### Current Extraction Flow

```
1. Load PDF
   ↓
2. Load Profile (table signatures, column mappings)
   ↓
3. Extract summary table rows from PDF
   ↓
4. For each row:
   - Extract coverage_name_raw (from PDF cell)
   - Extract proposal_facts (amount, premium, period)
   ↓
5. Output: List[ProposalFact]
   - coverage_name_raw: str  ← FROM PDF
   - proposal_facts: Dict
```

**Key Code Location:** `pipeline/step1_summary_first/extractor_v3.py:240-289`

```python
def _extract_from_summary(self) -> List[ProposalFact]:
    """
    Extract facts from summary tables using profile column map
    """
    facts = []

    # Get table signatures from profile
    primary_sigs = self.profile["summary_table"].get("primary_signatures", [])
    variant_sigs = self.profile["summary_table"].get("variant_signatures", [])

    # Process primary signatures (Pass A)
    facts.extend(self._extract_signatures(primary_sigs, mode="standard_first"))

    # Process variant signatures (Pass B)
    facts.extend(self._extract_signatures(variant_sigs, mode="hybrid_first"))

    return facts
```

### Critical Observation

**Line 54-57** (`extractor_v3.py`):
```python
@dataclass
class ProposalFact:
    """Proposal fact (raw text only, no inference)"""
    coverage_name_raw: str      # ← FROM PDF, NO coverage_code!
    proposal_facts: Dict[str, Any]
```

**Finding:** `ProposalFact` contains `coverage_name_raw` but **NO coverage_code**.

**Implication:** Step1 does NOT know coverage_code during extraction. Coverage_code is determined later in Step2.

---

## ❌ Violation 1: No SSOT Loading in Step1

### Expected Behavior

Step1 should:
```python
# ✅ REQUIRED
def extract(self):
    # 1. Load SSOT FIRST
    ssot = load_ssot('data/sources/insurers/담보명mapping자료.xlsx')

    # 2. Create target plan
    target_plan = create_target_plan(ssot, self.insurer)
    # target_plan = [
    #     {'coverage_code': 'A4200_1', 'allowed_name': '암진단비(유사암제외)'},
    #     {'coverage_code': 'A1300', 'allowed_name': '상해사망'},
    #     ...
    # ]

    # 3. Extract ONLY coverages in plan
    for target in target_plan:
        extract_coverage(pdf, target['coverage_code'], target['allowed_name'])
```

### Actual Behavior

Step1 does:
```python
# ❌ CURRENT (WRONG)
def extract(self):
    # 1. Load PDF profile (NO SSOT)
    profile = load_profile()

    # 2. Extract ALL coverage names from PDF summary
    for row in pdf_summary_table:
        coverage_name = row['coverage_name_column']  # FROM PDF
        facts = extract_facts(row)
        yield ProposalFact(coverage_name_raw=coverage_name, facts=facts)
```

**Evidence of Violation:**

File: `pipeline/step1_summary_first/extractor_v3.py`

Lines checked:
- Line 76-79: `_load_profile()` - loads profile JSON, NO SSOT
- Line 192-267: `extract()` method - NO SSOT loading
- Line 240-267: `_extract_from_summary()` - extracts from PDF, NO SSOT reference

**Grep Search Results:**
```bash
$ grep -r "ssot\|SSOT\|담보명mapping" pipeline/step1_summary_first/*.py
# Found 5 files with mentions, but all in comments/docs, NOT in code execution
```

**Conclusion:** Step1 does NOT load SSOT.

---

## ❌ Violation 2: Coverage Discovery from PDF

### Forbidden Behavior

> "Step1 MUST NOT discover coverages by scanning PDF summary"

### Actual Behavior

**File:** `pipeline/step1_summary_first/extractor_v3.py:554-603`

```python
def _extract_fact_from_row(
    self, row: List, column_map: Dict[str, int], ...
) -> Optional[Dict[str, Any]]:
    """Extract single coverage fact from table row"""

    # Get coverage name from PDF row
    coverage_name_col = column_map.get("coverage_name")
    if coverage_name_col is not None:
        coverage_name_raw = str(row[coverage_name_col]).strip()  # ← FROM PDF

    # ... extract other facts (amount, premium, etc.)

    return {
        "coverage_name_raw": coverage_name_raw,  # ← OUTPUT
        "proposal_facts": {...}
    }
```

**Evidence:**
- Coverage name is extracted from PDF cell
- NO check against SSOT
- NO pre-defined target list
- ALL coverage names in PDF are processed

**Conclusion:** Step1 **discovers** coverages from PDF, violating SSOT-first principle.

---

## ❌ Violation 3: Step2 Determines coverage_code (Not Step1)

### Where coverage_code is Assigned

**File:** `pipeline/step2_canonical_mapping/map_to_canonical.py:1-150`

**Line 12 (CRITICAL):**
```python
"""
Mapping source: data/sources/mapping/담보명mapping자료.xlsx ONLY
"""
```

**🚨 DOUBLE VIOLATION:**
1. coverage_code is determined in **Step2**, not Step1
2. Step2 uses **CONTAMINATED** mapping file (`data/sources/mapping/`)

**Correct SSOT Path:** `data/sources/insurers/담보명mapping자료.xlsx`

**Current (Wrong) Path:** `data/sources/mapping/담보명mapping자료.xlsx`

**Evidence:**

Line 26-30:
```python
def __init__(self, mapping_excel_path: str):
    self.mapping_excel_path = Path(mapping_excel_path)
    self.mapping_dict: Dict[str, Dict] = {}
    self._load_mapping()
```

Line 47-114: `_load_mapping()` method
- Loads Excel file
- Creates lookup dictionary: `coverage_name` → `coverage_code`
- Step2 then matches Step1 coverage names against this dictionary

**Conclusion:** Step2 maps coverage names to codes AFTER extraction, not BEFORE.

---

## 📊 Current Pipeline Flow (INCORRECT)

```
┌─────────────────────────────────────────┐
│  Step1: Extract from PDF               │
│  - Discover coverage names from PDF    │  ← VIOLATION
│  - Extract proposal facts               │
│  - Output: coverage_name_raw (NO CODE) │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Step2: Map to Canonical                │
│  - Load mapping Excel (CONTAMINATED!)   │  ← DOUBLE VIOLATION
│  - Match coverage_name → coverage_code  │
│  - Output: coverage_code + canonical    │
└─────────────────────────────────────────┘
```

**Problems:**
1. ❌ SSOT not loaded in Step1
2. ❌ Coverage names discovered from PDF
3. ❌ coverage_code determined AFTER extraction
4. ❌ Uses contaminated mapping file

---

## ✅ Required Pipeline Flow (CORRECT)

```
┌─────────────────────────────────────────┐
│  Pre-Step1: Load SSOT                   │
│  - Load: data/sources/insurers/         │
│          담보명mapping자료.xlsx          │
│  - Create target plan:                  │
│    [(ins, code, allowed_name), ...]     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Step1: Extract with Target Plan        │
│  - FOR EACH target in plan:             │
│    - Search PDF for allowed_name        │
│    - Extract facts for that coverage    │
│    - Tag with coverage_code from plan   │
│  - Output: (coverage_code, facts)       │
│  - DROP: Any coverage not in plan       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Step2: Validate & Enrich               │
│  - Verify coverage_code is in SSOT      │
│  - Add canonical_name from SSOT         │
│  - NO re-determination of coverage_code │
└─────────────────────────────────────────┘
```

---

## 🔬 A4200_1 Specific Analysis

### Meritz A4200_1 Extraction Path

**SSOT Definition (Row 9):**
- ins_cd: N01
- coverage_code: A4200_1
- canonical_name: 암진단비(유사암제외)
- allowed_display_name: 암진단비(유사암제외)

**Current Step1 Behavior:**
1. Open Meritz PDF (가입설계서)
2. Find summary table
3. For each row:
   - Extract coverage_name_raw = "암진단비(유사암제외)" (from PDF cell)
   - Extract proposal_facts = {amount, premium, period}
4. Output: ProposalFact(coverage_name_raw="암진단비(유사암제외)", ...)

**Current Step2 Behavior:**
1. Load mapping Excel (contaminated)
2. Match "암진단비(유사암제외)" → A4200_1
3. Output: {coverage_code: "A4200_1", ...}

**Problem:** If PDF uses a variant name or has a typo, Step2 matching fails. SSOT is not enforced upfront.

---

### Hanwha A4200_1 Extraction Path

**SSOT Definition (Row 39):**
- ins_cd: N02
- coverage_code: A4200_1
- canonical_name: 암진단비(유사암제외)
- allowed_display_name: 암(4대유사암제외)진단비

**Current Step1 Behavior:**
1. Open Hanwha PDF
2. Extract coverage_name_raw = "암(4대유사암제외)진단비" (from PDF)
3. Output: ProposalFact(coverage_name_raw="암(4대유사암제외)진단비", ...)

**Current Step2 Behavior:**
1. Match "암(4대유사암제외)진단비" → A4200_1
2. Output: {coverage_code: "A4200_1", ...}

**Problem:** Matching relies on string lookup in mapping file, not on pre-defined target plan.

---

## 🚨 Impact on A4200_1

### Why This Matters for A4200_1

1. **Meritz** uses "암진단비(유사암제외)"
2. **Hanwha** uses "암(4대유사암제외)진단비"

These are **different strings** for the **same coverage_code**.

**Current Approach (String Matching):**
- Requires mapping file to have both strings
- If mapping file is incomplete/outdated, extraction fails
- Relies on Step2 heuristics (normalization, fuzzy matching)

**Required Approach (SSOT-First):**
- Step1 knows Meritz A4200_1 is "암진단비(유사암제외)" BEFORE opening PDF
- Step1 knows Hanwha A4200_1 is "암(4대유사암제외)진단비" BEFORE opening PDF
- No string matching needed - direct lookup with pre-defined key

---

## 📋 Evidence Summary

### Files Reviewed

| File | Purpose | SSOT Usage | Verdict |
|------|---------|------------|---------|
| `step1_summary_first/extractor_v3.py` | Main extractor | ❌ NOT LOADED | FAIL |
| `step1_summary_first/__init__.py` | Module init | ❌ NOT LOADED | FAIL |
| `step1_summary_first/hybrid_layout.py` | Layout extraction | ❌ NOT LOADED | FAIL |
| `step2_canonical_mapping/map_to_canonical.py` | Code mapping | ⚠️ CONTAMINATED FILE | FAIL |
| `step2_canonical_mapping/run.py` | Step2 runner | ⚠️ CONTAMINATED FILE | FAIL |

### Key Findings

1. **No SSOT loading in Step1:** Grep search confirms SSOT not referenced in execution code
2. **PDF discovery:** Coverage names extracted from PDF cells directly
3. **Step2 mapping:** coverage_code determined AFTER extraction
4. **Contaminated source:** Step2 uses `data/sources/mapping/` not `data/sources/insurers/`

---

## ✅ Required Changes (NOT IMPLEMENTED)

### Change 1: Create SSOT Loader Module

**File:** `pipeline/step0_ssot_loader/load_ssot.py` (NEW)

```python
def load_ssot(ssot_path: str = 'data/sources/insurers/담보명mapping자료.xlsx'):
    """Load SSOT and return structured target plan"""
    df = pd.read_excel(ssot_path)

    target_plan = []
    for _, row in df.iterrows():
        target_plan.append({
            'ins_cd': row['ins_cd'],
            'insurer_name': row['보험사명'],
            'coverage_code': row['cre_cvr_cd'],
            'canonical_name': row['신정원코드명'],
            'allowed_display_name': row['담보명(가입설계서)']
        })

    return target_plan
```

### Change 2: Modify Step1 to Use Target Plan

**File:** `pipeline/step1_summary_first/extractor_v3.py`

```python
class ExtractorV3:
    def __init__(self, insurer: str, pdf_path: Path, profile_path: Path):
        self.insurer = insurer
        # ... existing init ...

        # NEW: Load SSOT target plan
        self.target_plan = self._load_target_plan()

    def _load_target_plan(self):
        """Load SSOT and filter for this insurer"""
        from pipeline.step0_ssot_loader import load_ssot

        full_plan = load_ssot()
        insurer_plan = [
            t for t in full_plan
            if t['ins_cd'] == self.insurer_code  # Need insurer code mapping
        ]

        return insurer_plan

    def extract(self):
        """Extract ONLY coverages in target plan"""
        facts = []

        for target in self.target_plan:
            # Search PDF for this specific coverage
            coverage_data = self._extract_target_coverage(
                coverage_code=target['coverage_code'],
                allowed_name=target['allowed_display_name']
            )

            if coverage_data:
                facts.append({
                    'coverage_code': target['coverage_code'],  # FROM SSOT
                    'canonical_name': target['canonical_name'],  # FROM SSOT
                    'coverage_name_raw': target['allowed_display_name'],
                    'proposal_facts': coverage_data
                })

        return facts
```

### Change 3: Step2 Validation Only

**File:** `pipeline/step2_canonical_mapping/run.py`

```python
def validate_step2(step1_output):
    """Validate that Step1 output uses SSOT coverage_codes"""
    ssot = load_ssot()
    ssot_codes = set(t['coverage_code'] for t in ssot)

    for record in step1_output:
        if record['coverage_code'] not in ssot_codes:
            raise ValueError(f"Invalid coverage_code: {record['coverage_code']}")

    # Step2 now only validates and enriches, does NOT determine coverage_code
    return step1_output
```

---

## 🔒 Enforcement Rules

### Rule 1: SSOT Must Be First

**Gate:** Pre-Step1

**Check:**
```python
def verify_ssot_loaded():
    if not hasattr(extractor, 'target_plan'):
        raise PipelineViolation("Step1 did not load SSOT target plan")

    if len(extractor.target_plan) == 0:
        raise PipelineViolation("Target plan is empty")
```

### Rule 2: No PDF Discovery

**Gate:** Post-Step1

**Check:**
```python
def verify_no_discovery(step1_output):
    for record in step1_output:
        if 'coverage_code' not in record:
            raise PipelineViolation("Step1 output missing coverage_code")

        if record['coverage_code'] is None:
            raise PipelineViolation("Step1 produced coverage without code")
```

### Rule 3: coverage_code Immutable After Step1

**Gate:** Post-Step2

**Check:**
```python
def verify_code_immutable(step1_output, step2_output):
    step1_codes = {r['coverage_code'] for r in step1_output}
    step2_codes = {r['coverage_code'] for r in step2_output}

    if step1_codes != step2_codes:
        raise PipelineViolation("Step2 modified coverage_codes")
```

---

## 📝 Conclusions

### Verdict: ❌ FAIL

Step1 does NOT follow SSOT-first principle.

### Critical Violations

1. ❌ **No SSOT loading in Step1**
   - SSOT not referenced in `extractor_v3.py`
   - No target plan created
   - Coverage discovery from PDF

2. ❌ **coverage_code determined in Step2**
   - Step1 outputs coverage_name_raw only
   - Step2 maps name → code
   - Reverse of required flow

3. ❌ **Contaminated mapping file**
   - Step2 uses `data/sources/mapping/담보명mapping자료.xlsx`
   - Should use `data/sources/insurers/담보명mapping자료.xlsx`

4. ❌ **String-based matching**
   - Step2 matches coverage names using lookup dictionary
   - Should use coverage_code from SSOT upfront

### Impact on A4200_1

- Current approach works BUT is fragile
- Relies on mapping file completeness
- Violates coverage-code first principle
- Cannot guarantee SSOT enforcement

### Required Remediation

1. Create SSOT loader module
2. Modify Step1 to load SSOT first
3. Create target plan from SSOT
4. Extract ONLY coverages in plan
5. Fix Step2 to use correct SSOT path
6. Change Step2 to validation-only

---

## 🔗 Related Documents

- `A4200_1_SSOT_ROW_SNAPSHOT.md` - SSOT baseline for A4200_1
- `COVERAGE_CANONICALIZATION_V2.md` - Coverage-code first constitution
- `MAPPING_DATA_DECONTAMINATION.md` - Contaminated mapping file policy
- `COVERAGE_MAPPING_PIPELINE_CONTRACT.md` - Required pipeline flow

---

**FINAL VERDICT:** ❌ FAIL - Step1 violates SSOT-first principle through PDF discovery

**Required Action:** Implement SSOT-first target plan in Step1 before any further processing

---

**END OF TRACE**
