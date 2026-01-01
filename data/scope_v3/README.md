# scope_v3 — Output SSOT (Single Source of Truth)

## Purpose

This directory contains **ALL canonical pipeline outputs** from Step1, Step2-a, and Step2-b.

**Constitutional Rule**: Downstream steps (Step3+) MUST ONLY read from this directory.

---

## File Structure

### Pipeline Outputs (per insurer)
```
{insurer}_step1_raw_scope_v3.jsonl          # Step1: Raw extraction
{insurer}_step2_sanitized_scope_v1.jsonl    # Step2-a: Sanitized
{insurer}_step2_canonical_scope_v1.jsonl    # Step2-b: Canonical mapped
{insurer}_step2_dropped.jsonl               # Step2-a: Dropped entries audit
{insurer}_step2_mapping_report.jsonl        # Step2-b: Mapping report
```

### Run Metadata
```
LATEST                  # Points to current run ID
_RUNS/{run_id}/         # Run-specific metadata
  ├── manifest.yaml     # Input manifest (if used)
  ├── profiles_sha.txt  # Profile checksums (SHA256)
  ├── outputs_sha.txt   # Output checksums (SHA256)
  └── SUMMARY.md        # Execution counts per insurer
```

---

## Canonical Pipeline Entrypoint

**STEP NEXT-53 Constitutional Rule**: Use ONLY this execution path.

### Step1 → Step2-a → Step2-b (Fixed Order)
```bash
# Step1: Profile + Extract (manifest-driven)
python -m pipeline.step1_summary_first.profile_builder_v3 \
  --manifest data/manifests/proposal_pdfs_v1.json \
  --insurer hanwha

python -m pipeline.step1_summary_first.extractor_v3 \
  --manifest data/manifests/proposal_pdfs_v1.json \
  --insurer hanwha

# Step2-a: Sanitize (JSONL-only, no PDF, no LLM)
python -m pipeline.step2_sanitize_scope.run --insurer hanwha

# Step2-b: Canonical mapping (JSONL-only, deterministic)
python -m pipeline.step2_canonical_mapping.run --insurer hanwha
```

**Inputs**:
- Manifest SSOT: `data/manifests/proposal_pdfs_v1.json`
- Mapping INPUT: `data/sources/mapping/담보명mapping자료.xlsx`

**Outputs** (all in `data/scope_v3/`):
- `*_step1_raw_scope_v3.jsonl`
- `*_step2_sanitized_scope_v1.jsonl`
- `*_step2_canonical_scope_v1.jsonl`

See `CLAUDE.md` for full runbook.

---

## Usage

### Get Latest Run
```bash
LATEST_RUN=$(cat data/scope_v3/LATEST)
echo "Current run: $LATEST_RUN"
```

### View Run Summary
```bash
LATEST_RUN=$(cat data/scope_v3/LATEST)
cat "data/scope_v3/_RUNS/$LATEST_RUN/SUMMARY.md"
```

### Verify Output Integrity
```bash
LATEST_RUN=$(cat data/scope_v3/LATEST)
cd data/scope_v3
sha256sum -c "_RUNS/$LATEST_RUN/outputs_sha.txt"
```

---

## File Naming Convention (Future)

**New outputs should follow**:
```
{insurer}__{variant}__{stage}__{version}.jsonl
```

Examples:
- `samsung__default__step1_raw__v3.jsonl`
- `lotte__male__step2_sanitized__v1.jsonl`
- `db__over41__step2_canonical_mapped__v1.jsonl`

**Current files** use simplified naming (no variant marker):
- `{insurer}_step{N}_{stage}_{version}.jsonl`

---

## Legacy Directories (DO NOT USE)

**Archived** (read-only reference):
- `archive/scope_legacy/run_20260101_step_next_52_hk/` (legacy Step2 outputs)
- `archive/legacy_outputs/run_20260101_004654_step_next_53/data_scope/` (legacy Step1 outputs)
- `archive/legacy_outputs/run_20260101_004654_step_next_53/data_scope_v2/` (v2 Step1 outputs)
- `archive/scope_v1_legacy/` (historical)
- `archive/scope_v2_legacy/` (historical)

**DO NOT** reference these directories in new code or downstream steps.

See `data/scope/README.md` for migration guide.

---

## Reproducibility

Each run creates a timestamped directory in `_RUNS/` with:
1. **Input checksums**: Profiles used for extraction
2. **Output checksums**: All generated JSONL files
3. **Execution summary**: Row counts per stage per insurer

This allows:
- Verification that outputs match a specific run
- Comparison of runs over time
- Rollback to previous run if needed

---

## Constitutional Enforcement (STEP NEXT-52-HK)

**SSOT Rule**: Only `data/scope_v3/` contains authoritative pipeline outputs.

**Guardrails**:
1. **Code-level validation**: Step2-a and Step2-b runners validate SSOT path at startup (exit 2 if violated)
2. **Test suite**: `tests/test_scope_ssot_no_legacy_step2_outputs.py` fails if ANY Step2 outputs exist in `data/scope/`
3. **Physical archive**: Legacy Step2 outputs moved to `archive/scope_legacy/run_20260101_step_next_52_hk/`
4. **README**: `data/scope/README.md` marks legacy directory as DO NOT USE

**Violations**:
- Reading from `data/scope/` or `data/scope_v2/` → RuntimeError
- Creating outputs outside `scope_v3/` → exit 2 (Step2-a/Step2-b runners)
- Legacy Step2 outputs in `data/scope/` → Test failure

---

## Created

**STEP NEXT-49-PREP** (2025-12-31)

**Purpose**: Establish single source of truth for pipeline outputs, eliminate directory confusion, enable run tracking.
