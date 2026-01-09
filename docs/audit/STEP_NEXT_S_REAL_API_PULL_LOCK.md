# STEP NEXT-S: Real API Pull + Premium SSOT Populate (LOCK)

**Date:** 2026-01-09
**Status:** ✅ IMPLEMENTED
**Type:** Infrastructure + Data Pipeline

---

## 0. 목표

**Q12/Q1/Q14 활성화**를 위해 54건의 실제 prDetail API 호출로 Premium SSOT 채우기.

**DoD:**
1. (D1) 54 raw files (9 products × 3 ages × 2 sexes)
2. (D2) Sum match: `sum(coverage monthlyPrem) == monthlyPremSum` (0 tolerance)
3. (D3) Failures tracked in `_failures/{baseDt}.jsonl`
4. (D4) Q12 premium gate 실검증
5. (D5) Q1/Q14 eligibility > 0

---

## 1. 정책 (LOCKED)

### 1.1 Endpoint (SSOT)

**URL:** `https://new-prod.greenlight.direct/public/prdata/prDetail`

**Method:** GET (querystring params)

**Parameters:**
- `baseDt`: YYYYMMDD
- `birthday`: YYYYMMDD (fixed templates)
- `customerNm`: "홍길동" (fixed)
- `sex`: "1" (M) | "2" (F)
- `age`: 30 | 40 | 50

---

### 1.2 Birthday Templates (FIXED, NO CALCULATION)

| Age | Birthday Template |
|-----|-------------------|
| 30  | 19960101          |
| 40  | 19860101          |
| 50  | 19760101          |

**금지:**
- ❌ Birthday를 계산식으로 만들기 (`datetime.now().year - age`)
- ❌ Response age를 DB key로 사용
- ✅ Request age = DB key (30/40/50)
- ✅ Response age = audit-only

---

### 1.3 Retry Policy (LOCKED)

**Max retries:** 2

**Retry conditions:**
- ✅ 5xx errors (server error)
- ✅ Timeout (15s)
- ✅ Connection errors
- ❌ 4xx errors (NO retry, log as failure)

**Delay:** 1s between retries

---

### 1.4 Failure Tracking (SSOT)

**Path:** `data/premium_raw/_failures/{baseDt}.jsonl`

**Required fields:**
- `timestamp`: ISO 8601
- `insurer_key`: Insurer key
- `product_id`: Product ID
- `age`: Request age (30/40/50)
- `sex`: M | F
- `request_params`: Full request params
- `error`: Error message
- `error_type`: Exception type
- `status_code`: HTTP status (if applicable)
- `response_snippet`: First 500 chars of response (if applicable)
- `retry_count`: Number of retries attempted

---

## 2. 구현

### 2.1 Puller Updates

**File:** `pipeline/premium_ssot/pull_prdetail_for_compare_products.py`

**Changes:**

1. **Fixed Birthday Templates:**
   ```python
   BIRTHDAY_TEMPLATES = {
       30: "19960101",
       40: "19860101",
       50: "19760101"
   }
   ```

2. **Real API Call (GET):**
   ```python
   def call_prdetail_api(request_params, retry_count=0):
       API_ENDPOINT = "https://new-prod.greenlight.direct/public/prdata/prDetail"
       params = {
           "baseDt": request_params['base_dt'],
           "birthday": request_params['birthday'],
           "customerNm": "홍길동",
           "sex": request_params['sex_code'],  # "1" or "2"
           "age": str(request_params['request_age'])
       }
       response = requests.get(API_ENDPOINT, params=params, timeout=15)
       # ... retry logic ...
   ```

3. **Failure Tracking:**
   ```python
   def save_failure(failure, output_dir, base_dt):
       failures_dir = Path(output_dir) / "_failures"
       failure_file = failures_dir / f"{base_dt}.jsonl"
       # Append to JSONL
   ```

4. **CLI Updates:**
   - `--baseDt` parameter now required
   - `--sexes` default=['M', 'F'] for full 54 requests

---

### 2.2 Validation Script

**File:** `tools/audit/validate_prdetail_pull.py`

**Checks:**
- (D1) Raw file count (expected: 54)
- (D3) Failure records completeness
- Breakdown by insurer/age/sex

**Usage:**
```bash
python3 tools/audit/validate_prdetail_pull.py --baseDt 20251126
```

---

## 3. 실행 커맨드 (SSOT)

### 3.1 Pull API (54 requests)

```bash
python3 pipeline/premium_ssot/pull_prdetail_for_compare_products.py \
    --baseDt 20251126 \
    --sexes M F
```

**Expected output:**
- 54 raw JSON files in `data/premium_raw/20251126/{insurer}/{product}/{age}_{sex}.json`
- Failures in `data/premium_raw/_failures/20251126.jsonl` (if any)

---

### 3.2 Validate Pull

```bash
python3 tools/audit/validate_prdetail_pull.py --baseDt 20251126
```

**Expected output:**
```
(D1) Raw Files:
  Expected: 54
  Found: 54
  Status: ✅ PASS

(D3) Failures:
  Total failures: 0

SUMMARY:
  Status: ✅ VALIDATION PASSED
```

---

### 3.3 Load to DB (Future)

```bash
# Load premium SSOT to DB
python3 tools/run_pipeline.py --stage premium_ssot

# Build PCT v3 (Q1/Q14 enablement)
python3 tools/run_pipeline.py --stage pct_v3
```

---

## 4. 산출물

### 4.1 Modified Files

1. `pipeline/premium_ssot/pull_prdetail_for_compare_products.py`
   - Real GET endpoint
   - Fixed birthday templates
   - Retry logic (2× for 5xx/timeout/connection)
   - Failure tracking
   - `--baseDt` required param

2. `tools/audit/validate_prdetail_pull.py`
   - D1/D3 validation
   - Breakdown by insurer/age/sex

---

### 4.2 New Files

1. `docs/audit/STEP_NEXT_S_REAL_API_PULL_LOCK.md`
   - This document

2. `data/premium_raw/{baseDt}/{insurer}/{product}/{age}_{sex}.json`
   - 54 raw API responses

3. `data/premium_raw/_failures/{baseDt}.jsonl`
   - Failure records (if any)

---

## 5. 검증 (DoD)

| Criterion | Status |
|-----------|--------|
| (D1) 54 raw files exist | ⚠️ Pending API call |
| (D2) Sum match (0 tolerance) | ⚠️ Pending data |
| (D3) Failures tracked | ✅ Implemented |
| (D4) Q12 premium gate works | ⚠️ Pending data |
| (D5) Q1/Q14 eligible | ⚠️ Pending data |

---

## 6. 다음 단계

1. **Run puller:**
   ```bash
   python3 pipeline/premium_ssot/pull_prdetail_for_compare_products.py --baseDt 20251126 --sexes M F
   ```

2. **Validate:**
   ```bash
   python3 tools/audit/validate_prdetail_pull.py --baseDt 20251126
   ```

3. **Load to DB:**
   ```bash
   python3 tools/run_pipeline.py --stage premium_ssot
   ```

4. **Test Q12:**
   ```bash
   python3 tools/audit/validate_q12_premium_gate.py --input data/compare_v1/compare_rows_v1.jsonl
   ```

---

## 7. 금지 사항 (ZERO TOLERANCE)

1. ❌ Birthday 계산식 사용
2. ❌ Response age를 DB key로 사용
3. ❌ LLM으로 premium 추정/보정
4. ❌ 4xx 에러 retry
5. ❌ Mock 데이터로 SSOT 채우기

---

**End of STEP_NEXT_S_REAL_API_PULL_LOCK.md**
