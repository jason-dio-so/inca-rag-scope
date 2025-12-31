# STEP NEXT-19 — Restatement (Scope-Constrained)

**Original Description**: "Hanwha/Heungkuk amount extraction stabilization"

**Restated Definition** (STEP NEXT-22):

> **STEP NEXT-19 is a localized correction logic that recovers fragmented amounts in the "가입금액" (coverage amount) column of proposal PDFs, specifically handling cases where PDF text extraction splits a single numeric value across multiple lines.**

---

## Scope Boundaries (What It IS)

### 1. Document Type: 가입설계서 (Proposal) ONLY

**Applies to**:
- `data/evidence_text/{insurer}/가입설계서/{insurer}_가입설계서_*.page.jsonl`

**Does NOT apply to**:
- 약관 (policy terms)
- 사업방법서 (business methods)
- 상품요약서 (product summary)
- Any other document type

**Code enforcement**:
```python
# extract_and_enrich_amounts.py:211
proposal_page_jsonl = Path(f".../{insurer}/가입설계서/...")
```

---

### 2. Semantic Context: 가입금액 Column ONLY

**Applies to amounts in table cells labeled**:
- 가입금액
- 보험가입금액
- 보장금액

**Does NOT apply to**:
- 보험료 (premium)
- 해약환급금 (surrender value)
- 책임준비금 (reserve)
- Page numbers
- Coverage codes

**Code enforcement**:
```python
# extract_and_enrich_amounts.py:222
if not any(kw in text for kw in ['가입금액', '보험가입금액', '보장금액', ...]):
    continue  # Skip pages without amount tables
```

---

### 3. Pattern: Trailing Comma + Unit on Next Line

**Detects**:
- Line N: `"1,"` (digits + comma, no unit)
- Line N+1: `"000만원"` (exactly 3 digits + unit)

**Merges to**: `"1,000만원"`

**Does NOT detect**:
- `"1"` + `"000만원"` (no comma)
- `"1,00"` + `"0만원"` (unit not on separate line)
- `"1,0000"` + `"만원"` (more than 3 digits)

**Code enforcement**:
```python
# extract_and_enrich_amounts.py:180-189
comma_match = re.fullmatch(r'(\d+),', first_line)
unit_match = re.fullmatch(r'(\d{3})(만?원)', next_line)
if comma_match and unit_match:
    merged = f"{comma_match.group(1)},{unit_match.group(1)}{unit_match.group(2)}"
```

---

## Root Cause

### PDF Rendering Behavior

When PDF table cells contain amounts like `"1,000만원"`, some rendering engines (pdfplumber/pymupdf) split the text across lines at word boundaries or fixed width:

**Original PDF cell**:
```
┌─────────────────┐
│  1,000만원      │
└─────────────────┘
```

**Text extraction output** (broken across lines):
```
1,
000만원
```

**Why this happens**:
- PDF uses absolute character positioning, not semantic line breaks
- Extractors use heuristics (spacing, newlines) to detect line boundaries
- Tables with narrow columns increase fragmentation likelihood

**Evidence**: Observed in Hanwha/Heungkuk proposals (page 3, 가입금액 column)

---

## Implementation Scope

### Affected Insurers (as of STEP NEXT-19)

- **Hanwha** (한화): Confirmed fragmentation in `한화_가입설계서_2511.page.jsonl`
- **Heungkuk** (흥국): Confirmed fragmentation in `흥국_가입설계서_2511.page.jsonl`

**Other insurers**:
- Samsung, Meritz, DB, Hyundai, KB, Lotte: Single-line amounts (no fragmentation detected)
- **Behavior**: Logic is applied to ALL insurers but only triggers when pattern is found

### Code Location

