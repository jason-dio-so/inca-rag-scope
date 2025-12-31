# Amount Verification Policy

**Effective Date**: 2025-12-30 (STEP NEXT-22)
**Applies To**: `pipeline/step7_amount_extraction/`

---

## Purpose

Separate **debug scan logs** from **proof evidence** to prevent confusion about what constitutes a "valid" amount.

**Background**: STEP NEXT-19 introduced multiline merge logic. During development, debug logs were used to explore fragmentation patterns. These logs are NOT proof of correctness.

---

## Two Categories of Amount Logs

### 1. Debug Scan (Development/Exploration)

**Purpose**: Discover edge cases, debug extraction failures, explore fragmentation patterns.

**Characteristics**:
- May include premium amounts (보험료)
- May include page numbers, header text
- May include amounts from non-proposal documents
- NO coverage_code association required
- Output format: print statements, ad-hoc JSON logs

**Examples**:
```python
# Debug: log ALL fragments found
print(f"[DEBUG] Fragment at page {page}: {fragment}")

# Debug: scan all numeric patterns
for pattern in ALL_PATTERNS:
    if pattern.match(line):
        debug_log.append(pattern)
```

**Usage**: Development only. NOT used as evidence in coverage_cards.jsonl.

**Status**: Can be removed in production without affecting SSOT.

---

### 2. Proof Evidence (Production/SSOT)

**Purpose**: Populate `coverage_cards.jsonl` with verified amounts.

**Characteristics**:
- **MUST** meet all 3 conditions from `AMOUNT_EVIDENCE_SCOPE.md`:
  1. `doc_type == 가입설계서`
  2. Semantic context == 가입금액 column
  3. Mapped to `coverage_code` in scope_mapped.csv
- **MUST** have `evidence_ref` with:
  - `page_num` (integer)
  - `snippet` (coverage_name + amount pair)
- Output format: JSON field in coverage_cards.jsonl

**Structure** (required fields):
```json
{
  "status": "CONFIRMED",
  "value_text": "1,000만원",
  "source_doc_type": "가입설계서",
  "source_priority": "proposal_table",
  "evidence_ref": {
    "page_num": 3,
    "snippet": "뇌졸중진단비 / 1,000만원"
  },
  "notes": []
}
```

**Validation**:
- `status == "CONFIRMED"` → ALL 3 conditions verified
- `status == "UNCONFIRMED"` → At least 1 condition failed
  - `value_text` = null
  - `evidence_ref` = null

---

## Policy Rules

### Rule 1: Debug Scans CANNOT Become Proof

If an amount is discovered via debug scan:
1. Extract source page + line context
2. Verify against 3 conditions (AMOUNT_EVIDENCE_SCOPE.md)
3. If ALL pass → write to coverage_card with `status: CONFIRMED`
4. If ANY fail → discard (do NOT write to coverage_card)

**Counter-Example**:
```python
# ❌ WRONG: Debug log directly copied to coverage_card
debug_amount = "7,450원"  # This is a premium, not 가입금액
card['amount'] = {"value_text": debug_amount}  # INVALID
```

**Correct**:
```python
# ✅ RIGHT: Verify before writing
if is_valid_amount_evidence(amount, doc_type, coverage_code):
    card['amount'] = build_proof_evidence(amount, page, snippet)
else:
    card['amount'] = {"status": "UNCONFIRMED", "value_text": null}
```

---

### Rule 2: Proof Evidence Must Be Traceable

Every `status: CONFIRMED` amount MUST have:
- Source file path (e.g., `한화_가입설계서_2511.page.jsonl`)
- Page number (integer)
- Snippet showing coverage_name + amount pair

**Counter-Example**:
```json
{
  "status": "CONFIRMED",
  "value_text": "1,000만원",
  "evidence_ref": null  // ❌ NOT TRACEABLE
}
```

**Correct**:
```json
{
  "status": "CONFIRMED",
  "value_text": "1,000만원",
  "evidence_ref": {
    "page_num": 3,
    "snippet": "뇌졸중진단비 / 1,000만원"
  }
}
```

---

### Rule 3: UNCONFIRMED Status is Not Failure

If an amount cannot be extracted (e.g., coverage not in proposal), use:
```json
{
  "status": "UNCONFIRMED",
  "value_text": null,
  "source_doc_type": null,
  "source_priority": null,
  "evidence_ref": null,
  "notes": []
}
```

This is **expected behavior** for:
- Coverages added after proposal generation
- Coverages in scope_mapped.csv but not in proposal table
- Coverages with special naming (e.g., insurer uses different term)

**DO NOT**:
- Guess amounts from policy terms (약관)
- Interpolate amounts from other insurers
- Use fuzzy matching to "find" amounts

---

## STEP NEXT-19 Verification

The multiline fragment merge logic (`merge_amount_fragments()`) is classified as **Proof Evidence** because:

1. **Triggered only for proposal tables**:
   ```python
   # Code: extract_and_enrich_amounts.py:222
   if not any(kw in text for kw in ['가입금액', '보험가입금액', ...]):
       continue
   ```

2. **Requires coverage association**:
   ```python
   # Code: extract_and_enrich_amounts.py:253-259
   if coverage_candidate:
       pairs.append(ProposalAmountPair(...))
   ```

3. **Output includes evidence_ref**:
   ```python
   # Code: extract_and_enrich_amounts.py:258
   line_text=f"{coverage_candidate} / {merged_amount}"
   ```

**Conclusion**: STEP NEXT-19 merges ARE proof-grade evidence, NOT debug scans.

---

## DoD for Amount Verification

Before releasing a coverage_cards.jsonl file:

- [ ] All `status: CONFIRMED` amounts have non-null `evidence_ref`
- [ ] All `evidence_ref.snippet` show coverage_name + amount pair
- [ ] No debug scan logs in production coverage_cards.jsonl
- [ ] `source_doc_type == "가입설계서"` for all CONFIRMED amounts
- [ ] No premium/reserve/surrender amounts in coverage_cards

---

## References

- `AMOUNT_EVIDENCE_SCOPE.md` — 3 conditions for VALID evidence
- `STEP19_RESTATEMENT.md` — STEP NEXT-19 scope definition
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` — Implementation
