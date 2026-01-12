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

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-12 | Initial LOCK: A6200 only | Canonical schema verification complete |

---

**Status:** 🔒 LOCKED - Do not modify without SSOT verification
