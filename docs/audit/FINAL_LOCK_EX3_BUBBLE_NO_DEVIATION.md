# FINAL LOCK: EX3 Bubble - NO DEVIATION

**Date**: 2026-01-04
**Type**: ABSOLUTE PROHIBITION RULE (행동 금지 규칙)
**Status**: LOCKED - NO MODIFICATIONS ALLOWED

---

## Purpose

This is NOT a modification request.
This is a **FINAL LOCK** defining what is **FORBIDDEN** in EX3_COMPARE bubble output.

**Any violation of these rules is a BUG.**

---

## ABSOLUTE RULES (행동 금지 규칙)

### Rule 1: NO Insurer-Specific Differences

EX3_COMPARE 왼쪽 요약 버블은 **보험사 간 차이 설명을 절대 포함하지 않는다**.

**FORBIDDEN**:
- ❌ "삼성화재는 A, 메리츠화재는 B"
- ❌ "{Insurer1}는 ..., {Insurer2}는 ..."
- ❌ Any insurer names (삼성, 메리츠, KB, 한화, 현대, 롯데, DB, 흥국)
- ❌ "즉," bullet format with insurer-specific items
- ❌ Any comparison language ("비교", "차이", "다릅니다")

**REASON**: EX3 bubble describes PRIMARY structure (NOT differences).

---

### Rule 2: AMOUNT-DRIVEN Coverage - ONE Sentence ONLY

암진단비, 암진단비(유사암제외)와 같은 AMOUNT-DRIVEN 담보는 **반드시 아래 한 문장만 사용한다**:

```
두 보험사는 모두 정액 지급 구조입니다.
```

**FORBIDDEN**:
- ❌ Additional explanation sentences
- ❌ "진단 또는 사고 발생 시 약정된 금액을 지급하는 방식으로..."
- ❌ "보장금액이 계약 시점에 명확히 정의됩니다"
- ❌ Any multi-line format
- ❌ Any elaboration beyond structure declaration

**REQUIRED**:
- ✅ Exactly ONE sentence
- ✅ "두 보험사는 모두 정액 지급 구조입니다." (EXACT TEXT)

---

### Rule 3: "삼성은 A, 메리츠는 B" - ABSOLUTE BAN

"삼성은 A, 메리츠는 B" 형식의 문장은 **EX3 영역에서 전면 금지한다**.

**REASON**: This is EXAM2 expression (exploration/discovery).

**EX3 ≠ EXAM2**:
- EXAM2 = 탐색 전용 (explores differences)
- EX3 = 보고서 전용 (confirms structure)

**FORBIDDEN IN EX3**:
- ❌ "{Insurer1}는 {structure1}이고, {Insurer2}는 {structure2}입니다"
- ❌ Any sentence pattern showing insurer-specific attributes
- ❌ Any comparison between insurers in bubble

---

### Rule 4: Bubble Purpose - Structure Declaration ONLY

EX3 요약 버블은:
- ❌ **테이블을 설명하지 않는다** (NO table explanation)
- ❌ **비교하지 않는다** (NO comparison)
- ❌ **판단하지 않는다** (NO judgment)
- ✅ **구조만 선언한다** (Structure declaration ONLY)

**Purpose Separation**:
- **LEFT bubble**: Confirms PRIMARY structure (AMOUNT or LIMIT)
- **RIGHT table**: Shows detailed value differences

**Bubble is NOT**:
- ❌ Summary of table contents
- ❌ Comparison between insurers
- ❌ Judgment of which is better
- ❌ Explanation of how coverage works

**Bubble IS**:
- ✅ Declaration of structural basis
- ✅ ONE sentence confirming AMOUNT or LIMIT structure

---

## Locked Output Templates

### AMOUNT-DRIVEN Coverage (LOCKED)

```
두 보험사는 모두 정액 지급 구조입니다.
```

**Applies to**:
- 암진단비
- 암진단비(유사암제외)
- 수술비
- Any coverage where PRIMARY definition = fixed amount

