# STEP NEXT-133 (EXAM2): Absolute Guard Against Additional Info UI — SSOT

**Date**: 2026-01-04
**Status**: FINAL LOCK
**Constitutional Basis**: EXAM CONSTITUTION (EXAM 간 혼합 금지)

---

## 0. Purpose (목적)

EXAM2(탐색/상품간 비교)가 EXAM3(보험사 선택 기반 비교) 로직에 오염되어 발생한 **추가 정보 요청 UI 버그를 구조적으로 금지**한다.

### 버그 증상 (Before STEP NEXT-133)

1. EXAM2 질문 입력 → "추가 정보가 필요합니다" 문구 표시
2. 보험사 선택(2개) UI 표시
3. 담보명 재입력 UI 표시
4. 결과가 EX2_DETAIL(단일 보험사)로 붕괴 → "samsung 담보 정보 없음" 오류

### 성공 정의 (DoD)

- ✅ EXAM2에서 "추가 정보가 필요합니다" 0%
- ✅ EXAM2에서 보험사 선택 UI 0%
- ✅ EXAM2에서 담보명 재입력 UI 0%
- ✅ EXAM2 결과는 "표(다수 보험사/상품) + (선택) 한 줄 결론"만

---

## 1. EXAM Constitutional Rule (헌법 규칙)

> **EXAM2는 EXAM2만 한다 (절대 혼합 금지)**

### EXAM2 특성 (ABSOLUTE)

1. **보험사 자동 확장**: A사/B사/C사/… 모든 보험사 비교 (많을수록 좋음)
2. **추가 정보 수집 금지**: 사용자에게 추가 입력 요구 ❌
3. **보험사 선택 요구 금지**: 사용자가 보험사를 선택하지 않음 ❌
4. **담보명 재입력 금지**: 초기 질의에서 이미 담보를 받았다는 전제 ❌
5. **단일 보험사 fallback 금지**: EX2_DETAIL로 다운그레이드 ❌

---

## 2. Implementation (구현)

### (A) Frontend Guard: EXAM2에서 Clarification UI 절대 차단

**File**: `apps/web/lib/clarificationUtils.ts`

```typescript
} else if (examType === "EX2") {
  // STEP NEXT-133: EXAM2 NEVER shows clarification UI
  // EXAM2 is self-contained: auto-expand insurers, proceed with coverage from message
  missingInsurers = false;  // ABSOLUTE: EXAM2 never requires insurer selection
  missingCoverage = false;  // ABSOLUTE: EXAM2 never requires coverage re-input
}
```

**Rule**:
- `examType === "EX2"` → `need_more_info` 플로우 진입 금지
- `AdditionalInfoPanel` 렌더링 금지
- "추가 정보가 필요합니다" 말풍선 생성 금지

---

### (B) Backend Guard: EXAM2에서 need_more_info 발생 자체를 금지

**File**: `apps/api/chat_intent.py`

```python
# Step 2: Validate slots
# STEP NEXT-133: EXAM2 (EX2_LIMIT_FIND) NEVER requires additional info
# EXAM2 is self-contained: auto-expand insurers, use coverage from message
if kind == "EX2_LIMIT_FIND":
    # ABSOLUTE: Skip slot validation for EXAM2
    # EXAM2 proceeds with whatever data is available (auto-expand mode)

    # Auto-fill missing insurers (expand to all available)
    if not request.insurers or len(request.insurers) == 0:
        all_insurers = ["samsung", "meritz", "hanwha", "lotte", "kb", "hyundai", "heungkuk", "db"]
        request.insurers = all_insurers  # Auto-expand

    # Auto-extract coverage from message if missing
    if not request.coverage_names or len(request.coverage_names) == 0:
        coverage_from_message = extract_coverage_keywords(request.message)
        if coverage_from_message:
            request.coverage_names = coverage_from_message  # Auto-extract

    is_valid = True
    missing_slots = []
else:
    is_valid, missing_slots = SlotValidator.validate(request, kind)
```

**Rules**:
- `kind == "EX2_LIMIT_FIND"` → Slot validation 완전 skip
- Missing insurers → Auto-expand to all insurers (8개)
- Missing coverage → Auto-extract from message
- `need_more_info = false` 고정

---

### (C) EXAM2 Empty Result Handling (빈 결과 처리)

**Scenario**: 담보 데이터를 찾지 못한 경우

**Before** (버그):
```
EX2_DETAIL fallback → "samsung 담보 정보 없음" (단일 보험사 오류)
```

**After** (STEP NEXT-133):
```
EXAM2 전용 빈 결과 메시지:
"해당 담보의 비교 데이터를 찾지 못했습니다. 다른 담보로 시도해 주세요."
```

