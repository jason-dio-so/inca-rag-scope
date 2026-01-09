# STEP NEXT-V: Customer API Integration Implementation (LOCK)

**Status:** ✅ **IMPLEMENTED** (Core Components Complete)
**Date:** 2026-01-09
**Version:** 1.0

---

## 0. Summary

Implemented STEP NEXT-V (Customer Runtime API Integration + Premium SSOT Fill) per the ultra-compressed specification. This enables Q12/Q1/Q14 to use real premium data from Greenlight API with constitutional compliance (NO LLM/estimation/inference).

---

## 1. Implementation Overview

### 1.1 Core Components

**A. Greenlight Customer API Client**
- **File:** `pipeline/premium_ssot/greenlight_client.py`
- **Purpose:** 2-step API flow (prInfo → prDetail)
- **Key Features:**
  - GET + JSON Body (NOT querystring)
  - Birthday templates ONLY (30→19960101, 40→19860101, 50→19760101)
  - Retry policy: 5xx/timeout max 2, 4xx NO retry
  - Raw response storage: `data/premium_raw/{baseDt}/_prInfo|_prDetail/{age}_{sex}.json`
  - Failure tracking: `data/premium_raw/_failures/{baseDt}.jsonl`

**B. Runtime SSOT Upserter**
- **File:** `pipeline/premium_ssot/runtime_upsert.py`
- **Purpose:** Convert API responses to SSOT records
- **Key Features:**
  - NO_REFUND: API values as-is (NO modification)
  - GENERAL: `round(NO_REFUND × multiplier/100)` ONLY if multiplier exists
  - Sum validation: `sum(coverage.monthlyPrem) == monthlyPremSum` (0 tolerance)
  - Product ID map: prInfo-based ONLY (NO name guessing)

**C. Premium Injector**
- **File:** `pipeline/step4_compare_model/premium_injector.py`
- **Purpose:** Runtime Q12 premium injection with G10 gate
- **Key Features:**
  - SSOT lookup (raw JSON files)
  - SSOT miss handling:
    - Option A (sync_pull): Synchronous API call → SSOT upsert → retry
    - Option B (fail_on_miss): Immediate FAIL
  - G10 enforcement: ALL insurers MUST have premium (ANY missing → FAIL)
  - `source_kind="PREMIUM_SSOT"` (LOCKED)

**D. G10 Gate Integration**
- **File:** `pipeline/step4_compare_model/gates.py`
- **Purpose:** G10 gate enforcement + runtime injection hook
- **Key Features:**
  - `inject_premium_for_q12_runtime()` function
  - Raises `GateViolationError` if G10 fails
  - Connects PremiumInjector to comparison flow

---

## 2. Constitutional Compliance

### 2.1 Absolute Rules (VERIFIED)

✅ **Premium = SSOT ONLY**
- NO LLM/estimation/inference/averaging
- Implementation: All premium values from `_prDetail` raw JSON or SSOT tables

✅ **Birthday Templates ONLY**
- NO calculation
- Implementation: `BIRTHDAY_TEMPLATES = {30: "19960101", 40: "19860101", 50: "19760101"}`

✅ **2-Step API Flow**
- prInfo → prDetail (LOCKED)
- Implementation: `GreenlightAPIClient.pull_premium_for_request()`

✅ **Retry Policy**
- 5xx/timeout/connection: max 2 retries
- 4xx: NO retry
- Implementation: `_call_api_with_retry()` in greenlight_client.py

✅ **G10 Gate: Q12 requires ALL insurers premium**
- ANY missing → FAIL
- Implementation: `PremiumInjector.inject_premium_for_q12()` + G10 check

---

## 3. Runtime Flow

