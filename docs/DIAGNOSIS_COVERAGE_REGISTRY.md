# Diagnosis Coverage Registry (SSOT)

**Version:** v1.0
**Status:** LOCKED
**Last Updated:** 2026-01-09

---

## 목적

본 레지스트리는 시스템에서 **"진단비"로 인정되는 담보의 정체성(identity)**을 단일 기준으로 고정한다.

**핵심 원칙:**
- 진단비는 `coverage_code` 기준으로만 식별
- 담보명 문자열로 추론 ❌
- Evidence 존재만으로 인정 ❌
- **Registry 미등재 coverage → 진단비 비교/추천 배제**

---

## 진단비(Diagnosis Benefit) 공식 정의

### 필수 조건 (ALL 만족 필요)

1. **지급 트리거: 진단 확정**
   - "진단 확정 시 지급"
   - "진단 확정되었을 때"
   - 치료 행위 발생을 조건으로 하지 않음

2. **담보 종류: 진단금 지급**
   - 치료비 ❌
   - 입원비 ❌
   - 수술비 ❌
   - 일당 ❌

3. **지급 목적: 진단 사실에 대한 보상**
   - 치료비 지원 목적 ❌
   - 입원 시 발생 비용 보상 ❌
   - 수술 실행에 대한 보상 ❌

---

## Coverage Kind 분류 (Fixed Enum)

### diagnosis_benefit ✅
**정의:** 질병 진단 확정 시 지급되는 진단금

**예시:**
- 암진단비(유사암 제외)
- 뇌졸중진단비
- 허혈성심장질환진단비
- 뇌출혈진단비
- 급성심근경색진단비
- 10대 주요암진단비

**사용 가능:**
- Q1-Q14 모든 고객 질문
- 회사 간 비교 (Q12)
- 추천 (Q4, Q5)

---

### treatment_trigger ❌
**정의:** 진단은 조건이지만, 실제 지급은 치료 행위 발생 시

**예시:**
- 암 치료비 지원
- 표적항암약물허가치료비 (진단 후 치료 시 지급)
- 암 직접치료 통원일당

**사용 불가:**
- 진단비 비교 테이블 ❌
- 진단비 추천 ❌
- Q13 출력 시 별도 표시: "진단 시 치료비 지급 (진단비 아님)"

---

### admission_benefit ❌
**정의:** 입원 일수 또는 입원 사실에 기반한 지급

**예시:**
- 암 요양병원 입원일당
- 질병입원일당
- 암 입원비

**사용 불가:**
- 진단비 비교 ❌
- 진단비 추천 ❌

---

### surgery_benefit ❌
**정의:** 수술 실행 시 지급

**예시:**
- 암 수술비
- 관상동맥우회술 수술비

**사용 불가:**
- 진단비 비교 ❌
- 진단비 추천 ❌

---

### definition_only ❌
**정의:** 정의 문구, 예시, 설명

**사용 불가:**
- 모든 고객 출력 ❌

---

## Subtype 처리 원칙 (LOCK)

### 제자리암 (In-situ Cancer)
**원칙:** coverage_name에 **명시적 포함** 시에만 diagnosis_benefit 인정

**예시:**
- "암진단비(유사암 제외)" + 유사암 정의에 "제자리암" 포함 → ❌ 제외
- "제자리암진단비" → ✅ 별도 진단비로 인정

---

### 경계성종양 (Borderline Tumor)
**원칙:** 제자리암과 동일

**예시:**
- "암진단비(유사암 제외)" + 유사암 정의에 "경계성종양" 포함 → ❌ 제외
- "경계성종양진단비" → ✅ 별도 진단비로 인정

---

### 유사암 (Similar Cancer)
**원칙:** **별도 담보**로 취급

**구성:**
- 기타피부암
- 갑상선암
- 대장점막내암
- 제자리암
- 경계성종양

**처리:**
- "암진단비(유사암 제외)"와 **완전 분리**
- "유사암진단비"는 독립된 diagnosis_benefit
- 비교 시 **절대 혼입 금지**

---

### 소액암 (Small Amount Cancer)
**원칙:** 감액 지급 조건이지, 별도 담보 아님

**예시:**
- "계약일부터 1년경과시점 전일 이전 소액암 진단시 1천5백만원(가입금액의 50%) 지급"
- → 암진단비의 **감액 지급 조건**으로 취급
- → 별도 진단비 ❌

---

## 진단비 vs 비진단비 구분 사례

### ✅ diagnosis_benefit

| Coverage | Reason |
|----------|--------|
| 암진단비(유사암 제외) | 진단 확정 시 지급, 치료비 아님 |
| 유사암진단비 | 진단 확정 시 지급, 별도 진단비 |
| 10대 주요암진단비 | 진단 확정 시 지급 |
| 5대고액치료비암진단비 | 진단 확정 시 지급 (명칭에 치료비 있으나 실제는 진단비) |
| 통합암진단비(전이포함) | 진단 확정 시 지급 |
| 뇌졸중진단비 | 진단 확정 시 지급 |
| 허혈성심장질환진단비 | 진단 확정 시 지급 |

---

### ❌ treatment_trigger

