# IMPLEMENTATION TICKETS (Pipeline Realignment)

**Purpose**: Ordered, concrete tickets for canonical-first pipeline refactor.

**Based on**: PIPELINE_REALIGNMENT_DECISION.md

**Execution Order**: MUST be done sequentially (no parallelization until Phase 2).

---

## PHASE 1: POC (Hanwha Only)

### Ticket 1.1: Create STEP 0 — Canonical Loader
**Scope**: Load Excel, generate search variants

**Files to Create**:
- `pipeline/step0_canonical_loader/__init__.py`
- `pipeline/step0_canonical_loader/load_canonical.py`

**Logic**:
```python
def load_canonical_scope(insurer: str, excel_path: Path) -> List[CanonicalCoverage]:
    """
    Load canonical coverage definitions from Excel.

    Returns:
        List[CanonicalCoverage]:
            - coverage_code (str)
            - coverage_name_canonical (str)
            - insurer_aliases (List[str], from Excel "담보명(가입설계서)" column)
            - search_variants (List[str], generated)
    """
    # 1. Load Excel (use openpyxl, reuse logic from step2_canonical_mapping)
    # 2. Filter by insurer (if Excel has ins_cd column)
    # 3. Generate search variants:
    #    - Exact: coverage_name_canonical
    #    - Normalized: remove whitespace, special chars
    #    - Parentheses-stripped: remove (...) suffix
    #    - Prefix-stripped: remove "일반", "고액", "통합" prefix
    # 4. Return dataclass list

def save_canonical_scope_csv(coverages: List[CanonicalCoverage], output_path: Path):
    """
    Save to data/canonical/{insurer}_canonical_scope.csv

    Columns:
        - coverage_code
        - coverage_name_canonical
        - insurer_aliases (JSON array string)
        - search_variants (JSON array string)
    """
```

**Output**: `data/canonical/hanwha_canonical_scope.csv`

**DoD**:
- [ ] CSV created with 4 columns
- [ ] search_variants includes: exact, normalized, parentheses-stripped, prefix-stripped
- [ ] Hanwha coverage count matches Excel (e.g., 30+ rows)
- [ ] No code generation of Excel content (read-only)

**Verification**:
```bash
python -m pipeline.step0_canonical_loader.load_canonical --insurer hanwha
head -5 data/canonical/hanwha_canonical_scope.csv
```

**Regression Risks**: NONE (new code, no dependencies)

---

### Ticket 1.2: Create STEP 1 — Proposal Extractor (with Amounts)
**Scope**: Extract (coverage_name, amount) pairs from proposal PDF

**Files to Create**:
- `pipeline/step1_proposal_extractor/__init__.py`
- `pipeline/step1_proposal_extractor/extract_proposal.py`

**Logic**:
```python
def extract_proposal_coverages(pdf_path: Path) -> List[ProposalCoverage]:
    """
    Extract coverage names AND amounts from proposal PDF.

    Strategy:
        - Parse main coverage table (has "담보명" + "가입금액" columns)
        - Extract (coverage_name_raw, amount_text) from SAME row
        - Avoid parsing separate tables (reduces name mismatch)

    Returns:
        List[ProposalCoverage]:
            - proposal_name_raw (str)
            - source_page (int)
            - proposal_amount (Optional[str], may be null if not in table)
    """
    # Reuse logic from:
    #   - step1_extract_scope/run.py (table extraction)
    #   - step7_amount_extraction (amount pattern recognition)
    # Merge: extract name + amount in SINGLE pass

def save_proposal_csv(coverages: List[ProposalCoverage], output_path: Path):
    """
    Save to data/proposal/{insurer}_proposal_raw.csv

    Columns:
        - proposal_name_raw
        - source_page
        - proposal_amount (nullable)
    """
```

**Output**: `data/proposal/hanwha_proposal_raw.csv`

