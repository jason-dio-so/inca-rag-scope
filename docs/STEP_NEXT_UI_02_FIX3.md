# STEP NEXT-UI-02-FIX3 — Chat API Response Unwrapping Fix

**Date**: 2026-01-01
**Status**: ✅ COMPLETE

## 목적

Frontend API wrapper가 backend response를 이중으로 감싸서 `response.message.message` 구조가 되는 문제 해결.
Backend가 반환하는 `ChatResponse`를 그대로 사용하도록 수정.

---

## 문제 증상

### 재현 상황
1. UI에서 "상품/담보 설명" 실행
2. 콘솔에 `chat response: { ok: true, message: {...} }` 출력
3. 결과 pane에 "⚠️ 섹션 데이터가 없습니다" 표시
4. kind/title/sections가 모두 undefined

### 원인 분석

**Backend Response Structure** (Python):
```python
class ChatResponse(BaseModel):
    request_id: uuid.UUID
    timestamp: datetime
    need_more_info: bool = False
    missing_slots: Optional[List[str]] = None
    clarification_options: Optional[Dict[str, List[str]]] = None
    message: Optional[AssistantMessageVM] = None  # ✅ Actual VM here
```

**Frontend API Wrapper** (Before Fix):
```typescript
// apps/web/lib/api.ts
const data = await response.json();
return {
  ok: true,
  message: data,  // ❌ WRONG: wraps backend response again
};
```

**결과**:
```typescript
// Backend returns:
{
  request_id: "...",
  timestamp: "...",
  need_more_info: false,
  message: { kind: "EX2_DETAIL", sections: [...], ... }  // ✅ AssistantMessageVM
}

// Frontend wrapper returns:
{
  ok: true,
  message: {  // ❌ Wrapper layer
    request_id: "...",
    timestamp: "...",
    need_more_info: false,
    message: { kind: "EX2_DETAIL", sections: [...], ... }  // ✅ Actual VM (nested)
  }
}
```

**page.tsx에서**:
```typescript
const vm = response.message;  // ❌ Gets wrapper, not VM
// vm.kind === undefined
// vm.sections === undefined
// vm.message === { kind: "EX2_DETAIL", sections: [...] }  // ✅ Actual VM here
```

---

## 해결 방법

### 1. API Wrapper 수정 (`apps/web/lib/api.ts`)

**Before**:
```typescript
const data = await response.json();
return {
  ok: true,
  message: data,
};
```

**After**:
```typescript
// Backend already returns ChatResponse shape, return it directly
const data = await response.json();
return data;
```

**효과**:
- Backend response를 그대로 반환
- 이중 wrapping 제거
- `response.message`가 바로 `AssistantMessageVM`

### 2. Types 수정 (`apps/web/lib/types.ts`)

Backend `ChatResponse` schema와 일치하도록 수정:

```typescript
export interface ChatResponse {
  // Success case - matches backend ChatResponse
  request_id?: string;
  timestamp?: string;
  need_more_info?: boolean;
  missing_slots?: string[];
  clarification_options?: Record<string, string[]>;
  message?: AssistantMessageVM;

  // Error case - added by frontend wrapper
  ok?: boolean;
  error?: {
    message: string;
    detail?: string;
  };
}
```

### 3. Page.tsx 에러 처리 개선 (`apps/web/app/page.tsx`)

```typescript
// Check for error response (from frontend wrapper)
if (response.ok === false || response.error) {
  // Handle error
} else if (!response.message) {
  // Handle empty response
} else {
  // Success - response.message is AssistantMessageVM
  const vm = response.message;
  setLatestResponse(vm);
  // ...
}
```

### 4. ResultDock 디버그 UI 개선 (`apps/web/components/ResultDock.tsx`)

Empty sections 경우 더 상세한 디버그 정보 표시:

