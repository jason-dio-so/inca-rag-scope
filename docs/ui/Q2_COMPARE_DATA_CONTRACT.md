# Q2 Compare Data Contract (SSOT)

## Date
2026-01-17

## Status
✅ ACTIVE - Implemented and gate-protected

## Purpose
Define the authoritative data contract for Q2 coverage limit comparison between frontend, backend, and database.

---

## 1. Query Lookup Strategy

### Primary Keys
Q2 data is queried from `compare_table_v2` table using:
- **coverage_code** (신정원 통일코드)
- **as_of_date** (YYYY-MM-DD)

### Tie-Breaker Rules
When multiple rows match (coverage_code, as_of_date):
1. **Largest insurer_set first**: `ORDER BY jsonb_array_length(insurer_set) DESC`
2. **Most recent generated_at**: `ORDER BY (payload->'debug'->>'generated_at') DESC`
3. **LIMIT 1**: Return only the best match

**Rationale**: Prefer the most comprehensive and recently generated data.

---

## 2. Subset Matching Policy

### Problem Statement
- Frontend requests 8 insurers: `["MERITZ","DB","HANWHA","LOTTE","KB","HYUNDAI","SAMSUNG","HEUNGKUK"]`
- Database has 7 insurers: `["N01","N03","N05","N08","N09","N10","N13"]` (N02=DB missing)
- Old behavior: 404 error (exact match required)
- New behavior: Return intersection (7 insurers) + missing_insurers debug

### Subset Matching Rules
1. **Query without insurer_set constraint**: Find row by (coverage_code, as_of_date) only
2. **Calculate intersection**: `requested_insurers ∩ available_insurers`
3. **Filter insurer_rows**: Return only rows where `insurer_code ∈ intersection`
4. **Debug transparency**: Include requested_insurer_set, available_insurer_set, returned_insurer_set, missing_insurers

### 404 Conditions (True Data Absence)
- No row found for (coverage_code, as_of_date)
- Intersection is empty (no matching insurers)

### 200 Conditions (Successful Subset)
- At least 1 matching insurer
- Returns filtered data + debug info

---

## 3. Payload Schema (SSOT)

### Top-Level Structure
```json
{
  "debug": {
    "profile_id": "A6200_Q11_PROFILE_V1",           // Legacy naming (to be updated to Q2)
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",
    "generated_at": "2026-01-16T10:06:15.580633Z",
    "generated_by": "tools/run_db_only_coverage.py",
    "chunk_rowcount_at_generation": 2107,

    // Q2 Subset Matching Debug (added by handler)
    "requested_insurer_set": ["N01","N02",...],     // What UI requested
    "available_insurer_set": ["N01","N03",...],     // What DB has
    "returned_insurer_set": ["N01","N03",...],      // What handler returned (intersection)
    "missing_insurers": ["N02"]                     // requested - available
  },
  "q13_report": null,                                // Not used in Q2
  "insurer_rows": [...]                              // See below
}
```

### insurer_rows Array Schema
```json
{
  "insurer_rows": [
    {
      "insurer_code": "N01",                         // ✅ INJECTED by handler (SSOT: insurer_set order)
      "ins_cd": "N01",                               // Legacy field (for backward compatibility)
      "product_name": "무배당 알파Plus보장보험2508...", // ✅ INJECTED by handler (SSOT: product.product_full_name)
      "product_id": "24882",                         // ✅ INJECTED by handler (SSOT: product.product_id)
      "slots": {
        "duration_limit_days": {
          "value": 180                               // ✅ Extracted from coverage_chunk (quantitative)
        },
        "daily_benefit_amount_won": {
          "value": 20000                             // ✅ Extracted from coverage_chunk (quantitative)
        },
        "exclusions": {
          "status": "FOUND",
          "excerpt": "..."
        },
        "waiting_period": {
          "status": "FOUND",
          "excerpt": "..."
        },
        "subtype_coverage_map": {
          "status": "FOUND",
          "excerpt": "..."
        }
      }
    }
  ]
}
```