**DoD**:
- [ ] CSV created with 3 columns
- [ ] Amount extraction rate ≥ 80% (proposal_amount not null)
- [ ] Coverage count ≥ 20 (Hanwha has ~23 coverages)
- [ ] No LLM usage
- [ ] Unit test: extract_amount_from_line() handles "1,000만원", "3천만원", etc.

**Verification**:
```bash
python -m pipeline.step1_proposal_extractor.extract_proposal --insurer hanwha
head -10 data/proposal/hanwha_proposal_raw.csv
# Check: proposal_amount column has values (not all null)
```

**Regression Risks**: LOW (new code, reuses existing patterns)

---

### Ticket 1.3: Create STEP 2 — Proposal Matcher (Variant-Based)
**Scope**: Match proposal names to canonical using search_variants

**Files to Create**:
- `pipeline/step2_proposal_matcher/__init__.py`
- `pipeline/step2_proposal_matcher/match_to_canonical.py`

**Logic**:
```python
def match_proposal_to_canonical(
    canonical_csv: Path,
    proposal_csv: Path
) -> List[ScopeMatch]:
    """
    Match proposal coverage names to canonical coverage_code.

    Matching priority:
        1. Exact match (proposal_name_raw == coverage_name_canonical)
        2. Alias match (proposal_name_raw in insurer_aliases)
        3. Variant match (normalized proposal_name in search_variants)
        4. Unmatched (no match found)

    Returns:
        List[ScopeMatch]:
            - coverage_code (Optional[str], null if unmatched)
            - coverage_name_canonical (Optional[str])
            - proposal_name_raw (str)
            - proposal_amount (Optional[str])
            - match_type (exact | alias | variant | unmatched)
            - match_confidence (0.0-1.0)
    """
    # 1. Load canonical scope (with search_variants)
    # 2. Build variant index: {variant_string: coverage_code}
    # 3. Load proposal CSV
    # 4. For each proposal row:
    #    a. Normalize proposal_name_raw
    #    b. Lookup in variant index
    #    c. Record match result
    # 5. Return matched scope

def save_scope_matched_csv(matches: List[ScopeMatch], output_path: Path):
    """
    Save to data/scope/{insurer}_scope_matched.csv

    Columns:
        - coverage_code (nullable)
        - coverage_name_canonical (nullable)
        - proposal_name_raw
        - proposal_amount (nullable)
        - match_type
        - match_confidence
    """
```

**Output**: `data/scope/hanwha_scope_matched.csv`

**DoD**:
- [ ] CSV created with 6 columns
- [ ] Match rate ≥ 90% (coverage_code not null)
- [ ] Hanwha: "유사암(8대) 진단비" matched to A4210_2 (variant match)
- [ ] No fuzzy matching (exact/alias/variant only)
- [ ] Unit test: variant normalization matches STEP 0 logic

**Verification**:
```bash
python -m pipeline.step2_proposal_matcher.match_to_canonical --insurer hanwha
grep "유사암" data/scope/hanwha_scope_matched.csv
# Expected: coverage_code=A4210_2, match_type=variant or alias
```

**Regression Risks**: LOW (new code, isolated logic)

---

### Ticket 1.4: Create STEP 3 — Sanitize Matched Scope
**Scope**: Filter non-coverages AFTER matching

**Files to Create**:
- `pipeline/step3_sanitize/__init__.py`
- `pipeline/step3_sanitize/sanitize_matched.py`

**Logic**:
```python
def sanitize_matched_scope(matched_csv: Path) -> List[ScopeFinal]:
    """
    Remove non-coverage entries from matched scope.

    DROP rules (same as current step1_sanitize_scope):
        - Condition sentences (진단확정된 경우, 인 경우, 시, etc.)
        - Administrative items (납입면제, 대상담보)
        - UNMATCHED rows (coverage_code is null)

    KEEP rules:
        - ALL matched rows (coverage_code is not null)
        - Even if name looks like condition sentence (trust match result)

    Returns:
        List[ScopeFinal]: Filtered matched scope
    """
    # Reuse DROP_PATTERNS from step1_sanitize_scope/run.py
    # Add: DROP if coverage_code is null (unmatched)

def save_scope_final_csv(scope: List[ScopeFinal], output_path: Path):
    """
    Save to data/scope/{insurer}_scope_final.csv

    Columns: Same as scope_matched.csv, filtered
    """
```

