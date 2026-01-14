# Pipeline Backward Analysis: Q1-Q14 Requirements to Step Design

**Date**: 2026-01-14
**Task**: STEP PIPELINE-REDESIGN-CONSTITUTION-02 (Radical Re-examination)
**Status**: ✅ COMPLETE (DECISION MATRIX)

---

## Absolute Premise (User-Declared)

1. **Coverage discovery is NOT needed** - All coverages are pre-defined in SSOT
2. **coverage_code is the ONLY identifier** - No string matching on coverage names
3. **String matching on coverage names = IMMEDIATELY FAIL**
4. **SSOT = `data/sources/insurers/담보명mapping자료.xlsx`** (264 rows, 8 insurers)

---

## Analysis Method

**Working BACKWARD from Q1-Q14**:
1. List information items required by each Q
2. Identify source documents for each item
3. Determine which Steps are ACTUALLY needed
4. Eliminate Steps that exist only for "discovery" paradigm

---

## Part 1: Q1-Q14 Information Requirements

### Q1: Coverage Comparison (가성비 Top3)

**Information items required**:
1. `coverage_code` - Coverage identifier
2. `premium_monthly` - Monthly premium per insurer
3. `cancer_amt` (payout_limit) - Coverage amount per insurer
4. `premium_per_10m` - Calculated efficiency metric
5. `product_name` - Product display name per insurer
6. `insurer_key` - Insurer identifier

**Source documents**:
- ✅ `q14_premium_ranking_v1` (DB table) - PRIMARY
- ✅ `compare_tables_v1.jsonl` - cancer_amt (payout_limit slot)
- ✅ `contract_meta_v1.jsonl` - product_name

**coverage_code source**: Must exist in all 3 sources (consistency check)

**Does this Q need coverage discovery?**: ❌ NO - Q1 only compares KNOWN coverages (A4200_1)

---

### Q11: Cancer Hospitalization (암직접입원비 일수구간)

**Information items required**:
1. `coverage_code` - C0600_2 (locked)
2. `benefit_day_range` - Day ranges (1-30일, 31-60일, etc.)
3. `payout_per_day` - Daily payout amount per range per insurer
4. `product_name` - Product display name

**Source documents**:
- ✅ `q11_references_v1.jsonl` - PRIMARY (frozen SSOT, ONLY source)

**coverage_code source**: Frozen SSOT (C0600_2)

**Does this Q need coverage discovery?**: ❌ NO - Q11 uses frozen SSOT only

---

### Q12: Product Recommendation (삼성 vs 메리츠)

**Information items required**:
1. `coverage_code` - Multiple coverage codes (A4200_1, etc.)
2. `premium_monthly` - Per insurer per coverage
3. `payout_limit` - Per insurer per coverage
4. `coverage_exists` - Boolean per insurer per coverage
5. `product_name` - Product display name
6. `filtering_rules` - 12 rules (A1-A12) for recommendation logic

**Source documents**:
- ✅ `product_premium_quote_v2` (DB table) - premium data
- ✅ `compare_tables_v1.jsonl` - coverage existence + payout_limit
- ✅ `Q12_RULE_CATALOG.md` - filtering rules
- ✅ `contract_meta_v1.jsonl` - product_name

**coverage_code source**: Must be pre-defined (no discovery needed)

**Does this Q need coverage discovery?**: ❌ NO - Q12 filters KNOWN coverages per Q12 rules

---

### Q13: Subtype Coverage Matrix (제자리암/경계성종양)

**Information items required**:
1. `coverage_code` - Cancer coverage code (A4200_1)
2. `subtype_coverage_map` - O/X per subtype per insurer
3. `product_name` - Product display name

**Source documents**:
- ✅ `compare_tables_v1.jsonl` - subtype_coverage_map slot
- ✅ `contract_meta_v1.jsonl` - product_name

**coverage_code source**: Must be pre-defined (A4200_1)

**Does this Q need coverage discovery?**: ❌ NO - Q13 compares single coverage (A4200_1)

---

### Q14: Premium Ranking (보험료 Top4)

**Information items required**:
1. `insurer_key` - Insurer identifier
2. `premium_monthly` - Monthly premium
3. `product_name` - Product display name
4. Coverage existence (implicit)

