# PIPELINE REALIGNMENT DECISION

**Purpose**: Lock to ONE structural direction. Reject all other options explicitly.

**Based on**: PIPELINE_INVENTORY.md + DATA_CONTRACT_TRACE.md + MISMATCH_ROOT_CAUSE_MAP.md

---

## DECISION: Canonical-First Pipeline (Excel-Driven Scope)

### Core Principle
**Start with canonical coverage definitions (Excel) as SSOT input, then map proposal to canonical.**

**Current (BROKEN)**: Proposal → Extract → Map → Sanitize → Lock
**Correct (FIXED)**: Canonical → Generate Variants → Extract+Match → Lock

---

## New Pipeline Order

```
STEP 0: Load Canonical Definitions (Excel SSOT)
  Input: data/sources/mapping/담보명mapping자료.xlsx
  Output: data/canonical/{insurer}_canonical_scope.csv
    - coverage_code (PK)
    - coverage_name_canonical
    - insurer_aliases (JSON array of known proposal names)
    - search_variants (generated: normalized, prefix-stripped, parentheses-stripped)

STEP 1: Extract Proposal Coverages (Proposal PDF)
  Input: data/sources/insurers/{insurer}/가입설계서/*.pdf
  Output: data/proposal/{insurer}_proposal_raw.csv
    - proposal_name_raw (as-is from PDF)
    - source_page
    - proposal_amount (if found in same table)

STEP 2: Match Proposal to Canonical (Fuzzy + Variant)
  Input:
    - data/canonical/{insurer}_canonical_scope.csv
    - data/proposal/{insurer}_proposal_raw.csv
  Logic:
    - Exact match (proposal_name_raw == canonical_name)
    - Alias match (proposal_name_raw in insurer_aliases)
    - Variant match (normalized proposal_name in search_variants)
    - Fuzzy match (optional: difflib.SequenceMatcher, threshold 0.85)
  Output: data/scope/{insurer}_scope_matched.csv
    - coverage_code (from canonical)
    - coverage_name_canonical (from canonical)
    - proposal_name_raw (from proposal)
    - proposal_amount (from proposal, if extracted)
    - match_type (exact | alias | variant | fuzzy | unmatched)
    - match_confidence (0.0-1.0)

STEP 3: Sanitize Matched Scope (Filter Non-Coverages)
  Input: data/scope/{insurer}_scope_matched.csv
  Logic:
    - DROP condition sentences (same as current STEP 1b)
    - DROP administrative items
    - KEEP only matched (coverage_code is not null)
  Output: data/scope/{insurer}_scope_final.csv
    - Same columns as input, filtered

STEP 4: Build Coverage Cards (SSOT Lock)
  Input:
    - data/scope/{insurer}_scope_final.csv
    - data/evidence_pack/{insurer}_evidence_pack.jsonl (existing)
  Output: data/compare/{insurer}_coverage_cards.jsonl (SSOT)
    - coverage_code (LOCKED)
    - coverage_name_canonical (LOCKED)
    - proposal_name_raw (LOCKED)
    - proposal_amount (LOCKED — from STEP 1 if available)
    - mapping_status (LOCKED)
    - evidence_status
    - evidences (from evidence_pack)

STEP 5: Enrich with Evidence (if needed)
  (Existing STEP 4: evidence search)

STEP 6: Amount Validation (NOT Extraction)
  Input: data/compare/{insurer}_coverage_cards.jsonl
  Logic:
    - IF proposal_amount exists in card → status=CONFIRMED
    - ELSE → search proposal PDF for amount (fallback)
  Output: data/compare/{insurer}_coverage_cards.jsonl (updated)
```

---

## Key Changes from Current Pipeline

### Change 1: Excel Becomes INPUT Contract (Not Mapping)
**Current**:
- Excel used only for Step2 mapping (after extraction)
- Excel is REACTIVE (maps whatever Step1 extracted)

**New**:
- Excel defines ENTIRE scope (what coverages SHOULD exist)
- Excel is PROACTIVE (defines truth, proposal follows)