**Output**: `data/scope/hanwha_scope_final.csv`

**DoD**:
- [ ] CSV created (filtered from scope_matched.csv)
- [ ] All rows have coverage_code (no nulls)
- [ ] No condition sentences in proposal_name_raw
- [ ] Coverage count ≥ 20 (Hanwha target)

**Verification**:
```bash
python -m pipeline.step3_sanitize.sanitize_matched --insurer hanwha
awk -F, '$1 == ""' data/scope/hanwha_scope_final.csv | wc -l
# Expected: 0 (no empty coverage_code)
```

**Regression Risks**: LOW (reuses existing DROP_PATTERNS)

---

### Ticket 1.5: Modify STEP 4 — Build Coverage Cards (Use New Inputs)
**Scope**: Update build_cards.py to read from scope_final.csv

**Files to Modify**:
- `pipeline/step5_build_cards/build_cards.py`

**Changes**:
```python
# OLD (line 271):
scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")
# Priority: sanitized → mapped → original

# NEW:
scope_final_csv = base_dir / "data" / "scope" / f"{insurer}_scope_final.csv"
# Direct path, no fallback (new pipeline only)

# OLD (line 154-167): Read scope_mapped.csv columns
# coverage_name_raw, coverage_code, mapping_status

# NEW: Read scope_final.csv columns
# coverage_code, coverage_name_canonical, proposal_name_raw, proposal_amount, match_type

# Update CoverageCard constructor (line 230-241):
# - coverage_name_raw → proposal_name_raw
# - Add proposal_amount field
# - mapping_status → match_type
```

**Output**: `data/compare/hanwha_coverage_cards.jsonl` (SSOT)

**DoD**:
- [ ] coverage_cards.jsonl schema UNCHANGED (for API contract)
  - Internal field names may change, but JSON keys preserved
- [ ] amount field populated from proposal_amount (if not null)
  - status: CONFIRMED if proposal_amount exists, else UNCONFIRMED
- [ ] Coverage count matches scope_final.csv
- [ ] Existing tests pass (step5 tests)

**Verification**:
```bash
python -m pipeline.step5_build_cards.build_cards --insurer hanwha
jq -c 'select(.coverage_code == "A4210_2")' data/compare/hanwha_coverage_cards.jsonl
# Expected: amount.status = CONFIRMED, amount.value_text = "N만원"
```

**Regression Risks**: MEDIUM (modifies SSOT generation, must preserve schema)

---

### Ticket 1.6: Validate POC — Hanwha KPI Check
**Scope**: Measure improvement vs baseline

**Verification Script**:
```bash
# Baseline (current pipeline)
grep '"status": "CONFIRMED"' data/compare/hanwha_coverage_cards.jsonl.backup | wc -l
# Expected: 4 (17.4% of 23)

# New pipeline
python -m pipeline.step0_canonical_loader.load_canonical --insurer hanwha
python -m pipeline.step1_proposal_extractor.extract_proposal --insurer hanwha
python -m pipeline.step2_proposal_matcher.match_to_canonical --insurer hanwha
python -m pipeline.step3_sanitize.sanitize_matched --insurer hanwha
python -m pipeline.step5_build_cards.build_cards --insurer hanwha

grep '"status": "CONFIRMED"' data/compare/hanwha_coverage_cards.jsonl | wc -l
# Target: ≥ 21 (90%+ of 23)
```

**DoD**:
- [ ] Hanwha CONFIRMED ≥ 90% (was 17.4%)
- [ ] No coverage loss (total coverages ≥ 23)
- [ ] SSOT schema unchanged (API tests pass)

