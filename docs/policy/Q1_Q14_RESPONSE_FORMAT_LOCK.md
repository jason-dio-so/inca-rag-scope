# Q1/Q14 Customer Response Format LOCK

**Version**: 1.0
**Status**: 🔒 **LOCKED**
**Date**: 2026-01-12
**Applies To**: Frontend, Backend, Database

---

## 📋 Purpose

This document defines the **IMMUTABLE response format** for Q1 (가성비 Top3) and Q14 (보험료 Top4) queries served to customers.

**Scope**:
- Frontend display format
- Backend API payload structure
- Database query contracts
- NULL handling rules
- Forbidden patterns (fallbacks, estimations, mixing)

**Audience**:
- Frontend developers (display logic)
- Backend developers (API endpoints)
- QA engineers (response validation)
- Product managers (customer-facing spec)

---

## 🎯 Q14: 보험료 Top4

### Query Definition

**Question Card ID**: `Q14`

**Customer Intent**: "보험료가 가장 저렴한 상품은 어디인가요?" (Which products have the lowest premiums?)

**Ranking Basis**: Monthly premium (lowest = best)

### Response Format

**Top-N Count**: **4 products** per segment

**Sorting Rule** (IMMUTABLE):
```
ORDER BY premium_monthly_total ASC,
         insurer_key ASC
```

**Output Schema**:
```typescript
interface Q14Response {
  segment: {
    age: 30 | 40 | 50;
    sex: "M" | "F";
    plan_variant: "GENERAL" | "NO_REFUND";
  };
  rankings: Q14Ranking[];  // length = 4
}

interface Q14Ranking {
  rank: 1 | 2 | 3 | 4;
  insurer_key: string;
  insurer_name_kr: string;
  product_name: string;
  premium_monthly: number;  // 원 (integer)
  plan_variant_label: "일반형" | "무해지형";
}
```

### Example Response (Age 30, Male, NO_REFUND)

```json
{
  "segment": {
    "age": 30,
    "sex": "M",
    "plan_variant": "NO_REFUND"
  },
  "rankings": [
    {
      "rank": 1,
      "insurer_key": "lotte",
      "insurer_name_kr": "롯데손해보험",
      "product_name": "Super 암보험 2.0",
      "premium_monthly": 52000,
      "plan_variant_label": "무해지형"
    },
    {
      "rank": 2,
      "insurer_key": "meritz",
      "insurer_name_kr": "메리츠화재",
      "product_name": "The 암보험",
      "premium_monthly": 54500,
      "plan_variant_label": "무해지형"
    },
    {
      "rank": 3,
      "insurer_key": "hyundai",
      "insurer_name_kr": "현대해상",
      "product_name": "굿앤굿 암보험",
      "premium_monthly": 55500,
      "plan_variant_label": "무해지형"
    },
    {
      "rank": 4,
      "insurer_key": "samsung",
      "insurer_name_kr": "삼성화재",
      "product_name": "다이렉트 암보험",
      "premium_monthly": 56200,
      "plan_variant_label": "무해지형"
    }
  ]
}
```

### Display Format (Frontend)

**Table Format**:
```
순위 | 보험사        | 상품명                | 월보험료
-----|--------------|----------------------|----------
 1위 | 롯데손해보험  | Super 암보험 2.0      | 52,000원
 2위 | 메리츠화재    | The 암보험           | 54,500원
 3위 | 현대해상      | 굿앤굿 암보험         | 55,500원
 4위 | 삼성화재      | 다이렉트 암보험       | 56,200원
```

**Number Formatting Rules**:
- Premium: Add thousand separators (e.g., `52,000`)
- Append currency unit: `원`
- No decimal places (premiums are integers)

**Plan Variant Label**:
- `NO_REFUND` → "무해지형"
- `GENERAL` → "일반형"

---

## 🎯 Q1: 가성비 Top3

### Query Definition

**Question Card ID**: `Q1`

**Customer Intent**: "암보험 가성비가 좋은 상품은 어디인가요?" (Which products have the best cost-efficiency for cancer insurance?)