**Rationale**:
- Excel contains canonical definitions (신정원코드명, cre_cvr_cd)
- Per CLAUDE.md: Excel is "INPUT contract", manual, immutable
- Proposal may be incomplete/inconsistent → Excel is more reliable

---

### Change 2: Variant Generation Happens BEFORE Extraction
**Current**:
- STEP 1a extracts proposal names as-is
- STEP 2 tries to match to Excel (static)
- STEP 7 tries to normalize (too late)

**New**:
- STEP 0 generates ALL possible variants from Excel
- STEP 2 matches proposal names using pre-built variant index
- NO late-stage normalization needed

**Variant Types** (generated in STEP 0):
1. **Exact**: "암진단비(유사암제외)"
2. **Normalized**: "암진단비유사암제외" (remove special chars)
3. **Parentheses-stripped**: "암진단비" (remove suffix)
4. **Prefix-stripped**: "상해사망" (from "일반상해사망")
5. **Semantic substitutions**: "4대유사암진단비" (if Excel lists "유사암(8대)진단비")

**Example** (Hanwha A4210_2):
```json
{
  "coverage_code": "A4210_2",
  "coverage_name_canonical": "유사암(8대)진단비",
  "insurer_aliases": ["유사암(8대) 진단비"],  // from Excel
  "search_variants": [
    "유사암(8대)진단비",       // normalized
    "유사암진단비",           // parentheses stripped
    "8대유사암진단비",        // reordered
    "4대유사암진단비"         // semantic substitution (4↔8)
  ]
}
```

---

### Change 3: Amount Extraction Moves to STEP 1 (Proposal Extraction)
**Current**:
- STEP 1a: Extract coverage names only
- STEP 7: Extract amounts (separate pass, different table)
- Problem: Same coverage has different names in listing vs amount tables

**New**:
- STEP 1: Extract (coverage_name, amount) pairs TOGETHER from proposal PDF
- Store both in `proposal_raw.csv`
- STEP 2 matching uses proposal_name_raw (which already has amount linked)

**Rationale**:
- Avoids "listing table name ≠ amount table name" mismatch
- Simpler: one PDF parse instead of two
- More accurate: preserves proposal structure

---

### Change 4: Sanitization Moves AFTER Matching (Not Before)
**Current**:
- STEP 1b sanitizes BEFORE matching
- Problem: May drop valid proposal names that haven't been matched yet

**New**:
- STEP 3 sanitizes AFTER matching
- Only drops UNMATCHED rows (coverage_code is null)
- Keeps ALL matched rows (even if name looks like condition sentence)

