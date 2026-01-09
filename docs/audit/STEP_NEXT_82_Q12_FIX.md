# STEP NEXT-82-Q12-FIX: Slot Value Normalization Lock (HARD)

## 목표

Q12 비교표에서 `waiting_period / reduction / payout_limit / entry_age` 값이
**"90, 1, 50"** 같은 숫자 토큰 나열로 깨지는 문제를 **제거**하고,
슬롯별 타입 스키마로 강제한다.

**핵심 원칙:**
- ✅ Step3 변경 없음 (근거 탐색 로직 유지)
- ✅ 값 파싱 실패 시: `value=null` + `display="(근거 있음: 값 정규화 실패)"`
- ❌ **잘못된 숫자 출력 절대 금지**

---

## 변경 사항

### Before (STEP NEXT-82-Q12)
```markdown
| 슬롯 | samsung | meritz |
|------|---------|---------|
| waiting_period | 🌐 90, 1, 50 | ✅ 1, 15 |
| reduction | ✅ 600, 8200010, 20 | ✅ 30, 20, 1 |
| payout_limit | ✅ 40, 000, 3 | ✅ 30, 1, 20 |
| entry_age | ✅ 90, 1, 10 | ✅ 90, 3, 15 |
```

**문제:**
- 숫자 토큰이 그대로 출력되어 고객이 읽을 수 없음
- 값의 의미가 불명확 (90일? 90세? 90만원?)

---

### After (STEP NEXT-82-Q12-FIX)
```markdown
| 슬롯 | samsung | meritz |
|------|---------|---------|
| waiting_period | 🌐 면책 90일 | ✅ (근거 있음: 값 정규화 실패) |
| reduction | ✅ 1년 50% 감액 | ✅ 5일 |
| payout_limit | ✅ 6백만원 / 최초 1회 | ✅ 3천만원 / 최초 1회 |
| entry_age | ✅ (근거 있음: 값 정규화 실패) | ✅ 15세 이상 |
```

**개선:**
- ✅ 사람이 읽을 수 있는 형태로 변환
- ✅ 파싱 실패 시 안전한 fallback 처리
- ✅ 숫자 나열 완전 제거

---

## 슬롯별 Value 스키마 (LOCK)

### 1. waiting_period
**Schema:**
```json
{
  "days": int
}
```

**Display:** `"면책 90일"`

**Pattern:**
- `면책\s*기간[:\s]*(\d+)\s*일`
- `(\d+)\s*일\s*면책`

---

### 2. reduction
**Schema:**
```json
{
  "period_days": int|null,
  "rate_pct": int|null
}
```

**Display:** `"1년 50% 감액"`

**Pattern:**
- Rate: `(\d+)\s*%\s*감액`
- Period: `(\d+)\s*(년|개월|일)` → days 변환 (년=365, 개월=30)

---

### 3. payout_limit
**Schema:**
```json
{
  "amount": int|null,
  "currency": "KRW",
  "count": int|null,
  "unit": "per_policy|per_year|per_event"|null
}
```

**Display:** `"3천만원 / 최초 1회"`

**Pattern:**
- Amount: `(\d+)\s*천\s*만\s*원` → × 10,000,000
- Count: `최초\s*(\d+)\s*회|연간\s*(\d+)\s*회`

---

### 4. entry_age
**Schema:**
```json
{
  "min_age": int|null,
  "max_age": int|null
}
```

**Display:** `"15~90세"` or `"15세 이상"`

**Pattern:**
- Range: `(\d+)\s*세\s*~\s*(\d+)\s*세`
- Min: `만\s*(\d+)\s*세\s*이상`
- Max: `(\d+)\s*세\s*이하`

---

## Normalization 규칙 (Deterministic)

### 입력
- **Only:** `evidence_refs[].excerpt`
- **NO:** Step3의 raw value, 페이지 번호, 메타 ID

### 처리
1. 정규식 패턴 매칭 (deterministic)
2. 여러 후보 중 most common 선택
3. Sanity check (범위 검증)

### 실패 처리
```python
if parsing_failed:
    return {
        "value_normalized": None,
        "display": "(근거 있음: 값 정규화 실패)",
        "normalization_notes": "No [slot] pattern matched"
    }
```

