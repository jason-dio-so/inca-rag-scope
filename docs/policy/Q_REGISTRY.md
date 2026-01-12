# Q_REGISTRY: Q1-Q14 Definition & Status (SSOT)

**Date**: 2026-01-12
**Snapshot**: as_of_date=2025-11-26
**Purpose**: Single source of truth for all customer questions Q1-Q14

---

## Registry Rules

1. **Each Q MUST have 8 fields** (no blanks allowed)
2. **Status = READY or BLOCKED** (no "partial" or "in progress")
3. **BLOCKED requires evidence** (what was searched, what was missing)
4. **No estimation/LLM/fallback** - DB/SSOT only
5. **SSOT Source must be verifiable** - table name or file path

---

### Q1
- **Customer Prompt (verbatim)**: "가성비 좋은 암보험 보험료 Top3 알려줘" / "암진단비 1천만원당 보험료가 얼마인지 비교해줘"
- **Inputs/Filters**: age (30/40/50), sex (M/F), plan_variant (NO_REFUND/GENERAL), as_of_date='2025-11-26'
- **SSOT Source**: DB table `q14_premium_ranking_v1`
- **Rule**: Sort by `premium_per_10m ASC, premium_monthly ASC, insurer_key ASC`. Formula: `premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)`. Unit: 원/1천만원. Top 3 per segment.
- **Response Spec**: `docs/ui/FINAL_VIEWMODEL_LOCK.md` Q1Response schema
- **Verification (psql)**:
  ```sql
  SELECT plan_variant, COUNT(*) FROM q14_premium_ranking_v1 WHERE as_of_date='2025-11-26' GROUP BY 1;
  -- Expected: GENERAL=18, NO_REFUND=18
  SELECT COUNT(*) FROM (SELECT r.*, (r.premium_monthly/(r.cancer_amt/10000000.0)) as recomputed FROM q14_premium_ranking_v1 r WHERE as_of_date='2025-11-26') t WHERE ABS(t.premium_per_10m - t.recomputed) > 0.01;
  -- Expected: 0 (formula integrity)
  ```
- **Status**: READY
- **Blocker (if any)**: N/A

---

### Q2
- **Customer Prompt (verbatim)**: "유병자(고혈압/당뇨) 가입 가능한가요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, age, underwriting_condition
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `underwriting_condition`
- **Rule**: Extract `underwriting_condition.value` from slot. Match against known conditions (고혈압, 당뇨, etc.). Coverage exists if condition found.
- **Response Spec**: Text response with underwriting_condition details
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table implementation. File-based slot in compare_rows_v1.jsonl exists but no presentation layer/API endpoint found. Searched: `apps/`, `docs/ui/`, no Q2 UI spec.

---

### Q3
- **Customer Prompt (verbatim)**: "특약 단독 가입 가능한가요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, mandatory_dependency
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `mandatory_dependency`
- **Rule**: Extract `mandatory_dependency.value`. If "단독가입가능" or similar → Yes. If "주계약필수" → No.
- **Response Spec**: Boolean + explanation text
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot exists in compare_rows_v1.jsonl but no UI spec or API endpoint. Searched: `docs/ui/`, `apps/api/`, no Q3 route found.

---

### Q4
- **Customer Prompt (verbatim)**: "재발/재진단 시에도 지급되나요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, payout_frequency
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `payout_frequency`
- **Rule**: Extract `payout_frequency.value`. If "1회한" → No recurrence. If "다회/무제한" → Yes recurrence.
- **Response Spec**: Text response with payout_frequency details
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot exists but no UI/API implementation. Searched: `apps/`, `docs/ui/`, no Q4 spec found.

---

### Q5
- **Customer Prompt (verbatim)**: "면책기간/대기기간은 얼마인가요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, waiting_period
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `waiting_period`
- **Rule**: Extract `waiting_period.value`. Format: "N일" or "N개월". Return as duration.
- **Response Spec**: Duration text (e.g., "90일", "없음")
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot active but no presentation layer. Searched: `docs/ui/`, no Q5 UI spec.

---

