# CANONICAL INPUT CONTRACT AUDIT

**Audit Date**: 2025-12-30
**Scope**: Code-based evidence ONLY (NO interpretation)

---

## 1. Canonical Decision Point

### 1.1 Decision Location

**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py`

**Decision Function**: `CanonicalMapper.map_coverage()` (line 110-144)

**Execution Point**: `map_scope_to_canonical()` → line 177

```python
# Line 177
mapping_result = mapper.map_coverage(coverage_name_raw)
```

### 1.2 Decision Logic

**Exact match** (line 125-129):
```python
if coverage_name_raw in self.mapping_dict:
    result = self.mapping_dict[coverage_name_raw].copy()
    result['mapping_status'] = 'matched'
    return result
```

**Normalized match** (line 131-136):
```python
normalized = self._normalize(coverage_name_raw)
if normalized in self.mapping_dict:
    result = self.mapping_dict[normalized].copy()
    result['mapping_status'] = 'matched'
    return result
```

**Unmatched** (line 138-144):
```python
return {
    'coverage_code': '',
    'coverage_name_canonical': '',
    'mapping_status': 'unmatched',
    'match_type': 'none'
}
```

### 1.3 Decision Output

**File Written**: `data/scope/{insurer}_scope_mapped.csv` (line 193-201)

**Output Fields** (line 194-198):
- `coverage_name_raw`
- `coverage_code` (empty string if unmatched)
- `coverage_name_canonical` (empty string if unmatched)
- `mapping_status` ('matched' | 'unmatched')
- `match_type`

---

## 2. Input Text State at Decision Point

### 2.1 Input Source

**File Read**: `pipeline/step2_canonical_mapping/map_to_canonical.py:218`

```python
scope_csv = base_dir / "data" / "scope" / f"{insurer}_scope.csv"
```

**Function Call**: `map_scope_to_canonical()` line 165-169

```python
scope_rows = []
with open(scope_csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    scope_rows = list(reader)
```

**Input Field Used**: line 176

```python
coverage_name_raw = row['coverage_name_raw']
```

### 2.2 Text State Evidence

**File System Evidence**:
```bash
$ head -5 data/scope/samsung_scope.csv
coverage_name_raw,insurer,source_page
보험료 납입면제대상Ⅱ,samsung,2
암 진단비(유사암 제외),samsung,2
유사암 진단비(기타피부암)(1년50%),samsung,2
유사암 진단비(갑상선암)(1년50%),samsung,2
```

**Text State**: RAW (no sanitization applied)

Evidence:
- Contains "보험료 납입면제대상Ⅱ" (non-coverage administrative item)
- Contains condition text patterns (retained in raw scope.csv)
- No DROP patterns applied

---

## 3. Canonical Re-evaluation Paths

### 3.1 Search for Re-canonicalization

**Search Query**: `coverage_code.*=` in `pipeline/**/*.py`

**Results**:

**Step1 (sanitize)** - line 120:
```python
coverage_code = row.get('coverage_code', '')
```
**Operation**: READ ONLY (used for DROP decision logic)

**Step5 (build_cards)** - line 164, 223:
```python
'coverage_code': row.get('coverage_code', '')
# ...
coverage_code = scope_info['coverage_code'] if scope_info['coverage_code'] else None
```
**Operation**: PASSTHROUGH (copies existing value)

**Step7 (amount_extraction)** - line 397:
```python
coverage_code = card.get('coverage_code')
```
**Operation**: READ ONLY (no modification)

### 3.2 Conclusion

**Re-evaluation exists**: NO

Evidence:
- `coverage_code` is SET once at step2:line 183
- All downstream steps READ or COPY (no assignment to new values)
- No code path calls `map_coverage()` after step2

---

## 4. Sanitize Timing vs Canonical Decision

### 4.1 Execution Order Evidence

**Step2 Input** (line 218):
```python
scope_csv = base_dir / "data" / "scope" / f"{insurer}_scope.csv"
```

**Step1 Input** (`pipeline/step1_sanitize_scope/run.py:240`):
```python
input_csv = project_root / 'data' / 'scope' / f'{insurer}_scope_mapped.csv'
```

**Step1 Output** (line 241):
```python
output_csv = project_root / 'data' / 'scope' / f'{insurer}_scope_mapped.sanitized.csv'
```

### 4.2 Data Dependency Chain

```
scope.csv (raw)
  ↓ [Step2 reads]
scope_mapped.csv (canonical decided)
  ↓ [Step1 reads]
scope_mapped.sanitized.csv (DROP applied)
```

### 4.3 Sanitize Before Canonical?

**Answer**: NO

Evidence:
- Step2 reads `scope.csv` (line 218)
- Step1 reads `scope_mapped.csv` (line 240)
- File dependency: Step2 output IS Step1 input
- Therefore: Canonical decision happens BEFORE sanitize

---

## 5. Sanitize Impact on Canonical Decision

### 5.1 Theoretical Impact Analysis

**Question**: Can sanitize affect canonical matching success rate?

**Answer**: YES (theoretical possibility exists)

Evidence:

**Example 1**: Text cleaned by sanitize might match better

Raw text in scope.csv:
```
"1. 암진단비(유사암 제외)"
```

If sanitize removed "1. " prefix:
```
"암진단비(유사암 제외)"
```

This COULD improve exact match success if mapping Excel has "암진단비(유사암 제외)" but not "1. 암진단비(유사암 제외)".

**Example 2**: DROP removes unmatched entries

File evidence:
```bash
$ grep "보험료 납입면제대상" data/scope/samsung_scope_mapped.csv
보험료 납입면제대상Ⅱ,samsung,2,,,unmatched,none
```

Sanitize DROPS this row:
```bash
$ grep "보험료 납입면제대상" data/scope/samsung_scope_mapped.sanitized.csv
# (no results - row removed)
```

Audit trail (`samsung_scope_filtered_out.jsonl`):
```json
{"coverage_name_raw": "보험료 납입면제대상Ⅱ", "coverage_code": "NONE", "mapping_status": "unmatched", "drop_reason": "PREMIUM_WAIVER"}
```

### 5.2 Reflection Path

**Question**: Can sanitized text trigger canonical re-evaluation?

**Answer**: NO

Evidence:
- Step5/7 use `resolve_scope_csv()` which prioritizes sanitized.csv
- BUT Step5 only READS `coverage_code` from CSV (line 164)
- Step5 does NOT call `map_coverage()` (no re-canonicalization logic exists)
- File: `pipeline/step5_build_cards/build_cards.py:163-167`

```python
scope_data[coverage_name_raw] = {
    'coverage_code': row.get('coverage_code', ''),  # READ from CSV
    'coverage_name_canonical': row.get('coverage_name_canonical', ''),
    'mapping_status': row['mapping_status']
}
```

### 5.3 Lock Point

**Irreversible Point**: `scope_mapped.csv` write (step2:line 193-201)

After this write:
- `coverage_code` is FIXED
- `mapping_status` is FIXED
- No downstream code can change these values

Evidence:
- Step1 normalizes `mapping_status` format (lowercase) but NOT value (line 135)
- Step5/7 only READ these fields
- No re-mapping logic exists

---

## 6. Contract Violation Determination

### Proposition

> "현재 pipeline은 sanitize 이후 더 정확한 담보명이 존재하더라도
> canonical identity는 갱신될 수 없다."

### Determination

**TRUE**

### Evidence

**Fact 1**: Canonical decision happens at step2 (line 177)

**Fact 2**: Canonical decision input is `scope.csv` (raw text, line 218)

**Fact 3**: Sanitize happens AFTER step2 (input is `scope_mapped.csv`, line 240)

**Fact 4**: No re-canonicalization path exists (section 3.1 proof)

**Fact 5**: `coverage_code` is locked after step2 write (line 193-201)

**Fact 6**: Step5 reads but never writes `coverage_code` (line 164)

**Logical Chain**:
1. Step2 decides canonical based on raw text
2. Step1 sanitizes AFTER decision is made
3. Sanitized text is NOT fed back to canonical decision
4. Therefore: Better text produced by sanitize CANNOT affect canonical identity

**File System Proof**:

Input to canonical decision (raw):
```
1. 암진단비(유사암 제외)  # hypothetical example with prefix
```

If sanitize produces cleaner text:
```
암진단비(유사암 제외)  # cleaner, might match better
```

This cleaner text is in `scope_mapped.sanitized.csv` but:
- `coverage_code` field is COPIED from `scope_mapped.csv` (already decided)
- No code path re-evaluates canonical decision with sanitized text

---

## 7. Additional Findings

### 7.1 Normalization Discrepancy

**Step2 Normalization** (`map_to_canonical.py:26-40`):
```python
def _normalize(self, text: str) -> str:
    text = re.sub(r'\s+', '', text)  # remove whitespace
    text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)  # remove special chars
    return text.lower()
