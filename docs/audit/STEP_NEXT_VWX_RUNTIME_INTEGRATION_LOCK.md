# STEP NEXT-VWX: Customer API Integration + Q14 Enhancement + Operational Stability (SPEC LOCK)

**Status:** 🔒 **SPECIFICATION LOCKED** (Implementation Pending)
**Date:** 2026-01-09
**Version:** 1.0

---

## 0. Constitutional Principles (ABSOLUTE)

### 0.1 Premium SSOT Rules (ZERO TOLERANCE)

```
✅ ALLOWED:
- Premium lookup from SSOT (product_premium_quote_v2 / coverage_premium_quote)
- Premium storage after API Pull
- Premium validation (sum match, schema check)

❌ FORBIDDEN:
- Premium calculation/estimation/inference via LLM
- Premium averaging/imputation for missing values
- Premium manipulation/adjustment/correction
- Birthday calculation (use templates only: 30→19960101, 40→19860101, 50→19760101)
```

### 0.2 API Contract (FIXED)

**2-Step Flow (LOCKED):**
1. `prInfo` → Get product list (prCd mapping)
2. `prDetail` → Get coverage premiums (filter by prCd)

**Request Parameters (LOCKED):**
- `baseDt`: YYYYMMDD (e.g., 20260109)
- `age`: 30 | 40 | 50 (string in API body)
- `sex`: "1" (M) | "2" (F)
- `birthday`: Fixed templates (NO calculation)
  - 30세: "19960101"
  - 40세: "19860101"
  - 50세: "19760101"
- `customerNm`: "홍길동" (LOCKED)

**API Method:** `GET` + JSON Body (NOT querystring)

---

## 1. STEP NEXT-V: Customer API Integration (Q12/Q1/Q14)

### 1.1 Runtime Flow (LOCK)

```
Customer Request (Q12/Q1/Q14)
  ↓
Extract Params: (baseDt, age, sex, plan_variant)
  ↓
Check Premium SSOT:
  - Query: product_premium_quote_v2 WHERE (insurer_key, product_id, age, sex, plan_variant, as_of_date)
  - Query: coverage_premium_quote WHERE (insurer_key, product_id, coverage_code, age, sex, plan_variant, as_of_date)
  ↓
IF SSOT MISS:
  ├─ (Option A) Synchronous Pull → Retry 1x → Return
  └─ (Option B) FAIL with "Premium SSOT not ready" (POLICY DECISION REQUIRED)
  ↓
IF SSOT HIT:
  ├─ Q12: Inject premium_monthly slot → G10 gate enforcement
  ├─ Q1: Return Top-N products by coverage
  └─ Q14: Rank by premium_per_10m → Return Top-3
```

### 1.2 Q12 Premium Injection (G10 Gate)

**File:** `pipeline/step4_compare_model/builder.py`

**Function:** `inject_premium_monthly_slot(compare_rows, premium_ssot_records)`

**Logic:**
```python
def inject_premium_monthly_slot(compare_rows, age, sex, plan_variant, baseDt):
    """
    G10 GATE: Q12 requires ALL insurers to have premium.

    Rules:
    1. Load premium from SSOT (product_premium_quote_v2)
    2. For each CompareRow:
       - Lookup: (insurer_key, product_id, age, sex, plan_variant, as_of_date=baseDt)
       - If found: Add premium_monthly slot with source_kind="PREMIUM_SSOT"
       - If missing: FAIL (G10 violation)
    3. If ANY insurer missing premium → exit(2) "G10: Q12 requires premium for all insurers"

    Returns:
        CompareRow[] with premium_monthly slot injected
    """
    pass
```

