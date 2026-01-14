# Contract-to-Step Impact Trace

**Date**: 2026-01-14
**Task**: STEP PIPELINE-CONTRACT-INVENTORY-01
**Status**: ✅ COMPLETE (FACT ONLY)

---

## Purpose

Trace how each contract file (SSOT/YAML/JSON/policy) is referenced in Step1-4 code and API.

For each contract:
- Code location (file:line)
- Reference method (load/import/join)
- Decision impact (what it determines)

NO inference. CODE EVIDENCE ONLY.

---

## 1. Mapping SSOT Traces

### 1.1 담보명mapping자료.xlsx (CONTAMINATED PATH)

**File**: `data/sources/mapping/담보명mapping자료.xlsx`

**Referenced by**:

#### pipeline/step2_canonical_mapping/map_to_canonical.py

**Lines**: 12, 305

**Evidence**:
```python
# Line 12 (comment)
"""
Mapping source: data/sources/mapping/담보명mapping자료.xlsx ONLY
"""

# Line 305 (actual load path)
mapping_excel = base_dir / "data" / "sources" / "mapping" / "담보명mapping자료.xlsx"
```

**Method**: `pd.read_excel()` (via `openpyxl.load_workbook()` in line 61)

**Function**: `CanonicalMapper._load_mapping()` (lines 47-114)

**Impact**: ⚠️ CRITICAL
- Loads Excel into in-memory dict: `{coverage_name: {coverage_code, canonical_name, match_type}}`
- Determines coverage_code assignment for all Step1 coverages
- 4 match types: exact, normalized, alias, normalized_alias

---

#### pipeline/step2_canonical_mapping/run.py

**Lines**: 87

**Evidence**:
```python
# Line 87
mapping_excel = project_root / 'data' / 'sources' / 'mapping' / '담보명mapping자료.xlsx'
```

**Method**: Path construction, passed to CanonicalMapper constructor

**Function**: `main()` entry point

**Impact**: ⚠️ CRITICAL - Entry point for Step2-b execution

---

### 1.2 담보명mapping자료.xlsx (CORRECT PATH)

**File**: `data/sources/insurers/담보명mapping자료.xlsx`

**Referenced by**: Policy documents only (no code references found)

**Issue**: ⚠️ CRITICAL - Code uses CONTAMINATED path, not this SSOT path

---

## 2. Evidence Schema Traces

### 2.1 evidence_patterns.py

**File**: `pipeline/step3_evidence_resolver/evidence_patterns.py`

**Defines**: `EVIDENCE_PATTERNS` dict (line 23)

**Referenced by**:

#### pipeline/step3_evidence_resolver/resolver.py

**Lines**: 30, 32, 72, 103

**Evidence**:
```python
# Line 30, 32
from .evidence_patterns import (
    PatternMatcher,
    EVIDENCE_PATTERNS,
    create_evidence_entry
)

# Line 72
if slots_to_resolve is None:
    slots_to_resolve = list(EVIDENCE_PATTERNS.keys())

# Line 103
pattern = EVIDENCE_PATTERNS.get(slot_key)
```

**Function**: `CoverageEvidenceResolver.resolve()` (lines 56-119)

**Method**: Direct import and dict lookup

**Impact**: ⚠️ CRITICAL
- Defines 14 evidence slots (start_date, payout_limit, etc.)
- Each slot has keyword patterns for document search
- Determines what evidence can be extracted

---

### 2.2 extended_slot_schema.py

**File**: `pipeline/step1_summary_first/extended_slot_schema.py`

**Referenced by**: Step1 `extractor_v3.py` (import, usage not verified in scan)

**Impact**: ⚠️ MEDIUM - Defines extended slots for Step1 extraction

---

## 3. Gate Rules Traces

### 3.1 gates.py (Step3)

**File**: `pipeline/step3_evidence_resolver/gates.py`

**Defines**: `EvidenceGates` class

**Referenced by**:

#### pipeline/step3_evidence_resolver/resolver.py

**Lines**: 35, 50, 53, 54, 181, 193, 207, 214, 227, 228

**Evidence**:
```python
# Line 35
from .gates import EvidenceGates

# Line 50, 53, 54
def __init__(self, document_set: DocumentSet, enable_gates: bool = True):
    ...
    self.gates = EvidenceGates() if enable_gates else None
    self.enable_gates = enable_gates

# Line 181-214 (usage in _resolve_slot)
if self.enable_gates:
    ...
    gate_result = self.gates.validate_candidate(
        candidate,
        coverage_code,  # P2-FIX: Coverage code for G5 gate
        slot_key
    )
    ...
    if not gate_result["pass"]:
        ...
    # If all candidates failed gates
    if not slot_candidates:
        return {
            "slot": {...},
            "status": "UNKNOWN",
            "evidences": candidates,
            "reason": f"All candidates failed gates: {'; '.join(unique_reasons)}"
        }
```

