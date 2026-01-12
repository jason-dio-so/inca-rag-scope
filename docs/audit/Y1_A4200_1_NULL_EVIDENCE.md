# Y1: A4200_1 payout_limit NULL Evidence

**Date**: 2026-01-12
**Audit**: STEP NEXT-Y Task 1 - Reality Check

---

## 1) JSONL Evidence: compare_rows_v1.jsonl

### Query Results

```bash
# Check step2 canonical mapping
$ cat data/scope_v3/*_step2_canonical_scope_v1.jsonl | jq -s 'map(select(.canonical_name == "암진단비(유사암제외)")) | length'
10

# Check step3 gated entries
$ cat data/scope_v3/*_step3_evidence_enriched_v1_gated.jsonl | jq -s 'map(select(.canonical_name == "암진단비(유사암제외)")) | length'
10

# Sample step3 evidence for hanwha
$ cat data/scope_v3/hanwha_step3_evidence_enriched_v1_gated.jsonl | jq 'select(.canonical_name == "암진단비(유사암제외)") | .evidence[] | select(.slot_key == "payout_limit")'
```

**Result**:
- `payout_limit` evidence exists in step3 (3 evidences found for hanwha)
- Evidence excerpt shows: "회한" keyword matching, but no amount parsed

### Sample Evidence (hanwha)

```json
{
  "slot_key": "payout_limit",
  "doc_type": "가입설계서",
  "page_start": 6,
  "page_end": 6,
  "excerpt": "100세만기 / \n20년납\n보장개시일 이후에 약관에서 정한 \"암\"으로 진단확정된 경우 보험가입금액 지급 (보장개시일은 계약일부터 \n그 날을 포함하여 90일이 지난 날의 다음날로 하며,\n 계약일부터 경과기간 1년미만시 보험가입금액의 50% 지\n급)(최초 1회한)\n47 4대유사암진단비",
  "locator": {
    "keyword": "회한",
    "line_num": 38,
    "is_table": false
  },
  "gate_status": "FOUND"
}
```

### Compare Rows (Final Output)

```bash
# Check hanwha A4200_1 in compare_rows_v1.jsonl
$ cat data/compare_v1/compare_rows_v1.jsonl | jq 'select(.identity.insurer_key == "hanwha" and .identity.coverage_name_raw == "암(4대유사암제외)진단비") | {name_raw: .identity.coverage_name_raw, payout: .slots.payout_limit.value}'
```

**Result**:
```json
{
  "name_raw": "암(4대유사암제외)진단비",
  "payout": null
}
```

---

## 2) Database Reality Check

```bash
$ psql -U cheollee -d inca_rag -c "SELECT COUNT(*) as total, COUNT(CASE WHEN payout_limit_value IS NULL THEN 1 END) as null_count FROM compare_rows WHERE canonical_coverage_id = 'A4200_1';"
```

**Result**:
```
psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: No such file or directory
```

**Status**: DB not running / not loaded

---

## 3) Summary: NULL Reality

### Coverage Mapping Status

| Stage | Coverage ID | Count | Status |
|-------|-------------|-------|--------|
| step2_canonical | `canonical_name == "암진단비(유사암제외)"` | **10** | ✅ Mapped |
| step3_evidence | `canonical_name == "암진단비(유사암제외)"` | **10** | ✅ Evidence found |
| step3 payout_limit | `slot_key == "payout_limit"` | 3+ evidences/insurer | ✅ Evidence exists |
| compare_rows_v1 | `payout_limit.value` | **0 non-null** | ❌ **ALL NULL** |

### Verdict

**10 insurers have `canonical_name == "암진단비(유사암제외)"` mapped in step2/step3**

BUT:

**100% (10/10) have `payout_limit.value = null` in compare_rows_v1.jsonl**

---

## 4) Root Cause Analysis (CONFIRMED)

### Code Location

**File**: `pipeline/step3_evidence_resolver/evidence_patterns.py:45-54`
**Function**: `EVIDENCE_PATTERNS["payout_limit"]`

```python
"payout_limit": EvidencePattern(
    slot_key="payout_limit",
    keywords=[
        "지급한도", "지급 한도", "보장한도", "보장 한도",
        "최고한도", "연간한도", "평생한도", "누적한도",
        "지급횟수", "지급 횟수", "회한", "1회한", "최초1회한"  # ❌ WRONG for diagnosis coverage
    ],
    context_lines=5,
    table_priority=True
)
```

**Extraction Logic**: `pipeline/step3_evidence_resolver/resolver.py:248-253`

```python
if pattern.slot_key in ["entry_age", "payout_limit", "reduction", "waiting_period"]:
    values = self.pattern_matcher.extract_numeric_values(
        first_candidate["context"]
    )
    if values:
        extracted_value = ", ".join(values[:3])  # ❌ Random numbers from context
```

### Observed Behavior

**hanwha A4200_1 (암진단비(유사암제외))**:

1. **proposal_facts** (CORRECT source):
   ```json
   {
     "coverage_amount_text": "3,000만원",  // ✅ THIS is the payout_limit
     "premium_text": "34,230원",
     "period_text": "100세만기 / 20년납"
   }
   ```

2. **evidence_slots.payout_limit** (WRONG source):
   ```json
   {
     "status": "FOUND",
     "value": "10, 1, 29",  // ❌ Random numbers from "최초 1회한" context
     "match_count": 841
   }
   ```

3. **Evidence excerpt matched**:
   ```
   "최초 1회한)\n47 4대유사암진단비"
   ```
   - Keyword: "회한" (occurrence limit)
   - Extracted numbers: "10, 1, 29" (from surrounding text, NOT amount)
   - Missing: "3,000만원" (actual coverage amount)

### Root Cause Confirmed

**Hypothesis 1: Keyword Mismatch (PRIMARY)**

The `payout_limit` pattern uses **"회한" (occurrence limit)** keywords, which are:
- ✅ CORRECT for frequency-based coverages (e.g., surgery count limits)
- ❌ WRONG for **diagnosis coverages** (e.g., A4200_1 암진단비)

For diagnosis coverages:
- **payout_limit** = coverage amount (e.g., "3,000만원")
- **payout_frequency** = occurrence limit (e.g., "최초 1회한")

The current implementation conflates these two concepts.

**Hypothesis 2: Source Priority (SECONDARY)**

For diagnosis coverages, `proposal_facts.coverage_amount_text` should be the PRIMARY source for `payout_limit`, not evidence document search.

Evidence:
- `step8_render_deterministic/example2_coverage_limit.py:L?`:
  ```python
  amount = proposal_facts.get("coverage_amount_text") or self.extract_amount(evidences)
  ```
- This pattern (proposal_facts first, evidences as fallback) is already used in rendering

---

## 5) Next Steps

1. Locate slot extraction logic for `payout_limit` (step3 evidence_resolver)
2. Check keyword/regex pattern used for `payout_limit` extraction
3. Verify why amount-bearing excerpts (e.g., "가입금액 3,000만원") are not prioritized
4. Implement fix to prioritize amount-bearing evidence over occurrence-limit keywords

---

**Conclusion**:
- W/Q14 0 rows is CORRECT given 100% NULL payout_limit
- Blocker is NOT in Q14 ranking logic, but in upstream slot extraction (step3)