### Field Definitions

| Field | Type | Required | Description | SSOT Source |
|-------|------|----------|-------------|-------------|
| `insurer_code` | string | ✅ | Insurer code (N01-N13) | Handler injects from insurer_set[index] |
| `ins_cd` | string | ⚠️ Legacy | Duplicate of insurer_code | Handler injects (backward compat) |
| `product_name` | string | ✅ | Full product name (official) | **SSOT: product.product_full_name** (joined by ins_cd + as_of_date) |
| `product_id` | string | ✅ | Product identifier | **SSOT: product.product_id** (joined by ins_cd + as_of_date) |
| `slots` | object | ✅ | Coverage slots (qualitative + quantitative) | Mixed (DB payload + coverage_chunk extraction) |
| `slots.duration_limit_days.value` | number | ⚠️ Best effort | Coverage duration limit in days | Extracted from coverage_chunk text (regex patterns) |
| `slots.daily_benefit_amount_won.value` | number | ⚠️ Best effort | Daily benefit amount in KRW | Extracted from coverage_chunk text (regex patterns) |
| `slots.*.status` | string | ✅ | "FOUND" or "NOT_FOUND" | DB payload |
| `slots.*.excerpt` | string | ✅ | Evidence text excerpt | DB payload |

---

## 4. insurer_code Injection (SSOT)

### Problem
DB payload `insurer_rows` array has NO `insurer_code` field (only `slots`).

### Solution
Handler injects `insurer_code` using `insurer_set` array order as SSOT:
- `insurer_set[0]` → `insurer_rows[0].insurer_code`
- `insurer_set[1]` → `insurer_rows[1].insurer_code`
- ...

### Code Reference
See `apps/api/server.py:830-840`:
```python
for idx, ins_cd in enumerate(available_insurer_set):
    if ins_cd in returned_insurer_set:
        row_data = insurer_rows[idx] if idx < len(insurer_rows) else {}
        row_data['insurer_code'] = ins_cd  # INJECTION
        filtered_rows.append(row_data)
```

---

## 5. product_name SSOT Injection (STEP NEXT-73)

### Problem
- DB payload `insurer_rows` has NO `product_name` or `product_id` fields (only `ins_cd` and `slots`)
- Previous solution: Regex extraction from `coverage_chunk` text
- Previous issues: Unreliable (4/7 failed or messy), captured table headers, not SSOT

### Solution (A안: Reuse product SSOT)
Handler queries `product` table to inject official product names using Q1 join pattern:

**Q1 Join Key**: `product_id` (apps/api/q1_endpoints.py:200)
```python
LEFT JOIN product p ON c.product_id = p.product_id
-- product_name = p.product_full_name
```

**Q2 Adaptation**: `ins_cd + as_of_date` (payload lacks product_id)
```python
SELECT ins_cd, product_id, product_full_name
FROM product
WHERE ins_cd = ANY(%s) AND as_of_date = %s
```

**Rule**: Both Q1 and Q2 MUST use `product.product_full_name` as SSOT. NO regex/text extraction allowed.

### Code Reference
See `apps/api/server.py:851-946`:
```python
# STEP 1: Query product SSOT for all returned insurers (batch query)
self.cursor.execute("""
    SELECT ins_cd, product_id, product_full_name
    FROM product
    WHERE ins_cd = ANY(%s) AND as_of_date = %s
""", (returned_insurer_set, as_of_date))

product_map = {row['ins_cd']: row for row in self.cursor.fetchall()}

# STEP 2: Inject product_name from SSOT
for idx, ins_cd in enumerate(available_insurer_set):
    if ins_cd in returned_insurer_set:
        row_data = insurer_rows[idx] if idx < len(insurer_rows) else {}

        # Q2 Adapter: Inject product_name from SSOT (NO regex extraction)
        if ins_cd in product_map:
            row_data['product_name'] = product_map[ins_cd]['product_full_name']
            row_data['product_id'] = product_map[ins_cd]['product_id']
        else:
            row_data['product_name'] = None  # UI will show "정보없음"
            row_data['product_id'] = None
```