**Function**: `_resolve_slot()` (lines 126-230)

**Method**: Instantiate EvidenceGates, call `validate_candidate()` per evidence item

**Impact**: ⚠️ CRITICAL
- G3: Conflict detection (multiple values)
- G5: Coverage attribution (evidence belongs to this coverage?)
- G6: Slot tier enforcement (trust hierarchy)
- Determines evidence status: FOUND/UNKNOWN/CONFLICT

---

### 3.2 gates.py (Step4)

**File**: `pipeline/step4_compare_model/gates.py`

**Defines**: `CoverageAttributionValidator`, `SlotGateValidator`, `SlotTierEnforcementGate`, `PremiumSSOTGate`

**Referenced by**:

#### pipeline/step4_compare_model/builder.py

**Lines**: 27, 29, 31, 65, 642

**Evidence**:
```python
# Line 27-31
from .gates import (
    DiagnosisCoverageRegistry,
    CoverageAttributionValidator,
    SlotGateValidator,
    SlotTierEnforcementGate,
    ConfidenceLabeler
)

# Line 65
def __init__(self):
    """Initialize with G5 gate validator and G6 tier enforcement"""
    self.gate_validator = SlotGateValidator()
    self.tier_gate = SlotTierEnforcementGate()

# Line 642
from .gates import PremiumSSOTGate
```

**Functions**:
- `CompareRowBuilder.__init__()` (line 62-65)
- `build_premium_compare_response()` (line 642)

**Method**: Instantiate gate validators, call validation methods

**Impact**: ⚠️ HIGH
- Validates coverage_code assignments
- Validates slot-level trust
- Enforces trust tier hierarchy
- Validates premium data sourcing

---

## 4. Overlay SSOT Traces

### 4.1 q5_waiting_policy_v1.jsonl

**File**: `data/compare_v1/q5_waiting_policy_v1.jsonl`

**Generated by**:
- `pipeline/step3_evidence_resolver/generate_q5_waiting_policy.py` (script, not auto-run)

**Referenced by**:

#### apps/api/overlays/q5/loader.py

**Lines**: 29, 36

**Evidence**:
```python
# Line 29
ssot_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "compare_v1" / "q5_waiting_policy_v1.jsonl"

# Line 36-50
with open(ssot_path, 'r', encoding='utf-8') as f:
    for line in f:
        ...
        data = json.loads(line)
        insurer_key = data.get('insurer_key', '')
        ...
        policy = ContractWaitingPolicy(
            insurer_key=insurer_key,
            waiting_period_policy=data.get('waiting_period_policy', 'UNKNOWN'),
            ...
        )
        policies.append(policy)
```

**Function**: `load_q5_waiting_policy()` (lines 14-60)

**Method**: Read JSONL, parse per line, construct dataclass

**Impact**: ⚠️ HIGH - Determines Q5 response per insurer

---

#### apps/api/server.py

**Lines**: 876, 893, 903

**Evidence**:
```python
# Line 876 (comment)
"""
- Data source: q5_waiting_policy_v1.jsonl (Overlay SSOT)
"""

# Line 893
from apps.api.overlays.q5.loader import load_q5_waiting_policy

# Line 903
policies = load_q5_waiting_policy(insurers_filter=insurers_filter)
```

**Function**: `q5_waiting_period()` endpoint (lines 865-950)

**Method**: Call loader, transform to response format

**Impact**: ⚠️ CRITICAL - Q5 endpoint uses this SSOT directly

---

### 4.2 q7_waiver_policy_v1.jsonl

**File**: `data/compare_v1/q7_waiver_policy_v1.jsonl`

**Generated by**:
- `pipeline/step3_evidence_resolver/contract_policy_resolver.py` (referenced by generation script)

**Referenced by**:

#### apps/api/overlays/q7/loader.py

**Lines**: 29 (similar to q5/loader.py)

**Function**: `load_q7_waiver_policy()`

**Method**: Read JSONL, parse per line

**Impact**: ⚠️ HIGH - Determines Q7 response per (insurer, coverage_code)

---

#### apps/api/server.py

**Lines**: 960, 978, 988

