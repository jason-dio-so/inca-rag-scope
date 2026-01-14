# Insurer Identifier SSOT: ins_cd Only

**Date**: 2026-01-14
**Task**: STEP PIPELINE-REDESIGN-CONSTITUTION-02 (Identifier Standardization)
**Status**: ✅ COMPLETE (CONSTITUTIONAL DECLARATION)

---

## Constitutional Declaration

**SSOT**: `data/sources/insurers/담보명mapping자료.xlsx`의 `ins_cd` 컬럼

**Principle**: ins_cd is the ONLY insurer identifier across the entire system.

---

## ins_cd Definition (from SSOT)

| ins_cd | 보험사명 | English | Legacy insurer_key |
|--------|---------|---------|-------------------|
| **N01** | 메리츠 | Meritz | ~~meritz~~ |
| **N02** | 한화 | Hanwha | ~~hanwha~~ |
| **N03** | 롯데 | Lotte | ~~lotte~~ |
| **N05** | 흥국 | Heungkuk | ~~heungkuk~~ |
| **N08** | 삼성 | Samsung | ~~samsung~~ |
| **N09** | 현대 | Hyundai | ~~hyundai~~ |
| **N10** | KB | KB | ~~kb~~ |
| **N13** | DB | DB | ~~db_over41, db_under40~~ |

**Source**: SSOT Excel file (8 insurers total)

---

## Constitutional Rules (IMMUTABLE)

### Rule 1: ins_cd is the ONLY identifier

**Principle**: All code MUST use `ins_cd` (N01, N02, ...) as the insurer identifier.

**Violation examples**:
- ❌ Using `insurer_key` ("meritz", "hanwha")
- ❌ Using English names ("samsung", "kb")
- ❌ Using Korean names ("메리츠", "한화")
- ❌ Creating custom insurer codes (M01, H01, etc.)

**Correct usage**:
- ✅ Using `ins_cd` from SSOT (N01, N02, ...)

---

### Rule 2: NO insurer_key field

**Principle**: `insurer_key` field is DEPRECATED. Use `ins_cd` instead.

**Migration**:
- ❌ OLD: `{"insurer_key": "meritz", "ins_cd": "N01"}`
- ✅ NEW: `{"ins_cd": "N01"}`

**Rationale**: Single identifier reduces complexity, eliminates mapping errors.

---

### Rule 3: Display names come from SSOT

**Principle**: If display name needed, load from SSOT `보험사명` column.

**Correct approach**:
```python
# Load SSOT
ssot = pd.read_excel('data/sources/insurers/담보명mapping자료.xlsx')
insurer_map = dict(zip(ssot['ins_cd'], ssot['보험사명']))

# Get display name
display_name = insurer_map["N01"]  # → "메리츠"
```

**Violation**:
```python
# ❌ Hardcoded mapping
insurer_names = {
    "meritz": "메리츠",
    "hanwha": "한화"
}
```

---

### Rule 4: File paths use ins_cd

**Principle**: All file paths MUST use `ins_cd` for insurer identification.

**Correct paths**:
- ✅ `data/scope_v3/N01_step1_targeted_v2.jsonl` (메리츠)
- ✅ `data/scope_v3/N02_step1_targeted_v2.jsonl` (한화)

**Violation**:
- ❌ `data/scope_v3/meritz_step1_targeted_v2.jsonl`
- ❌ `data/scope_v3/hanwha_step1_targeted_v2.jsonl`

---

### Rule 5: API parameters use ins_cd

**Principle**: API endpoints MUST accept `ins_cd` as parameter.

**Correct API**:
```python
@app.get("/q1/coverage_compare")
def q1_coverage_compare(ins_cd: List[str]):  # ← ins_cd, not insurer_key
    # Filter by ins_cd
    data = load_data(ins_cd=ins_cd)
    ...
```

**Violation**:
```python
@app.get("/q1/coverage_compare")
def q1_coverage_compare(insurers: List[str]):  # ← "insurers" is ambiguous
    ...
```

---

## Legacy insurer_key Deprecation

### Current Code Usage (to be removed)

**File**: `pipeline/step1_summary_first/extractor_v3.py`

**Current logic**:
```python
# ❌ Creates insurer_key from directory name
insurer_key = "meritz"  # Derived from directory path
ins_cd = "M01"  # Custom code (NOT SSOT)

# Outputs both
output = {
    "insurer_key": insurer_key,  # ❌ DEPRECATED
    "ins_cd": ins_cd  # ❌ WRONG CODE (should be N01, not M01)
}
```

**Violation**:
1. `insurer_key` is redundant (ins_cd already identifies insurer)
2. `ins_cd` is WRONG (uses M01, but SSOT uses N01)

