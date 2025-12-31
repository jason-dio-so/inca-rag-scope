# Step Cleanup Plan

**Effective Date**: 2025-12-31
**Authority**: Pipeline Constitution Audit (STEP NEXT-31)
**Purpose**: Remediation actions to implement canonical pipeline

---

## Cleanup Matrix

| step | decision | reason | replacement | risk_if_left |
|------|----------|--------|-------------|--------------|
| **step0_scope_filter/coverage_candidate_filter.py** | DEPRECATE | Superseded by step1_sanitize_scope/run.py | step1_sanitize_scope | Confusion: two sanitization paths exist |
| **step0_scope_filter/filter_scope_mapped.py** | DEPRECATE | Superseded by step1_sanitize_scope/run.py | step1_sanitize_scope | Confusion: two sanitization paths exist |
| **step1_extract_scope** | KEEP | CORE STEP: proposal PDF → scope.csv | N/A | None (essential) |
| **step1_sanitize_scope** | KEEP + FIX | CORE STEP: INPUT contract for step5 | N/A | None (essential); currently has input alignment bug |
| **step2_canonical_mapping** | KEEP | CORE STEP: scope → canonical codes | N/A | None (essential) |
| **step2_extract_pdf/** | DELETE | Ghost directory (no code exists) | step3_extract_text | Developer confusion; misleading directory name |
| **step3_extract_text** | KEEP | CORE STEP: PDFs → evidence_text/*.page.jsonl | N/A | None (essential) |
| **step4_evidence_search** | KEEP + FIX | CORE STEP: evidence search via keywords | N/A | Critical bug: uses wrong scope file (join-key drift) |
| **step5_build_cards** | KEEP | **SSOT GENERATOR**: joins scope + evidence | N/A | None (SSOT foundation) |
| **step7_amount_extraction** | KEEP + REFACTOR | OPTIONAL enrichment (LLM-based amounts) | N/A | Mutates SSOT in-place (immutability violation) |
| **step7_compare** | DEPRECATE | Replaced by tools/audit and JSONL-only comparison | tools/audit/** | Deprecated per CLAUDE.md:113; generates stale reports |
| **step8_multi_compare** | DEPRECATE | Replaced by tools/audit aggregation | tools/audit/** | Deprecated per CLAUDE.md:114; execution forbidden |
| **step8_single_coverage** | RELOCATE | Analysis tool, not pipeline step | tools/query_coverage.py | Namespace pollution; misleading as "step8" |
| **step10_audit/** | DEPRECATE | Replaced by tools/audit/run_step_next_17b_audit.py | tools/audit/** | Deprecated per CLAUDE.md:116; outdated audit logic |

---

## Action Plan (Prioritized)

### Phase 1: Critical Fixes (Block Further Corruption)

#### Action 1.1: Fix Step4 Input Alignment 🔴 CRITICAL
**Impact**: JOIN KEY DRIFT → Evidence not_found failures (e.g., Hanwha 0/41)

**File**: `pipeline/step4_evidence_search/search_evidence.py`
**Line**: 732

**Current Code**:
```python
scope_mapped_csv = base_dir / "data" / "scope" / f"{insurer}_scope_mapped.csv"
```

**Fixed Code**:
```python
# Use same scope file as step5 (sanitized)
from core.scope_gate import resolve_scope_csv
scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")
```

**Validation**:
```bash
# After fix, re-run for all insurers
for ins in samsung meritz db kb hanwha hyundai heungkuk lotte; do
    python -m pipeline.step4_evidence_search.search_evidence --insurer $ins
    python -m pipeline.step5_build_cards.build_cards --insurer $ins
done

# Verify no join failures
jq -r '.evidence_status' data/compare/*_coverage_cards.jsonl | sort | uniq -c
# Should see "found" counts, not all "not_found"
```

**Estimated Time**: 15 minutes
**Risk if Skipped**: Continued evidence join failures on every pipeline run

---

#### Action 1.2: Add Step5 Join-Rate Gate 🟡 HIGH
**Impact**: Prevents SSOT corruption from stale evidence_pack

**File**: `pipeline/step5_build_cards/build_cards.py`
**Location**: After cards generation, before saving

**New Validation**:
```python
# Calculate join rate (scope_mapped.sanitized vs evidence_pack coverage keys)
scope_keys = set(scope_data.keys())
evidence_keys = set(evidence_data.keys())
join_rate = len(scope_keys & evidence_keys) / len(scope_keys) if scope_keys else 0

print(f"[Step 5] Join rate: {join_rate:.1%} ({len(scope_keys & evidence_keys)}/{len(scope_keys)})")

# Gate: FAIL if join_rate < 95%
if join_rate < 0.95:
    raise ValueError(
        f"Join rate too low ({join_rate:.1%}). "
        f"Evidence pack may be stale. Regenerate step4 evidence_pack."
    )
```

**Validation**:
```bash
# Test with intentionally stale evidence_pack
touch -t 202401010000 data/evidence_pack/test_evidence_pack.jsonl
python -m pipeline.step5_build_cards.build_cards --insurer test
# Should FAIL with join rate error
```

**Estimated Time**: 20 minutes
**Risk if Skipped**: Silent join failures; SSOT contains incomplete data

---

### Phase 2: Deprecation & Archive (Remove Confusion)

#### Action 2.1: Archive step0_scope_filter
```bash
mkdir -p _deprecated
git mv pipeline/step0_scope_filter _deprecated/
git commit -m "chore: deprecate step0_scope_filter (superseded by step1_sanitize_scope)"
```

**Rationale**: Two sanitization paths cause confusion; step1_sanitize_scope is canonical

**Validation**: Ensure no imports remain
```bash
grep -r "step0_scope_filter" --include="*.py" . | grep -v "_deprecated"
# Should return 0 results (except docs)
```

**Estimated Time**: 5 minutes

---

#### Action 2.2: Delete step2_extract_pdf (Ghost)
```bash
rm -rf pipeline/step2_extract_pdf/
git add -A
git commit -m "chore: delete ghost directory step2_extract_pdf (no code exists)"
```

**Rationale**: Empty directory with only `__pycache__` misleads developers

**Validation**: Verify removal
```bash
ls pipeline/step2_extract_pdf
# ls: pipeline/step2_extract_pdf: No such file or directory
```

**Estimated Time**: 2 minutes

---

#### Action 2.3: Archive step7_compare
```bash
git mv pipeline/step7_compare _deprecated/
git commit -m "chore: deprecate step7_compare (replaced by tools/audit)"
```

**Rationale**: CLAUDE.md:113 explicitly marks as deprecated ("실행 금지")

**Validation**: Check for remaining usage
```bash
grep -r "step7_compare" --include="*.py" . | grep -v "_deprecated" | grep -v "test"
# Should return 0 active code references
```

**Estimated Time**: 5 minutes

---

#### Action 2.4: Archive step8_multi_compare
```bash
git mv pipeline/step8_multi_compare _deprecated/
git commit -m "chore: deprecate step8_multi_compare (replaced by tools/audit)"
```

**Rationale**: CLAUDE.md:114 marks as deprecated

**Validation**: Same as 2.3

**Estimated Time**: 5 minutes

---

#### Action 2.5: Archive step10_audit
```bash
git mv pipeline/step10_audit _deprecated/
git commit -m "chore: deprecate step10_audit (replaced by tools/audit/run_step_next_17b_audit.py)"
```

**Rationale**: CLAUDE.md:116 marks as deprecated

**Validation**: Ensure tools/audit/** is active replacement
```bash
ls tools/audit/run_step_next_17b_audit.py
# Should exist
```

**Estimated Time**: 5 minutes

---

#### Action 2.6: Relocate step8_single_coverage to Tools
```bash
mkdir -p tools/
git mv pipeline/step8_single_coverage/extract_single_coverage.py tools/query_coverage.py
git rm -rf pipeline/step8_single_coverage/
git commit -m "refactor: move step8_single_coverage to tools/query_coverage.py (not pipeline step)"
```

**Rationale**: It's a query tool, not a pipeline step

**Update Imports** (if any):
```bash
# Find and update imports
grep -r "step8_single_coverage" --include="*.py" . | grep -v "_deprecated"
# Update to: from tools import query_coverage
```

**Estimated Time**: 10 minutes

---

### Phase 3: Refactoring (Long-Term Stability)

#### Action 3.1: Fix Step7 SSOT Mutation (Immutability)
**Impact**: Prevents SSOT corruption if amount extraction fails

**File**: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py`

**Current Behavior**: Modifies `coverage_cards.jsonl` in-place

**Option A: Separate Enriched File** (Recommended)
```python
# Write to separate file
output_cards_jsonl = base_dir / "data" / "compare" / f"{insurer}_coverage_cards_enriched.jsonl"

# Downstream tools/audit should check:
# 1. If *_enriched.jsonl exists, use it (has amounts)
# 2. Else use *_coverage_cards.jsonl (base SSOT)
```

**Option B: Atomic Update with Backup**
```python
import shutil
backup = shutil.copy(cards_jsonl, f"{cards_jsonl}.backup")
try:
    enrich_amounts_in_place(cards_jsonl)
    os.remove(f"{cards_jsonl}.backup")
except Exception as e:
    shutil.move(f"{cards_jsonl}.backup", cards_jsonl)
    raise
```

**Recommendation**: Option A (separation) is cleaner and follows SSOT immutability

**Estimated Time**: 1-2 hours (includes testing)
**Risk if Skipped**: Amount extraction errors corrupt SSOT; manual recovery needed

---

#### Action 3.2: Implement Content Hash Validation
**Impact**: Prevents join-key drift at runtime

**Files**:
- `pipeline/step4_evidence_search/search_evidence.py` (generate hash)
- `pipeline/step5_build_cards/build_cards.py` (validate hash)

**Step4 Change** (Embed hash in evidence_pack metadata):
```python
import hashlib

# After creating evidence_pack items
scope_file_hash = hashlib.sha256(open(scope_mapped_csv, 'rb').read()).hexdigest()

# Write metadata header to evidence_pack.jsonl
metadata = {
    "_metadata": True,
    "scope_file_path": str(scope_mapped_csv),
    "scope_file_hash": scope_file_hash,
    "generated_at": datetime.now().isoformat()
}

with open(output_pack_jsonl, 'w', encoding='utf-8') as f:
    f.write(json.dumps(metadata, ensure_ascii=False) + '\n')
    for item in evidence_pack:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
```

**Step5 Change** (Validate hash before join):
```python
# Read metadata header
with open(evidence_pack_jsonl, 'r', encoding='utf-8') as f:
    first_line = f.readline()
    metadata = json.loads(first_line)

    if metadata.get("_metadata"):
        # Validate scope hash
        current_hash = hashlib.sha256(open(scope_mapped_csv, 'rb').read()).hexdigest()
        if metadata["scope_file_hash"] != current_hash:
            raise ValueError(
                f"Evidence pack stale: scope file changed since pack generation.\n"
                f"Regenerate step4 evidence_pack for {insurer}"
            )
```

**Estimated Time**: 2 hours (includes testing)
**Risk if Skipped**: Restart-induced corruption not caught until manual audit

---

#### Action 3.3: Create Atomic Regeneration Script
**Impact**: Enforces dependency tracking; prevents partial pipeline runs

**File**: `tools/rebuild_insurer.sh`

```bash
#!/bin/bash
set -euo pipefail

INSURER=$1

if [[ -z "$INSURER" ]]; then
    echo "Usage: $0 <insurer>"
    exit 1
fi

echo "[Rebuild] Starting atomic regeneration for $INSURER"

# Wipe downstream artifacts (Tier 2+)
echo "[Rebuild] Removing stale artifacts..."
rm -f data/scope/${INSURER}_scope_mapped.csv
rm -f data/scope/${INSURER}_scope_mapped.sanitized.csv
rm -f data/scope/${INSURER}_scope_filtered_out.jsonl
rm -f data/evidence_pack/${INSURER}_evidence_pack.jsonl
rm -f data/compare/${INSURER}_coverage_cards.jsonl

# Re-run core pipeline
echo "[Rebuild] Running core pipeline..."
python -m pipeline.step1_extract_scope.run --insurer $INSURER
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer $INSURER
python -m pipeline.step1_sanitize_scope.run --insurer $INSURER
python -m pipeline.step3_extract_text.extract_pdf_text --insurer $INSURER
python -m pipeline.step4_evidence_search.search_evidence --insurer $INSURER
python -m pipeline.step5_build_cards.build_cards --insurer $INSURER

echo "[Rebuild] ✓ SSOT regenerated: data/compare/${INSURER}_coverage_cards.jsonl"
echo "[Rebuild] Run step7 (amount extraction) manually if needed."
```

**Usage**:
```bash
chmod +x tools/rebuild_insurer.sh
./tools/rebuild_insurer.sh samsung
```

**Estimated Time**: 30 minutes
**Risk if Skipped**: Manual "just re-run step X" commands create partial/inconsistent state

---

### Phase 4: Documentation Updates

#### Action 4.1: Update CLAUDE.md with Canonical Pipeline
**File**: `CLAUDE.md`

**Section to Replace** (lines 102-116):
```markdown
## Pipeline Architecture (Active Steps)

**Canonical Pipeline** (See docs/architecture/CANONICAL_PIPELINE.md for full flow):
1. **step1_extract_scope**: 가입설계서 PDF → scope.csv
2. **step2_canonical_mapping**: scope.csv + mapping 엑셀 → scope_mapped.csv
3. **step1_sanitize_scope**: scope_mapped.csv → scope_mapped.sanitized.csv (INPUT contract)
4. **step3_extract_text**: evidence PDFs → evidence_text/**/*.page.jsonl
5. **step4_evidence_search**: evidence_text + sanitized scope → evidence_pack.jsonl
6. **step5_build_cards**: sanitized scope + evidence_pack → coverage_cards.jsonl (SSOT)
7. **step7_amount_extraction** (optional): coverage_cards + PDFs → amount enrichment
8. **tools/audit/run_step_next_17b_audit.py**: SSOT → AMOUNT_STATUS_DASHBOARD.md

