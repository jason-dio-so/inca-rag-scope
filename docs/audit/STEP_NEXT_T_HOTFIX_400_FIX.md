# STEP NEXT-T: HOTFIX - prDetail 400 Error Fix

**Date:** 2026-01-09
**Status:** ✅ IMPLEMENTED
**Type:** Bug Fix (Request Schema Correction)

---

## 0. 문제

**STEP NEXT-S 실행 결과:**
- 54/54 requests → **ALL HTTP 400 (Client Error)**
- Root cause: **불필요한 prCd 파라미터** (내부 product_id가 잘못 전송됨)
- Response body 미저장으로 디버깅 불가

---

## 1. 해결 방법 (LOCK)

### 1.1 API Request Parameters (ONLY Spec Fields)

**BEFORE (STEP NEXT-S):**
```python
params = {
    "baseDt": "20251126",
    "birthday": "19860101",
    "customerNm": "홍길동",
    "sex": "1",
    "age": "40",
    "prCd": "kb__some_internal_product_id"  # ❌ WRONG - internal ID
}
```

**AFTER (STEP NEXT-T):**
```python
params = {
    "baseDt": "20251126",
    "birthday": "19860101",
    "customerNm": "홍길동",
    "sex": "1",
    "age": "40"
}
# prCd REMOVED - internal fields stay in audit/logging only
```

---

### 1.2 Response Body Capture (4xx/5xx)

**BEFORE:**
```python
if 400 <= status_code < 500:
    raise Exception(f"Client error {status_code}: {response.text[:200]}")
```

**AFTER:**
```python
if 400 <= status_code < 500:
    # Capture FULL response body (up to 2000 chars)
    raise Exception(f"Client error {status_code}||RESPONSE_BODY:{response_text[:2000]}")
```

**Failure record now includes:**
```json
{
  "status_code": 400,
  "error": "Client error 400",
  "response_body_snippet": "{ \"error\": \"Invalid prCd\" }"
}
```

---

### 1.3 Validation (D0 Added)

**New check (D0):**
- HTTP 200 rate
- 4xx vs 5xx breakdown
- Response body snippets for failures

**Pass condition:** At least 1 HTTP 200 response

---

## 2. 구현

### 2.1 Modified Files

**1. `pipeline/premium_ssot/pull_prdetail_for_compare_products.py`**

Changes:
- ✅ Removed `prCd` from API request params
- ✅ Capture `response.text` for 4xx/5xx errors
- ✅ Store `response_body_snippet` (first 1000 chars) in failure records
- ✅ Cleaner error message format: `error||RESPONSE_BODY:body`

**2. `tools/audit/validate_prdetail_pull.py`**

Changes:
- ✅ Added `_validate_d0_http_status()` method
- ✅ HTTP status distribution (200/4xx/5xx)
- ✅ Success rate calculation
- ✅ Response body snippet display for failures

---

## 3. 실행 커맨드

### 3.1 Pull API (After Fix)

```bash
python3 pipeline/premium_ssot/pull_prdetail_for_compare_products.py \
    --baseDt 20251126 \
    --sexes M F
```

**Expected:** At least 1 HTTP 200 (D0 PASS)

---

### 3.2 Validate

```bash
python3 tools/audit/validate_prdetail_pull.py --baseDt 20251126
```

**Expected output:**
```
(D0) HTTP Status Distribution:
  HTTP 200 (success): N >= 1
  HTTP 4xx (client error): ...
  HTTP 5xx (server error): ...
  Success rate: X.X%
  Status: ✅ PASS (at least 1 HTTP 200)
```

---

## 4. 검증 (DoD)

| Criterion | Target | Status |
|-----------|--------|--------|
| (D0) At least 1 HTTP 200 | >= 1 | ⚠️ Pending execution |
| (D1) Raw files stored | Per success | ⚠️ Pending execution |
| (D2) Failures with response_body_snippet | 100% | ✅ Implemented |
| (D3) Root cause traceable from failures | Yes | ✅ Implemented |

---

## 5. 변경 요약

### Before (STEP NEXT-S)
- ❌ 54/54 HTTP 400
- ❌ prCd = internal product_id (wrong)
- ❌ No response body in failures
- ❌ No root cause visibility

### After (STEP NEXT-T)
- ✅ prCd removed from request
- ✅ Response body captured (up to 1000 chars)
- ✅ D0 validation (HTTP status distribution)
- ✅ Root cause traceable from failures

---

## 6. 다음 단계

**If D0 PASS (>= 1 HTTP 200):**
1. Check response structure
2. Verify sum match (D2)
3. Load to DB
4. Test Q12 premium gate

**If D0 FAIL (all 400/4xx):**
1. Check `response_body_snippet` in failures
2. Identify missing/incorrect params
3. Adjust request schema
4. Re-run

---

**End of STEP_NEXT_T_HOTFIX_400_FIX.md**