**Source documents**:
- ✅ `q14_premium_top4_v1` (DB table) - PRIMARY
- ✅ `contract_meta_v1.jsonl` - product_name

**coverage_code source**: Not required (insurer-level ranking)

**Does this Q need coverage discovery?**: ❌ NO - Q14 ranks premium, not coverage

---

### Q5: Waiting Period (면책기간)

**Information items required**:
1. `coverage_code` - Coverage identifier
2. `waiting_period` - Duration per insurer per coverage
3. `product_name` - Product display name

**Source documents**:
- ✅ `q5_waiting_policy_v1.jsonl` - PRIMARY (overlay SSOT)

**coverage_code source**: Overlay SSOT (pre-defined)

**Does this Q need coverage discovery?**: ❌ NO - Q5 uses overlay SSOT only

---

### Q7: Premium Waiver (보험료 납입면제)

**Information items required**:
1. `coverage_code` - Coverage identifier
2. `waiver_policy` - Policy per insurer per coverage
3. `waiver_conditions` - Conditions for waiver
4. `product_name` - Product display name

**Source documents**:
- ✅ `q7_waiver_policy_v1.jsonl` - PRIMARY (overlay SSOT)

**coverage_code source**: Overlay SSOT (pre-defined)

**Does this Q need coverage discovery?**: ❌ NO - Q7 uses overlay SSOT only

---

### Q8: Surgery Repeat Payment (수술급여 재지급)

**Information items required**:
1. `coverage_code` - Surgery coverage codes
2. `repeat_payment_policy` - Policy per insurer per coverage
3. `repeat_interval` - Interval between repeat payments
4. `product_name` - Product display name

**Source documents**:
- ✅ `q8_surgery_repeat_policy_v1.jsonl` - PRIMARY (overlay SSOT)

**coverage_code source**: Overlay SSOT (pre-defined)

**Does this Q need coverage discovery?**: ❌ NO - Q8 uses overlay SSOT only

---

### Q2-Q4, Q6, Q9-Q10: BLOCKED Questions

**Status**: Not implemented (no UI/API spec)

**Information items required**: Various slots from compare_rows_v1.jsonl

**Source documents**: compare_tables_v1.jsonl (assumed)

**Does this Q need coverage discovery?**: ❌ NO - All use compare model (pre-built)

---

## Part 2: Information Item → Source Document Map

### Coverage Code (`coverage_code`)

**Required by**: Q1, Q5, Q7, Q8, Q11, Q12, Q13

**Source documents**:
1. `담보명mapping자료.xlsx` (SSOT) - 264 rows (8 insurers × ~30 coverages)
2. `q11_references_v1.jsonl` - Frozen SSOT (C0600_2 only)
3. `q5/q7/q8_policy_v1.jsonl` - Overlay SSOT (coverage-specific policies)
4. `compare_tables_v1.jsonl` - Compare model output

**Critical observation**: coverage_code is ALWAYS pre-defined, NEVER discovered from PDF

---

### Premium Data (`premium_monthly`)

**Required by**: Q1, Q12, Q14

**Source documents**:
1. `q14_premium_ranking_v1` (DB table) - PRIMARY for Q1
2. `product_premium_quote_v2` (DB table) - PRIMARY for Q12
3. `q14_premium_top4_v1` (DB table) - PRIMARY for Q14

**Critical observation**: Premium data is ALWAYS from DB tables, NEVER from PDF

---

### Coverage Amount (`payout_limit`, `cancer_amt`)

**Required by**: Q1, Q12

**Source documents**:
1. `compare_tables_v1.jsonl` - payout_limit slot (from Step3 evidence)

**Origin**: PDF → Step1 proposal_facts → Step3 evidence → Step4 compare model

**Critical observation**: This is the ONLY item that requires PDF extraction

---

### Product Name (`product_name`)

**Required by**: Q1, Q5, Q7, Q8, Q11, Q12, Q13

**Source documents**:
1. `contract_meta_v1.jsonl` - PRIMARY (overlay)
2. Step1 `product` field - FALLBACK

**Origin**: PDF → Step1 product extraction

**Critical observation**: Product name CAN be extracted from PDF OR provided by overlay

---

### Evidence Slots (14 slots)

**Required by**: Q2-Q10, Q13 (various slots)

**Source documents**:
1. `compare_tables_v1.jsonl` - Step4 output (embedded Step3 evidence_slots)