**Deprecated Steps** (archived to _deprecated/):
- step0_scope_filter (replaced by step1_sanitize_scope)
- step2_extract_pdf (ghost; deleted)
- step7_compare (replaced by tools/audit)
- step8_multi_compare (replaced by tools/audit)
- step10_audit (replaced by tools/audit)
```

**Estimated Time**: 10 minutes

---

#### Action 4.2: Add Pipeline Constitution Reference
**File**: `CLAUDE.md` (after "Session Start Protocol")

```markdown
## Pipeline Constitution (Mandatory Reading)

Before modifying pipeline:
1. Read `docs/architecture/CANONICAL_PIPELINE.md` (official pipeline flow)
2. Check `docs/architecture/PIPELINE_STEP_REGISTRY.md` (step inventory)
3. Follow `docs/architecture/STEP_CLEANUP_PLAN.md` (refactoring rules)

**Hard Rules**:
- SSOT is `data/compare/*_coverage_cards.jsonl` (immutable except step7 enrichment)
- Step4 and Step5 MUST use identical scope file (`scope_mapped.sanitized.csv`)
- Deprecated steps in `_deprecated/` are execution-forbidden
- Step numbers MUST be unique (no duplicates)
```

**Estimated Time**: 5 minutes

---

## Validation Checklist (Post-Cleanup)

After completing all actions, verify:

### Critical Fixes
- [ ] Step4 uses `scope_mapped.sanitized.csv` (not `scope_mapped.csv`)
- [ ] Step5 has join-rate gate (FAIL if < 95%)
- [ ] No evidence join failures (test with Hanwha)

### Deprecation
- [ ] `_deprecated/` directory contains: step0, step7_compare, step8_multi_compare, step10_audit
- [ ] `pipeline/step2_extract_pdf/` deleted
- [ ] `tools/query_coverage.py` exists (relocated from step8_single_coverage)
- [ ] No imports to deprecated steps in active code

### Documentation
- [ ] CLAUDE.md updated with canonical pipeline
- [ ] Pipeline constitution reference added to CLAUDE.md
- [ ] All architecture docs (`PIPELINE_STEP_REGISTRY.md`, `DUPLICATE_STEP_ANALYSIS.md`, `CANONICAL_PIPELINE.md`, this file) exist

### Regression Testing
- [ ] Re-run full pipeline for one insurer (e.g., `samsung`)
- [ ] Verify SSOT generated: `data/compare/samsung_coverage_cards.jsonl`
- [ ] Check join rate: `jq -r '.evidence_status' data/compare/samsung_coverage_cards.jsonl | sort | uniq -c`
- [ ] No STOP failures in steps 1-5

---

## Execution Timeline

| Phase | Actions | Estimated Time | Risk Priority |
|-------|---------|----------------|---------------|
| **Phase 1: Critical Fixes** | 1.1, 1.2 | 35 minutes | 🔴 CRITICAL (blocking) |
| **Phase 2: Deprecation** | 2.1-2.6 | 32 minutes | 🟡 HIGH (confusion risk) |
| **Phase 3: Refactoring** | 3.1-3.3 | 3.5-4 hours | 🟢 MEDIUM (stability) |
| **Phase 4: Documentation** | 4.1-4.2 | 15 minutes | 🟢 LOW (reference) |
| **Total** | All actions | ~4.5-5 hours | — |

**Recommended Order**:
1. Phase 1 (fix join-key drift) → immediate deployment
2. Phase 2 (archive deprecated) → same PR
3. Phase 4 (update docs) → same PR
4. Phase 3 (refactoring) → separate PR (more invasive)

---

## Success Criteria (Definition of Done)

✅ **Phase 1 Complete** when:
- Step4 uses correct scope file (no join-key drift)
- Step5 validates join-rate (prevents stale evidence_pack)
- Hanwha evidence_status shows `found` (not `not_found`)

✅ **Phase 2 Complete** when:
- No duplicate step numbers exist in `pipeline/`
- Deprecated steps archived to `_deprecated/`
- Ghost directory `step2_extract_pdf` deleted

✅ **Phase 3 Complete** when:
- Step7 writes to separate enriched file (SSOT immutability)
- Content hash validation prevents stale joins at runtime
- Atomic regeneration script exists and tested

✅ **Phase 4 Complete** when:
- CLAUDE.md references canonical pipeline
- All architecture docs committed to repo
- New developers can onboard from docs alone

---

## Risk Mitigation

### Backup Before Cleanup
```bash
# Create snapshot before Phase 2-3 changes
tar -czf _backup_pre_cleanup_$(date +%Y%m%d).tgz \
    pipeline/ data/scope/ data/compare/ data/evidence_pack/
