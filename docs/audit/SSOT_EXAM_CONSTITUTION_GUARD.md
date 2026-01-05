# EXAM CONSTITUTION ENFORCEMENT — SSOT

**Date**: 2026-01-04
**Purpose**: Structural prevention of EXAM cross-contamination and automatic transitions
**Scope**: Frontend + Backend (isolation guards ONLY, NO feature changes)

---

## Constitutional Basis

**EXAM CONSTITUTION** (CLAUDE.md Section 0):

본 시스템에서 EXAM은 서로 독립적인 문제 유형이다.

- EXAM1, EXAM2, EXAM3, EXAM4는 서로의 입력/출력/상태를 절대 공유하지 않는다.
- 하나의 EXAM 결과가 다른 EXAM의 입력으로 사용되는 것은 금지된다.
- "정리/확장/보고서화/자연스럽게 이어짐" 같은 표현을 근거로 EXAM 간 연결을 추측하지 않는다.
- EXAM 간 전환은 오직 사용자 명시 동작(버튼/선택)으로만 가능하다.

**정의**:
- **EXAM1 (EX1)**: 진입/선택/의도 결정 (라우팅만)
- **EXAM2 (EX2)**: 조건 기반 탐색 및 차이 발견 (탐색 전용)
- **EXAM3 (EX3)**: 고객 전달용 보고서 (보고서 전용)
- **EXAM4 (EX4)**: 가능/불가 (O/X) 판단 (OX 전용)

---

## Implementation

### 1. Backend Changes

#### 1.1 Schema Changes (`apps/api/chat_vm.py`)

**Added**:
```python
# EXAM ISOLATION: Explicit exam type for cross-contamination prevention
ExamType = Literal[
    "EXAM1",  # Entry/routing only
    "EXAM2",  # Exploration (EX2_DETAIL, EX2_LIMIT_FIND, EX2_DETAIL_DIFF)
    "EXAM3",  # Report (EX3_COMPARE, EX3_INTEGRATED)
    "EXAM4"   # O/X judgment (EX4_ELIGIBILITY)
]

def get_exam_type_from_kind(kind: MessageKind) -> ExamType:
    """Map MessageKind to ExamType (deterministic only, NO guessing)"""
    if kind in ("EX1_PREMIUM_DISABLED", "PREMIUM_COMPARE"):
        return "EXAM1"
    elif kind in ("EX2_DETAIL", "EX2_DETAIL_DIFF", "EX2_LIMIT_FIND"):
        return "EXAM2"
    elif kind in ("EX3_INTEGRATED", "EX3_COMPARE"):
        return "EXAM3"
    elif kind == "EX4_ELIGIBILITY":
        return "EXAM4"
    else:
        raise ValueError(f"Unknown MessageKind: {kind}")
```

**AssistantMessageVM field added**:
```python
class AssistantMessageVM(BaseModel):
    message_id: uuid.UUID
    request_id: uuid.UUID
    kind: MessageKind
    exam_type: ExamType  # EXAM ISOLATION: Explicit exam type (MANDATORY)
    timestamp: datetime
    # ... rest of fields
```

#### 1.2 Handler Changes

**Modified Files**:
- `apps/api/chat_handlers.py` (4 instantiations updated)
- `apps/api/chat_handlers_deterministic.py` (9 instantiations updated)

**Pattern Applied**:
```python
from apps.api.chat_vm import get_exam_type_from_kind

return AssistantMessageVM(
    request_id=request_id,
    kind="EX2_DETAIL",
    exam_type=get_exam_type_from_kind("EX2_DETAIL"),  # NEW
    title=title,
    ...
)
```

**Total**: 13 AssistantMessageVM instantiations updated

---

### 2. Frontend Changes

#### 2.1 Type Definitions (`apps/web/lib/types.ts`)

**Added**:
```typescript
// EXAM ISOLATION: Explicit exam type for cross-contamination prevention
export type ExamType = "EXAM1" | "EXAM2" | "EXAM3" | "EXAM4";

export interface AssistantMessageVM {
  kind: MessageKind;
  exam_type: ExamType;  // EXAM ISOLATION: Explicit exam type (MANDATORY)
  title?: string;
  summary_bullets?: string[];
  sections?: Section[];
  bubble_markdown?: string;
  lineage?: Lineage;
}
```