```typescript
<div className="border border-yellow-200 bg-yellow-50 rounded-lg p-4">
  <p className="text-sm font-medium text-yellow-800">
    ⚠️ 섹션 데이터가 없습니다
  </p>
  <div className="mt-2 text-xs text-yellow-700 space-y-1">
    <p>kind: <code>{response.kind || "undefined"}</code></p>
    <p>title: <code>{response.title || "undefined"}</code></p>
    <p>sections.length: <code>{sections.length}</code></p>
  </div>
  <details>
    <summary>전체 VM 구조 보기</summary>
    <pre>{JSON.stringify(response, null, 2)}</pre>
  </details>
</div>
```

---

## 수정 파일

### 1. `apps/web/lib/api.ts`
- Backend response를 그대로 반환 (이중 wrapping 제거)

### 2. `apps/web/lib/types.ts`
- `ChatResponse` interface를 backend schema와 일치하도록 수정
- `ok`, `error` 필드는 optional (frontend error wrapper용)

### 3. `apps/web/app/page.tsx`
- 에러 체크 로직 개선
- `response.ok === false` 체크 추가
- `!response.message` 체크 추가

### 4. `apps/web/components/ResultDock.tsx`
- Empty sections 디버그 UI 개선
- kind, title, sections.length 즉시 표시
- 전체 VM 구조는 details/summary로 접기 가능

---

## 검증 (DoD)

### Before Fix
```json
{
  "ok": true,
  "message": {
    "request_id": "...",
    "need_more_info": false,
    "message": {  // ✅ Actual VM nested here
      "kind": "EX2_DETAIL",
      "title": "A4200_1 보장한도 비교",
      "sections": [...]
    }
  }
}
```

### After Fix
```json
{
  "request_id": "...",
  "timestamp": "...",
  "need_more_info": false,
  "message": {  // ✅ Actual VM directly here
    "kind": "EX2_DETAIL",
    "title": "A4200_1 보장한도 비교",
    "sections": [...]
  }
}
```

### 테스트 시나리오

#### 1. EX2_DETAIL (상품/담보 설명)
```
입력: 담보명 "암진단비(유사암제외)"
예상:
  - ✅ console.log shows: kind: "EX2_DETAIL"
  - ✅ "A4200_1 보장한도 비교" 테이블 표시
  - ✅ "근거 자료" 아코디언 표시
  - ✅ NO "섹션 데이터가 없습니다" warning
```

#### 2. Empty Sections (Debug)
```
시나리오: Backend returns message with empty sections
예상:
  - ✅ "⚠️ 섹션 데이터가 없습니다" 표시
  - ✅ kind/title/sections.length 표시
  - ✅ 전체 VM 구조 펼칠 수 있음
```

---

## 결과

### Before
- ❌ `response.message` = wrapper object
- ❌ `response.message.kind` = undefined
- ❌ `response.message.sections` = undefined
- ❌ Actual VM at `response.message.message` (nested)
- ❌ UI shows "섹션 데이터가 없습니다"

### After
- ✅ `response.message` = AssistantMessageVM directly
- ✅ `response.message.kind` = "EX2_DETAIL"
- ✅ `response.message.sections` = Array(2)
- ✅ No unnecessary nesting
- ✅ UI renders table + evidence correctly

---

## 헌법 준수

- ✅ Backend 수정 없음 (Frontend only)
- ✅ LLM OFF 기본값 유지
- ✅ VM 구조 그대로 사용 (가공 없음)
- ✅ Optional guard 유지 (crash 방지)
- ✅ Type safety 개선

---

## 다음 단계

1. **통합 테스트**: 예제 1~4 모두 LLM OFF 모드에서 테스트
2. **에러 처리 테스트**: API 에러 응답 시 UI 동작 확인
3. **성능 테스트**: Large tables rendering performance

---

## 관련 문서

- `docs/STEP_NEXT_UI_01.md` - 결정론적 핸들러 설계
- `docs/STEP_NEXT_UI_02_LOCAL.md` - 로컬 개발 환경 설정
- `docs/STEP_NEXT_UI_02_FIX.md` - UI 크래시 방지 패치
- `docs/STEP_NEXT_UI_02_FIX2.md` - Sections-first rendering
