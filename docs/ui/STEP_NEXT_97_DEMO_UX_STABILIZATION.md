# STEP NEXT-97 — Customer Demo UX Stabilization

**Status**: ✅ COMPLETE
**Date**: 2026-01-03
**Scope**: View Layer ONLY (NO business logic change)

---

## Purpose

고객이 처음 사용해도 **질문 → 응답 → 이해의 흐름이 끊기지 않게** 만들기

**Definition of Success**:
> "고객이 설명 없이 1분 안에 써보고 '아, 이렇게 쓰는 거구나' 라고 말하면 성공"

---

## Problems Solved

### 1. 좌측 카테고리 vs 질문 UX 혼재

**As-Is**: 좌측 "지식 탐색 카테고리"와 중앙 "질문 실행"이 혼재되어 고객 혼란
**To-Be**:
- 좌측 카테고리 기본 접힘 (12px 폭)
- 확장 토글 버튼 제공
- 질문 중심 UX로 명확화

**Implementation**:
- `apps/web/components/SidebarCategories.tsx`
  - `useState(false)` — 기본 접힘
  - 토글 버튼 (chevron icon)
  - 확장 시에만 카테고리 목록 표시

---

### 2. 보험사 선택 영역 중복/재등장

**As-Is**: 질문 실행 중에도 보험사 selector 노출, 조건 유지 불명확
**To-Be**:
- Conversation Context Lock
- 첫 메시지 후 보험사 selector 비활성화
- "현재 대화 조건" 표시
- "조건 변경" 버튼 → 명시적 초기화

**Implementation**:
- `apps/web/components/ChatPanel.tsx`
  - `conversationActive = messages.length > 0`
  - Selector disabled when `conversationActive === true`
  - Context indicator banner: "현재 대화 조건: 삼성화재 · 메리츠화재"
  - "조건 변경" 버튼 → confirm + page reload

---

### 3. 말풍선 자동 스크롤 문제

**As-Is**: 새 응답이 와도 자동 스크롤 없음, 고객이 직접 스크롤해야 확인
**To-Be**:
- 새 bubble render 시 자동 스크롤 (smart)
- 사용자가 아래를 보고 있으면 → 자동 이동 ✅
- 사용자가 위로 스크롤해 과거 내용 보는 중 → 자동 이동 ❌

**Implementation**:
- `apps/web/components/ChatPanel.tsx`
  - `messagesContainerRef` — scroll container
  - `messagesEndRef` — scroll anchor
  - `useEffect` on `messages` change
  - `isNearBottom` threshold (100px)
  - Conditional `scrollIntoView({ behavior: "smooth" })`

---

## Implementation Details

### Files Modified

1. **apps/web/components/ChatPanel.tsx**
   - Added `useRef` for scroll management
   - Added `conversationActive` state (derived from `messages.length > 0`)
   - Auto-scroll logic in `useEffect([messages])`
   - Context lock indicator UI
   - Disabled insurer selector when conversation active
   - Fixed deprecated `onKeyPress` → `onKeyDown`

2. **apps/web/components/SidebarCategories.tsx**
   - Added collapsible sidebar (`isExpanded` state)
   - Default collapsed (12px width)
   - Toggle button with chevron icons
   - Smooth width transition

3. **apps/web/lib/normalize/table.ts**
   - Added `kpi_condition` to `NormalizedTable` meta type
   - Fixed TypeScript error in TwoInsurerCompareCard.tsx

---

## UX Principles (Constitution)

1. **Customer-First Flow**
   고객의 시선은 항상 "다음에 읽을 말풍선"에 머문다

2. **Context is Sacred**
   선택한 보험사/담보는 대화 중 흔들리지 않는다

3. **No Surprise**
   화면 요소가 이유 없이 다시 나타나거나 사라지지 않는다

4. **View-Only Change**
   결과 의미/내용은 단 1글자도 변하지 않는다

---

## Verification Scenarios

### ✅ Scenario A — 첫 방문 고객
1. 페이지 진입
2. 질문 입력
3. 자동으로 응답 말풍선 표시
4. 스크롤 조작 없이 결과 인지 가능

### ✅ Scenario B — 대화 중 조건 변경
1. 삼성/메리츠 선택 후 질문
2. 보험사 selector 비활성화 확인
3. "조건 변경" 클릭 → selector 활성화

### ✅ Scenario C — 긴 대화
1. 여러 말풍선 누적
2. 새 응답 시 자동 스크롤
3. 과거 스크롤 중에는 강제 이동 없음

---

## Definition of Done (DoD)

- [x] 좌측 카테고리와 질문 UX 충돌 제거
- [x] 보험사 선택 영역 재등장 없음
- [x] 대화 중 조건 고정 시각적으로 명확
- [x] 새 말풍선 자동 스크롤 동작
- [x] 사용자 스크롤 방해 없음
- [x] API / 데이터 / 로직 변경 0건
- [x] TypeScript build PASS
- [x] 기존 EX2/EX3/EX4 테스트 전부 PASS

---

## Out of Scope (Forbidden)

❌ DB 설계 / 마이그레이션
❌ 보험사 데이터 추가
❌ 비즈니스 로직 변경
❌ 판단/추천/점수 로직
❌ LLM 사용
❌ API 응답 구조 변경

---

## Impact

**Before**:
- 고객이 카테고리/질문 UX 혼란
- 보험사 조건이 대화 중 변경될 수 있다는 불안
- 새 응답을 못 보고 지나침

**After**:
- 질문 중심 UX 명확
- 대화 조건 명시적 고정 (조건 변경은 명시적 액션)
- 새 응답 자동 표시 (smart scroll)

---

## Compatibility

- ✅ NO breaking changes
- ✅ NO API changes
- ✅ NO database changes
- ✅ NO business logic changes
- ✅ 100% backward compatible

---

## Related Documents

- STEP NEXT-86: EX2_DETAIL Lock
- STEP NEXT-94/95: Coverage Grouping UX
- STEP NEXT-77: EX3_COMPARE Response Schema Lock

---

**Result**: "고객이 이미 똑똑한 것을 이해하게 만들기" ✅