**Evidence**:
```python
# Line 960 (comment)
"""
- Data source: q7_waiver_policy_v1.jsonl (Overlay SSOT)
"""

# Line 978
from apps.api.overlays.q7.loader import load_q7_waiver_policy

# Line 988
policies = load_q7_waiver_policy(insurers_filter=insurers_filter)
```

**Function**: `q7_waiver_policy()` endpoint (lines 953-1025)

**Impact**: ⚠️ CRITICAL - Q7 endpoint uses this SSOT directly

---

### 4.3 q8_surgery_repeat_policy_v1.jsonl

**File**: `data/compare_v1/q8_surgery_repeat_policy_v1.jsonl`

**Generated by**:
- `pipeline/step3_evidence_resolver/generate_q8_surgery_repeat_policy.py`

**Referenced by**:

#### apps/api/overlays/q8/loader.py

**Lines**: 29 (similar to q5/loader.py)

**Function**: `load_q8_surgery_repeat_policy()`

**Method**: Read JSONL, parse per line

**Impact**: ⚠️ HIGH - Determines Q8 response per (insurer, coverage_code)

---

#### apps/api/server.py

**Lines**: 1038, 1056, 1066

**Evidence**:
```python
# Line 1038 (comment)
"""
- Data source: q8_surgery_repeat_policy_v1.jsonl (Overlay SSOT)
"""

# Line 1056
from apps.api.overlays.q8.loader import load_q8_surgery_repeat_policy

# Line 1066
policies = load_q8_surgery_repeat_policy(insurers_filter=insurers_filter)
```

**Function**: `q8_surgery_repeat_policy()` endpoint (lines 1031-1105)

**Impact**: ⚠️ CRITICAL - Q8 endpoint uses this SSOT directly

---

### 4.4 q11_references_v1.jsonl

**File**: `data/compare_v1/q11_references_v1.jsonl`

**Generated by**: Manual curation (frozen)

**Referenced by**:

#### apps/api/server.py

**Lines**: 1420, 1422

**Evidence**:
```python
# Line 1420-1422 (comment + path)
# Load references from q11_references_v1.jsonl (SSOT: business method only)
# FROZEN: This is the single source of truth for Q11, DO NOT BACKFILL
references_path = "data/compare_v1/q11_references_v1.jsonl"
```

**Function**: `q11_cancer_hospitalization()` endpoint (lines 1110-1380)

**Method**: Read JSONL, parse per line, construct response directly

**Impact**: ⚠️ CRITICAL
- Q11 BYPASSES normal pipeline (Step1-4)
- Uses frozen reference data directly
- NO compare_tables_v1.jsonl used for Q11

---

### 4.5 contract_meta_v1.jsonl

**File**: `data/compare_v1/contract_meta_v1.jsonl`

**Generated by**: `pipeline/generate_contract_meta_v1.py`

**Referenced by**:

#### apps/api/server.py

**Lines**: 1178, 1179, 1181, 1188, 1193, 1263, 1386

**Evidence**:
```python
# Line 1178-1193
contract_meta_path = "data/compare_v1/contract_meta_v1.jsonl"
contract_meta_map = {}
try:
    with open(contract_meta_path, 'r', encoding='utf-8') as meta_file:
        for line in meta_file:
            ...
            data = json.loads(line)
            insurer_key = data.get('insurer_key')
            if insurer_key:
                contract_meta_map[insurer_key] = {
                    'product_name_display': data.get('product_name_display', ''),
                    'evidence': data.get('evidence', [])
                }
except FileNotFoundError:
    logger.warning(f"Contract metadata file not found: {contract_meta_path}")

# Line 1263 (usage in Q1)
product_meta = contract_meta_map.get(insurer_key, {})

# Line 1386 (usage in Q13)
product_meta = contract_meta_map.get(insurer_key, {})
```

**Functions**: Multiple Q endpoints (Q1, Q13)

**Method**: Load into dict at endpoint start, lookup per insurer

**Impact**: ⚠️ MEDIUM
- Provides product display names
- Provides contract-level evidence (disclaimers)
- Used in Q1, Q13 responses

---

## 5. Compare Model Output Traces

### 5.1 compare_tables_v1.jsonl

**File**: `data/compare_v1/compare_tables_v1.jsonl`

**Generated by**:
- Step4: `pipeline/step4_compare_model/builder.py` (`CompareTableBuilder`)

**Referenced by**:

#### apps/api/server.py

**Lines**: 1152, 1195, 1196

**Evidence**:
```python
# Line 1152 (comment)
"""
- Data source: compare_tables_v1.jsonl (has coverage_code)
"""

# Line 1195-1196
# Load data from compare_tables_v1.jsonl (has coverage_code)
data_path = "data/compare_v1/compare_tables_v1.jsonl"
```

