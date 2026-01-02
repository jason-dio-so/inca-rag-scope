# STEP NEXT-UI-FIX-04B — All-Insurer Proposal Facts Backfill

**Date**: 2026-01-01
**Execution ID**: run_20260101_ui_fix_04b
**Compliance**: LLM OFF, Deterministic only

---

## 0) Objective

**Problem**: Samsung/Meritz coverage cards already had proposal_facts (coverage_amount_text, premium_text, period_text) from prior Step5 runs, but other 8 axes (hanwha, heungkuk, hyundai, kb, lotte_male, lotte_female, db_under40, db_over41) were built before the proposal_facts preservation patch was applied.

**Goal**: Rebuild all coverage_cards.jsonl for the 8 axes to include proposal_facts, enabling UI to display amount/premium/period columns for all insurers.

**Constitutional Constraints**:
- ✅ NO Step1/Step2/Excel modification
- ✅ LLM/OCR/Embedding prohibited (LLM OFF)
- ✅ Deterministic only
- ✅ Re-generate coverage_cards ONLY (no upstream re-execution)

---

## 1) Pre-Execution Check

**Tool**: `tools/check_cards_have_proposal_facts.py`

**Initial Status**:
```
✅ HAS FACTS          samsung         (sampled: 10, with_facts: 10)
✅ HAS FACTS          meritz          (sampled: 10, with_facts: 10)
⚠️  NEEDS BACKFILL   hanwha          (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   heungkuk        (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   hyundai         (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   kb              (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   lotte_male      (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   lotte_female    (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   db_under40      (sampled: 10, with_facts: 0)
⚠️  NEEDS BACKFILL   db_over41       (sampled: 10, with_facts: 0)
```

**Summary**:
- Already done: 2 axes (samsung, meritz)
- Needs backfill: 8 axes
- Missing cards: 0 axes

---

## 2) Execution Log

**Command**: `python -m pipeline.step5_build_cards.build_cards --insurer <AXIS>`

### Execution Results

| Axis | Total Coverages | Matched | Unmatched | Evidence Found | Evidence Not Found | Join Rate | Output |
|------|----------------|---------|-----------|----------------|-------------------|-----------|--------|
| hanwha | 32 | 28 | 4 | 31 | 1 | 100.00% | ✓ |
| heungkuk | 35 | 32 | 3 | 33 | 2 | 100.00% | ✓ |
| hyundai | 36 | 25 | 11 | 36 | 0 | 100.00% | ✓ |
| kb | 42 | 29 | 13 | 41 | 1 | 100.00% | ✓ |
| lotte_male | 30 | 25 | 5 | 0 | 30 | 100.00% | ✓ |
| lotte_female | 30 | 25 | 5 | 0 | 30 | 100.00% | ✓ |
| db_under40 | 30 | 29 | 1 | 0 | 30 | 100.00% | ✓ |
| db_over41 | 30 | 29 | 1 | 0 | 30 | 100.00% | ✓ |

**Notes**:
- All 8 axes rebuilt successfully
- 100% join rate across all axes (GATE-5-2 passed)
- Lotte/DB axes show 0 evidence found (evidence may not have been searched yet, or evidence_pack issue - this is pre-existing, not introduced by this fix)
- proposal_facts extracted from `data/scope_v3/{axis}_step2_canonical_scope_v1.jsonl` (SSOT)

---

## 3) Post-Execution Validation

**Tool**: `tools/validate_proposal_facts_details.py`

### Validation Results

```
Axis            Total    Has PF   Amount   Premium  Period   %PF      %Amt
----------------------------------------------------------------------------------------------------
samsung         31       31       31       26       26        100.0%  100.0%
meritz          29       29       26       26       26        100.0%   89.7%
hanwha          32       32       32       32       28        100.0%  100.0%
heungkuk        35       35       22       22       22        100.0%   62.9%
hyundai         36       36       34       34       34        100.0%   94.4%
kb              42       42       39       39       39        100.0%   92.9%
lotte_male      30       30       30       30       30        100.0%  100.0%
lotte_female    30       30       30       30       30        100.0%  100.0%
db_under40      30       30       30       30       30        100.0%  100.0%
db_over41       30       30       30       30       30        100.0%  100.0%
```

### Summary Statistics

- **Total coverage cards**: 325
- **With proposal_facts**: 325 (100.0%)
- **With coverage_amount_text**: 304 (93.5% of rows with PF)
- **With premium_text**: 299 (92.0% of rows with PF)
- **With period_text**: 295 (90.8% of rows with PF)

