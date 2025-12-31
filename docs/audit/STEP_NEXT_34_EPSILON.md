# STEP NEXT-34-ε Emergency Rollback & Re-implementation

**Date**: 2025-12-31
**Purpose**: Fix constitutional violation from STEP NEXT-34 (Samsung 42→41 regression)
**Strategy**: Revert unsafe normalization, implement newline-only removal as search_key

---

## Problem Summary

**STEP NEXT-34 Constitutional Violation**:
- Changed `coverage_name_raw` (SSOT) by applying normalization **before** validation
- Caused Samsung count change: 42 → 41 (duplicate collapsed)
- Violated constitution: "coverage_name_raw must remain unchanged"

**Root Cause**:
- Normalization included space collapse + strip, not just newline removal
- Applied normalization to `coverage_name_raw` directly, changing SSOT
- No separation between raw (SSOT) and search_key (derived value)

---

## Solution Architecture

**Principle**: Raw (SSOT) + Search_Key (Derived)

```
Step1 Extract
  ↓
  coverage_name_raw (SSOT, unchanged, includes \n)
  coverage_name_search_key (derived, newline removed only)
  ↓
Step2 Canonical Mapping (preserves both columns)
  ↓
Step1 Sanitize (preserves both columns)
  ↓
Step4 Evidence Search (uses search_key for exact match)
```

---

## Implementation

### 1. Revert STEP NEXT-34 Commits

```bash
git revert 333457f  # fix(step-next-34): normalize scope newline...
git revert b191f69  # docs(step-next-34): update STATUS...
```

**Result**: Samsung/KB/Meritz counts restored to original (42/45/34)

---

### 2. New Function: `normalize_newline_only()`

**Location**: `pipeline/step1_extract_scope/hardening.py`

```python
def normalize_newline_only(s: str) -> str:
    """
    STEP NEXT-34-ε: Newline-only removal for search key stability

    Deterministic + idempotent.
    Allowed: remove '\n' and '\r\n' only.
    Forbidden: strip(), collapse spaces, regex \s+, other normalization.
    """
    if s is None:
        return s
    return s.replace("\r\n", "").replace("\n", "")
```

**Explicitly Forbidden**:
- ❌ `.strip()` (leading/trailing whitespace removal)
- ❌ `re.sub(r'\s+', ' ')` (space collapse)
- ❌ Any other text transformation
- ✅ Only `\n` and `\r\n` deletion (no space substitution)

---

### 3. Step1 Output: Add `coverage_name_search_key` Column

**File**: `pipeline/step1_extract_scope/run.py`

**Before**:
```csv
coverage_name_raw,insurer,source_page
```

**After**:
```csv
coverage_name_raw,insurer,source_page,coverage_name_search_key
"(20년갱신)...(연간1회\n한)",meritz,3,(20년갱신)...(연간1회한)
```

**Key Point**:
- `coverage_name_raw` = SSOT (unchanged, includes `\n`)
- `coverage_name_search_key` = Derived (newline removed)

---

### 4. Step2 & Step1_sanitize: Preserve `coverage_name_search_key`

**Step2** (`pipeline/step2_canonical_mapping/map_to_canonical.py`):
- Reads `coverage_name_search_key` from Step1 output
- Preserves it in mapped CSV output
- Dynamically adds to fieldnames if present

**Step1_sanitize** (`pipeline/step1_sanitize_scope/run.py`):
- Already preserves all fieldnames dynamically
- No changes needed

---

### 5. Step4: Use `coverage_name_search_key` for Exact Match

**File**: `pipeline/step4_evidence_search/search_evidence.py`

**Changes**:
1. Added `coverage_name_search_key` parameter to `search_coverage_evidence()`
2. Use `search_key` (fallback to `raw` if None) for keyword construction
3. Read `coverage_name_search_key` from scope CSV in main loop

**Search Logic**:
```python
# STEP NEXT-34-ε: Use search_key for exact match (fallback to raw if None)
search_raw = coverage_name_search_key if coverage_name_search_key else coverage_name_raw

# Matched: search both canonical + search_raw
# Unmatched: search only search_raw
keywords = [coverage_name_canonical, search_raw] if matched else [search_raw]
```

---

## Verification Results

### Step1 Counts (Unchanged ✓)

| Insurer | Before STEP-34-ε | After STEP-34-ε | Status |
|---------|------------------|-----------------|--------|
| Samsung | 42 | 42 | ✓ PASS |
| KB | 45 | 45 | ✓ PASS |
| Meritz | 34 | 34 | ✓ PASS |

All pollution rates: 0.00% ✓

---

### Meritz Full Pipeline Rebuild

**Scope CSV** (line 14-15):
```csv
coverage_name_raw,coverage_name_search_key
"(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회
한)",(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
```