**Rationale**:
- Matching should see ALL proposal data (don't filter prematurely)
- Sanitization should only remove NON-coverages (confirmed by match failure)

---

### Change 5: SSOT Lock Includes proposal_amount (From STEP 1)
**Current**:
- Cards locked in STEP 5 (without amount)
- Amount added later in STEP 7 (in-place update)

**New**:
- Cards locked in STEP 4 (WITH amount from STEP 1)
- No in-place updates
- Amount field is IMMUTABLE once locked

**Rationale**:
- Simpler: one write, no updates
- More reliable: amount extracted with proposal_name in single pass
- Audit-friendly: SSOT never changes after creation

---

## Options REJECTED

### REJECTED Option 1: Keep Current Order, Improve Step7 Normalization
**Proposal**: Add fuzzy matching to Step7, handle more patterns

**Why REJECTED**:
- Step7 has no Excel access (proven in MISMATCH_ROOT_CAUSE_MAP.md)
- Cannot generate semantic substitutions ("4대" → "8대")
- Cannot reconcile proposal table name ≠ amount table name
- Band-aid fix, not structural solution

---

### REJECTED Option 2: LLM-Based Matching
**Proposal**: Use LLM to match proposal names to canonical names

**Why REJECTED**:
- Per CLAUDE.md: "LLM 요약/추론/생성" is FORBIDDEN
- Per CLAUDE.md: "담보명 자동 매칭/추천" is FORBIDDEN
- Non-deterministic, audit trail unclear
- Performance/cost concerns

---

### REJECTED Option 3: Proposal-First (Keep Current Step1a)
**Proposal**: Keep extracting proposal first, but improve matching later

**Why REJECTED**:
- Proposal is inconsistent (proven: different names in different tables)
- Proposal may be incomplete (missing coverages)
- Excel is SSOT (per CLAUDE.md), not proposal
- Current approach has 0-17% CONFIRMED rates (proven in MISMATCH_ROOT_CAUSE_MAP.md)

---

### REJECTED Option 4: Dual-Source (Proposal + Excel in Parallel)
**Proposal**: Extract from both, then merge

**Why REJECTED**:
- Merging logic is complex (which source wins?)
- Duplicates effort
- Excel already contains proposal aliases (Excel is superset)
- Simpler to use Excel as canonical input

---

### REJECTED Option 5: Keep Step1a, Add Alias File Separately
**Proposal**: Maintain current pipeline, generate alias file offline

**Why REJECTED**:
- Doesn't fix "listing name ≠ amount name" problem
- Doesn't fix late-stage normalization
- Doesn't move sanitization to correct position
- Partial fix, not structural realignment

---

## Implementation Constraints (LOCKED)

### Constraint 1: Excel is IMMUTABLE (Manual Only)
- Per CLAUDE.md: "수동 편집은 허용, 코드로 생성/변경 금지"
- STEP 0 reads Excel, does NOT modify it
- Variants generated in-memory or separate CSV (not Excel)

### Constraint 2: SSOT Contract Preserved
- `data/compare/*_coverage_cards.jsonl` remains SSOT
- Audit SSOT: `docs/audit/AMOUNT_STATUS_DASHBOARD.md`
- No breaking changes to downstream consumers (API, UI)

### Constraint 3: No LLM, No Fuzzy Logic (Optional)
- Exact/alias/variant matching ONLY
- Fuzzy matching (difflib) is OPTIONAL, low priority
- All matching must be deterministic, auditable

### Constraint 4: Scope Gate Still Applies
- `core/scope_gate.py` filters coverages
- Only IN-SCOPE coverages (from Excel) are processed
- OUT-OF-SCOPE proposal entries are dropped (logged)

---

## Migration Path (Existing Data)

### Phase 1: Proof of Concept (1 Insurer)
1. Implement STEP 0 (canonical loader) for Hanwha
2. Generate search_variants (exact, normalized, prefix-stripped, parentheses-stripped)
3. Re-run STEP 1 (extract proposal + amounts)
4. Re-run STEP 2 (match with variants)
5. Compare: Old coverage_cards vs New coverage_cards
6. Measure: CONFIRMED % improvement (17.4% → target 90%+)

### Phase 2: Validate (Heungkuk)
1. Apply same pipeline to Heungkuk
2. Target: 0% → 80%+ CONFIRMED
3. Validate: No regression on other insurers (Samsung, DB, Meritz, Lotte, Hyundai, KB)

### Phase 3: Rollout (All 8 Insurers)
1. Re-run pipeline for all insurers
2. Replace old coverage_cards.jsonl
3. Re-run audit (generate new AMOUNT_STATUS_DASHBOARD.md)
4. Lock: Tag as `realignment-v2-complete`

---

## Verification Criteria (Definition of Done)

### Success Metrics
- ✅ Hanwha: CONFIRMED ≥ 90% (was 17.4%)
- ✅ Heungkuk: CONFIRMED ≥ 80% (was 0%)
- ✅ Other 6 insurers: NO REGRESSION (maintain 88-100%)
- ✅ Overall KPI: IN-SCOPE CONFIRMED ≥ 95% (was 99.4%, but excluding outliers)

### Structural Checks
- ✅ Excel is FIRST input (not Step1a proposal extraction)
- ✅ Variants generated BEFORE matching
- ✅ Amount extracted WITH proposal name (same table)
- ✅ Sanitization happens AFTER matching
- ✅ SSOT locked once (no in-place updates)

### Regression Tests
- ✅ Existing tests pass (202+ tests, 38 xfailed)
- ✅ coverage_cards.jsonl schema unchanged
- ✅ API contract unchanged (apps/api/dto.py)
- ✅ Audit dashboard format unchanged

---

## Directory Structure (New Artifacts)

```
data/
  canonical/
    {insurer}_canonical_scope.csv        ← NEW (STEP 0 output)
  proposal/
    {insurer}_proposal_raw.csv           ← NEW (STEP 1 output, replaces *_scope.csv)
  scope/
    {insurer}_scope_matched.csv          ← NEW (STEP 2 output, replaces *_scope_mapped.csv)
    {insurer}_scope_final.csv            ← NEW (STEP 3 output, replaces *_scope_mapped.sanitized.csv)
  compare/
    {insurer}_coverage_cards.jsonl       ← UNCHANGED (SSOT)

pipeline/
  step0_canonical_loader/
    load_canonical.py                    ← NEW
  step1_proposal_extractor/
    extract_proposal.py                  ← REPLACES step1_extract_scope/run.py
  step2_proposal_matcher/
    match_to_canonical.py                ← REPLACES step2_canonical_mapping/map_to_canonical.py
  step3_sanitize/
    sanitize_matched.py                  ← REPLACES step1_sanitize_scope/run.py (reordered)
  step4_build_cards/
    build_cards.py                       ← MODIFIED (use new inputs)
```

---

## Code Changes Summary

### Files to CREATE
- `pipeline/step0_canonical_loader/load_canonical.py`
- `pipeline/step1_proposal_extractor/extract_proposal.py`
- `pipeline/step2_proposal_matcher/match_to_canonical.py`
- `pipeline/step3_sanitize/sanitize_matched.py`

### Files to MODIFY
- `pipeline/step4_build_cards/build_cards.py` (change input paths)
- `core/scope_gate.py` (add resolve_canonical_csv() function)

### Files to DEPRECATE (keep for reference, not execution)
- `pipeline/step1_extract_scope/run.py` → DEPRECATED (replaced by step1_proposal_extractor)
- `pipeline/step2_canonical_mapping/map_to_canonical.py` → DEPRECATED (replaced by step2_proposal_matcher)
- `pipeline/step1_sanitize_scope/run.py` → DEPRECATED (replaced by step3_sanitize, reordered)
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` → DEPRECATED (amount extraction moved to STEP 1)

---

## Open Questions (To Resolve in STEP 5)

### Q1: Semantic Substitutions (e.g., "4대" ↔ "8대")
- **Option A**: Hardcode substitution rules (insurer-specific)
- **Option B**: Extract from Excel comments/metadata
- **Option C**: Skip for now, handle manually in Excel
- **Recommendation**: Option C (manual), revisit if KPI < 90%

### Q2: Fuzzy Matching Threshold
- **Option A**: Use difflib.SequenceMatcher, threshold 0.85
- **Option B**: Use Levenshtein distance, threshold ≤ 3
- **Option C**: No fuzzy matching (exact/alias/variant only)
- **Recommendation**: Option C (no fuzzy), use exact/variant first

### Q3: Proposal Amount Extraction Scope
- **Option A**: Extract ALL amounts from proposal (any table)
- **Option B**: Extract only from main coverage table
- **Option C**: Extract from both, prefer main table
- **Recommendation**: Option B (main table only, simpler)

---

## LOCKED DIRECTION (Final)

```
Pipeline: Canonical-First (Excel-Driven Scope)

Order:
  STEP 0: Load Canonical (Excel)
  STEP 1: Extract Proposal (with amounts)
  STEP 2: Match Proposal to Canonical (variants)
  STEP 3: Sanitize (after matching)
  STEP 4: Lock to SSOT (coverage_cards)

Variant Generation: STEP 0 (before matching)
Amount Extraction: STEP 1 (with proposal names)
Sanitization: STEP 3 (after matching)
SSOT Lock: STEP 4 (immutable, no updates)

Excel: INPUT contract (immutable)
SSOT: coverage_cards.jsonl (unchanged schema)
```

**ALL OTHER OPTIONS REJECTED.**

**NEXT STEP**: Create IMPLEMENTATION_TICKETS_NEXT.md with ordered refactor tasks.

---

**END OF DECISION**