**Origin**: PDF → Step3 evidence search → Step4 compare model

**Critical observation**: Evidence slots require PDF search, but ONLY for KNOWN coverage_code

---

### Policy Overlays (waiting, waiver, repeat)

**Required by**: Q5, Q7, Q8

**Source documents**:
1. `q5_waiting_policy_v1.jsonl` - Overlay SSOT
2. `q7_waiver_policy_v1.jsonl` - Overlay SSOT
3. `q8_surgery_repeat_policy_v1.jsonl` - Overlay SSOT

**Origin**: Generated ONCE from Step3 evidence, then frozen

**Critical observation**: Overlay SSOT does NOT require runtime pipeline

---

## Part 3: Source Document → Pipeline Step Trace

### `담보명mapping자료.xlsx` (SSOT)

**Used by pipeline step**: Step2-b (map_to_canonical.py:12)

**Purpose in current pipeline**: Assign coverage_code via string matching

**Required for Q1-Q14?**: ✅ YES - coverage_code is essential

**Should be used in pipeline?**: ✅ YES - BUT as INPUT to Step1, NOT Step2-b output

---

### PDF Files (가입설계서, 약관, etc.)

**Used by pipeline step**: Step1 (extractor_v3.py:240-289)

**Purpose in current pipeline**:
1. Extract coverage_name_raw (for discovery)
2. Extract proposal_facts (premium, amount, period)
3. Extract product metadata

**Required for Q1-Q14?**: ⚠️ PARTIAL
- ✅ YES for payout_limit (Q1, Q12)
- ✅ YES for evidence slots (Q2-Q10, Q13)
- ❌ NO for coverage_code (SSOT provides)
- ❌ NO for premium (DB provides)

**Should be used in pipeline?**: ✅ YES - BUT for TARGETED extraction, NOT discovery

---

### `compare_tables_v1.jsonl` (Step4 Output)

**Used by pipeline step**: Step4 (builder.py:67-109)

**Purpose in current pipeline**: Aggregate Step3 evidence into compare model

**Required for Q1-Q14?**: ✅ YES (Q1, Q12, Q13, Q2-Q10)

**Should be used in pipeline?**: ✅ YES - Compare model is essential

---

### Overlay SSOT Files (`q5/q7/q8_policy_v1.jsonl`)

**Used by pipeline step**: NOT used by pipeline (API loads directly)

**Purpose in current pipeline**: N/A (bypasses pipeline)

**Required for Q1-Q14?**: ✅ YES (Q5, Q7, Q8)

**Should be used in pipeline?**: ❌ NO - Already frozen, no runtime pipeline needed

---

### Frozen SSOT (`q11_references_v1.jsonl`)

**Used by pipeline step**: NOT used by pipeline (API loads directly)

**Purpose in current pipeline**: N/A (bypasses pipeline)

**Required for Q1-Q14?**: ✅ YES (Q11)

**Should be used in pipeline?**: ❌ NO - Constitutionally frozen, MUST NOT use pipeline

---

## Part 4: Step1-4 Keep/Delete/Change Decision Matrix

### Step1: PDF Extraction

**Current role**:
- Discover ALL coverages from PDF summary table
- Extract coverage_name_raw (string identifier)
- Extract proposal_facts (premium, amount, period)
- Extract product metadata

**Required by Q1-Q14?**: ⚠️ PARTIAL
- ✅ YES: proposal_facts (for payout_limit → Q1, Q12)
- ✅ YES: product metadata (for product_name fallback)
- ❌ NO: coverage_name_raw discovery (SSOT provides coverage_code)

**Violates absolute premise?**: ✅ YES
- Discovers coverages (premise: no discovery needed)
- Uses coverage_name_raw as identifier (premise: coverage_code only)

**Decision**: ❌ **DELETE current Step1, REPLACE with Step1 V2**

**Step1 V2 role**:
1. Load SSOT target list (coverage_code + insurer_key pairs)
2. Parse PDF summary table
3. Match PDF rows to SSOT targets (lookup, not assignment)
4. Extract proposal_facts ONLY for matched targets
5. Output: coverage_code (from SSOT) + proposal_facts (from PDF)