**Regression Risks**: NONE (validation only)

---

## PHASE 2: Validate (Heungkuk + Regression Check)

### Ticket 2.1: Apply POC to Heungkuk
**Scope**: Run STEP 0-4 for Heungkuk

**Commands**:
```bash
python -m pipeline.step0_canonical_loader.load_canonical --insurer heungkuk
python -m pipeline.step1_proposal_extractor.extract_proposal --insurer heungkuk
python -m pipeline.step2_proposal_matcher.match_to_canonical --insurer heungkuk
python -m pipeline.step3_sanitize.sanitize_matched --insurer heungkuk
python -m pipeline.step5_build_cards.build_cards --insurer heungkuk
```

**DoD**:
- [ ] Heungkuk CONFIRMED ≥ 80% (was 0%)
- [ ] Coverage count ≥ 30 (Heungkuk has ~30-36 coverages)
- [ ] match_type distribution: variant matches ≥ 20% (proves variant logic works)

**Verification**:
```bash
grep '"status": "CONFIRMED"' data/compare/heungkuk_coverage_cards.jsonl | wc -l
# Target: ≥ 24 (80% of 30)
```

**Regression Risks**: LOW (same logic as Hanwha POC)

---

### Ticket 2.2: Regression Check — Samsung/DB/Meritz/Lotte/Hyundai/KB
**Scope**: Ensure NO regression on high-performing insurers

**Commands**:
```bash
for insurer in samsung db meritz lotte hyundai kb; do
  echo "Processing $insurer..."
  python -m pipeline.step0_canonical_loader.load_canonical --insurer $insurer
  python -m pipeline.step1_proposal_extractor.extract_proposal --insurer $insurer
  python -m pipeline.step2_proposal_matcher.match_to_canonical --insurer $insurer
  python -m pipeline.step3_sanitize.sanitize_matched --insurer $insurer
  python -m pipeline.step5_build_cards.build_cards --insurer $insurer
done
```

**DoD**:
- [ ] Samsung: CONFIRMED ≥ 95% (was 100%, allow 5% margin)
- [ ] DB: CONFIRMED ≥ 95% (was 100%)
- [ ] Meritz: CONFIRMED ≥ 90% (was 97.1%)
- [ ] Lotte: CONFIRMED ≥ 95% (was 100%)
- [ ] Hyundai: CONFIRMED ≥ 90% (was 96.0%)
- [ ] KB: CONFIRMED ≥ 85% (was 88.0%)

**Verification**:
```bash
for insurer in samsung db meritz lotte hyundai kb; do
  total=$(jq -c 'select(.mapping_status == "matched")' data/compare/${insurer}_coverage_cards.jsonl | wc -l)
  confirmed=$(jq -c 'select(.amount.status == "CONFIRMED")' data/compare/${insurer}_coverage_cards.jsonl | wc -l)
  pct=$(echo "scale=1; $confirmed * 100 / $total" | bc)
  echo "$insurer: $confirmed/$total ($pct%)"
done
```

**Regression Risks**: MEDIUM (logic change may affect edge cases)

---

### Ticket 2.3: Deprecate Legacy Steps (Git Rename + Warnings)
**Scope**: Mark old steps as DEPRECATED, prevent accidental usage

**Files to Rename**:
```bash
git mv pipeline/step1_extract_scope pipeline/DEPRECATED_step1_extract_scope
git mv pipeline/step2_canonical_mapping pipeline/DEPRECATED_step2_canonical_mapping
git mv pipeline/step1_sanitize_scope pipeline/DEPRECATED_step1_sanitize_scope
git mv pipeline/step7_amount_extraction pipeline/DEPRECATED_step7_amount_extraction
```

**Add Fail-Fast to Deprecated Files**:
```python
# In each DEPRECATED step's run.py or main():
raise RuntimeError(
    "This step is DEPRECATED. Use new pipeline: "
    "step0_canonical_loader → step1_proposal_extractor → step2_proposal_matcher → step3_sanitize → step5_build_cards"
)
```

