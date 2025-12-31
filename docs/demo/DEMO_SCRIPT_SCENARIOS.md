# Demo Script & Scenarios
**STEP NEXT-38-E: Customer Demo Package**

**Duration**: 10-15 minutes
**Audience**: Prospective customers / stakeholders
**Environment**: Mock API + UI Prototype (localhost)

---

## Demo Principles (Constitutional Rules)

**MUST FOLLOW**:
1. **No recommendations**: We compare, we do not recommend
2. **Evidence-based**: Every claim must reference source document
3. **Scope-limited**: Only mapped coverages (no fuzzy matching, no guessing)
4. **Read-only**: No calculations, no simulations, no LLM generation

**PROHIBITED**:
- "We recommend..."
- "This is better..."
- "You should choose..."
- Any suggestion of financial advice

---

## Scenario A: Product Summary (Example 3)
**Intent**: PRODUCT_SUMMARY
**Demo fixture**: example3_product_summary.json
**Duration**: 4-5 minutes

### Customer Question (Natural Language)
> "삼성화재 New 원더풀 암보험과 한화생명 암보험의 주요 보장 내용을 비교해주세요."

### UI Flow

#### Block 1: Meta
- Query ID: Auto-generated UUID
- Intent: PRODUCT_SUMMARY
- Timestamp: Current time

**Demo Point**: "시스템은 모든 조회에 고유 ID를 부여하여 추적 가능성을 보장합니다."

#### Block 2: Query Summary
- Targets: 삼성화재 / 한화생명
- Coverage scope: 9개 핵심 보장 (Canonical set: EXAMPLE3_CORE_9)
- Premium notice: false

**Demo Point**: "비교 대상 상품과 범위를 명시적으로 확인합니다. 보험료 계산은 포함되지 않습니다."

#### Block 3: Comparison Table
9개 담보 비교 (Coverage Code 기준):
- A4200_1: 암 진단비 (삼성 3,000만원 vs 한화 5,000만원)
- A4210: 유사암 진단비 (삼성 차등 vs 한화 통합 500만원)
- A5200: 암 수술비 (삼성 200만원 vs 한화 150만원)
- A5100: 질병 수술비 (수술 종류별 차등)
- A6100_1: 질병 입원일당 (삼성 5만원 vs 한화 3만원)
- A6300_1: 암 직접치료 입원일당 (삼성 10만원 vs 한화 7만원)
- A9617_1: 항암방사선약물치료비
- A9640_1: 항암약물허가치료비
- A4102: 뇌출혈 진단비

**Evidence for each row**:
- Status: found / not_found / not_applicable
- Source: "가입설계서 p.X, 약관 p.Y"
- Snippet: 원문 발췌

**Demo Point**: "모든 수치는 약관 및 가입설계서 원문에서 직접 추출되었으며, 출처와 페이지를 명시합니다. 클릭 시 원문을 확인할 수 있습니다(향후 기능)."

#### Block 4: Notes
7개 주제별 요약:
- 암 진단비 차이
- 유사암 지급 방식 차이 (차등 vs 통합)
- 입원일당 비교
- 수술비 범위
- 항암치료비
- 뇌출혈 진단비
- 보장 조건 확인 필요성

**Demo Point**: "주제별로 정리된 비교 사항입니다. 해석이나 추천이 아닌, 사실 정리입니다."

#### Block 5: Limitations
- 약관 기반 정보 제공
- 세부 조건은 약관 직접 확인 필요
- 보험료 계산 미포함
- 특약 구성에 따라 달라질 수 있음

**Demo Point**: "우리는 근거 없는 주장을 하지 않습니다. 확인 불가능한 사항은 명시적으로 한계를 설명합니다."

### Expected Questions & Answers

**Q1**: "그럼 어느 상품이 더 좋은가요?"
**A**: "우리는 추천하지 않습니다. 두 상품의 보장 내용과 금액 차이를 근거 문서 기반으로 정리해드렸습니다. 선택은 고객님의 상황과 우선순위에 따라 결정하셔야 합니다."

**Q2**: "이 금액이 정확한가요?"
**A**: "모든 금액은 약관 및 가입설계서 원문에서 직접 추출했으며, 출처 페이지를 함께 표시했습니다. 클릭하시면 원문을 확인하실 수 있습니다."

**Q3**: "다른 담보도 비교할 수 있나요?"
**A**: "네, 하지만 담보명 매핑 데이터에 존재하는 보장만 처리 가능합니다. 매핑되지 않은 담보는 '확인 불가'로 표시됩니다. 이는 잘못된 매칭을 방지하기 위한 정책입니다."

---

## Scenario B: Coverage Condition Diff (Example 2)
**Intent**: COVERAGE_CONDITION_DIFF
**Demo fixture**: example2_coverage_compare.json
**Duration**: 3-4 minutes

### Customer Question
> "암 진단비의 면책사항과 지급 요건이 두 상품 간 어떻게 다른가요?"

### UI Flow

#### Block 2: Query Summary
- Intent: COVERAGE_CONDITION_DIFF (조건/면책 비교에 특화)
- Target coverage: A4200_1 (암 진단비)

#### Block 3: Comparison - Condition Focus
Structured diff showing:
- **지급요건** (Payment conditions)
- **면책사항** (Exclusions)
- **대기기간** (Waiting period)
- **감액기간** (Reduction period)

**Demo Point**: "동일 담보라도 지급 조건, 면책사항, 대기기간이 다릅니다. 이를 조건별로 구조화하여 비교합니다."

#### Block 4: Notes
- 대기기간: 삼성 90일 vs 한화 90일 (동일)
- 면책: 두 상품 모두 '고의적 사고' 면책
- 지급요건: 병리조직검사 기준 차이

