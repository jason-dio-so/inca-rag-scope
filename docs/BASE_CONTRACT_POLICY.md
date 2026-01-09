# Base Contract (기본계약/의무담보) Policy SSOT

**Version**: v1
**Date**: 2025-01-09
**Purpose**: Q3 기본계약 최소화 계산 기준 정의

---

## 1. Policy Definition

**기본계약 (Base Contract)**: 보험 상품의 필수 가입 담보로, 일반적으로 사망 및 장해 보장을 포함

**SSOT Location**: `/data/policy/base_contract_codes.json`

---

## 2. Base Contract Codes (LOCKED)

**v1 Definition** (2025-01-09):

| Code | Name | Category |
|------|------|----------|
| `A1100` | 질병사망 | 사망 |
| `A1300` | 상해사망 | 사망 |
| `A3300_1` | 상해후유장해 | 장해 |

**Rationale**:
- 사망/장해는 보험의 핵심 기본 보장
- 4개 보험사 표준 구조 기준 최소 구성
- 기존 A4001~A4003는 DEPRECATED (신정원 코드 체계 변경)

---

## 3. Calculation Rules

### 3.1 base_contract_monthly_sum

**Formula**:
```python
base_contract_monthly_sum = sum(
    coverage.premium_monthly_coverage
    for coverage in coverage_premium_quote
    if coverage.coverage_code in BASE_CONTRACT_CODES
)
```

**Rules**:
1. Coverage가 없으면 → `base_contract_monthly_sum = NULL`
2. NULL이면 Q3에서 제외 (추정 금지)
3. 보험료가 0인 coverage는 제외 (0원 담보는 계산 안 함)

### 3.2 base_contract_min_flags

**Fields**:
```json
{
  "has_death": bool,        // A1100 or A1300 존재
  "has_disability": bool,   // A3300_1 존재
  "min_level": int          // len(base_contract_codes found)
}
```

---

## 4. Usage in Q3

**Q3 Question**: "의무 담보 최소화 (기본계약 최소 가입조건 낮음)"

**Query Pattern**:
```sql
SELECT
    insurer_key,
    product_key,
    plan_variant,
    base_contract_monthly_sum,
    base_contract_min_flags
FROM pct_v3
WHERE base_contract_monthly_sum IS NOT NULL
ORDER BY base_contract_monthly_sum ASC
LIMIT 10;
```

**Output**:
- Top 10 products with lowest base contract premium
- Display: `base_contract_monthly_sum` (원), `base_contract_min_flags`
- **Prohibited**: "가성비", "저렴", "추천" marketing phrases

---

## 5. Versioning and Updates

**Update Process**:
1. Modify `/data/policy/base_contract_codes.json`
2. Increment `version` field
3. Update `as_of_date`
4. Re-run PCT v3 builder
5. Validate Q3 output

**Deprecation**:
- Old codes: A4001, A4002, A4003 (STEP NEXT-P/Q)
- Reason: 신정원 코드 체계 변경 → A1xxx/A3xxx 사용

---

## 6. Constraints

1. **NO estimation**: Missing base contract → NULL (not 0)
2. **NO inference**: Coverage not in API → excluded
3. **NO marketing**: Objective calculation only

---

**Status**: ✅ LOCKED
**Authority**: STEP NEXT-R
**Next Review**: When coverage code structure changes
