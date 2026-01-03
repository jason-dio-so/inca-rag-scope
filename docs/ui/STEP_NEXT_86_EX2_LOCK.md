# STEP NEXT-86: EX2 고정 (담보 설명 전용 모드)

**목표**: EX2를 "담보 이해/설명 전용 모드"로 고정하여 EX3/EX4와 의미·UX·의사결정 경계를 명확히 분리

**날짜**: 2026-01-03
**상태**: SSOT (Single Source of Truth)

---

## 1. 문제 인식 (Why)

### 현재 EX2의 문제점
1. **역할 불명확**: 설명 + 비교 + 조건 + 암묵적 판단이 혼재
2. **coverage_code 노출 위험**: "A4200_1" 등 내부 코드가 사용자에게 노출될 수 있음
3. **bubble 부실**: 빈약하거나 EX3/EX4와 UX 레벨이 불일치
4. **사용자 혼란**: "이게 설명인지 비교인지" 의도가 불분명

**결과**: 사용자에게 명확한 가치 전달 실패

---

## 2. EX2의 헌법적 정의 (Constitutional Lock)

### EX2 = "단일 담보를 이해시키는 모드"

**허용**:
- ✅ 담보 개념 설명
- ✅ 보장 조건 안내
- ✅ 근거 자료 제공 (refs)
- ✅ KPI 요약 (한도, 지급유형, 조건)

**금지**:
- ❌ 보험사 간 비교
- ❌ 추천/판단
- ❌ 보험사 우열 표현
- ❌ coverage_code UI 노출
- ❌ raw_text 본문 노출

**원칙**:
> 비교·추천·판단은 EX3 / EX4 전용

---

## 3. Intent 분기 규칙 (Anti-Confusion Gates)

### Intent Router 규칙 (고정)

| 조건 | 라우팅 | 예시 |
|------|--------|------|
| `insurers = 1` | **EX2_DETAIL** | "삼성화재 암진단비 설명해줘" |
| `insurers ≥ 2` + "차이/비교/다른" | **EX2_LIMIT_FIND** | "A사 B사 보장한도 차이" |
| `insurers ≥ 2` + 종합비교 의도 | **EX3_COMPARE** | "삼성화재와 메리츠화재 암진단비 비교" |
| subtype 키워드 (제자리암 등) | **EX4_ELIGIBILITY** | "제자리암 보장 가능 여부" |

### 분기 우선순위
1. **Explicit kind** (request.kind) → 100% 우선
2. **insurers count** → EX2_DETAIL vs others 분기
3. **Anti-confusion gates** → EX2_LIMIT_FIND vs EX4_ELIGIBILITY
4. **Keyword patterns** → fallback

---

## 4. EX2_DETAIL 출력 구조 (SSOT)

### Message Meta
```python
{
    "kind": "EX2_DETAIL",
    "coverage_name": "암진단비(유사암 제외)",  # Display only
    "insurer": "삼성화재"
}
```

**절대 금지**: `coverage_code` (e.g., "A4200_1") 노출

---

### bubble_markdown (4-Section LOCKED)

#### ① 핵심 요약
```markdown
## 핵심 요약

- **보험사**: 삼성화재
- **담보명**: 암진단비(유사암 제외)
- **데이터 기준**: 가입설계서
```

#### ② 보장 요약 (KPI Summary)
```markdown
## 보장 요약

- **보장한도**: 3,000만원
- **지급유형**: 정액형 (진단 시 일시금)
- **근거**: [근거 보기](PD:samsung:A4200_1)
```

**표현 규칙**:
- 데이터 없음 → "표현 없음" (NOT "Unknown")
- 금액 포맷 → "3,000만원" (천 단위 쉼표)
- refs → `PD:` / `EV:` prefix 필수

#### ③ 조건 요약 (KPI Condition)
```markdown
## 조건 요약

- **감액**: 1년 미만 50% ([근거 보기](EV:samsung:A4200_1:02))
- **대기기간**: 90일 ([근거 보기](EV:samsung:A4200_1:03))
- **면책**: 계약일 이전 발생 질병 ([근거 보기](EV:samsung:A4200_1:04))
- **갱신**: 비갱신형
```

**표현 규칙**:
- Unknown 금지 → "근거 없음"으로 통일
- 조건별 refs 필수

#### ④ 근거 안내
```markdown
## 근거 자료

상세 근거는 "근거 보기" 링크를 클릭하시면 확인하실 수 있습니다.
```

