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

## TC11: Demographics Together - Complete Input

### Steps
1. Navigate to `/q2`
2. First message should ask for age+sex together
3. In chat: "40대 남성"
4. Wait for response

### Expected Results
- ✅ Bot responds: "비교할 담보를 입력해 주세요.\n예) 암진단비, 암직접입원비, 뇌졸중진단비"
- ✅ Demographics confirmed
- ✅ State transitions to 'collect_coverage_query'
- ✅ NO coverage_candidates API call yet

---

## TC12: Demographics Partial - Age Only

### Steps
1. Navigate to `/q2`
2. In chat: "40대"
3. Wait for response

### Expected Results
- ✅ Bot responds: "연령은 확인되었습니다. 성별을 함께 입력해주세요.\n예) 40대 남성"
- ✅ State remains 'collect_demographics'
- ✅ NO coverage_candidates API call yet
- ✅ NO state transition

---

## TC13: Demographics Partial - Sex Only

### Steps
1. Navigate to `/q2`
2. In chat: "남성"
3. Wait for response

### Expected Results
- ✅ Bot responds: "성별은 확인되었습니다. 연령대를 함께 입력해주세요.\n예) 40대 남성"
- ✅ State remains 'collect_demographics'
- ✅ NO coverage_candidates API call yet
- ✅ NO state transition

---

## TC14: Demographics + Coverage Together

### Steps
1. Navigate to `/q2`
2. In chat: "40대 남성 암진단비"
3. Wait for response

### Expected Results
- ✅ Demographics confirmed
- ✅ Coverage_candidates API called immediately
- ✅ If 1 candidate: Auto-executes Q2 compare
- ✅ If 2~3 candidates: Shows numbered list
- ✅ State flow: collect_demographics → executing → (selecting_candidate or completed)

---

## TC15: Pending Coverage Then Demographics

### Steps
1. Navigate to `/q2`
2. In chat: "암진단비"
3. Bot stores as pending
4. In chat: "40대 남성"
5. Wait for response

### Expected Results
- ✅ Coverage stored as pending (NO API call on step 2)
- ✅ After demographics confirmed: Auto-proceeds with pending coverage
- ✅ Coverage_candidates API called after demographics
- ✅ Result displays correctly

---

## TC16: Demographics Flow - Result Area NO Forbidden Terms

### Steps
1. Complete any demographics flow (TC11-TC15)
2. Inspect result table carefully

### Expected Results
- ✅ Table shows ONLY: 순위, 보험사, 상품명, 보장한도, 일일보장금액
- ✅ NO forbidden terms in result area: 근거|출처|사유|기준|산출|공식|배수|multiplier|formula|%
- ✅ Evidence Rail (when row clicked) CAN show forbidden terms
- ✅ Gate check_q234_result_no_evidence.sh passes

---

## TC17: Q2 Chat → Compare (422 Prevention)

### Steps
1. Navigate to `/q2`
2. In chat: "40대 남성"
3. Bot asks for coverage
4. In chat: "암진단비"
5. Bot presents candidate(s)
6. Select candidate (if multiple)
7. Wait for result

### Expected Results
- ✅ POST /api/q2/compare returns 200 OK (NOT 422)
- ✅ FastAPI /compare receives valid CompareRequest payload
- ✅ Console log shows: [Q2][compare] payload with correct structure
- ✅ Console log shows: insurers = ["MERITZ", "DB", ...] (NOT ["N01", "N02"])
- ✅ Result table renders correctly with comparison data
- ✅ Evidence Rail opens on row click
- ✅ NO 422 Unprocessable Entity error

### Debug Verification (Console)
```
[Q2][compare] payload = {
  "query": "coverage_code:...",
  "insurers": ["MERITZ", "DB", ...],
  "age": 40,
  "gender": "M",
  "coverage_codes": ["..."],
  "sort_by": "monthly",
  "plan_variant_scope": "all",
  "as_of_date": "2025-11-26"
}
[Q2][compare] insurers = ["MERITZ", "DB", ...]
[Q2][compare] status = 200
```

---

## TC18: Q2 Proxy - Direct curl Test (coverage_codes Array)

### Steps
1. Ensure backend is running (port 8000)
2. Ensure frontend is running (port 3000)
3. Run curl command:
```bash
curl -i -X POST http://localhost:3000/api/q2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query":"암진단비 보장한도 비교",
    "ins_cds":["N01","N02","N03","N05","N08","N09","N10","N13"],
    "age":40,
    "gender":"M",
    "coverage_codes":["A4200_1"],
    "sort_by":"monthly",
    "plan_variant_scope":"all",
    "as_of_date":"2025-11-26"
  }'
```

