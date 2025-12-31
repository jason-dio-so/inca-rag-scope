# Architecture Documentation Index

**Last Updated**: 2025-12-31

---

## 📋 Navigation Guide

### 🔴 **Start Here** (Constitutional Documents)

1. **[CANONICAL_PIPELINE.md](CANONICAL_PIPELINE.md)** (23K)
   - Official pipeline definition
   - Tier-based data flow (Tier 0 → Tier 5)
   - Constitutional principles (SSOT, determinism, input alignment)
   - Critical fixes required (join-key drift, SSOT mutation)
   - **Read this first** before modifying pipeline

2. **[PIPELINE_STEP_REGISTRY.md](PIPELINE_STEP_REGISTRY.md)** (10K)
   - Complete inventory of all 13 pipeline modules
   - Evidence-based usage analysis (grep/import references)
   - I/O contracts, determinism status, entrypoints
   - Step lifecycle classification (KEEP/DEPRECATE/GHOST)

3. **[STEP_CLEANUP_PLAN.md](STEP_CLEANUP_PLAN.md)** (18K)
   - Concrete remediation actions (4 phases, ~5 hours)
   - Phase 1: Critical fixes (join-key drift, join-rate gate)
   - Phase 2: Deprecation (archive 5 steps, delete ghost)
   - Phase 3: Refactoring (SSOT immutability, content hash)
   - Phase 4: Documentation updates

---

### 🟡 **Analysis Documents** (Root-Cause Diagnosis)

4. **[DUPLICATE_STEP_ANALYSIS.md](DUPLICATE_STEP_ANALYSIS.md)** (11K)
   - Why 6 step numbers have collisions (step0, step1, step2, step7, step8, step10)
   - Evidence-based explanations (code inspection, grep hits)
   - Timeline reconstruction (evolutionary development)
   - Impact assessment (developer confusion, data corruption risk)

5. **[STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md](STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md)** (9.6K)
   - Executive summary of constitutional audit
   - Critical questions answered (SSOT, why problems repeat, restart safety)
   - Structural diagnosis (4/5 problems are contract violations)
   - Recommended next steps (Phase 1-4 execution order)

---

### 🟢 **Legacy Documents** (Historical Context)

6. **[CANONICAL_INPUT_CONTRACT.md](CANONICAL_INPUT_CONTRACT.md)** (13K)
   - STEP NEXT-27 canonical suffix recovery
   - Historical context for sanitized scope INPUT contract

7. **[STEP_NEXT_27_CANONICAL_SUFFIX_RECOVERY.md](STEP_NEXT_27_CANONICAL_SUFFIX_RECOVERY.md)** (14K)
   - Previous recovery effort (pre-constitutional audit)

8. **Other Legacy Docs** (see full `ls` below)
   - PIPELINE_INVENTORY.md
   - PIPELINE_REALITY_SNAPSHOT.md
   - PIPELINE_ALIGNMENT_AUDIT.md
   - etc.

---

## 🎯 Quick Reference by Use Case

### "I need to understand the current pipeline"
→ Read **CANONICAL_PIPELINE.md** (official flow diagram + tier structure)

### "I want to know which steps are active/deprecated"
→ Read **PIPELINE_STEP_REGISTRY.md** (complete inventory with evidence)

### "I need to fix the join-key drift issue"
→ Read **STEP_CLEANUP_PLAN.md** Phase 1 (Action 1.1: Fix Step4 Input Alignment)

### "Why do we have step7_compare AND step7_amount_extraction?"
→ Read **DUPLICATE_STEP_ANALYSIS.md** Q2 (step7 collision explanation)

### "What is the SSOT and why does it matter?"
→ Read **STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md** Q1 (SSOT declaration)

### "How do I safely restart the pipeline?"
→ Read **CANONICAL_PIPELINE.md** "Atomic Regeneration Rule" + **STEP_CLEANUP_PLAN.md** Action 3.3 (rebuild_insurer.sh)

---

## 📊 Document Dependency Graph