**Ranking Basis**: Premium per 10 million won of cancer coverage (lowest = best value)

### Response Format

**Top-N Count**: **3 products** per segment

**Sorting Rule** (IMMUTABLE):
```
ORDER BY premium_per_10m ASC,
         premium_monthly ASC,
         insurer_key ASC
```

**Output Schema**:
```typescript
interface Q1Response {
  segment: {
    age: 30 | 40 | 50;
    sex: "M" | "F";
    plan_variant: "GENERAL" | "NO_REFUND";
  };
  rankings: Q1Ranking[];  // length = 3
}

interface Q1Ranking {
  rank: 1 | 2 | 3;
  insurer_key: string;
  insurer_name_kr: string;
  product_name: string;
  premium_monthly: number;      // 원 (integer)
  cancer_amt: number;           // 원 (integer)
  premium_per_10m: number;      // 원/1천만원 (float, 2 decimals)
  plan_variant_label: "일반형" | "무해지형";
}
```

### Example Response (Age 30, Male, NO_REFUND)

```json
{
  "segment": {
    "age": 30,
    "sex": "M",
    "plan_variant": "NO_REFUND"
  },
  "rankings": [
    {
      "rank": 1,
      "insurer_key": "lotte",
      "insurer_name_kr": "롯데손해보험",
      "product_name": "Super 암보험 2.0",
      "premium_monthly": 52000,
      "cancer_amt": 30000000,
      "premium_per_10m": 17333.33,
      "plan_variant_label": "무해지형"
    },
    {
      "rank": 2,
      "insurer_key": "meritz",
      "insurer_name_kr": "메리츠화재",
      "product_name": "The 암보험",
      "premium_monthly": 54500,
      "cancer_amt": 30000000,
      "premium_per_10m": 18166.67,
      "plan_variant_label": "무해지형"
    },
    {
      "rank": 3,
      "insurer_key": "hyundai",
      "insurer_name_kr": "현대해상",
      "product_name": "굿앤굿 암보험",
      "premium_monthly": 55500,
      "cancer_amt": 30000000,
      "premium_per_10m": 18500.00,
      "plan_variant_label": "무해지형"
    }
  ]
}
```

### Display Format (Frontend)

**Table Format**:
```
순위 | 보험사        | 월보험료  | 암진단비   | 1천만원당 보험료
-----|--------------|----------|-----------|----------------
 1위 | 롯데손해보험  | 52,000원 | 3,000만원 | 17,333원
 2위 | 메리츠화재    | 54,500원 | 3,000만원 | 18,167원
 3위 | 현대해상      | 55,500원 | 3,000만원 | 18,500원
```

**Number Formatting Rules**:
- `premium_monthly`: Add thousand separators, append `원`
- `cancer_amt`: Divide by 10,000, add thousand separators, append `만원`
  - Example: `30000000` → `3,000만원`
- `premium_per_10m`: Add thousand separators, NO decimal places for display
  - Example: `17333.33` → `17,333원`
  - Note: Store as float in backend, round to integer for display

**Plan Variant Label**:
- `NO_REFUND` → "무해지형"
- `GENERAL` → "일반형"

### Calculation Verification (Backend)

**Formula** (must be computed server-side):
```python
premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)
```

**Example**:
```python
premium_monthly = 52000      # 원
cancer_amt = 30000000        # 원 (3천만원)

premium_per_10m = 52000 / (30000000 / 10000000)
                = 52000 / 3.0
                = 17333.33   # 원/1천만원
```

**Precision**: Store as `DECIMAL(10,2)` in database, round to 2 decimal places

---

## 🚫 Forbidden Patterns

### For Q14 (보험료 Top4)

**NEVER**:
- ❌ Use GENERAL premium to estimate NO_REFUND (or vice versa)
- ❌ Apply multiplier factors (e.g., "NO_REFUND = GENERAL × 0.85")
- ❌ Fall back to file-based data if DB is missing
- ❌ Show estimated/interpolated premiums
- ❌ Mix plan_variant values in same response