### Debug Transparency
Handler adds 3 debug fields for product SSOT:
- `debug.product_join_key_fact`: 'ins_cd + as_of_date'
- `debug.product_name_missing_insurers`: List of ins_cd without product rows
- `debug.product_table_as_of_date_used`: as_of_date value used for query

### Gate Enforcement
Script: `tools/gate/check_q2_product_name_ssot.sh`

Checks:
- ✅ Q1 join key FACT documented in Q2_PRODUCT_DB_AUDIT.md
- ✅ No regex product_name extraction in Q2 handler
- ✅ Product SSOT batch query exists
- ✅ A6200 returns non-empty product_names
- ✅ No table header noise patterns
- ✅ Debug transparency fields present

---

## 6. Legacy Naming (Q11 → Q2 Migration)

### Current State
- `debug.profile_id`: "A6200_Q11_PROFILE_V1"
- Generation script: `tools/run_db_only_coverage.py` (Q11/Q12/Q13 context)

### Migration Path
**Option A (Hotfix - Current)**:
- Keep legacy naming in DB
- Handler handles subset matching transparently
- No DB regeneration required

**Option B (Future Cleanup)**:
- Regenerate all rows with `profile_id: "A6200_Q2_PROFILE_V1"`
- Update generation script to Q2-specific context
- Archive old rows

**Decision**: Option A (hotfix) is sufficient for MVP. Option B deferred to future refactor.

---

## 6. UI Integration

### Frontend Request (apps/web/app/q2/page.tsx)
```typescript
const response = await fetch('/api/q2/compare', {
  method: 'POST',
  body: JSON.stringify({
    query: "보장한도 차이 비교",
    coverage_code: "A6200",               // Single code
    age: 40,
    gender: "M",
    ins_cds: ["N01","N02",...],           // 8 insurers
    sort_by: "monthly",
    plan_variant_scope: "all",
    as_of_date: "2025-11-26"
  })
});
```

### Proxy Transformation (apps/web/app/api/q2/compare/route.ts)
```typescript
const comparePayload = {
  intent: "Q2_COVERAGE_LIMIT_COMPARE",
  products: [],                           // Empty for Q2
  insurers: ["MERITZ", "DB", ...],        // ENUM (transformed from ins_cds)
  coverage_codes: [resolvedCoverageCode],
  age, gender, as_of_date, ...
};
```

### UI Rendering (apps/web/components/chat/Q2LimitDiffView.tsx)
```typescript
// Expect payload with insurer_rows array
insurer_rows.map(row => (
  <tr key={row.insurer_code}>           // Use injected insurer_code
    <td>{row.insurer_code}</td>
    <td>{row.slots.subtype_coverage_map.excerpt}</td>
  </tr>
))

// Display missing insurers notice
{debug.missing_insurers.length > 0 && (
  <Notice>
    {debug.missing_insurers.length}개 보험사 데이터 없음: {debug.missing_insurers.join(', ')}
  </Notice>
)}
```

---

## 7. Gate Enforcement

### Gate Script
`tools/gate/check_q2_data_subset_ok.sh`

### Checks
1. ✅ Backend health (port 8000)
2. ✅ A6200 with 8 insurers → HTTP 200
3. ✅ returned_insurer_set has 7 insurers
4. ✅ missing_insurers contains "N02"
5. ✅ insurer_rows has 7 elements
6. ✅ All insurer_rows have insurer_code field
7. ✅ insurer_codes match returned_insurer_set

### Run Gate
```bash
bash tools/gate/check_q2_data_subset_ok.sh
```

---

## 8. Known Issues & Future Work

