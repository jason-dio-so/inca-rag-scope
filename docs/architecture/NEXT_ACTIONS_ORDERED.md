# NEXT ACTIONS — Ordered Priority (Reality-Based)

**Context**: Post-STEP NEXT-21 pipeline reality check
**Repo**: `inca-rag-scope`
**Date**: 2025-12-30

---

## Pre-Realignment Checklist (DO THIS FIRST)

Before implementing any tickets, stabilize the current mixed state:

- [ ] **T0.1**: Document which sanitization step is canonical (`step0` vs `step1`)
  - **Evidence**: Both write `*_scope_mapped.sanitized.csv`
  - **Decision**: Pick ONE as INPUT contract entrypoint
  - **DoD**: Update CLAUDE.md with single source reference

- [ ] **T0.2**: Freeze `coverage_cards.jsonl` schema
  - **Evidence**: step5 generates, step7 enriches (overwrites)
  - **Decision**: Define immutable fields vs enrichable fields
  - **DoD**: Add JSON schema file in `docs/schema/coverage_card_schema.json`

- [ ] **T0.3**: Remove or clearly mark DEPRECATED step10_audit
  - **Evidence**: `audit_step7_amount_gt.py` still has `__main__` entrypoint
  - **Decision**: Remove entrypoint or add `raise DeprecationWarning`
  - **DoD**: No confusion about audit SSOT location

- [ ] **T0.4**: Unify proposal extraction (step0 vs step1)
  - **Evidence**: Both `coverage_candidate_filter.py` and `run.py` extract proposals
  - **Decision**: Consolidate into single entry or clarify roles
  - **DoD**: One canonical "proposal → scope.csv" path documented

- [ ] **T0.5**: Archive STATUS.md historical noise
  - **Evidence**: STATUS.md.backup exists, main file has conflicting info
  - **Decision**: Move pre-STEP18X content to `STATUS_ARCHIVE.md`
  - **DoD**: Clean STATUS.md with only active pipeline state

---

## Priority Queue (Execute After Checklist)

### 🔴 P0: SSOT Contract Hardening

**T1**: Lock `coverage_cards.jsonl` write permissions
- **What**: Only step5 + step7 may write; others read-only
- **Why**: Prevent accidental corruption of SSOT
- **How**: Add file locking or validation in CI
- **Evidence**: `PIPELINE_REALITY_SNAPSHOT.md` Step C
- **DoD**: Attempting write from step8/step10 throws error

**T2**: Add `coverage_cards.jsonl` schema validation
- **What**: JSON schema enforced on every SSOT write
- **Why**: Catch schema drift early (e.g., missing `amount` field)
- **How**: Use `jsonschema` lib in step5/step7
- **Evidence**: Historical "amount field missing" bugs (STEP NEXT-10B)
- **DoD**: Invalid card write fails with clear error message

### 🟡 P1: Pipeline Clarity

**T3**: Create single-page pipeline flow diagram
- **What**: ASCII or Mermaid diagram of active steps only
- **Why**: Current entrypoint list is confusing (12 steps, 5 deprecated)
- **How**: Generate from PIPELINE_REALITY_SNAPSHOT.md Step B
- **DoD**: New contributor can trace INPUT → SSOT → OUTPUT in <2 minutes

**T4**: Rename/reorganize step directories to reflect actual flow
- **What**: `step0_scope_filter` → `step1_extract_proposals`, etc.
- **Why**: Step numbers don't reflect execution order
- **How**: Git mv + update imports
- **DoD**: Step numbers match actual pipeline sequence

### 🟢 P2: STEP19 Validation

**T5**: Add unit test for `merge_amount_fragments()`
- **What**: Test cases for `"1," + "000만원"` → `"1,000만원"`
- **Why**: Critical logic with no explicit test coverage
- **Evidence**: `PIPELINE_REALITY_SNAPSHOT.md` Step D
- **DoD**: Test covers edge cases (trailing comma without unit, etc.)

**T6**: Backfill fragment merge audit log
- **What**: Log when fragments are merged (source page + lines)
- **Why**: Debugging fragmentation issues requires traceability
- **How**: Extend `evidence_ref` in coverage_cards with `merge_log`
- **DoD**: Heungkuk/Hanwha cards show which amounts were merged

### 🔵 P3: STEP20 Decision

**T7**: Close or implement STEP NEXT-20
- **What**: Decide if "유사암/경계담보 canonical expansion" is in scope
- **Why**: Currently undefined (not in inca-rag-scope, maybe in U-4.16)
- **Evidence**: `PIPELINE_REALITY_SNAPSHOT.md` Step E (NOT FOUND)
- **DoD**: Either:
  - Add A4210/A4209_3/A4209_6 to mapping file + update step4 search
  - OR: Document as "out of scope for inca-rag-scope"

### 🟣 P4: Tech Debt

**T8**: Remove `reports/` references from docs
- **What**: Clean up legacy references to `reports/*.md`
- **Why**: Already removed in STEP18X, but docs still mention it
- **Evidence**: `PIPELINE_REALITY_SNAPSHOT.md` Step C (prohibited outputs)
- **DoD**: No grep hits for `reports/` in `docs/` directory

**T9**: Consolidate `*_COMPLETION.md` files
- **What**: Merge 13+ completion docs into single CHANGELOG
- **Why**: Fragmented history makes handoff difficult
- **How**: Create `docs/PIPELINE_CHANGELOG.md` with chronological entries
- **DoD**: New session can read 1 file to understand full history

**T10**: Add CI pipeline validation
- **What**: GitHub Actions workflow for `pytest` + SSOT validation
- **Why**: Manual `pytest -q` is easy to forget
- **How**: `.github/workflows/ci.yml` with artifact checks
- **DoD**: PR cannot merge if SSOT schema validation fails

---

## Anti-Patterns to Avoid

1. **DO NOT** implement IMPLEMENTATION_TICKETS_NEXT.md tickets without completing T0.1-T0.5
   - **Reason**: Mixed state will cause conflicts

2. **DO NOT** add new steps (step11+) before reorganizing existing ones
   - **Reason**: Number inflation without clarity

3. **DO NOT** create new SSOT files without updating CLAUDE.md
   - **Reason**: SSOT contract must be single source of truth

4. **DO NOT** reference `inca-rag-demo(U-4.16)` when documenting inca-rag-scope
   - **Reason**: Separate repos, separate states

---

## Execution Order

```
T0.1-T0.5 (Checklist) → T1-T2 (SSOT) → T3-T4 (Clarity) → T5-T10 (Validation/Debt)
```

**Estimated Time**: 1-2 days for checklist + P0/P1, 2-3 days for P2-P4.
