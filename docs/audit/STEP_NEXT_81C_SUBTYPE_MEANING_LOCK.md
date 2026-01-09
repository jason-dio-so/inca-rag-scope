# STEP NEXT-81C: Subtype Coverage Meaning Lock (HARD)

## 목적

STEP NEXT-81B에서 `scope=diagnosis, condition_type=지급사유`로 분류된 항목이
고객에게 **"진단비 보장"**으로 오해되지 않도록
**coverage_kind 필드를 추가하여 O의 의미를 보장유형별로 고정(Lock)** 함.

---

## 문제 정의

### Before (STEP NEXT-81B)
```json
{
  "coverage_name": "표적항암약물허가치료비",
  "subtype_coverage_refined": {
    "in_situ": {
      "decision": "O",
      "scope": "diagnosis",
      "condition_type": "지급사유",
      "usable_as_coverage": true
    }
  }
}
```

**문제:**
- `scope=diagnosis` → "진단비 보장 O"로 오해 가능
- 실제로는 **"진단 시 치료비 지급 트리거"**일 뿐, 진단비가 아님
- 고객이 "제자리암 진단비 받을 수 있다"고 착각할 위험

---

## 해결책: coverage_kind 필드 추가

### coverage_kind 정의 (LOCK)

| coverage_kind | 의미 | Q13 표시 규칙 | usable_as_coverage |
|---------------|------|---------------|-------------------|
| **diagnosis_benefit** | 진단비 자체 (진단 시 일시금) | ✅ **보장 O** | `true` |
| **treatment_trigger** | 치료비 지급 트리거 (진단비 아님) | ⚠️ **진단 시 치료비 지급 (진단비 아님)** | `false` |
| **definition_only** | 정의/예시/범위 설명 | ℹ️ **정의 문맥 언급** | `false` |
| **excluded** | 제외 문구 | ❌ **보장 X** | `false` |

---

## 분류 규칙 (LOCK)

### Rule 1: diagnosis_benefit
- 담보명에 "진단비" 포함 **AND**
- `scope in {diagnosis, treatment}`

### Rule 2: treatment_trigger
- 담보명에 "치료비/약물/수술/항암" 포함 **AND**
- `scope = diagnosis`

### Rule 3: definition_only
- `scope in {definition, example, unknown}`

### Rule 4: excluded
- `original_covered = false` **OR**
- `scope = excluded`

---

## Before/After 비교 (KB 표적항암약물허가치료비)

### Before (STEP NEXT-81B)
```json
{
  "coverage_name": "280 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)",
  "subtype_coverage_refined": {
    "in_situ": {
      "decision": "O",
      "scope": "diagnosis",
      "condition_type": "지급사유",
      "usable_as_coverage": true,
      "evidence_refs": [{
        "excerpt": "보험기간 중 기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단확정시"
      }]
    }
  }
}
```

**오해 가능성:**
- ❌ "제자리암 진단비 보장 O"로 표시될 위험
- ❌ 고객이 "진단 시 일시금 받을 수 있다"고 착각

---

### After (STEP NEXT-81C)
```json
{
  "coverage_name": "280 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)",
  "subtype_coverage_locked": {
    "in_situ": {
      "decision": "O",
      "scope": "diagnosis",
      "condition_type": "지급사유",
      "coverage_kind": "treatment_trigger",
      "usable_as_coverage": false,
      "q13_display_rule": "진단 시 치료비 지급 (진단비 아님)",
      "evidence_refs": [{
        "excerpt": "보험기간 중 기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단확정시"
      }]
    }
  }
}
```

**개선점:**
- ✅ `coverage_kind=treatment_trigger` → 명확히 "치료비 트리거"임을 표시
- ✅ `usable_as_coverage=false` → 진단비 비교에 사용 금지
- ✅ `q13_display_rule="진단 시 치료비 지급 (진단비 아님)"` → 고객 오해 방지

---

## Q13 출력 규칙 (HARD LOCK)

### diagnosis_benefit만 "보장 O"로 표시

```python
if coverage_kind == "diagnosis_benefit":
    display = "보장 O"
elif coverage_kind == "treatment_trigger":
    display = "진단 시 치료비 지급 (진단비 아님)"
elif coverage_kind == "definition_only":
    display = "정의 문맥 언급"
else:  # excluded
    display = "보장 X"
```

---

## 검증 결과 (DoD)

### DoD 기준
- ✅ treatment_trigger → "진단비 O" 출력 **0건**
- ✅ diagnosis_benefit / treatment_trigger 명확 분리
- ✅ KB 표적항암약물허가치료비 검증 PASS

### 실행 결과
```
Total processed: 1
  diagnosis_benefit: 0
  treatment_trigger: 2 (in_situ + borderline)
  definition_only: 0
  excluded: 0

DoD Status: ✅ PASS
  - treatment_trigger → 진단비 O 출력: 0 건
```

---

## 산출물

1. **Locked JSONL:**
   `docs/audit/step_next_81c_subtype_coverage_locked.jsonl`

2. **Validation 결과:**
   `docs/audit/step_next_81c_validation.json`

3. **LOCK 문서 (본 문서):**
   `docs/audit/STEP_NEXT_81C_SUBTYPE_MEANING_LOCK.md`

---

## 사용 예시 (Q13 테이블)

### Before (오해 위험)
| 담보 | 제자리암 | 경계성종양 |
|------|---------|-----------|
| KB 표적항암약물허가치료비 | ❌ O | ❌ O |

→ 고객: "제자리암 진단비 받을 수 있네!" (착각)

---

### After (명확한 구분)
| 담보 | 제자리암 | 경계성종양 | 비고 |
|------|---------|-----------|------|
| KB 표적항암약물허가치료비 | ⚠️ 진단 시 치료비 지급 (진단비 아님) | ⚠️ 진단 시 치료비 지급 (진단비 아님) | 치료비 트리거 |

→ 고객: "아, 진단비가 아니라 치료비 받을 때 조건이구나" (정확한 이해)

---

## 금지 사항 (HARD)

- ❌ treatment_trigger를 "보장 O"로 표시 금지
- ❌ "진단비"와 "치료비 트리거"를 혼동하지 말 것
- ❌ LLM 추론으로 coverage_kind 결정 금지 (규칙 기반만)

---

## 다음 단계

- UI/Q13 출력에서 `coverage_kind` 및 `q13_display_rule` 필드 적용
- `diagnosis_benefit`만 "보장 O"로 표시
- `treatment_trigger`는 별도 표기 (⚠️ 아이콘 + 설명)