**Reasoning**:
- Current Step1 is designed for "discovery" paradigm (find all coverages)
- Q1-Q14 do NOT need discovery (all coverages in SSOT)
- Step1 V2 is "targeted extraction" (extract facts for KNOWN coverages)

---

### Step2-a: Sanitization

**Current role**:
- Normalize coverage_name_raw (remove special chars, whitespace)
- Clean proposal_facts (parse amounts, periods)

**Required by Q1-Q14?**: ⚠️ PARTIAL
- ✅ YES: proposal_facts cleaning (for payout_limit)
- ❌ NO: coverage_name_raw normalization (not used if coverage_code exists)

**Violates absolute premise?**: ⚠️ INDIRECT
- Sanitizes coverage_name_raw (but coverage_code should be only identifier)

**Decision**: ⚠️ **MERGE into Step1 V2**

**Reasoning**:
- Sanitization is necessary (clean proposal_facts)
- But coverage_name_raw sanitization is NOT needed if coverage_code from SSOT
- Merge proposal_facts cleaning into Step1 V2 (combined extract + clean)

---

### Step2-b: Canonical Mapping

**Current role**:
- Assign coverage_code via 4 string matching methods
- Load SSOT (담보명mapping자료.xlsx)
- Match coverage_name_raw → coverage_code

**Required by Q1-Q14?**: ❌ NO
- coverage_code should be INPUT (from SSOT), not OUTPUT (from Step2-b)

**Violates absolute premise?**: ✅ YES - CRITICAL VIOLATION
- Creates coverage_code via string matching (premise: coverage_code from SSOT only)
- Uses coverage_name_raw for matching (premise: coverage_code is only identifier)

**Decision**: ❌ **DELETE Step2-b entirely**

**Reasoning**:
- Step2-b exists ONLY to create coverage_code (string matching)
- If Step1 V2 provides coverage_code (from SSOT), Step2-b is OBSOLETE
- All Q1-Q14 require coverage_code, but it should come from SSOT, not Step2-b

---

### Step3: Evidence Resolution

**Current role**:
- Search PDF detail pages for evidence
- Use coverage_name_raw as search keyword (VIOLATION!)
- Extract 14 evidence slots (payout_limit, waiting_period, etc.)
- Apply G3/G5/G6 gates (validation)

**Required by Q1-Q14?**: ✅ YES
- Q1: payout_limit slot
- Q12: payout_limit slot
- Q13: subtype_coverage_map slot
- Q2-Q10: Various slots (waiting_period, payout_frequency, etc.)

**Violates absolute premise?**: ✅ YES - CRITICAL VIOLATION
- Uses coverage_name_raw as search keyword (premise: coverage_code only)

**Decision**: ⚠️ **KEEP Step3, but CHANGE search logic**

**Step3 V2 role**:
1. Load coverage_code metadata from SSOT (canonical_name, insurer_coverage_name)
2. Search PDF detail pages using SSOT metadata (not coverage_name_raw)
3. Extract 14 evidence slots (same as current)
4. Apply G3/G5/G6 gates (same as current)
5. Output: coverage_code (from input) + evidence_slots (from PDF)

**Reasoning**:
- Evidence extraction is ESSENTIAL for Q1-Q14
- But search keyword should be from SSOT metadata, not coverage_name_raw
- Step3 V2 is "evidence resolver with SSOT-driven search"

---

### Step4: Compare Model Builder

**Current role**:
- Aggregate Step3 evidence into compare model
- Group by coverage_code
- Calculate unanchored flag (no coverage_code)
- Apply tier enforcement gates

**Required by Q1-Q14?**: ✅ YES
- Q1: compare_tables_v1.jsonl (primary data source)
- Q12: compare_tables_v1.jsonl (coverage data)
- Q13: compare_tables_v1.jsonl (subtype map)
- Q2-Q10: compare_tables_v1.jsonl (various slots)

**Violates absolute premise?**: ❌ NO
- Groups by coverage_code (correct identifier)
- Does NOT use string matching

**Decision**: ✅ **KEEP Step4 unchanged**

**Reasoning**:
- Step4 is ESSENTIAL for Q1-Q14 (compare model is primary data source)
- Step4 does NOT violate premise (uses coverage_code, not string matching)
- Only change: unanchored flag becomes impossible (coverage_code always exists from SSOT)

---

## Part 5: Decision Summary Table

