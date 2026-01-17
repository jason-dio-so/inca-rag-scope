# Q2 Backend Endpoint Mismatch — BLOCKED BY BACKEND SCHEMA

## Date
2026-01-17 (Updated after Final Hotfix Directive)

## Status
🔴 **BLOCKED** - Frontend complete per directive, backend schema incompatible

## Issue Summary
Q2 proxy sends `intent: "Q2_COVERAGE_LIMIT_COMPARE"` and `products: []` per directive, but POST `/compare` endpoint rejects both values.

## Root Cause
POST `/compare` has strict Pydantic validation (apps/api/server.py:112-118):
```python
class CompareRequest(BaseModel):
    intent: str = Field(..., pattern="^(PRODUCT_SUMMARY|COVERAGE_CONDITION_DIFF|COVERAGE_AVAILABILITY|PREMIUM_REFERENCE)$")
    insurers: List[str] = Field(..., min_items=1)
    products: List[ProductInfo] = Field(..., min_items=1)  # CANNOT BE EMPTY
    target_coverages: List[TargetCoverage] = []
    options: Optional[RequestOptions] = RequestOptions()
    debug: Optional[DebugOptions] = DebugOptions()

class ProductInfo(BaseModel):
    insurer: str
    product_name: str
```

**Problems:**
1. `intent`: "Q2" not in allowed enum → Fixed to "COVERAGE_CONDITION_DIFF" ✅
2. `products`: Cannot be empty array (min_items=1) → **BLOCKED** ❌

Q2 use case: Compare coverage limits across ALL products (no specific product selection).
Backend requires: At least 1 ProductInfo object `{ insurer, product_name }`.

## Alternative Endpoint Available
GET `/compare_v2` (apps/api/server.py:1800-1815) appears designed for Q2:
```python
@app.get("/compare_v2")
async def compare_v2(
    coverage_code: str,
    as_of_date: str = "2025-11-26",
    ins_cds: Optional[str] = None
):
```

This matches Q2's needs:
- Simple query params (coverage_code + ins_cds)
- No product objects required
- Designed for coverage-centric comparison

## Current Implementation Status

### ✅ Completed (Per Directive)
1. ✅ Accept both `coverage_codes[]` (array) and `coverage_code` (single) from frontend
2. ✅ Extract coverage_code with priority validation
3. ✅ Return 400 if coverage_code missing/empty
4. ✅ Transform `ins_cds` → `insurers` ENUM
5. ✅ Include `intent: "COVERAGE_CONDITION_DIFF"` in payload
6. ✅ Include `products` field in payload (set to `["*"]` wildcard)
7. ✅ NO `coverage_code:undefined` pattern (regression prevention)
8. ✅ Use `query` from input as-is (NO overwrite)
9. ✅ Gate checks updated (11/11 passing)
10. ✅ Smoke tests updated (TC18-TC21 added)

### ❌ Blocked by Backend Schema
- TC18-TC19: Returns 422 (products validation error)
- Backend requires `products: List[ProductInfo]` with min_items=1
- Q2 has no specific products to provide

## Solutions

### Option A: Use GET /compare_v2 (Recommended)
**Pros:**
- Already exists in backend
- Matches Q2 use case exactly
- Simple integration

**Cons:**
- Deviates from original directive (POST /compare)

**Implementation:**
```typescript
// apps/web/app/api/q2/compare/route.ts
const backendUrl = `${API_BASE}/compare_v2?coverage_code=${resolvedCoverageCode}&as_of_date=${as_of_date}&ins_cds=${ins_cds.join(',')}`;

const response = await fetch(backendUrl, {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' },
});
```

### Option B: Update Backend POST /compare
**Pros:**
- Follows original directive
- Unified comparison endpoint

**Cons:**
- Requires backend changes
- Schema complexity

**Implementation:**
Backend needs to:
1. Add new intent enum: "COVERAGE_LIMIT_COMPARISON"
2. Make `products` optional when intent is Q2-related
3. OR accept wildcard product indicator

## Recommendation
Use GET `/compare_v2` for Q2. It's purpose-built for this use case and avoids schema complexity.

## Test Results

### Validation Tests (✅ PASS)
- TC20: Missing coverage_code → 400 ✅
- TC21: Empty coverage_codes[] → 400 ✅
- Gates: 11/11 + 12/12 + 7/7 = 30/30 ✅

### Backend Integration (❌ BLOCKED)
- TC18: coverage_codes array → 422 (products validation)
- TC19: coverage_code single → 422 (products validation)

## Next Steps
1. **Decision Required**: GET /compare_v2 vs. POST /compare backend update?
2. If GET /compare_v2: Update proxy to use GET endpoint
3. If POST /compare: Backend team updates schema validation
4. Re-test TC18-TC19 after decision

## Files Modified
- `/apps/web/app/api/q2/compare/route.ts`: Proxy logic + validation
- `/tools/gate/check_q2_compare_payload.sh`: 11 checks (all passing)
- `/docs/ui/Q2_CHAT_SMOKE.md`: TC18-TC21 added

## Backend Changes Required

### apps/api/server.py

**Option 1: Add Q2 to intent enum (REQUIRED)**

```python
class CompareRequest(BaseModel):
    intent: str = Field(..., pattern="^(PRODUCT_SUMMARY|COVERAGE_CONDITION_DIFF|COVERAGE_AVAILABILITY|PREMIUM_REFERENCE|Q2_COVERAGE_LIMIT_COMPARE)$")
    # Add Q2_COVERAGE_LIMIT_COMPARE to pattern ^^^
```

**Option 2: Make products optional for Q2 (REQUIRED)**

```python
class CompareRequest(BaseModel):
    intent: str
    products: List[ProductInfo] = Field([], min_items=0)  # Allow empty for Q2
    # OR use conditional validation based on intent
```

**Option 3: Use GET /compare_v2 (ALTERNATIVE)**

Proxy changes route to use existing `GET /compare_v2?coverage_code=...&ins_cds=...` endpoint.

## Commit Status
✅ Frontend complete - committed with backend dependency documented
⏳ Blocked by backend schema - requires apps/api/server.py update