### Q6
- **Customer Prompt (verbatim)**: "감액기간/비율은 어떻게 되나요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, reduction
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `reduction`
- **Rule**: Extract `reduction.value`. Format: "N년 감액 M%" or "없음".
- **Response Spec**: Text response with reduction details
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot exists but no UI/API spec. Searched: `apps/`, `docs/ui/`, no Q6 route.

---

### Q7
- **Customer Prompt (verbatim)**: "가입 나이 제한은 어떻게 되나요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, entry_age
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `entry_age`
- **Rule**: Extract `entry_age.value`. Format: "만 N세 ~ M세" or range.
- **Response Spec**: Age range text
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot exists but no presentation spec. Searched: `docs/ui/`, no Q7 UI found.

---

### Q8
- **Customer Prompt (verbatim)**: "타사 가입도 영향 받나요? (업계 누적 한도)"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, industry_aggregate_limit
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `industry_aggregate_limit`
- **Rule**: Extract `industry_aggregate_limit.value`. If exists → Yes (업계누적 한도 적용). If null → No.
- **Response Spec**: Boolean + limit amount text
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot FOUND_GLOBAL in 43 rows (per CUSTOMER_QUESTION_COVERAGE.md) but no UI/API. Searched: `apps/`, no Q8 route.

---

### Q9
- **Customer Prompt (verbatim)**: "보장 개시일은 언제인가요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, start_date
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `start_date`
- **Rule**: Extract `start_date.value`. Format: "계약일로부터 N일" or specific date.
- **Response Spec**: Date/duration text
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot active but no UI spec. Searched: `docs/ui/`, no Q9 presentation found.

---

### Q10
- **Customer Prompt (verbatim)**: "어떤 경우 제외되나요? (면책사항)"
- **Inputs/Filters**: insurer_key, product_id, coverage_code, exclusions
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `exclusions`
- **Rule**: Extract `exclusions.value`. List all exclusion conditions. Format: bullet list.
- **Response Spec**: List of exclusion items
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: No DB table. Slot exists but no UI/API implementation. Searched: `apps/`, `docs/ui/`, no Q10 spec.

---

### Q11
- **Customer Prompt (verbatim)**: "암직접입원비 보장한도(일수구간)는 어떻게 되나요?"
- **Inputs/Filters**: insurer_key, product_id, coverage_code (암직접입원비), benefit_day_range
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `benefit_day_range`
- **Rule**: Extract `benefit_day_range.value`. Format: "N일~M일: X원/일" (multiple ranges possible).
- **Response Spec**: Table with day ranges and daily amounts
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: Slot implemented (STEP NEXT-80 per docs/CUSTOMER_QUESTION_COVERAGE.md) but no DB table. No UI/API spec found. Searched: `docs/ui/`, no Q11 presentation.

---

### Q12
- **Customer Prompt (verbatim)**: "삼성과 메리츠 암진단비 비교해주고 추천해줘"
- **Inputs/Filters**: insurers=['samsung', 'meritz'], age (30/40/50), sex (M/F), plan_variant (NO_REFUND/GENERAL), as_of_date='2025-11-26'
- **SSOT Source**: DB table `product_premium_quote_v2` + `data/compare_v1/compare_rows_v1.jsonl` (for cancer_amt from A4200_1 payout_limit)
- **Rule**: Compare premium_monthly and cancer_amt (payout_limit) for both insurers. Calculate difference (absolute + percentage). Identify cheaper option. Provide recommendation based on premium difference.
- **Response Spec**: `docs/ui/FINAL_VIEWMODEL_LOCK.md` Q12Response schema. Includes: metadata, summary (cheaper_insurer, price_difference, price_difference_pct), products array with premium + coverage details.
- **Verification (psql)**:
  ```sql
  SELECT insurer_key, COUNT(*) FROM product_premium_quote_v2 WHERE as_of_date='2025-11-26' AND insurer_key IN ('samsung','meritz') GROUP BY 1;
  -- Expected: samsung rows + meritz rows for all segments
  ```
- **Status**: READY
- **Blocker (if any)**: N/A

---