**Implementation**:
- Handler에서 `insurers` 비어있거나 `coverage_data` 없으면 → EXAM2 전용 메시지 반환
- EX2_DETAIL로 다운그레이드 금지 (ABSOLUTE)

---

## 3. Processing Flow (처리 흐름)

1. **User**: EXAM1에서 EXAM2 질문 입력
   예: "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘"

2. **Intent/Router**: EXAM2로 분기 → `kind = "EX2_LIMIT_FIND"`

3. **Validation (Backend)**:
   - EXAM2 감지 → Slot validation skip
   - Missing insurers → Auto-expand to all
   - Missing coverage → Auto-extract from message
   - `is_valid = True` (강제)

4. **Frontend**:
   - `examType === "EX2"` 확인
   - `showClarification = false` (강제)
   - AdditionalInfoPanel 렌더링 ❌
   - 보험사 선택 버튼 ❌
   - 담보 재입력 UI ❌

5. **Result**:
   - EXAM2 테이블 표시 ✅
   - 또는 EXAM2 전용 빈 결과 메시지 ✅

---

## 4. Verification Scenarios (검증 시나리오)

### Scenario 1 (핵심)
**Input**: "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘"

**Expected**:
- ✅ "추가 정보가 필요합니다" 문구 없음
- ✅ 보험사 선택 UI 없음
- ✅ 담보 입력 UI 없음
- ✅ 표가 나오거나, 표가 없으면 EXAM2 전용 빈 결과 메시지

### Scenario 2
**Input**: EXAM2 질문을 3회 반복

**Expected**:
- ✅ 매번 동일 UX (추가정보 UI 0%)

### Scenario 3
**Input**: EXAM3/EXAM4 수행 후 "처음으로" → 다시 EXAM2 질문

**Expected**:
- ✅ EXAM2에서 추가정보 UI 0% 유지

### Scenario 4 (Regression)
**Input**: EXAM3 질문 "암진단비 비교해줘"

**Expected**:
- ✅ 추가정보(보험사 선택) 플로우 정상 동작
- ✅ EXAM2 수정이 EXAM3를 망가뜨리지 않음

---

## 5. Forbidden Behaviors (금지 사항)

❌ **ABSOLUTE FORBIDDEN**:
1. EXAM2에서 `need_more_info` 기반 UI/말풍선/선택 패널 표시
2. EXAM2에서 보험사 "2개 선택" 요구
3. EXAM2에서 담보명 재입력 요구
4. EXAM2를 EX2_DETAIL로 fallback
5. EXAM2에서 추천/랭킹/판단 문구

---

## 6. Files Modified

### Frontend
- `apps/web/lib/clarificationUtils.ts`: EXAM2 clarification logic = false (ABSOLUTE)

### Backend
- `apps/api/chat_intent.py`: EXAM2 slot validation skip + auto-expand

---

## 7. Git Reflection

**Branch**: `feat/step-next-133-exam2-no-additional-info`

**Commit Message**:
```
feat(step-next-133): EXAM2 absolute guard against additional info UI

EXAM2(탐색/비교) 전용 처리:
- Frontend: EXAM2 clarification UI 절대 차단
- Backend: EXAM2 slot validation skip + auto-expand
- Constitutional: EXAM2는 추가정보 플로우 금지 (ABSOLUTE)

Fixes: EXAM2 → EXAM3 로직 오염 버그 완전 차단
SSOT: docs/audit/STEP_NEXT_133_EXAM2_NO_ADDITIONAL_INFO_GUARD.md

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 8. Update CLAUDE.md

**Section**: `# EXAM CONSTITUTION (SSOT)`

**Add Line**:
```markdown
- **EXAM2는 추가정보 플로우 금지** (ABSOLUTE): 보험사 자동 확장, 담보 메시지 추출, need_more_info = false
```

---

## 9. Definition of Success

> **"EXAM2 질문을 10번 반복해도 추가정보 UI가 1번도 안 뜨고, 매번 표 또는 빈 결과 메시지만 나오면 성공"**

---

## 10. EXAM CONSTITUTION Compliance

| EXAM Rule | Compliance |
|-----------|------------|
| EXAM2 = 탐색/비교 전용 | ✅ 추가정보 UI 0% |
| EXAM3 = 보험사 선택 비교 | ✅ Regression test 통과 |
| EXAM4 = O/X 판단 | ✅ 영향 없음 |
| EXAM 간 혼합 금지 | ✅ EXAM2 로직 독립 보장 |

---

**END OF SSOT**