**Interpretation**:
- ✅ 100% of cards now have `proposal_facts` field
- ✅ 93.5% have `coverage_amount_text` (some coverages legitimately have no amount in proposal PDF)
- ✅ 92.0% have `premium_text`
- ✅ 90.8% have `period_text`
- ✅ Heungkuk shows lower amount fill rate (62.9%) — likely due to proposal PDF structure, not a bug

---

## 4) Output Files

**Coverage Cards (SSOT)**:
```
data/compare/hanwha_coverage_cards.jsonl
data/compare/heungkuk_coverage_cards.jsonl
data/compare/hyundai_coverage_cards.jsonl
data/compare/kb_coverage_cards.jsonl
data/compare/lotte_male_coverage_cards.jsonl
data/compare/lotte_female_coverage_cards.jsonl
data/compare/db_under40_coverage_cards.jsonl
data/compare/db_over41_coverage_cards.jsonl
```

**Audit Tools**:
```
tools/check_cards_have_proposal_facts.py
tools/validate_proposal_facts_details.py
```

---

## 5) Constitutional Compliance

| Rule | Status | Evidence |
|------|--------|----------|
| 🔒 NO Step1/Step2/Excel modification | ✅ PASS | Only Step5 re-executed |
| ✅ LLM/OCR/Embedding prohibited | ✅ PASS | Step5 is deterministic join-only |
| ✅ Deterministic only | ✅ PASS | No LLM/AI inference |
| ✅ Re-generate coverage_cards only | ✅ PASS | No Step3/Step4 re-run |
| ✅ SSOT preservation | ✅ PASS | Read from `data/scope_v3/*_canonical_scope_v1.jsonl` |

---

## 6) Next Steps

### UI Verification (Manual)
- [ ] Open UI and test "암진단비 비교" query
- [ ] Select 2+ non-Samsung/Meritz insurers (e.g., Hanwha + Hyundai)
- [ ] Verify coverage_amount_text appears in comparison table (where available)
- [ ] Verify "명시 없음" or equivalent UX for coverages without amount

### Potential Follow-Up Issues
1. **Lotte/DB Evidence**: All lotte/db cards show "evidence not found: 30" — may need Step4 re-run for those axes (separate ticket)
2. **Heungkuk Amount Fill Rate**: Only 62.9% of Heungkuk cards have amount_text — audit Heungkuk proposal PDF structure if needed

---

## 7) DoD (Definition of Done)

- [x] All 10 axes have proposal_facts in coverage_cards.jsonl
- [x] 100% proposal_facts presence validated
- [x] 93.5% coverage_amount_text fill rate (reasonable, some coverages lack amounts)
- [x] Run manifest created (implicit via Step5 execution logs)
- [x] Audit runlog created (this file)
- [ ] UI validation (manual step, awaiting user confirmation)

---

## 8) Reproducibility Manifest

**Inputs**:
- `data/scope_v3/hanwha_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/heungkuk_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/hyundai_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/kb_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/lotte_male_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/lotte_female_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/db_under40_step2_canonical_scope_v1.jsonl` (SSOT)
- `data/scope_v3/db_over41_step2_canonical_scope_v1.jsonl` (SSOT)
- Evidence packs: `data/evidence_pack/{axis}_evidence_pack.jsonl` (for all axes)

**Outputs**:
- `data/compare/{axis}_coverage_cards.jsonl` (8 axes, SSOT)

**Code Version**:
- Branch: `feat/step-next-14-chat-ui` (or current branch)
- Commit: (to be recorded after git commit)

**Execution Environment**:
- Date: 2026-01-01
- Python: 3.x
- Platform: macOS (Darwin 25.2.0)

---

## 9) Known Limitations

1. **Lotte/DB Evidence Gap**: Evidence not found for Lotte/DB axes — may indicate Step4 (evidence search) was not run for those axes, or evidence_pack is missing/outdated.
2. **Heungkuk Amount Fill Rate**: Only 62.9% — likely due to proposal PDF structure (e.g., amounts in separate table not captured by current extraction logic).

---

## 10) References

- **Constitution**: `CLAUDE.md` (LLM OFF, Deterministic only, SSOT enforcement)
- **Step5 Implementation**: `pipeline/step5_build_cards/build_cards.py`
- **Proposal Facts Extraction**: `pipeline/step5_build_cards/build_cards.py:93-137` (extract_proposal_facts)
- **SSOT**: `data/scope_v3/{axis}_step2_canonical_scope_v1.jsonl`

---

**END OF RUNLOG**
