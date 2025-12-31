# STEP NEXT-31 — Constitutional Audit Summary

**Date**: 2025-12-31
**Auditor**: Claude (Pipeline Constitution Auditor)
**Status**: ✅ AUDIT COMPLETE

---

## Executive Summary

The pipeline root-cause audit has identified **6 critical structural issues** causing repeated data corruption and ad-hoc fixes:

1. **JOIN KEY DRIFT** (Critical): step4 and step5 use different scope files → evidence join failures
2. **STEP NUMBER COLLISIONS**: 6 duplicate step IDs across 13 modules → developer confusion
3. **GHOST STEP**: step2_extract_pdf exists as empty directory → misleading
4. **SSOT MUTATION**: step7_amount_extraction modifies SSOT in-place → immutability violation
5. **DEPRECATED CLUTTER**: 5 deprecated steps remain in `pipeline/` → namespace pollution
6. **NO ATOMIC REGENERATION**: Manual "just re-run step X" creates partial state

**Root Cause**: Evolutionary development without constitutional governance + deprecation without removal = structural debt.

---

## Audit Deliverables

### 1. **PIPELINE_STEP_REGISTRY.md**
Complete inventory of all 13 pipeline modules with evidence-based usage analysis.

**Key Findings**:
- 6 CORE steps (required for SSOT generation)
- 2 OPTIONAL steps (enrichment/audit)
- 5 DEPRECATED steps (execution-forbidden)
- 1 GHOST step (no code exists)

**Evidence Collection**: 196 grep references for step7_amount, 0 for step2_extract_pdf.

---

### 2. **DUPLICATE_STEP_ANALYSIS.md**
Explains why 6 step numbers have collisions and resolves conflicts.

**Answers to Mandatory Questions**:

| Question | Answer |
|----------|--------|
| Why does step2 exist twice? | step2_canonical_mapping is legitimate; step2_extract_pdf is GHOST (code deleted) |
| Why does step7 exist twice? | step7_amount_extraction is active; step7_compare is DEPRECATED (per CLAUDE.md:113) |
| Why does step8 exist twice? | Both deprecated as pipeline steps; step8_single_coverage is query tool |
| Is step2_extract_pdf same as step3_extract_text? | Cannot confirm (no code), but step3 replaced step2 during refactoring |

**Timeline Reconstruction**: Tracked evolution from initial pipeline → STEP NEXT-18 refactoring → amount extraction priority shift → current state.

---

### 3. **CANONICAL_PIPELINE.md**
Official pipeline definition with constitutional enforcement rules.

**Canonical Flow** (Tier-based):
```
Tier 0: Sources (PDFs, mapping 엑셀)
  ↓ step1_extract_scope
Tier 1: scope.csv, evidence_text/
  ↓ step2_canonical_mapping
Tier 2: scope_mapped.csv
  ↓ step1_sanitize_scope
Tier 3: scope_mapped.sanitized.csv, evidence_pack.jsonl
  ↓ step4_evidence_search, step5_build_cards
Tier 4: coverage_cards.jsonl (SSOT) ⭐
  ↓ step7_amount_extraction (optional)
Tier 4': enriched coverage_cards.jsonl
  ↓ audit
Tier 5: AMOUNT_STATUS_DASHBOARD.md
```

**Constitutional Principles**:
1. Single Pipeline: One canonical path PDF → SSOT
2. Step Numbers are Unique: No duplicates
3. SSOT is Sacred: coverage_cards.jsonl is immutable truth
4. Determinism Default: All core steps deterministic
5. Input Alignment: No join-key drift allowed

**Critical Fixes Identified**:
- **Fix #1**: step4 must use `scope_mapped.sanitized.csv` (file:732)
- **Fix #2**: step7 must write to separate enriched file (immutability)

---

### 4. **STEP_CLEANUP_PLAN.md**
Concrete remediation actions with estimated timelines.

**4 Phases**:

| Phase | Actions | Time | Priority |
|-------|---------|------|----------|
| Phase 1: Critical Fixes | Fix join-key drift, add join-rate gate | 35 min | 🔴 CRITICAL |
| Phase 2: Deprecation | Archive 5 deprecated steps, delete ghost | 32 min | 🟡 HIGH |
| Phase 3: Refactoring | SSOT immutability, content hash, atomic regeneration | 3.5-4 hr | 🟢 MEDIUM |
| Phase 4: Documentation | Update CLAUDE.md, add constitution reference | 15 min | 🟢 LOW |

**Total Estimated Time**: 4.5-5 hours

**Definition of Done**:
- ✅ Step4 uses correct scope file (no drift)
- ✅ Step5 validates join-rate >= 95%
- ✅ No duplicate step numbers in `pipeline/`
- ✅ Deprecated steps in `_deprecated/`
- ✅ CLAUDE.md references canonical pipeline

---

## Critical Questions Answered

### Q1: What is the SSOT?
**Answer**: `data/compare/{insurer}_coverage_cards.jsonl`

All other artifacts are INPUTS or DERIVATIVES. Only coverage_cards.jsonl is the single source of truth for coverage queries.

---

### Q2: Why do problems repeat?
**Answer**: **Multi-SSOT assumption + no state management**

- Step4 and Step5 use different scope files → join-key drift
- No content hash tracking → stale artifacts accepted
- No atomic regeneration → partial pipeline runs corrupt state
- Deprecation without removal → namespace pollution

---

### Q3: Is the restart-corruption pattern a "bug" or "design flaw"?
**Answer**: **Design flaw** (Constitutional Violation)

The pipeline is **stateless steps + stateful artifacts WITHOUT state management**.