---

### Step1 V2 Correction

**File**: `pipeline/step1_targeted_v2/extractor.py`

**Correct logic**:
```python
def load_ssot_targets(ins_cd: str) -> List[CoverageTarget]:
    """
    Load SSOT coverage targets for this insurer.

    Args:
        ins_cd: Insurer code from SSOT (N01, N02, ...)

    Returns:
        List of CoverageTarget
    """
    # Read SSOT
    df = pd.read_excel('data/sources/insurers/담보명mapping자료.xlsx')

    # Filter by ins_cd (from SSOT)
    insurer_rows = df[df['ins_cd'] == ins_cd]

    # Convert to targets
    targets = []
    for _, row in insurer_rows.iterrows():
        targets.append(CoverageTarget(
            coverage_code=row['cre_cvr_cd'],
            canonical_name=row['신정원코드명'],
            insurer_coverage_name=row['담보명(가입설계서)'],
            ins_cd=row['ins_cd']  # ✅ FROM SSOT (N01, N02, ...)
        ))

    return targets
```

**Key changes**:
1. ✅ Function parameter: `ins_cd` (not `insurer_key`)
2. ✅ Filter SSOT by `ins_cd` (from SSOT column)
3. ✅ NO insurer_key field in output

---

## Step1 V2 Output Schema (Corrected)

**File**: `data/scope_v3/N01_step1_targeted_v2.jsonl`

**Schema** (corrected):
```json
{
  "ins_cd": "N01",
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "coverage_name_raw": "암진단비(유사암제외)",
  "proposal_facts": {
    "coverage_amount": 30000000,
    "premium": 30480,
    "period": {"payment_years": 20, "maturity_age": 100}
  },
  "product": {
    "product_name_raw": "(무) 알파Plus보장보험2511 ..."
  },
  "ssot_match_status": "FOUND"
}
```

**Removed fields**:
- ❌ `insurer_key` (DEPRECATED)
- ❌ Custom ins_cd codes (M01, H01, etc.)

**Only field**:
- ✅ `ins_cd` from SSOT (N01, N02, ...)

---

## API Response Schema (Corrected)

**Endpoint**: `/q1/coverage_compare?ins_cd=N01&ins_cd=N02`

**Response**:
```json
{
  "metadata": {
    "question": "Q1",
    "insurers": ["N01", "N02"]
  },
  "data": [
    {
      "ins_cd": "N01",
      "insurer_name": "메리츠",
      "coverage_code": "A4200_1",
      "payout_limit": 30000000,
      "premium_monthly": 30480
    },
    {
      "ins_cd": "N02",
      "insurer_name": "한화",
      "coverage_code": "A4200_1",
      "payout_limit": 30000000,
      "premium_monthly": 34230
    }
  ]
}
```

**Key fields**:
- ✅ `ins_cd`: N01, N02 (from SSOT)
- ✅ `insurer_name`: 메리츠, 한화 (from SSOT `보험사명` column)

---

## Migration Checklist

### Phase 1: Code Cleanup

- [ ] Remove `insurer_key` field from all schemas
- [ ] Replace `insurer_key` parameters with `ins_cd`
- [ ] Remove hardcoded insurer_key → ins_cd mappings
- [ ] Update file paths to use ins_cd (N01, N02, ...)

### Phase 2: SSOT Validation

- [ ] Verify all insurers have ins_cd in SSOT
- [ ] Verify no duplicate ins_cd values
- [ ] Verify ins_cd is consistent across all SSOT rows

### Phase 3: Data Migration

- [ ] Rename existing files: `meritz_*.jsonl` → `N01_*.jsonl`
- [ ] Update existing JSONL files: remove `insurer_key`, keep `ins_cd`
- [ ] Regenerate Step1 V2 outputs with ins_cd only

### Phase 4: API Migration

- [ ] Update API parameters: `insurers` → `ins_cd`
- [ ] Update API responses: use `ins_cd`, remove `insurer_key`
- [ ] Update frontend to send ins_cd (not insurer_key)

---

## Benefits of ins_cd Standardization

### Benefit 1: Single Source of Truth

**Current**: ins_cd defined in SSOT, insurer_key defined in code (2 sources)

**New**: ins_cd defined in SSOT only (1 source)

**Impact**: ✅ No mapping errors, no synchronization issues

---

### Benefit 2: Simplified Code

**Current**: Need to maintain insurer_key → ins_cd mapping

```python
# ❌ Hardcoded mapping
insurer_map = {
    'meritz': 'N01',
    'hanwha': 'N02',
    ...
}
```

