# STEP NEXT-34 Normalization Policy

**Date**: 2025-12-31
**Purpose**: Apply deterministic newline normalization at Step1 scope boundary
**Related**: STEP NEXT-33 (not_found root cause analysis)

---

## Policy Decision

**Adopted**: **Option A - Step1 Scope Post-Processing Normalization**

**Rationale**:
- Scope is the SSOT input boundary
- Data hygiene fix, not search expansion
- Step1 already hardened and locked (STEP NEXT-32)
- Deterministic, idempotent, backward-compatible

---

## Normalization Rule (Single, Deterministic)

```python
def normalize_coverage_name(coverage_name: str) -> str:
    """
    Rule (single, deterministic, idempotent):
    1. Replace all internal newlines (\n, \r\n) with single space
    2. Collapse multiple spaces into one
    3. Trim leading/trailing whitespace
    """
    normalized = coverage_name.replace('\r\n', ' ').replace('\n', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    return normalized
```

**Explicitly Forbidden**:
- ❌ Word deletion
- ❌ Bracket removal
- ❌ Number changes
- ❌ Meaning-based transformations
- ❌ Alias generation
- ❌ Fuzzy matching

---

## Implementation Scope

**Files Modified**:
- `pipeline/step1_extract_scope/run.py` (added normalize_coverage_name function + 2 call sites)
- `pipeline/step1_extract_scope/hardening.py` (added normalize_coverage_name function + 4 call sites)

**Application Points**:
- All coverage_name_raw append operations
- Before validation filters
- Before deduplication (seen set)

**Affected Insurers**: ALL (no conditional branches)

---

## Impact Analysis

### Expected Impact

| Insurer | Before | After | Change |
|---------|--------|-------|--------|
| Samsung | 42 | 41 | -1 (duplicate collapsed) |
| KB | 45 | 45 | 0 (no change) |
| Meritz | 34 | 34 | 0 (count unchanged) |

### Actual Impact (STEP NEXT-34 Execution)

**Samsung**:
- Count: 42 → 41 ✓ (Expected: newline normalization collapsed 1 duplicate)
- Gates: PASS (41 ≥ 30, pollution 0%)
- No existing found → not_found regression

**KB**:
- Count: 45 → 45 ✓ (No change)
- Gates: PASS (45 ≥ 30, pollution 0%)
- Bit-identical result

**Meritz**:
- Count: 34 → 34 ✓ (No change)
- Gates: PASS (34 ≥ 30, pollution 0%)
- Newline normalized in scope CSV (line 14):
  - Before: `"(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회\n한)"`
  - After: `"(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회 한)"`

---

## Meritz Not Found Case - Post-Normalization Analysis

### STEP NEXT-33 Original Finding

**Root Cause**: Newline in scope (`연간1회\n한`) ≠ Evidence text (`연간1회한`)

**Classification**: Case C (Join Failure)

### STEP NEXT-34 Post-Normalization Finding

**Status**: Still not_found (unchanged)

**New Root Cause**: Prefix mismatch (NOT newline)
- **Scope**: `(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회 한)`
- **Evidence**: `갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)`

**Key Differences**:
1. Prefix: Scope has `(20년갱신)` prefix, evidence doesn't
2. Space: Scope has `1회 한` (with space), evidence has `1회한` (no space)

**Newline Normalization**: ✅ **Successfully applied** (newline → space)

**Search Failure**: ❌ **Still fails** due to structural mismatch (prefix + space)

**Re-Classification**: **Case A (Alias Miss)**
- Coverage extracted correctly from PDF
- Evidence exists in documents
- Exact-match search correctly fails (they ARE different strings)
- Requires alias mapping (not normalization)

---

## Why Normalization Didn't "Fix" Meritz Case

**This is CORRECT behavior**:

1. **Newline normalization worked**: `\n` → ` ` (space)
2. **Search correctly failed**: Scope and evidence ARE structurally different
3. **No fuzzy matching**: We deliberately DON'T expand search logic
4. **Proper solution**: Canonical mapping / alias (not text normalization)

**Evidence**:
```
Scope:     (20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회 한)
Evidence:            갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
           ^^^^^^^^^                                           ^
           Prefix missing                                    Space mismatch
```

---

## Why This Policy Is Safe

1. **Deterministic**: Same input always produces same output
2. **Idempotent**: Applying twice = applying once
3. **Minimal**: Only whitespace normalization, no semantic changes
4. **Backward-compatible**: Existing data without newlines unchanged
5. **No search expansion**: Maintains exact-match search rigor
6. **Data hygiene**: Fixes PDF extraction artifacts only

---

## Future Recommendations

**For Meritz "(20년갱신)" Case**:
- **Option 1**: Add alias in `담보명mapping자료.xlsx`
  - Map `(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회 한)` to canonical code
- **Option 2**: Add to Step2 normalization rules (prefix stripping)
- **Not recommended**: Fuzzy search, substring matching, regex expansion

**General**:
- Monitor for similar "(N년갱신)" prefix patterns
- Consider prefix normalization in Step2 canonical mapping
- Keep exact-match search rigid (no relaxation)

---

## Verification

**Commands**:
```bash
# Verify scope normalization
grep "(20년갱신)갱신형 중증질환자(뇌혈관질환)" data/scope/meritz_scope_mapped.sanitized.csv

# Verify evidence text (no prefix)
grep "갱신형 중증질환자(뇌혈관질환)" data/evidence_text/meritz/약관/메리츠_약관.page.jsonl

# Verify search correctly fails
jq 'select(.coverage_name_raw | contains("중증질환자(뇌혈관질환)"))' \
data/compare/meritz_coverage_cards.jsonl
```

---

## Conclusion

**STEP NEXT-34 Result**:
- ✅ Newline normalization successfully implemented
- ✅ Samsung/KB results unchanged (or expected change)
- ✅ Meritz scope normalized correctly
- ❌ Meritz not_found NOT resolved (different root cause)

**Final Status**:
- **Normalization policy**: Locked and operational
- **Meritz case**: Re-classified as Case A (Alias Miss), not Case C
- **Next step**: Canonical mapping enhancement (STEP NEXT-35 candidate)

**Why This Is Acceptable**:
- Newline normalization is a data hygiene improvement
- It prevents future newline-based join failures
- The Meritz case failing is CORRECT (strings ARE different)
- Proper fix is alias mapping, not search expansion