### ⚠️ Q11 Naming Artifacts
- `debug.profile_id` still references Q11 (harmless but misleading)
- **Impact**: None (UI doesn't use profile_id)
- **Fix**: Regenerate with Q2-specific profile_id (deferred)

### ⚠️ Canonical Name Not in Payload
- Q2 payload doesn't include `canonical_name` field at top level
- UI must fetch from coverage_canonical table OR accept it from proxy
- **Workaround**: Proxy can inject canonical_name from coverage_candidates response

### ⚠️ Multiple insurer_set Rows
- DB may have duplicate coverage_code+as_of_date with different insurer_sets
- **Current behavior**: Tie-breaker chooses largest set
- **Risk**: UI requests might hit smaller set if generated_at is newer
- **Mitigation**: Regenerate with consistent 8-insurer sets

---

## 9. Examples

### Example 1: Full Match (8 requested, 8 available)
**Request**: ["N01","N02","N03","N05","N08","N09","N10","N13"]
**DB**: ["N01","N02","N03","N05","N08","N09","N10","N13"]
**Response**:
- HTTP 200
- returned_insurer_set: 8 insurers
- missing_insurers: []
- insurer_rows: 8 elements

### Example 2: Partial Match (8 requested, 7 available)
**Request**: ["N01","N02","N03","N05","N08","N09","N10","N13"]
**DB**: ["N01","N03","N05","N08","N09","N10","N13"]
**Response**:
- HTTP 200
- returned_insurer_set: 7 insurers
- missing_insurers: ["N02"]
- insurer_rows: 7 elements

### Example 3: No Match (8 requested, 0 overlap)
**Request**: ["N01","N02","N03","N05"]
**DB**: ["N08","N09","N10","N13"]
**Response**:
- HTTP 404
- Error: "No matching insurers"

### Example 4: No Data (coverage_code not in DB)
**Request**: ["N01","N02","N03","N05"]
**DB**: No row for coverage_code="A9999"
**Response**:
- HTTP 404
- Error: "No Q2 data found for coverage_code=A9999"

---

## 10. References

- Backend handler: `apps/api/server.py:740-859` (Q2CoverageLimitCompareHandler)
- Frontend proxy: `apps/web/app/api/q2/compare/route.ts`
- Frontend page: `apps/web/app/q2/page.tsx`
- Gate script: `tools/gate/check_q2_data_subset_ok.sh`
- Gate payload checks: `tools/gate/check_q2_compare_payload.sh`

---

## Changelog

### 2026-01-17 - Product Name SSOT Integration (STEP NEXT-73)
- **Problem**: product_name extracted via regex from coverage_chunk (unreliable: 4/7 failed or messy)
- **Solution**: Query product.product_full_name SSOT (A안: reuse existing product table)
- **Changes**:
  - Removed all regex product_name extraction from Q2 handler
  - Added batch query to product table (ins_cd + as_of_date join)
  - Added product_name and product_id injection to insurer_rows
  - Added 3 debug transparency fields: product_join_key_fact, product_name_missing_insurers, product_table_as_of_date_used
  - Created gate: tools/gate/check_q2_product_name_ssot.sh
  - Updated docs: Q2_PRODUCT_DB_AUDIT.md (comprehensive DB audit)
- **Result**: 7/7 insurers now have clean SSOT product names (no table headers, no None)
- **Q1 Consistency**: Q2 now uses same SSOT source as Q1 (product.product_full_name)

### 2026-01-17 - Subset Matching Implemented
- Changed query from exact insurer_set match to (coverage_code, as_of_date) lookup
- Added subset filtering: return requested ∩ available insurers
- Added debug fields: requested_insurer_set, available_insurer_set, returned_insurer_set, missing_insurers
- Added insurer_code injection to insurer_rows
- Created gate: check_q2_data_subset_ok.sh
- Updated handler: Q2CoverageLimitCompareHandler (apps/api/server.py:740-859)

---

## Approval & Enforcement

**Status**: ✅ ACTIVE
**Gate**: REQUIRED (check_q2_data_subset_ok.sh must pass)
**SSOT**: This document is the authoritative reference for Q2 compare data contract
**Updates**: Any changes to Q2 payload structure or query strategy MUST update this document first