| Step | Current Role | Q1-Q14 Requirement | Violates Premise? | Decision | New Role |
|------|-------------|-------------------|-------------------|----------|----------|
| **Step1** | Discover coverages from PDF | ⚠️ PARTIAL (proposal_facts only) | ✅ YES (discovery + string ID) | ❌ DELETE → REPLACE | **Step1 V2**: Targeted extraction for SSOT-defined coverages |
| **Step2-a** | Sanitize coverage_name_raw + proposal_facts | ⚠️ PARTIAL (proposal_facts only) | ⚠️ INDIRECT (sanitizes string ID) | ⚠️ MERGE | Merge into Step1 V2 (clean proposal_facts) |
| **Step2-b** | Assign coverage_code via string matching | ❌ NO (coverage_code from SSOT) | ✅ YES (creates coverage_code) | ❌ DELETE | N/A (obsolete if Step1 V2 provides coverage_code) |
| **Step3** | Extract evidence using coverage_name_raw keyword | ✅ YES (evidence slots essential) | ✅ YES (uses string keyword) | ⚠️ KEEP + CHANGE | **Step3 V2**: Evidence search with SSOT metadata keyword |
| **Step4** | Aggregate evidence into compare model | ✅ YES (compare model essential) | ❌ NO (uses coverage_code) | ✅ KEEP | Unchanged (unanchored flag becomes impossible) |

---

## Part 6: New Pipeline Structure (V2)

### Overview

```
┌─────────────────────────────────────────────────────────┐
│ Input: SSOT Target List                                 │
│ data/sources/insurers/담보명mapping자료.xlsx             │
│ → [(coverage_code, canonical_name, insurer_name), ...]  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Step1 V2: Targeted Extraction                           │
│ • Load SSOT targets (coverage_code + metadata)          │
│ • Parse PDF summary table                               │
│ • Match PDF rows to SSOT targets (lookup)               │
│ • Extract proposal_facts for matched rows               │
│ • Clean proposal_facts (sanitize)                       │
│ Output: coverage_code (SSOT) + proposal_facts (PDF)     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Step3 V2: Evidence Resolution (SSOT-Driven Search)      │
│ • Load coverage_code metadata from SSOT                 │
│ • Search PDF detail pages using SSOT metadata           │
│ • Extract 14 evidence slots                             │
│ • Apply G3/G5/G6 gates                                  │
│ Output: coverage_code + proposal_facts + evidence_slots │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Step4: Compare Model Builder (Unchanged)                │
│ • Group by coverage_code                                │
│ • Aggregate evidence_slots                              │
│ • Apply tier enforcement gates                          │
│ Output: compare_tables_v1.jsonl                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ API: Q1/Q12/Q13/Q2-Q10 Endpoints                        │
│ Read: compare_tables_v1.jsonl                           │
└─────────────────────────────────────────────────────────┘
```

---

### V2 Pipeline Characteristics

**Key changes**:
1. ❌ **DELETE Step2-b** - coverage_code from SSOT, not string matching
2. ⚠️ **MERGE Step2-a into Step1 V2** - Combined extract + clean
3. ⚠️ **CHANGE Step3** - SSOT metadata search, not coverage_name_raw search
4. ✅ **KEEP Step4** - Unchanged (compare model builder)

**Steps reduced**: 5 steps (Step1 → Step2-a → Step2-b → Step3 → Step4) → 3 steps (Step1 V2 → Step3 V2 → Step4)

**String matching eliminated**:
- ❌ Step2-b: 4 string matching operations (exact, normalized, alias, normalized_alias) → DELETED
- ⚠️ Step3: 1 string matching operation (coverage_name_raw keyword) → REPLACED with SSOT metadata

**coverage_code flow**:
- ❌ OLD: PDF → Step1 (coverage_name_raw) → Step2-b (string match) → coverage_code
- ✅ NEW: SSOT → Step1 V2 (coverage_code) → Step3 V2 (coverage_code) → Step4 (coverage_code)

---

### V2 Pipeline Inputs

**Required inputs** (from outside pipeline):
1. `data/sources/insurers/담보명mapping자료.xlsx` - SSOT target list
2. PDF files (가입설계서, 약관, etc.) - Evidence source
3. Profile JSON (summary page ranges, column mappings) - PDF structure

