# Q11 Reference Block Policy

## Purpose
Allow displaying business method (사업방법서) coverage information in Q11 WITHOUT affecting proposal SSOT ranking/comparison.

## Constitutional Rules (ZERO TOLERANCE)

### 1. SSOT Separation
- **items[]**: ONLY coverage_code A6200 from `compare_tables_v1.jsonl` (proposal SSOT)
- **references[]**: Business method only sources from `q11_references_v1.jsonl`
- ❌ NEVER mix references into items
- ❌ NEVER use references for ranking/sorting/premium calculation

### 2. Data Sources
- **items**: `data/compare_v1/compare_tables_v1.jsonl` (Step4 output, proposal-based)
- **references**: `data/compare_v1/q11_references_v1.jsonl` (NEW, business method only)

### 3. Reference Schema (LOCK)
```json
{
  "insurer_key": "hanwha",
  "coverage_title": "암(4대유사암포함)직접치료입원비Ⅱ(요양병원제외,1일이상180일한도)",
  "duration_limit_days": 180,
  "daily_benefit_amount_won": null,
  "evidence": {
    "doc_type": "사업방법서",
    "page": 7,
    "excerpt": "..."
  },
  "badge": "REFERENCE_ONLY_NOT_IN_PROPOSAL",
  "note": "가입설계서에 미포함, 사업방법서 7페이지에 명시"
}
```

### 4. API Response Structure
```json
{
  "query_id": "Q11",
  "as_of_date": "2025-11-26",
  "coverage_code": "A6200",
  "items": [...],  // Ranked list (proposal SSOT)
  "references": [  // Business method references (no ranking)
    {
      "insurer_key": "hanwha",
      "coverage_title": "...",
      "badge": "REFERENCE_ONLY_NOT_IN_PROPOSAL"
    }
  ]
}
```

### 5. UI Display Rules
- **items**: Standard ranking table (with premium, evidence)
- **references**: Separate section BELOW items
- **Mandatory label**:
  > ※ 아래 정보는 가입설계서 기준 산출 대상이 아니며, 사업방법서에 존재하는 것으로 확인되었습니다(보험료/순위 미반영).

### 6. Forbidden Actions
- ❌ Add references to items array
- ❌ Use references for sorting/ranking
- ❌ Calculate premium using references
- ❌ Estimate/infer values (null if no evidence)
- ❌ Use similarity/pattern matching for references

## Implementation
- **Backend**: `apps/api/server.py` - `/q11` endpoint
- **Data**: `data/compare_v1/q11_references_v1.jsonl`
- **Frontend**: (TODO) Q11 component reference section

## Validation
✅ references field always present (empty array if no data)
✅ references don't affect items ranking
✅ Badge "REFERENCE_ONLY_NOT_IN_PROPOSAL" present on all references
✅ UI displays warning label for references section

---
Created: 2026-01-13
Status: ACTIVE
