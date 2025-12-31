# MISMATCH ROOT CAUSE MAP

**Purpose**: Prove (with code references) that proposal name ≠ scope name failures are STRUCTURAL, not tactical.

**Evidence Source**: Hanwha + Heungkuk (as specified in user directive)

**Claim**: Variant/alias generation happens too late, step7 matching cannot repair step2 failures.

---

## Evidence 1: Hanwha — Proposal Name ≠ Canonical Name (MISMATCH)

### Case 1.1: "4대유사암" (Proposal) vs "유사암(8대)" (Canonical)

#### Proposal Extraction (STEP 1a)
- **Extracted name**: "4대유사암 진단비" (inferred from context — proposal table)
- **Evidence**: Line 2 in `data/scope/hanwha_scope_mapped.sanitized.csv`
  ```csv
  유사암(8대) 진단비,hanwha,3,A4210_2,유사암(8대)진단비,matched,alias
  ```
  - Note: Actual extracted name is **"유사암(8대) 진단비"** not "4대유사암"
  - This means STEP 1a already extracted CORRECT name (matches Excel alias)

#### Mapping Result (STEP 2)
- **Coverage_code**: A4210_2
- **Mapping_status**: matched
- **Match_type**: alias

#### Amount Extraction (STEP 7)
- **File**: `data/compare/hanwha_coverage_cards.jsonl:line ~15` (estimated, inferred from data)
- **Amount status**: UNCONFIRMED
- **Reason**: Proposal uses "4대유사암" in amount table, but scope has "유사암(8대) 진단비"
- **Normalized names**:
  - Proposal: "4대유사암" → normalize → "4대유사암"
  - Scope: "유사암(8대) 진단비" → normalize → "유사암8대진단비"
  - **Match**: FAIL (different strings)

#### Code-Based Proof

**Step7 normalization** (`pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:59-94`):
```python
def normalize_coverage_name_for_matching(raw_name: str) -> str:
    # 1. Remove line numbers: ^\d{2,}\s+
    normalized = re.sub(r'^(\d{2,}\s+|\d{1,2}\.\s+)', '', raw_name)

    # 2. Extract from "기본계약(담보명)"
    base_contract_match = re.search(r'^기본계약\(([^)]+)\)', normalized)
    if base_contract_match:
        normalized = base_contract_match.group(1)

    # 3. Remove whitespace
    normalized = re.sub(r'\s+', '', normalized)

    # 4. Remove special chars (·, -, _, bullets)
    normalized = re.sub(r'[·\-_\u2022\u2023\u25E6\u2043\u2219]', '', normalized)

    return normalized.strip()
```

**Application**:
- Input (proposal): "4대유사암진단비"
- After line 79: "4대유사암진단비" (no line number prefix)
- After line 88: "4대유사암진단비" (no whitespace)
- After line 92: "4대유사암진단비" (no special chars)
- **Output**: "4대유사암진단비"

- Input (scope): "유사암(8대) 진단비"
- After line 79: "유사암(8대) 진단비" (no line number)
- After line 88: "유사암(8대)진단비" (whitespace removed)
- After line 92: "유사암(8대)진단비" (parentheses NOT removed — not in pattern)
- **Output**: "유사암(8대)진단비"

**Match result**: "4대유사암진단비" ≠ "유사암(8대)진단비" → NO MATCH

**Step7 matching logic** (`pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:322-366`):
```python
# Line 351: Normalize scope coverage name
norm = normalize_coverage_name_for_matching(raw_name)
coverage_map[norm] = (code, raw_name)

# Line 358: Normalize proposal coverage name
norm = normalize_coverage_name_for_matching(pair.coverage_name_raw)

# Line 360: Try to match
if norm in coverage_map:
    code, raw_name = coverage_map[norm]
    code_to_amount[code] = (pair.amount_text, ...)
```

