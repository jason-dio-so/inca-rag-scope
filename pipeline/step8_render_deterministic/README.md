# Step8: Deterministic Render Engine (LLM OFF)

**STEP NEXT-63**: Customer example rendering with ZERO LLM/OCR/Embedding

---

## Purpose

Render customer-facing comparison UI/responses using ONLY deterministic evidence extraction.

**Constitutional Rules**:
- ❌ NO LLM for fact generation/comparison/summary
- ❌ NO OCR / Embedding / Vector DB
- ❌ NO inference / recommendation / judgment
- ✅ ALL outputs fact-based with evidence references
- ✅ 100% deterministic (same input → same output SHA256)

---

## Examples Implemented

### Example 1: Premium Comparison (Top-4)
**File**: `example1_premium_compare.py`

**Input**:
- List of insurers
- Sort by: premium (ascending)

**Output**:
- Top-4 insurers by monthly premium
- Monthly / Total premium with evidence refs

**Gates**:
- >= 4 insurers with premium data OR NotAvailable

**Usage**:
```bash
python3 example1_premium_compare.py \
  --insurers samsung meritz hanwha lotte kb hyundai \
  --output output/example1.json
```

---

### Example 2: Coverage Limit Comparison
**File**: `example2_coverage_limit.py`

**Input**:
- coverage_code (canonical)
- List of insurers

**Output**:
- Insurer-by-insurer table:
  - Amount / Payment Type / Limit / Conditions
  - Evidence references

**Gates**:
- coverage_code alignment 100%
- Amount parsing fails → null + reason

**Usage**:
```bash
python3 example2_coverage_limit.py \
  --insurers samsung meritz lotte \
  --coverage-code A4200_1 \
  --output output/example2.json
```

---

### Example 3: Two-Insurer Comparison
**File**: `example3_two_insurer_compare.py`

**Input**:
- 2 insurers
- coverage_code

**Output**:
- Side-by-side comparison table
- 3-line summary (fixed templates):
  1. Amount: same/different
  2. Payment type: same/different
  3. Conditions: same/different
- All fields with evidence links

**Gates**:
- join_rate == 1.0 (both must have coverage)
- evidence_fill_rate >= 0.8
- Numeric fields must be numeric only

**Usage**:
```bash
python3 example3_two_insurer_compare.py \
  --insurer1 samsung \
  --insurer2 meritz \
  --coverage-code A4200_1 \
  --output output/example3.json
```

---

### Example 4: Subtype Eligibility (제자리암 / 경계성종양)
**File**: `example4_subtype_eligibility.py`

**Input**:
- subtype keyword (e.g., "제자리암", "경계성종양")
- List of insurers

**Output**:
- O / X / △ / Unknown status table
- Judgment basis:
  - 정의 (definition)
  - 면책 (exclusion)
  - 감액 (reduction)
  - 지급률 (payment rate)
- Evidence reference required

**Gates**:
- No evidence → Unknown + reason

**Usage**:
```bash
python3 example4_subtype_eligibility.py \
  --insurers samsung meritz lotte \
  --subtype 제자리암 \
  --output output/example4.json
```

---

## Templates Module

**File**: `templates.py`

Fixed sentence templates (NO LLM):
- Premium table rows
- Coverage limit rows
- Comparison summaries (amount/payment/conditions)
- Eligibility status (O/X/△/Unknown)

**Forbidden Phrases Detection**:
```python
FORBIDDEN_PHRASES = [
    "추천", "권장", "유리", "불리", "좋", "나쁨",
    "우수", "열등", "최선", "최악", "선호",
    "~해야", "~하세요", "~하는 것이 좋습니다",
    "종합 판단", "결론적으로", "~로 보임", "~으로 추정"
]
```

---

## Test Suite

**File**: `tests/test_examples_llm_off.py`

**Coverage**:
- Example 1-4 functional tests
- NO LLM imports verification
- Forbidden phrases validation
- Deterministic reproducibility checks

**Run**:
```bash
pytest tests/test_examples_llm_off.py -v
```

**Result**: 11 passed in 0.03s

---

## Input SSOT

### Canonical Scope
```
data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl
```
- Contains: coverage_code, proposal_facts (premium_text)

### Coverage Cards
```
data/compare/{insurer}_coverage_cards.jsonl
```
- Contains: evidences, hits_by_doc_type

---

## Deterministic Guarantees

### SHA256 Verification
Same input → Same output (byte-identical JSON)

**Example**:
```bash
# Run 1
python3 example2_coverage_limit.py --insurers samsung meritz lotte --coverage-code A4200_1 --output out.json
sha256sum out.json
# 38ae8c82f762b5ed98ca5074d193cd2ac427c6119955c98ee2eaa9ea201c100b

# Run 2
python3 example2_coverage_limit.py --insurers samsung meritz lotte --coverage-code A4200_1 --output out.json
sha256sum out.json
# 38ae8c82f762b5ed98ca5074d193cd2ac427c6119955c98ee2eaa9ea201c100b
```

✅ Identical

---

## Next Steps (NOT in STEP NEXT-63 scope)

1. **Amount Enrichment**: Integrate STEP NEXT-62 amount engine outputs
2. **Premium Data**: Investigate proposal_facts premium extraction issues
3. **Evidence Fill Rate**: Improve pattern extraction for higher fill rates

---

## Audit

See: `docs/audit/STEP_NEXT_63_LLM_OFF_EXAMPLES.md`

**DoD Status**: ✅ COMPLETE
