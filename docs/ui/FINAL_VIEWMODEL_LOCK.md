# FINAL ViewModel LOCK - Q1/Q12/Q14 Response Specification

**Date**: 2026-01-12
**Status**: 🔒 LOCKED
**Scope**: Q1 (Cost-Efficiency), Q12 (Samsung vs Meritz), Q14 (Premium Top4)
**as_of_date**: 2025-11-26
**plan_variants**: NO_REFUND, GENERAL

---

## Absolute Rules

### Data Source (SSOT)
- **Q14**: `q14_premium_top4_v1` table
- **Q1**: `q14_premium_ranking_v1` table
- **Q12**: `product_premium_quote_v2` table

### Forbidden Operations
❌ NO premium estimation or imputation
❌ NO cancer_amt fallback (must use actual DB values)
❌ NO mixing Q1/Q14 formulas (Q14 = simple premium sort, Q1 = premium_per_10m)
❌ NO GENERAL data if not in DB (skip segment instead)

### Database Connection
```
postgresql://inca_admin:inca_secure_prod_2025_db_key@127.0.0.1:5432/inca_rag_scope
```

---

## Q14: Premium Top4 Ranking

### Purpose
Show the 4 cheapest insurance products by monthly premium for a given segment.

### Input Parameters
```typescript
interface Q14Request {
  as_of_date: string;        // '2025-11-26'
  plan_variant: string;      // 'NO_REFUND' | 'GENERAL'
  age: number;               // 30 | 40 | 50
  sex: string;               // 'M' | 'F'
  insurer_keys?: string[];   // Optional filter
}
```

### Sorting Rule (LOCKED)
```sql
ORDER BY premium_monthly ASC, insurer_key ASC
```

### Response Schema
```typescript
interface Q14Response {
  metadata: {
    as_of_date: string;
    plan_variant: string;
    age: number;
    sex: string;
    total_insurers: number;
  };
  rankings: Q14Ranking[];
}

interface Q14Ranking {
  rank: number;              // 1-4
  insurer_key: string;
  product_id: string;
  premium_monthly: number;   // 원

  // Optional fields
  product_name?: string;
  pay_term_years?: number;
  ins_term_years?: number;
  smoke?: string;
}
```

### Response Example (JSON)
```json
{
  "metadata": {
    "as_of_date": "2025-11-26",
    "plan_variant": "NO_REFUND",
    "age": 30,
    "sex": "M",
    "total_insurers": 8
  },
  "rankings": [
    {
      "rank": 1,
      "insurer_key": "meritz",
      "product_id": "30654",
      "premium_monthly": 96111,
      "product_name": "메리츠 The 안심 암보험",
      "pay_term_years": 20,
      "ins_term_years": 100,
      "smoke": "N"
    },
    {
      "rank": 2,
      "insurer_key": "lotte",
      "product_id": "30636",
      "premium_monthly": 118594,
      "product_name": "롯데 Super 암보험",
      "pay_term_years": 20,
      "ins_term_years": 100,
      "smoke": "N"
    },
    {
      "rank": 3,
      "insurer_key": "hanwha",
      "product_id": "30635",
      "premium_monthly": 110981,
      "product_name": "한화 무배당 암보험",
      "pay_term_years": 20,
      "ins_term_years": 100,
      "smoke": "N"
    },
    {
      "rank": 4,
      "insurer_key": "samsung",
      "product_id": "30626",
      "premium_monthly": 132685,
      "product_name": "삼성 무배당 암보험",
      "pay_term_years": 20,
      "ins_term_years": 100,
      "smoke": "N"
    }
  ]
}
```

### Prohibited Fields
❌ `premium_per_10m` - This is Q1's metric only
❌ `cancer_amt` - Internal calculation only

---

## Q1: Cost-Efficiency Ranking (Premium per 10M Coverage)

### Purpose
Show the 3 most cost-efficient insurance products based on premium per 10 million won of cancer coverage.

### Formula (LOCKED)
```
premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)
Unit: 원/1천만원 (how much premium per 10M won of coverage)
```

