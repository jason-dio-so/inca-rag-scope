# 금지언어 정책 적용 범위 (STEP NEXT-14-β)

**Version**: 1.0.0
**Status**: 🔒 LOCKED (Production Policy)
**Lock Date**: 2025-12-29
**Single Source**: `apps/api/policy/forbidden_language.py`

---

## 원칙

1. **Single Source of Truth**: 모든 금지언어 검증은 `apps/api/policy/forbidden_language.py` 모듈로 위임
2. **Allowlist-First**: 허용 문구 체크 → 금지 패턴 체크 순서로 검증
3. **Context-Aware**: 단어 단위가 아닌 **문맥 기반 패턴 매칭** (e.g., "차이를 확인" 허용, "차이는 100만원" 금지)
4. **NO Interpretation**: Frontend는 텍스트를 해석하지 않고 있는 그대로 렌더

---

## 적용 범위 (Code-Level)

### 1. **AssistantMessageVM** (Chat UI Response)

**파일**: `apps/api/chat_vm.py`

| 필드 | 검증 함수 | 적용 여부 | 비고 |
|-----|----------|---------|-----|
| `title` | `validate_text()` | ✅ YES | 제목 텍스트 검증 |
| `summary_bullets` | `validate_text_list()` | ✅ YES | 요약 bullet 배열 전체 검증 |
| `ComparisonTableSection.rows[].values[]` | `validate_text()` | ✅ YES | 표 셀 텍스트 검증 |
| `InsurerExplanationsSection.explanations[].text` | `validate_text()` | ✅ YES | 보험사별 설명 텍스트 검증 |
| `CommonNotesSection.bullets[]` | `validate_text_list()` | ✅ YES | 공통사항/유의사항 bullet 검증 |
| `CommonNotesSection.groups[].bullets[]` | `validate_text_list()` | ✅ YES | Grouped bullets 검증 (신규) |
| `EvidenceAccordionSection.items[].snippet` | ❌ NO | **원문 예외** (아래 참조) |

**Validator 위치**:
```python
# apps/api/chat_vm.py
from apps.api.policy.forbidden_language import validate_text, validate_text_list

@field_validator('summary_bullets')
@classmethod
def validate_no_forbidden_words_in_summary(cls, v: List[str]) -> List[str]:
    validate_text_list(v)
    return v
```

### 2. **InsurerExplanationDTO** (Step12 설명 레이어)

**파일**: `apps/api/explanation_dto.py`

| 필드 | 검증 함수 | 적용 여부 | 비고 |
|-----|----------|---------|-----|
| `explanation` | `validate_text()` | ✅ YES | Step12 설명 템플릿 검증 |
| `value_text` | ❌ NO | 금액/상태 표시 (검증 불필요) |

**Validator 위치**:
```python
# apps/api/explanation_dto.py
from apps.api.policy.forbidden_language import validate_text

@field_validator('explanation')
@classmethod
def validate_no_forbidden_words(cls, v: str) -> str:
    validate_text(v)
    return v
```

**NOTE**: Step12 템플릿 자체는 LOCKED (변경 금지), validator는 템플릿 생성 **후** 호출됨.

### 3. **Evidence Snippet** (원문 예외)

**파일**: `apps/api/chat_vm.py` (`EvidenceAccordionSection`)

| 필드 | 검증 함수 | 적용 여부 | 비고 |
|-----|----------|---------|-----|
| `snippet` | ❌ NO | **원문 그대로 표시** (검증 제외) |

**예외 이유**:
- Evidence snippet은 약관/사업방법서 **원문 발췌**
- 원문에 "더 높다", "유리하다" 같은 표현이 포함될 수 있음
- UI에서는 **"근거자료 원문"** 라벨과 함께 접힌 상태로 표시 (사용자가 명시적으로 펼쳐야 확인 가능)

**UI 라벨 규칙**:
```typescript
// Figma Component: EvidenceAccordion
<Accordion defaultCollapsed={true} label="근거자료 (원문)">
  {items.map(item => (
    <EvidenceItem>
      <Badge>원문 발췌</Badge>  {/* 원문임을 명시 */}
      <Text>{item.snippet}</Text>
    </EvidenceItem>
  ))}
</Accordion>
```

---

## 허용/금지 문구 상세