**New**: No mapping needed

```python
# ✅ Use ins_cd directly
ins_cd = "N01"
```

**Impact**: ✅ Less code, fewer bugs

---

### Benefit 3: SSOT Alignment

**Current**: Code creates custom insurer codes (M01, H01) that differ from SSOT (N01, N02)

**New**: Code uses SSOT ins_cd (N01, N02)

**Impact**: ✅ Constitutional compliance (SSOT is sole authority)

---

### Benefit 4: File Path Consistency

**Current**: File paths use insurer_key ("meritz"), but SSOT uses ins_cd (N01)

**New**: File paths use ins_cd (N01), same as SSOT

**Impact**: ✅ File paths directly map to SSOT rows

---

### Benefit 5: Eliminates Shadow Identifier

**Current**: insurer_key is a shadow identifier (not in SSOT, created by code)

**New**: ins_cd is SSOT identifier (from SSOT, not created)

**Impact**: ✅ No shadow contract violation

---

## ins_cd Usage Examples

### Example 1: Load SSOT Targets

```python
# ✅ Correct
def load_ssot_targets(ins_cd: str) -> List[CoverageTarget]:
    df = pd.read_excel('data/sources/insurers/담보명mapping자료.xlsx')
    rows = df[df['ins_cd'] == ins_cd]  # Filter by ins_cd from SSOT
    ...

# Usage
targets_meritz = load_ssot_targets(ins_cd="N01")
targets_hanwha = load_ssot_targets(ins_cd="N02")
```

---

### Example 2: API Endpoint

```python
# ✅ Correct
@app.get("/q1/coverage_compare")
def q1_coverage_compare(ins_cd: List[str] = Query(...)):
    """
    Compare coverage across insurers.

    Args:
        ins_cd: List of insurer codes (N01, N02, ...)
    """
    data = load_compare_data(ins_cd=ins_cd)
    return {"insurers": ins_cd, "data": data}

# Usage
# GET /q1/coverage_compare?ins_cd=N01&ins_cd=N02
```

---

### Example 3: File Paths

```python
# ✅ Correct
def get_step1_output_path(ins_cd: str) -> str:
    return f"data/scope_v3/{ins_cd}_step1_targeted_v2.jsonl"

# Usage
path_meritz = get_step1_output_path("N01")  # → "data/scope_v3/N01_step1_targeted_v2.jsonl"
path_hanwha = get_step1_output_path("N02")  # → "data/scope_v3/N02_step1_targeted_v2.jsonl"
```

---

### Example 4: Display Names

```python
# ✅ Correct: Load from SSOT
def get_insurer_name(ins_cd: str) -> str:
    df = pd.read_excel('data/sources/insurers/담보명mapping자료.xlsx')
    row = df[df['ins_cd'] == ins_cd].iloc[0]
    return row['보험사명']

# Usage
name = get_insurer_name("N01")  # → "메리츠"
```

---

## Legacy Code to Remove

### Violation 1: insurer_key in extractor_v3.py

**File**: `pipeline/step1_summary_first/extractor_v3.py`

**Code to remove**:
```python
# ❌ Remove this
insurer_key = "meritz"  # Derived from directory
output["insurer_key"] = insurer_key
```

**Replacement**: None (use ins_cd only)

---

### Violation 2: Custom ins_cd codes

**Files**: Various

**Code to remove**:
```python
# ❌ Remove this
insurer_map = {
    "meritz": "M01",  # ← Custom code (NOT SSOT)
    "hanwha": "H01",  # ← Custom code (NOT SSOT)
}
```

**Replacement**: Use SSOT ins_cd (N01, N02, ...)

---

### Violation 3: Hardcoded insurer_key → ins_cd mapping

**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py` (example)

**Code to remove**:
```python
# ❌ Remove this
def map_insurer_key_to_ins_cd(insurer_key: str) -> str:
    mapping = {
        'meritz': 'N01',
        'hanwha': 'N02',
        ...
    }
    return mapping[insurer_key]
```

**Replacement**: None (accept ins_cd as parameter)

---

## DoD Checklist

- [✅] ins_cd declared as ONLY insurer identifier
- [✅] Constitutional rules defined (5 rules)
- [✅] Legacy insurer_key deprecation declared
- [✅] Step1 V2 schema corrected (ins_cd only)
- [✅] API schema corrected (ins_cd only)
- [✅] Migration checklist provided (4 phases)
- [✅] Benefits documented (5 benefits)
- [✅] Usage examples provided (4 examples)
- [✅] Legacy code violations identified (3 violations)

---

**END OF INSURER IDENTIFIER SSOT DECLARATION**