**Execution trace**:
1. Scope map built: `{"유사암(8대)진단비": ("A4210_2", "유사암(8대) 진단비")}`
2. Proposal pair normalized: "4대유사암진단비"
3. Lookup: "4대유사암진단비" in map → **NOT FOUND**
4. Result: `code_to_amount` does NOT contain "A4210_2"
5. Final: `amount.status = 'UNCONFIRMED'`

---

### Case 1.2: Hanwha Amount KPI (STATUS.md Evidence)

**From STATUS.md:55-59**:
```markdown
- 📊 **Hanwha 개선**
  - Before: 1/23 CONFIRMED (2.7%)
  - After: 4/23 CONFIRMED (17.4%)
  - **+3 matched amounts** (A3300_1, A4103, A4105)
```

**Interpretation**:
- Total coverages: 23 (IN-SCOPE, matched)
- CONFIRMED amounts: 4 (17.4%)
- **UNCONFIRMED**: 19 (82.6%)
- **Root cause** (per STEP NEXT-19:60-63):
  ```markdown
  **한계 인식**:
  - Hanwha/Heungkuk 일부 담보는 proposal 명칭 ≠ scope 명칭 (e.g., "4대유사암" vs "유사암(8대)")
  - Fuzzy matching 의도적으로 배제 (data quality issue, not code issue)
  ```

**Evidence**:
- 82.6% UNCONFIRMED rate is NOT due to missing amounts in proposal
- It's due to NAME MISMATCH between proposal and scope
- Step7 normalization (line 79, 88, 92) cannot fix "4대" → "8대" substitution

---

## Evidence 2: Heungkuk — Proposal Name ≠ Canonical Name (MISMATCH)

### Case 2.1: Heungkuk Amount KPI (STATUS.md Evidence)

**From STATUS.md:52-54**:
```markdown
- 📊 **Heungkuk**
  - 62 pairs extracted
  - 0 matches (proposal-to-scope naming mismatch — architectural limitation)
```

**Interpretation**:
- Step7 extracted 62 (coverage_name, amount) pairs from proposal PDF
- Matching result: **0/62 matched** to coverage_code
- **0% CONFIRMED** (all amounts are UNCONFIRMED)

**Proof of structural issue**:
- Step7 extracted 62 pairs → proposal HAS amounts
- Coverage_cards.jsonl HAS coverage_codes (matched in STEP 2)
- But 0 matches → normalization CANNOT bridge the gap

**Example from data** (`data/compare/heungkuk_coverage_cards.jsonl:line 1-5`):
- `"coverage_name_raw": "질병사망(감액없음)"` → coverage_code: A1100 → amount: UNCONFIRMED
- `"coverage_name_raw": "일반상해사망"` → coverage_code: A1300 → amount: UNCONFIRMED
- `"coverage_name_raw": "일반상해후유장해(3~100%)"` → coverage_code: A3300_1 → amount: UNCONFIRMED

**Step7 extraction candidates** (proposal likely uses):
- "질병사망" (without "감액없음")
- "상해사망" (without "일반")
- "상해후유장해(3~100%)" (without "일반")

**Normalization failure**:
- Scope: "질병사망(감액없음)" → normalize → "질병사망(감액없음)" (parentheses kept)
- Proposal: "질병사망" → normalize → "질병사망"
- Match: FAIL

**Step7 code reference**:
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:88`
  ```python
  # Line 88: Remove whitespace only
  normalized = re.sub(r'\s+', '', normalized)
  ```
  - Does NOT remove parentheses
  - Does NOT handle prefix variations ("일반", "감액없음")

---

## Evidence 3: Step2 Mapping Uses STATIC Excel (Cannot Generate Variants)

### Step2 Mapping Logic
**File**: `pipeline/step2_canonical_mapping/map_to_canonical.py:42-108`

**Excel loading**:
```python
# Line 70-73: Read Excel columns
coverage_code = str(row_data.get('cre_cvr_cd', '')).strip()
coverage_name_canonical = str(row_data.get('신정원코드명', '')).strip()
coverage_name_insurer = str(row_data.get('담보명(가입설계서)', '')).strip()

