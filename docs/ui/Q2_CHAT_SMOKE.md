# Q2 Chat Mode Smoke Tests

## Purpose
Manual smoke tests to verify Q2 chat-driven coverage limit comparison works correctly.

---

## Test Environment
- Browser: Chrome/Safari/Firefox
- Page: `/q2`
- Backend: `http://localhost:8000` (SSOT DB required)
- Frontend: `http://localhost:3000`

---

## TC1: Complete Input (1 Candidate → Auto-execute)

### Steps
1. Navigate to `/q2`
2. In chat: "암직접입원비 40대 남자"
3. Wait for response

### Expected Results
- ✅ Parser extracts:
  - coverage_query: "암직접입원비"
  - age_band: 40
  - sex: 'M'
- ✅ Backend returns 1 candidate
- ✅ Auto-executes Q2 compare
- ✅ Result table displays on right panel
- ✅ NO forbidden terms in result table (근거/출처/%)

---

## TC2: Candidate Selection (2~3 Candidates)

### Steps
1. Navigate to `/q2`
2. In chat: "암진단비 40대 남자"
3. Bot asks: "다음 중 어떤 담보를 비교할까요? (1) 암진단비 (2) 유사암진단비"
4. In chat: "1"

### Expected Results
- ✅ Bot presents numbered choice (1~3)
- ✅ User selects number
- ✅ Executes Q2 compare with selected coverage
- ✅ Result table displays correctly

---

## TC3: Zero Candidates → Re-prompt

### Steps
1. Navigate to `/q2`
2. In chat: "알수없는담보 40대 남자"
3. Wait for response

### Expected Results
- ✅ Bot responds: "해당 담보를 찾지 못했습니다. 다른 표현으로 다시 입력해 주세요."
- ✅ State resets to 'idle'
- ✅ User can retry with different input

---

## TC4: Missing Age → Clarification

### Steps
1. Navigate to `/q2`
2. In chat: "암진단비 남자"
3. Wait for response

### Expected Results
- ✅ Bot responds: "연령대와 성별을 알려주세요. 예) 40대 남성, 30대 여성"
- ✅ State remains 'collecting_slots'
- ✅ Waits for age input

---

## TC5: Missing Gender → Clarification

### Steps
1. Navigate to `/q2`
2. In chat: "암진단비 40대"
3. Wait for response

### Expected Results
- ✅ Bot responds: "연령대와 성별을 알려주세요. 예) 40대 남성, 30대 여성"
- ✅ State remains 'collecting_slots'
- ✅ Waits for gender input

---

## TC6: Plan Variant Scope (무해지로)

### Steps
1. Navigate to `/q2`
2. In chat: "암진단비 40대 남자 무해지로"
3. Wait for response

### Expected Results
- ✅ Parser extracts plan_variant_scope: 'no_refund'
- ✅ API called with plan_variant_scope='no_refund'
- ✅ Result shows only 무해지 products (if available)
- ✅ If no 무해지 data: "—" displayed

---

## TC7: Plan Variant Scope (일반으로)

### Steps
1. Navigate to `/q2`
2. In chat: "뇌졸중진단비 50대 여자 일반으로"
3. Wait for response

### Expected Results
- ✅ Parser extracts plan_variant_scope: 'standard'
- ✅ API called with plan_variant_scope='standard'
- ✅ Result shows only 일반 products (if available)

---

## TC8: Result Table Forbidden Terms Validation

### Steps
1. Complete any Q2 query (TC1)
2. Inspect result table carefully

### Expected Results
- ✅ Table shows ONLY: 순위, 보험사, 상품명, 보장한도, 일일보장금액
- ✅ NO forbidden terms: 근거|출처|사유|기준|산출|공식|배수|multiplier|formula|%
- ✅ Missing values displayed as "—"

---

## TC9: Evidence Rail Click → Evidence Display

### Steps
1. Complete any Q2 query (TC1)
2. Click on any row in result table
3. Evidence Rail opens on right

### Expected Results
- ✅ Evidence Rail opens (fixed right, 384px width)
- ✅ Displays:
  - 확인된 값 (duration_limit_days, daily_benefit_amount_won)
  - 출처/기준일
  - 산출 원칙
- ✅ Close button works
- ✅ Row highlight (blue ring + bg-blue-50)

---

## TC10: Gates Pass (Automated)

### Steps
1. Run: `bash tools/gate/check_q2_chat_mode.sh`
2. Verify output

### Expected Results
- ✅ All 8 checks pass:
  - Q2ChatPanel exists
  - slotParser exists + NO LLM imports
  - /api/q2/coverage_candidates route exists
  - /api/q2/compare route exists
  - q2/page.tsx renders Q2ChatPanel
  - Q2 result components have NO forbidden terms
  - NO preset buttons
  - NO legacy UI imports
- ✅ Exit code 0

---

## Regression Checks

### NO Preset Buttons
- [ ] Q2 page has NO "2개/4개/8개" preset UI
- [ ] Insurers fixed to 8 (N01-N13) internally

### Result/Evidence Separation
- [ ] Result table: ONLY numeric values, NO explanations
- [ ] Evidence Rail: ONLY explanations/sources, NO in-table mixing

### Chat State Machine
- [ ] idle → collecting_slots (when slots incomplete)
- [ ] collecting_slots → selecting_candidate (when 2~3 candidates)
- [ ] selecting_candidate → executing (when choice made)
- [ ] executing → completed (when result received)

### Deterministic Parsing
- [ ] NO LLM imports in slotParser
- [ ] Regex-based extraction only
- [ ] Korean text normalization works

---

## Pass Criteria
- ✅ All TCs (TC1-TC10) pass
- ✅ All regression checks pass
- ✅ Gate script passes (8/8 checks)
- ✅ NO console errors in browser DevTools
- ✅ Evidence Rail works independently

---

## Run Date
To be filled after execution: `YYYY-MM-DD HH:MM`

## Notes
- Backend `/compare` endpoint must exist for Q2 to work
- If backend not ready: Proxy route returns 500 → Expected behavior
- Mock data can be used for frontend-only testing
- Evidence Rail display is independent of chat logic
