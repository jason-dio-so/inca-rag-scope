# DATA CONTRACT TRACE

**Purpose**: Trace EXACTLY where "coverage exists", "coverage has identity", and "coverage is locked" decisions happen.

**Method**: Code-based evidence (file:line references)

---

## Decision 1: "This Coverage Exists"

### Primary Decision Point
- **File**: `pipeline/step1_extract_scope/run.py`
- **Lines**: 29-120 (extract_coverages method)
- **Logic**:
  ```python
  # Method 1: Text-based (line 45-76)
  for line in lines:
      if triggers in line and '보험료' in line:
          # Extract coverage_name from table rows
          coverage_name = match.group(2).split()[0]
          coverages.append({
              "coverage_name_raw": coverage_name,
              "insurer": self.insurer,
              "source_page": page_num
          })

  # Method 2: Table-based (lines 78-118)
  for table in tables:
      if '담보명' in header and '보험료' in header:
          coverage_name = row[coverage_col_idx]
          coverages.append(...)
  ```
- **Decision Criteria**:
  - Coverage name appears in proposal PDF table
  - Row has coverage name + amount/premium columns
  - Name passes filters (length >= 3, not pure digits, not "합계")
- **Output**: `data/scope/{insurer}_scope.csv`
  - Fields: `coverage_name_raw`, `insurer`, `source_page`
  - **NO coverage_code yet**

### Hardening Fallback (if count < 30)
- **File**: `pipeline/step1_extract_scope/hardening.py`
- **Trigger**: `pipeline/step1_extract_scope/run.py:209-211`
  ```python
  if extracted_total < 30:
      all_coverages, declared_count, pages_found = hardening_correction(insurer, pdf_files)
  ```
- **Logic**: OCR-like search for "담보수 NN개" declaration, then re-extract

### Overwrite Decision Point (Sanitize Filter)
- **File**: `pipeline/step1_sanitize_scope/run.py`
- **Lines**: 58-86 (should_drop_row function)
- **Logic**:
  ```python
  for pattern, reason in DROP_PATTERNS:
      if re.search(pattern, coverage_name_raw):
          return True, reason  # DROP THIS COVERAGE
  ```
- **Effect**: **REMOVES** coverage from existence
- **Output**: `data/scope/{insurer}_scope_mapped.sanitized.csv`
  - Dropped entries → `data/scope/{insurer}_scope_filtered_out.jsonl`

### Key Discovery
- **Existence decision happens BEFORE identity assignment**
- If proposal PDF doesn't list a coverage → it never enters scope → never gets coverage_code
- Example: If "유사암(8대)" not in proposal table → STEP 1a never extracts it → no amount can be matched later

---

## Decision 2: "This Coverage Has Identity (coverage_code)"

### Primary Decision Point
- **File**: `pipeline/step2_canonical_mapping/map_to_canonical.py`
- **Lines**: 110-144 (map_coverage method)
- **Logic**:
  ```python
  # 1. Exact match (line 126-129)
  if coverage_name_raw in self.mapping_dict:
      result['mapping_status'] = 'matched'
      return result  # Has coverage_code

  # 2. Normalized match (line 132-136)
  normalized = self._normalize(coverage_name_raw)
  if normalized in self.mapping_dict:
      result['mapping_status'] = 'matched'
      return result  # Has coverage_code

  # 3. Unmatched (line 139-144)
  return {
      'coverage_code': '',  # EMPTY
      'mapping_status': 'unmatched',
  }
  ```
- **Decision Criteria**:
  - Coverage name matches Excel entry (exact or normalized)
  - Matching logic: strip whitespace, remove special chars, lowercase
- **Output**: `data/scope/{insurer}_scope_mapped.csv`
  - NEW FIELDS: `coverage_code`, `coverage_name_canonical`, `mapping_status`
  - If mapping_status='unmatched' → coverage_code='' (EMPTY STRING)

### Mapping Source (IMMUTABLE INPUT)
- **File**: `data/sources/mapping/담보명mapping자료.xlsx`
- **Excel Structure** (loaded at line 42-108):
  - Column `cre_cvr_cd` → coverage_code (e.g., "A3300_1")
  - Column `신정원코드명` → coverage_name_canonical
  - Column `담보명(가입설계서)` → insurer-specific alias
- **Loading logic** (line 70-108):
  ```python
  coverage_code = str(row_data.get('cre_cvr_cd', '')).strip()
  coverage_name_canonical = str(row_data.get('신정원코드명', '')).strip()
  coverage_name_insurer = str(row_data.get('담보명(가입설계서)', '')).strip()

  # Build mapping_dict with 4 match types
  self.mapping_dict[coverage_name_canonical] = {
      'coverage_code': coverage_code,
      'match_type': 'exact'
  }
  self.mapping_dict[normalized_canonical] = {..., 'match_type': 'normalized'}
  self.mapping_dict[coverage_name_insurer] = {..., 'match_type': 'alias'}
  self.mapping_dict[normalized_insurer] = {..., 'match_type': 'normalized_alias'}
  ```