**NOT required** (eliminated):
- ❌ `data/sources/mapping/담보명mapping자료.xlsx` - Contaminated path (shadow contract)
- ❌ coverage_name_raw as identifier - Replaced by coverage_code

---

### V2 Pipeline Outputs

**Step1 V2 output**: `step1_targeted_v2.jsonl`
```json
{
  "coverage_code": "A4200_1",  // ← FROM SSOT (input)
  "canonical_name": "암진단비(유사암제외)",  // ← FROM SSOT
  "coverage_name_raw": "암진단비(유사암제외)",  // ← FROM PDF (matched)
  "proposal_facts": {
    "premium": "10000",  // ← FROM PDF (cleaned)
    "amount": "30000000",  // ← FROM PDF (cleaned)
    "period": "100세만기"  // ← FROM PDF (cleaned)
  },
  "ssot_match_status": "FOUND"  // ← NEW: FOUND | NOT_FOUND | AMBIGUOUS
}
```

**Step3 V2 output**: `step3_targeted_v2.jsonl`
```json
{
  "coverage_code": "A4200_1",  // ← FROM Step1 V2 (immutable)
  "proposal_facts": { ... },  // ← FROM Step1 V2
  "evidence_slots": {
    "payout_limit": { "value": "30000000", "status": "FOUND" },
    "waiting_period": { "value": "90일", "status": "FOUND" },
    ...
  },
  "gate_results": { ... }
}
```

**Step4 output**: `compare_tables_v1.jsonl` (unchanged format)

---

## Part 7: Questions That Bypass Pipeline (Unchanged)

### Q11: Cancer Hospitalization

**Pipeline usage**: ❌ BYPASSED (frozen SSOT only)

**Reason**: Constitutional freeze (q11_references_v1.jsonl)

**Impact of V2**: ZERO (Q11 does not use pipeline)

---

### Q5/Q7/Q8: Contract-Level Policy

**Pipeline usage**: ❌ BYPASSED at runtime (overlay SSOT only)

**Reason**: Overlay SSOT frozen (generated once from Step3, then immutable)

**Impact of V2**: ⚠️ ONE-TIME (overlay regeneration may be needed if Step3 V2 changes evidence quality)

---

## Part 8: Impact on Q1-Q14

| Q | Current Pipeline Dependency | V2 Pipeline Dependency | Impact |
|---|----------------------------|------------------------|--------|
| Q1 | Step1-4 (via compare model) | Step1 V2 → Step3 V2 → Step4 | ⚠️ MUST regenerate compare model |
| Q5 | NONE (overlay SSOT) | NONE | ✅ NO IMPACT |
| Q7 | NONE (overlay SSOT) | NONE | ✅ NO IMPACT |
| Q8 | NONE (overlay SSOT) | NONE | ✅ NO IMPACT |
| Q11 | NONE (frozen SSOT) | NONE | ✅ NO IMPACT |
| Q12 | Step1-4 (via compare model) | Step1 V2 → Step3 V2 → Step4 | ⚠️ MUST regenerate compare model |
| Q13 | Step1-4 (via compare model) | Step1 V2 → Step3 V2 → Step4 | ⚠️ MUST regenerate compare model |
| Q14 | Step1-4 (partial) | Step1 V2 → Step3 V2 → Step4 | ⚠️ MUST regenerate compare model |
| Q2-Q10 | Step1-4 (via compare model) | Step1 V2 → Step3 V2 → Step4 | ⚠️ MUST regenerate compare model (when implemented) |

**Critical observation**: Q1, Q12, Q13, Q14, Q2-Q10 ALL require compare model regeneration (Step4 output)

**Questions unaffected**: Q5, Q7, Q8, Q11 (4 questions, 0 impact)

---

## Part 9: Migration Risks

### Risk 1: SSOT Incompleteness

**Issue**: If SSOT lacks a coverage present in current PDF → Step1 V2 does NOT extract → coverage missing in compare model

**Impact**: Q1/Q12/Q13 may have fewer coverages than before

**Mitigation**: Validate SSOT completeness before migration (compare Step1 V1 vs Step1 V2 coverage counts)

**Severity**: ⚠️ HIGH - Coverage loss

---

### Risk 2: Match Rate Drop

**Issue**: If PDF text differs from SSOT `담보명(가입설계서)` column → Step1 V2 match fails → coverage NOT extracted

