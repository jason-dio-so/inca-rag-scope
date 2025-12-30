# STEP NEXT-10B-1A — Completion Report

## Date
2025-12-28

## Objective
Recover Step7 source files and lock lineage to prevent DB contamination.

## Problem
- `pipeline/step7_amount` and `pipeline/step7_amount_integration` contained only .pyc files (no .py sources)
- No git history → sources never committed (Branch C scenario)
- Risk of lineage contamination from inca-rag-final or other sources

## Solution
Implemented Branch C protocol:
1. Created minimal stub implementations based on documented requirements
2. Locked entrypoint to `pipeline/step7_amount/run.py`
3. Added guardrail tests to prevent forbidden imports
4. Documented lineage lock procedures

## Deliverables

### Source Files (6 files)
- `pipeline/step7_amount/__init__.py`
- `pipeline/step7_amount/run.py` ← **SINGLE ENTRYPOINT**
- `pipeline/step7_amount/extract_proposal_amount.py`
- `pipeline/step7_amount/proposal_profile.py`
- `pipeline/step7_amount_integration/__init__.py`
- `pipeline/step7_amount_integration/integrate_amount.py`

### Tests (1 file, 5 test cases)
- `tests/test_lineage_lock_step7.py`
  - ✅ test_step7_amount_sources_exist
  - ✅ test_step7_no_forbidden_imports
  - ✅ test_step7_entrypoint_executable
  - ✅ test_step7_validation_functions_exist
  - ✅ test_step7_dry_run_no_side_effects

### Documentation (2 files)
- `docs/audit/STEP_NEXT_10B_1A_STEP7_DIAG.md` (diagnostic report)
- `docs/guardrails/LINEAGE_LOCK.md` (lineage control procedures)

### Updates
- `STATUS.md` (added STEP NEXT-10B-1A section)

## Verification Results
```bash
pytest tests/test_lineage_lock_step7.py -v
# 5 passed in 0.05s

pytest -q
# 101 passed in 0.58s

python -m pipeline.step7_amount.run --help
# Exit 0

python -m pipeline.step7_amount.run --insurer samsung --dry-run
# Exit 0, displays dry-run plan
```

## Forbidden Imports (Enforced by Tests)
❌ `inca-rag-final` / `inca_rag_final`
❌ `apps.loader.*`
❌ `apps.api.*`

## Authorized Execution Path
```bash
python -m pipeline.step7_amount.run --insurer INSURER [--dry-run]
```

## Next Steps (STEP NEXT-10B-2)
1. Implement actual amount extraction logic
2. Update loader for amount_fact table
3. Re-populate DB with amounts
4. Audit amount_fact data

## Status
**COMPLETE** ✅

All DoD criteria satisfied:
- [x] Source files exist and committed
- [x] Entrypoint locked
- [x] Lineage tests PASS
- [x] All tests PASS
- [x] Documentation complete
- [x] STATUS.md updated
