# Q2-Q4 Evidence Rail Smoke Tests

## Purpose
Manual smoke tests to verify Q2-Q4 Evidence Rail integration works correctly.

---

## Test Environment
- Browser: Chrome/Safari/Firefox
- Pages: `/q2`, `/q3`, `/q4`
- Mock data used for demonstration

---

## TC1: Q2 Row Click → Evidence Rail

### Steps
1. Navigate to `/q2`
2. View the coverage limit comparison table
3. Click on any row (e.g., 메리츠화재)
4. Verify Evidence Rail appears on the right (384px width)
5. Verify selected row has blue ring highlight (`ring-2 ring-blue-500`)
6. Verify selected row has blue background (`bg-blue-50`)
7. Click the "×" button on Evidence Rail
8. Verify Evidence Rail closes
9. Verify row highlight is removed

### Expected Results
- ✅ Evidence Rail opens on row click
- ✅ Visual selection feedback (blue ring + background)
- ✅ NO text indicators ("선택됨" forbidden)
- ✅ Evidence Rail displays:
  - 확인된 값 (duration_limit_days, daily_benefit_amount_won)
  - 출처/기준일
  - 산출 원칙
- ✅ Rail closes on "×" click

---

## TC2: Q3 Row Click → Evidence Rail

### Steps
1. Navigate to `/q3`
2. View the comprehensive comparison table
3. Click on any row (e.g., 메리츠화재)
4. Verify Evidence Rail appears on the right
5. Verify selected row has blue ring + background
6. Click the "×" button
7. Verify Evidence Rail closes

### Expected Results
- ✅ Evidence Rail opens on row click
- ✅ Visual selection feedback (identical to Q2)
- ✅ Evidence Rail displays:
  - 슬롯 상세 (all slots with values)
  - 요약/추천의 입력 근거
  - 출처 (SSOT DB references)
- ✅ Rail closes correctly

---

## TC3: Q4 Cell Click → Evidence Rail

### Steps
1. Navigate to `/q4`
2. View the support matrix (제자리암/경계성종양)
3. Click on "제자리암" cell for 메리츠화재
4. Verify Evidence Rail appears on the right
5. Verify selected cell has blue ring + background
6. Click on "경계성종양" cell for 메리츠화재
7. Verify Evidence Rail updates with new cell data
8. Verify previous cell highlight is removed
9. Click "×" button
10. Verify Evidence Rail closes

### Expected Results
- ✅ Evidence Rail opens on cell click
- ✅ Cell-level selection (not row-level)
- ✅ Visual feedback per cell
- ✅ Evidence Rail displays:
  - 판정 (O/X/—/⚠️ with interpretation)
  - 근거 (evidence_refs or "약관에서 확인되지 않음")
  - 주의사항 (treatment trigger warnings)
- ✅ Rail updates when clicking different cells
- ✅ Rail closes correctly

---

## TC4: Result Area Terminology Validation (Gate-Based)

### Steps
1. Run: `bash tools/gate/check_q234_result_no_evidence.sh`
2. Verify all 7 checks pass:
   - Q2LimitDiffView: NO forbidden terms
   - Q3ThreePartView: NO forbidden terms
   - Q4SupportMatrixView: NO forbidden terms
   - Q2/Q3/Q4 pages: NO forbidden terms in result areas
   - NO percentage symbols
   - Evidence Rails exist
   - Approved neutral terminology

### Expected Results
- ✅ All 7 checks pass
- ✅ NO forbidden terms in result components:
  - `근거|출처|사유|기준|산출|공식|배수|multiplier|formula`
- ✅ Exit code 0

---

## TC5: Evidence Rail Existence Validation (Gate-Based)

### Steps
1. Run: `bash tools/gate/check_q234_evidence_rail_exists.sh`
2. Verify all 7 checks pass:
   - EvidenceRailBase exists
   - Q2/Q3/Q4 EvidenceRail components exist
   - Q2Row interface exported
   - Q2LimitDiffView has onRowClick
   - All Rails use EvidenceRailBase

### Expected Results
- ✅ All 7 checks pass
- ✅ Infrastructure complete
- ✅ Exit code 0

---

## Regression Checks

### Visual Consistency
- [ ] All Evidence Rails have identical width (384px)
- [ ] All selection highlights use same colors (blue-500 ring, blue-50 bg)
- [ ] NO text indicators anywhere ("선택됨" forbidden)
- [ ] Close buttons work identically across all rails

### Architecture Compliance
- [ ] Result components contain ONLY numbers/conclusions
- [ ] Evidence Rails contain ONLY explanations/sources
- [ ] NO forbidden terminology in result components
- [ ] Consistent interaction pattern across Q1-Q4

---

## Pass Criteria
- ✅ All manual TCs (TC1-TC3) pass
- ✅ All gate TCs (TC4-TC5) pass with 7/7 checks each
- ✅ All regression checks pass
- ✅ NO console errors in browser DevTools
- ✅ Responsive behavior acceptable

---

## Run Date
To be filled after execution: `YYYY-MM-DD HH:MM`

## Notes
- Mock data used for demonstration purposes
- Real backend integration pending
- Evidence refs display as strings (real PDF viewer integration pending)