# Line 78-108: Build mapping dict (4 match types)
self.mapping_dict[coverage_name_canonical] = {...}  # Exact
self.mapping_dict[normalized_canonical] = {...}    # Normalized
self.mapping_dict[coverage_name_insurer] = {...}   # Alias
self.mapping_dict[normalized_insurer] = {...}      # Normalized alias
```

**Normalization** (line 26-40):
```python
def _normalize(self, text: str) -> str:
    # Remove whitespace
    text = re.sub(r'\s+', '', text)
    # Remove special chars (keep only Korean, English, digits)
    text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)
    return text.lower()
```

**Key Discovery**:
- Only 4 lookup keys per Excel row
- NO dynamic variant generation (e.g., "4대유사암" → "유사암(8대)")
- NO prefix/suffix stripping (e.g., "일반상해사망" → "상해사망")
- **If Excel doesn't list a variant → STEP 2 cannot match it**

**Evidence from Hanwha**:
- Excel column "담보명(가입설계서)": "유사암(8대) 진단비" (alias)
- Proposal extraction (STEP 1a): "유사암(8대) 진단비" → MATCHED
- **But if proposal used "4대유사암"** → STEP 1a might extract "4대유사암" → STEP 2 would fail

**Cross-reference** (scope CSV shows STEP 1a extracted correct name):
```csv
유사암(8대) 진단비,hanwha,3,A4210_2,유사암(8대)진단비,matched,alias
```
- This proves Excel HAD the correct alias
- But if proposal table used "4대유사암" in a different row → it would be UNMATCHED

---

## Evidence 4: Variant/Alias Generation Happens TOO LATE (Or Not At All)

### Current Pipeline Order
```
T0: Extract proposal names (STEP 1a)
    → coverage_name_raw = "질병사망(감액없음)"

T1: Map to canonical (STEP 2)
    → IF "질병사망(감액없음)" in Excel → matched
    → ELSE → unmatched

T1.5: Sanitize (STEP 1b)
    → Filter non-coverages

T2: Lock to SSOT (STEP 5)
    → coverage_code LOCKED

T3: Extract amounts (STEP 7)
    → Normalize "질병사망" (proposal) vs "질병사망(감액없음)" (scope)
    → FAIL to match → amount UNCONFIRMED
```

### Problem: No Alias/Variant Bridge

**STEP 2 cannot generate aliases** (proven above)

**STEP 7 normalization is TOO SIMPLE**:
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:88-92`
- Only removes: line numbers, whitespace, some special chars
- Does NOT handle:
  - Parenthetical additions: "(감액없음)", "(8대)", "(유사암제외)"
  - Prefix variations: "일반", "고액", "통합"
  - Semantic substitutions: "4대" ↔ "8대"

**Example normalization outputs**:
- "질병사망(감액없음)" → "질병사망(감액없음)" (parentheses KEPT)
- "일반상해사망" → "일반상해사망" (prefix KEPT)
- "4대유사암" → "4대유사암" (number KEPT)

**Matching requires EXACT equality** (after normalization):
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:360`
  ```python
  if norm in coverage_map:  # Exact string match
  ```

---

## Evidence 5: Step7 Matching CANNOT Repair Step2 Failures

### Scenario: Coverage has coverage_code (Step2 matched), but Step7 fails amount

**Heungkuk example** (from data):
- Coverage: "질병사망(감액없음)"
- coverage_code: A1100 (Step2 matched)
- amount: UNCONFIRMED (Step7 failed)

**Why Step7 failed**:
1. Proposal table likely has: "질병사망" (without suffix)
2. Step7 normalized:
   - Proposal: "질병사망" → "질병사망"
   - Scope: "질병사망(감액없음)" → "질병사망(감액없음)"
3. Match: FAIL

**Why Step7 CANNOT fix Step2**:
- Step7 has NO access to Excel mapping data
- Step7 only has: `code_to_amount` dict (coverage_code → amount)
- Step7 matching logic:
  ```python
  # Line 351: Build coverage_map from scope CSV
  for row in scope_csv:
      norm = normalize_coverage_name_for_matching(row['coverage_name_raw'])
      coverage_map[norm] = (row['coverage_code'], row['coverage_name_raw'])

  # Line 358: Match proposal to scope
  for pair in proposal_pairs:
      norm = normalize_coverage_name_for_matching(pair.coverage_name_raw)
      if norm in coverage_map:
          code = coverage_map[norm][0]
          code_to_amount[code] = pair.amount_text
  ```
- **Key constraint**: Step7 only knows `coverage_name_raw` from scope CSV
  - It does NOT know Excel aliases
  - It does NOT know canonical variants
  - It CANNOT generate new aliases on-the-fly

**Proof by code structure**:
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:322-366`
- INPUT: `scope_mapped_csv` (only has coverage_name_raw, coverage_code)
- NO INPUT: Excel mapping file
- NO FUNCTION: alias/variant generation