### Q13
- **Customer Prompt (verbatim)**: "제자리암/경계성종양 보장 비교해줘 (O/X 매트릭스)"
- **Inputs/Filters**: insurer_keys (multiple), coverage_subtypes (제자리암, 경계성종양, etc.), subtype_coverage_map
- **SSOT Source**: `data/compare_v1/compare_rows_v1.jsonl` → slot `subtype_coverage_map`
- **Rule**: Extract `subtype_coverage_map.value` for each insurer. Create matrix: rows=insurers, cols=subtypes, cells=O/X. O=covered, X=not covered.
- **Response Spec**: Matrix table (insurers × subtypes)
- **Verification (psql)**: N/A (file-based SSOT)
- **Status**: BLOCKED
- **Blocker (if any)**: Slot implemented (STEP NEXT-81 per docs/CUSTOMER_QUESTION_COVERAGE.md: KB 100% + Meritz) but no DB table. No UI/API spec found. Searched: `docs/ui/`, `apps/`, no Q13 presentation layer.

---

### Q14
- **Customer Prompt (verbatim)**: "보험료 가성비 Top4 비교해줘" / "월보험료 순위 보여줘"
- **Inputs/Filters**: age (30/40/50), sex (M/F), plan_variant (NO_REFUND/GENERAL), as_of_date='2025-11-26', limit=4
- **SSOT Source**: DB table `q14_premium_top4_v1`
- **Rule**: Sort by `premium_monthly ASC, insurer_key ASC` (tie-break). Top 4 per segment (age×sex×variant). NO premium_per_10m calculation (unlike Q1).
- **Response Spec**: `docs/ui/FINAL_VIEWMODEL_LOCK.md` Q14Response schema
- **Verification (psql)**:
  ```sql
  SELECT plan_variant, COUNT(*) FROM q14_premium_top4_v1 WHERE as_of_date='2025-11-26' GROUP BY 1;
  -- Expected: GENERAL=24, NO_REFUND=24
  SELECT age, sex, plan_variant, COUNT(*) FROM q14_premium_top4_v1 WHERE as_of_date='2025-11-26' GROUP BY 1,2,3;
  -- Expected: Each segment has exactly 4 rows
  ```
- **Status**: READY
- **Blocker (if any)**: N/A

---

## Summary Table

| Q# | Customer Question | Status | SSOT Source | Blocker |
|----|------------------|--------|-------------|---------|
| Q1 | 가성비 Top3 | READY | `q14_premium_ranking_v1` | - |
| Q2 | 유병자 가입 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q3 | 특약 단독가입 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q4 | 재발지급 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q5 | 면책기간 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q6 | 감액 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q7 | 가입나이 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q8 | 업계누적 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q9 | 보장개시 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q10 | 면책사항 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q11 | 암직접입원비 일수 | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q12 | 삼성 vs 메리츠 | READY | `product_premium_quote_v2` + `compare_rows_v1.jsonl` | - |
| Q13 | 제자리암 O/X | BLOCKED | `compare_rows_v1.jsonl` (slot) | No UI/API spec |
| Q14 | 보험료 Top4 | READY | `q14_premium_top4_v1` | - |

**READY Count**: 3 (Q1, Q12, Q14)
**BLOCKED Count**: 11 (Q2-Q11, Q13)

---

## Implementation Priority (Based on READY Status)

### Tier 1: READY (Can implement immediately)
1. **Q12** - Samsung vs Meritz comparison (비교표 + 추천)
2. **Q14** - Premium Top4 (간단 정렬 UI)
3. **Q1** - Cost-efficiency Top3 (연령별 블록 UI)

### Tier 2: BLOCKED (Requires spec + implementation)
- Q2-Q11, Q13: All require:
  1. API endpoint creation
  2. UI presentation spec
  3. Slot extraction logic (already exists in compare_rows_v1.jsonl)
  4. Response formatting

---

## Governance

- **No estimation**: If SSOT value is NULL/missing, return "없음" or skip that insurer
- **No LLM calculation**: All numeric values must come from DB or file SSOT
- **No fallback**: If premium/coverage missing → BLOCK output, do not guess
- **Version control**: This registry is LOCKED as of 2026-01-12 for as_of_date=2025-11-26

---

## Evidence

All DB validations for Q1/Q12/Q14 documented in:
- `docs/audit/Q_REGISTRY_EVIDENCE_2025-11-26.md`
- `docs/audit/FINAL_SMOKE_LOG_2025-11-26.md`

---

**END OF REGISTRY**