**Characteristics**:
- Exactly 19 characters (including spaces)
- ONE sentence (ONE period)
- NO insurer names
- NO elaboration

---

### LIMIT-DRIVEN Coverage (LOCKED)

```
두 보험사는 모두 한도 기준 구조입니다.
```

**Applies to**:
- 입원일당
- Any coverage where PRIMARY definition = limit/횟수/일수 제한

**Characteristics**:
- Exactly 19 characters (including spaces)
- ONE sentence (ONE period)
- NO insurer names
- NO elaboration

---

## Forbidden Patterns (BLACKLIST)

**Insurer Names**:
- ❌ 삼성, 삼성화재
- ❌ 메리츠, 메리츠화재
- ❌ KB, KB손해보험
- ❌ 한화, 한화손해보험
- ❌ 현대, 현대해상
- ❌ 롯데, 롯데손해보험
- ❌ DB, DB손해보험
- ❌ 흥국, 흥국화재

**Comparison Language**:
- ❌ "비교"
- ❌ "차이"
- ❌ "다릅니다"
- ❌ "는 A, 는 B"
- ❌ "즉,"

**Explanation Language**:
- ❌ "진단 또는 사고 발생 시"
- ❌ "약정된 금액을 지급하는 방식"
- ❌ "계약 시점에 명확히 정의됩니다"
- ❌ "지급 한도, 횟수, 또는 일수 제한이 적용되며"
- ❌ "보장 조건 해석이 중요합니다"

**Judgment Language**:
- ❌ "유리"
- ❌ "불리"
- ❌ "추천"
- ❌ "더 좋다"

---

## Implementation (LOCKED)

**File**: `apps/api/response_composers/ex3_compare_composer.py`

**Lines**: 760-768

```python
if primary_structure == "AMOUNT":
    # AMOUNT-DRIVEN coverage (FINAL LOCK)
    return "두 보험사는 모두 정액 지급 구조입니다."
elif primary_structure == "LIMIT":
    # LIMIT-DRIVEN coverage (FINAL LOCK)
    return "두 보험사는 모두 한도 기준 구조입니다."
else:
    # UNKNOWN (fallback to AMOUNT)
    return "두 보험사는 모두 정액 지급 구조입니다."
```

**Characteristics**:
- 3 return statements ONLY
- NO multi-line strings
- NO f-strings with insurer names
- NO conditional formatting
- LOCKED TEXT (cannot be modified)

---

## Verification Checklist

Before ANY change to `_build_bubble_markdown()`, verify:

1. ✅ Output is EXACTLY "두 보험사는 모두 정액 지급 구조입니다." OR "두 보험사는 모두 한도 기준 구조입니다."
2. ✅ NO insurer names in output (0% exposure)
3. ✅ NO comparison language (0% exposure)
4. ✅ NO explanation sentences (0% exposure)
5. ✅ Exactly ONE sentence (1 period)
6. ✅ NO additional elaboration
7. ✅ Complies with ALL 4 ABSOLUTE RULES

**If ANY check fails → OUTPUT IS A BUG**

---

## Priority Hierarchy

This FINAL LOCK rule has **HIGHEST PRIORITY** over:

1. ~~STEP NEXT-141~~ (superseded - was 4 lines with explanation)
2. ~~STEP NEXT-128~~ (superseded - was comparison format)
3. ~~STEP NEXT-126~~ (superseded - was 6 lines with insurer names)
4. Any UX preference
5. Any "readability" argument
6. Any "user might want to know..." argument

**Reason**: This is a constitutional rule, not a feature request.

---

## Enforcement

**Any output that violates these rules is considered a BUG.**

**Immediate action required**:
- Revert to locked template
- Do NOT elaborate
- Do NOT add explanation
- Do NOT show insurer differences

**This is NOT negotiable.**

---

## Definition of Success

> "EX3 bubble output = Exactly 19 characters, ONE sentence, NO insurer names, NO elaboration. 100% compliance."

---

**FINAL LOCK STATUS**: ✅ ENFORCED (2026-01-04)

**DEVIATION ALLOWED**: ❌ NONE