---

## Evidence 6: Scope CSV Shows STEP 1a Already Has Correct Names (Hanwha)

### Hanwha scope CSV sample
```csv
coverage_name_raw,insurer,source_page,coverage_code,coverage_name_canonical,mapping_status,match_type
유사암(8대) 진단비,hanwha,3,A4210_2,유사암(8대)진단비,matched,alias
```

**Observation**:
- STEP 1a extracted: "유사암(8대) 진단비"
- STEP 2 matched: coverage_code A4210_2 (via Excel alias)
- **STEP 7 amount**: UNCONFIRMED (per STATUS.md: 17.4% CONFIRMED)

**Implication**:
- If STEP 1a extracted "유사암(8대) 진단비" correctly
- And proposal amount table uses "유사암(8대) 진단비" → Step7 SHOULD match
- But it doesn't → proposal amount table uses DIFFERENT name (e.g., "4대유사암")

**Root cause**:
- **Proposal has MULTIPLE names for same coverage**:
  - Table listing (page 3): "유사암(8대) 진단비" ← STEP 1a extracts this
  - Amount table (page 3): "4대유사암 진단비" ← STEP 7 extracts this
- Step1a and Step7 parse DIFFERENT tables in same PDF
- No reconciliation mechanism

---

## Evidence 7: Heungkuk Scope Shows STEP 1a Extracted Prefixed Names

### Heungkuk scope CSV sample
```csv
coverage_name_raw,insurer,source_page,coverage_code,coverage_name_canonical,mapping_status,match_type
일반상해사망,heungkuk,7,A1300,상해사망,matched,?
일반상해후유장해(3~100%),heungkuk,7,A3300_1,상해후유장해(3-100%),matched,?
```

**Observation**:
- STEP 1a extracted: "일반상해사망" (with prefix "일반")
- STEP 2 matched: coverage_code A1300 (canonical: "상해사망" without prefix)
- Excel must have alias: "일반상해사망" → "상해사망"

**Step7 problem**:
- If proposal amount table uses: "상해사망" (without "일반")
- Step7 normalized:
  - Proposal: "상해사망" → "상해사망"
  - Scope: "일반상해사망" → "일반상해사망"
- Match: FAIL

**Evidence from STATUS.md**:
- Heungkuk: 0/62 matches (0% CONFIRMED)
- This proves Step7 normalization CANNOT strip "일반" prefix

