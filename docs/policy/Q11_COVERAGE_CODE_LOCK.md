# Q11 Coverage Code LOCK

**Document Type:** Policy SSOT
**Date:** 2026-01-12
**Status:** 🔒 LOCKED

---

## Q11 Query Definition

**User Question:**
> "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"

**Target Coverage:**
- 암직접치료입원일당 (암직접입원비 계열)

---

## Canonical Coverage Code (SSOT)

### Allowlist (IMMUTABLE)

```python
Q11_COVERAGE_CODES = ["A6200"]
```

**Source:** `data/scope_v3/*_step2_canonical_scope_v1.jsonl`

**Verification:**
```bash
cat data/scope_v3/*_step2_canonical_scope_v1.jsonl | \
  jq -r 'select(.canonical_name) | select(.canonical_name | contains("암직접") and contains("입원")) | [.coverage_code, .canonical_name] | @tsv' | \
  sort -u
```

**Output:**
```
A6200	암직접치료입원일당(1-180,요양병원제외)
```

**Conclusion:** Only **one canonical code** exists across all insurers: `A6200`

---

## Data Source

### Primary Source
- **File:** `data/compare_v1/compare_tables_v1.jsonl`
- **Filter:** `.coverage_rows[] | select(.identity.coverage_code == "A6200")`

### Schema
```json
{
  "identity": {
    "insurer_key": "kb",
    "product_key": "kb__KB건강보험",
    "variant_key": "default",
    "coverage_code": "A6200",
    "coverage_title": "암직접치료입원일당",
    "coverage_name_raw": "503. 암직접치료입원일당(요양제외,1일이상180일한도)"
  },
  "slots": {
    "daily_benefit_amount_won": {
      "status": "FOUND",
      "value": "10000",
      ...
    },
    "duration_limit_days": {
      "status": "FOUND",
      "value": "180",
      ...
    }
  }
}
```

---

## Forbidden Behaviors

❌ **DO NOT:**
1. Filter by `coverage_title` or `coverage_name` text patterns
2. Use regex matching on Korean coverage names
3. Infer or estimate coverage codes from text similarity
4. Add codes to allowlist without canonical schema verification

✅ **MUST:**
1. Use `coverage_code IN Q11_COVERAGE_CODES` filter ONLY
2. Load data from `compare_tables_v1.jsonl` (has coverage_code)
3. Verify coverage_code exists in canonical schema before adding to allowlist

---

## Insurer Coverage Distribution

**Query:**
```bash
jq -r '.coverage_rows[] | select(.identity.coverage_code == "A6200") | [.identity.insurer_key, .identity.coverage_code, .identity.coverage_title] | @tsv' data/compare_v1/compare_tables_v1.jsonl
```

**Result (as of 2025-11-26):**
```
samsung	A6200	암 직접치료 입원일당Ⅱ
heungkuk	A6200	암직접치료입원비
hyundai	A6200	암직접치료입원일당
kb	A6200	암직접치료입원일당
meritz	A6200	암직접치료입원일당
db	A6200	암직접치료입원일당Ⅱ (2 variants)
```

**Coverage:** 6 insurers (samsung, heungkuk, hyundai, kb, meritz, db)

---

## Implementation Contract

### Backend Filter
```python
# ❌ OLD (FORBIDDEN)
coverage_title =~ /암직접.*입원/i

# ✅ NEW (REQUIRED)
coverage_code IN ["A6200"]
```

### Data Loading
```python
# Load from compare_tables_v1.jsonl
with open("data/compare_v1/compare_tables_v1.jsonl") as f:
    for line in f:
        data = json.loads(line)
        for row in data["coverage_rows"]:
            if row["identity"]["coverage_code"] == "A6200":
                # Process row
```

### Sorting (NULLS LAST)
```python
# Python sort key
def sort_key(item):
    days = item["duration_limit_days"]
    daily = item["daily_benefit_amount_won"]
    insurer = item["insurer_key"]

    return (
        (days is None, -days if days is not None else 0),  # DESC NULLS LAST
        (daily is None, -daily if daily is not None else 0),  # DESC NULLS LAST
        insurer  # ASC
    )
```

---

## Verification Commands

