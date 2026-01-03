# STEP NEXT-110A — Product Header SSOT Lock (Without product_name)

**Date**: 2026-01-03
**Scope**: EX2_DETAIL response composition + Frontend rendering
**Status**: ✅ LOCKED

---

## Purpose

고객 데모에서 "이게 어떤 상품 기준이냐?"가 절대 나오지 않도록,
**모든 응답의 최상단에 상품 정체성 헤더**를 고정 표시한다.

---

## Evidence-Based Decisions

### Product_name 데이터 부재 증거

```bash
# grep search results (2026-01-03)
grep -r "product_name" → No files found
grep -r "proposal_facts" → No files found
grep -r "plan_name|상품명" → No files found
```

**결론**: `product_name` 데이터가 현재 시스템에 존재하지 않음이 증거 기반으로 확인됨.

**대응**: STEP NEXT-110A는 현재 가용한 SSOT만 사용 (보험사 + 담보명 + 기준).
Product_name은 STEP NEXT-110B (데이터 파이프라인 구축 후)로 분리.

---

## Header SSOT v1 (LOCKED)

```
**[보험사 표시명]**
**담보명**
_기준: 가입설계서_

---
```

### SSOT 우선순위

1. **보험사**: `format_insurer_name(insurer_code)`
   - samsung → 삼성화재
   - meritz → 메리츠화재
   - NO insurer code exposure

2. **담보명**: `display_coverage_name(coverage_name, coverage_code)`
   - Use coverage_name if available
   - Fallback to sanitized coverage_code
   - NO coverage_code pattern exposure (A[0-9]{4}_[0-9]+)

3. **기준**: 고정 문자열 ("가입설계서")
   - 현재는 모든 데이터가 proposal (가입설계서) 기준
   - 나중에 dynamic source 가능 (약관/사업방법서 등)

4. **상품명**: ❌ NOT IMPLEMENTED (데이터 없음)
   - Placeholder 사용 금지 (혼란 초래)
   - STEP NEXT-110B에서 추가 예정

---

## Constitutional Rules

### ✅ MUST

- Header MUST be at **top** of bubble_markdown
- Header MUST use **display names** (NOT codes)
- Header MUST come **BEFORE** all sections (---로 구분)
- coverage_code pattern **MUST NOT** appear in header
- Header structure MUST be **locked** (format/order)

### ❌ MUST NOT

- NO product_name guessing/assuming
- NO placeholder text (e.g., "상품명: (미확보)")
- NO LLM usage
- NO business logic change (판단/비교/추출 불변)

---

## Implementation

### Backend: EX2_DETAIL Composer

**File**: `apps/api/response_composers/ex2_detail_composer.py`

**Changes**:
```python
def _build_bubble_markdown(insurer_display, display_name, card_data):
    lines = []

    # STEP NEXT-110A: Product Header (fixed at top)
    lines.append(f"**[{insurer_display}]**")
    lines.append(f"**{display_name}**")
    lines.append("_기준: 가입설계서_\n")
    lines.append("---\n")  # Separator

    # Section 1: 보장 요약
    ...
```

**Header Position**: BEFORE "핵심 요약" section (이전에 "핵심 요약"에 있던 보험사/담보명 정보를 헤더로 분리)

---

### Frontend: ChatPanel Styling

**File**: `apps/web/components/ChatPanel.tsx`

**Changes**:
```tsx
<div className="prose prose-sm ...
  prose-strong:text-gray-900
  prose-strong:font-bold
  first:prose-strong:text-lg        // First <strong>: larger font
  first:prose-strong:block          // Block display
  prose-hr:my-3                      // Separator spacing
  prose-hr:border-gray-300">
  <ReactMarkdown>{msg.content}</ReactMarkdown>
</div>
```

**Visual Hierarchy**:
- **[보험사]**: Bold, Large (text-lg)
- **담보명**: Bold, Large
- _기준_: Italic, Normal size
- Horizontal rule (---): Visual separator

---

## Header Structure (LOCKED)

### Line-by-Line Format

```
Line 1: **[보험사 표시명]**
Line 2: **담보명**
Line 3: _기준: 가입설계서_
Line 4: (empty)
Line 5: ---
Line 6: (empty)
Line 7: ## 보장 요약
...
```

### Format Rules

1. **Line 1**: `**[{insurer_display}]**`
   - MUST start with `**[`
   - MUST end with `]**`
   - Insurer display name (e.g., "삼성화재")

2. **Line 2**: `**{display_name}**`
   - MUST start with `**`
   - MUST end with `**`
   - Coverage display name (e.g., "암진단비(유사암제외)")

3. **Line 3**: `_기준: {source}_`
   - MUST start with `_기준:`
   - MUST end with `_`
   - Currently always "가입설계서"

4. **Line 4**: Empty line

5. **Line 5**: `---` (horizontal rule)

6. **Line 6**: Empty line

7. **Line 7+**: Sections (## 보장 요약, ## 조건 요약, etc.)

---

## Testing

### Contract Tests

**File**: `tests/test_step_next_110a_product_header_contract.py`

**Coverage**:
1. ✅ Header exists at top
2. ✅ Header uses display names
3. ✅ NO coverage_code in header
4. ✅ Header structure locked
5. ✅ Regression: sections preserved

**All Tests**: 5/5 PASS

---

## Future Work: STEP NEXT-110B

When `product_name` data is available:

**Header SSOT v2** (future):
```
**[보험사] 상품명**
**담보명**
_기준: 가입설계서_

---
```

**SSOT Priority** (future):
1. proposal_facts.product_name
2. card_data.product_name
3. evidence_ref → doc_meta.product_name
4. Fallback: "(자료에서 미확보)"

**Validation** (future):
- NO coverage_code pattern in product_name
- NO insurer code only
- Length > 2
- NOT generic terms ("가입설계서" etc.)

---

## Definition of Done (STEP NEXT-110A)

✅ EX2_DETAIL 응답 최상단에 헤더 표시
✅ 헤더 구조 LOCKED (format + order)
✅ coverage_code UI 노출 0%
✅ Display names ONLY (NO codes)
✅ Contract tests 5/5 PASS
✅ Frontend markdown styling applied
✅ NO business logic change
✅ NO LLM usage
✅ Evidence-based (NO product_name guessing)

❌ Product_name NOT implemented (데이터 없음, STEP NEXT-110B로 연기)

---

**Constitutional Lock**: ✅ STEP NEXT-110A Complete
**Data Dependency**: product_name → STEP NEXT-110B
**Demo Impact**: 고객이 "보험사 + 담보명 + 기준"을 즉시 확인 가능