```
STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md (start here)
  ├─ CANONICAL_PIPELINE.md (official flow)
  │   └─ PIPELINE_STEP_REGISTRY.md (step inventory)
  ├─ DUPLICATE_STEP_ANALYSIS.md (collision explanations)
  └─ STEP_CLEANUP_PLAN.md (remediation actions)
      └─ CANONICAL_PIPELINE.md (references fixes)
```

---

## 🔍 Full Directory Listing

```bash
$ ls -lh docs/architecture/
total 496
-rw-r--r--  CANONICAL_INPUT_CONTRACT.md (13K)
-rw-r--r--  CANONICAL_PIPELINE.md (23K) ⭐
-rw-r--r--  DUPLICATE_STEP_ANALYSIS.md (11K) ⭐
-rw-r--r--  NEXT_ACTIONS_ORDERED.md
-rw-r--r--  PIPELINE_ALIGNMENT_AUDIT.md
-rw-r--r--  PIPELINE_INVENTORY.md
-rw-r--r--  PIPELINE_REALITY_SNAPSHOT.md
-rw-r--r--  PIPELINE_STEP_REGISTRY.md (10K) ⭐
-rw-r--r--  README.md (this file)
-rw-r--r--  STEP_CLEANUP_PLAN.md (18K) ⭐
-rw-r--r--  STEP_NEXT_27_CANONICAL_SUFFIX_RECOVERY.md (14K)
-rw-r--r--  STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md (9.6K) ⭐
```

⭐ = **Constitutional documents** (STEP NEXT-31 audit deliverables)

---

## 🚀 Recommended Reading Order

### For New Developers
1. STEP_NEXT_31_CONSTITUTIONAL_AUDIT_SUMMARY.md (executive summary)
2. CANONICAL_PIPELINE.md (learn official flow)
3. PIPELINE_STEP_REGISTRY.md (understand each step)

### For Pipeline Maintainers
1. CANONICAL_PIPELINE.md (constitutional rules)
2. STEP_CLEANUP_PLAN.md (how to fix structural issues)
3. DUPLICATE_STEP_ANALYSIS.md (why duplicates exist)

### For Debugging Join-Key Drift
1. STEP_CLEANUP_PLAN.md Phase 1 Action 1.1 (fix step4 input)
2. CANONICAL_PIPELINE.md "Fix #1" section (detailed explanation)
3. DUPLICATE_STEP_ANALYSIS.md Q4 (step2 vs step3 analysis)

---

## 📝 Document Maintenance

### When to Update These Docs

| Trigger | Documents to Update |
|---------|---------------------|
| New pipeline step added | PIPELINE_STEP_REGISTRY.md, CANONICAL_PIPELINE.md |
| Step deprecated | PIPELINE_STEP_REGISTRY.md, STEP_CLEANUP_PLAN.md |
| SSOT changes | CANONICAL_PIPELINE.md (Tier structure) |
| Critical fix applied | STEP_CLEANUP_PLAN.md (mark action as DONE) |
| Pipeline refactoring | All constitutional docs |

### Version Control
- All constitutional docs (⭐) are under git version control
- Changes require PR review (no direct commits)
- Breaking changes require CLAUDE.md update

---

## 🛡️ Constitutional Principles (Quick Reference)

From **CANONICAL_PIPELINE.md**:

1. **Single Pipeline**: One canonical execution path PDF → SSOT
2. **Step Numbers are Unique**: No duplicates; deprecated steps archived
3. **SSOT is Sacred**: coverage_cards.jsonl is immutable (except optional enrichment)
4. **Determinism Default**: All core steps MUST be deterministic
5. **Input Alignment**: Downstream steps MUST use identical scope file versions

---

## 📞 Support

Questions about pipeline architecture?
1. Check **CANONICAL_PIPELINE.md** first
2. Search **DUPLICATE_STEP_ANALYSIS.md** for collision explanations
3. Refer to **STEP_CLEANUP_PLAN.md** for known issues + fixes

Found a structural issue?
1. Document in new `docs/architecture/ISSUE_*.md`
2. Reference constitutional violation (which principle broken?)
3. Propose fix in `STEP_CLEANUP_PLAN.md` format

---

**Last Constitutional Audit**: 2025-12-31 (STEP NEXT-31)
**Next Review**: After Phase 1-4 cleanup completion