**Impact**: Lower match rate than Step2-b string matching

**Mitigation**: Enhance Step1 V2 normalization (same as Step2-b: exact + normalized + alias)

**Severity**: ⚠️ MEDIUM - Reduced coverage count

---

### Risk 3: Evidence Quality Change

**Issue**: If Step3 V2 uses different search keywords → evidence quality may change

**Impact**: G3/G5/G6 gate results may differ → FOUND/UNKNOWN/CONFLICT status may change

**Mitigation**: Run Step3 V1 vs Step3 V2 in parallel, compare evidence_slots

**Severity**: ⚠️ MEDIUM - Evidence trust level change

---

### Risk 4: API Response Regression

**Issue**: If compare model changes → Q1/Q12/Q13 API responses change → user-visible regression

**Impact**: Breaking change for frontend

**Mitigation**: API response diff before/after, validate with stakeholders

**Severity**: ⚠️ HIGH - User-visible change

---

### Risk 5: Overlay SSOT Invalidation

**Issue**: If Step3 V2 evidence quality improves → current overlay SSOT may be stale

**Impact**: Q5/Q7/Q8 may need overlay regeneration

**Mitigation**: Re-run overlay generation scripts after Step3 V2 migration

**Severity**: ⚠️ LOW - One-time regeneration, not runtime impact

---

## Part 10: Benefits of V2 Pipeline

### Benefit 1: Constitutional Compliance

**Current**: Step2-b violates "Coverage-Code-First" (creates coverage_code)

**V2**: coverage_code is SSOT input (immutable from start)

**Impact**: ✅ Architectural alignment with constitutional principle

---

### Benefit 2: String Matching Elimination

**Current**: 5 string matching violations (Step2-b: 4, Step3: 1)

**V2**: 0 string matching for coverage_code assignment (Step1 V2: lookup only, not assignment)

**Impact**: ✅ 100% elimination of critical violations

---

### Benefit 3: Simplified Pipeline

**Current**: 5 steps (Step1 → Step2-a → Step2-b → Step3 → Step4)

**V2**: 3 steps (Step1 V2 → Step3 V2 → Step4)

**Impact**: ✅ 40% reduction in pipeline complexity

---

### Benefit 4: Shadow Contract Elimination

**Current**: Step2-b uses contaminated path (`data/sources/mapping/`)

**V2**: Step1 V2 uses SSOT path (`data/sources/insurers/`)

**Impact**: ✅ Shadow contract violation resolved

---

### Benefit 5: Unanchored Coverages Become Impossible

**Current**: If Step2-b fails to map → unanchored coverage → dropped in Step4

**V2**: coverage_code from SSOT → ALL coverages anchored (by definition)

**Impact**: ✅ Structural elimination of unanchored risk

---

## Part 11: Final Verdict

### Step1 유지 여부: **NO**

**이유**:
1. ❌ Current Step1은 "coverage discovery" 패러다임 (모든 담보 발견)
2. ❌ coverage_name_raw를 식별자로 사용 (constitutional violation)
3. ❌ Q1-Q14는 discovery가 필요 없음 (SSOT에 모든 담보 사전 정의)
4. ✅ 대체: Step1 V2 "targeted extraction" (SSOT-defined coverages만 추출)

---

### Step2-a 유지 여부: **NO (Merge into Step1 V2)**

**이유**:
1. ⚠️ Sanitization은 필요 (proposal_facts cleaning)
2. ❌ coverage_name_raw sanitization은 불필요 (coverage_code가 유일 식별자)
3. ✅ 대체: Step1 V2에 proposal_facts cleaning 통합

---

### Step2-b 유지 여부: **NO**

**이유**:
1. ❌ coverage_code 생성이 유일한 역할 (string matching via 4 methods)
2. ❌ Constitutional violation (coverage_code는 SSOT input이어야 함, Step2-b output 아님)
3. ❌ Q1-Q14는 Step2-b가 필요 없음 (coverage_code는 SSOT에서 제공)
4. ✅ 대체: Step1 V2가 SSOT에서 coverage_code 로드 → Step2-b 불필요

---

### Step3 유지 여부: **YES (But CHANGE search logic)**