```

### Rollback Plan
```bash
# If cleanup breaks pipeline
git revert <commit-hash>  # Revert deprecation commits
tar -xzf _backup_pre_cleanup_*.tgz  # Restore artifacts if needed
```

### Testing Protocol
```bash
# Test on single insurer before full deployment
./tools/rebuild_insurer.sh samsung

# If successful, batch-run all insurers
for ins in samsung meritz db kb hanwha hyundai heungkuk lotte; do
    ./tools/rebuild_insurer.sh $ins
done
```

---

## Next Steps (Post-Cleanup)

After STEP NEXT-31 cleanup is complete:

1. **STEP NEXT-32**: Fix Samsung/Meritz step1 extraction (now safe, no join-key drift)
2. **STEP NEXT-33**: Implement pipeline orchestrator (Makefile or Airflow)
3. **STEP NEXT-34**: Add unit tests for each canonical step

**Note**: Do NOT attempt Samsung/Meritz extractor fixes until Phase 1 (join-key alignment) is complete. Fixing extraction without fixing joins will still fail.

---

## Appendix: File Change Summary

### Files to Modify
- `pipeline/step4_evidence_search/search_evidence.py` (line 732: fix input file)
- `pipeline/step5_build_cards/build_cards.py` (add join-rate gate)
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` (separate enriched output)
- `CLAUDE.md` (update pipeline architecture section)

### Files/Directories to Delete
- `pipeline/step2_extract_pdf/` (ghost directory)

### Files/Directories to Move
- `pipeline/step0_scope_filter/` → `_deprecated/step0_scope_filter/`
- `pipeline/step7_compare/` → `_deprecated/step7_compare/`
- `pipeline/step8_multi_compare/` → `_deprecated/step8_multi_compare/`
- `pipeline/step10_audit/` → `_deprecated/step10_audit/`
- `pipeline/step8_single_coverage/extract_single_coverage.py` → `tools/query_coverage.py`

### Files to Create
- `tools/rebuild_insurer.sh` (atomic regeneration script)
- `docs/architecture/PIPELINE_STEP_REGISTRY.md` (this audit created it)
- `docs/architecture/DUPLICATE_STEP_ANALYSIS.md` (this audit created it)
- `docs/architecture/CANONICAL_PIPELINE.md` (this audit created it)
- `docs/architecture/STEP_CLEANUP_PLAN.md` (this document)

---

**End of Step Cleanup Plan**