### (A) Coverage Code Exists in Canonical Schema
```bash
cat data/scope_v3/*_step2_canonical_scope_v1.jsonl | \
  jq -r 'select(.coverage_code == "A6200") | [.insurer_key, .coverage_code, .canonical_name] | @tsv' | \
  head -10
```

### (B) Coverage Code Exists in Compare Tables
```bash
jq -r '.coverage_rows[] | select(.identity.coverage_code == "A6200") | .identity.insurer_key' \
  data/compare_v1/compare_tables_v1.jsonl | sort -u
```

### (C) Slot Values Distribution
```bash
jq -r '.coverage_rows[] | select(.identity.coverage_code == "A6200") |
  [.identity.insurer_key,
   .slots.duration_limit_days.value,
   .slots.daily_benefit_amount_won.value] | @tsv' \
  data/compare_v1/compare_tables_v1.jsonl
```

---

## Insurer Count: 8 → 6 (7 Records) Explanation

**Question:** "왜 8개가 아니라 6개(7 records)인가?"

**Answer:**

### Total Insurers in Dataset: 8
`[db, hanwha, heungkuk, hyundai, kb, lotte, meritz, samsung]`

### Insurers WITH A6200: 6
`[db, heungkuk, hyundai, kb, meritz, samsung]`

### Insurers WITHOUT A6200: 2
- **hanwha** (한화생명): Data gap (scope_v3에 담보 미포함)
- **lotte** (롯데손해보험): Evidence gap (A6200 동일성 검증 불가)

### Total Records: 7
- **db** appears twice (2 product variants: db_over41, db_under40)
- Other 5 insurers: 1 record each

**Rationale:**
- Q11은 `coverage_code = "A6200"` (암직접입원비) 기준으로만 필터
- compare_tables_v1.jsonl에 A6200이 존재하는 insurer만 포함

**세부 사유 (Fact-based):**

**hanwha** (한화생명):
- **Fact:** `compare_tables_v1.jsonl`에 A6200 row 부재
- **Q11 제외:** ✅ 정당 (Proposal SSOT에 A6200 row 없음)

**lotte** (롯데손해보험):
- **Fact:** `compare_tables_v1.jsonl`에 A6200 row 부재
- **Q11 제외:** ✅ 정당 (Proposal SSOT에 A6200 row 없음)

**Historical Note:**
- 이전 8개 결과는 text-pattern 기반 필터로 인한 과포함이었음
- 본 정책은 canonical coverage_code 기반 SSOT 정정

---

## FOUND + NULL Normalization (MANDATORY)

### Problem (Before Patch)
Some insurers had `status="FOUND"` but `value=None` for slots:
- heungkuk, hyundai, meritz, db: `duration_limit_days` = FOUND + NULL
- **SSOT Violation**: FOUND status must guarantee value existence

### Solution (server.py:927-933)
```python
# SSOT Normalization: FOUND + NULL → UNKNOWN
if slot.get('status') == 'FOUND' and slot.get('value') is None:
    slot = {'status': 'UNKNOWN', 'evidences': []}
```

### Enforcement
- **Location**: `apps/api/server.py` (Q11 endpoint)
- **Rule**: ALL slots with FOUND status MUST have non-null value
- **Patch Date**: 2026-01-12 (STEP NEXT-P2-Q11-PATCH-γ)
- **DoD**: FOUND + NULL records = 0

### UI Contract
- `status=FOUND`: Display value (guaranteed non-null)
- `status=UNKNOWN`: Display "UNKNOWN (근거 부족)"
- Never display FOUND status with missing value

---

## Unit-Guard Validation (MANDATORY)

### Purpose
Prevent contamination of `daily_benefit_amount_won` and `duration_limit_days` by enforcing evidence-based validation rules.

### daily_benefit_amount_won Unit-Guard

**Rule:** FOUND status requires explicit daily benefit context in evidence excerpt.

**Required Keywords (at least 1):**
- "일당", "1일당", "매일", "입원 1일당", "입원일당", "1일", "하루"

**Special Validations:**
1. **Total Amount Detection:**
   - Pattern: `사용금액 X만원` where X*10000 == value
   - Action: FOUND → UNKNOWN (reason: "value extracted from total amount example")

2. **Large Amount Validation (≥1,000,000):**
   - Requires explicit statement like "1일당 X만원" matching the value
   - Without confirmation: FOUND → UNKNOWN

