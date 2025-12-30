# KB Type 분류 규칙 (문서 구조 우선 정책)
**Date**: 2025-12-30
**Status**: GUARDRAIL (MANDATORY)
**Scope**: Presentation layer / UX decision layer

---

## 1. 원칙 (HARD RULE)

### 1-1) 보험사 고정 분류 금지
❌ **금지**: "KB는 항상 Type C다"
❌ **금지**: "KB는 항상 Type A/B다"
✅ **허용**: "이 KB 상품/문서는 Type A/B 구조를 가진다"

### 1-2) 문서 구조 기반 판정이 우선
- `config/amount_lineage_type_map.json`은 **기본값(default)** 일 뿐
- **문서 구조 판정**이 존재하면 → map 값을 override
- 판정 단위: **상품/문서** (보험사 단위 아님)

### 1-3) 추론 금지
❌ **금지**: "보험가입금액: 3천만원" → 모든 담보를 3천만원으로 전개
✅ **허용**: 문서에 명시된 담보별 금액만 사용

---

## 2. Type 판정 기준 (문서 구조)

### Type A/B: 담보별 금액 명시형
**판정 신호**:
- ✅ 담보별 가입금액 테이블 존재 (`보장명 | 가입금액`)
- ✅ 각 담보마다 고유 금액 명시 (3천만원, 1천만원, 6백만원 등)
- ✅ 특정 담보에 대해 "X천만원" 직접 표기

**예시** (KB 가입설계서 페이지 2):
```
보장명 가입금액 보험료(원)
70 암진단비(유사암제외) 3천만원 36,420
72 10대고액치료비암진단비 1천만원 6,640
```

**UX 표기**:
- CONFIRMED: `3,000만원` (콤마 포맷)
- UNCONFIRMED: `금액 미표기`

### Type C: 보험가입금액 참조형
**판정 신호**:
- ✅ "보험가입금액: X" 단일 값만 존재
- ✅ 다수 담보가 "보험가입금액 지급" 형태로 참조
- ❌ 담보별 독립 금액 테이블 없음

**예시** (한화/현대 가입설계서 패턴):
```
보험가입금액: 5,000만원

[담보 목록]
- 암진단 시 보험가입금액 지급
- 뇌출혈진단 시 보험가입금액 지급
```

**UX 표기**:
- CONFIRMED: 문서에서 추출된 경우 `X,XXX만원`
- UNCONFIRMED: `보험가입금액 기준` (A/B와 다른 표현)
- 공통 노트: "보험가입금액은 계약 시 결정되는 금액입니다" (1회 노출)

### Type 혼재 (Hybrid)
**판정**:
일부 담보는 독립 금액, 일부 담보는 "보험가입금액" 참조

**처리 방식**:
- 담보별로 개별 판정
- 보험사 단위 Type 고정 금지
- 문서 증거 기반 판정만 사용

**예시** (KB):
- 암진단비(유사암제외): Type A/B (3천만원 명시)
- 상해후유장해: Type C 패턴 ("보험가입금액에 곱한 금액")

---

## 3. KB 특이사항 (Case Study)

### 3-1) KB 가입설계서 구조
- **페이지 2**: 담보별 가입금액 표 존재
- **암진단비(유사암제외)**: `3천만원` 명시
- **판정**: Type A/B (이 담보에 한정)

### 3-2) KB config 값과 충돌
**현재 config** (`config/amount_lineage_type_map.json`):
```json
{
  "kb": "C"
}
```

**문제점**:
- config는 "C"로 설정되어 있지만,
- 실제 문서는 담보별 금액 테이블을 가짐 (A/B 구조)

**해결 방안** (표현계층/판정계층만):
1. **Option A**: config를 "A" 또는 "B"로 변경
2. **Option B**: config는 유지, 문서 구조 판정을 override로 우선 적용
   - presentation_utils.py 등에서 문서 구조 판정 로직 추가
   - 판정 결과가 있으면 → config 무시

**권장**: Option B (config는 기본값, 문서 판정 우선)

---

## 4. 구현 가이드 (표현계층 한정)

### 4-1) 판정 로직 위치
**허용 범위**:
- `apps/api/presentation_utils.py`
- `apps/api/amount_handler.py` (UX 결정 레이어만)