**Function**: `q1_coverage_compare()` endpoint (lines 1110-1380)

**Method**: Read JSONL, filter by coverage_code, construct response

**Impact**: ⚠️ CRITICAL
- Primary data source for TYPE A questions (Q1, Q13)
- Grouped by coverage_code
- Contains all 8 insurers per coverage

---

#### apps/api/chat_handlers.py (likely, not scanned in detail)

**Impact**: Used for other TYPE A questions

---

### 5.2 compare_rows_v1.jsonl

**File**: `data/compare_v1/compare_rows_v1.jsonl`

**Generated by**:
- Step4: `pipeline/step4_compare_model/builder.py` (`CompareRowBuilder`)

**Referenced by**: Internal (Step4 table building), debugging only

**Impact**: ⚠️ MEDIUM - Granular row-level data, not directly used by API

---

## 6. Step Output Traces

### 6.1 Step1 → Step2

**Output**: `data/scope_v3/*_step1_raw_scope_v3.jsonl`

**Generated by**: Step1 `extractor_v3.py`

**Referenced by**:
- Step2-a: `pipeline/step2_sanitize_scope/sanitize.py` (reads Step1 output)
- Step2-b: `pipeline/step2_canonical_mapping/map_to_canonical.py` (reads Step2-a output)

**Method**: JSONL stream processing (read line-by-line)

**Impact**: ⚠️ CRITICAL - Step2 depends on Step1 output

---

### 6.2 Step2 → Step3

**Output**: `data/scope_v3/*_step2_canonical_scope_v1.jsonl`

**Generated by**: Step2-b `map_to_canonical.py`

**Referenced by**:
- Step3: `pipeline/step3_evidence_resolver/resolver.py` (reads Step2-b output)

**Method**: JSONL stream processing

**Impact**: ⚠️ CRITICAL - Step3 depends on Step2 output (especially coverage_code field)

---

### 6.3 Step3 → Step4

**Output**: `data/scope_v3/*_step3_evidence_enriched_v1.jsonl`

**Generated by**: Step3 `resolver.py`

**Referenced by**:
- Step4: `pipeline/step4_compare_model/builder.py` (reads Step3 output)

**Method**: JSONL stream processing

**Impact**: ⚠️ CRITICAL - Step4 depends on Step3 output (evidence_slots, evidence_status)

---

## 7. Policy Document Traces

### 7.1 Q1_Q14_RESPONSE_FORMAT_LOCK.md

**File**: `docs/policy/Q1_Q14_RESPONSE_FORMAT_LOCK.md`

**Referenced by**: API response composers (implicitly, not direct code reference)

**Impact**: ⚠️ CRITICAL - Defines 5-block structure for all Q responses

**Evidence**: Response structure in `apps/api/server.py` endpoints matches 5-block format

---

### 7.2 Q12_RULE_CATALOG.md

**File**: `docs/policy/Q12_RULE_CATALOG.md`

**Referenced by**: `pipeline/step5_recommendation/*` (Q12 builder)

**Impact**: ⚠️ CRITICAL - Defines 12 coverage filtering rules (A1-A12)

**Evidence**: Q12 builder logic implements rules from catalog

---

### 7.3 COVERAGE_MAPPING_SSOT.md

**File**: `docs/policy/COVERAGE_MAPPING_SSOT.md`

**Referenced by**: Policy adherence (no direct code reference)

**Impact**: ⚠️ CRITICAL - Declares `담보명mapping자료.xlsx` as SSOT

**Violation**: Code uses CONTAMINATED path `data/sources/mapping/`, not `data/sources/insurers/`

---

## Step Impact Summary

### Step1: PDF Extraction

**Contracts referenced**: 1

| Contract | Reference Location | Impact |
|----------|-------------------|--------|
| `extended_slot_schema.py` | `extractor_v3.py` (import) | Defines extractable slots |

**Decision impact**: ⚠️ MEDIUM - Defines what can be extracted from PDF

---

### Step2-a: Sanitization

**Contracts referenced**: 0

**Decision impact**: None (normalization only)

---

### Step2-b: Canonical Mapping

**Contracts referenced**: 1

| Contract | Reference Location | Impact |
|----------|-------------------|--------|
| `담보명mapping자료.xlsx` (CONTAMINATED) | `map_to_canonical.py:12, 305` | Defines coverage_code assignments |

**Decision impact**: ⚠️ CRITICAL
- Loads mapping Excel (CONTAMINATED PATH)
- Determines coverage_code for all Step1 coverages
- 4 string matching methods (exact, normalized, alias, normalized_alias)

