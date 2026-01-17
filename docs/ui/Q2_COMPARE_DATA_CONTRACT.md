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
      "slots": {
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
| `slots` | object | ✅ | Coverage slots (exclusions, waiting_period, subtype_coverage_map) | DB payload |
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

## 5. Legacy Naming (Q11 → Q2 Migration)

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