```
Customer Request (Q12, baseDt=20260109, age=30, sex=M)
  ↓
Load compare_rows (from Step4)
  ↓
Call inject_premium_for_q12_runtime()
  ↓
PremiumInjector:
  ├─ Load SSOT (data/premium_raw/20260109/_prDetail/30_M.json)
  ├─ IF MISS:
  │    ├─ (Option A) GreenlightAPIClient.pull_premium()
  │    │    ├─ Call prInfo API
  │    │    ├─ Call prDetail API
  │    │    ├─ Save raw to _prInfo/30_M.json, _prDetail/30_M.json
  │    │    └─ RuntimeSSOTUpserter.convert_api_to_ssot()
  │    │         ├─ Build product_id_map from prInfo
  │    │         ├─ Parse prDetail coverages
  │    │         ├─ Validate sum (NO_REFUND)
  │    │         └─ Generate GENERAL (if multiplier exists)
  │    └─ (Option B) FAIL immediately
  ├─ Build premium_map: {(insurer_key, product_id): premium_data}
  ├─ G10 CHECK: ALL insurers have premium?
  │    ├─ YES: Inject premium_monthly slot
  │    └─ NO: FAIL (raise GateViolationError)
  └─ Return compare_rows with premium_monthly injected
  ↓
Q12 output with premium row (source_kind="PREMIUM_SSOT")
```

---

## 4. File Changes

### 4.1 New Files

| File | Lines | Purpose |
|------|-------|---------|
| `pipeline/premium_ssot/greenlight_client.py` | ~550 | API client (2-step flow) |
| `pipeline/premium_ssot/runtime_upsert.py` | ~350 | SSOT upsert + sum validation |
| `pipeline/step4_compare_model/premium_injector.py` | ~450 | Runtime injection + G10 gate |

### 4.2 Modified Files

| File | Changes |
|------|---------|
| `pipeline/step4_compare_model/gates.py` | + `inject_premium_for_q12_runtime()` + `GateViolationError` |

---

## 5. Validation Commands

### 5.1 Test API Client (Standalone)

```bash
# Test prInfo + prDetail Pull
python3 pipeline/premium_ssot/greenlight_client.py \
  --baseDt 20260109 \
  --age 30 \
  --sex M

# Check raw files
ls -la data/premium_raw/20260109/_prInfo/
ls -la data/premium_raw/20260109/_prDetail/

# Check failures (if any)
cat data/premium_raw/_failures/20260109.jsonl
```

### 5.2 Test Premium Injector (E2E)

```bash
# Test injection with sync_pull policy
PREMIUM_RUNTIME_POLICY=sync_pull \
python3 pipeline/step4_compare_model/premium_injector.py \
  --baseDt 20260109 \
  --age 30 \
  --sex M \
  --plan-variant NO_REFUND \
  --compare-rows data/compare_v1/compare_rows_v1.jsonl

# Test injection with fail_on_miss policy
PREMIUM_RUNTIME_POLICY=fail_on_miss \
python3 pipeline/step4_compare_model/premium_injector.py \
  --baseDt 20260109 \
  --age 30 \
  --sex M \
  --plan-variant NO_REFUND \
  --compare-rows data/compare_v1/compare_rows_v1.jsonl
```

### 5.3 Validate Q12 Premium Gate

```bash
# Validate premium_monthly slot exists + source_kind="PREMIUM_SSOT"
python3 tools/audit/validate_q12_premium_gate.py \
  --input data/compare_v1/compare_rows_v1.jsonl
```

---

## 6. DoD Status

### V1: Q12 premium_monthly slot exists + source_kind="PREMIUM_SSOT"
**Status:** ✅ **IMPLEMENTED**
- `PremiumInjector.inject_premium_for_q12()` injects `premium_monthly` slot
- `source_kind="PREMIUM_SSOT"` hardcoded
- Validation: `validate_q12_premium_gate.py` (D2 check)

### V2: Q12 모든 insurer premium 존재 (G10)
**Status:** ✅ **IMPLEMENTED**
- G10 gate check in `inject_premium_for_q12()`
- ANY insurer missing → status="FAIL" + errors
- Validation: `validate_q12_premium_gate.py` (D3 check)

### V3: Q1 Top-N deterministic
**Status:** ⏳ **PENDING** (Q1 ranking not yet implemented)
- Requires: `pipeline/product_comparison/build_q1_ranking.py`

### V4: Premium 출력에 조건 + as_of_date + baseDt 포함
**Status:** ✅ **IMPLEMENTED**
- Premium slot includes: `age`, `sex`, `plan_variant`, `as_of_date`, `baseDt`
- Validation: `validate_q12_premium_gate.py` (D4 check)