**DoD**:
- [ ] Directories renamed with DEPRECATED prefix
- [ ] Fail-fast RuntimeError added to entry points
- [ ] Git history preserved (use `git mv`)
- [ ] Documentation updated (CLAUDE.md, STATUS.md)

**Regression Risks**: LOW (only renames, no logic change)

---

## PHASE 3: Rollout (All Insurers + Lock)

### Ticket 3.1: Batch Execution — All 8 Insurers
**Scope**: Run full pipeline for all insurers

**Script**:
```bash
#!/bin/bash
# tools/realignment/run_all_insurers.sh

INSURERS="samsung db meritz lotte hyundai kb hanwha heungkuk"

for insurer in $INSURERS; do
  echo "===== Processing $insurer ====="
  python -m pipeline.step0_canonical_loader.load_canonical --insurer $insurer || exit 1
  python -m pipeline.step1_proposal_extractor.extract_proposal --insurer $insurer || exit 1
  python -m pipeline.step2_proposal_matcher.match_to_canonical --insurer $insurer || exit 1
  python -m pipeline.step3_sanitize.sanitize_matched --insurer $insurer || exit 1
  python -m pipeline.step5_build_cards.build_cards --insurer $insurer || exit 1
done

echo "✓ All insurers processed"
```

**DoD**:
- [ ] All 8 insurers processed without errors
- [ ] All coverage_cards.jsonl files updated
- [ ] No test failures (pytest -q)

**Verification**:
```bash
bash tools/realignment/run_all_insurers.sh
pytest -q
```

**Regression Risks**: LOW (tested in Phase 2)

---

### Ticket 3.2: Regenerate Audit SSOT
**Scope**: Update AMOUNT_STATUS_DASHBOARD.md with new KPIs

**Commands**:
```bash
python -m tools.audit.run_step_next_17b_audit
```

**DoD**:
- [ ] docs/audit/AMOUNT_STATUS_DASHBOARD.md updated
- [ ] Overall KPI ≥ 95% (was 99.4% excluding outliers)
- [ ] Hanwha/Heungkuk no longer listed as "structural outliers"

**Verification**:
```bash
grep "KPI Status" docs/audit/AMOUNT_STATUS_DASHBOARD.md
# Expected: PASS (≥90% target)
```

**Regression Risks**: NONE (audit only)

---

### Ticket 3.3: Lock Realignment (Git Tag + Freeze)
**Scope**: Create immutable checkpoint

**Commands**:
```bash
git add .
git commit -m "feat(realignment): complete canonical-first pipeline (POC → rollout)

- STEP 0: Canonical loader (Excel SSOT)
- STEP 1: Proposal extractor (with amounts)
- STEP 2: Variant-based matcher (exact/alias/variant)
- STEP 3: Post-match sanitization
- STEP 4: SSOT lock (coverage_cards)

Results:
- Hanwha: 17.4% → 90%+ CONFIRMED
- Heungkuk: 0% → 80%+ CONFIRMED
- Overall: 99.4% → 95%+ (no outliers)

BREAKING: Old pipeline DEPRECATED (step1_extract_scope, step2_canonical_mapping, step1_sanitize_scope, step7_amount_extraction)
"

git tag -a realignment-v2-complete -m "Pipeline realignment complete (canonical-first)"
git push origin HEAD --tags
```

**DoD**:
- [ ] Commit created
- [ ] Tag created: `realignment-v2-complete`
- [ ] Pushed to remote

**Regression Risks**: NONE (git operation only)

---

### Ticket 3.4: Update Documentation (CLAUDE.md + STATUS.md)
**Scope**: Reflect new pipeline in project docs

