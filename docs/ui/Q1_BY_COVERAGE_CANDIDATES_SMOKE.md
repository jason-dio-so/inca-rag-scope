# Q1 BY_COVERAGE Candidates - Smoke Test

**Purpose**: Manual testing guide for Q1 BY_COVERAGE candidate resolution (free text → canonical coverage_code)

**Scope**: STEP 2.2-β - Coverage candidate selection with deterministic matching

**Date**: 2026-01-17

---

## Prerequisites

- ✅ Frontend dev server running on http://localhost:3000
- ✅ Backend API server running on http://localhost:8000
- ✅ SSOT database accessible at localhost:5433
- ✅ Gate checks passing: `tools/gate/check_q1_chat_no_legacy_mix.sh` (12/12)

---

## Test Cases

### TC1: Free Text → Single Candidate (Auto-Select)

**Steps**:
1. Navigate to http://localhost:3000/q1
2. Type "40대 남성" in chat
3. Click "전송"
4. System responds: "비교 기준을 선택해주세요: (1) 전체보험료 (2) 담보별 보험료"
5. Type "담보별" in chat
6. Click "전송"
7. System responds: "어떤 담보 기준으로 볼까요?\n예) 암진단비, 뇌졸중진단비\n또는 담보코드 직접 입력 (예: A4200_1)"
8. Type "뇌졸중진단비" in chat (should match exactly one coverage)
9. Click "전송"

**Expected**:
- ✅ System automatically selects the single matching candidate
- ✅ System shows confirmation: `"[coverage name]" ([code])로 비교합니다.`
- ✅ Premium comparison table renders immediately
- ✅ NO candidate selection UI shown

---

### TC2: Free Text → Multiple Candidates (Selection UI)

**Steps**:
1. Navigate to http://localhost:3000/q1
2. Complete age/gender/mode setup (follow TC1 steps 2-7)
3. Type "암진단비" in chat
4. Click "전송"

**Expected**:
- ✅ System shows 2-3 candidates with numbered options:
  ```
  다음 중 선택해 주세요:
  1) 암진단비(유사암제외) (A4200_1)
  2) 고액암진단비 (A4209)
  3) 유사암진단비 (A4210)

  번호를 입력하세요 (1, 2, 3)
  ```
- ✅ pendingCandidates state populated
- ✅ Waiting for user input

**Continue**:
1. Type "2" in chat
2. Click "전송"

**Expected**:
- ✅ System confirms selection: `"고액암진단비" (A4209)로 비교합니다.`
- ✅ Premium comparison table renders with A4209 data
- ✅ pendingCandidates state cleared

---

### TC3: Invalid Candidate Selection

**Steps**:
1. Follow TC2 steps to get candidate selection UI
2. Type "5" in chat (invalid choice)
3. Click "전송"

**Expected**:
- ✅ System responds: `유효한 번호를 입력해 주세요 (1~3)`
- ✅ Candidate selection UI remains active
- ✅ User can retry with valid number

---

### TC4: Zero Candidates (No Match)

**Steps**:
1. Navigate to http://localhost:3000/q1
2. Complete age/gender/mode setup
3. Type "asdfqwerzxcv" in chat (nonsense text)
4. Click "전송"

**Expected**:
- ✅ System responds: `"asdfqwerzxcv"에 해당하는 담보를 찾지 못했습니다.\n다른 담보명을 입력하거나 담보코드를 직접 입력해 주세요.\n예) 암진단비, A4200_1`
- ✅ NO crash or blank screen
- ✅ User can retry with different text

---

### TC5: Direct Coverage Code (Bypass Candidate Resolution)

**Steps**:
1. Navigate to http://localhost:3000/q1
2. Complete age/gender/mode setup
3. Type "A4200_1" in chat (direct coverage code)
4. Click "전송"

**Expected**:
- ✅ System bypasses candidate resolution (recognizes `^A\d+` pattern)
- ✅ Calls ranking endpoint directly with A4200_1
- ✅ Premium comparison table renders immediately
- ✅ NO candidate selection flow triggered

---

### TC6: Backend Direct Test (Candidates Endpoint)

**Steps**:
```bash
curl -s -X POST http://localhost:8000/q1/coverage_candidates \
  -H "Content-Type: application/json" \
  -d '{"query_text":"암진단비","max_candidates":3}' | jq '.'
```

**Expected Output**:
```json
{
  "query_text": "암진단비",
  "candidates": [
    {
      "coverage_code": "A4200_1",
      "canonical_name": "암진단비(유사암제외)",
      "score": 80.0,
      "match_reason": "contains_canonical"
    },
    {
      "coverage_code": "A4209",
      "canonical_name": "고액암진단비",
      "score": 80.0,
      "match_reason": "contains_canonical"
    },
    {
      "coverage_code": "A4210",
      "canonical_name": "유사암진단비",
      "score": 80.0,
      "match_reason": "contains_canonical"
    }
  ]
}
```

- ✅ Returns 1-3 candidates sorted by score desc
- ✅ All fields populated (coverage_code, canonical_name, score, match_reason)
- ✅ No crashes or 500 errors

---

### TC7: Candidate Selection → Ranking Integration

**Steps**:
1. Follow TC2 to get candidate selection UI
2. Select option 1
3. Verify ranking result

**Expected**:
- ✅ executeCoverageRanking called with selected coverage_code
- ✅ Table shows insurer_name + product_name for all rows
- ✅ Coverage label in success message matches canonical_name
- ✅ Slot state updated correctly

---

## Known Limitations (STEP 2.2-β)

- ⚠️ Deterministic matching only (NO fuzzy match, NO typo correction)
- ⚠️ Max 3 candidates returned
- ⚠️ No candidate re-ranking after selection
- ⚠️ Coverage codes must exist in coverage_canonical table

---

## Success Criteria

✅ All 7 test cases pass
✅ Gate script passes (12/12 checks)
✅ NO legacy UI imports
✅ NO LLM usage
✅ Deterministic candidate resolution works end-to-end
✅ Direct coverage_code input still works (bypass path)
✅ Single candidate auto-selects
✅ Multiple candidates show numbered UI
✅ Invalid selections handled gracefully

---

## Next Steps (Future Enhancements)

After STEP 2.2-β validation:
- Add fuzzy matching for typo tolerance
- Add alias/synonym expansion
- Add coverage description hover tooltips
- Add candidate re-ranking based on user history
- Add evidence rail for coverage details
