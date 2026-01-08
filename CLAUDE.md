# CLAUDE.md

## Project
Insurance Proposal Canonical Mapping & Comparison System

---

## 🔒 Active Constitution (SSOT)
All ACTIVE rules, gates, and absolute constraints are defined here:

➡️ `docs/active_constitution.md`

⚠️ This file is the ONLY source of truth for:
- Pipeline rules
- Canonical mapping rules
- Identity rules (insurer / product / variant)
- GATE enforcement
- Forbidden behaviors

CLAUDE MUST read and follow `active_constitution.md` first.

---

## 📦 Data SSOT
- Scope SSOT: `data/scope_v3/`
- Mapping Source (input): `data/sources/mapping/담보명mapping자료.xlsx`

---

## 🚦 Working Rules for Claude
- Do NOT redefine rules already declared in active_constitution.md
- Do NOT summarize or restate the constitution unless explicitly asked
- Do NOT infer or guess missing values
- If a rule conflict is suspected → STOP and ask

---

## 🔒 Pipeline Execution (STEP NEXT-73: ZERO-TOLERANCE)

### ABSOLUTE RULE: Single Entry Point ONLY

**ALWAYS use:**
```bash
python3 tools/run_pipeline.py --stage {step2b|step3|step4|all}
```

**NEVER use:**
- ❌ `python -m pipeline.step2_canonical_mapping.run`
- ❌ `python pipeline/step3_evidence_resolver/run.py`
- ❌ Direct module imports

### Validation Scripts REQUIRE Parameters

**ALWAYS use:**
```bash
python3 tools/audit/validate_anchor_gate.py --input data/compare_v1/compare_rows_v1.jsonl
python3 tools/audit/validate_universe_gate.py --data-dir data
```

**NEVER use:**
- ❌ `python3 tools/audit/validate_anchor_gate.py` (no --input)
- ❌ Hardcoded default paths

### Execution Receipt MANDATORY

After EVERY pipeline run:
1. Check `docs/audit/run_receipt.json` exists
2. Use receipt data for ALL summaries/reports
3. Never claim "completed" without receipt

---

## 🗂️ History / Audit
- Historical decisions and completed steps are archived under:
  - `docs/audit/`
- CLAUDE.md does NOT contain historical logic

---

## Start Here
1. Read `docs/ACTIVE_CONSTITUTION.md`
2. Confirm current STEP NEXT instruction
3. Execute deterministically using `tools/run_pipeline.py`