**금지**:
- ❌ raw_text 본문 직접 노출
- ❌ coverage_code 문자열 노출

---

### sections (UI 렌더링)

#### Section 1: KPI 요약 카드
```python
{
    "kind": "common_notes",
    "title": "보장 요약",
    "bullets": [
        "보장한도: 3,000만원",
        "지급유형: 정액형",
        "근거: PD:samsung:A4200_1"
    ]
}
```

#### Section 2: 조건 카드
```python
{
    "kind": "common_notes",
    "title": "조건 요약",
    "bullets": [
        "감액: 1년 미만 50% (EV:samsung:A4200_1:02)",
        "대기기간: 90일 (EV:samsung:A4200_1:03)",
        "면책: 계약일 이전 발생 질병 (EV:samsung:A4200_1:04)",
        "갱신: 비갱신형"
    ]
}
```

#### Section 3: 근거 섹션 (lazy-load)
```python
{
    "kind": "evidence_accordion",
    "title": "근거 자료",
    "items": [
        {
            "evidence_ref_id": "PD:samsung:A4200_1",
            "insurer": "삼성화재",
            "coverage_name": "암진단비(유사암 제외)",
            "doc_type": "가입설계서",
            "page": 3,
            "snippet": "암 진단 시 3,000만원 지급..."  # Max 400 chars
        }
    ]
}
```

---

## 5. 기술 구현 지시

### Backend

#### 5.1 MessageKind 추가
**파일**: `apps/api/chat_vm.py`

```python
MessageKind = Literal[
    "EX2_DETAIL",           # NEW: 단일 담보 설명 (insurers=1)
    "EX2_DETAIL_DIFF",      # LEGACY
    "EX2_LIMIT_FIND",       # STEP NEXT-78: 한도/조건 차이
    "EX3_INTEGRATED",       # LEGACY
    "EX3_COMPARE",          # STEP NEXT-77
    "EX4_ELIGIBILITY",      # STEP NEXT-79
    "EX1_PREMIUM_DISABLED"
]
```

#### 5.2 Intent Router 수정
**파일**: `apps/api/chat_intent.py`

```python
@staticmethod
def route(request: ChatRequest) -> MessageKind:
    # Priority 1: Explicit kind
    if request.kind is not None:
        return request.kind

    # Priority 2: insurers count gate
    insurers = request.insurers or []
    if len(insurers) == 1:
        return "EX2_DETAIL"

    # Priority 3: detect_intent() (existing logic)
    kind, confidence = IntentRouter.detect_intent(request)
    return kind
```

#### 5.3 EX2DetailComposer 생성
**파일**: `apps/api/response_composers/ex2_detail_composer.py`

**요구사항**:
- Deterministic only (NO LLM)
- `display_coverage_name()` + `sanitize_no_coverage_code()` 강제 적용
- 4-section bubble_markdown 생성
- KPI Summary + Condition 포함
- refs 전용 (raw_text 금지)

#### 5.4 EX2DetailHandler 생성
**파일**: `apps/api/chat_handlers_deterministic.py`

**로직**:
1. Load slim card (single insurer)
2. Extract KPI summary + condition
3. Call EX2DetailComposer
4. Build AssistantMessageVM
5. Return response

---

### Frontend

#### 5.1 기존 카드 재사용
- **새 UI 금지**
- EX2 bubble은 읽기 전용 요약 영역
- 근거 클릭 시 lazy-load (기존 Evidence Accordion)

#### 5.2 렌더링 우선순위
1. `bubble_markdown` → 중앙 버블 (주요 표시)
2. `sections` → 하단 상세 (접기/펼치기)

---

## 6. 금지 사항 (Hard Stop)

### 절대 금지
1. ❌ **coverage_code UI 노출**: "A4200_1" 등 내부 코드
2. ❌ **"더 좋음 / 추천" 문구**: 판단 표현 금지
3. ❌ **보험사 간 상대 평가**: "A사가 B사보다" 등
4. ❌ **subtype 판단**: EX4 전용 영역 침범
5. ❌ **raw_text 본문 직접 노출**: refs 전용

### 허용
- ✅ 사실 기반 조건 나열
- ✅ KPI 요약 (한도, 유형, 조건)
- ✅ 근거 refs 제공
- ✅ "표현 없음" / "근거 없음" 표시

---

## 7. Definition of Done (DoD)