**Premium Slot Structure:**
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
        "response_hash": "abc123..."
      }
    ]
  }
}
```

### 1.3 Q1 Top-N Ranking (Premium-Based)

**Query:** "30세 남성 무해지 기준으로 암진단비 보장이 가장 좋은 상품 Top 3는?"

**Algorithm:**
```python
def rank_q1_top_n(insurers, coverage_code, age, sex, plan_variant, baseDt):
    """
    Q1: Rank products by coverage amount (descending).

    Steps:
    1. Load compare_rows for coverage_code
    2. Load premium from SSOT
    3. Sort by: payout_limit.amount DESC (or coverage_amount DESC)
    4. Return Top-N with premium metadata
    """
    rows = load_compare_rows(coverage_code=coverage_code)
    premium_records = load_premium_ssot(age, sex, plan_variant, baseDt)

    # Join by (insurer_key, product_id)
    for row in rows:
        premium = premium_records.get((row.insurer_key, row.product_id))
        if premium:
            row.premium_monthly = premium

    # Sort by coverage amount
    rows.sort(key=lambda r: r.payout_limit.amount, reverse=True)

    return rows[:3]
```

---

## 2. STEP NEXT-W: Q14 Premium Ranking (LOCK)

### 2.1 Q14 Formula (HARD LOCK)

**Question:** "암진단비 가성비 Top 3는?" (30세 남성 무해지 기준)

**Formula:**
```python
premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)

# Where:
# - premium_monthly: From product_premium_quote_v2 (SSOT)
# - cancer_amt: From compare_rows_v1 (암진단비 유사암제외, payout_limit.amount)
# - Unit: 원 per 1,000만원 보장

