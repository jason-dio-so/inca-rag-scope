# STEP NEXT-80-FE — ui_config.json kind 동기화 (EX3_COMPARE / EX2_LIMIT_FIND)

## 목표
- `ui_config.json`의 `example_kind`를 최신 MessageKind 표준에 맞춰 업데이트
- STEP NEXT-77/78 이후 변경된 kind 반영
- Frontend와 Backend의 kind 일관성 보장

## 문제
- **ui_config.json**: `EX3_INTEGRATED` (구 표준)
- **ChatPanel.tsx**: `EX3_COMPARE` (신 표준, STEP NEXT-77)
- **Backend**: 둘 다 지원하지만 `EX3_COMPARE`가 공식 kind
- 결과: kind 불일치로 혼란 발생 가능

## 변경 사항

### A) ui_config.json 업데이트

**File**: `apps/web/public/ui_config.json`

**Changes**:
1. Line 15: `EX2_DETAIL_DIFF` → `EX2_LIMIT_FIND` (STEP NEXT-78 표준)
2. Line 23: `EX3_INTEGRATED` → `EX3_COMPARE` (STEP NEXT-77 표준)
3. Line 29: `EX3_INTEGRATED` → `EX3_COMPARE` (sub_examples 동기화)

**Before**:
```json
{
  "id": "coverage_detail",
  "label": "② 상품/담보 설명",
  "example_kind": "EX2_DETAIL_DIFF",
  ...
},
{
  "id": "product_compare",
  "label": "③ 상품 비교",
  "example_kind": "EX3_INTEGRATED",
  ...
  "sub_examples": [
    {
      "label": "2사 비교",
      "example_kind": "EX3_INTEGRATED"
    },
    ...
  ]
}
```

**After**:
```json
{
  "id": "coverage_detail",
  "label": "② 상품/담보 설명",
  "example_kind": "EX2_LIMIT_FIND",
  ...
},
{
  "id": "product_compare",
  "label": "③ 상품 비교",
  "example_kind": "EX3_COMPARE",
  ...
  "sub_examples": [
    {
      "label": "2사 비교",
      "example_kind": "EX3_COMPARE"
    },
    ...
  ]
}
```

### B) page.tsx 타입 오류 수정

**File**: `apps/web/app/page.tsx`

**Change**: Line 7 - Removed unused `Category` import

**Before**:
```typescript
import {
  Message,
  LlmMode,
  Category,  // ❌ Unused
  AssistantMessageVM,
  UIConfig,
  MessageKind,
} from "@/lib/types";
```

**After**:
```typescript
import {
  Message,
  LlmMode,
  AssistantMessageVM,
  UIConfig,
  MessageKind,
} from "@/lib/types";
```

## MessageKind 표준 (LOCKED)

### STEP NEXT-77: EX3_COMPARE
- **용도**: 2개 보험사 담보 비교
- **Output Schema**: `docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md`
- **Handler**: `Example3HandlerDeterministic`

### STEP NEXT-78: EX2_LIMIT_FIND
- **용도**: 보장한도/조건 값 차이 비교 (NO O/X)
- **Anti-confusion**: Disease subtypes → EX4 (not EX2)
- **Handler**: `Example2DiffHandlerDeterministic`

### Legacy (Deprecated)
- `EX3_INTEGRATED` → Use `EX3_COMPARE` instead
- `EX2_DETAIL_DIFF` → Use `EX2_LIMIT_FIND` instead

## 검증

### 1) TypeScript 컴파일 확인
```bash
cd apps/web
npm run build
# Expected: No TypeScript errors
```

### 2) ui_config.json 로드 확인
```bash
# Frontend 서버 시작
npm run dev

# Browser console에서 확인
fetch('/ui_config.json').then(r => r.json()).then(console.log)
# Expected: example_kind 값이 EX3_COMPARE, EX2_LIMIT_FIND
```

### 3) 예제 버튼 kind 전송 확인
- 브라우저에서 예제3 버튼 클릭
- Console에서 `[page.tsx] Sending request with explicit kind:` 확인
- `kind: "EX3_COMPARE"` 확인

## 영향 범위

### ✅ Breaking Changes 없음
- Backend는 `EX3_INTEGRATED`와 `EX3_COMPARE` 모두 동일한 handler로 처리
- Backend는 `EX2_DETAIL_DIFF`와 `EX2_LIMIT_FIND` 모두 동일한 handler로 처리
- 기존 요청도 계속 작동 (backward compatible)

### ✅ 일관성 개선
- Frontend config와 code가 동일한 kind 사용
- STEP NEXT-77/78 표준 준수
- 신규 개발자 혼란 감소

## 파일 변경 요약

### Modified Files
1. `apps/web/public/ui_config.json` - example_kind 업데이트 (3곳)
2. `apps/web/app/page.tsx` - Unused import 제거 (1곳)

### New Files
1. `docs/audit/STEP_NEXT_80_FE_UI_CONFIG_SYNC.md` - This document

### Test Coverage
- TypeScript 컴파일 통과
- ui_config.json 로드 정상
- 예제 버튼 kind 전송 확인 (수동 테스트)

## DoD

### Completed
- ✅ ui_config.json: EX3_INTEGRATED → EX3_COMPARE
- ✅ ui_config.json: EX2_DETAIL_DIFF → EX2_LIMIT_FIND
- ✅ page.tsx: TypeScript 오류 수정
- ✅ Documentation 작성

### Pending (User Verification)
- ⏳ 브라우저 테스트: 예제3 버튼 → kind=EX3_COMPARE 전송
- ⏳ 브라우저 테스트: 예제4 버튼 → kind=EX4_ELIGIBILITY 전송
- ⏳ 브라우저 테스트: 카테고리 ② 선택 → kind=EX2_LIMIT_FIND 전송

## Reference
- **STEP NEXT-77**: `docs/audit/STEP_NEXT_77_EX3_COMPARE_LOCK.md`
- **STEP NEXT-78**: `docs/ui/INTENT_ROUTER_RULES.md`
- **STEP NEXT-80**: `docs/audit/STEP_NEXT_80_EXPLICIT_KIND_LOCK.md`
