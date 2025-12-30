# STEP NEXT-10B-1A — Step7 Source Recovery Diagnostic

## Date
2025-12-28

## Objective
Diagnose and recover missing Step7 source files (.py) that exist only as compiled bytecode (.pyc).

---

## STEP 0 — Diagnostic Commands & Output

### 1. Working Directory Confirmation
```bash
pwd
```
**Output:**
```
/Users/cheollee/inca-rag-scope
```

### 2. Git Status
```bash
git status -sb
```
**Output:**
```
## stage/step-next-db-2c-gamma...origin/stage/step-next-db-2c-gamma [ahead 3]
?? STEP_NEXT_10_COMPLETION_REPORT.md
?? apps/api/
?? docs/HISTORY_SCOPE_V1.md
?? docs/run/STEP_NEXT_10B1_DB_AUDIT_REPORT.md
?? simple_test.html
?? test_api.html
```

### 3. Step7 Directory Listing
```bash
ls -la pipeline/step7_amount pipeline/step7_amount_integration
```
**Output:**
```
pipeline/step7_amount:
total 0
drwxr-xr-x   4 cheollee  staff  128 Dec 28 02:11 __pycache__
drwxr-xr-x   3 cheollee  staff   96 Dec 28 10:20 .
drwx------  16 cheollee  staff  512 Dec 28 01:42 ..

pipeline/step7_amount_integration:
total 0
drwxr-xr-x   4 cheollee  staff  128 Dec 28 02:11 __pycache__
drwxr-xr-x   3 cheollee  staff   96 Dec 28 10:20 .
drwx------  16 cheollee  staff  512 Dec 28 01:42 ..
```
**Finding:** Directories exist with only __pycache__, NO .py source files.

### 4. File Discovery in step7 Directories
```bash
find pipeline/step7_amount pipeline/step7_amount_integration -maxdepth 2 -type f -print
```
**Output:**
```
pipeline/step7_amount/__pycache__/proposal_profile.cpython-311.pyc
pipeline/step7_amount/__pycache__/extract_proposal_amount.cpython-311.pyc
pipeline/step7_amount_integration/__pycache__/integrate_amount.cpython-311.pyc
pipeline/step7_amount_integration/__pycache__/__init__.cpython-311.pyc
```
**Finding:** 4 .pyc files discovered:
- `proposal_profile.cpython-311.pyc`
- `extract_proposal_amount.cpython-311.pyc`
- `integrate_amount.cpython-311.pyc`
- `__init__.cpython-311.pyc`

### 5. Search for step7/amount Python Sources
```bash
find pipeline -maxdepth 4 -type f -name "*.py" | grep -E "step7|amount"
```
**Output:**
```
pipeline/step7_compare/compare_insurers.py
```
**Finding:** NO step7_amount or step7_amount_integration .py files found anywhere in pipeline.

### 6. Pyc Module Inventory
```python
import glob
for p in ["pipeline/step7_amount/__pycache__", "pipeline/step7_amount_integration/__pycache__"]:
    files = sorted(glob.glob(p+"/*.pyc"))
    for f in files: print(f)
```
**Output:**
```
=== pipeline/step7_amount/__pycache__ ===
  pipeline/step7_amount/__pycache__/extract_proposal_amount.cpython-311.pyc
  pipeline/step7_amount/__pycache__/proposal_profile.cpython-311.pyc

=== pipeline/step7_amount_integration/__pycache__ ===
  pipeline/step7_amount_integration/__pycache__/__init__.cpython-311.pyc
  pipeline/step7_amount_integration/__pycache__/integrate_amount.cpython-311.pyc
```

### 7. Git History Check
```bash
git log --name-status --all -- pipeline/step7_amount pipeline/step7_amount_integration | head -300
```
**Output:** (empty)

```bash
git log --all --diff-filter=D -- 'pipeline/step7_amount/*.py' 'pipeline/step7_amount_integration/*.py'
```
**Output:** (empty)

```bash
git log --all --oneline -- 'pipeline/step7_amount/*.py'
```
**Output:** (empty)

```bash
git ls-tree -r --name-only HEAD pipeline/step7_amount pipeline/step7_amount_integration
```
**Output:** (empty)

**Finding:** NO git history for these .py files — they were NEVER committed.

### 8. Search for Sources Elsewhere
```bash
find . -name "extract_proposal_amount.py" -o -name "proposal_profile.py" -o -name "integrate_amount.py"
```
**Output:** (empty)

**Finding:** Source files do NOT exist anywhere in the repository.

### 9. Import References Check
```bash
grep -r "extract_proposal_amount\|proposal_profile\|integrate_amount" --include="*.py"
```
**Output:** No matches found

**Finding:** No code references these modules.

---

