# Q1 Evidence Rail - Smoke Test

**Purpose**: Manual testing guide for Q1 Evidence Rail (rail-only, fixed copy, no main-table formulas)

**Scope**: STEP 3 - Evidence Rail with row click interaction

**Date**: 2026-01-17

---

## Prerequisites

- ✅ Frontend dev server running on http://localhost:3000
- ✅ Backend API server running on http://localhost:8000
- ✅ SSOT database accessible at localhost:5433
- ✅ Gate checks passing: `bash tools/gate/check_q1_evidence_rail.sh` (7/7)
- ✅ GENERAL variant data loaded (1,584 rows for as_of_date=2025-11-26)

---

## Test Cases

### TC1: BY_COVERAGE Execution → Table Display

**Steps**:
1. Navigate to http://localhost:3000/q1
2. Type "40대 남성" in chat
3. Click "전송"
4. System responds: "비교 기준을 선택해주세요: (1) 전체보험료 (2) 담보별 보험료"
5. Type "2" in chat
6. Click "전송"
7. System responds: "어떤 담보 기준으로 볼까요?\n예) 암진단비, 뇌졸중진단비"
8. Type "암진단비" in chat
9. Click "전송"
10. Select candidate (e.g., type "1")
11. Click "전송"

**Expected**:
- ✅ Premium comparison table displays with top 4 rows
- ✅ Table shows numeric columns only (NO formulas, NO %, NO explanations)
- ✅ Footer note: "※ 보험료는 DB 기준 (2025-11-26) / 행을 클릭하면 상세 근거를 확인할 수 있습니다"
- ✅ NO evidence rail visible yet (no row selected)

---

### TC2: Row Click → Rail Opens with Base Premium

**Steps**:
1. Continue from TC1
2. Click on any row in the table (e.g., rank 1)

**Expected**:
- ✅ Right-side evidence rail opens (fixed position, 384px width)
- ✅ Header shows:
  - Rank badge (e.g., "1")
  - Insurer name (e.g., "메리츠")
  - Product name (truncated if long)
  - Close button (X)
- ✅ Section "1. 기준 보험료" displays:
  - Label: "기준: 무해지형(NO_REFUND)" (term only in rail, not table)
  - 월납보험료: formatted number (e.g., "40,020원")
  - 총납입보험료: formatted number (e.g., "9,604,800원")
  - 출처: "SSOT DB (coverage_premium_quote)"
  - 기준일: "2025-11-26"
- ✅ Selected row in table has blue highlight (ring-2 ring-blue-500)

---

### TC3: GENERAL Data Null → Fixed Copy Displayed

**Steps**:
1. Continue from TC2
2. Check if the selected product has null GENERAL data
3. Observe "2. 일반형 보험료" section

**Expected** (if GENERAL is null):
- ✅ Section shows:
  - Title: "2. 일반형 보험료"
  - Status: "데이터 없음"
  - Fixed reason (yellow box):
    - "사유: 해당 기준일(as_of_date)에는 담보별 일반형(GENERAL) 보험료가 SSOT에 적재되지 않았습니다."
    - "안내: 일반형 산출식/배수/퍼센트 정보는 결과 테이블에 표시하지 않으며, 필요 시 별도 근거 레일에서만 제공합니다."
- ✅ NO formulas, NO "130%", NO "× 1.3" in rail

**Expected** (if GENERAL exists):
- ✅ Section shows:
  - Title: "2. 일반형 보험료"
  - Label: "기준: 일반형(GENERAL)"
  - 월납보험료: formatted number (e.g., "52,026원")
  - 총납입보험료: formatted number (e.g., "12,486,240원")
  - 출처: "SSOT DB (coverage_premium_quote)"
  - 기준일: "2025-11-26"

---

### TC4: Rail Close → Selection Cleared

**Steps**:
1. Continue from TC3
2. Click the close button (X) in the rail header

**Expected**:
- ✅ Evidence rail closes (disappears)
- ✅ Table row highlight removed
- ✅ Table remains displayed with no selection

---

### TC5: Forbidden Tokens Not Present (Gate Enforced)

**Steps**:
1. Run gate check:
   ```bash
   bash tools/gate/check_q1_evidence_rail.sh
   ```

**Expected**:
- ✅ CHECK 1 PASS: Q1PremiumTable has no forbidden tokens (%, ×, multiplier, 공식, 배수, 130)
- ✅ CHECK 2 PASS: Q1PremiumTable cells have no explanation keywords (근거, 출처, 사유, 기준일)
- ✅ CHECK 3 PASS: Q1EvidenceRail exists
- ✅ CHECK 4 PASS: Q1 page imports/uses Q1EvidenceRail
- ✅ CHECK 5 PASS: No suspicious math operations found
- ✅ CHECK 6 PASS: Evidence Rail has fixed copy for null GENERAL data
- ✅ CHECK 7 PASS: Table has row click handler
- ✅ Overall: ALL CHECKS PASSED (7/7)

---

### TC6: Multiple Row Selection

**Steps**:
1. Continue from TC4
2. Click row rank 1
3. Verify rail opens for rank 1
4. Click row rank 2
5. Verify rail updates to rank 2

**Expected**:
- ✅ Each row click updates the rail content
- ✅ Only one row highlighted at a time
- ✅ Rail content changes smoothly without errors

---

### TC7: Section 3 - 산출 원칙 (Fixed Bullets)

**Steps**:
1. Continue from TC6
2. Scroll down in the rail to section "3. 산출 원칙"

**Expected**:
- ✅ Section displays three fixed bullet points:
  - "모든 보험료 값은 SSOT DB 결과를 그대로 표시합니다."
  - "UI에서 계산/추정/보정하지 않습니다."
  - "공식/배수/퍼센트는 결과 테이블에 표시하지 않습니다(근거 레일 전용)."
- ✅ NO dynamic content in this section
- ✅ Text is consistent across all rows

---

## Known Limitations (STEP 3)

- ⚠️ Fixed copy for null GENERAL (no formula explanation yet)
- ⚠️ NO evidence for source/calculation details (SSOT only)
- ⚠️ NO evidence for coverage amount derivation
- ⚠️ NO evidence for insurer/product metadata

---

## Success Criteria

✅ All 7 test cases pass
✅ Gate script passes (7/7 checks)
✅ Main table remains numeric-only (NO formulas/explanations)
✅ Evidence rail displays all 3 sections correctly
✅ Row click interaction works smoothly
✅ Fixed copy for null GENERAL data displays correctly
✅ Close button works
✅ Only one row selected at a time

---

## Next Steps (Future Enhancements)

After STEP 3 validation:
- Add formula explanation for GENERAL calculation (e.g., "= NO_REFUND × 1.3")
- Add coverage amount evidence with calculation details
- Add insurer/product metadata in rail
- Add evidence for source table references
- Add historical comparison data
