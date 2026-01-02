# Intent Router Rules SSOT

**STEP NEXT-78: Intent Router Lock**

## Purpose

Define **explicit, deterministic rules** for routing user queries to the correct MessageKind.

**Goals**:
1. Eliminate intent confusion between EX2 / EX4
2. Lock routing logic to prevent ambiguity
3. Ensure "보장한도 차이" → EX2_LIMIT_FIND (NOT EX4_ELIGIBILITY)

---

## Constitutional Rules (Hard Stop)

1. ❌ **NO LLM-based classification**
2. ✅ **Rule-based pattern matching ONLY**
3. ✅ **Priority: Category > FAQ > Keywords**
4. ✅ **Unknown intent → Clarification request**
5. ✅ **Intent is LOCKED (cannot be overridden by inference)**

---

## Intent Mapping (1:1)

| Intent | MessageKind | Purpose |
|--------|-------------|---------|
| 예제1 | `EX1_PREMIUM_DISABLED` | 보험료 비교 (현재 비활성) |
| 예제2 | `EX2_LIMIT_FIND` | 보장한도/조건 **값 차이** 비교 |
| 예제3 | `EX3_COMPARE` | 2개 보험사 종합 비교 |
| 예제4 | `EX4_ELIGIBILITY` | 질병 하위개념 보장 **가능 여부** (O/X/△) |

---

## Routing Rules (Priority Order)

### Priority 1: Explicit `kind` (100% Deterministic)

If `ChatRequest.kind` is set → Use it directly (NO router)

**Use Case**: FAQ button click, API direct call

### Priority 2: Category-based Routing (100% Confidence)

If `ChatRequest.selected_category` is set → Use category mapping

**Mapping**:
```python
{
    "단순보험료 비교": "EX1_PREMIUM_DISABLED",
    "② 상품/담보 설명": "EX2_LIMIT_FIND",  # CHANGED in STEP NEXT-78
    "상품 비교": "EX3_COMPARE",
    "보험 상식": "KNOWLEDGE_BASE"  # Future
}
```

### Priority 3: Pattern Matching (Fallback)

If no explicit routing → Use keyword patterns

**Threshold**: ≥ 0.3 confidence (30% of patterns matched)

---

## Pattern Matching Rules (LOCKED)

### EX1_PREMIUM_DISABLED

**Keywords**:
- "보험료", "납입", "가격", "비용"
- "월납", "총납", "저렴", "비싸"
- "정렬", "순위"

**Examples**:
- "보험료가 저렴한 순으로 보여줘"
- "월납 보험료 비교해줘"

**Output**: Disabled notice (no premium data)

---

### EX2_LIMIT_FIND

**Purpose**: Find **differences in coverage limits/conditions**

**Keywords** (STEP NEXT-78: LOCKED):
- "보장한도" + "다른" / "차이" / "비교"
- "한도" + "다른"
- "조건" + "다른"
- "지급유형" + "다른"
- "면책" / "감액" + "다른"

**Anti-Patterns** (MUST NOT match):
- ❌ "보장 가능 여부" → EX4
- ❌ "O/X" → EX4
- ❌ "제자리암", "경계성종양", "유사암" (질병 하위개념) → EX4

**Examples**:
- ✅ "보장한도가 다른 상품 찾아줘"
- ✅ "A사와 B사의 보장한도 차이를 비교해줘"
- ✅ "면책기간이 다른 상품은?"
- ❌ "제자리암 보장 가능 여부" → EX4

**Output**: Diff table (NO O/X/△)

---

### EX3_COMPARE

**Purpose**: Integrated comparison of 2+ insurers

**Keywords**:
- "비교해줘" + 보험사 ≥ 2
- "통합 비교"
- "전체 비교"
- "종합 비교"

**Examples**:
- "삼성화재와 메리츠화재 암진단비 비교해줘"
- "A사, B사 상품 비교"

**Output**: Comparison table + KPI + common notes

---

### EX4_ELIGIBILITY

**Purpose**: Check eligibility for disease subtypes (O/X/△)

**Keywords** (STEP NEXT-78: STRENGTHENED):
- 질병 하위개념 명시:
  - "제자리암", "경계성종양", "유사암"
  - "갑상선암", "기타피부암", "대장점막내암"
  - "전립선암", "방광암"
- "보장 가능", "보장 여부"
- "O/X", "가능 여부"

**Anti-Patterns** (MUST NOT match):
- ❌ "보장한도 차이" → EX2
- ❌ "조건 비교" → EX2

**Examples**:
- ✅ "제자리암 보장 가능 여부"
- ✅ "갑상선암 O/X 확인"
- ✅ "유사암 보장 여부"
- ❌ "보장한도가 다른 상품" → EX2

