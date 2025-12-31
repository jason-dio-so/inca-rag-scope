# STEP NEXT-27 — Canonical Matching Recovery (Evidence-Bound)

**Implementation Date**: 2025-12-30
**Method**: Suffix-normalized matching within Step2 canonical mapping

---

## 1. Problem Statement

### Root Cause (STEP NEXT-24 Finding)

**Current Pipeline Order**:
```
raw scope.csv
  → Step2 canonical mapping (LOCK canonical decision)
  → Step1 sanitize (remove suffix patterns)
  → sanitized.csv
```

**Issue**: Suffix patterns present during Step2 canonical matching block matches that would succeed if suffix were removed.

**Example**:
- Proposal text: `뇌혈관질환 진단비(1년50%)`
- Excel canonical: `뇌혈관질환 진단비`
- Step2 result: **UNMATCHED** (suffix `(1년50%)` blocks exact match)
- After sanitize: Suffix removed, but **too late** (canonical already locked as "unmatched")

---

## 2. Solution Design

### OPTION A — Canonical-Aware Suffix Normalization (Implemented)

**Approach**: Add suffix-normalized matching tier **within** Step2 canonical mapping logic.

**Advantages**:
- ✅ Minimal code change (Step2 only)
- ✅ No pipeline restructuring
- ✅ Preserves raw coverage_name_raw (original text intact)
- ✅ Evidence-bound (only patterns verified in STEP NEXT-26β)

**Implementation**:
```python
# Step2 matching sequence (UPDATED):
1. Exact match (unchanged)
2. Normalized match (unchanged)
3. Suffix-normalized match ← NEW
   - Remove evidence-verified suffix patterns
   - Retry exact + normalized match
4. Unmatched
```

---

## 3. Allowed Suffix Patterns (Evidence-Verified)

### Pattern 1: Period/Occurrence Metadata
**Regex**: `\((?:\d+년\d+%?|\d+년주기|최초\d+회한)\)$`

**Examples**:
- `(1년50%)` — period with percentage
- `(1년주기)` — period cycle
- `(최초1회한)` — occurrence limit

**Coverage**:
- samsung: 뇌혈관질환 진단비`(1년50%)`, 허혈성심장질환 진단비`(1년50%)`
- samsung: [갱신형] 표적항암약물허가 치료비`(1년50%)`
- samsung: 2대주요기관질병 관혈수술비Ⅱ`(1년50%)`, 2대주요기관질병 비관혈수술비Ⅱ`(1년50%)`

### Pattern 2: Duration Range
**Regex**: `\(\d+일-\d+일\)$`

**Examples**:
- `(1일-180일)` — duration range

**Coverage**:
- lotte: 상해입원비`(1일-180일)`

### Pattern 3: Renewal Metadata
**Regex**: `\(갱신형_\d+년\)$`

**Examples**:
- `(갱신형_10년)` — renewal period

**Coverage**:
- heungkuk: [갱신형]표적항암약물허가치료비Ⅱ`(갱신형_10년)`

### Pattern 4: Condition Specifier
**Regex**: `\([^)]+질환\)$|\(뇌졸중\)$`

**Examples**:
- `(특정심장질환)` — condition specifier
- `(뇌졸중)` — condition specifier

**Coverage**:
- kb: 혈전용해치료비Ⅱ(최초1회한)`(특정심장질환)`
- kb: 혈전용해치료비Ⅱ(최초1회한)`(뇌졸중)`

**NOTE**: KB cases map to same canonical `혈전용해치료비Ⅲ(최초1회한)` (Excel base coverage).

---

## 4. Forbidden Patterns (Rejected)

### Pattern: Diagnosis Type — `(재진단형)`

**Coverage**: hanwha — 뇌출혈 진단비`(재진단형)`

**Status**: ❌ **ARTIFACT_CASE** (STEP NEXT-26β)

**Evidence**: NOT FOUND in proposal PDF

**Reason**: Scope extraction error (text merged from different sections or product variant mismatch)

**Action**: Excluded from allowed patterns

---

## 5. Implementation Details

### Code Changes