### Expected Results
- ✅ HTTP 200 OK
- ✅ Response contains comparison data
- ✅ Console log shows: `[Q2][compare] payload` with `intent: "Q2"` and `products: []`
- ✅ Console log shows: `coverage_codes: ["A4200_1"]` (NOT null)
- ✅ NO `coverage_code:undefined` in payload
- ✅ Backend receives valid CompareRequest

---

## TC19: Q2 Proxy - Single coverage_code Input (Backward Compatibility)

### Steps
1. Run curl command with single `coverage_code` field:
```bash
curl -i -X POST http://localhost:3000/api/q2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query":"암진단비 보장한도 비교",
    "ins_cds":["N01","N02"],
    "age":40,
    "gender":"M",
    "coverage_code":"A4200_1",
    "sort_by":"monthly",
    "plan_variant_scope":"all",
    "as_of_date":"2025-11-26"
  }'
```

### Expected Results
- ✅ HTTP 200 OK
- ✅ Proxy correctly transforms `coverage_code` → `coverage_codes: ["A4200_1"]`
- ✅ Backend receives valid CompareRequest
- ✅ Response contains comparison data

---

## TC20: Q2 Proxy - Missing coverage_code → 400

### Steps
1. Run curl command without coverage_code:
```bash
curl -i -X POST http://localhost:3000/api/q2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query":"암진단비 보장한도 비교",
    "ins_cds":["N01","N02"],
    "age":40,
    "gender":"M",
    "sort_by":"monthly",
    "plan_variant_scope":"all",
    "as_of_date":"2025-11-26"
  }'
```

### Expected Results
- ✅ HTTP 400 Bad Request (NOT 422)
- ✅ Response body: `{ "error": "Missing coverage_code", "detail": "coverage_codes[0] or coverage_code is required and must not be empty" }`
- ✅ Proxy blocks request BEFORE sending to backend
- ✅ NO backend 422 error

---

## TC21: Q2 Proxy - Empty coverage_codes Array → 400

### Steps
1. Run curl command with empty array:
```bash
curl -i -X POST http://localhost:3000/api/q2/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query":"암진단비 보장한도 비교",
    "ins_cds":["N01","N02"],
    "age":40,
    "gender":"M",
    "coverage_codes":[],
    "sort_by":"monthly",
    "plan_variant_scope":"all",
    "as_of_date":"2025-11-26"
  }'
```

### Expected Results
- ✅ HTTP 400 Bad Request
- ✅ Response body: `{ "error": "Missing coverage_code", ... }`
- ✅ Proxy validation catches empty array
- ✅ NO backend call made

---

## Regression Checks

### Demographics Together Enforcement
- [ ] First prompt always asks for age+sex together
- [ ] Partial input (age only or sex only) stays in collect_demographics
- [ ] NO API calls until demographics_confirmed = true
- [ ] Coverage mentioned early is stored as pending

### NO Preset Buttons
- [ ] Q2 page has NO "2개/4개/8개" preset UI
- [ ] Insurers fixed to 8 (N01-N13) internally

### Result/Evidence Separation
- [ ] Result table: ONLY numeric values, NO explanations
- [ ] Evidence Rail: ONLY explanations/sources, NO in-table mixing

### Chat State Machine
- [ ] collect_demographics → collect_coverage_query (when demographics confirmed, no pending coverage)
- [ ] collect_demographics → executing (when demographics confirmed, with pending/provided coverage)
- [ ] executing → selecting_candidate (when 2~3 candidates)
- [ ] selecting_candidate → executing (when choice made)
- [ ] executing → completed (when result received)

### Deterministic Parsing
- [ ] NO LLM imports in slotParser
- [ ] Regex-based extraction only
- [ ] Korean text normalization works

---

## Pass Criteria
- ✅ All TCs (TC1-TC21) pass
- ✅ All regression checks pass (including demographics together enforcement)
- ✅ Gate script passes (updated with demographics + intent/products checks)
- ✅ NO console errors in browser DevTools
- ✅ Evidence Rail works independently
- ✅ Demographics together enforced: age+sex → coverage → result
- ✅ Proxy curl tests pass: TC18-TC21 (intent/products included, coverage_codes array support, 400 validation)

---

## Run Date
To be filled after execution: `YYYY-MM-DD HH:MM`

## Notes
- Backend `/compare` endpoint must exist for Q2 to work
- If backend not ready: Proxy route returns 500 → Expected behavior
- Mock data can be used for frontend-only testing
- Evidence Rail display is independent of chat logic