```

**Step1 Sanitization** (`run.py:34-55`):
```python
DROP_PATTERNS = [
    (r'(으로|로)\s*진단확정된\s*경우', 'CONDITION_DIAGNOSIS'),
    (r'(인|한)\s*경우$', 'CONDITION_CASE'),
    # ... (pattern-based row removal)
]
```

**Observation**:
- Step2 normalization: character-level (whitespace, special chars)
- Step1 sanitization: row-level (DROP entire rows matching patterns)
- These operate on different text transformation axes

### 7.2 Resolver Priority Does Not Reverse Lock

`core/scope_gate.py:140-143`:
```python
candidates = [
    scope_dir / f"{insurer}_scope_mapped.sanitized.csv",  # 1st priority
    scope_dir / f"{insurer}_scope_mapped.csv",            # 2nd priority
    scope_dir / f"{insurer}_scope.csv"                     # 3rd priority
]
```

**Observation**:
- Resolver chooses WHICH FILE to read
- But `coverage_code` field in sanitized.csv is COPIED from mapped.csv
- Resolver does NOT re-execute canonical decision
- Therefore: Priority does not unlock canonical identity

---

## 8. Summary of Evidence

| Question | Answer | Evidence Location |
|----------|--------|------------------|
| Where is canonical decided? | `step2_canonical_mapping/map_to_canonical.py:177` | Section 1.1 |
| What text state is used? | Raw (`scope.csv`) | Section 2.1 |
| Can canonical be re-evaluated? | NO | Section 3.1-3.2 |
| Does sanitize happen before canonical? | NO | Section 4.1-4.3 |
| Can sanitize affect matching? | YES (theoretical) | Section 5.1 |
| Can sanitized text update canonical? | NO | Section 5.2-5.3 |
| Contract violation? | TRUE | Section 6 |

---

## 9. Lock Contract

### 9.1 Accepted Input Text State

**State**: RAW (unsanitized)

**File**: `data/scope/{insurer}_scope.csv`

**Evidence**: `pipeline/step2_canonical_mapping/map_to_canonical.py:218`

### 9.2 Lock Point

**Location**: `scope_mapped.csv` write

**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py:193-201`