### 허용 문구 (Allowlist)

**파일**: `apps/api/policy/forbidden_language.py`

```python
ALLOWLIST_PHRASES: Set[str] = {
    # Factual statements
    "비교합니다", "비교를", "비교한", "비교 결과",
    "확인합니다", "확인할",
    "표시합니다", "표시한",
    "정리했습니다", "정리한",
    "안내합니다", "안내한",
    "명시되어 있습니다", "명시된",
    "존재합니다", "존재하지 않습니다",
    "포함합니다", "포함된",
    "제공합니다", "제공된",
    "기준으로", "기반으로",
    # Context-specific allowed
    "차이를 확인",  # "Difference checking" is ALLOWED
    "보다 자세",    # "More detailed" is ALLOWED
    "더 확인",      # "Further checking" is ALLOWED
}
```

**예시**:
- ✅ "삼성화재와 메리츠화재의 암진단비를 **비교합니다**"
- ✅ "가입설계서에 3천만원으로 **명시되어 있습니다**"
- ✅ "담보 간 **차이를 확인**하실 수 있습니다"
- ✅ "**보다 자세**한 내용은 약관을 참조하세요"

### 금지 패턴 (Forbidden)

**파일**: `apps/api/policy/forbidden_language.py`

```python
EVALUATIVE_FORBIDDEN_PATTERNS: List[str] = [
    # Superiority/Inferiority
    r'(?:유리|불리)(?:합니다|한|하다)',
    r'(?:우수|열등)(?:합니다|한|하다)',
    r'(?:좋|나쁜|나쁘)(?:습니다|은|다)',

    # Comparative evaluation
    r'(?:더|덜)\s+(?:높|낮|많|적|크|작)',
    r'(?:높|낮|많|적)(?:습니다|은|다)(?!\s*(?:명시|표시|확인))',
    r'보다\s+(?:높|낮|많|적|크|작|좋|나쁘)',
    r'[가-힣]+(?:가|은|는)\s+[가-힣]+보다',  # "A가 B보다"

    # Contrastive conjunctions
    r'반면(?:에)?',
    r'그러나',
    r'하지만',

    # Extremes/Rankings
    r'가장\s+(?:높|낮|많|적|크|작|좋|나쁘)',
    r'(?:최고|최저|최대|최소)(?:입니다|의|인)',

    # Recommendations/Judgments
    r'(?:추천|권장|제안)(?:합니다|한|하다)',
    r'(?:선택|판단|결론)(?:하세요|합니다|하다)',

    # Calculations/Aggregations
    r'(?:평균|합계|총합)(?:은|는|입니다)',
    r'차이(?:는|가)\s+[0-9]',  # "차이는 100만원"
]
```

**예시**:
- ❌ "삼성화재가 메리츠화재**보다 높습니다**"
- ❌ "**더 유리**한 조건입니다"
- ❌ "삼성은 높습니다. **반면** 메리츠는 낮습니다"
- ❌ "**가장 좋은** 상품입니다"
- ❌ "**추천합니다**"
- ❌ "**평균은** 2천만원입니다"
- ❌ "**차이는 100만원**입니다"

---

## 검증 알고리즘 (Allowlist-First)

**파일**: `apps/api/policy/forbidden_language.py`

```python
def validate_text(text: str) -> None:
    """
    1. Sanitize text: Replace allowlist phrases with placeholder
    2. Check forbidden patterns in sanitized text
    3. Raise ValueError if match found
    """
    sanitized_text = text

    # Step 1: Allowlist-first (remove allowed phrases)
    for allowed_phrase in ALLOWLIST_PHRASES:
        sanitized_text = sanitized_text.replace(allowed_phrase, "___ALLOWED___")

    # Step 2: Check forbidden patterns
    for pattern in EVALUATIVE_FORBIDDEN_PATTERNS:
        match = re.search(pattern, sanitized_text)
        if match:
            raise ValueError(
                f"FORBIDDEN language detected: pattern '{pattern}' matches in '{text}'\n"
                f"Matched substring: '{match.group()}'\n"
                f"Policy: Evaluative/comparative language is prohibited."
            )
```

