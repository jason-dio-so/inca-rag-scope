# Pipeline Constitution — STEP NEXT-56

**Effective Date**: 2026-01-01
**Purpose**: Permanently prevent Samsung/Hyundai/DB regressions through structural enforcement

---

## 🔒 Constitutional Rules (Absolute)

### Rule 1: Single Entrypoint Enforcement

**The ONLY allowed execution method:**

```bash
./tools/run_pipeline_v3.sh --manifest data/manifests/proposal_pdfs_v1.json
```

**FORBIDDEN** (exit code 2):
- `python -m pipeline.step1_summary_first.profile_builder_v3 --manifest ...`
- `python -m pipeline.step1_summary_first.extractor_v3 --insurer samsung`
- Any direct module execution
- Any `--insurer` single-insurer runs

**Rationale**: Single entrypoint ensures:
- All steps run sequentially (Step1 → Step2-a → Step2-b)
- Variant consistency across all steps
- Constitutional gates execute every run
- No ad-hoc partial runs that skip validation

---

### Rule 2: Step Definitions (Locked)

| Step | Meaning | Forbidden Actions |
|------|---------|-------------------|
| **Step1-A** | Profile Builder | Column detection, table structure analysis |
| **Step1-B** | Extractor | Raw fact extraction from proposal PDFs |
| **Step2-A** | Sanitize | Normalization, fragment removal (NO semantic judgment) |
| **Step2-B** | Canonical Mapping | 신정원 unified code mapping (deterministic only) |

**Step Boundaries**:
- Step1 = Profile + Extract (both 1A and 1B)
- Step2 = Sanitize + Canonical Mapping (both 2A and 2B)
- **Step2+ CANNOT access PDF/layout/profile** (JSONL input only)

---

### Rule 3: Step1 Contract (Most Critical)

Step1 output MUST guarantee:

1. **`coverage_name_raw` preserves original text** without loss
   - "1. 상해사망" → "1. 상해사망" ✅
   - "1. 상해사망" → ". 상해사망" ❌ (prefix loss FORBIDDEN)

2. **Prefix/number/symbol preservation**
   - Leading markers ("1.", "2.", "(1)", etc.) MUST be preserved
   - Applies to both hybrid and standard extraction modes

3. **Profile stability lock**
   - Same PDF fingerprint → same column_map
   - column_map change → exit code 2 (HARD FAIL)

4. **No result reduction via profile changes**
   - Samsung regression (17→32 fix) precedent
   - Category column detection MUST prevent false mapping

**Enforcement**:
- Profile lock gate (`_verify_profile_lock()`)
- 3-run stability test (checksum verification)

---

### Rule 4: Variant Axis Preservation

**Variant-aware insurers:**

| Insurer | Variants |
|---------|----------|
| DB | `under40` / `over41` |
| LOTTE | `male` / `female` |

**Mandatory rules:**

1. **All steps MUST be variant-aware**
   - Step1: `{insurer}_{variant}_proposal_profile_v3.json`
   - Step1: `{insurer}_{variant}_step1_raw_scope_v3.jsonl`
   - Step2-a: `{insurer}_{variant}_step2_sanitized_scope_v1.jsonl`
   - Step2-b: `{insurer}_{variant}_step2_canonical_scope_v1.jsonl`

2. **Single-variant files are FORBIDDEN**
   - `db_step2_canonical_scope_v1.jsonl` ❌ (CONSTITUTIONAL VIOLATION)
   - `lotte_step2_sanitized_scope_v1.jsonl` ❌ (CONSTITUTIONAL VIOLATION)

3. **Variant pairs MUST exist together**
   - DB: both `under40` AND `over41`
   - LOTTE: both `male` AND `female`

**Enforcement**:
- GATE-56-2: Variant Preservation Check
- File naming validation in all pipeline steps

---

### Rule 5: SSOT (Output Single Source of Truth)

**Valid output directory:**
```
data/scope_v3/
```

**Structure:**
```
data/scope_v3/
 ├─ _RUNS/<run_id>/
 │   ├─ manifest.json          # Input manifest copy
 │   ├─ outputs_sha.txt        # Output checksums
 │   ├─ profiles_sha.txt       # Profile checksums
 │   └─ SUMMARY.md             # Execution summary
 ├─ LATEST → <run_id>          # Symlink to latest run
 ├─ {insurer}_{variant}_step1_raw_scope_v3.jsonl
 ├─ {insurer}_{variant}_step2_sanitized_scope_v1.jsonl
 ├─ {insurer}_{variant}_step2_canonical_scope_v1.jsonl
 ├─ {insurer}_{variant}_step2_dropped.jsonl
 ├─ {insurer}_{variant}_step2_mapping_report.jsonl
 └─ README.md
```

**FORBIDDEN directories:**
- `data/scope/` (archived)
- `data/scope_v2/` (archived)
- Root-level JSONL files

**Enforcement**:
- GATE-56-4: SSOT Enforcement Check
- Step2 modules reject non-`scope_v3/` paths

---

### Rule 6: Step Dependency Isolation

**Import restrictions:**