### 기능 요구사항
- [ ] EX2_DETAIL 요청 시 항상 bubble_markdown 4섹션 출력
- [ ] coverage_code UI 노출 0%
- [ ] raw_text 본문 노출 0%
- [ ] `insurers=1` → EX2_DETAIL 고정
- [ ] `insurers≥2` → EX2_LIMIT_FIND 또는 EX3_COMPARE 명확 분기

### 품질 요구사항
- [ ] EX3/EX4 UX 레벨과 시각적 밀도 정합
- [ ] Contract test 통과 (coverage_code scrub)
- [ ] Forbidden phrase validation 통과
- [ ] bubble_markdown 렌더링 테스트 통과

### 문서화 요구사항
- [ ] `docs/ui/STEP_NEXT_86_EX2_LOCK.md` (SSOT)
- [ ] `CLAUDE.md` 업데이트
- [ ] `STATUS.md` 업데이트

---

## 8. 산출물

### 문서
- `docs/ui/STEP_NEXT_86_EX2_LOCK.md` (이 문서 - SSOT)

### 코드
- `apps/api/chat_vm.py` (MessageKind 추가)
- `apps/api/chat_intent.py` (Intent Router 수정)
- `apps/api/response_composers/ex2_detail_composer.py` (NEW)
- `apps/api/chat_handlers_deterministic.py` (Handler 추가)

### 테스트
- `tests/test_ex2_bubble_contract.py` (NEW)

### 메타문서
- `CLAUDE.md` (STEP NEXT-86 규칙 추가)
- `STATUS.md` (진행 상황 기록)

---

## 9. 최종 한 줄 요약

> **EX2는 "설명", EX3는 "비교", EX4는 "판단" — 이 경계를 코드·UX·테스트로 완전히 고정한다.**

---

## 10. 예시 시나리오

### 시나리오 1: 단일 보험사 담보 설명
**입력**:
```json
{
    "message": "삼성화재 암진단비 설명해줘",
    "insurers": ["삼성화재"],
    "coverage_names": ["암진단비(유사암 제외)"]
}
```

**라우팅**: `EX2_DETAIL`

**출력 bubble_markdown**:
```markdown
## 핵심 요약
- **보험사**: 삼성화재
- **담보명**: 암진단비(유사암 제외)
- **데이터 기준**: 가입설계서

## 보장 요약
- **보장한도**: 3,000만원
- **지급유형**: 정액형
- **근거**: [근거 보기](PD:samsung:A4200_1)

## 조건 요약
- **감액**: 1년 미만 50% ([근거 보기](EV:samsung:A4200_1:02))
- **대기기간**: 90일
- **면책**: 계약일 이전 발생 질병
- **갱신**: 비갱신형

## 근거 자료
상세 근거는 "근거 보기" 링크를 클릭하시면 확인하실 수 있습니다.
```

---

### 시나리오 2: 보장한도 차이 비교 (EX2_LIMIT_FIND)
**입력**:
```json
{
    "message": "보장한도가 다른 상품 찾아줘",
    "insurers": ["삼성화재", "메리츠화재"],
    "coverage_names": ["암진단비(유사암 제외)"]
}
```

**라우팅**: `EX2_LIMIT_FIND` (NOT EX2_DETAIL)

**이유**: `insurers ≥ 2` + "다른" 키워드

---

### 시나리오 3: 종합 비교 (EX3_COMPARE)
**입력**:
```json
{
    "message": "삼성화재와 메리츠화재 암진단비 비교해줘",
    "insurers": ["삼성화재", "메리츠화재"],
    "coverage_names": ["암진단비(유사암 제외)"]
}
```

**라우팅**: `EX3_COMPARE` (NOT EX2_DETAIL)

**이유**: `insurers ≥ 2` + "비교" 키워드

---

## 11. 검증 체크리스트

### Intent Routing 검증
- [ ] `insurers=1` → EX2_DETAIL
- [ ] `insurers≥2` + "다른/차이" → EX2_LIMIT_FIND
- [ ] `insurers≥2` + "비교" → EX3_COMPARE
- [ ] subtype 키워드 → EX4_ELIGIBILITY

### Output 검증
- [ ] bubble_markdown 4섹션 완전 출력
- [ ] coverage_code 0% 노출
- [ ] raw_text 0% 노출
- [ ] refs 100% `PD:` / `EV:` prefix

### UX 검증
- [ ] EX3/EX4와 시각적 밀도 일치
- [ ] 근거 lazy-load 동작
- [ ] 읽기 전용 요약 영역 렌더링

---

**버전**: STEP NEXT-86
**작성일**: 2026-01-03
**작성자**: Claude Code
**상태**: LOCKED (SSOT)