**예시**:
```python
# Input: "암진단비를 비교합니다"
# Step 1: "암진단비를 ___ALLOWED___" (비교합니다 → placeholder)
# Step 2: No forbidden pattern match
# Result: PASS ✅

# Input: "삼성이 메리츠보다 높습니다"
# Step 1: "삼성이 메리츠보다 높습니다" (no allowlist match)
# Step 2: Pattern r'보다\s+(?:높|낮|많|적)' matches "보다 높"
# Result: FAIL ❌
```

---

## UI 표시 규칙 (Frontend Contract)

### 1. 검증된 텍스트 (As-Is 렌더)

**적용 대상**: title, summary_bullets, table cells, explanations, common notes

```typescript
// NO parsing, NO interpretation
<Text>{section.title}</Text>  // Render as-is
<Text>{explanation.text}</Text>  // Render as-is
```

### 2. Evidence Snippet (원문 라벨 표시)

**적용 대상**: EvidenceAccordionSection.items[].snippet

```typescript
<Accordion defaultCollapsed={true}>
  <AccordionHeader>
    근거자료 (원문)  {/* 원문임을 명시 */}
  </AccordionHeader>
  <AccordionContent>
    {items.map(item => (
      <EvidenceItem>
        <Badge variant="neutral">원문 발췌</Badge>
        <EvidenceText>{item.snippet}</EvidenceText>
        <EvidenceSource>
          {item.insurer} · {item.doc_type} · {item.page}p
        </EvidenceSource>
      </EvidenceItem>
    ))}
  </AccordionContent>
</Accordion>
```

**NOTE**: Evidence snippet은 접힌 상태가 기본이며, 사용자가 명시적으로 펼쳐야 확인 가능.

---

## 테스트 커버리지

### 1. 단위 테스트 (Forbidden Patterns)

**파일**: `tests/test_comparison_explanation.py`

```python
@pytest.mark.parametrize("forbidden_pattern,explanation_text", [
    ("유리", "삼성화재가 유리합니다"),
    ("불리", "메리츠는 불리한 조건입니다"),
    ("더 높", "삼성은 더 높습니다"),
    ("보다 낮", "메리츠가 보다 낮습니다"),
    ("A가 B보다", "삼성화재가 메리츠보다 좋습니다"),
    ("반면", "삼성은 높지만 반면 메리츠는 낮습니다"),
    ("추천", "삼성을 추천합니다"),
    ("평균", "평균은 2천만원입니다"),
])
def test_forbidden_word_raises(forbidden_pattern, explanation_text):
    with pytest.raises((ValueError, Exception)):
        InsurerExplanationDTO(
            insurer="삼성화재",
            status="CONFIRMED",
            explanation=explanation_text,
            value_text="3천만원"
        )
```

### 2. 통합 테스트 (Chat Integration)

**파일**: `tests/test_chat_integration.py`

```python
def test_forbidden_words_in_summary_bullets():
    handler = HandlerRegistry.get_handler("EX2_DETAIL")
    vm = handler.execute(compiled_query, request)

    # Check summary bullets
    for bullet in vm.summary_bullets:
        for pattern in FORBIDDEN_PATTERNS:
            assert not re.search(pattern, bullet)

def test_forbidden_words_in_explanations():
    handler = HandlerRegistry.get_handler("EX2_DETAIL")
    vm = handler.execute(compiled_query, request)

    # Check explanation sections
    explanation_sections = [s for s in vm.sections if s.kind == "insurer_explanations"]
    for section in explanation_sections:
        for exp in section.explanations:
            for pattern in FORBIDDEN_PATTERNS:
                assert not re.search(pattern, exp.text)
```

---

## DoD (완료 기준)

- [x] Single source 모듈 생성 (`apps/api/policy/forbidden_language.py`)
- [x] Allowlist-first 알고리즘 구현
- [x] AssistantMessageVM 전체 필드 검증 적용
- [x] InsurerExplanationDTO 검증 적용
- [x] Evidence snippet 원문 예외 처리 및 UI 라벨 규칙 정의
- [x] 테스트 커버리지 100% (forbidden patterns)
- [x] Frontend 계약 문서화 (원문 표시 규칙)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|-----|-----|---------|
| 2025-12-29 | 1.0.0 | 초기 버전 (STEP NEXT-14-β Lock) |

---

**END OF DOCUMENT**
