# STEP NEXT-108 — ChatGPT UI 정합: Left Bubble 강화 + Bottom Dock 최소화

**Date**: 2026-01-03
**Scope**: Frontend View Layer ONLY
**Files Modified**: 3
**Packages Added**: 3

---

## 1. Purpose (Why)

### Problem Statement

고객 데모에서 UI가 ChatGPT와 다르게 "설문/폼"처럼 보이는 문제:

1. **Left Bubble (말풍선) 빈약**:
   - EX2_LIMIT_FIND / EX3_COMPARE 같은 결과에서
   - 왼쪽 말풍선이 "제목 + 1~2줄"로 끝남
   - 테이블/핵심 값이 안 보임
   - 고객이 "뭐가 다른데?"를 즉시 못 느낌

2. **Bottom Dock (하단 입력 영역) 과다**:
   - 컨텍스트 배너 + 보험사 버튼 + 담보 입력 + 질문 입력
   - 중앙 채팅 영역의 **절반**을 차지
   - ChatGPT UI 컨셉을 깨고 "설문"처럼 보임

---

## 2. Solution (What)

### 2.1 Left Bubble 강화 — Markdown Rich Rendering

**Before**:
```
왼쪽 말풍선: 제목만 표시 (plain text)
```

**After**:
```markdown
## 요약
- 결론: **A사가 다릅니다**

| 담보 | 삼성 | 메리츠 | 결론 |
|---|---:|---:|---|
| 암직접입원비 | 1~120일 | 1~180일 | 메리츠↑ |

근거: [삼성](PD:...) · [메리츠](PD:...)
```

**Implementation**:
- `react-markdown` + `remark-gfm` (table support)
- `@tailwindcss/typography` (prose styles)
- Assistant messages render as markdown
- User messages remain plain text

---

### 2.2 Bottom Dock 축소 — Collapsible Options Panel

**Before**:
```
[ 현재 대화 조건: 삼성화재 · 메리츠화재 ]  [ 조건 변경 ]

보험사 선택 (복수 가능)
[삼성화재] [메리츠화재] [KB손보] [한화손보] ... (8개 버튼)

담보명 (선택사항, 쉼표로 구분)
[_________________________]

질문을 입력하세요...
[________________________________] [전송]
```
→ **화면 절반 차지** (ChatGPT와 다름)

**After**:
```
대화 중: 삼성화재 · 메리츠화재  [옵션 ▾]

질문을 입력하세요...
[________________________________] [전송]
```
→ **최소화 완료** (ChatGPT 스타일)

**Expanded** (옵션 ▴ 클릭 시):
```
대화 중: 삼성화재 · 메리츠화재  [옵션 ▴]

┌─────────────────────────────────────┐
│ 보험사 선택 (복수 가능)             │
│ [삼성화재] [메리츠화재] [KB손보] ... │
│                                     │
│ 담보명 (선택사항)                   │
│ [_____________________________]     │
│                                     │
│ [대화 초기화]                       │
└─────────────────────────────────────┘

질문을 입력하세요...
[________________________________] [전송]
```

---

## 3. Implementation Details

### 3.1 Packages Installed

```bash
npm install react-markdown remark-gfm @tailwindcss/typography
```

- `react-markdown`: Markdown → React components
- `remark-gfm`: GitHub Flavored Markdown (tables, strikethrough, etc.)
- `@tailwindcss/typography`: Prose styles (typography plugin)

---

### 3.2 Code Changes

#### File 1: `apps/web/components/ChatPanel.tsx`

**Added**:
1. **Markdown rendering** for assistant messages:
   ```tsx
   import ReactMarkdown from "react-markdown";
   import remarkGfm from "remark-gfm";

   {msg.role === "assistant" ? (
     <div className="prose prose-sm ...">
       <ReactMarkdown remarkPlugins={[remarkGfm]}>
         {msg.content}
       </ReactMarkdown>
     </div>
   ) : (
     <div>{msg.content}</div>
   )}
   ```

2. **Collapsible options panel**:
   ```tsx
   const [isOptionsExpanded, setIsOptionsExpanded] = useState(false);

   // Compact header
   대화 중: 삼성화재 · 메리츠화재  [옵션 ▾]

   // Collapsible panel
   {isOptionsExpanded && (
     <div className="max-h-48 overflow-y-auto">
       보험사 선택 / 담보명 입력 / 대화 초기화
     </div>
   )}
   ```

3. **ChatGPT-style input**:
   - Message input: `rows={1}` (single line, auto-expand on type)
   - Rounded borders: `rounded-lg`
   - Compact padding: `px-4 py-2`

**Lines Modified**: ~180 lines (major refactor of input area)

---

#### File 2: `apps/web/tailwind.config.ts` (NEW)

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/typography"),
  ],
};

export default config;
```

**Purpose**: Enable `prose` classes for markdown styling

---

#### File 3: `apps/web/package.json` (AUTO-UPDATED)

```json
{
  "dependencies": {
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0",
    "@tailwindcss/typography": "^0.5.10"
  }
}
```

---

## 4. UI Behavior

### 4.1 Initial State (Before First Message)

```
[보험사/담보 선택 ▾]  ← Collapsed by default