### Input Parameters
```typescript
interface Q1Request {
  as_of_date: string;        // '2025-11-26'
  plan_variant: string;      // 'NO_REFUND' | 'GENERAL'
  age: number;               // 30 | 40 | 50
  sex: string;               // 'M' | 'F'
  insurer_keys?: string[];   // Optional filter
}
```

### Sorting Rule (LOCKED)
```sql
ORDER BY premium_per_10m ASC, premium_monthly ASC, insurer_key ASC
```

### Response Schema
```typescript
interface Q1Response {
  metadata: {
    as_of_date: string;
    plan_variant: string;
    age: number;
    sex: string;
    total_candidates: number;
  };
  rankings: Q1Ranking[];
}

interface Q1Ranking {
  rank: number;                // 1-3
  insurer_key: string;
  product_id: string;
  premium_monthly: number;     // 원
  cancer_amt: number;          // 원 (e.g., 30000000 = 3천만원)
  premium_per_10m: number;     // 원/1천만원

  // Optional
  product_name?: string;
}
```

### Response Example (JSON)
```json
{
  "metadata": {
    "as_of_date": "2025-11-26",
    "plan_variant": "GENERAL",
    "age": 30,
    "sex": "F",
    "total_candidates": 8
  },
  "rankings": [
    {
      "rank": 1,
      "insurer_key": "meritz",
      "product_id": "30654",
      "premium_monthly": 96279,
      "cancer_amt": 30000000,
      "premium_per_10m": 32093.00,
      "product_name": "메리츠 The 안심 암보험"
    },
    {
      "rank": 2,
      "insurer_key": "samsung",
      "product_id": "30626",
      "premium_monthly": 100080,
      "cancer_amt": 30000000,
      "premium_per_10m": 33360.00,
      "product_name": "삼성 무배당 암보험"
    },
    {
      "rank": 3,
      "insurer_key": "hanwha",
      "product_id": "30635",
      "premium_monthly": 104863,
      "cancer_amt": 30000000,
      "premium_per_10m": 34954.33,
      "product_name": "한화 무배당 암보험"
    }
  ]
}
```

### Critical Note
- `cancer_amt` MUST come from DB (A4200_1 payout_limit)
- If `cancer_amt` is NULL or 0, EXCLUDE that insurer (do NOT use fallback)

---

## Q12: Samsung vs Meritz Comparison

### Purpose
Compare premium and coverage between Samsung and Meritz for specific segment.

### Input Parameters
```typescript
interface Q12Request {
  as_of_date: string;        // '2025-11-26'
  plan_variant: string;      // 'NO_REFUND' | 'GENERAL'
  age: number;               // 30 | 40 | 50
  sex: string;               // 'M' | 'F'
  insurers: string[];        // ['samsung', 'meritz']
}
```

### Response Schema
```typescript
interface Q12Response {
  metadata: {
    as_of_date: string;
    plan_variant: string;
    age: number;
    sex: string;
    comparison_type: string;  // 'samsung_vs_meritz'
  };
  summary: {
    cheaper_insurer: string;   // 'samsung' | 'meritz'
    price_difference: number;  // 원
    price_difference_pct: number;  // %
  };
  products: Q12Product[];
}

interface Q12Product {
  insurer_key: string;
  product_id: string;
  product_name: string;
  premium_monthly: number;   // 원

  // Coverage details (optional)
  cancer_amt?: number;       // 원
  pay_term_years?: number;
  ins_term_years?: number;
}
```

### Response Example (JSON)
```json
{
  "metadata": {
    "as_of_date": "2025-11-26",
    "plan_variant": "NO_REFUND",
    "age": 30,
    "sex": "M",
    "comparison_type": "samsung_vs_meritz"
  },
  "summary": {
    "cheaper_insurer": "meritz",
    "price_difference": 36574,
    "price_difference_pct": 27.56
  },
  "products": [
    {
      "insurer_key": "samsung",
      "product_id": "30626",
      "product_name": "삼성 무배당 암보험",
      "premium_monthly": 132685,
      "cancer_amt": 30000000,
      "pay_term_years": 20,
      "ins_term_years": 100
    },
    {
      "insurer_key": "meritz",
      "product_id": "30654",
      "product_name": "메리츠 The 안심 암보험",
      "premium_monthly": 96111,
      "cancer_amt": 30000000,
      "pay_term_years": 20,
      "ins_term_years": 100
    }
  ]
}
```