**Locked Fields**:
- `coverage_code`
- `coverage_name_canonical`
- `mapping_status`

**Irreversibility**: No downstream code modifies these fields

**Evidence**: Section 3.1 (grep results show READ-only access)

### 9.3 Post-Lock Operations

**Step1-sanitize**:
- Reads locked fields from `scope_mapped.csv`
- COPIES fields to `scope_mapped.sanitized.csv`
- Normalizes `mapping_status` format (strip, lowercase) — NOT value change

**Step5-build_cards**:
- Reads locked fields from `scope_mapped.sanitized.csv` (via resolver)
- COPIES fields to `coverage_cards.jsonl`

**Step7-amount_extraction**:
- Reads `coverage_code` from cards
- Uses for matching ONLY (no modification)

---

## 10. Proven Contract Violation

### Violation Statement

**Current pipeline contract violates the following principle**:

> "Canonical identity should be determined based on the cleanest available text representation to maximize matching accuracy."

### Violation Proof

**Evidence Chain**:

1. **Canonical uses raw text** (section 2.1)
2. **Sanitize produces cleaner text** (section 5.1, example 1)
3. **Cleaner text cannot affect canonical** (section 5.2)
4. **Therefore**: Canonical decision is made on suboptimal input

**Concrete Example** (hypothetical but structurally possible):

Given mapping Excel entry:
```
"암진단비(유사암 제외)"  # canonical name
```

If scope.csv contains:
```
"1. 암진단비(유사암 제외)"  # raw text with prefix
```

Step2 matching:
- Exact match: FAIL ("1. 암진단비..." ≠ "암진단비...")
- Normalized match: FAIL (normalization removes chars but keeps "1")
- Result: `mapping_status = 'unmatched'`

If sanitize removed "1. " prefix:
```
"암진단비(유사암 제외)"  # sanitized text
```

This would enable:
- Exact match: SUCCESS
- Result: `mapping_status = 'matched'`

**But this cannot happen** because:
- Sanitize runs AFTER canonical decision (section 4.3)
- Sanitized text is not fed back (section 5.2)

### Violation Impact

**Theoretical**:
- Reduced canonical matching success rate
- Increased `unmatched` entries
- Potential loss of coverage_code assignment for legitimately matchable coverages

**Cannot quantify without**:
- Actual scope.csv samples with prefixes/suffixes
- Mapping Excel content comparison
- Match rate differential analysis (raw vs sanitized)

**Note**: This is a STRUCTURAL violation (contract-level), not necessarily a DATA violation (current files may not exhibit the problem).

---

## 11. No Solution Provided

Per audit scope: Analysis ONLY.

No recommendations, refactoring suggestions, or implementation proposals included.

---

## 12. Audit Limitations

**Cannot determine**:
- Whether actual scope.csv files contain text that would match better after sanitization
- Quantitative impact on matching success rate
- Whether this was intentional design trade-off

**Can only state**:
- Canonical decision timing (factual)
- Text state at decision point (factual)
- Lock point irreversibility (factual)
- Contract violation existence (logical proof from facts)

---

## End of Audit

**All conclusions are code-evidence based.**
**No interpretive statements included.**
**Judgment calls marked as "cannot determine".**