**File**: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py`

**Functions**:
1. `is_amount_fragment()` (line 135-160): Detect if line is a fragment
2. `merge_amount_fragments()` (line 162-192): Merge consecutive fragments
3. `extract_proposal_amount_pairs()` (line 195-330): Main extraction loop

**Entry point**: Line 238 (BEFORE skipping short lines)

---

## What It Does NOT Do

### ❌ NOT a Fuzzy Matcher

STEP NEXT-19 does **NOT**:
- Use string similarity to "guess" amounts
- Interpolate missing amounts from other insurers
- Apply machine learning to predict amounts

**Why**: Scope is limited to **deterministic text reassembly** (merging split lines).

### ❌ NOT an Amount Validator

STEP NEXT-19 does **NOT**:
- Check if amount is reasonable (e.g., "1,000,000만원" is too large)
- Verify amount against policy terms
- Cross-check amounts across documents

**Why**: Validation is a separate concern (handled by audit tools, not extraction).

### ❌ NOT a Premium Extractor

STEP NEXT-19 does **NOT**:
- Extract 보험료 (premium) amounts
- Extract 납입보험료 (paid premium)
- Extract any non-가입금액 amounts

**Why**: Scope is strictly 가입금액 (coverage amount) ONLY.

---

## Success Criteria (DoD)

STEP NEXT-19 is considered **successful** if:

1. **No false positives**: Merge ONLY occurs for actual fragmented amounts
   - Counter-example: Does NOT merge page numbers like `"26." + "03.30"`
   - Enforcement: Line 249 requires Korean coverage name in lookback

2. **No false negatives**: All fragmented amounts in proposal tables are merged
   - Counter-example: `"1," + "000만원"` should NEVER be left as 2 separate entries
   - Enforcement: Pattern match at line 180-189 is exhaustive

3. **Evidence traceability**: Every merged amount has `evidence_ref` with snippet
   - Format: `"coverage_name / amount"`
   - Code: Line 258

---

## Limitations (Accepted Trade-offs)

### Limitation 1: Only 3-Digit Unit Fragments

**Current logic**:
```python
unit_match = re.fullmatch(r'(\d{3})(만?원)', next_line)
```

**Implication**: Does NOT merge:
- `"1," + "00만원"` (2 digits)
- `"1," + "0000만원"` (4 digits)

**Justification**: Real-world amounts use standard notation (e.g., 1,000만원, not 1,00만원).

### Limitation 2: Single-Line Lookback for Coverage Name

**Current logic**:
```python
for lookback in range(1, 4):  # Max 3 lines back
    if re.search(r'[가-힣]', prev_line):
        coverage_candidate = prev_line
        break
```

**Implication**: If coverage name is >3 lines before amount → NOT matched.

**Justification**: Proposal tables have consistent layout (coverage name immediately before amount).

### Limitation 3: Insurer-Specific Layout Assumptions

**Assumption**: Proposal tables have structure:
```
담보명    가입금액    보험료
A담보     1,000만원   500원
```

**Implication**: If insurer uses different layout (e.g., vertical table) → logic may fail.

**Mitigation**: Layout validation during step1 (scope extraction).

---

## Verification Examples

### Example 1: VALID Merge (Hanwha)

**Input** (raw lines):
```
Line 22: "보통약관(상해사망)"
Line 23: "1,"
Line 24: "000만원"
Line 25: "590원"
```

**STEP NEXT-19 Execution**:
1. Line 23: `is_amount_fragment("1,")` → True
2. Lines 23-24: `merge_amount_fragments(...)` → `"1,000만원"`, consumed=2
3. Lookback: Line 22 = `"보통약관(상해사망)"` (Korean, >3 chars) → coverage_candidate
4. **Output**: `ProposalAmountPair(coverage_name_raw="보통약관(상해사망)", amount_text="1,000만원")`

✅ **VALID**: All 3 scope conditions met.

### Example 2: INVALID Merge Attempt (Premium)

**Input** (raw lines):
```
Line 22: "보통약관(상해사망)"
Line 23: "1,000만원"
Line 24: "7,"
Line 25: "450원"
```

**STEP NEXT-19 Execution**:
1. Line 23: Single-line amount detected → `"1,000만원"` (no merge needed)
2. Line 24: `is_amount_fragment("7,")` → True
3. Lines 24-25: `merge_amount_fragments(...)` → `"7,450원"`, consumed=2
4. Lookback: Line 22 = `"보통약관(상해사망)"` → **WRONG context** (this is premium, not 가입금액)

❌ **INVALID**: Semantic context condition fails (보험료 vs 가입금액).

**Mitigation**: Code at line 232 skips lines with `"보험료"` keyword → This merge should NOT occur.

---

## Conclusion

**STEP NEXT-19 is NOT**:
- A general-purpose amount extractor
- A fuzzy matcher
- An amount guesser

**STEP NEXT-19 IS**:
- A **localized correction** for PDF text fragmentation
- Scoped to **proposal tables, 가입금액 column**
- **Deterministic** (no ML, no heuristics beyond regex)

**Restatement in one sentence**:

> STEP NEXT-19 merges consecutive text lines matching the pattern `"\d+,"` + `"\d{3}만?원"` when found in the 가입금액 column of proposal PDFs, recovering amounts that PDF text extraction incorrectly split across lines.