# Example:
# - Samsung: premium=45,000, cancer_amt=50,000,000
#   → premium_per_10m = 45,000 / (50,000,000 / 10,000,000) = 9,000
# - Meritz: premium=60,000, cancer_amt=80,000,000
#   → premium_per_10m = 60,000 / (80,000,000 / 10,000,000) = 7,500
# - Meritz is BETTER (lower cost per 1,000만원)
```

**Sort:** `premium_per_10m` ASC (lower is better)

**Tie-Breaker:**
1. `premium_per_10m` (ASC)
2. `premium_monthly` (ASC)
3. `insurer_key` (ASC) — deterministic

**Rounding Policy:** 소수점 2자리 (e.g., 9,000.00)

### 2.2 Q14 Output Schema (LOCK)

```json
{
  "question_id": "Q14",
  "question": "암진단비 가성비 Top 3는? (30세 남성 무해지)",
  "conditions": {
    "age": 30,
    "sex": "M",
    "plan_variant": "NO_REFUND",
    "baseDt": "20260109",
    "coverage_code": "A4200_1",
    "coverage_title": "암진단비(유사암제외)"
  },
  "ranking": [
    {
      "rank": 1,
      "insurer_key": "meritz",
      "product_id": "meritz__메리츠화재건강보험",
      "premium_monthly": 60000,
      "cancer_amt": 80000000,
      "premium_per_10m": 7500.00,
      "source": {
        "premium_ssot": {
          "as_of_date": "2026-01-09",
          "baseDt": "20260109",
          "table_id": "prDetail_api"
        },
        "compare_rows": {
          "file": "data/compare_v1/compare_rows_v1.jsonl",
          "coverage_code": "A4200_1"
        }
      }
    },
    {
      "rank": 2,
      "insurer_key": "samsung",
      "product_id": "samsung__삼성화재건강보험",
      "premium_monthly": 45000,
      "cancer_amt": 50000000,
      "premium_per_10m": 9000.00,
      "source": {
        "premium_ssot": {
          "as_of_date": "2026-01-09",
          "baseDt": "20260109",
          "table_id": "prDetail_api"
        },
        "compare_rows": {
          "file": "data/compare_v1/compare_rows_v1.jsonl",
          "coverage_code": "A4200_1"
        }
      }
    }
  ]
}
```

### 2.3 Q14 Implementation File

**File:** `pipeline/product_comparison/build_q14_premium_ranking.py`

**Function:** `build_q14_ranking(age, sex, plan_variant, baseDt)`

**Dependencies:**
- `data/compare_v1/compare_rows_v1.jsonl` (cancer_amt source)
- `product_premium_quote_v2` (premium source)

---

## 3. STEP NEXT-X: Operational Stability

### 3.1 baseDt Rolling Policy

**Strategy:** Monthly batch Pull + On-demand Pull

**Batch Schedule:**
- **Frequency:** 월 1회 (매월 1일 실행 권장)
- **Scope:** All products × 3 ages × 2 sexes = 54 API calls
  - prInfo: 6 calls (age × sex)
  - prDetail: 6 calls (age × sex, filtered by prCd)
  - Total: 12 API calls per baseDt
- **Storage:** `data/premium_raw/{baseDt}/`
  - `_prInfo/{age}_{sex}.json`
  - `_prDetail/{age}_{sex}.json`
  - `_failures/{baseDt}.jsonl` (if errors)

**On-Demand Pull:**
- Trigger: Customer request with new baseDt not in SSOT
- Execution: Synchronous (block until complete or timeout)
- Timeout: 30s per API call
- Fallback: Return "Premium SSOT not ready for baseDt={baseDt}" (Option B)

### 3.2 Failure Policy (LOCK)

**Retry Rules:**
- **5xx / Timeout / Connection Error:** Retry 2x (max 3 attempts)
- **4xx (Client Error):** Do NOT retry → Save to `_failures/` immediately

**Failure Storage:**
```jsonl
{
  "timestamp": "2026-01-09T10:30:00Z",
  "endpoint": "prDetail",
  "age": 30,
  "sex": "M",
  "request_params": {
    "baseDt": "20260109",
    "birthday": "19960101",
    "sex": "1",
    "age": "30"
  },
  "error_type": "HTTPError",
  "status_code": 400,
  "error": "Client error 400",
  "response_body_snippet": "{\"error\": \"Invalid birthday format\"}",
  "retry_count": 0
}
```

**Failure Impact:**
- Q12: If ANY insurer premium missing → G10 FAIL → Block customer output
- Q1/Q14: If product premium missing → Exclude from ranking (no estimation)

### 3.3 Cache/Performance

**Cache Key:**
```
(baseDt, age, sex, plan_variant, product_id)
```

**Cache Strategy:**
- **TTL:** baseDt 기준 (동일 baseDt는 변경 불가 → 긴 TTL 가능)
- **Invalidation:** baseDt 변경 시 자동 무효화
- **Storage:** In-memory (Redis 권장) or File-based

**Deduplication:**
- Before Pull: Check `content_hash` of existing raw JSON
- If hash match → Skip API call

---

## 4. Deliverables (DoD)

### 4.1 STEP NEXT-V (Customer API Integration)

**Files:**
- [ ] `pipeline/step4_compare_model/premium_injector.py` (Q12 premium slot injection)
- [ ] `pipeline/product_comparison/build_q1_ranking.py` (Q1 Top-N)
- [ ] `pipeline/step4_compare_model/gates.py` (G10 gate enforcement)

**Validation:**
- [ ] `tools/audit/validate_vwx_e2e.py` → DoD-V checks (D1-D5)
- [ ] Q12: premium_monthly slot 존재 + source_kind="PREMIUM_SSOT"
- [ ] Q12: 모든 insurer premium 존재 확인 (G10)
- [ ] Q1: Top-N ranking deterministic

### 4.2 STEP NEXT-W (Q14 Enhancement)

**Files:**
- [ ] `pipeline/product_comparison/build_q14_premium_ranking.py`
- [ ] `schema/050_q14_ranking_output.sql` (optional, for persistence)

**Validation:**
- [ ] `tools/audit/validate_q14_ranking.py` → DoD-W checks (W1-W3)
- [ ] Same input → Same Top-3 (deterministic)
- [ ] premium_per_10m calculation correct
- [ ] Tie-breaker rules applied

### 4.3 STEP NEXT-X (Operational Stability)

**Files:**
- [ ] `pipeline/premium_ssot/batch_pull.py` (monthly batch Pull)
- [ ] `pipeline/premium_ssot/on_demand_pull.py` (runtime Pull)
- [ ] `pipeline/premium_ssot/cache_manager.py` (optional)

**Validation:**
- [ ] `tools/audit/validate_prdetail_pull.py` → 54 calls 성공/실패 집계
- [ ] `tools/audit/validate_premium_ssot.py` → Sum match + schema check
- [ ] `tools/audit/validate_premium_allocation.py` → Sum match between tables

---

## 5. Validation Commands (LOCK)

### 5.1 DoD-V (Customer API Integration)

```bash
# D1: Q12 premium_monthly row 존재
python3 tools/audit/validate_q12_premium_gate.py \
  --input data/compare_v1/compare_rows_v1.jsonl