| Coverage | Reason |
|----------|--------|
| 표적항암약물허가치료비 | 진단 후 치료 시 지급 (치료비) |
| 암 치료비 지원 | 치료 행위 발생 시 지급 |
| 암 직접치료 통원일당 | 통원 치료 시 지급 |
| 항암약물치료비 | 치료 발생 시 지급 |
| 허혈성심장질환수술비 | 진단 후 수술 시 지급 (수술비) |

---

### ❌ admission_benefit

| Coverage | Reason |
|----------|--------|
| 암 요양병원 입원일당 | 입원 일수 기반 지급 |
| 암 입원비 | 입원 사실 기반 지급 |

---

### ❌ surgery_benefit

| Coverage | Reason |
|----------|--------|
| 암 수술비 | 수술 실행 시 지급 |

---

## Registry 적용 범위

### 필수 적용 단계

1. **Step4 (Compare Model)**
   - Q12 회사 간 비교
   - coverage_code가 registry에 등재된 경우만 비교 허용

2. **Step5 (Recommendation)**
   - Q4, Q5 추천
   - diagnosis_benefit만 추천 대상

3. **Q1-Q14 Customer Output**
   - 모든 고객 질문
   - Registry 기준 강제 적용

4. **G5 Coverage Attribution Gate**
   - SSOT 기준으로 excluded_patterns 생성
   - Registry 미등재 담보는 자동 제외

---

### 적용 방식

```python
# Load registry
registry = load_diagnosis_coverage_registry()

# Check if coverage is diagnosis_benefit
if coverage_code in registry:
    coverage_entry = registry[coverage_code]
    if coverage_entry["coverage_kind"] == "diagnosis_benefit":
        # ✅ Allow comparison/recommendation
        pass
    else:
        # ❌ Reject: not diagnosis_benefit
        reject(f"{coverage_code} is {coverage_entry['coverage_kind']}, not diagnosis_benefit")
else:
    # ❌ Reject: not in registry
    reject(f"{coverage_code} not in Diagnosis Coverage Registry")
```

---

## 금지 사항 (ABSOLUTE)

### ❌ 담보명 문자열로 진단비 추론
**잘못된 예:**
```python
if "진단비" in coverage_name:
    return "diagnosis_benefit"  # ❌ 금지
```

**올바른 방법:**
```python
if coverage_code in registry and registry[coverage_code]["coverage_kind"] == "diagnosis_benefit":
    return True  # ✅
```

---

### ❌ Evidence 존재만으로 diagnosis_benefit 인정
**잘못된 예:**
```python
if evidence_refs:
    return "diagnosis_benefit"  # ❌ 금지
```

**올바른 방법:**
```python
# Evidence는 값 추출에만 사용
# coverage_kind는 registry로만 판단
```

---

### ❌ 암진단비 기준을 다른 진단비에 유추 적용
**잘못된 예:**
```python
# 암진단비 기준을 뇌졸중진단비에 그대로 적용
if "진단비" in coverage_name and "뇌졸중" in coverage_name:
    return "diagnosis_benefit"  # ❌ 금지
```

**올바른 방법:**
```python
# 뇌졸중진단비는 registry에 별도 등재 필요
# 등재 전까지는 비교/추천 불가
```

---

### ❌ Registry 미등재 coverage_code 출력
**규칙:** Registry에 없는 coverage_code는 고객 출력 금지

**예외:** Q13 (coverage inventory)는 표시 가능하되, coverage_kind 표시 필수

---

## 확장 원칙

### 신규 진단비 추가 절차

1. **Registry 등재 (MUST)**
   - `data/registry/diagnosis_coverage_registry.json`에 추가
   - coverage_code, coverage_kind, excluded_subtypes 명시

2. **SSOT 문서 갱신**
   - 본 문서에 사례 추가

3. **G5 Gate 갱신**
   - excluded_patterns 업데이트

4. **검증**
   - Q12 재검증
   - UNKNOWN 증가는 정상 (registry 기준 강화)

---

### 다음 확장 대상

1. **STEP NEXT-E: 급성심근경색증진단비**
   - Samsung + KB 파일럿
   - Registry 등재 후 확장

2. **STEP NEXT-83: 전 진단비**
   - 암 → 뇌졸중 → 허혈성심장질환 → 급성심근경색
   - 순차적 registry 등재

---

## 최종 선언

**본 시스템에서 "진단비"는**
**Diagnosis Coverage Registry에 등재된 `coverage_code`만을 의미하며,**
**그 외 모든 담보는 진단비 비교·추천에서 배제된다.**

---

## 변경 이력

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-01-09 | Initial SSOT lock (Samsung + KB cancer diagnosis) |
| v1.0 | 2026-01-09 | STEP NEXT-C: Added stroke diagnosis (Samsung + KB, A4103) |
| v1.0 | 2026-01-09 | STEP NEXT-D: Added ischemic heart disease diagnosis (Samsung + KB, A4105) |

---

## 참조

- `data/registry/diagnosis_coverage_registry.json` - Machine-readable registry
- `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` - Implementation audit
- `docs/audit/STEP_NEXT_82_Q12_FIX_2.md` - Coverage Attribution Gate (G5)
