# STEP NEXT-46: Step2 Sanitize Scope

## Summary

**Status**: ✅ COMPLETE

**Purpose**: Separate sanitization logic from Step1 (extraction) into dedicated Step2 pipeline.

---

## Constitutional Changes

### Step1 (FROZEN)
- **step1_summary_first** (v3) is now FROZEN
- NO sanitization / filtering / judgment logic allowed
- Output: Raw extraction ONLY (`*_step1_raw_scope.jsonl`)

### Step2 (NEW)
- **step2_sanitize_scope** (new module)
- Deterministic pattern matching (NO LLM, NO inference)
- Input: `*_step1_raw_scope.jsonl`
- Output: `*_step2_sanitized_scope_v1.jsonl`
- Audit trail: `*_step2_dropped.jsonl`

---

## Implementation

### Files Created
```
pipeline/step2_sanitize_scope/
├── __init__.py          # Module docstring
├── sanitize.py          # Core sanitization logic
└── run.py               # CLI runner
```

### Sanitization Rules (ANY match → DROP)

**Category 1: Fragment Detection**
- Parentheses-only: `^\([^)]+\)$`
- Trailing clause markers: `(인 경우|일 때|시)$`
- Condition fragments: `으로 진단확정된`, `지급 조건`, `보장 개시일`

**Category 2: Sentence-like Noise**
- Explanations: `지급(조건|사유|내용)`, `보장(개시일|내용)`
- Long text (>40 chars) without coverage keywords

**Category 3: Administrative Non-Coverage**
- Premium waiver targets: `납입면제.*대상`
- Meta-entries: `대상(담보|보장)`

**Category 4: Variant Deduplication**
- Keep first occurrence, drop duplicates

---

## Execution Results (All Insurers)

```
Total input: 343 entries
Total kept: 335 entries (97.7%)
Total dropped: 8 entries (2.3%)

Global drop reasons:
  - PREMIUM_WAIVER_TARGET: 6 (75.0%)
  - COVERAGE_EXPLANATION: 1 (12.5%)
  - LONG_TEXT_NO_KEYWORDS: 1 (12.5%)
```

### Per-Insurer Results
- **Samsung**: 62 → 61 (98.4% kept, 1 dropped: COVERAGE_EXPLANATION)
- **Hyundai**: 35 → 34 (97.1% kept, 1 dropped: PREMIUM_WAIVER_TARGET)
- **Lotte**: 65 → 64 (98.5% kept, 1 dropped: LONG_TEXT_NO_KEYWORDS)
- **DB**: 50 → 48 (96.0% kept, 2 dropped: PREMIUM_WAIVER_TARGET)
- **KB**: 37 → 36 (97.3% kept, 1 dropped: PREMIUM_WAIVER_TARGET)
- **Meritz**: 36 → 36 (100.0% kept, 0 dropped)
- **Hanwha**: 35 → 34 (97.1% kept, 1 dropped: PREMIUM_WAIVER_TARGET)
- **Heungkuk**: 23 → 22 (95.7% kept, 1 dropped: PREMIUM_WAIVER_TARGET)

---

## Usage

### Single Insurer
```bash
python -m pipeline.step2_sanitize_scope.run --insurer hanwha
```

### All Insurers
```bash
python -m pipeline.step2_sanitize_scope.run --all
```

### Output
- Sanitized: `data/scope/{insurer}_step2_sanitized_scope_v1.jsonl`
- Audit trail: `data/scope/{insurer}_step2_dropped.jsonl`

---

## Verification

**Anti-contamination gate**: HARD GATE (RuntimeError if contamination detected)

Failure patterns checked:
- `진단확정된 경우`
- `인 경우$`
- `일 때$`
- `^\([^)]+\)$`

All insurers: ✅ VERIFIED (no contamination detected)

---

## Updated Documentation

- `CLAUDE.md`: Updated Pipeline Architecture section
  - Step1 marked as FROZEN
  - Step2 added to canonical pipeline
  - Updated execution commands

---

## Next Steps

1. Update Step3 (canonical_mapping) to consume `*_step2_sanitized_scope_v1.jsonl`
2. Update downstream steps (Step4, Step5) to use Step2 output
3. Deprecate `*_scope_mapped.sanitized.csv` (old format)
4. Add integration tests for Step1 → Step2 → Step3 flow
