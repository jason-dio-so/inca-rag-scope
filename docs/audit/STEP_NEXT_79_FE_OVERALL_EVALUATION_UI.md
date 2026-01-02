# STEP NEXT-79-FE — EX4 종합평가(추천/판단) 프론트 통합 LOCK

## 목적 (WHY)

EX4_ELIGIBILITY 응답에 항상 포함되는 overall_evaluation 섹션을
프론트엔드에서 누락·변형 없이 고정 렌더링한다.

- "추천 / 비추천 / 중립" 판단이 UI에서 사라지거나 다른 섹션에 섞이는 문제를 구조적으로 차단
- ChatGPT-style UI 유지 + 고객 기획안의 예제 4 응답 형태 보장

---

## 적용 범위 (SCOPE)

**대상 Intent**: EX4_ELIGIBILITY 전용
**금지 사항**: 다른 EX2 / EX3 흐름에는 영향 금지

---

## 구현 완료 사항

### 1️⃣ Backend Schema (chat_vm.py)

Added Pydantic models for overall evaluation section:

```python
OverallDecision = Literal["RECOMMEND", "NOT_RECOMMEND", "NEUTRAL"]

class OverallEvaluationReason(BaseModel):
    type: str
    description: str
    refs: List[str]

class OverallEvaluation(BaseModel):
    decision: OverallDecision
    summary: str
    reasons: List[OverallEvaluationReason]
    notes: str

class OverallEvaluationSection(BaseModel):
    kind: Literal["overall_evaluation"] = "overall_evaluation"
    title: str
    overall_evaluation: OverallEvaluation
```

**Section Union Type** updated to include `OverallEvaluationSection`:

```python
Section = (
    ComparisonTableSection |
    InsurerExplanationsSection |
    CommonNotesSection |
    EvidenceAccordionSection |
    CoverageDiffResultSection |
    OverallEvaluationSection  # STEP NEXT-79
)
```

### 2️⃣ Frontend Types (types.ts)

Added TypeScript types matching backend schema:

```typescript
export type OverallDecision = "RECOMMEND" | "NOT_RECOMMEND" | "NEUTRAL";

export interface OverallEvaluationReason {
  type: string;
  description: string;
  refs: string[];
}

export interface OverallEvaluationSection {
  kind: "overall_evaluation";
  title: string;
  overall_evaluation: {
    decision: OverallDecision;
    summary: string;
    reasons: OverallEvaluationReason[];
    notes: string;
  };
}
```

**Section Union Type** updated:

```typescript
export type Section =
  | ComparisonTableSection
  | CommonNotesSection
  | EvidenceAccordionSection
  | CoverageDiffResultSection
  | OverallEvaluationSection;  // STEP NEXT-79-FE
```

### 3️⃣ UI Component (OverallEvaluationCard.tsx)

**Fixed rendering rules**:
1. **Decision Badge** (top, color-coded)
   - RECOMMEND → Green badge
   - NOT_RECOMMEND → Red badge
   - NEUTRAL → Gray badge

2. **Summary** (1 line, factual)
   - NO emotional phrases
   - Deterministic decision summary

3. **Reasons List** with refs
   - Info icon (ⓘ) for reasons with refs
   - Click to expand refs accordion
   - "근거 문서 없음" for Unknown status

4. **Notes** (fixed template)
   - Explanation of decision criteria

**Forbidden elements**:
- ❌ Scores, percentages, star ratings
- ❌ Emotional phrases ("좋습니다", "추천합니다")
- ❌ LLM-generated text

### 4️⃣ ResultDock Integration

Added explicit branch for overall_evaluation section:

```typescript
case "overall_evaluation":
  // STEP NEXT-79-FE: Overall evaluation card (EX4_ELIGIBILITY only)
  return <OverallEvaluationCard key={idx} section={section} />;
```

**Rendering order** (locked):
1. Eligibility Matrix table
2. **Overall Evaluation** (MANDATORY)
3. Common Notes