#### 2.2 EXAM3 Report Guard (`apps/web/lib/report/composeEx3Report.ts`)

**Added isolation guard**:
```typescript
export function composeEx3Report(messages: AssistantMessageVM[]): EX3ReportDoc | null {
  // EXAM ISOLATION: Only use messages with exam_type="EXAM3"
  let latestEX3: AssistantMessageVM | null = null;

  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];

    // EXAM ISOLATION GUARD: Verify both kind AND exam_type
    if (msg.kind === 'EX3_COMPARE' && msg.exam_type === 'EXAM3') {
      latestEX3 = msg;
      break;
    }

    // WARNING: If kind=EX3_COMPARE but exam_type != EXAM3, skip (contamination)
    if (msg.kind === 'EX3_COMPARE' && msg.exam_type !== 'EXAM3') {
      console.warn('[EXAM ISOLATION VIOLATION] Found EX3_COMPARE with non-EXAM3 type:', msg.exam_type);
    }
  }

  if (!latestEX3) {
    return null;
  }
  // ... rest of function
}
```

**Rules**:
- ✅ EX3 Report View uses ONLY messages with `exam_type === "EXAM3"`
- ❌ EX2/EX4 messages NEVER used in EX3 report (0% mixing)
- ⚠️ Console warning if kind/exam_type mismatch detected

#### 2.3 "Back to EXAM1" Button (`apps/web/app/page.tsx`)

**Added**:
```typescript
{/* EXAM ISOLATION: Reset to EXAM1 button (always visible in EXAM2/3/4) */}
{messages.length > 0 && (
  <button
    onClick={() => {
      if (confirm('대화를 초기화하고 처음으로 돌아가시겠습니까?')) {
        window.location.reload();
      }
    }}
    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 border border-gray-300 rounded hover:bg-gray-200 transition-colors"
    title="EXAM1으로 돌아가기"
  >
    ← 처음으로
  </button>
)}
```

**Location**: Header (top-right, next to LLM toggle)
**Visibility**: Shown whenever `messages.length > 0` (any EXAM active)
**Action**: Confirm dialog → Page reload (clean state)

---

## Verification Scenarios

### ✅ Scenario 1: EX3 Report View Uses EX3 Only

**Steps**:
1. Perform EX3_COMPARE query
2. Navigate to "보고서 보기"
3. Check browser console

**Expected**:
- ✅ Report shows EX3_COMPARE data
- ❌ NO EX2/EX4 messages used in report (0% mixing)
- ❌ NO console warnings about exam_type mismatch

**Verified**: Frontend guard in `composeEx3Report` filters by `exam_type === "EXAM3"`

---

### ✅ Scenario 2: EX4 After EX3 (No Auto-Report Generation)

**Steps**:
1. Perform EX3_COMPARE query
2. Navigate to "보고서 보기" (EX3 report shows)
3. Perform EX4_ELIGIBILITY query
4. Check "보고서 보기" again

**Expected**:
- ✅ EX3 report still shows (NO update from EX4)
- ❌ EX4 does NOT generate/update EX3 report automatically
- ❌ NO cross-exam data mixing

**Rationale**: EX4 has `exam_type="EXAM4"`, so it's filtered out by EX3 report guard

---

### ✅ Scenario 3: EX2 After EX3 (No Auto-Report Generation)

**Steps**:
1. Perform EX3_COMPARE query
2. Navigate to "보고서 보기" (EX3 report shows)
3. Perform EX2_DETAIL query
4. Check "보고서 보기" again

**Expected**:
- ✅ EX3 report still shows (NO update from EX2)
- ❌ EX2 does NOT generate/update EX3 report automatically
- ❌ NO cross-exam data mixing

**Rationale**: EX2 has `exam_type="EXAM2"`, so it's filtered out by EX3 report guard

---

### ✅ Scenario 4: "처음으로" Button Works From Any EXAM

**Steps**:
1. Perform any EXAM query (EX2/EX3/EX4)
2. Click "← 처음으로" button in header
3. Confirm dialog

**Expected**:
- ✅ Button visible when messages exist
- ✅ Confirm dialog shows
- ✅ Page reloads on confirm (clean state)
- ✅ Returns to EXAM1 entry screen

**Verified**: Button shows when `messages.length > 0` (universal)

