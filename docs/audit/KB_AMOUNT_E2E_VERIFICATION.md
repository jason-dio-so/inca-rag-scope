# KB 금액 E2E 검증 결과
**Date**: 2025-12-30
**Coverage**: 암진단비(유사암제외)
**Status**: ⚠️  INVALID (Mock data detected)

---

## 1. 검증 요약

**결론**: 현재 E2E 테스트 결과는 **무효(INVALID)** 입니다.

**이유**:
- `apps/api/chat_handlers.py:189`에 하드코딩된 Mock 데이터 사용
- 실제 AmountRepository/Step11 integration 없음
- 표시되는 금액("1천만원")은 Mock, 실제 데이터 아님

**증거**:
```python
# apps/api/chat_handlers.py:189
cells.append(TableCell(
    text="1천만원",  # Mock
    meta=CellMeta(status="CONFIRMED")
))
```

---

## 2. 시나리오 실행 결과 (Current State)

### S1: KB 단독
| 항목 | 값 | 비고 |
|------|-----|------|
| Insurer | KB손해보험 | |
| Coverage | 암진단비(유사암제외) | |
| **Displayed Value** | **1천만원** | ⚠️  Mock (handler hardcoded) |
| **Status** | **CONFIRMED** | ⚠️  Mock (handler hardcoded) |
| Evidence | N/A | Mock이므로 무의미 |

**문제점**:
- 표시값 "1천만원"은 handler에 하드코딩된 Mock
- 실제 데이터 레이어는 UNCONFIRMED (아래 참조)

### S2: KB vs 삼성
| Insurer | Displayed Value | Status | 비고 |
|---------|----------------|--------|------|
| KB손해보험 | 1천만원 | CONFIRMED | ⚠️  Mock |
| 삼성화재 | 1천만원 | CONFIRMED | ⚠️  Mock |

**문제점**:
- 양쪽 모두 동일한 Mock 값("1천만원") 표시
- Type C vs Type A/B 차이를 검증할 수 없음
- 실제 금액 차이(KB 3천만원 vs 삼성 X만원)가 반영 안됨

### S3: KB vs 한화
| Insurer | Displayed Value | Status | 비고 |
|---------|----------------|--------|------|
| KB손해보험 | 1천만원 | CONFIRMED | ⚠️  Mock |
| 한화손해보험 | 1천만원 | CONFIRMED | ⚠️  Mock |

**문제점**:
- Type C + UNCONFIRMED 시나리오 검증 불가
- "보험가입금액 기준" 표시 로직 검증 불가
- 공통 노트 1회 노출 검증 불가

---

## 3. 데이터 레이어 실제 상태

### KB coverage_cards.jsonl (Step7 결과)
```json
{
  "coverage_name_canonical": "암진단비(유사암제외)",
  "amount": {
    "status": "UNCONFIRMED",
    "value_text": null,
    "source_doc_type": null,
    "evidence_ref": null
  }
}
```

### 대조: KB 가입설계서 원문 (페이지 2)
```
보장명 가입금액 보험료(원)
70 암진단비(유사암제외) 3천만원 36,420
```

**불일치 분석**:
| 항목 | 문서 원문 | Step7 결과 | 판정 |
|------|----------|-----------|------|
| 금액 존재 | ✅  3천만원 명시 | ❌ None | **Step7 Miss** |
| Status | 명시 → CONFIRMED | UNCONFIRMED | **추출 실패** |
| Source | 가입설계서 p.2 | null | **참조 누락** |

---

## 4. 문제 진단

### 4-1) Handler Mock Data (BLOCKER)
**위치**: `apps/api/chat_handlers.py:185-191`

```python
for ins in insurers:
    # Mock data (in production, query from Step11)
    if item == "보장한도":
        cells.append(TableCell(
            text="1천만원",  # Mock
            meta=CellMeta(status="CONFIRMED")
        ))
```

**영향**:
- ✅ `tests/test_no_mock_amounts_in_chat_handlers.py` → **FAIL** (정상)
- ❌ 모든 E2E 테스트 결과 무효
- ❌ Type C UX 로직 검증 불가
- ❌ KB regression 검증 불가

**조치 필요**:
1. Mock 제거 또는
2. AmountRepository integration 완료 후 재검증

### 4-2) Step7 Extraction Miss
**증거**:
- 문서: `70 암진단비(유사암제외) 3천만원`
- Step7 결과: `status: UNCONFIRMED, value_text: null`

**영향**:
- 데이터 레이어가 문서 사실과 불일치
- Handler가 실제 데이터를 사용해도 "금액 미표기" 표시됨
- KB Type A/B 판정에도 불구하고 금액 표시 안됨