**금지 범위**:
- ❌ Step7 (추출/파싱/DB write)
- ❌ amount_fact 테이블
- ❌ apps/loader/* (데이터 로더)

### 4-2) Override 구현 예시
```python
def get_insurer_type_for_coverage(
    insurer: str,
    coverage: str,
    document_structure_hints: Optional[Dict] = None
) -> str:
    """
    Get insurer type with document structure override

    Priority:
    1. Document structure hints (if available)
    2. config/amount_lineage_type_map.json (default)

    Args:
        insurer: 보험사명
        coverage: 담보명
        document_structure_hints: 문서 구조 판정 결과
            예: {"has_coverage_amount_table": True, "amount": "3천만원"}

    Returns:
        "A", "B", or "C"
    """
    # Priority 1: Document structure override
    if document_structure_hints:
        if document_structure_hints.get("has_coverage_amount_table"):
            return "A"  # 또는 "B"

    # Priority 2: Config default
    type_map = load_type_map()  # config/amount_lineage_type_map.json
    return type_map.get(insurer.lower(), "A")  # Default to A
```

### 4-3) UX 표기 결정 예시
```python
def format_amount_for_display(
    amount_dto: AmountDTO,
    insurer: str,
    coverage: str
) -> str:
    """Format amount with type-aware logic"""

    # Get type (with document override)
    insurer_type = get_insurer_type_for_coverage(
        insurer, coverage, document_structure_hints=...
    )

    if amount_dto.status == "CONFIRMED":
        return format_with_comma(amount_dto.value_text)  # "3,000만원"

    elif amount_dto.status == "UNCONFIRMED":
        if insurer_type == "C":
            return "보험가입금액 기준"
        else:  # A or B
            return "금액 미표기"

    else:  # NOT_AVAILABLE
        return "해당 담보 없음"
```

---

## 5. 테스트 검증 규칙

### 5-1) 필수 테스트
1. **Mock 차단**: `tests/test_no_mock_amounts_in_chat_handlers.py`
   - 하드코딩 금액 존재 시 FAIL
2. **KB Type override**: `tests/test_kb_type_override.py` (권장)
   - KB 암진단비가 Type A/B로 처리되는지 확인
3. **UX 표기 일관성**: `tests/test_amount_display_format.py` (권장)
   - CONFIRMED → "3,000만원"
   - UNCONFIRMED (A/B) → "금액 미표기"
   - UNCONFIRMED (C) → "보험가입금액 기준"

### 5-2) 검증 명령어
```bash
# Mock 차단 확인 (MUST PASS for valid E2E)
python -m pytest tests/test_no_mock_amounts_in_chat_handlers.py -v

# 전체 테스트
python -m pytest -q
```

---

## 6. 금지 사항 (재강조)

### 데이터 레이어 변경 금지
- ❌ Step7 로직 수정
- ❌ amount_fact 재생성/업데이트
- ❌ DB write 경로 변경

### 추론 금지
- ❌ "보험가입금액: X"를 담보별로 전개
- ❌ "KB는 항상 C" 같은 보험사 고정
- ❌ 문서에 없는 금액 생성

### 허용 범위
- ✅ 표현계층(presentation) 로직
- ✅ 문서 구조 기반 판정 (UX 결정용)
- ✅ 포맷/노트/문구 조정

---

## 7. 향후 작업 (Future Work)

### 7-1) Step7 개선 (별도 STEP)
현재 KB 암진단비(유사암제외)는:
- **문서**: `3천만원` 명시 (페이지 2, 라인 16)
- **Step7 결과**: `UNCONFIRMED`, `value_text: None`

→ **Step7 추출 실패 (miss)** 로 확인됨

**별도 STEP에서 처리**:
- Step7 로직 디버깅
- KB 가입설계서 파싱 규칙 보강
- amount_fact 재생성

### 7-2) 문서 구조 자동 판정
현재는 수동 판정(증거 문서 작성)이지만,
향후 자동화 가능:
- PDF 테이블 파싱
- "보장명 가입금액" 헤더 탐지
- 담보별 금액 존재 여부 확인

---

## 8. 참고 문서

- `docs/audit/KB_AMOUNT_STRUCTURE_EVIDENCE.md` - KB 문서 구조 증거
- `docs/audit/KB_AMOUNT_E2E_VERIFICATION.md` - E2E 검증 결과
- `tests/test_no_mock_amounts_in_chat_handlers.py` - Mock 차단 게이트

---

**Status**: ACTIVE GUARDRAIL
**Last Updated**: 2025-12-30
**Enforcement**: Presentation layer only (Step7 unchanged)