# D2: source_kind="PREMIUM_SSOT" (no DOC_EVIDENCE)
# (Included in validate_q12_premium_gate.py)

# D3: 모든 insurer premium 존재 (G10)
# (Included in validate_q12_premium_gate.py)

# D4: Premium 출력에 조건 + as_of_date + baseDt 포함
# (Included in validate_q12_premium_gate.py)

# D5: G5~G9 회귀 테스트
python3 tools/run_pipeline.py --stage step4
python3 tools/audit/validate_universe_gate.py --data-dir data
```

### 5.2 DoD-W (Q14 Enhancement)

```bash
# W1: 동일 입력 → 동일 Top-3
python3 tools/audit/validate_q14_ranking.py \
  --baseDt 20260109 \
  --age 30 \
  --sex M \
  --plan-variant NO_REFUND

# W2: Premium 누락 상품 제외 (추정 금지)
# (Included in validate_q14_ranking.py)

# W3: Rounding 정책 고정 (소수점 2자리)
# (Included in validate_q14_ranking.py)
```

### 5.3 DoD-X (Operational Stability)

```bash
# X1: 54개 API 호출 성공/실패 집계
python3 tools/audit/validate_prdetail_pull.py \
  --baseDt 20260109

# X2: Premium SSOT 검증 (sum match + schema)
python3 tools/audit/validate_premium_ssot.py \
  --baseDt 20260109

python3 tools/audit/validate_premium_allocation.py \
  --baseDt 20260109

# X3: E2E 회귀 테스트 (Q12 + Q1 + Q14)
python3 tools/audit/validate_vwx_e2e.py \
  --baseDt 20260109
```

---

## 6. Migration Path (Current → VWX)

### 6.1 Current State (2026-01-09)

**✅ Implemented:**
- Premium SSOT infrastructure (pull_prdetail_for_compare_products.py)
- Premium validation tools (validate_premium_ssot.py, validate_premium_allocation.py)
- Q12 gate definition (validate_q12_premium_gate.py — validation only)
- Routing policy (question_card_routing.json)

**❌ Not Implemented:**
- Q12 runtime premium injection (builder.py)
- Q14 ranking algorithm (no file)
- G10 gate enforcement in pipeline
- Batch Pull scheduler
- On-demand Pull runtime hook

### 6.2 Implementation Phases

**Phase 1: V (Customer API Integration)**
1. Implement `premium_injector.py` (Q12 slot injection)
2. Implement G10 gate in `gates.py`
3. Implement `build_q1_ranking.py` (Q1 Top-N)
4. Integrate with compare endpoint (if API exists)
5. Run DoD-V validation

**Phase 2: W (Q14 Enhancement)**
1. Implement `build_q14_premium_ranking.py`
2. Lock formula + tie-breaker + rounding
3. Create `validate_q14_ranking.py`
4. Run DoD-W validation

**Phase 3: X (Operational Stability)**
1. Implement `batch_pull.py` (monthly cron)
2. Implement `on_demand_pull.py` (runtime fallback)
3. Implement cache manager (optional)
4. Run DoD-X validation

---

## 7. Forbidden Scenarios (ZERO TOLERANCE)

### 7.1 Premium Estimation/Inference

❌ **FORBIDDEN:**
```python
# WRONG: LLM-based premium estimation
if premium is None:
    estimated_premium = llm.estimate_premium(insurer, product, age, sex)

# WRONG: Average-based imputation
if premium is None:
    premium = avg(other_insurers_premium)

# WRONG: Manual calculation
if premium is None:
    premium = base_premium * age_multiplier * sex_multiplier