### Key Discovery
- **Identity assignment is STATIC** (Excel-driven)
- No dynamic alias/variant generation
- If proposal name not in Excel → mapping_status='unmatched' → NO coverage_code
- Example: Proposal "4대유사암" not in Excel → unmatched → later steps cannot match amount

---

## Decision 3: "This Coverage Is Locked to SSOT"

### Primary Decision Point
- **File**: `pipeline/step5_build_cards/build_cards.py`
- **Lines**: 230-241 (CoverageCard creation)
- **Logic**:
  ```python
  # Line 223: Get coverage_code from scope (may be None)
  coverage_code = scope_info['coverage_code'] if scope_info['coverage_code'] else None

  # Line 230-241: Create IMMUTABLE card
  card = CoverageCard(
      insurer=insurer,
      coverage_name_raw=coverage_name_raw,
      coverage_code=coverage_code,  # LOCKED (may be None)
      coverage_name_canonical=coverage_name_canonical,
      mapping_status=mapping_status,  # LOCKED
      evidence_status=evidence_status,
      evidences=selected_evidences,
      hits_by_doc_type=hits_by_doc_type,
      flags=flags
  )
  cards.append(card)
  ```
- **Input Source Resolution** (line 271):
  ```python
  scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")
  # Priority: sanitized → mapped → original
  ```
- **Output**: `data/compare/{insurer}_coverage_cards.jsonl` ← **SSOT**
- **Fields Locked**:
  - `coverage_code` (from scope, may be None if unmatched)
  - `mapping_status` ('matched' | 'unmatched')
  - `coverage_name_raw` (from proposal)
  - `coverage_name_canonical` (from Excel, may be None if unmatched)
  - `evidence_status` ('found' | 'not_found')

### Post-Lock Enrichment (Amount)
- **File**: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py`
- **Lines**: 369-440 (enrich_coverage_cards_with_amounts function)
- **Logic**:
  ```python
  # Line 397: Read EXISTING coverage_code from card
  coverage_code = card.get('coverage_code')

  # Line 400-414: IF coverage_code in extracted amounts → CONFIRMED
  if coverage_code and coverage_code in code_to_amount:
      card['amount'] = {
          'status': 'CONFIRMED',
          'value_text': amount_text,
          ...
      }
  # Line 415-425: ELSE → UNCONFIRMED
  else:
      card['amount'] = {
          'status': 'UNCONFIRMED',
          'value_text': None,
          ...
      }
  ```
- **Key Constraint**: Cannot change coverage_code (line 397 is READ-ONLY)
- **Output**: Same file (IN-PLACE UPDATE)
  - `data/compare/{insurer}_coverage_cards.jsonl`

---

## Decision Flow Timeline

```
TIME    DECISION                              FILE:LINE                           OUTPUT FIELD
─────────────────────────────────────────────────────────────────────────────────────────────────
T0      "Coverage exists in proposal"         step1_extract_scope/run.py:64       coverage_name_raw
        PDF table parsing                     (line 64: coverages.append)         insurer
                                                                                  source_page

T1      "Coverage has canonical identity"     step2_canonical_mapping.py:110      coverage_code
        Excel exact/normalized match          (map_coverage method)               coverage_name_canonical
                                                                                  mapping_status
                                                                                  match_type

T1.5    "Coverage survives sanitization"      step1_sanitize_scope/run.py:58      (filter only)
        DROP non-coverage patterns            (should_drop_row)                   dropped → filtered_out.jsonl

T2      "Coverage is locked to SSOT"          step5_build_cards.py:230            ALL FIELDS LOCKED
        CoverageCard creation                 (CoverageCard constructor)          → coverage_cards.jsonl

T3      "Coverage has confirmed amount"       step7_amount_extraction.py:400      amount.status
        Proposal amount matching              (enrich_coverage_cards)             amount.value_text
        (READ-ONLY to coverage_code)                                              (enrichment only)
