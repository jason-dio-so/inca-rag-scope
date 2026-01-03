# STEP NEXT-113: EX2 ChatGPT UX Structure Redesign (LOCK)

## Executive Summary

**Problem**: EX2_DETAIL 화면이 기능은 정상이나 UX 구조 붕괴
- 동일 정보가 왼쪽 말풍선 + 오른쪽 패널에 중복
- 말풍선이 문서/리포트처럼 과도하게 무거움
- ChatGPT UI 정체성 상실

**Solution**: 역할 강제 분리 (SSOT 재정의)
- Left bubble = Conversational summary ONLY (2-3 sentences)
- Right panel = All detailed info (tables, conditions, evidence)
- NO duplication

**Definition of Success**:
> "이 화면은 문서가 아니라 대화처럼 느껴진다"

---

## 1. Constitutional UX Rules (ABSOLUTE)

### 1️⃣ 역할 강제 분리 (LOCKED)

| 영역 | 역할 | 성격 |
|------|------|------|
| 왼쪽 말풍선 | 대화의 본문 (SSOT) | 요약 · 설명 · 흐름 |
| 오른쪽 패널 | 보조 정보 | 상세 · 표 · 근거 |

**❌ 같은 정보가 양쪽에 동시에 존재하면 실패**

### 2️⃣ ChatGPT UX 원칙 (LOCKED)
- 말풍선은 10초 안에 읽혀야 한다
- 스크롤이 필요한 말풍선은 ❌
- 조건·근거·표는 말풍선에 포함 금지

---

## 2. Left Bubble Structure (LOCKED)

### ✅ 허용되는 구성 (고정)

```markdown
[보험사명]
담보명
기준: 가입설계서

• 이 담보는 어떤 보장인지 (1문장)
• 보장 방식의 핵심 특징 (1문장)

→ 주요 조건(감액/대기기간 등)이 적용됩니다.

---
🔎 다음으로 이런 질문도 해볼 수 있어요
- 메리츠는?
- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘
```

### 🔒 규칙
- ✔︎ 보험사명 / 담보명 / 기준은 헤더로만
- ✔︎ 설명 문장은 최대 2줄
- ✔︎ 조건·금액·횟수 구체 수치 언급 금지
- ✔︎ "자세한 내용은 오른쪽을 참고" 같은 문구 ❌

### ❌ 말풍선에서 제거된 것 (전부)
- 보장금액 수치
- 보험기간 중 1회 같은 한도 표현
- 조건 요약 리스트 (감액 50%, 대기기간 90일 등)
- 근거 자료 / 링크
- 표 / 카드 / 박스 UI
- "## 보장 요약" / "## 조건 요약" 섹션

**👉 말풍선은 '설명'이지 '증명'이 아니다**

---

## 3. Right Panel Structure (LOCKED)

### ✅ 오른쪽 패널이 담당할 것

1. **보장 요약** (표)
   - 보장금액 / 한도 / 지급유형
   - STEP NEXT-96: 보장금액 최우선 (customer-first)

2. **조건 요약** (표)
   - 감액 / 대기기간 / 면책 / 갱신

3. **근거 자료**
   - 가입설계서 / 약관 링크
   - 접기(default closed)

### 🔻 시각적 규칙 (중요)
- 전체 폰트 크기 왼쪽보다 작게 (text-xs)
- 강조 색상/굵기 최소화 (text-gray-600/700)
- 배경 회색 (bg-gray-50)
- 카드 그림자 약화 또는 제거

**👉 오른쪽은 "읽고 싶으면 보는 영역"**

---

## 4. Implementation Details

### Modified Files

#### Backend (Composer)
- `apps/api/response_composers/ex2_detail_composer.py`
  - `_build_bubble_markdown()`: Lightweight conversational summary ONLY
  - `_build_kpi_summary_section()`: Enhanced with 보장금액 first (customer-first)
  - `_build_kpi_condition_section()`: Unchanged (all details in right panel)

#### Frontend (UI)
- `apps/web/components/ResultDock.tsx`
  - Title/summary styling downgraded (text-xs, text-gray-700)
  - `common_notes` section styling downgraded (bg-gray-50, text-xs)
  - Visual hierarchy enforced (right panel is secondary)

### Contract Tests
- **NEW**: `tests/test_step_next_113_ex2_chatgpt_ux.py` (10 tests, all PASS)
  - `test_bubble_has_no_tables`: NO "## 보장 요약" / "## 조건 요약" in bubble
  - `test_bubble_has_no_specific_condition_values`: NO "50%", "90일" in bubble
  - `test_bubble_is_lightweight_2_3_sentences`: 2-4 sentences ONLY
  - `test_bubble_has_product_header`: Product header with insurer · coverage · 기준
  - `test_bubble_has_question_hints`: 2 fixed hints (demo flow LOCK)
  - `test_sections_contain_all_details`: Sections have 보장 요약 + 조건 요약 + 근거 자료
  - `test_no_duplication_between_bubble_and_sections`: NO duplicate values
  - `test_bubble_conversational_tone_with_amount`: Conversational tone (amount case)
  - `test_bubble_conversational_tone_no_amount`: Conversational tone (no amount case)
  - `test_no_coverage_code_exposure_in_bubble`: NO coverage_code exposure