## CONCLUSION — Branch C (Sources Never Committed)

**Status:** Branch C confirmed.

**Evidence:**
1. ✅ .pyc files exist in `__pycache__` directories
2. ✅ NO corresponding .py source files exist
3. ✅ NO git history of these files being added or deleted
4. ✅ NO .py files found anywhere in repository
5. ✅ NO code references these modules

**Root Cause:**
Step7 amount extraction modules were implemented locally but **never committed to git**. Only the compiled bytecode remains from local execution.

**Risk Assessment:**
- **CRITICAL:** Cannot determine lineage/correctness of step7 logic
- **CRITICAL:** Potential contamination from inca-rag-final or other sources
- **CRITICAL:** No version control = no audit trail

**Mitigation Strategy:**
Following Branch C protocol:
1. Do NOT attempt decompilation (unreliable/untrusted)
2. Reconstruct minimal step7 interface from documentation/requirements
3. Implement clean, scope-based step7 modules with explicit guards
4. Add strong lineage lock tests to prevent future contamination
5. Document why sources were missing + prevention measures

---

## Actions Completed (STEP 1-4)

### STEP 1 — Source Recovery (Branch C)
- ✅ Created `pipeline/step7_amount/__init__.py`
- ✅ Created `pipeline/step7_amount/run.py`
- ✅ Created `pipeline/step7_amount/extract_proposal_amount.py`
- ✅ Created `pipeline/step7_amount/proposal_profile.py`
- ✅ Created `pipeline/step7_amount_integration/__init__.py`
- ✅ Created `pipeline/step7_amount_integration/integrate_amount.py`

**Implementation Approach:** Minimal stub following documented requirements
- No LLM, no calculation, no inference
- Scope-first principle (only canonical mapping coverages)
- Stub returns NOT_IMPLEMENTED status for actual logic (to be refined in NEXT-10B-2)

### STEP 2 — Entrypoint Lock
- ✅ `pipeline/step7_amount/run.py` established as single entrypoint
- ✅ `--dry-run` support implemented
- ✅ Lineage validation on every execution
- ✅ Command verified: `python -m pipeline.step7_amount.run --help` (exit 0)
- ✅ Command verified: `python -m pipeline.step7_amount.run --insurer samsung --dry-run` (exit 0)

### STEP 3 — Guardrail Installation
**Tests Added:** `tests/test_lineage_lock_step7.py`
- ✅ `test_step7_amount_sources_exist` — Verify .py files exist
- ✅ `test_step7_no_forbidden_imports` — Detect contamination
- ✅ `test_step7_entrypoint_executable` — Verify run.py works
- ✅ `test_step7_validation_functions_exist` — Check validation functions
- ✅ `test_step7_dry_run_no_side_effects` — Verify dry-run safety

**Documentation Added:** `docs/guardrails/LINEAGE_LOCK.md`
- ✅ Authorized entrypoint definition
- ✅ Forbidden import list
- ✅ Change control process
- ✅ Incident response procedure
- ✅ DoD checklist

### STEP 4 — Validation (DoD)
- ✅ `pipeline/step7_amount/` contains 4 .py files
- ✅ `pipeline/step7_amount_integration/` contains 2 .py files
- ✅ Step7 entrypoint locked to `run.py`
- ✅ `tests/test_lineage_lock_step7.py` PASS (5/5)
- ✅ `pytest -q` PASS (101/101)
- ✅ `docs/audit/STEP_NEXT_10B_1A_STEP7_DIAG.md` complete
- ✅ `docs/guardrails/LINEAGE_LOCK.md` complete
- ✅ `STATUS.md` updated with STEP NEXT-10B-1A completion

**Final Verification:**
```bash
pytest tests/test_lineage_lock_step7.py -v
# Result: 5 passed in 0.05s

pytest -q
# Result: 101 passed in 0.58s

python -m pipeline.step7_amount.run --help
# Result: Exit 0, help text displayed

python -m pipeline.step7_amount.run --insurer samsung --dry-run
# Result: Exit 0, dry-run plan displayed
```

---

## Conclusion

**STEP NEXT-10B-1A: COMPLETE**

**Status:** Branch C (sources never committed) — Sources successfully recovered as minimal stubs

**Lineage Lock:** ACTIVE — All guardrails in place

**Risk Mitigation:**
1. ✅ Sources under version control (.py files committed)
2. ✅ Forbidden imports blocked by tests
3. ✅ Single entrypoint enforced
4. ✅ Runtime validation on every execution
5. ✅ Incident response procedure documented

**Next STEP:** STEP NEXT-10B-2
- Implement actual amount extraction logic
- Refine integration with coverage_cards.jsonl
- Update loader to handle amount_fact
- Re-populate DB with amounts
- Audit amount_fact table