| Step | CAN import | CANNOT import |
|------|------------|---------------|
| Step2-A | Common utils | Step1 modules |
| Step2-B | Common utils | Step1, Step2-A modules |
| Step3+ | API utils | Step1, Step2 modules |

**Input/Output contract:**
- All step communication via JSONL files ONLY
- No direct function calls between steps
- No shared state/global variables

**Enforcement**:
- Manual code review
- Import violation → exit code 2

---

## 🧪 Mandatory Gates (HARD FAIL on violation)

### GATE-56-1: Step1 Stability

**Test**: 3 consecutive runs (Samsung, Hyundai, DB)

**Requirements**:
- Profile checksum: Identical (3/3)
- Raw output checksum: Identical (3/3)
- Row count: Identical (3/3)

**Implementation**: `tests/test_step1_stability.py`

---

### GATE-56-2: Variant Preservation

**Test**: Variant file pair existence

**Requirements**:
- DB: Both `under40` AND `over41` files exist
- LOTTE: Both `male` AND `female` files exist
- No single-variant files (`db_step2_*.jsonl`)

**Implementation**: `tests/test_variant_preservation.py`

---

### GATE-56-3: Raw Integrity

**Test**: Prefix/marker preservation

**Requirements**:
- Zero occurrences of `^\. ` (broken prefix)
- Zero occurrences of `^\)\(` (broken markers)
- Proper prefixes intact ("1. ", "2. ", etc.)

**Implementation**: Built into `run_pipeline_v3.sh`

---

### GATE-56-4: SSOT Enforcement

**Test**: No outputs outside `data/scope_v3/`

**Requirements**:
- Zero JSONL files in `data/scope/`
- Zero JSONL files in `data/scope_v2/`
- All outputs in `data/scope_v3/` ONLY

**Implementation**: `tests/test_ssot_violation.py`

---

## 🚫 Change Control (Prohibited Actions)

**FORBIDDEN in this project:**

1. ❌ Add heuristics/guessing to Step1 column detection
2. ❌ Add insurer-specific hardcoding (Samsung/Hyundai/DB-only logic)
3. ❌ Add "result expansion" logic (increasing row count artificially)
4. ❌ Add LLM/embedding/AI to any deterministic step
5. ❌ Create new entrypoints (`run_pipeline_v4.sh`, etc.)
6. ❌ Modify SSOT directory structure
7. ❌ Bypass constitutional gates

**ALLOWED changes:**

✅ Fix deterministic bugs (with evidence + gate verification)
✅ Add gates/guardrails (NEVER remove)
✅ Improve documentation
✅ Add tests (NEVER remove passing tests)

---

## 📋 Amendment Process

**To modify this constitution:**

1. **Evidence required**: Concrete failure case with logs/data
2. **Gate-first approach**: Add gate BEFORE making change
3. **Non-regression proof**: All existing gates MUST still pass
4. **Documentation update**: Reflect change in this document
5. **Approval threshold**: 100% gate pass rate

**Example valid amendment:**
- New insurer with 3+ variants → Add to Rule 4 variant list
- New gate discovered → Add to Mandatory Gates section

**Example INVALID amendment:**
- "Step1 should filter XXX" → Violates Step1 Contract (Rule 3)
- "Let's merge Step2-a and Step2-b" → Violates Step Definitions (Rule 2)

---

## 🎯 Success Criteria

**Pipeline is constitutional if:**

1. ✅ Single entrypoint used exclusively
2. ✅ All 4 mandatory gates pass
3. ✅ No imports across step boundaries
4. ✅ Variant axis preserved across all steps
5. ✅ SSOT enforced (no legacy directory pollution)
6. ✅ Step1 stability proven (3-run checksums identical)

**Pipeline has regressed if:**

- Any gate fails
- New JSONL appears outside `scope_v3/`
- Profile changes break Samsung/DB/Hyundai
- Variant files merge into single files

---

## 📖 Historical Context

**Why this constitution exists:**

| Date | Incident | Root Cause | Prevention |
|------|----------|------------|------------|
| 2026-01-01 | Samsung 17-row regression | Category column misdetection | Rule 3: Profile lock |
| 2026-01-01 | DB 0% mapping | Prefix loss (". 상해사망") | GATE-56-3: Raw integrity |
| 2026-01-01 | Variant confusion | Step2 single-file generation | Rule 4: Variant axis |
| 2025-12-31 | Ad-hoc runs | No entrypoint enforcement | Rule 1: Single entrypoint |

**Precedents**:
- STEP NEXT-55: DB normalization fix
- STEP NEXT-55A: Samsung category column fix
- STEP NEXT-52-HK: SSOT guardrail enforcement

---

## 🔗 Related Documents

- `docs/audit/STEP_NEXT_56_PIPELINE_LOCK_REPORT.md` — Implementation audit
- `STATUS.md` — Current project status
- `CLAUDE.md` — Project instructions for AI assistant
- `tools/run_pipeline_v3.sh` — Constitutional entrypoint

---

**This constitution is IMMUTABLE unless amended via the process above.**

**Effective immediately. No grandfather clauses.**