**Decontamination Action:**
- Status: FOUND → UNKNOWN
- Value: X → null
- Evidences: cleared
- Reason: "UnitGuardFail: [specific reason]"

### duration_limit_days Context Validation

**Required Patterns (at least 1):**
- `\d+일\s*[-~]\s*\d+일` (e.g., "1일-180일", "1일~180일")
- `\d+일\s*한도` (e.g., "180일 한도")
- `보장일수\s*\d+` (e.g., "보장일수 180일")
- `\d+일이상\d+일한도` (e.g., "1일이상180일한도")

**Additional Check:**
- Value must appear in excerpt (numeric match)

**Weak Evidence Warning:**
- If validation fails but status=FOUND, log warning
- No automatic decontamination (manual review required)

### Enforcement Location

**Tool:** `q11_unit_guard.py` (standalone decontamination script)

**Execution:**
```bash
python3 q11_unit_guard.py
# Input:  data/compare_v1/compare_tables_v1.jsonl
# Output: data/compare_v1/compare_tables_v1_decontaminated.jsonl
```

**Integration Point:**
- Applied after step4 (compare model generation)
- Before Q11 API endpoint loads data

### Historical Contamination Case

**DB Case (2026-01-13):**
- **Before:** daily_benefit_amount_won = 3,000,000 (FOUND)
- **Evidence:** "(사용일수 10일, 사용금액 300만원)"
- **Issue:** 300만원 is total amount, not daily benefit
- **Action:** Decontaminated to UNKNOWN
- **Backup:** `compare_tables_v1_before_decontamination_2026-01-13.jsonl`

---

---

## Evidence-First Rules (MANDATORY)

### Purpose
Enforce evidence-based SSOT for Q11 slot values. Prohibit backfilling from non-evidence sources.

### Core Rules

**Rule 1: Step3 Evidence Pack is SSOT**
- Q11 슬롯(duration_limit_days, daily_benefit_amount_won)은 Step3 evidence_pack 기반으로만 FOUND 처리한다.
- Source: `data/scope_v3/*_step3_evidence_enriched_v1_gated.jsonl`

**Rule 2: Empty Evidence Pack → UNKNOWN**
- Step3 evidence_pack이 빈 배열(len=0)이면, 해당 슬롯은 무조건 UNKNOWN이다.
- No exceptions. No inference.

**Rule 3: No Backfilling**
- Step4/Proposal_facts/coverage_name_raw로 Q11 슬롯을 backfill하는 것은 금지한다.
- Rationale: Evidence-First principle (근거 없으면 UNKNOWN)

### Enforcement

**Verification Command:**
```bash
# Check if A6200 has empty evidence_pack in Step3
jq -c 'select(.coverage_code=="A6200") | {insurer, evidence_pack_len:(.evidence_pack|length)}' \
  data/scope_v3/*_step3_evidence_enriched_v1_gated.jsonl
```

**Expected:** If `evidence_pack_len == 0`, then compare_tables_v1 must show `status: "UNKNOWN"` for both slots.

**Fact Record:** `docs/audit/Q11_FACT_SNAPSHOT_2026-01-13.md`

---

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-12 | Initial LOCK: A6200 only | Canonical schema verification complete |
| 2026-01-12 | FOUND+NULL normalization mandatory | SSOT integrity enforcement (PATCH-γ) |
| 2026-01-12 | Document 8→6 (7 records) rationale | Insurer A6200 coverage analysis |
| 2026-01-13 | Add Unit-Guard validation policy | Decontaminate DB 3,000,000 total amount contamination (DECONTAMINATE-δ) |
| 2026-01-13 | Add Evidence-First Rules (MANDATORY) | Prohibit backfilling from non-evidence sources (FREEZE-γ) |

---

**Status:** 🔒 FROZEN - Do not modify without SSOT verification

**Related Documentation:**
- Fact snapshot: `docs/audit/Q11_FACT_SNAPSHOT_2026-01-13.md`
- Freeze declaration: `docs/policy/Q11_FREEZE_DECLARATION.md`
- Decontamination report: `docs/audit/Q11_DECONTAMINATION_REPORT_2026-01-13.md`
- Full patch details: `docs/audit/Q11_FINAL_HARDENING_PATCH_2026-01-12.md`
- API implementation: `apps/api/server.py:868-995`
- Unit-guard tool: `q11_unit_guard.py`