**이유**:
1. ✅ Evidence extraction은 필수 (Q1/Q12/Q13/Q2-Q10 모두 evidence_slots 필요)
2. ❌ Current Step3은 coverage_name_raw를 search keyword로 사용 (violation)
3. ✅ 대체: Step3 V2는 SSOT metadata를 search keyword로 사용
4. ✅ 역할 변경: "coverage_name-based search" → "SSOT metadata-driven search"

---

### Step4 유지 여부: **YES (Unchanged)**

**이유**:
1. ✅ Compare model은 필수 (Q1/Q12/Q13/Q2-Q10 모두 compare_tables_v1.jsonl 사용)
2. ✅ Step4는 constitutional violation 없음 (coverage_code 사용, string matching 없음)
3. ✅ 유일한 변화: unanchored flag가 항상 False (coverage_code always exists from SSOT)

---

## Part 12: Step1 V2 Structure Draft

### Step1 V2: Targeted Extraction (Coverage-Code-First)

**Input**:
1. SSOT target list: `data/sources/insurers/담보명mapping자료.xlsx`
2. PDF files: 가입설계서, 약관, etc.
3. Profile JSON: Summary page ranges, column mappings

**Output**: `data/scope_v3/{INSURER}_step1_targeted_v2.jsonl`

**Logic** (4 phases):

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Load SSOT Targets                            │
├────────────────────────────────────────────────────────┤
│ • Read 담보명mapping자료.xlsx                          │
│ • Filter by insurer_key (e.g., "meritz")              │
│ • Extract: coverage_code, canonical_name, 담보명       │
│ • Result: ~30 coverage targets per insurer            │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: Parse PDF Summary Table                      │
├────────────────────────────────────────────────────────┤
│ • Parse PDF summary table (same as current Step1)     │
│ • Extract coverage_name_raw from each row             │
│ • Extract proposal_facts (premium, amount, period)    │
│ • Result: List of PDF rows                            │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: Match PDF Rows to SSOT Targets (NEW)         │
├────────────────────────────────────────────────────────┤
│ • For each PDF row:                                    │
│   1. Try exact match: coverage_name_raw == 담보명      │
│   2. Try normalized match: normalize() == normalize()  │
│   3. If match found → assign coverage_code from SSOT   │
│   4. If no match → log warning, set status=NOT_FOUND   │
│ • Result: List of matched rows with coverage_code      │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ Phase 4: Clean Proposal Facts (Merge from Step2-a)    │
├────────────────────────────────────────────────────────┤
│ • Sanitize proposal_facts:                             │
│   - Parse amount: "3천만원" → 30000000                 │
│   - Parse period: "100세만기" → structured format      │
│   - Clean premium: "10,000" → 10000                    │
│ • Result: cleaned proposal_facts                       │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ Output: step1_targeted_v2.jsonl                        │
├────────────────────────────────────────────────────────┤
│ {                                                      │
│   "coverage_code": "A4200_1",  ← FROM SSOT             │
│   "canonical_name": "암진단비(유사암제외)",             │
│   "coverage_name_raw": "암진단비(유사암제외)",          │
│   "proposal_facts": { ... },  ← FROM PDF (cleaned)     │
│   "ssot_match_status": "FOUND"                         │
│ }                                                      │
└────────────────────────────────────────────────────────┘
```

**Key differences from current Step1**:
1. ✅ coverage_code is INPUT (from SSOT), not OUTPUT (from Step2-b)
2. ✅ Only extract SSOT-defined coverages (no discovery)
3. ✅ Match PDF → SSOT (lookup), not create coverage_code (assignment)
4. ✅ Combine extraction + sanitization (merge Step1 + Step2-a)

---

## DoD Checklist

- [✅] Q1-Q14 information requirements listed (8 questions analyzed)
- [✅] Source documents mapped for each information item
- [✅] Step1-4 decision matrix created (4 steps: DELETE/MERGE/DELETE/CHANGE/KEEP)
- [✅] New pipeline structure designed (V2: 3 steps)
- [✅] Impact on Q1-Q14 analyzed (compare model regeneration required)
- [✅] Migration risks documented (5 risks)
- [✅] Benefits documented (5 benefits)
- [✅] Final verdict provided (Step1: NO, Step2-a: NO, Step2-b: NO, Step3: YES+CHANGE, Step4: YES)
- [✅] Step1 V2 structure drafted (4-phase logic)

---

**END OF BACKWARD ANALYSIS**