**Output**: Eligibility matrix (O/X/△)

---

## Decision Tree (Simplified)

```
Query Input
  │
  ├─ Has explicit kind? → Use kind (100%)
  │
  ├─ Has category? → Use category mapping (100%)
  │
  ├─ Contains "보장한도" + "다른/차이"?
  │   └─ YES → EX2_LIMIT_FIND
  │
  ├─ Contains disease subtype (제자리암, 유사암, etc.)?
  │   └─ YES → EX4_ELIGIBILITY
  │
  ├─ Contains "비교" + 보험사 ≥ 2?
  │   └─ YES → EX3_COMPARE
  │
  ├─ Contains "보험료"?
  │   └─ YES → EX1_PREMIUM_DISABLED
  │
  └─ Unknown → Clarification request
```

---

## Clarification Strategy

If confidence < 0.3 (ambiguous) → Ask user

**Questions**:
1. "어떤 항목을 비교하시겠습니까?"
   - 보장한도
   - 보장 가능 여부 (O/X)
   - 종합 비교
2. "보험사를 선택해주세요" (if missing)
3. "담보를 선택해주세요" (if missing)

---

## Examples with Routing

### Example 1: "보장한도가 다른 상품 찾아줘"

**Match**:
- Pattern: "보장한도" + "다른" → EX2_LIMIT_FIND
- Confidence: 1.0

**Route**: `EX2_LIMIT_FIND`

**Output**: Diff table (insurer × limit_summary)

---

### Example 2: "제자리암 보장 가능 여부"

**Match**:
- Pattern: "제자리암" (질병 하위개념) + "보장 가능" → EX4_ELIGIBILITY
- Confidence: 1.0

**Route**: `EX4_ELIGIBILITY`

**Output**: Eligibility matrix (O/X/△)

---

### Example 3: "삼성화재와 메리츠화재 암진단비 비교"

**Match**:
- Pattern: "비교" + 보험사 2개 → EX3_COMPARE
- Confidence: 1.0

**Route**: `EX3_COMPARE`

**Output**: Integrated comparison table

---

### Example 4: "보험료 저렴한 순"

**Match**:
- Pattern: "보험료" + "저렴" → EX1_PREMIUM_DISABLED
- Confidence: 1.0

**Route**: `EX1_PREMIUM_DISABLED`

**Output**: Disabled notice

---

## Validation Rules

### Pre-Execution Validation

Before handler execution:
1. ✅ Required slots present (coverage_names, insurers, etc.)
2. ✅ Insurer codes normalized (삼성화재 → samsung)
3. ✅ Coverage names canonical (암진단비 → A4200_1)
4. ✅ compare_field extracted (보장한도, 지급유형, etc.)

### Post-Execution Validation

After handler execution:
1. ✅ EX2_LIMIT_FIND → NO O/X/△ in output
2. ✅ EX4_ELIGIBILITY → Must have O/X/△ matrix
3. ✅ EX3_COMPARE → Must have comparison table
4. ✅ All responses → Forbidden phrase validation

---

## Anti-Confusion Gates (STEP NEXT-78)

### Gate 1: EX2 vs EX4

**Question**: "보장한도가 다른 상품 찾아줘"

**Decision**:
- Contains "다른" / "차이" → **Value comparison** → EX2_LIMIT_FIND
- Does NOT contain disease subtype → NOT EX4

**Result**: EX2_LIMIT_FIND ✅

---

### Gate 2: EX4 Subtype Detection

**Question**: "제자리암 보장 여부"

**Decision**:
- Contains "제자리암" (subtype) → **Eligibility check** → EX4_ELIGIBILITY
- Does NOT contain "다른" / "차이" → NOT EX2

**Result**: EX4_ELIGIBILITY ✅

---

### Gate 3: EX3 Multi-Insurer

**Question**: "A사, B사 비교"

**Decision**:
- Contains ≥ 2 insurers → **Integrated comparison** → EX3_COMPARE
- General "비교" keyword → NOT specific field comparison

**Result**: EX3_COMPARE ✅

---

## Implementation Checklist

- [x] Document intent mapping (this file)
- [ ] Update `IntentRouter.PATTERNS` in `chat_intent.py`
- [ ] Add disease subtype detection in `IntentRouter.detect_intent()`
- [ ] Add EX2_LIMIT_FIND MessageKind to `chat_vm.py`
- [ ] Implement `EX2LimitFindComposer`
- [ ] Implement `EX2LimitFindHandler`
- [ ] Add anti-confusion gates in router logic
- [ ] Test with example queries (EX2 vs EX4 separation)

---

**Version**: STEP NEXT-78
**Date**: 2026-01-02
**Status**: SSOT (Single Source of Truth)