**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py`

**New Method**: `_remove_suffix_patterns(text: str) -> Optional[str]`
```python
def _remove_suffix_patterns(self, text: str) -> Optional[str]:
    """
    Remove trailing suffix patterns (condition/period/limit metadata)

    Returns:
        Suffix-removed text, or None if no pattern matched
    """
    # Pattern 1: Period/occurrence metadata
    pattern_period = r'\((?:\d+년\d+%?|\d+년주기|최초\d+회한)\)$'
    text_stripped = re.sub(pattern_period, '', text).strip()
    if text_stripped != text:
        return text_stripped

    # Pattern 2: Duration range
    pattern_duration = r'\(\d+일-\d+일\)$'
    text_stripped = re.sub(pattern_duration, '', text).strip()
    if text_stripped != text:
        return text_stripped

    # Pattern 3: Renewal metadata
    pattern_renewal = r'\(갱신형_\d+년\)$'
    text_stripped = re.sub(pattern_renewal, '', text).strip()
    if text_stripped != text:
        return text_stripped

    # Pattern 4: Condition specifier
    pattern_condition = r'\([^)]+질환\)$|\(뇌졸중\)$'
    text_stripped = re.sub(pattern_condition, '', text).strip()
    if text_stripped != text:
        return text_stripped

    return None
```

**Updated Method**: `map_coverage(coverage_name_raw: str) -> Dict`
```python
def map_coverage(self, coverage_name_raw: str) -> Dict:
    # 1. Exact match (unchanged)
    if coverage_name_raw in self.mapping_dict:
        result = self.mapping_dict[coverage_name_raw].copy()
        result['mapping_status'] = 'matched'
        return result

    # 2. Normalized match (unchanged)
    normalized = self._normalize(coverage_name_raw)
    if normalized in self.mapping_dict:
        result = self.mapping_dict[normalized].copy()
        result['mapping_status'] = 'matched'
        return result

    # 3. Suffix-normalized match (NEW)
    suffix_removed = self._remove_suffix_patterns(coverage_name_raw)
    if suffix_removed:
        # Try exact match on suffix-removed string
        if suffix_removed in self.mapping_dict:
            result = self.mapping_dict[suffix_removed].copy()
            result['mapping_status'] = 'matched'
            result['match_type'] = 'suffix_normalized'
            return result

        # Try normalized match on suffix-removed string
        normalized_suffix_removed = self._normalize(suffix_removed)
        if normalized_suffix_removed in self.mapping_dict:
            result = self.mapping_dict[normalized_suffix_removed].copy()
            result['mapping_status'] = 'matched'
            result['match_type'] = 'suffix_normalized'
            return result

    # 4. Unmatched
    return {
        'coverage_code': '',
        'coverage_name_canonical': '',
        'mapping_status': 'unmatched',
        'match_type': 'none'
    }