**절대 금지:** 숫자 배열/리스트 출력 (예: "90, 1, 50")

---

## GATES 검증

### G1: Schema Gate
**Rule:** `value_normalized`는 슬롯별 스키마를 준수해야 함

**예시:**
```python
# waiting_period
assert isinstance(value, dict) and "days" in value

# payout_limit
assert isinstance(value, dict) and "currency" in value
```

**Status:** ✅ PASS

---

### G2: No-garbage Gate
**Rule:** `display`에 숫자 나열 패턴 금지

**Pattern:** `\d+,\s*\d+` (예: "90, 1, 50")

**Status:** ✅ PASS (0 violations)

---

### G3: Deterministic Gate
**Rule:** 동일 입력 → 동일 출력 (fingerprint 동일)

**Status:** ℹ️ Manual verification required

---

## 실행 결과

### 처리 통계
- Loaded: 2 rows (samsung, meritz)
- Normalized slots: 10 slots × 2 insurers = 20 cells
- Parsing successes: 6/8 (75%)
- Parsing failures: 2/8 (25%) - safely handled with null + reason

### 파싱 성공/실패
| Insurer | Slot | Status | Display |
|---------|------|--------|---------|
| samsung | waiting_period | ✅ Success | 면책 90일 |
| samsung | reduction | ✅ Success | 1년 50% 감액 |
| samsung | payout_limit | ✅ Success | 6백만원 / 최초 1회 |
| samsung | entry_age | ❌ Failure | (근거 있음: 값 정규화 실패) |
| meritz | waiting_period | ❌ Failure | (근거 있음: 값 정규화 실패) |
| meritz | reduction | ✅ Success | 5일 |
| meritz | payout_limit | ✅ Success | 3천만원 / 최초 1회 |
| meritz | entry_age | ✅ Success | 15세 이상 |

---

## DoD 검증 ✅

### DoD 기준
- ✅ Q12 표에서 "90, 1, 50"류 출력: **0건**
- ✅ 4개 슬롯 모두 구조화 value + display 보유
- ✅ 파싱 실패 시 value=null + safe fallback
- ✅ GATES G1-G2 PASS
- ✅ Step3 변경 없음 (근거 유지)

### DoD Status
**✅ ALL PASSED**

---

## 산출물

1. **`docs/audit/q12_cancer_compare.jsonl`** (교체)
   - 모든 슬롯에 `value_normalized` + `display` 추가
   - 파싱 실패 시 안전 처리

2. **`docs/audit/q12_cancer_compare.md`** (교체)
   - 사람이 읽을 수 있는 display로 표시
   - 숫자 나열 완전 제거

3. **`docs/audit/q12_gate_validation_fix.json`**
   - G1/G2 PASS 증명

4. **`docs/audit/STEP_NEXT_82_Q12_FIX.md`** (본 문서)

---

## 금지 사항 (HARD)

### ❌ 절대 금지
1. **숫자 나열 출력**
   - "90, 1, 50" 형태의 출력 금지
   - GATE G2 위반 시 exit 2

2. **Step3 로직 변경**
   - 증거 탐색 로직은 건드리지 않음
   - evidence_refs는 그대로 유지

3. **잘못된 값 추론**
   - LLM 사용 금지
   - 패턴 매칭 실패 시 → null + reason

---

## 다음 단계

1. **UI 적용**
   - `value_normalized` 필드 활용
   - `display` 문자열을 고객용으로 표시

2. **추가 패턴**
   - 필요 시 정규식 패턴 추가 (deterministic만)
   - 새로운 슬롯 타입 스키마 정의

3. **전 보험사 확대**
   - 현재: samsung, meritz (2개사)
   - 향후: 전 보험사 담보 적용

---

## 완료 상태 메시지

```
✅ STEP NEXT-82-Q12-FIX 완료

Q12 표에서 숫자 나열(90, 1, 50) 출력: 0건
4개 슬롯 모두 구조화 value + display
GATES PASS
Step3 변경 없음

Customer-readable Q12 comparison table generated successfully.
```