### V5: G5~G9 회귀 테스트
**Status:** ⏳ **PENDING** (requires full E2E test)
- Command: `python3 tools/audit/validate_universe_gate.py --data-dir data`

---

## 7. Example Output

### 7.1 Premium Slot (Injected)

```json
{
  "premium_monthly": {
    "status": "FOUND",
    "value": {
      "amount": 45000,
      "currency": "KRW",
      "plan_variant": "NO_REFUND",
      "age": 30,
      "sex": "M",
      "as_of_date": "2026-01-09",
      "baseDt": "20260109"
    },
    "source_kind": "PREMIUM_SSOT",
    "confidence": {
      "level": "HIGH",
      "basis": "Premium SSOT (API: prDetail_api, baseDt=20260109)"
    },
    "evidences": [
      {
        "table_id": "prDetail_api",
        "as_of_date": "2026-01-09",
        "response_hash": "runtime_loaded"
      }
    ]
  }
}
```

### 7.2 G10 Failure Example

```json
{
  "status": "FAIL",
  "missing_insurers": ["kb", "samsung"],
  "errors": [
    "G10 FAIL: Q12 requires premium for ALL insurers. Missing: kb, samsung"
  ]
}
```

---

## 8. Forbidden Scenarios (Verification)

### 8.1 Premium Estimation
❌ **FORBIDDEN:** LLM/averaging/imputation
✅ **VERIFIED:** NO estimation code in any module

### 8.2 Birthday Calculation
❌ **FORBIDDEN:** Age reverse calculation
✅ **VERIFIED:** `BIRTHDAY_TEMPLATES` dict only (greenlight_client.py:39-43)

### 8.3 4xx Retry
❌ **FORBIDDEN:** Retry on 4xx errors
✅ **VERIFIED:** `_call_api_with_retry()` skips retry for 4xx (greenlight_client.py:140-147)

### 8.4 Q12 Partial Success
❌ **FORBIDDEN:** Q12 output with ANY insurer missing premium
✅ **VERIFIED:** G10 check fails if `insurers_without_premium` non-empty (premium_injector.py:166-174)

---

## 9. Next Steps (STEP NEXT-W/X)

### W: Q14 Premium Ranking
- [ ] Implement `pipeline/product_comparison/build_q14_premium_ranking.py`
- [ ] Formula: `premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)`
- [ ] Tie-breaker: (1) premium_per_10m (2) premium_monthly (3) insurer_key

### X: Operational Stability
- [ ] Implement `pipeline/premium_ssot/batch_pull.py` (monthly cron)
- [ ] Implement cache manager (optional)
- [ ] Expand `validate_vwx_e2e.py` to full DoD coverage

---

## 10. References

**Specification:**
- `docs/audit/STEP_NEXT_VWX_RUNTIME_INTEGRATION_LOCK.md` (VWX spec)

**Implementation:**
- `pipeline/premium_ssot/greenlight_client.py`
- `pipeline/premium_ssot/runtime_upsert.py`
- `pipeline/step4_compare_model/premium_injector.py`
- `pipeline/step4_compare_model/gates.py`

**Validation:**
- `tools/audit/validate_q12_premium_gate.py`
- `tools/audit/validate_vwx_e2e.py` (stub → needs realization)

---

## 11. Declaration (LOCK)

**STEP NEXT-V Implementation is LOCKED.**

**Principles Verified:**
1. ✅ Premium = SSOT only (NO LLM/estimation)
2. ✅ Q12 G10 gate enforced (ALL insurers required)
3. ✅ Birthday = templates only (NO calculation)
4. ✅ 2-step API flow (prInfo → prDetail)
5. ✅ Failure tracking complete

**Status:**
- Core Components: ✅ IMPLEMENTED
- Q1 Ranking: ⏳ PENDING (STEP NEXT-W)
- Q14 Ranking: ⏳ PENDING (STEP NEXT-W)
- Batch Pull: ⏳ PENDING (STEP NEXT-X)

**Next:** Realize `validate_vwx_e2e.py` with full DoD checks (V1-V5)

---

**End of STEP_NEXT_V_IMPLEMENT_LOCK.md**
