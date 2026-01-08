# STEP NEXT-71 — Universe Gate + Unanchored Backlog (SSOT 기반)

**Date**: 2026-01-08
**Status**: ✅ COMPLETED
**Prerequisites**: STEP NEXT-70-ANCHOR-FIX

---

## 절대 원칙

1. **Universe SSOT**: Step2-b canonical output (`*_step2_canonical_scope_v1.jsonl`)
2. **Anchored definition**: `anchored := bool(coverage_code)` from Step2-b
3. **Row conservation**: U == E == C (exact count match)
4. **No inference**: Regex extraction is auxiliary only, never for anchoring

---

## TASK-A: Universe Definition & Gate

### Universe SSOT

```
Universe = ⋃ data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl
           for insurer in [samsung, hanwha, heungkuk, hyundai, kb, meritz,
                          db_over41, db_under40, lotte_female, lotte_male]
```

**Row count**: 340 coverages across 8 base insurers

### Universe Gate (HARD FAIL)

**Definition**: U == E == C

Where:
- **U**: Universe rows (Step2-b canonical)
- **E**: Evidence rows (Step3 gated output)
- **C**: Compare rows (Step4 compare_rows)

**Exit code**: 2 if ANY mismatch (total or per-insurer)

### Validation Tool

**Script**: `tools/audit/validate_universe_gate.py`

**Output**:
```
[Universe Gate Validation]
================================================================================

Per-Insurer Breakdown:
Insurer              U      E      C   U==E   E==C   Status
--------------------------------------------------------------------------------
db                  62     62     62      ✓      ✓   ✅ PASS
hanwha              33     33     33      ✓      ✓   ✅ PASS
heungkuk            36     36     36      ✓      ✓   ✅ PASS
hyundai             37     37     37      ✓      ✓   ✅ PASS
kb                  43     43     43      ✓      ✓   ✅ PASS
lotte               60     60     60      ✓      ✓   ✅ PASS
meritz              37     37     37      ✓      ✓   ✅ PASS
samsung             32     32     32      ✓      ✓   ✅ PASS

--------------------------------------------------------------------------------
TOTAL              340    340    340

Total Match:
  U (Universe):  340
  E (Evidence):  340
  C (Compare):   340
  U == E == C:   True

✅ UNIVERSE GATE PASSED
   All insurers: U == E == C (340 rows)
```

**Interpretation**:
- ✅ No row loss in pipeline
- ✅ Step2-b → Step3 → Step4 preserves all coverage rows
- ✅ Universe integrity maintained

---

## TASK-B: Anchored Gate

### Anchored Definition

```python
# Absolute rule
anchored := bool(coverage_code)  # from Step2-b canonical mapping

# Equivalent
unanchored := not bool(coverage_code)
```

### Anchored Gate (HARD FAIL)

**Definition**: `pct_code == pct_anchor`

Where:
- **pct_code** = % of rows where `coverage_code != null`
- **pct_anchor** = % of rows where `anchored == true`

**Exit code**: 2 if mismatch

### Validation Tool

**Script**: `tools/audit/validate_anchor_gate.py`

**Output**:
```
[Anchor GATE Validation]
  Total rows: 340
  Has coverage_code: 278 (81.8%)
  Anchored (unanchored=false): 278 (81.8%)

✅ GATE PASSED: pct_code == pct_anchor (81.8%)
```

**Interpretation**:
- ✅ 100% consistency between `coverage_code` and `anchored` status
- ✅ Anchored logic is deterministic (no regex dependency)
- ✅ 278/340 (81.8%) coverages successfully mapped to coverage_code

---

## TASK-C: Unanchored Backlog Analysis

### Total Unanchored

- **Count**: 62 / 340 (18.2%)
- **Source**: All from Step2-b mapping failures

### A/B Classification

**Rules**:
- **(A) Mapping/Excel gap**: Step2-b has `coverage_code == null`
- **(B) Pipeline drop/bug**: Step2-b has `coverage_code != null` but Step4 has `null`

### Export Tool

**Script**: `tools/audit/export_unanchored_backlog.py`

**Output**:
```
[Unanchored Backlog Export]
================================================================================

Loading Step2-b canonical mapping...
  Loaded 280 coverage mappings

Extracting unanchored rows from compare_rows...
  Found 62 unanchored coverages

✅ Exported 62 rows to docs/audit/unanchored_backlog_v1.csv

## Classification Summary
- Total unanchored: 62
- **(A) Mapping/Excel gap**: 62 / 62 (100.0%)
- **(B) Pipeline drop/bug**: 0 / 62 (0.0%)
- **(?) Other**: 0 / 62

✅ No pipeline bugs detected
   All unanchored coverages are legitimate mapping gaps
   → Remaining work is mapping backlog (Excel updates)
```

### Sample (20 rows, seed=42)

