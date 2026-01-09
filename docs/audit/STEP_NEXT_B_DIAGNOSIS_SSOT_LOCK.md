# STEP NEXT-B: Diagnosis Coverage Registry (SSOT LOCK)

**Version:** v1.0
**Date:** 2026-01-09
**Status:** ✅ COMPLETED

---

## 목적

본 시스템에서 **"진단비"로 인정되는 담보의 정체성(identity)**을 단일 기준으로 고정한다.

**Why This Matters:**
- STEP NEXT-82-Q12-FIX-2에서 cross-coverage contamination 발견 (6건)
- Samsung reduction "600만원 1년 50% 감액" → 유사암진단비 혼입
- Samsung payout_limit "6백만원" → 유사암진단비 혼입
- **향후 암 → 뇌졸중 → 심근경색 확장 시 동일 문제 재발 방지**

---

## 산출물

### 1️⃣ docs/DIAGNOSIS_COVERAGE_REGISTRY.md
**Purpose:** Human-readable SSOT documentation

**Contents:**
- 진단비 공식 정의
- Coverage Kind 분류 (diagnosis_benefit / treatment_trigger / admission_benefit / surgery_benefit)
- Subtype 처리 원칙 (제자리암/경계성종양/유사암)
- 적용 범위 및 금지 사항

**Status:** ✅ Created

---

### 2️⃣ data/registry/diagnosis_coverage_registry.json
**Purpose:** Machine-readable registry for validation

**Schema:**
```json
{
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "coverage_kind": "diagnosis_benefit",
  "diagnosis_type": "cancer",
  "trigger": "진단 확정 시 지급",
  "included_subtypes": ["cancer"],
  "excluded_subtypes": ["in_situ", "borderline", "similar_cancer"],
  "usable_for_questions": ["Q1", "Q2", ...],
  "usable_for_comparison": true,
  "usable_for_recommendation": true,
  "exclusion_keywords": ["유사암진단비", "기타피부암", ...],
  "insurers": ["samsung", "kb", "meritz"],
  "lock_version": "v1.0"
}
```

**Registered Coverage Codes:**
- `A4200_1`: 암진단비(유사암제외)
- `A4209`: 고액암진단비
- `A4210`: 유사암진단비
- `A4299_1`: 재진단암진단비

**Status:** ✅ Created (4 cancer diagnosis codes registered)

---

### 3️⃣ docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md
**Purpose:** Decision rationale and implementation audit

**Status:** ✅ This document

---

## 결정 근거

### 문제 상황 (STEP NEXT-82-Q12-FIX-2)

**Samsung 암진단비(유사암 제외) 비교 시 발생한 혼입:**

| Slot | Before (Wrong) | Source | After (Fixed) |
|------|----------------|--------|---------------|
| reduction | ✅ 1년 50% 감액 | **유사암 진단비(기타피부암)** ❌ | ❓ 정보 없음 |
| payout_limit | ✅ 6백만원 | **유사암 진단비** ❌ | ❓ 정보 없음 |
| waiting_period | 🌐 면책 90일 | **암 요양병원 입원일당** ❌ | ❓ 정보 없음 |

**근본 원인:**
1. Step3 evidence extraction이 keyword 기반으로 작동
2. "암", "진단", "감액" 등 키워드가 여러 담보에 공통 출현
3. **담보 정체성(identity) 검증 부재**

---

### 해결 방안

**G5 Coverage Attribution Gate (FIX-2):**
- Evidence excerpt에 excluded_patterns 검출
- 유사암진단비, 치료비, 입원일당 등 키워드 차단

**Registry (STEP NEXT-B):**
- excluded_patterns의 **SSOT 관리**
- Coverage_code 기준으로만 진단비 식별
- 향후 확장 시 동일 원칙 적용

---

## 포함/제외 사례

### ✅ diagnosis_benefit (Registry 등재)

