# PHASE2 Q11 UI SPEC

**Query:** Q11 - 암직접입원비 담보 중 보장한도가 다른 상품 찾기
**Status:** READY (Backend + Frontend Spec)
**Date:** 2025-01-12

---

## Query Definition (HARDCODED)

**User Question:**
> "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"

**Target Values:**
- `daily_benefit_amount_won` = 일당 금액(원)
- `duration_limit_days` = 최대 보장일수(일)

**Coverage Filter:**
- `coverage_title =~ /암직접.*입원/i`
- **NO** fallback to other codes (암진단비 etc.)
- If no A6200 data exists, use coverage_title match only

---

## Sorting (DETERMINISTIC)

**Rule (IMMUTABLE):**
1. `duration_limit_days` DESC (null sorts LAST)
2. `daily_benefit_amount_won` DESC (null sorts LAST)
3. `insurer_key` ASC (tie-break)

**Example:**
```
KB: 180 days, 10,000원/일 → Rank 1
DB: null days, 3,000,000원/일 → Rank 2
Meritz: null days, 140,000원/일 → Rank 3
```

---

## UI Output Format

### 1. Header
```
질문: 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘

기준: 일당 금액과 최대 보장일수로 비교합니다.
```

### 2. Table (PHASE1 스타일)

| 순위 | 보험사 | 담보명 | 일당 | 보장일수 | 근거 |
|------|--------|--------|------|----------|------|
| 1 | KB | 암직접치료입원일당 | 10,000원/일 | 최대 180일 | 가입설계서 p.3 |
| 2 | DB | 암직접치료입원일당Ⅱ | 3,000,000원/일 | UNKNOWN (근거 부족) | 약관 p.168 |
| 3 | Meritz | 암직접치료입원일당 | 140,000원/일 | UNKNOWN (근거 부족) | 가입설계서 p.6 |

**Column Widths (approximate):**
- 순위: 10%
- 보험사: 15%
- 담보명: 20%
- 일당: 20%
- 보장일수: 20%
- 근거: 15%

### 3. Evidence Display

**근거 컬럼:**
- Format: `{doc_type} p.{page}`
- Hover/click → Show `excerpt` (trimmed to 200 chars)
- If `evidence.excerpt` is empty or null → omit excerpt display

---

## Forbidden Behaviors

❌ **DO NOT:**
1. Estimate or fallback to arbitrary values (e.g., 90/120 days)
2. Mix unrelated coverages (e.g., 암진단비)
3. Show coverage if `duration_limit_days=null` as a specific number
4. Sort by any criteria other than the spec

✅ **MUST:**
1. Display `null` as "UNKNOWN (근거 부족)"
2. Use deterministic sort order (days DESC, daily DESC, insurer ASC)
3. Show evidence attribution (doc_type + page)

---

## API Contract

**Endpoint:** `GET /q11`

**Query Params:**
- `as_of_date` (default: 2025-11-26)
- `insurers` (optional, comma-separated)

**Response Shape:**
```json
{
  "query_id": "Q11",
  "as_of_date": "2025-11-26",
  "items": [
    {
      "rank": 1,
      "insurer_key": "kb",
      "coverage_name": "암직접치료입원일당",
      "daily_benefit_amount_won": 10000,
      "duration_limit_days": 180,
      "evidence": {
        "doc_type": "가입설계서",
        "page": 3,
        "excerpt": "..."
      }
    },
    {
      "rank": 2,
      "insurer_key": "db",
      "coverage_name": "암직접치료입원일당Ⅱ",
      "daily_benefit_amount_won": 3000000,
      "duration_limit_days": null,
      "evidence": {
        "doc_type": "약관",
        "page": 168,
        "excerpt": "..."
      }
    }
  ]
}
```

---

## Frontend Implementation

**Component Name:** `Q11CancerHospitalizationCard`

**Data Flow:**
1. Fetch `GET /q11?as_of_date=2025-11-26`
2. Render table from `response.items`
3. Display:
   - `daily_benefit_amount_won` → `{value.toLocaleString()}원/일`
   - `duration_limit_days`:
     - If `null` → "UNKNOWN (근거 부족)"
     - If number → `최대 {value}일`
   - Evidence → `{doc_type} p.{page}` (with hover for excerpt)

**Styling:**
- Reuse PHASE1 table styles
- Match screenshot layout (header + table + evidence column)

---

## Testing Checklist

✅ Backend:
- [x] Endpoint `/q11` returns 200
- [x] Sorting is deterministic
- [x] Evidence is present for all items

⬜ Frontend:
- [ ] Table renders with correct columns
- [ ] UNKNOWN displays for null values
- [ ] Evidence hover/click shows excerpt
- [ ] Sorting order matches backend response

---

## Notes

- **Data Limitation:** As of 2025-11-26, only KB has non-null `duration_limit_days` (180). All others display UNKNOWN. This is acceptable per spec.
- **No A6200 Code:** The data uses `coverage_title` matching (`암직접.*입원`) instead of canonical code A6200. This is due to data structure differences in compare_rows_v1.jsonl.

---

**Status:** SPEC LOCKED ✅
**Next Step:** Implement frontend Q11 card component