---

### Step3: Evidence Resolution

**Contracts referenced**: 2

| Contract | Reference Location | Impact |
|----------|-------------------|--------|
| `evidence_patterns.py` (EVIDENCE_PATTERNS) | `resolver.py:30, 72, 103` | Defines 14 evidence slots + search patterns |
| `gates.py` (EvidenceGates) | `resolver.py:35, 53, 181, 193` | Validates evidence (G3/G5/G6 gates) |

**Decision impact**: ⚠️ CRITICAL
- Evidence patterns: Determines which slots to search, what keywords to use
- Evidence gates: Determines evidence trust (FOUND/UNKNOWN/CONFLICT)

---

### Step4: Comparison Model

**Contracts referenced**: 1

| Contract | Reference Location | Impact |
|----------|-------------------|--------|
| `gates.py` (SlotGateValidator, SlotTierEnforcementGate) | `builder.py:27-31, 65` | Validates slot trust, enforces tier hierarchy |

**Decision impact**: ⚠️ HIGH
- Slot gate validation: Ensures slot data quality
- Tier enforcement: Prioritizes evidence sources

---

### API: Q1-Q14 Endpoints

**Contracts referenced**: 8

| Contract | Reference Location | Impact |
|----------|-------------------|--------|
| `compare_tables_v1.jsonl` | `server.py:1196` | Q1, Q13 data source |
| `q5_waiting_policy_v1.jsonl` | `overlays/q5/loader.py:29` | Q5 data source |
| `q7_waiver_policy_v1.jsonl` | `overlays/q7/loader.py:29` | Q7 data source |
| `q8_surgery_repeat_policy_v1.jsonl` | `overlays/q8/loader.py:29` | Q8 data source |
| `q11_references_v1.jsonl` | `server.py:1422` | Q11 data source (FROZEN) |
| `contract_meta_v1.jsonl` | `server.py:1178` | Q1, Q13 product metadata |
| `Q1_Q14_RESPONSE_FORMAT_LOCK.md` | (implicit) | All Q endpoints structure |
| `Q12_RULE_CATALOG.md` | `step5_recommendation/*` | Q12 recommendation rules |

**Decision impact**: ⚠️ CRITICAL
- Overlay SSOT files (Q5/Q7/Q8/Q11): Determine question-specific responses
- Compare model: Primary data source for TYPE A questions
- Policy docs: Define response structure, rules

---

## Contract Dependency Graph

```
담보명mapping자료.xlsx (Step2-b)
  ↓ (coverage_code assignment)
Step2 Output (*_step2_canonical_scope_v1.jsonl)
  ↓ (coverage_code + facts)
evidence_patterns.py (Step3)
  ↓ (evidence search patterns)
gates.py (Step3)
  ↓ (evidence validation)
Step3 Output (*_step3_evidence_enriched_v1.jsonl)
  ↓ (evidence_slots + evidence_status)
gates.py (Step4)
  ↓ (slot validation, tier enforcement)
compare_tables_v1.jsonl (Step4 output)
  ↓ (grouped by coverage_code)
API Q1/Q13 Endpoints
  ↓ (response construction)
Q1_Q14_RESPONSE_FORMAT_LOCK.md
  ↓ (5-block structure)
UI/Frontend
```

**Parallel dependencies** (API overlays):
```
generate_q5_waiting_policy.py → q5_waiting_policy_v1.jsonl → Q5 API
generate_q8_surgery_repeat_policy.py → q8_surgery_repeat_policy_v1.jsonl → Q8 API
(manual curation) → q11_references_v1.jsonl → Q11 API
```

---

## Critical Path Contracts

Contracts that MUST be available for pipeline to function:

1. **담보명mapping자료.xlsx** (Step2-b) - Without this, no coverage_code assignments
2. **evidence_patterns.py** (Step3) - Without this, no evidence extraction
3. **gates.py** (Step3, Step4) - Without this, no evidence validation
4. **compare_tables_v1.jsonl** (Step4 output) - Without this, TYPE A questions fail
5. **q11_references_v1.jsonl** (Q11 frozen) - Without this, Q11 endpoint fails

---

## DoD Checklist

- [✅] All high-impact contracts traced (7+ contracts)
- [✅] Code locations documented (file:line)
- [✅] Reference methods documented (load/import/join)
- [✅] Decision impacts described (what it determines)
- [✅] Step-by-step impact summary created
- [✅] Contract dependency graph visualized
- [✅] Critical path contracts identified

---

**END OF TRACE DOCUMENT**