**CLAUDE.md Changes**:
```markdown
## Pipeline Architecture (Active Steps)

**Current Pipeline** (Canonical-First, v2):
1. **step0_canonical_loader**: Excel → canonical scope (with search variants)
2. **step1_proposal_extractor**: Proposal PDF → (coverage_name, amount) pairs
3. **step2_proposal_matcher**: Proposal + Canonical → matched scope (variant-based)
4. **step3_sanitize**: Matched scope → sanitized scope (post-match filter)
5. **step5_build_cards**: Sanitized scope → coverage_cards.jsonl (SSOT)

**DEPRECATED Pipeline** (Proposal-First, v1):
- ~~step1_extract_scope~~ (replaced by step1_proposal_extractor)
- ~~step2_canonical_mapping~~ (replaced by step2_proposal_matcher)
- ~~step1_sanitize_scope~~ (replaced by step3_sanitize, reordered)
- ~~step7_amount_extraction~~ (merged into step1_proposal_extractor)
```

**STATUS.md Changes**:
```markdown
**최종 업데이트**: 2025-12-30
**현재 상태**: 🎉 PIPELINE REALIGNMENT COMPLETE (Canonical-First v2)

### STEP REALIGNMENT-V2 — Canonical-First Pipeline (Hanwha/Heungkuk Recovery)

**목표**: Structural fix for proposal name ≠ canonical name mismatch

**주요 성과**:
- ✅ Canonical-first pipeline (Excel SSOT → Proposal match)
- ✅ Variant generation (exact, normalized, prefix-stripped, parentheses-stripped)
- ✅ Hanwha: 17.4% → 90%+ CONFIRMED
- ✅ Heungkuk: 0% → 80%+ CONFIRMED
- ✅ Overall KPI: 99.4% → 95%+ (structural outliers resolved)
```

**DoD**:
- [ ] CLAUDE.md updated (Pipeline Architecture section)
- [ ] STATUS.md updated (add STEP REALIGNMENT-V2 entry)
- [ ] README.md updated (if applicable)

**Regression Risks**: NONE (documentation only)

---

## Summary (Execution Checklist)

### Phase 1: POC (Hanwha) — 6 Tickets
- [ ] 1.1: Create STEP 0 (canonical loader)
- [ ] 1.2: Create STEP 1 (proposal extractor with amounts)
- [ ] 1.3: Create STEP 2 (variant-based matcher)
- [ ] 1.4: Create STEP 3 (sanitize after match)
- [ ] 1.5: Modify STEP 4 (build_cards.py)
- [ ] 1.6: Validate POC (Hanwha KPI ≥ 90%)

### Phase 2: Validate (Heungkuk + Regression) — 3 Tickets
- [ ] 2.1: Apply to Heungkuk (KPI ≥ 80%)
- [ ] 2.2: Regression check (6 insurers, no loss)
- [ ] 2.3: Deprecate legacy steps (git mv + fail-fast)

### Phase 3: Rollout (All + Lock) — 4 Tickets
- [ ] 3.1: Batch execution (all 8 insurers)
- [ ] 3.2: Regenerate audit SSOT
- [ ] 3.3: Git tag + freeze
- [ ] 3.4: Update documentation

**Total**: 13 tickets, sequential execution, ~3-5 days estimate

---

## Open Issues (Deferred to Post-Rollout)

### Issue 1: Semantic Substitutions (e.g., "4대" → "8대")
- **Current**: Not handled (variant generation does basic prefix/suffix/parentheses)
- **Impact**: May need manual Excel aliases for some edge cases
- **Decision**: Defer to post-rollout analysis (check if KPI ≥ 95% without this)

### Issue 2: Fuzzy Matching
- **Current**: Not implemented (exact/alias/variant only)
- **Impact**: May miss some typos or OCR errors
- **Decision**: Defer (exact/variant should achieve 90%+ KPI)

### Issue 3: Multi-Table Proposal Parsing
- **Current**: STEP 1 extracts from main coverage table only
- **Impact**: If amount is in separate table, may be missed
- **Decision**: Defer (validate proposal_amount extraction rate ≥ 80%)

---

**END OF TICKETS**