질문을 입력하세요...
[________________________________] [전송]
```

Click "보험사/담보 선택 ▾" → Shows insurer buttons + coverage input

---

### 4.2 Active Conversation (After First Message)

```
대화 중: 삼성화재 · 메리츠화재  [옵션 ▾]  ← Collapsed by default

질문을 입력하세요...
[________________________________] [전송]
```

Click "옵션 ▾" → Shows options panel (insurers disabled, coverage enabled)

---

### 4.3 Left Bubble Rendering

**Assistant messages**:
- Rendered as Markdown with tables, lists, headings, links
- Prose styles: compact spacing, small font, gray headings
- Tables: striped rows, borders, compact padding

**User messages**:
- Plain text (no markdown parsing)
- Blue background, white text

---

## 5. Prose Styles (Tailwind Typography)

```tsx
className="prose prose-sm max-w-none
  prose-headings:text-gray-900
  prose-h2:text-base
  prose-h2:font-semibold
  prose-h2:mt-0
  prose-h2:mb-2
  prose-p:my-1
  prose-ul:my-1
  prose-li:my-0.5
  prose-table:text-xs
  prose-th:bg-gray-200
  prose-th:p-2
  prose-td:p-2
  prose-td:border
  prose-td:border-gray-300"
```

**Customizations**:
- `prose-sm`: Smaller font size (chat bubbles)
- `max-w-none`: No max width restriction
- `prose-h2:text-base`: H2 same size as body
- `prose-table:text-xs`: Compact table font
- `prose-th:bg-gray-200`: Light gray table headers
- `prose-td:border`: Table cell borders

---

## 6. Validation Scenario (Demo Flow)

### Test Steps

1. **Initial State**:
   - ✅ Bottom dock: collapsed (single line: "보험사/담보 선택 ▾" + input)
   - ✅ Chat area: full screen height

2. **Click Example Button** (삼성화재 암진단비):
   - ✅ Bottom dock: collapsed ("대화 중: 삼성화재" + "옵션 ▾" + input)
   - ✅ Left bubble: Markdown rendering (headings, bullets, tables if any)
   - ✅ Right panel: Detailed view (unchanged)

3. **Type "메리츠는?"**:
   - ✅ Bottom dock: still collapsed
   - ✅ Left bubble: Markdown rendering for EX2_DETAIL response

4. **Type "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"**:
   - ✅ LIMIT_FIND clarification appears (STEP NEXT-106)
   - ✅ Coverage input disabled (gray background)
   - ✅ Bottom dock: multi-select insurers (STEP NEXT-106)

5. **Select insurer + submit**:
   - ✅ EX2_LIMIT_FIND table response
   - ✅ Left bubble: **Markdown table rendering** (핵심!)
   - ✅ Bottom dock: restored to collapsed state

---

## 7. Success Criteria (DoD)

### ✅ Left Bubble (Markdown Rendering)

- [ ] Assistant messages render as markdown
- [ ] Tables display correctly (striped, bordered, compact)
- [ ] Headings, bullets, links all render
- [ ] User messages remain plain text (blue bubble)

### ✅ Bottom Dock (Collapsed by Default)

- [ ] Initial state: "보험사/담보 선택 ▾" + input only
- [ ] Active conversation: "대화 중: ..." + "옵션 ▾" + input only
- [ ] Options panel: collapsible (click ▾/▴ to toggle)
- [ ] Options panel: scrollable if tall (max-h-48)
- [ ] Chat area: occupies **majority** of screen height

### ✅ ChatGPT Style Impression

- [ ] Customer sees: "대화 중심 UI" (not "설문 form")
- [ ] Left bubble: rich content visible (tables, summaries)
- [ ] Bottom dock: minimal (like ChatGPT input bar)
- [ ] Demo flow: EX2 → 전환 → LIMIT_FIND seamless

---

## 8. Prohibited Behaviors (Explicit NO)

❌ NO backend비교/판단 로직 변경
❌ NO 추천/추론/스코어링 추가
❌ NO 버튼으로 자동 질문 실행 (텍스트 힌트만)
❌ NO coverage_code UI 노출
❌ NO LLM usage

---

## 9. Regression Check

### Existing Features (MUST NOT BREAK)

- [x] STEP NEXT-97: Auto-scroll on new messages
- [x] STEP NEXT-101: Conversation context carryover
- [x] STEP NEXT-102: Insurer switch + LIMIT_FIND validation
- [x] STEP NEXT-103: Payload override for insurer switch
- [x] STEP NEXT-104: Followup hints (text-only)
- [x] STEP NEXT-106: Coverage input disabled during LIMIT_FIND clarification

---

## 10. Final Statement

> **ChatGPT UI 정합 = 대화 중심, 옵션 최소화, 응답 풍부**
>
> Left Bubble에 미니 테이블/요약이 들어가고,
> Bottom Dock이 collapsed 기본값이며,
> 고객이 "ChatGPT처럼 대화로 진행된다"고 느끼면 성공이다.

---

**Constitutional Lock**: ✅ STEP NEXT-108 Complete
**View Layer**: UI rendering + layout ONLY
**Business Logic**: NO changes
**Demo Flow**: EX2 → 메리츠는? → LIMIT_FIND (ChatGPT style)