**조치 필요** (별도 STEP):
- Step7 로직 디버깅
- KB 가입설계서 파싱 규칙 점검
- amount_fact 재생성

### 4-3) Type 분류 충돌
**Config**: `config/amount_lineage_type_map.json` → `"kb": "C"`
**문서 구조**: Type A/B (담보별 금액 표 존재)

**영향**:
- Type C 로직이 KB에 적용될 가능성
- "보험가입금액 기준" 표시 오류 위험
- UX 오염

**조치 완료** (이번 STEP):
- ✅ `docs/guardrails/KB_TYPE_CLASSIFICATION_RULE.md` 작성
- ✅ 문서 구조 우선 정책 수립
- ⏳ 구현 대기 (표현계층에서 override)

---

## 5. 향후 검증 계획

### Phase 1: Mock 제거 (BLOCKER 해제)
- [ ] Handler에서 Mock 데이터 제거
- [ ] AmountRepository integration
- [ ] `tests/test_no_mock_amounts_in_chat_handlers.py` → **PASS**

### Phase 2: Step7 수정 (별도 STEP)
- [ ] KB 가입설계서 파싱 디버깅
- [ ] "3천만원" 추출 로직 수정
- [ ] amount_fact 재생성
- [ ] coverage_cards.jsonl 업데이트

### Phase 3: E2E 재검증
**S1: KB 단독** (예상):
- Status: CONFIRMED
- Value: "3,000만원" (콤마 포맷)
- Evidence: 가입설계서 p.2

**S2: KB vs 삼성** (예상):
- KB: "3,000만원" (CONFIRMED, Type A/B)
- 삼성: "X,XXX만원" (CONFIRMED, Type A)
- 차이: 금액 값 차이만, 표기 방식 동일

**S3: KB vs 한화** (예상):
- KB: "3,000만원" (CONFIRMED, Type A/B override)
- 한화: "보험가입금액 기준" (UNCONFIRMED, Type C)
- 차이: Type 차이로 인한 표기 방식 차이
- 공통 노트: "보험가입금액은..." (1회 노출)

---

## 6. 검증 재현 명령어

### 6-1) 현재 상태 확인
```bash
# Mock 차단 테스트 (현재 FAIL 예상)
python -m pytest tests/test_no_mock_amounts_in_chat_handlers.py -v

# E2E 시나리오 (Mock 데이터 출력 예상)
python -c "
from apps.api.chat_vm import ChatRequest
from apps.api.chat_intent import IntentDispatcher

req = ChatRequest(
    message='KB 암진단비',
    kind='EX2_DETAIL',
    coverage_names=['암진단비(유사암제외)'],
    insurers=['KB손해보험']
)
resp = IntentDispatcher.dispatch(req)
# ... (결과 확인)
"

# 데이터 레이어 확인
python -c "
import json
with open('data/compare/kb_coverage_cards.jsonl', 'r') as f:
    for line in f:
        card = json.loads(line)
        if '암진단비' in card.get('coverage_name_canonical', ''):
            print(card.get('amount'))
            break
"
```

### 6-2) Mock 제거 후 재검증 (Phase 1 완료 후)
```bash
# Mock 차단 테스트 → PASS 예상
python -m pytest tests/test_no_mock_amounts_in_chat_handlers.py -v

# E2E 재실행 (실제 데이터 반영 예상)
# (단, Step7 miss로 인해 여전히 UNCONFIRMED 가능)
```

### 6-3) Step7 수정 후 최종 검증 (Phase 2 완료 후)
```bash
# 데이터 레이어 확인 → CONFIRMED 예상
# E2E 재실행 → "3,000만원" 표시 예상
```

---

## 7. 결론

### 현재 상태 (2025-12-30)
- ❌ **E2E 결과 무효** (Mock data)
- ❌ **Step7 추출 실패** (3천만원 miss)
- ⚠️  **Type 분류 충돌** (config=C, 문서=A/B)

### 완료된 작업
- ✅ KB 문서 구조 증거 확보
- ✅ Mock 차단 테스트 추가
- ✅ Type 분류 guardrail 수립

### 대기 중 작업
- ⏳ Handler Mock 제거 (표현계층)
- ⏳ Step7 수정 (별도 STEP)
- ⏳ E2E 재검증

### 검증 가능 시점
**Phase 1 완료 시**: Mock 제거 → UX 로직 검증 가능
**Phase 2 완료 시**: Step7 수정 → 종단간 정합성 검증 가능

---

**Status**: DOCUMENTED (Invalid due to mock data)
**Next Action**: Remove mock data or integrate AmountRepository
**Blocker Test**: `tests/test_no_mock_amounts_in_chat_handlers.py` must PASS
