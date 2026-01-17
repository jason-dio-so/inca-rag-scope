# Q1 Chat TOTAL Mode - Smoke Test

**Purpose**: Manual testing guide for Q1 chat interface with TOTAL mode (premium ranking)

**Scope**: STEP 2.1 - Chat panel + deterministic slot parsing + TOTAL mode execution

**Date**: 2026-01-17

---

## Prerequisites

- ✅ Frontend dev server running on http://localhost:3000
- ✅ Backend API server running on http://localhost:8000
- ✅ SSOT database accessible at localhost:5433
- ✅ Gate checks passing: `tools/gate/check_q1_chat_no_legacy_mix.sh`

---

## Test Cases

### TC1: Initial Page Load

**Steps**:
1. Navigate to http://localhost:3000/
2. Click "Q1 보험료 비교" card
3. Verify Q1 page loads

**Expected**:
- ✅ Chat panel visible on left (empty message list with example prompts)
- ✅ "고급 옵션" collapsed on right
- ✅ "현재 설정" panel shows all slots as "미설정"
- ✅ "메인으로" link at top
- ✅ NO legacy UI elements (no SidebarCategories, no old ChatPanel)
- ✅ NO preset buttons (2개/4개/8개)

---

### TC2: Slot Parsing - Sex Only

**Steps**:
1. Type "남성" in chat input
2. Click "전송"

**Expected**:
- ✅ User message appears (blue, right-aligned)
- ✅ Assistant clarification appears: "연령대와 성별을 알려주세요. 예) 40대 남성, 30대 여성"
- ✅ "현재 설정" shows: 성별=남성, 연령대=미설정, 비교 모드=미설정
- ✅ NO API call made (slot incomplete)

---

### TC3: Slot Parsing - Age Only

**Steps**:
1. Type "40대" in chat input
2. Click "전송"

**Expected**:
- ✅ User message appears
- ✅ Assistant clarification: "연령대와 성별을 알려주세요..."
- ✅ "현재 설정" shows: 성별=남성, 연령대=40대, 비교 모드=미설정
- ✅ NO API call made (still missing premium_mode)

---

### TC4: Slot Parsing - Premium Mode Needed

**Steps**:
1. After TC3, type "전체보험료로" in chat input
2. Click "전송"

**Expected**:
- ✅ User message appears
- ✅ API call executes (all required slots filled)
- ✅ Assistant message: "비교 결과를 생성했습니다. 아래 표를 확인하세요."
- ✅ Q1PremiumTable renders below with 4 rows
- ✅ Table shows: 순위, 보험사, 상품명, 무해지 총납/월납, 일반 총납/월납
- ✅ "현재 설정" shows: 성별=남성, 연령대=40대, 비교 모드=TOTAL

---

### TC5: One-Shot Complete Query

**Steps**:
1. Refresh page
2. Type "40대 남성 전체보험료" in chat input
3. Click "전송"

**Expected**:
- ✅ User message appears
- ✅ API call executes immediately (all slots parsed from one message)
- ✅ Assistant message: "비교 결과를 생성했습니다..."
- ✅ Q1PremiumTable renders with correct data
- ✅ "현재 설정" all filled

---

### TC6: Age Mapping (Actual Age → Band)

**Steps**:
1. Refresh page
2. Type "35세 여성 총보험료" in chat input
3. Click "전송"

**Expected**:
- ✅ Age 35 mapped to band 40 (35-44 → 40)
- ✅ "현재 설정" shows: 성별=여성, 연령대=40대
- ✅ API called with age=40, gender=F
- ✅ Table renders with correct data

---

### TC7: Korean Variations

**Steps**:
1. Refresh page
2. Type "50대 여자 전체" in chat input (여자 instead of 여성)
3. Click "전송"

**Expected**:
- ✅ Parser recognizes "여자" as F
- ✅ Parser recognizes "전체" as TOTAL mode
- ✅ API executes correctly

---

### TC8: Sort By + Plan Variant

**Steps**:
1. Refresh page
2. Type "30대 남성 월납 일반만" in chat input
3. Click "전송"

**Expected**:
- ✅ Slots parsed: age_band=30, sex=M, sort_by=monthly, plan_variant_scope=standard, premium_mode=TOTAL (inferred)
- ✅ "현재 설정" shows: 정렬=월납, 보험 종류=일반만
- ✅ API called with filters.sort_by=monthly, filters.product_type=standard
- ✅ Table shows only "일반" columns (no "무해지" columns)

---

### TC9: BY_COVERAGE Mode (Blocked)

**Steps**:
1. Refresh page
2. Type "40대 남성 암진단비 담보별" in chat input
3. Click "전송"

**Expected**:
- ✅ User message appears
- ✅ System message (yellow box): "⚠️ 담보별 비교는 아직 지원되지 않습니다. 전체보험료 비교를 사용하세요."
- ✅ NO API call made
- ✅ "현재 설정" shows: 비교 모드=BY_COVERAGE

---

### TC10: Form Controls (Advanced Options)

**Steps**:
1. Click "고급 옵션" to expand
2. Change 성별 to "여성"
3. Change 연령대 to "50대"
4. Click "비교 생성"

**Expected**:
- ✅ Form controls expand/collapse correctly
- ✅ API executes with form values (sex=F, age=50)
- ✅ Table renders
- ✅ NO chat message added (form bypass)

---

### TC11: Slot → Form Sync

**Steps**:
1. Refresh page
2. Type "30대 여성" in chat
3. Click "전송"
4. Expand "고급 옵션"

**Expected**:
- ✅ Form controls show: 연령대=30대 (blue selected), 성별=여성 (blue selected)
- ✅ Slots synced to form state correctly

---

### TC12: Multiple Queries

**Steps**:
1. Complete TC5 (40대 남성 전체보험료)
2. Type "50대는?" in chat
3. Click "전송"

**Expected**:
- ✅ Parser updates age_band to 50 (preserves sex=M, premium_mode=TOTAL)
- ✅ New API call with age=50
- ✅ Table updates with new data
- ✅ Previous result replaced (not appended)

---

### TC13: Error Handling

**Steps**:
1. Stop backend API server
2. Type "40대 남성 전체보험료" in chat
3. Click "전송"

**Expected**:
- ✅ Error message appears in red box above table: "요청 처리 중 오류가 발생했습니다."
- ✅ Chat shows user message but no assistant response
- ✅ Loading state ends

---

## Gate Verification

Run gate after all manual tests:

```bash
tools/gate/check_q1_chat_no_legacy_mix.sh
```

**Expected**:
```
✅ Q1 CHAT GATE: ALL CHECKS PASSED
```

---

## Known Limitations (STEP 2.1)

- ❌ BY_COVERAGE mode not implemented (blocked with system message)
- ❌ No coverage_code resolution
- ❌ No evidence rail (scheduled for later step)
- ❌ No multi-insurer selection (uses all 8 by default)
- ❌ No percentage/formula display in table (numbers only)

---

## Success Criteria

✅ All 13 test cases pass
✅ Gate script passes
✅ NO legacy UI imports
✅ NO LLM calls (deterministic regex only)
✅ NO preset buttons
✅ Chat clarification flow works correctly
✅ Slot parsing handles Korean variations
✅ Form controls sync with slots
✅ Table renders with correct show/hide logic

---

## Next Steps

After STEP 2.1 completion:
- STEP 2.2: Implement BY_COVERAGE mode
- Add coverage_resolver utility
- Create /api/q1/coverage_ranking endpoint
- Add evidence rail