### Data Source Query Example
```sql
SELECT
  insurer_key,
  product_id,
  premium_monthly_total as premium_monthly,
  age, sex, plan_variant, as_of_date
FROM product_premium_quote_v2
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND age = 30
  AND sex = 'M'
  AND insurer_key IN ('samsung', 'meritz')
```

---

## TypeScript Type Definitions

Location: `apps/web/src/lib/types.ts` (or equivalent shared types file)

```typescript
// ============================================
// Q14: Premium Top4
// ============================================
export interface Q14Request {
  as_of_date: string;
  plan_variant: 'NO_REFUND' | 'GENERAL';
  age: 30 | 40 | 50;
  sex: 'M' | 'F';
  insurer_keys?: string[];
}

export interface Q14Ranking {
  rank: number;
  insurer_key: string;
  product_id: string;
  premium_monthly: number;
  product_name?: string;
  pay_term_years?: number;
  ins_term_years?: number;
  smoke?: string;
}

export interface Q14Response {
  metadata: {
    as_of_date: string;
    plan_variant: string;
    age: number;
    sex: string;
    total_insurers: number;
  };
  rankings: Q14Ranking[];
}

// ============================================
// Q1: Cost-Efficiency
// ============================================
export interface Q1Request {
  as_of_date: string;
  plan_variant: 'NO_REFUND' | 'GENERAL';
  age: 30 | 40 | 50;
  sex: 'M' | 'F';
  insurer_keys?: string[];
}

export interface Q1Ranking {
  rank: number;
  insurer_key: string;
  product_id: string;
  premium_monthly: number;
  cancer_amt: number;
  premium_per_10m: number;
  product_name?: string;
}

export interface Q1Response {
  metadata: {
    as_of_date: string;
    plan_variant: string;
    age: number;
    sex: string;
    total_candidates: number;
  };
  rankings: Q1Ranking[];
}

// ============================================
// Q12: Samsung vs Meritz Comparison
// ============================================
export interface Q12Request {
  as_of_date: string;
  plan_variant: 'NO_REFUND' | 'GENERAL';
  age: 30 | 40 | 50;
  sex: 'M' | 'F';
  insurers: ['samsung', 'meritz'];
}

export interface Q12Product {
  insurer_key: string;
  product_id: string;
  product_name: string;
  premium_monthly: number;
  cancer_amt?: number;
  pay_term_years?: number;
  ins_term_years?: number;
}

export interface Q12Response {
  metadata: {
    as_of_date: string;
    plan_variant: string;
    age: number;
    sex: string;
    comparison_type: 'samsung_vs_meritz';
  };
  summary: {
    cheaper_insurer: 'samsung' | 'meritz';
    price_difference: number;
    price_difference_pct: number;
  };
  products: Q12Product[];
}
```

---

## Implementation Notes

### Backend API Endpoints (Suggested)
```
POST /api/v1/insurance/ranking/premium-top4    # Q14
POST /api/v1/insurance/ranking/cost-efficiency # Q1
POST /api/v1/insurance/compare/samsung-meritz  # Q12
```

### Frontend Display Guidance

**Q14 Display**:
- Show as simple table: Rank | Insurer | Premium
- Highlight rank 1 (cheapest)
- Format premium with commas: `96,111원`

**Q1 Display**:
- Show 3 age blocks (30/40/50) separately
- Each block shows Top 3 with premium_per_10m metric
- Explain metric: "1천만원 암진단금 받기 위한 월 보험료"
- Format: `32,093원/1천만원`

**Q12 Display**:
- Side-by-side comparison cards
- Show percentage difference prominently
- Use visual indicator (green/red) for cheaper option

---

## Validation

All implementations MUST pass:
```bash
python3 tools/audit/validate_final_q1_q12_q14.py --as-of-date 2025-11-26
```

See `docs/audit/FINAL_SMOKE_LOG_2025-11-26.md` for expected output.

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-12 | 1.0 | Initial LOCK - Q1/Q12/Q14 specs finalized |

---

**END OF SPECIFICATION**