```

---

## 6. Verification Results

### VALID_CASE Recovery (9 cases from STEP NEXT-26β)

| Insurer | Raw scope.csv | Suffix Removed | Before | After | Coverage Code | Match Type |
|---------|---------------|----------------|--------|-------|---------------|------------|
| samsung | 뇌혈관질환 진단비(1년50%) | `(1년50%)` | unmatched | ✅ matched | A4101 | suffix_normalized |
| samsung | 허혈성심장질환 진단비(1년50%) | `(1년50%)` | unmatched | ✅ matched | A4105 | suffix_normalized |
| samsung | [갱신형] 표적항암약물허가 치료비(1년50%) | `(1년50%)` | unmatched | ✅ matched | A9619_1 | suffix_normalized |
| samsung | 2대주요기관질병 관혈수술비Ⅱ(1년50%) | `(1년50%)` | unmatched | ✅ matched | A5104_1 | suffix_normalized |
| samsung | 2대주요기관질병 비관혈수술비Ⅱ(1년50%) | `(1년50%)` | unmatched | ✅ matched | A5104_1 | suffix_normalized |
| kb | 혈전용해치료비Ⅱ(최초1회한)(특정심장질환) | `(특정심장질환)` | unmatched | ✅ matched** | A9640_1 | suffix_normalized |
| kb | 혈전용해치료비Ⅱ(최초1회한)(뇌졸중) | `(뇌졸중)` | unmatched | ✅ matched** | A9640_1 | suffix_normalized |
| lotte | 상해입원비(1일-180일) | `(1일-180일)` | unmatched | ✅ matched | A6300_1 | suffix_normalized |
| heungkuk | [갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년) | `(갱신형_10년)` | unmatched | ✅ matched | A9619_1 | suffix_normalized |

**Total Recovered**: 9 / 9 VALID_CASE instances (100%) ← **STEP NEXT-28 completed KB recovery**

**KB Recovery Note**: KB scope.csv was initially corrupted (4 lines, 3 garbage rows). KB VALID_CASE instances were recovered in STEP NEXT-28 by regenerating kb_scope.csv from proposal PDF. See `docs/architecture/STEP_NEXT_28_KB_SCOPE_RECOVERY.md` for details.

---

### Step2 Matching Statistics (Before vs After)

| Insurer | Before Matched | After Matched | Delta | Total Rows | Match Rate Improvement |
|---------|----------------|---------------|-------|------------|----------------------|
| samsung | 33 | 38 | +5 | 41 | +12.2%p (80.5% → 92.7%) |
| db | 26 | 26 | 0 | 31 | No change (83.9%) |
| meritz | 26 | 26 | 0 | 34 | No change (76.5%) |
| hyundai | 25 | 25 | 0 | 37 | No change (67.6%) |
| lotte | 30 | 31 | +1 | 37 | +2.7%p (81.1% → 83.8%) |
| heungkuk | 30 | 31 | +1 | 36 | +2.8%p (83.3% → 86.1%) |
| kb | 0** | 27** | +27** | 45 | **Recovered in STEP NEXT-28** |
| hanwha | (not re-run) | (not re-run) | N/A | 37 | (unchanged) |

**Total Improvement**: +34 matched coverages across 4 insurers (samsung +5, lotte +1, heungkuk +1, kb +27**)

**Note**: KB improvement includes scope regeneration (STEP NEXT-28). Without scope regeneration, KB would show 0 improvement due to input file corruption.

**No Regression**: 0 existing matches broken (db, meritz, hyundai unchanged)

---

## 7. Why This Approach Works

### Structural Correctness

**Coverage Base Noun Preservation**: All suffix patterns are **metadata** (period/condition/limit), not part of core coverage definition.

**Examples**:
- `뇌혈관질환 진단비` ← base coverage (what is covered)
- `(1년50%)` ← metadata (when/how much/how often)

**Excel Mapping Strategy**: Canonical keys use base coverage WITHOUT metadata suffixes.

**Evidence**: All 9 VALID_CASE instances confirmed via exact grep against proposal PDFs (STEP NEXT-26β).

---

### Why NOT Fuzzy Matching

**Fuzzy matching REJECTED**:
- ❌ Could match unrelated coverages (false positives)
- ❌ No evidence bound (arbitrary similarity threshold)
- ❌ Violates CLAUDE.md rules (exact/normalized only)

**Suffix-normalized matching APPROVED**:
- ✅ Pattern-based (deterministic, not similarity-based)
- ✅ Evidence-bound (only patterns verified in PDFs)
- ✅ Preserves coverage semantics (base noun unchanged)
- ✅ Minimal scope (9 cases, 4 insurers, 11.25% of unmatched)

---

## 8. Limitations & Known Issues

### 1. KB Scope Corruption (RESOLVED in STEP NEXT-28)

**Issue**: `data/scope/kb_scope.csv` contained only 3 rows (corrupted/minimal).

**Impact**: KB VALID_CASE instances (혈전용해치료비Ⅱ(최초1회한)(특정심장질환), 혈전용해치료비Ⅱ(최초1회한)(뇌졸중)) NOT recovered in STEP-27.

**Resolution**: ✅ **COMPLETED in STEP NEXT-28**
- KB scope regenerated from proposal PDF: 4 lines → 46 lines (45 coverages)
- Step2/Step1/Step5 re-executed with STEP NEXT-27 suffix-normalized logic
- Both KB VALID_CASE instances recovered with `coverage_code = A9640_1, match_type = suffix_normalized`
- See `docs/architecture/STEP_NEXT_28_KB_SCOPE_RECOVERY.md` for full recovery documentation

---

### 2. Hanwha Artifact Case

**Coverage**: 뇌출혈 진단비(재진단형)

**Status**: ARTIFACT_CASE (STEP NEXT-26β)

**Evidence**: NOT FOUND in hanwha proposal PDF

**Action**: Pattern `(재진단형)` EXCLUDED from allowed patterns

**Implication**: Artifact cases will remain unmatched (correct behavior).

---

### 3. Pattern Specificity

**Current Patterns**: Evidence-verified from 9 VALID_CASE instances

**Limitation**: May not cover all possible suffix patterns in future data

**Mitigation**:
- Pattern addition requires evidence verification (grep against proposal PDFs)
- No speculative pattern expansion allowed (STEP NEXT-27 contract)

---

## 9. Prohibited Actions (Hard Stop)

### What This Implementation Does NOT Do

❌ **No Sanitize Logic Reuse**: Step2 uses its own suffix patterns (evidence-bound), NOT Step1 sanitize regex.

❌ **No Fuzzy Matching**: All matching is exact/normalized/suffix-normalized (pattern-based, deterministic).

❌ **No Amount/Premium Reference**: Suffix removal based on pattern only, NO column inspection.

❌ **No Re-evaluation of Existing Matched Rows**: Suffix-normalized matching only attempted if Tier 1/2 fail.

❌ **No Canonical Re-assignment in Step5/7**: Coverage_code locked at Step2, downstream steps read-only.

---

## 10. Success Criteria (DoD)

### Definition of Done

✅ **VALID_CASE Recovery**: 9 / 9 instances recovered (100%)
- samsung: 5/5 ✅
- lotte: 1/1 ✅
- heungkuk: 1/1 ✅
- kb: 2/2 ✅ (recovered in STEP NEXT-28 after scope regeneration)

✅ **No Regression**: 0 existing matches broken (db, meritz, hyundai unchanged)

✅ **SSOT Preservation**: Coverage_cards.jsonl unchanged (will be regenerated in next pipeline run)

✅ **Documentation**: Evidence table (STEP NEXT-26β), implementation guide (this document), prohibited actions (section 9)

---

## 11. Next Steps (Post-STEP-27)

### Immediate Actions

1. **Regenerate Sanitized Scope** (Step1):
   - Run: `python -m pipeline.step1_sanitize_scope.run --all`
   - Input: `*_scope_mapped.csv` (updated with suffix_normalized matches)
   - Output: `*_scope_mapped.sanitized.csv`

2. **Regenerate Coverage Cards** (Step5):
   - Run: `python -m pipeline.step5_build_cards.build_cards --all`
   - Input: sanitized scope files
   - Output: `data/compare/*_coverage_cards.jsonl` (SSOT update)

3. **Verify Coverage_Cards**:
   - Check: 7 new matched coverages with `match_type: suffix_normalized`
   - Check: Original coverage_name_raw preserved (NOT suffix-removed)

### Optional Follow-up

**STEP NEXT-28** (if required): KB Scope Reconstruction
- Recover full kb_scope.csv from coverage_cards.jsonl or re-extract from proposal PDF
- Re-run Step2 for KB with suffix-normalized logic
- Target: +2 matched (혈전용해치료비Ⅱ cases)

---

## 12. Evidence Audit Trail

**Evidence Source**: STEP NEXT-26β (docs/architecture/STEP_NEXT_26B_EVIDENCE_VERIFIED.md)

**Verification Method**: Direct grep against `data/evidence_text/{insurer}/가입설계서/*.page.jsonl`

**VALID_CASE Rate**: 90% (9/10 cases verified)

**ARTIFACT_CASE Rate**: 10% (1/10 cases rejected)

**Structural Finding**: All VALID_CASE instances follow consistent suffix pattern (metadata in trailing parentheses).

---

## End of Document

**STEP NEXT-27 Status**: ✅ **COMPLETE**

**Canonical Recovery**: 9 / 9 VALID_CASE instances (100%) ← **STEP NEXT-28 completed KB recovery**

**Regression**: 0 cases broken

**Code Change**: 1 file modified (`pipeline/step2_canonical_mapping/map_to_canonical.py`)

**Documentation**:
- This file (STEP_NEXT_27_CANONICAL_SUFFIX_RECOVERY.md)
- KB recovery: `docs/architecture/STEP_NEXT_28_KB_SCOPE_RECOVERY.md`