```

✅ **CORRECT:**
```python
if premium is None:
    raise GateViolationError("G10: Premium SSOT missing for Q12")
```

### 7.2 Birthday Calculation

❌ **FORBIDDEN:**
```python
# WRONG: Age reverse calculation
birthday = (current_year - age) * 10000 + 101
```

✅ **CORRECT:**
```python
# RIGHT: Use fixed templates
BIRTHDAY_TEMPLATES = {
    30: "19960101",
    40: "19860101",
    50: "19760101"
}
birthday = BIRTHDAY_TEMPLATES[age]
```

### 7.3 Partial Success for Q12

❌ **FORBIDDEN:**
```python
# WRONG: Return Q12 result even if some insurers missing premium
if any_insurer_has_premium:
    return q12_result  # WRONG!
```

✅ **CORRECT:**
```python
# RIGHT: Fail if ANY insurer missing premium
if not all_insurers_have_premium:
    exit(2)  # G10 violation
```

---

## 8. Reproduction Commands (LOCK)

### 8.1 Full VWX Pipeline

```bash
# Step 1: Pull Premium SSOT (monthly batch)
python3 pipeline/premium_ssot/pull_prdetail_for_compare_products.py \
  --compare-rows data/compare_v1/compare_rows_v1.jsonl \
  --ages 30 40 50 \
  --sexes M F \
  --baseDt 20260109 \
  --output-dir data/premium_raw \
  --multiplier-excel "data/sources/insurers/4. 일반보험요율예시.xlsx"

# Step 2: Build Q12 with premium injection
python3 tools/run_pipeline.py --stage step4

# Step 3: Build Q1 Top-N
python3 pipeline/product_comparison/build_q1_ranking.py \
  --coverage-code A4200_1 \
  --age 30 \
  --sex M \
  --plan-variant NO_REFUND \
  --baseDt 20260109

# Step 4: Build Q14 ranking
python3 pipeline/product_comparison/build_q14_premium_ranking.py \
  --age 30 \
  --sex M \
  --plan-variant NO_REFUND \
  --baseDt 20260109

# Step 5: Validate all DoD
python3 tools/audit/validate_vwx_e2e.py --baseDt 20260109
```

---

## 9. References

**Constitution:**
- `docs/active_constitution.md` (Pipeline rules)

**Policies:**
- `docs/QUESTION_ROUTING_POLICY.md` (Q1-Q14 routing)
- `docs/PREMIUM_OUTPUT_POLICY.md` (To be created)

**SSOT:**
- `data/compare_v1/compare_rows_v1.jsonl` (Coverage amounts)
- `schema/020_premium_quote.sql` (Premium SSOT schema)
- `data/premium_raw/{baseDt}/` (Raw API responses)

**Implementation:**
- `pipeline/premium_ssot/pull_prdetail_for_compare_products.py` (API Pull)
- `pipeline/step4_compare_model/builder.py` (Compare builder)
- `pipeline/step4_compare_model/gates.py` (G10 gate)

**Validation:**
- `tools/audit/validate_q12_premium_gate.py` (G10 validation)
- `tools/audit/validate_premium_ssot.py` (SSOT validation)
- `tools/audit/validate_premium_allocation.py` (Sum match)

---

## 10. Declaration (LOCK)

**This specification is LOCKED for STEP NEXT-VWX.**

**Principles:**
1. ✅ Premium = SSOT only (no LLM/inference)
2. ✅ Q12 requires ALL insurers premium (G10)
3. ✅ Q14 formula deterministic (no randomness)
4. ✅ Birthday = templates only (no calculation)
5. ✅ baseDt rolling + failure tracking mandatory

**Status:**
- Specification: ✅ LOCKED
- Implementation: ⏳ PENDING
- Validation: ⏳ PENDING (DoD scripts ready)

**Next Step:**
1. Review this spec with stakeholders
2. Get approval for Option A vs Option B (SSOT miss handling)
3. Implement Phase 1 (V: Customer API Integration)

---

**End of STEP_NEXT_VWX_RUNTIME_INTEGRATION_LOCK.md**