### 5️⃣ Handler Integration (chat_handlers_deterministic.py)

Updated Example4HandlerDeterministic to build OverallEvaluationSection:

```python
elif section_dict["kind"] == "overall_evaluation":
    # STEP NEXT-79: Build OverallEvaluationSection
    overall_eval_data = section_dict["overall_evaluation"]
    reasons = [
        OverallEvaluationReason(**reason)
        for reason in overall_eval_data["reasons"]
    ]
    overall_eval = OverallEvaluation(
        decision=overall_eval_data["decision"],
        summary=overall_eval_data["summary"],
        reasons=reasons,
        notes=overall_eval_data["notes"]
    )
    overall_eval_section = OverallEvaluationSection(
        title=section_dict["title"],
        overall_evaluation=overall_eval
    )
    sections.append(overall_eval_section)
```

---

## 테스트 검증 (DoD)

### Contract Tests ✅
**tests/test_ex4_overall_evaluation_contract.py** - 9 tests, all passing

- ✅ overall_evaluation always exists
- ✅ decision is valid enum
- ✅ RECOMMEND when O majority
- ✅ NOT_RECOMMEND when X majority
- ✅ NEUTRAL when mixed
- ✅ Reasons have refs (except Unknown)
- ✅ Deterministic (same input → same decision)
- ✅ No forbidden phrases
- ✅ Structure matches spec

### Integration Tests ✅
**tests/test_ex4_overall_evaluation_integration.py** - 7 tests, all passing

- ✅ EX4 response has overall_evaluation section
- ✅ Decision structure matches frontend types
- ✅ RECOMMEND scenario
- ✅ NOT_RECOMMEND scenario
- ✅ NEUTRAL scenario
- ✅ Section order preserved (matrix → evaluation → notes)
- ✅ No LLM usage (deterministic only)

**Total: 16/16 tests passing** ✅

---

## 안전장치 (Safety Gates)

1. **Backend validation**: Pydantic models enforce schema
2. **Frontend types**: TypeScript ensures type safety
3. **Explicit rendering**: No fallback to default renderer
4. **Order preservation**: Section order locked in composer
5. **Intent isolation**: Only EX4_ELIGIBILITY uses overall_evaluation

---

## 금지 사항 (ABSOLUTE)

- ❌ LLM usage in evaluation
- ❌ Frontend-side decision generation
- ❌ Modifying decision enum
- ❌ Mixing with other section types
- ❌ Scoring/weighting/inference

---

## 산출물

### Backend
- [x] `apps/api/chat_vm.py` - OverallEvaluationSection added to Section union
- [x] `apps/api/chat_handlers_deterministic.py` - Example4 handler updated
- [x] `tests/test_ex4_overall_evaluation_contract.py` - Contract tests
- [x] `tests/test_ex4_overall_evaluation_integration.py` - Integration tests

### Frontend
- [x] `apps/web/lib/types.ts` - OverallEvaluationSection type added
- [x] `apps/web/components/cards/OverallEvaluationCard.tsx` - New component
- [x] `apps/web/components/ResultDock.tsx` - Rendering logic added

### Documentation
- [x] `docs/audit/STEP_NEXT_79_FE_OVERALL_EVALUATION_UI.md`
- [x] `CLAUDE.md` updated (STEP NEXT-79 section)

---

## 다음 단계 (Next Steps)

1. ✅ Frontend UI integration complete
2. ✅ Tests passing (16/16)
3. ⏳ Manual UI testing with live API
4. ⏳ Evidence lazy load integration for refs
5. ⏳ Production deployment

---

**Commit Message:**
```
feat(step-79-fe): integrate overall evaluation UI for EX4

- Add OverallEvaluationSection to backend/frontend types
- Create OverallEvaluationCard component with fixed rendering
- Wire overall_evaluation rendering in ResultDock
- Update Example4 handler to build Pydantic section
- All tests passing (16/16 contract + integration)
```
