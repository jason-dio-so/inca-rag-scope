# Lineage Lock — Step7 Amount Extraction

## Purpose
Prevent contamination of inca-rag-scope pipeline with code from inca-rag-final or other sources.

This document defines the ONLY authorized execution path for Step7 amount extraction.

---

## Authorized Entrypoint

**ONLY ONE entrypoint is authorized:**

```bash
python -m pipeline.step7_amount.run --insurer INSURER [--dry-run]
```

### Examples
```bash
# Dry run (shows plan, no changes)
python -m pipeline.step7_amount.run --insurer samsung --dry-run

# Actual execution
python -m pipeline.step7_amount.run --insurer samsung
```

---

## Module Structure

```
pipeline/step7_amount/
├── __init__.py                      # Module declaration
├── run.py                           # ENTRYPOINT (LOCKED)
├── extract_proposal_amount.py       # Amount extraction logic
└── proposal_profile.py              # Document structure profiles

pipeline/step7_amount_integration/
├── __init__.py                      # Module declaration
└── integrate_amount.py              # Amount integration logic
```

---

## Forbidden Imports

The following imports are **ABSOLUTELY PROHIBITED** in step7 modules:

### Forbidden Patterns
```python
# NEVER import from:
from inca_rag_final import *         # ❌ FORBIDDEN
from inca-rag-final import *         # ❌ FORBIDDEN
from apps.loader import *            # ❌ FORBIDDEN
from apps.api import *               # ❌ FORBIDDEN
import inca_rag_final                # ❌ FORBIDDEN
```

### Allowed Imports
```python
# ONLY import from:
from pipeline.step7_amount import *  # ✅ ALLOWED
from pipeline.step1_load_scope import *  # ✅ ALLOWED (other pipeline modules)
import csv, json, logging            # ✅ ALLOWED (stdlib)
from pathlib import Path             # ✅ ALLOWED (stdlib)
from typing import Dict, List        # ✅ ALLOWED (stdlib)
```

---

## Enforcement Mechanisms

### 1. Automated Tests
**Location:** `tests/test_lineage_lock_step7.py`

**Tests:**
- `test_step7_amount_sources_exist`: Verify .py files exist (not just .pyc)
- `test_step7_no_forbidden_imports`: Check for contamination on import
- `test_step7_entrypoint_executable`: Verify run.py works
- `test_step7_validation_functions_exist`: Check validation functions
- `test_step7_dry_run_no_side_effects`: Verify dry-run safety

**Run:**
```bash
pytest tests/test_lineage_lock_step7.py -v
```

### 2. Runtime Validation
Each module contains `validate_no_forbidden_imports()` function:

```python
from pipeline.step7_amount.extract_proposal_amount import validate_no_forbidden_imports

validate_no_forbidden_imports()  # Raises ImportError if contaminated
```

This validation is **automatically called** by `run.py` before execution.

---

## Definition of Done (DoD)

Before ANY change to step7 modules can be committed:

- [ ] All .py source files exist (no orphaned .pyc)
- [ ] `pytest tests/test_lineage_lock_step7.py` PASS
- [ ] `pytest -q` (all tests) PASS
- [ ] `python -m pipeline.step7_amount.run --help` exits 0
- [ ] `python -m pipeline.step7_amount.run --insurer samsung --dry-run` exits 0
- [ ] No imports from forbidden patterns (verified by tests)
- [ ] Git commit message references this document

---

## Change Control

### To Modify Step7 Logic

1. **Create feature branch:**
   ```bash
   git checkout -b feature/step7-amount-DESCRIPTION
   ```

2. **Make changes ONLY in:**
   - `pipeline/step7_amount/*.py`
   - `pipeline/step7_amount_integration/*.py`
   - `tests/test_lineage_lock_step7.py` (if adding tests)

3. **DO NOT modify:**
   - `apps/loader/*`
   - `apps/api/*`
   - Any files outside pipeline/step7*

4. **Validate before commit:**
   ```bash
   pytest tests/test_lineage_lock_step7.py -v
   pytest -q
   python -m pipeline.step7_amount.run --insurer samsung --dry-run
   ```

5. **Commit with reference:**
   ```bash
   git commit -m "feat(step7): DESCRIPTION [ref: LINEAGE_LOCK.md]"
   ```

6. **PR checklist:**
   - [ ] Tests PASS
   - [ ] No forbidden imports
   - [ ] DoD satisfied
   - [ ] PR description explains lineage safety

---

## Incident Response

### If Contamination Detected

**Symptoms:**
- `test_step7_no_forbidden_imports` FAILS
- Runtime `validate_no_forbidden_imports()` raises ImportError
- .pyc files exist without .py sources

**Actions:**
1. **STOP all execution immediately**
2. **Quarantine changes:**
   ```bash
   git stash
   git checkout master
   ```
3. **Report to team:** Document forbidden import detected
4. **Clean cache:**
   ```bash
   find pipeline/step7_amount* -name "*.pyc" -delete
   find pipeline/step7_amount* -name "__pycache__" -type d -exec rm -rf {} +
   ```
5. **Restore from known-good commit:**
   ```bash
   git checkout <LAST_GOOD_COMMIT> -- pipeline/step7_amount
   git checkout <LAST_GOOD_COMMIT> -- pipeline/step7_amount_integration
   ```
6. **Verify restoration:**
   ```bash
   pytest tests/test_lineage_lock_step7.py -v
   ```

---

## References

- **Diagnostic Report:** `docs/audit/STEP_NEXT_10B_1A_STEP7_DIAG.md`
- **DB Schema:** `docs/foundation/ERD_PHYSICAL.md`
- **Step9 Loader Spec:** `docs/foundation/STEP9_DB_POPULATION_SPEC.md`
- **Project Rules:** `CLAUDE.md`

---

## Version

- **Created:** 2025-12-28
- **Last Updated:** 2025-12-28
- **Status:** ACTIVE
- **Enforcement:** MANDATORY