- Steps assume inputs are fresh (no timestamp validation)
- Evidence_pack can be generated from old scope snapshot
- Step5 blindly joins without checking evidence_pack staleness
- Manual "re-run step X" breaks implicit assumptions

**Classification**: [B] CONTRACT VIOLATION (see Root-Cause Audit Q3)

---

### Q4: What prevents future "땜빵 루프"?
**Answer**: Constitutional enforcement + atomic regeneration

**Must-Have Safeguards**:
1. ✅ **Step-level Gate**: step5 FAIL if join_rate < 95%
2. ✅ **Content Hash Validation**: step5 rejects evidence_pack if scope hash mismatch
3. ✅ **Atomic Regeneration Rule**: Tier N change → invalidate all Tier N+1
4. ✅ **Input Alignment Lock**: step4 and step5 use identical scope file

**Not Needed** (nice-to-have):
- ❌ Insurer-specific extractors (parameterized OK)
- ❌ run_id tracking (content_hash sufficient)
- ❌ Step re-execution ban (regeneration valid if atomic)

---

## Structural Diagnosis

### Why Samsung/Meritz/Hanwha/KB Problems Emerged

| Problem | Root Cause | Evidence | Classification |
|---------|-----------|----------|----------------|
| **Samsung 1건 추출** | Step1 heuristic fails on Samsung table structure | hardening.py:70-94 | [A] 설계 결함 |
| **Meritz header 혼입** | Step1 exclude_keywords insufficient | hardening.py:156-160 | [A] 설계 결함 |
| **Hanwha evidence 0/41** | step4 uses stale scope snapshot → join-key mismatch | step4:732, step5:271 | [B] 계약 위반 |
| **KB scope corruption** | Manual edit or incomplete step1 run | (operational) | [C] 운영 실수 |
| **Restart mismatch** | No version sync between scope/pack/cards | (architectural) | [B] 계약 위반 |

**Pattern**: 4/5 problems are [A] Design Flaws or [B] Contract Violations.

**Solution**: Fix contracts FIRST (Phase 1), then fix extractors (STEP NEXT-32).

---

## Impact Assessment

### Before Constitutional Audit
```
❌ Pipeline trust: LOW (manual fixes required after every run)
❌ Restart safety: UNSAFE (join-key drift)
❌ Step clarity: CONFUSING (6 duplicate step IDs)
❌ SSOT integrity: VIOLATED (step7 mutates in-place)
❌ Deprecation: INCOMPLETE (5 steps remain in pipeline/)
```

### After Cleanup (Phase 1-4 Complete)
```
✅ Pipeline trust: HIGH (deterministic, gated)
✅ Restart safety: SAFE (content hash validation)
✅ Step clarity: CLEAR (unique step IDs, documented)
✅ SSOT integrity: PROTECTED (enrichment separate)
✅ Deprecation: CLEAN (_deprecated/ archive)
```

---

## Recommended Next Steps

### Immediate (STEP NEXT-31 Implementation)
1. Execute **Phase 1 Critical Fixes** (35 min) → deploy immediately
2. Execute **Phase 2 Deprecation** (32 min) → same PR
3. Execute **Phase 4 Documentation** (15 min) → same PR

**Total Time**: ~1.5 hours
**Expected Result**: Hanwha evidence 0/41 → 41/41 recovery; no more join-key drift

---

### Short-Term (STEP NEXT-32)
**After** Phase 1 fixes are deployed:
- Fix Samsung step1 extraction (table pattern anchors)
- Fix Meritz step1 extraction (section header removal)

**Rationale**: Extractor fixes are now safe because join-key drift is resolved.

---

### Long-Term (STEP NEXT-33+)
**After** cleanup is complete:
- Execute **Phase 3 Refactoring** (3.5-4 hr) → separate PR
- Implement pipeline orchestrator (Makefile/Airflow)
- Add unit tests for canonical steps 1-7

---

## Definition of Done (Constitutional Audit)

✅ **SSOT Declared**: `coverage_cards.jsonl` (single source of truth)

✅ **Step Contracts Defined**: PIPELINE_STEP_REGISTRY.md (table format)

✅ **Problems Explained**: DUPLICATE_STEP_ANALYSIS.md (why collisions exist)

✅ **Canonical Pipeline Documented**: CANONICAL_PIPELINE.md (official flow)

✅ **Cleanup Plan Created**: STEP_CLEANUP_PLAN.md (concrete actions)

✅ **Root Cause Identified**: Join-key drift + no state management

✅ **Confident Next Step**: Execute Phase 1 fixes → test Hanwha → deploy

---

## Closing Statement

This is not a bug-fix task. This is a constitutional audit to make the pipeline trustworthy again.

**The pipeline has been structurally diagnosed. The constitution has been written. The cleanup plan is executable.**

**Recommendation**: Proceed with STEP_CLEANUP_PLAN.md Phase 1-2-4 immediately (total ~1.5 hours), then tackle Samsung/Meritz extraction as STEP NEXT-32.

---

## Audit Files Created

1. `docs/architecture/PIPELINE_STEP_REGISTRY.md` (step inventory + evidence)
2. `docs/architecture/DUPLICATE_STEP_ANALYSIS.md` (collision explanations)
3. `docs/architecture/CANONICAL_PIPELINE.md` (official pipeline definition)
4. `docs/architecture/STEP_CLEANUP_PLAN.md` (remediation actions)
5. `docs/architecture/STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md` (this document)

**All documents are evidence-based, grep-verified, and cross-referenced.**

---

**End of Constitutional Audit**

Audited by: Claude (Pipeline Constitution Auditor)
Date: 2025-12-31
Status: ✅ COMPLETE