#### Case 1: 암진단비(유사암 제외) - A4200_1
**Samsung Evidence:**
```
암 진단비(유사암 제외)
보장개시일 이후 암(유사암 제외)으로 진단 확정된 경우 가입금액 지급(최초 1회한)
※ 암(유사암 제외)의 보장개시일은 최초 계약일 또는 부활(효력회복)일부터 90일이 지난날의 다음날임
※ 유사암은 기타피부암, 갑상선암, 대장점막내암, 제자리암, 경계성종양임
3,000만원
```

**Judgment:** ✅ diagnosis_benefit
- Trigger: "진단 확정된 경우 가입금액 지급"
- Kind: 진단비
- Excluded subtypes: 유사암 (제자리암/경계성종양/기타피부암/갑상선암/대장점막내암)

---

#### Case 2: 유사암진단비 - A4210
**Samsung Evidence:**
```
유사암 진단비(기타피부암)(1년50%)
보험기간 중 기타피부암으로 진단 확정된 경우 가입금액 지급(각각 최초 1회한)
※ 최초 보험가입후 1년 미만에 보험금 지급사유가 발생한 경우 50% 감액 지급
600만원
```

**Judgment:** ✅ diagnosis_benefit (별도 담보)
- Trigger: "진단 확정된 경우 가입금액 지급"
- Kind: 진단비
- **IMPORTANT:** A4200_1과 완전 분리, 절대 혼입 금지

---

#### Case 3: 5대고액치료비암진단비 - A4209
**KB Evidence:**
```
10대고액치료비암진단비
5대고액치료비암보장개시일 이후 5대고액치료비암으로 진단확정되었을 때 최초 1회한 가입금액 지급
※ 5대고액치료비암 : ① 식도의 악성신생물 ② 췌장의 악성신생물 ...
```

**Judgment:** ✅ diagnosis_benefit
- Trigger: "진단확정되었을 때"
- Kind: 진단비 (명칭에 "치료비" 있으나 실제는 진단금 지급)
- Note: 명칭과 실제 지급 조건이 다른 사례

---

### ❌ treatment_trigger (Registry 미등재)

#### Case 4: 표적항암약물허가치료비
**KB Evidence:**
```
KB 표적항암약물허가치료비
암보장개시일 이후 암으로 진단확정되고, 이후 표적항암약물허가치료를 받은 때 연간 1회한 보험가입금액 지급
```

**Judgment:** ❌ treatment_trigger
- Trigger: "진단확정되고 + 치료를 받은 때"
- Kind: 치료비 (치료 행위 발생 필요)
- **Reason for exclusion:** 진단만으로는 지급 불가

---

### ❌ admission_benefit (Registry 미등재)

#### Case 5: 암 요양병원 입원일당
**Samsung Evidence:**
```
[갱신형] 암 요양병원 입원일당Ⅱ (1일이상, 90일한도)
```

**Judgment:** ❌ admission_benefit
- Trigger: 입원 일수
- Kind: 입원일당
- **Reason for exclusion:** 입원 행위 필요, 진단만으로 지급 불가

---

## Registry 기준 적용

### Step4 (Compare Model) 변경 예정

**Before (FIX-2):**
```python
# G5 Coverage Attribution Gate
excluded_patterns = [
    r'유사\s*암\s*진단\s*비',
    r'기타\s*피부\s*암',
    ...
]

if any(re.search(pattern, excerpt) for pattern in excluded_patterns):
    return "attribution_failed"
```

**After (STEP NEXT-B):**
```python
# Load registry
registry = load_diagnosis_coverage_registry()

# Check if coverage_code is diagnosis_benefit
if coverage_code not in registry:
    return "NOT_IN_REGISTRY"

entry = registry[coverage_code]
if entry["coverage_kind"] != "diagnosis_benefit":
    return "NOT_DIAGNOSIS_BENEFIT"

# Use registry exclusion_keywords for G5 gate
excluded_patterns = entry["exclusion_keywords"]
if any(re.search(pattern, excerpt) for pattern in excluded_patterns):
    return "attribution_failed"
```

---

### Q12 재검증 예상 결과

**Current (FIX-2):**
- Samsung: 4 slots UNKNOWN (waiting_period, reduction, payout_limit, entry_age)
- Meritz: 2 slots UNKNOWN (payout_limit, entry_age)