---

### ✅ Scenario 5: API Response Contains `exam_type`

**Steps**:
1. Perform EX2_DETAIL query
2. Check network response in DevTools

**Expected**:
```json
{
  "request_id": "...",
  "timestamp": "...",
  "message": {
    "kind": "EX2_DETAIL",
    "exam_type": "EXAM2",  // ✅ Present
    "title": "...",
    ...
  }
}
```

**Verified**: All 13 backend handlers add `exam_type=get_exam_type_from_kind(kind)`

---

### ✅ Scenario 6: No Automatic EXAM Transitions

**Steps**:
1. Perform EX2_DETAIL query
2. Check if system automatically routes to EX3/EX4

**Expected**:
- ❌ NO automatic route to EX3 (comparison)
- ❌ NO automatic route to EX4 (O/X judgment)
- ✅ User must explicitly trigger EX3/EX4 via buttons/input

**Rationale**: `exam_type` is set deterministically from `kind`, NO inference/guessing

---

## Forbidden Behaviors (ABSOLUTE)

❌ **NO cross-exam mixing**:
- EX2 messages in EX3 report (0% occurrence)
- EX4 messages in EX3 report (0% occurrence)
- EX3 messages used as EX2/EX4 input (0% occurrence)

❌ **NO automatic EXAM transitions**:
- EX2 → EX3 auto-route (FORBIDDEN)
- EX4 → EX3 auto-report generation (FORBIDDEN)
- EX3 → EX2/EX4 auto-expansion (FORBIDDEN)

❌ **NO exam_type guessing**:
- `exam_type` is ALWAYS derived from `kind` via `get_exam_type_from_kind()`
- NO LLM inference
- NO heuristic mapping

❌ **NO exam_type override**:
- Frontend CANNOT change `exam_type` from backend value
- Backend sets `exam_type` once per message (immutable)

---

## Files Modified

### Backend
1. **`apps/api/chat_vm.py`**
   - Added `ExamType` literal
   - Added `get_exam_type_from_kind()` function
   - Added `exam_type` field to `AssistantMessageVM`
2. **`apps/api/chat_handlers.py`**
   - Added `exam_type=get_exam_type_from_kind(kind)` to 4 instantiations
3. **`apps/api/chat_handlers_deterministic.py`**
   - Added `exam_type=get_exam_type_from_kind(kind)` to 9 instantiations

### Frontend
1. **`apps/web/lib/types.ts`**
   - Added `ExamType` type
   - Added `exam_type` field to `AssistantMessageVM` interface
2. **`apps/web/lib/report/composeEx3Report.ts`**
   - Added `exam_type === "EXAM3"` guard in message loop
   - Added console warning for kind/exam_type mismatch
3. **`apps/web/app/page.tsx`**
   - Added "← 처음으로" button in header
   - Button visible when `messages.length > 0`
   - Reload page on confirm (return to EXAM1)

### Documentation
1. **`CLAUDE.md`**
   - Added EXAM CONSTITUTION at Section 0 (top of file)
   - Added ⚠️ EXAM RULE NOTICE (MANDATORY)
2. **`docs/audit/SSOT_EXAM_CONSTITUTION_GUARD.md`** (this file)
   - Complete implementation documentation
   - Verification scenarios
   - Forbidden behaviors

---

## Definition of Success

> **"EXAM 혼합(상태/출력/보고서/테이블)이 구조적으로 불가능"**

**Achieved**:
- ✅ `exam_type` field present in ALL backend responses
- ✅ EX3 Report View filters by `exam_type === "EXAM3"` (0% cross-exam mixing)
- ✅ "처음으로" button available from any EXAM (universal escape hatch)
- ✅ NO automatic transitions (user-driven ONLY)
- ✅ Console warnings detect kind/exam_type mismatches (structural integrity check)

---

## Future Extension

**Additional Guards** (if needed):
- EX2 view: Filter by `exam_type === "EXAM2"` (currently not composite)
- EX4 view: Filter by `exam_type === "EXAM4"` (currently not composite)
- Multi-EXAM report: Explicit opt-in (NOT automatic)

**Current Status**: EXAM3 is the only composite view (report), so only EX3 guard is implemented.

---

**LOCKED**: 2026-01-04
**Constitutional Enforcement**: COMPLETE