```

---

## Duplicate Decisions (CONFLICT POINTS)

### Conflict 1: Sanitize expects coverage_code to exist
- **Location**: `pipeline/step1_sanitize_scope/run.py:120-121`
  ```python
  coverage_code = row.get('coverage_code', '')
  mapping_status = row.get('mapping_status', '')
  ```
- **Problem**: Step name is "1b" but INPUT requires STEP 2 output (`coverage_code` field)
- **Actual execution order**: 1a (extract) → 2 (map) → 1b (sanitize) → 5 (cards)
- **Naming conflict**: "STEP 1b" runs AFTER "STEP 2"

### Conflict 2: Resolver fallback cannot fix upstream failures
- **Location**: `core/scope_gate.py:140-148` (resolve_scope_csv)
  ```python
  candidates = [
      scope_dir / f"{insurer}_scope_mapped.sanitized.csv",  # 1st
      scope_dir / f"{insurer}_scope_mapped.csv",            # 2nd
      scope_dir / f"{insurer}_scope.csv"                     # 3rd
  ]
  for candidate in candidates:
      if candidate.exists():
          return candidate  # Use first found
  ```
- **Problem**: Fallback only checks FILE EXISTENCE, not DATA COMPLETENESS
  - If STEP 1a fails to extract coverage X → X not in ANY fallback file
  - Resolver cannot recover missing data

### Conflict 3: Step7 matching uses normalized names, but mapping used exact match
- **Step7 normalization** (line 59-94):
  ```python
  # Remove line numbers: ^\d{2,}\s+
  # Extract from "기본계약(담보명)" → "담보명"
  # Remove whitespace, special chars
  ```
- **Step2 normalization** (line 26-40):
  ```python
  # Remove whitespace
  # Remove special chars
  # Lowercase
  ```
- **Problem**: Different normalization rules → different match results
  - Step2 may fail to match proposal name → unmatched → no coverage_code
  - Step7 may succeed in normalizing → but coverage_code is empty → cannot match amount

---

## Overwritten Decisions (DATA LOSS)

### Overwrite 1: Sanitize DELETES coverages
- **Location**: `pipeline/step1_sanitize_scope/run.py:118-137`
  ```python
  if should_drop:
      dropped_rows.append(...)  # Lost forever
  else:
      kept_rows.append(row)
  ```
- **Effect**: Coverage exists in `*_scope_mapped.csv` but NOT in `*_scope_mapped.sanitized.csv`
- **Recovery**: IMPOSSIBLE (dropped data logged to JSONL but not used)

### Overwrite 2: Step5 locks mapping_status permanently
- **Location**: `pipeline/step5_build_cards/build_cards.py:204-208`
  ```python
  mapping_status = scope_info['mapping_status']
  if mapping_status == 'matched':
      stats['matched'] += 1
  else:
      stats['unmatched'] += 1
  ```
- **Effect**: Once mapping_status='unmatched' in scope CSV → locked to SSOT forever
- **Recovery**: IMPOSSIBLE without re-running entire pipeline (STEP 1a → 2 → 1b → 5)

---

## Late Decisions (TOO LATE TO FIX)

### Late Decision 1: Amount matching happens AFTER coverage_code lock
- **Coverage_code locked**: T2 (step5_build_cards.py:230)
- **Amount matching runs**: T3 (step7_amount_extraction.py:322-366)
- **Problem**: Step7 can normalize "기본계약(암진단비)" → "암진단비", but coverage_code is already empty
  - Cannot assign coverage_code retroactively
  - Cannot fix mapping_status='unmatched'

### Late Decision 2: Evidence search uses scope_gate filter
- **Location**: `pipeline/step4_evidence_search/search_evidence.py:652-654`
  ```python
  mapping_status = row['mapping_status']

  if mapping_status == 'matched':
      coverage_code_list.append(coverage_code)
  ```
- **Problem**: Only searches evidence for 'matched' coverages
  - 'unmatched' coverages get NO evidence search
  - Even if evidence exists, it's never linked

---

## Key Discoveries (ROOT CAUSE)

### Discovery 1: Identity assignment is TOO RIGID
- **Location**: STEP 2 (map_to_canonical.py:110-144)
- **Problem**: Excel exact match only, no fuzzy/variant generation
- **Example**:
  - Proposal: "4대유사암"
  - Excel: "유사암(8대)"
  - Match: FAIL → mapping_status='unmatched' → no coverage_code
  - STEP 7 cannot fix this (coverage_code already locked)

### Discovery 2: Existence decision happens TOO EARLY
- **Location**: STEP 1a (extract_scope/run.py:29-120)
- **Problem**: Proposal table parsing before canonical knowledge
- **Example**:
  - If proposal table has "암진단" but Excel has "일반암진단비" → extraction succeeds but mapping fails
  - If proposal has merged cells / formatting issues → extraction fails → coverage never enters scope

### Discovery 3: Normalization happens in WRONG ORDER
- **Current order**: Extract → Map (normalize) → Sanitize → Lock
- **Problem**: Step7 has BETTER normalization (line number removal, parentheses extraction) but runs AFTER lock
- **Should be**: Normalize → Map → Extract → Lock

---

**END OF TRACE**