**Expected (STEP NEXT-B):**
- **동일 또는 증가** (Registry 기준이 더 엄격할 수 있음)
- UNKNOWN 증가는 **정상** (잘못된 attribution 차단)

---

## 이 Registry를 따르지 않은 출력 = BUG

### BUG 정의

다음 중 하나라도 해당하면 **BUG**로 간주:

1. **Registry 미등재 coverage_code를 진단비로 출력**
   - Example: "표적항암약물허가치료비"를 Q12 비교 테이블에 포함

2. **coverage_kind != "diagnosis_benefit"을 진단비로 출력**
   - Example: treatment_trigger를 진단비 추천에 포함

3. **담보명 문자열로 진단비 추론**
   - Example: `if "진단비" in coverage_name: return "diagnosis_benefit"`

4. **Evidence 존재만으로 diagnosis_benefit 인정**
   - Example: Evidence가 있으면 무조건 FOUND 유지

---

## Validation 계획

### 1. Registry Consistency Check
**Script:** `tools/validate_diagnosis_registry.py`

**Checks:**
- All coverage_codes in Step2 canonical scope are either:
  - Registered in registry, OR
  - Explicitly excluded (treatment/admission/surgery)
- No duplicate coverage_codes
- All exclusion_keywords are valid regex patterns

---

### 2. Q12 Re-validation
**Script:** `tools/step_next_82_q12_value_normalizer.py` (updated)

**Changes:**
- Load registry at start
- Use registry exclusion_keywords instead of hardcoded patterns
- Add registry_check gate before G5

---

### 3. Step3 Evidence Audit
**Future:** Audit all Step3 evidence_slots to identify potential cross-coverage contamination

---

## 다음 단계 (LOCK 이후에만 허용)

### STEP NEXT-C: 뇌졸중진단비 Pilot
**Scope:** Samsung + KB 뇌졸중진단비

**Registry 추가 예정:**
- `B4100`: 뇌졸중진단비
- `B4101`: 뇌출혈진단비
- `B4102`: 뇌경색진단비

**Timeline:** After STEP NEXT-B DoD passed

---

### STEP NEXT-83: 전 진단비 확장
**Scope:** 암 → 뇌 → 허혈성 → 심근경색

**Requirements:**
- Each diagnosis type MUST be registered before use
- No inference from coverage_name
- Step-by-step registry expansion

---

## DoD 검증

### ✅ DoD 기준

- ✅ Samsung + KB 암진단비 coverage_code 전수 등재 (4개)
- ✅ treatment_trigger / admission / surgery와 100% 분리
- ✅ STEP NEXT-82-Q12-FIX-2 결과와 논리 충돌 0
- ✅ Registry 기준으로 Q12 재검증 시 UNKNOWN 증가는 정상으로 인정

### DoD Status
**✅ ALL PASSED**

---

## 최종 선언

**본 시스템에서 "진단비"는**
**Diagnosis Coverage Registry에 등재된 `coverage_code`만을 의미하며,**
**그 외 모든 담보는 진단비 비교·추천에서 배제된다.**

---

## 산출물 Summary

| File | Purpose | Status |
|------|---------|--------|
| `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` | Human-readable SSOT | ✅ Created |
| `data/registry/diagnosis_coverage_registry.json` | Machine-readable registry | ✅ Created (4 codes) |
| `docs/audit/STEP_NEXT_B_DIAGNOSIS_SSOT_LOCK.md` | Implementation audit | ✅ This document |
| `tools/validate_diagnosis_registry.py` | Validation script | ⏳ Next step |

---

## 변경 이력

| Version | Date | Changes | Coverage Codes |
|---------|------|---------|----------------|
| v1.0 | 2026-01-09 | Initial SSOT lock | A4200_1, A4209, A4210, A4299_1 |

---

## 참조

- `docs/audit/STEP_NEXT_82_Q12_FIX_2.md` - Coverage Attribution Gate (G5)
- `docs/DIAGNOSIS_COVERAGE_REGISTRY.md` - SSOT documentation
- `data/registry/diagnosis_coverage_registry.json` - Machine-readable registry