| # | Class | Insurer | Coverage Name | Step2 Code | Classification |
|---|-------|---------|---------------|------------|----------------|
| 1 | **A MAPPING GAP** | meritz | 일반상해사망 | NULL | No coverage_code in Step2-b |
| 2 | **A MAPPING GAP** | hanwha | 4대유사암진단비 | NULL | No coverage_code in Step2-b |
| 3 | **A MAPPING GAP** | samsung | 골절 진단비(치아파절(깨짐, 부러짐) 제외) | NULL | No coverage_code in Step2-b |
| 4 | **A MAPPING GAP** | meritz | 대표계약 기준 : 남자40세... | NULL | No coverage_code in Step2-b |
| 5 | **A MAPPING GAP** | hyundai | 18. 심혈관질환(I49)진단담보 | NULL | No coverage_code in Step2-b |
| 6 | **A MAPPING GAP** | hyundai | 10. 유사암진단Ⅱ담보 | NULL | No coverage_code in Step2-b |
| 7 | **A MAPPING GAP** | hyundai | 3. 보험료납입면제대상담보 | NULL | No coverage_code in Step2-b |
| 8 | **A MAPPING GAP** | hanwha | 암(갑상선암및전립선암제외)다빈치로봇수술비... | NULL | No coverage_code in Step2-b |
| 9 | **A MAPPING GAP** | lotte | 암직접입원비(요양병원제외)(1일-120일) | NULL | No coverage_code in Step2-b |
| 10 | **A MAPPING GAP** | hanwha | 상해후유장해(3-100%) | NULL | No coverage_code in Step2-b |
| ... | ... | ... | ... | ... | ... |

**Full CSV**: `docs/audit/unanchored_backlog_v1.csv` (62 rows)

---

## Summary Statistics

### Universe Integrity

| Metric | Value | Status |
|--------|-------|--------|
| Universe rows (U) | 340 | ✅ |
| Evidence rows (E) | 340 | ✅ |
| Compare rows (C) | 340 | ✅ |
| U == E == C | TRUE | ✅ PASS |

### Anchoring Quality

| Metric | Value | Status |
|--------|-------|--------|
| Total coverages | 340 | - |
| Anchored (has coverage_code) | 278 (81.8%) | ✅ |
| Unanchored (no coverage_code) | 62 (18.2%) | ℹ️ |
| pct_code == pct_anchor | TRUE | ✅ PASS |

### Unanchored Classification

| Class | Count | % | Implication |
|-------|-------|---|-------------|
| (A) Mapping/Excel gap | 62 | 100% | Mapping backlog |
| (B) Pipeline drop/bug | 0 | 0% | No bugs |

---

## Conclusions

### ✅ All Gates Passed

1. **Universe Gate**: U == E == C (340 rows) ✅
2. **Anchor Gate**: pct_code == pct_anchor (81.8%) ✅
3. **No Pipeline Bugs**: B_PIPELINE_DROP = 0 ✅

### Remaining Work

**Nature**: Mapping backlog (not pipeline bugs)

**Action Required**: Update `담보명mapping자료.xlsx` to cover 62 unmapped coverages

**Examples of unmapped patterns**:
- Generic terms: "수술", "장해/장애", "간병/사망"
- Insurer-specific: "4대유사암진단비", "상해후유장해(3-100%)"
- Premium waiver: "보험료납입면제대상담보"
- Complex modifiers: "암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형)"

### Pipeline Quality

- ✅ **Row conservation**: No coverage loss (U == E == C)
- ✅ **Anchoring determinism**: 100% match between coverage_code and anchored
- ✅ **No carry-through bugs**: All unanchored are legitimate mapping gaps
- ✅ **Architecture correctness**: Step2-b → Step3 → Step4 flow validated

---

## Deliverables

### Code

1. **tools/audit/validate_universe_gate.py**
   - HARD GATE: U == E == C validation
   - Exit code 2 on failure
   - Per-insurer breakdown

2. **tools/audit/validate_anchor_gate.py**
   - HARD GATE: pct_code == pct_anchor validation
   - Exit code 1 on failure (from STEP NEXT-70-ANCHOR-FIX)

3. **tools/audit/export_unanchored_backlog.py**
   - Full CSV export (62 rows)
   - A/B classification
   - Seed-based sampling (deterministic)

### Data

1. **docs/audit/unanchored_backlog_v1.csv**
   - 62 unanchored coverages
   - Full Step2-b metadata
   - A/B classification
   - Ready for Excel mapping updates

### Documentation

1. **docs/audit/STEP_NEXT_71_UNIVERSE_AND_ANCHOR_GATES.md** (this file)
   - Universe definition
   - Gate specifications
   - Validation results
   - Backlog analysis

---

## Execution Commands

```bash
# Universe Gate (HARD FAIL if mismatch)
python tools/audit/validate_universe_gate.py

# Anchor Gate (HARD FAIL if mismatch)
python tools/audit/validate_anchor_gate.py

# Export Unanchored Backlog
python tools/audit/export_unanchored_backlog.py
```

---

## Absolute Rules Compliance

- ✅ **SSOT-first**: Step2-b canonical as Universe source
- ✅ **No LLM**: Deterministic only
- ✅ **No inference**: coverage_code from mapping only
- ✅ **Evidence-first**: No value fabrication
- ✅ **Deterministic**: Seed-based sampling for reproducibility

---

**End of STEP NEXT-71**
