# Q1 BY_COVERAGE Mode - Smoke Test

**Purpose**: Manual testing guide for Q1 BY_COVERAGE mode (coverage-specific premium ranking)

**Scope**: STEP 2.2 - BY_COVERAGE endpoint + frontend integration (simplified coverage_code input)

**Date**: 2026-01-17

---

## Prerequisites

- ✅ Frontend dev server running on http://localhost:3000
- ✅ Backend API server running on http://localhost:8000
- ✅ SSOT database accessible at localhost:5433
- ✅ Gate checks passing: `tools/gate/check_q1_chat_no_legacy_mix.sh` (10/10)

---

## Test Cases

### TC1: BY_COVERAGE Flow - Direct Coverage Code Input

**Steps**:
1. Navigate to http://localhost:3000/q1
2. Type "40대 남성" in chat
3. Click "전송"
4. System responds: "비교 기준을 선택해주세요: (1) 전체보험료 (2) 담보별 보험료"
5. Type "담보별" in chat
6. Click "전송"
7. System responds: "담보 코드를 입력해 주세요.\n예시: A4200_1 (암진단비), A4103 (뇌졸중진단비)"
8. Type "A4200_1" in chat
9. Click "전송"

**Expected**:
- ✅ API call to /api/q1/coverage_ranking with coverage_codes=["A4200_1"]
- ✅ Assistant message: "담보별 비교 결과를 생성했습니다.\n기준: 암진단비(유사암제외)\n아래 표를 확인하세요."
- ✅ Q1PremiumTable renders with 3-4 rows
- ✅ Each row has insurer_name + product_name (both non-null)
- ✅ 무해지 columns show premium_monthly + premium_total
- ✅ 일반 columns show "—" (because GENERAL data doesn't exist in SSOT for A4200_1)

---

### TC2: plan_variant_scope=all - GENERAL Null Handling

**Steps**:
1. Complete TC1
2. Check "현재 설정" panel
3. Verify productType = "전체비교" (all)
4. Inspect browser console for result data

**Expected**:
- ✅ viewModel.mode = "BY_COVERAGE"
- ✅ viewModel.coverage_codes = ["A4200_1"]
- ✅ viewModel.coverage_labels[0].canonical_name = "암진단비(유사암제외)"
- ✅ viewModel.rows[*].premium_monthly has values (NO_REFUND data)
- ✅ viewModel.rows[*].premium_monthly_general = null (no GENERAL data in SSOT)
- ✅ Table displays "—" for 일반 columns (not "0" or empty)

---

### TC3: plan_variant_scope=no_refund - Hide GENERAL Columns

**Steps**:
1. Navigate to /q1
2. Click "고급 옵션" to expand
3. Change "보험 종류" to "무해지만"
4. Type "40대 남성 담보별 A4200_1" in chat
5. Click "전송"

**Expected**:
- ✅ Table renders with NO_REFUND columns ONLY
- ✅ GENERAL columns (일반) are hidden
- ✅ Rows sorted by premium_monthly (NO_REFUND)

---

### TC4: Insurer/Product Name Enforcement

**Steps**:
1. Complete TC1
2. Inspect each row in the table
3. Check backend logs for aggregation count

**Expected**:
- ✅ ALL rows have insurer_name populated (e.g., "메리츠", "삼성화재")
- ✅ ALL rows have product_name populated (full product name string)
- ✅ NO rows with null/missing names (backend excludes them)
- ✅ Backend logs: "aggregated X product-variant rows" → "returning top Y products"
- ✅ Y ≤ X (some rows excluded due to missing names)

---

### TC5: Invalid Coverage Code

**Steps**:
1. Navigate to /q1
2. Type "40대 남성 담보별 INVALID_CODE" in chat
3. Click "전송"

**Expected**:
- ✅ API returns error OR empty rows
- ✅ Error message displayed in red box
- ✅ NO crash or blank screen

---

### TC6: Backend Curl Test (Direct)

**Steps**:
```bash
curl -s -X POST http://localhost:8000/q1/coverage_ranking \
  -H "Content-Type: application/json" \
  -d '{
    "ins_cds":["N01","N02","N03"],
    "age":40,
    "gender":"M",
    "sort_by":"monthly",
    "plan_variant_scope":"all",
    "coverage_codes":["A4200_1"],
    "as_of_date":"2025-11-26"
  }' | jq '{
    kind,
    mode:.viewModel.mode,
    rows_count:(.viewModel.rows|length),
    first_row:.viewModel.rows[0]|{insurer_name,product_name,premium_monthly,premium_monthly_general}
  }'
```

**Expected Output**:
```json
{
  "kind": "Q1",
  "mode": "BY_COVERAGE",
  "rows_count": 3,
  "first_row": {
    "insurer_name": "메리츠",
    "product_name": "(무)알파Plus보장보험2508_해약환급금미지급형(납입후50%)_보험료납입면제형",
    "premium_monthly": 40020,
    "premium_monthly_general": null
  }
}
```

- ✅ insurer_name and product_name are strings (not null)
- ✅ premium_monthly has value
- ✅ premium_monthly_general is null (expected for A4200_1)

---

## Known Limitations (STEP 2.2 Simplified)

- ❌ NO coverage name resolution (user must input coverage_code directly)
- ❌ NO candidate selection UI (deferred to STEP 2.2-β)
- ❌ NO fuzzy matching or alias lookup
- ❌ NO evidence rail (scheduled for later step)
- ⚠️ GENERAL data often null in SSOT (expected behavior, not a bug)

---

## Success Criteria

✅ All 6 test cases pass
✅ Gate script passes (10/10 checks)
✅ NO legacy UI imports
✅ NO preset buttons
✅ insurer_name + product_name ALWAYS populated in table
✅ Table handles null general premiums gracefully ("—")
✅ BY_COVERAGE mode works end-to-end

---

## Next Steps (STEP 2.2-β)

After STEP 2.2 completion:
- Add coverage candidate resolver UI
- Implement fuzzy coverage name matching
- Add numbered candidate selection
- Add evidence rail
- Add meta.general_missing indicator