**Demo Point**: "조건이 동일해 보여도 세부 기준이 다를 수 있습니다. 약관 원문 확인이 필수입니다."

### Expected Questions

**Q1**: "대기기간이 짧은 상품을 추천해주세요."
**A**: "추천은 하지 않습니다. 두 상품의 대기기간 정보를 비교해드렸으니, 고객님의 상황에 맞춰 판단하시기 바랍니다."

**Q2**: "면책사항 전체를 보여줄 수 있나요?"
**A**: "현재 화면에는 주요 면책사항만 표시됩니다. 전체 목록은 약관 원문을 확인하시기 바랍니다."

**Q3**: "이 차이가 중요한가요?"
**A**: "우리는 차이가 '중요한지'를 판단하지 않습니다. 차이가 '무엇인지'를 근거와 함께 보여드립니다."

---

## Scenario C: O/X Availability (Example 4)
**Intent**: COVERAGE_AVAILABILITY
**Demo fixture**: example4_ox.json
**Duration**: 2-3 minutes

### Customer Question
> "제자리암과 경계성종양이 보장되는지 확인해주세요."

### UI Flow

#### Block 3: O/X Table
Simple Yes/No table:
- 제자리암 보장: 삼성 O / 한화 O
- 제자리암 보장 금액: 삼성 200만원 / 한화 유사암 통합 500만원
- 경계성종양 보장: 삼성 O / 한화 X

**Evidence**:
- Each O/X backed by document reference
- X (not available) also requires evidence: "약관 전문 검토 결과 해당 담보 없음"

**Demo Point**: "O/X 판단도 근거 문서가 필요합니다. 'X'도 '약관을 검토한 결과 없음'이라는 증거가 있습니다."

### Expected Questions

**Q1**: "왜 한화는 경계성종양이 없나요?"
**A**: "약관 검토 결과 해당 보장이 명시되지 않았습니다. 정확한 이유는 보험사에 문의하셔야 합니다."

**Q2**: "그럼 삼성이 더 낫네요?"
**A**: "우리는 '더 낫다'는 판단을 하지 않습니다. 보장 유무와 금액을 비교해드렸으니, 고객님의 필요에 맞춰 선택하시기 바랍니다."

**Q3**: "다른 보험사도 확인할 수 있나요?"
**A**: "매핑 데이터에 포함된 보험사만 조회 가능합니다. 현재는 5개 보험사(삼성, 한화, KB, 메리츠, 현대해상)를 지원합니다."

---

## Scenario D: Premium Reference (Example 1) - Warning Demo
**Intent**: PREMIUM_REFERENCE
**Demo fixture**: example1_premium.json
**Duration**: 1-2 minutes (Warning showcase)

### Customer Question
> "보험료를 비교해주세요."

### UI Flow

#### Block 2: Query Summary
- Intent: PREMIUM_REFERENCE
- **premium_notice**: true (WARNING FLAG)

#### Block 3: Comparison
Shows reference premiums from proposals (if available):
- Source: 가입설계서 표지
- Conditions: 특정 연령/성별/특약 기준
- **WARNING BANNER**: "이 보험료는 가입설계서 기준이며, 개인 조건에 따라 달라집니다. 정확한 보험료는 보험사 설계를 받으셔야 합니다."

**Demo Point**: "보험료는 '비교'가 아닌 '참고'만 가능합니다. 우리는 계산하지 않으며, 가입설계서에 명시된 값을 그대로 전달합니다."

#### Block 5: Limitations
- 보험료 계산 기능 없음
- 가입설계서 기준값 표시만 가능
- 개인 조건에 따라 실제 보험료 상이
- 정확한 산출은 보험사 상담 필수

### Expected Question

**Q1**: "내 나이/성별로 보험료를 계산해주세요."
**A**: "죄송합니다. 우리는 보험료를 계산하지 않습니다. 보험사에 직접 설계를 요청하시기 바랍니다. 우리는 가입설계서에 명시된 참고 값만 표시합니다."

---

## General Demo Tips

### Opening (30 seconds)
"이 시스템은 보험 상품을 **비교**합니다. **추천하지 않습니다**. 모든 정보는 약관과 가입설계서 원문에 근거하며, 근거가 없으면 '확인 불가'로 표시합니다."

### Transition Between Scenarios (15 seconds each)
"다음 시나리오로 넘어가겠습니다. [시나리오명]을 보여드리겠습니다."

### Closing (1 minute)
"우리의 원칙을 다시 강조하겠습니다:
1. **추천 금지**: 우리는 비교만 합니다
2. **근거 기반**: 모든 정보는 출처가 명시됩니다
3. **범위 제한**: 매핑된 담보만 처리합니다
4. **읽기 전용**: 계산, 예측, 생성을 하지 않습니다

질문 있으시면 받겠습니다."

---

## Troubleshooting During Demo

### If API fails to respond
"Mock API가 응답하지 않네요. 잠시만 기다려주세요."
→ Check http://127.0.0.1:8001/health
→ Restart if needed

### If UI doesn't load
"UI가 로드되지 않네요. 새로고침하겠습니다."
→ Check http://127.0.0.1:8000
→ Clear browser cache if needed

### If customer asks out-of-scope question
"좋은 질문이지만, 그 부분은 현재 시스템 범위에 포함되지 않습니다. [이유 설명]. 향후 확장 시 검토하겠습니다."

---

**Last Updated**: 2025-12-31 (STEP NEXT-38-E)
**Status**: Ready for customer demo
**Environment**: Mock-only (no DB, no real API)