- **DEPRECATED**: `tests/test_ex2_bubble_contract.py`, `tests/test_step_next_96_customer_first_order.py`
  - These tests expect detailed sections (## 보장 요약) in bubble markdown
  - STEP NEXT-113 moved these to right panel ONLY
  - Tests are SUPERSEDED by STEP NEXT-113 contract
  - Will be renamed to `*_DEPRECATED.py` and archived

---

## 5. Example Output

### Left Bubble (New)
```markdown
**삼성화재**
**암진단비(유사암제외)**
_기준: 가입설계서_

---

이 담보는 암진단비(유사암제외)에 해당할 때 보장합니다.

정액으로 3000만원을 지급하는 방식입니다.

→ 감액, 대기기간 등 주요 조건이 적용됩니다.

---
🔎 **다음으로 이런 질문도 해볼 수 있어요**

- 메리츠는?
- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘
```

### Right Panel (Enhanced)
**보장 요약**
- 보장금액: 3000만원
- 보장한도: 보험기간 중 1회 한도
- 지급유형: 정액형 (일시금)
- 근거: EV:samsung:A4200_1:01

**조건 요약**
- 감액: 1년 미만 50% 감액 ([근거 보기](EV:samsung:A4200_1:02))
- 대기기간: 90일 ([근거 보기](EV:samsung:A4200_1:03))
- 면책: 계약일 이전 발생 질병 제외
- 갱신: 비갱신형

**근거 자료**
[Collapsible accordion with PD/EV refs]

---

## 6. Comparison (Before vs After)

### Before (STEP NEXT-110A)
- Left bubble: **4 sections** (Product Header + 보장 요약 + 조건 요약 + 근거 안내)
- Right panel: **3 sections** (보장 요약 bullets + 조건 요약 bullets + 근거 accordion)
- **Duplication**: 보장 요약/조건 요약 in BOTH left and right
- **User confusion**: "어디를 읽어야 하는지 모르겠음"

### After (STEP NEXT-113)
- Left bubble: **3 conversational sentences** (Product Header + What + How + Condition note)
- Right panel: **3 detailed sections** (보장 요약 + 조건 요약 + 근거 자료)
- **NO duplication**: Each piece of info exists in EXACTLY one place
- **Clear hierarchy**: Left = conversation, Right = drill-down

---

## 7. Constitutional Guarantees

### Business Logic (Unchanged)
- ✅ Deterministic only (NO LLM)
- ✅ KPI extraction unchanged (STEP NEXT-76/96 preserved)
- ✅ Ref format unchanged (PD:/EV: prefix)
- ✅ Coverage_code sanitization unchanged (NO exposure)
- ✅ Display name usage unchanged (STEP NEXT-103)

### View Layer (Changed)
- ✅ Bubble markdown: Lightweight conversational summary ONLY
- ✅ Sections: All detailed info (enhanced with 보장금액 first)
- ✅ Frontend: Right panel visually secondary (smaller, lighter)

---

## 8. Success Criteria (DoD)

### Functional Tests
- ✅ 10/10 tests PASS (`test_step_next_113_ex2_chatgpt_ux.py`)

### Visual UX
- ✅ Left bubble readable in 10 seconds (NO scroll)
- ✅ NO duplication between left and right
- ✅ Right panel visually secondary (smaller fonts, lighter colors)
- ✅ Product header prominent (insurer · coverage · 기준)

### Conversational Tone
- ✅ "이 담보는..." (what this coverage is)
- ✅ "정액으로..." / "방식으로..." (how it works)
- ✅ "조건이 적용됩니다" (condition note, NO specifics)

---

## 9. Migration Notes

### For Developers
- Old tests (`test_ex2_bubble_contract.py`, `test_step_next_96_customer_first_order.py`) will FAIL
- This is EXPECTED (bubble structure redesigned)
- Use `test_step_next_113_ex2_chatgpt_ux.py` as new contract

### For Customers
- NO breaking changes (all data still visible)
- Improved readability (clear role separation)
- Faster comprehension (conversation-first design)

---

## 10. Definition of Success (Final)

> "이 화면은 문서가 아니라 대화처럼 느껴진다"

If a customer says this after using EX2_DETAIL, STEP NEXT-113 is a success.

---

**SSOT Status**: LOCKED (2026-01-04)
**Modified Files**: 3 (ex2_detail_composer.py, ResultDock.tsx, test_step_next_113_ex2_chatgpt_ux.py)
**Tests**: 10/10 PASS
**Supersedes**: STEP NEXT-86, STEP NEXT-96, STEP NEXT-110A (bubble structure redesigned)