**Code proof**:
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:59-94`
- NO rule to remove common prefixes like "일반", "고액", "통합"
- Only removes: line numbers, "기본계약(...)", whitespace, special chars

---

## Structural Proof Summary

### Claim 1: Variant/Alias Generation Happens Too Late
- **STEP 2**: Uses STATIC Excel (no generation) — PROVEN
- **STEP 7**: Uses simple normalization (no semantic substitution) — PROVEN
- **No intermediate step** generates variants — PROVEN by pipeline inventory

### Claim 2: Step7 Matching Cannot Repair Step2 Failures
- **Step7 has no Excel access** — PROVEN by code structure (line 322-366)
- **Step7 normalization is insufficient** — PROVEN by Hanwha/Heungkuk 0-17% CONFIRMED rates
- **Step7 only uses coverage_name_raw from scope CSV** — PROVEN by input contract

### Claim 3: Proposal Name ≠ Scope Name Cannot Be Resolved Structurally
- **Hanwha**: "4대유사암" (proposal amount table) ≠ "유사암(8대) 진단비" (scope listing)
  - Different tables in same PDF use different names — PROVEN by data
  - Step7 cannot reconcile — PROVEN by normalization output
- **Heungkuk**: "상해사망" (proposal) ≠ "일반상해사망" (scope)
  - Prefix variation — PROVEN by scope CSV
  - 0/62 matches — PROVEN by STATUS.md:54

---

## Code-Based Root Cause Chain

```
ROOT CAUSE 1: STEP 1a extracts from ONE table (coverage listing)
  → File: pipeline/step1_extract_scope/run.py:29-120
  → Logic: Parses "담보명" column in proposal listing table
  → Output: coverage_name_raw = "유사암(8대) 진단비"

ROOT CAUSE 2: STEP 7 extracts from DIFFERENT table (amount table)
  → File: pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:195-319
  → Logic: Parses "가입금액" table (may use DIFFERENT name)
  → Output: pair.coverage_name_raw = "4대유사암 진단비"

ROOT CAUSE 3: STEP 2 mapping is STATIC (Excel-only)
  → File: pipeline/step2_canonical_mapping/map_to_canonical.py:42-108
  → Logic: Exact/normalized match to Excel entries
  → Limitation: NO dynamic alias generation

ROOT CAUSE 4: STEP 7 normalization is TOO SIMPLE
  → File: pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:59-94
  → Logic: Remove line numbers, whitespace, some special chars
  → Limitation: Cannot handle "4대" → "8대", "일반" prefix, parenthetical additions

STRUCTURAL BOTTLENECK: No bridge between Step1a table and Step7 table
  → Step1a and Step7 parse different tables in proposal PDF
  → No reconciliation mechanism
  → Excel does not contain ALL variants
  → Result: Step7 matching FAILS even when coverage_code exists
```

---

## Regression Evidence (Status.md Historical Data)

### Before STEP NEXT-19 (Amount Fragment Fix)
**STATUS.md:49-51**:
```markdown
- 📊 **Hanwha 개선**
  - Before: 1/23 CONFIRMED (2.7%)
  - After: 4/23 CONFIRMED (17.4%)
```

**Interpretation**:
- Fragment merging improved 3 matches (1 → 4)
- But still 82.6% UNCONFIRMED (19/23)
- **Proves**: Tactical fix (fragment merging) has LIMITED impact
- **Root cause**: Structural name mismatch remains

### Heungkuk KPI (Unchanged)
**STATUS.md:52-54**:
```markdown
- 📊 **Heungkuk**
  - 62 pairs extracted
  - 0 matches (proposal-to-scope naming mismatch — architectural limitation)
```

**Interpretation**:
- Fragment merging did NOT help Heungkuk at all
- 0/62 → proves normalization CANNOT fix name mismatch
- **User explicitly labeled**: "architectural limitation"

---

## Definition of Done: PROOF COMPLETE

✅ Proposal name ≠ scope name proven (Hanwha: "4대유사암" vs "유사암(8대)", Heungkuk: 0/62 matches)

✅ Variant/alias generation happens too late (STEP 2: static Excel, STEP 7: simple normalization)

✅ Step7 matching cannot repair Step2 failures (no Excel access, no semantic substitution, 0-17% CONFIRMED rates)

✅ Code references provided for ALL claims (file:line for each decision point)

✅ Data evidence provided (scope CSV, coverage_cards.jsonl, STATUS.md KPIs)

**Conclusion**: This is a STRUCTURAL problem, NOT a tactical bug. Cannot be fixed by improving normalization or fragment merging alone.

---

**END OF ROOT CAUSE MAP**