**NULL Handling**:
- If `premium_monthly` is NULL → EXCLUDE from ranking (don't show)
- If entire segment has <4 products → Show only available products (don't fill gaps)

### For Q1 (가성비 Top3)

**NEVER**:
- ❌ Use default cancer_amt (e.g., "assume 3000만원")
- ❌ Estimate cancer_amt from other insurers
- ❌ Calculate premium_per_10m client-side (MUST be from DB)
- ❌ Show products with NULL cancer_amt
- ❌ Use premium_monthly_total as fallback for premium_monthly

**NULL Handling**:
- If `cancer_amt` is NULL → EXCLUDE from ranking
- If `premium_monthly` is NULL → EXCLUDE from ranking
- If `premium_per_10m` formula fails → EXCLUDE (don't estimate)
- If entire segment has <3 products → Show only available products

---

## 🎨 Frontend Integration

### Component Props

**Q14 Component**:
```typescript
interface Q14Props {
  segment: {
    age: 30 | 40 | 50;
    sex: "M" | "F";
    plan_variant: "GENERAL" | "NO_REFUND";
  };
  rankings: Q14Ranking[];
  loading: boolean;
  error?: string;
}
```

**Q1 Component**:
```typescript
interface Q1Props {
  segment: {
    age: 30 | 40 | 50;
    sex: "M" | "F";
    plan_variant: "GENERAL" | "NO_REFUND";
  };
  rankings: Q1Ranking[];
  loading: boolean;
  error?: string;
}
```

### Error States

**No Data Available**:
```
죄송합니다. 현재 해당 조건에 맞는 상품 정보가 없습니다.
다른 연령대나 상품 유형을 선택해 주세요.
```

**API Failure**:
```
일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
```

**Partial Data** (e.g., only 2 products instead of 4 for Q14):
- Show available products
- Display message: "현재 {count}개 상품만 비교 가능합니다."

---

## 🔌 Backend API Contract

### Q14 Endpoint

**Path**: `GET /api/rankings/premium-top4`

**Query Parameters**:
```
?age=30
&sex=M
&plan_variant=NO_REFUND
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "segment": { "age": 30, "sex": "M", "plan_variant": "NO_REFUND" },
    "rankings": [...]
  },
  "meta": {
    "as_of_date": "2025-11-26",
    "total_count": 4
  }
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NO_DATA",
    "message": "No premium data available for the specified segment"
  }
}
```

### Q1 Endpoint

**Path**: `GET /api/rankings/cost-efficiency-top3`

**Query Parameters**:
```
?age=30
&sex=M
&plan_variant=NO_REFUND
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "segment": { "age": 30, "sex": "M", "plan_variant": "NO_REFUND" },
    "rankings": [...]
  },
  "meta": {
    "as_of_date": "2025-11-26",
    "total_count": 3
  }
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NO_DATA",
    "message": "No ranking data available for the specified segment"
  }
}
```

### Database Query Template

**Q14 Query**:
```sql
SELECT
  rank,
  insurer_key,
  product_name,
  premium_monthly_total AS premium_monthly,
  seg_age AS age,
  seg_sex AS sex,
  plan_variant
FROM q14_premium_top4_v1
WHERE as_of_date = $1
  AND seg_age = $2
  AND seg_sex = $3
  AND plan_variant = $4
ORDER BY rank ASC;
```

**Q1 Query**:
```sql
SELECT
  rank,
  insurer_key,
  product_name,
  premium_monthly,
  cancer_amt,
  premium_per_10m,
  seg_age AS age,
  seg_sex AS sex,
  plan_variant
FROM q14_premium_ranking_v1
WHERE as_of_date = $1
  AND seg_age = $2
  AND seg_sex = $3
  AND plan_variant = $4
ORDER BY rank ASC;
```

---

## 📊 Segment Coverage Matrix

**Plan Variants Supported**:
- `NO_REFUND` (무해지형) — **PRIMARY** (current lock scope)
- `GENERAL` (일반형) — FUTURE (not in 2025-11-26 snapshot)

**Age Groups Supported**:
- 30세
- 40세
- 50세

**Sex Supported**:
- M (남성)
- F (여성)

**Total Segments** (current):
- 3 ages × 2 sexes × 1 plan_variant = **6 segments**

**Future Expansion** (when GENERAL data is available):
- 3 ages × 2 sexes × 2 plan_variants = **12 segments**

---

## 🔐 Response Validation Rules

### Q14 Validation

**MUST checks**:
1. `rankings.length <= 4` (never exceed Top-4)
2. `rank` values are sequential (1, 2, 3, 4)
3. No duplicate `insurer_key` in same response
4. `premium_monthly > 0` (positive integers)
5. All `insurer_key` values exist in `insurer` table

**SHOULD checks**:
1. `rankings.length == 4` (unless data is sparse)
2. Premiums are sorted ascending
3. `plan_variant_label` matches `plan_variant` enum

### Q1 Validation

**MUST checks**:
1. `rankings.length <= 3` (never exceed Top-3)
2. `rank` values are sequential (1, 2, 3)
3. No duplicate `insurer_key` in same response
4. `premium_monthly > 0`
5. `cancer_amt > 0`
6. `premium_per_10m` matches formula:
   ```
   abs(premium_per_10m - (premium_monthly / (cancer_amt / 10_000_000))) < 0.01
   ```

**SHOULD checks**:
1. `rankings.length == 3` (unless data is sparse)
2. `premium_per_10m` values are sorted ascending
3. `cancer_amt` is typically in range [10,000,000 ~ 50,000,000] (1천만원 ~ 5천만원)

---

## 🧪 Test Cases

### Q14 Test Case 1: Normal Response

**Input**:
- age: 30
- sex: M
- plan_variant: NO_REFUND

**Expected Output**:
- 4 rankings
- Ranks: [1, 2, 3, 4]
- Premiums sorted ascending
- All fields non-null

### Q14 Test Case 2: Sparse Data

**Input**:
- age: 30
- sex: M
- plan_variant: GENERAL (假设只有2个产品)

**Expected Output**:
- 2 rankings (not 4)
- Ranks: [1, 2]
- No synthetic/placeholder data

### Q1 Test Case 1: Normal Response

**Input**:
- age: 40
- sex: F
- plan_variant: NO_REFUND

**Expected Output**:
- 3 rankings
- Ranks: [1, 2, 3]
- `premium_per_10m` formula verified
- All fields non-null

### Q1 Test Case 2: Formula Edge Case

**Input**:
- premium_monthly: 100000
- cancer_amt: 50000000 (5천만원)

**Expected Calculation**:
```
premium_per_10m = 100000 / (50000000 / 10000000)
                = 100000 / 5.0
                = 20000.00
```

**Display**: "20,000원/1천만원"

---

## 📝 Change Log

**Version 1.0** (2026-01-12):
- Initial lock for `as_of_date=2025-11-26`
- Q14: 24 rows (6 segments × Top4)
- Q1: 18 rows (6 segments × Top3)
- Plan variant: NO_REFUND only

**Future Versions**:
- v1.1: Add GENERAL plan_variant support
- v1.2: Expand age groups (20/25/35/45/55/60)
- v2.0: Add smoking status dimension

---

## 🔗 References

**Evidence**:
- `docs/audit/STEP_NEXT_FINAL_EVIDENCE_2025-11-26.md`

**Implementation**:
- Backend: `apps/api/src/routes/rankings/`
- Frontend: `apps/web/src/components/Rankings/`

**Database Schema**:
- `schema/050_q14_premium_ranking.sql` (Q1)
- `schema/051_q14_premium_top4.sql` (Q14)

**Active Constitution**:
- `docs/active_constitution.md` (formula rules)

---

**Document Version**: 1.0
**Status**: 🔒 **LOCKED**
**Last Updated**: 2026-01-12
**Review Trigger**: New as_of_date or schema change