**Newline Normalization**: ✅ Success
- Raw: `연간1회\n한` (with newline)
- Search key: `연간1회한` (newline removed)

**Step4 Evidence Search**: 약관:0 사업방법서:0 상품요약서:0
**Step5 Evidence Status**: `not_found`

---

### Meritz Case Analysis: Why Still Not_Found (CORRECT Behavior)

**Scope search_key**:
```
(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
```

**Evidence text** (약관 p21, 상품요약서 p63):
```
갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
^^^^^^^^^
Missing prefix: "(20년갱신)"
```

**Key Differences**:
1. Prefix mismatch: Scope has `(20년갱신)`, evidence doesn't
2. Newline normalized: `\n` → `` (deletion, not space)

**Classification**: Case A (Alias Miss)
- Newline normalization **worked correctly**
- Exact match **correctly failed** (strings ARE different)
- This is **NOT** a normalization problem
- Proper fix: Canonical mapping / alias (not search expansion)

---

## Why This Is Safe

### Constitutional Compliance

1. **Raw SSOT Unchanged**: ✓
   - `coverage_name_raw` never modified
   - Step1 counts unchanged (42/45/34)
   - Deduplication unchanged

2. **No Search Expansion**: ✓
   - Still exact match only
   - No fuzzy matching
   - No prefix stripping
   - No substring matching

3. **Deterministic**: ✓
   - `normalize_newline_only()` is idempotent
   - Same input → same output
   - Newline removal only (no heuristics)

4. **Backward Compatible**: ✓
   - Old CSVs without `search_key` still work (fallback to `raw`)
   - Step2/Step1_sanitize preserve new column automatically

---

## Impact Summary

### Files Modified

**Core Pipeline**:
- `pipeline/step1_extract_scope/hardening.py` (+normalize_newline_only function)
- `pipeline/step1_extract_scope/run.py` (+search_key generation in save_to_csv)
- `pipeline/step2_canonical_mapping/map_to_canonical.py` (+search_key preservation)
- `pipeline/step4_evidence_search/search_evidence.py` (+search_key parameter & usage)

**Data Files**:
- ❌ No data files committed (as required)
- All insurers regenerated with new schema

---

### Gates Status

**All Quality Gates**: ✓ PASS

| Gate | Samsung | KB | Meritz |
|------|---------|-----|--------|
| Count (≥30) | ✓ 42 | ✓ 45 | ✓ 34 |
| Pollution (<5%) | ✓ 0% | ✓ 0% | ✓ 0% |

---

## What Changed vs STEP NEXT-34

| Aspect | STEP NEXT-34 (Unsafe) | STEP NEXT-34-ε (Safe) |
|--------|----------------------|---------------------|
| Normalization | Space collapse + strip + newline | Newline deletion only |
| Application | Overwrote `coverage_name_raw` | Separate `coverage_name_search_key` |
| SSOT Impact | Changed (42→41) | Unchanged (42) |
| Search Usage | Applied before validation | Applied only in Step4 |
| Constitution | ❌ Violated | ✓ Compliant |

---

## Future Recommendations

### For Meritz "(20년갱신)" Case

**Not Recommended**:
- ❌ Prefix stripping normalization (changes meaning)
- ❌ Fuzzy matching (widens search)
- ❌ Substring matching (false positives)

**Recommended**:
- ✅ Add alias in `담보명mapping자료.xlsx`
  - Map `(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회 한)` → canonical code
- ✅ Monitor for similar "(N년갱신)" prefix patterns
- ✅ Keep exact-match search rigid (no relaxation)

---

## Conclusion

**STEP NEXT-34-ε Result**:
- ✅ Constitutional violation fixed (Samsung 42 restored)
- ✅ Raw SSOT unchanged across all insurers
- ✅ Newline normalization implemented safely (search_key separation)
- ✅ Meritz case correctly classified as Case A (Alias Miss)
- ✅ No search expansion (exact match rigor maintained)

**Final Status**:
- Newline normalization: **Operational & Safe**
- Meritz not_found case: **CORRECT behavior** (requires alias mapping)
- Next step: Canonical mapping enhancement (if needed)

**Why Meritz Case Remains Not_Found**:
- Newline removal worked: `\n` → `` (deleted)
- Exact match correctly failed: Prefix mismatch `(20년갱신)갱신형...` vs `갱신형...`
- This is **proper behavior** per constitution (no fuzzy matching)
- Proper fix: Alias mapping in Step2, not normalization in Step1

---

**DoD**: ✅ All Complete
- Revert commits: ✓
- Newline-only function: ✓
- search_key separation: ✓
- Step4 wiring: ✓
- Counts unchanged: ✓ (42/45/34)
- No data committed: ✓
- Constitution compliant: ✓
