# STEP NEXT-70 — Document Discovery Fix & Anchor Enforcement

**Date**: 2026-01-08
**Status**: ✅ COMPLETED

---

## 목적

1. Step3에서 누락된 보험사 복구
   - db_over41, db_under40, lotte_female, lotte_male
2. 비교 결과에서 anchored 비율 개선
3. conflict 집계 기준 정합성 확보
4. 고객 설명 가능한 상태 만들기 (근거 + 일관성)

---

## 문제 진단

### TASK 1: Step3 문서 탐색 로직 문제

**증상**:
- db_over41, db_under40, lotte_female, lotte_male 이 "PDF 없음"으로 처리됨

**원인**:
```python
# DocumentSet.__init__ in document_reader.py
insurer_dir = self.sources_base_dir / self.insurer_key  # ❌
```

- Variant insurer keys (e.g., `db_over41`) 를 그대로 디렉터리명으로 사용
- 실제 디렉터리는 base insurer명 (`db`, `lotte`)으로 존재
- 결과: `data/sources/insurers/db_over41/` 경로 없음 → RuntimeError

**실제 파일 구조**:
```
data/sources/insurers/
  db/
    가입설계서/
      DB_가입설계서(40세이하)_2511.pdf
      DB_가입설계서(41세이상)_2511.pdf
    상품요약서/DB_상품요약서.pdf
    사업방법서/DB_사업방법서.pdf
    약관/DB_약관.pdf
  lotte/
    가입설계서/
      롯데_가입설계서(여)_2511.pdf
      롯데_가입설계서(남)_2511.pdf
    ...
```

### TASK 2: Anchor 정책 문제

**증상**:
- coverage_code 있음에도 unanchored 처리됨
- 기존: 31.0% anchored (245 rows)

**원인**:
```python
# extract_coverage_code in model.py (기존)
match = re.match(r'^(\d+)\.', coverage_name_raw)  # ❌
```

- "280  표적항암약물허가치료비(...)" → None (double space separator)
- "206. 다빈치로봇 암수술비(...)" → "206" (period separator)

정규식이 period (`.`) 구분자만 인식하고, double space 구분자는 인식 못함.

### TASK 3: Conflict 집계 기준 혼재

**증상**:
- Step3 conflict(슬롯 기준) vs Step4 conflict(커버리지 기준) 구분 불명확
- Meritz conflict 수치 설명 어려움

**원인**:
- 문서화 부족
- conflict_count가 무엇을 세는지 명확하지 않음

---

## 해결 방안

### TASK 1: Document Discovery 로직 수정

**변경 사항** (`pipeline/step3_evidence_resolver/document_reader.py`):

1. **Variant to Base Insurer Mapping**:
```python
class DocumentSet:
    # Variant key to base insurer directory mapping
    VARIANT_TO_BASE_INSURER = {
        "db_over41": "db",
        "db_under40": "db",
        "lotte_female": "lotte",
        "lotte_male": "lotte"
    }
```

2. **Variant-aware PDF Selection**:
```python
def _select_variant_pdf(self, pdf_files, insurer_key):
    variant_patterns = {
        "db_over41": ["41세이상", "41세 이상"],
        "db_under40": ["40세이하", "40세 이하"],
        "lotte_female": ["여", "(여)"],
        "lotte_male": ["남", "(남)"]
    }
    # Match PDF filename to variant pattern
```

3. **Discovery Logging**:
```python
print(f"[DocumentSet] Discovering documents for {self.insurer_key}")
print(f"[DocumentSet] Base insurer: {base_insurer}, Directory: {insurer_dir}")
print(f"[DocumentSet] Found {len(pdf_files)} PDF(s) in {doc_type}: {[p.name for p in pdf_files]}")
print(f"[DocumentSet] Selected PDF for {doc_type}: {selected_pdf.name}")
```

**결과**:
```
[DocumentSet] Discovering documents for db_over41
[DocumentSet] Base insurer: db, Directory: .../data/sources/insurers/db
[DocumentSet] Found 2 PDF(s) in 가입설계서: ['DB_가입설계서(40세이하)_2511.pdf', 'DB_가입설계서(41세이상)_2511.pdf']
[DocumentSet] Selected PDF for 가입설계서: DB_가입설계서(41세이상)_2511.pdf  ✅
[DocumentSet] Total documents discovered: 4
```

### TASK 2: Anchor 정책 강화

**변경 사항** (`pipeline/step4_compare_model/model.py`):

```python
def extract_coverage_code(coverage_name_raw: str) -> Optional[str]:
    # OLD: r'^(\d+)\.'
    # NEW: r'^(\d+)(?:\.|[\s]{2,})'  ← period OR 2+ spaces
    match = re.match(r'^(\d+)(?:\.|[\s]{2,})', coverage_name_raw)
    return match.group(1) if match else None
```

**테스트**:
```python
"206. 다빈치로봇 암수술비(...)" → "206" ✅
"280  표적항암약물허가치료비(...)" → "280" ✅  (이전: None ❌)
"일반상해사망" → None ✅
```

### TASK 3: Conflict 집계 기준 정합화

**변경 사항** (`pipeline/step4_compare_model/builder.py`):

1. **Documentation Enhancement**:
```python
def _has_conflict(self, coverage: Dict) -> bool:
    """
    Check if coverage has any slot-level conflicts.

    Definition: A coverage has conflict if ANY of its evidence slots
    has CONFLICT status (meaning documents disagree for that slot).

    This is coverage-level conflict, aggregated from slot-level conflicts.
    """
    evidence_status = coverage.get("evidence_status", {})
    return "CONFLICT" in evidence_status.values()
```

2. **Warning Message Enhancement**:
```python
def _generate_warnings(...):
    if conflict_count > 0:
        # Calculate total slot-level conflicts
        total_slot_conflicts = sum(
            row.slot_status_summary.get("CONFLICT", 0)
            for row in rows
        )
        warnings.append(
            f"CONFLICT detected in {conflict_count} coverages "
            f"({total_slot_conflicts} slot-level conflicts) (문서 불일치)"
        )
```

**출력 예**:
```
CONFLICT detected in 112 coverages (121 slot-level conflicts) (문서 불일치)
```

이제 다음을 명확하게 구분:
- **Coverage-level conflict count**: 112 (하나라도 슬롯에 CONFLICT 있는 커버리지 수)
- **Slot-level conflict count**: 121 (실제 CONFLICT 상태인 슬롯 총 개수)

---

## 실행 결과

### Step3 Evidence Resolver (전체 10개 보험사)

```
========== samsung ==========
  Total coverages: 32
  Slots FOUND: 96 (50.0%)
  Slots FOUND_GLOBAL: 93
  Slots CONFLICT: 3
  Slots UNKNOWN: 0
  Total evidence rate: 98.4%

========== hanwha ==========
  Total coverages: 33
  Slots FOUND: 118 (59.6%)
  Slots CONFLICT: 5
  Total evidence rate: 97.5%

========== heungkuk ==========
  Total coverages: 36
  Slots FOUND: 152 (70.4%)
  Slots CONFLICT: 11
  Total evidence rate: 94.9%

========== hyundai ==========
  Total coverages: 47
  Slots FOUND: 189 (67.0%)
  Slots CONFLICT: 16
  Total evidence rate: 94.3%

========== kb ==========
  Total coverages: 60
  Slots FOUND: 226 (62.8%)
  Slots CONFLICT: 10
  Total evidence rate: 97.2%

========== meritz ==========
  Total coverages: 37
  Slots FOUND: 101 (45.5%)
  Slots CONFLICT: 34
  Total evidence rate: 84.7%

========== db_over41 ========== ✅ (복구)
  Total coverages: 31
  Slots FOUND: 170 (91.4%)
  Slots CONFLICT: 3
  Total evidence rate: 98.4%

========== db_under40 ========== ✅ (복구)
  Total coverages: 31
  Slots FOUND: 166 (89.2%)
  Slots CONFLICT: 6
  Total evidence rate: 96.8%

========== lotte_female ========== ✅ (복구)
  Total coverages: 30
  Slots FOUND: 86 (47.8%)
  Slots CONFLICT: 32
  Total evidence rate: 82.2%

========== lotte_male ========== ✅ (복구)
  Total coverages: 30
  Slots FOUND: 85 (47.2%)
  Slots CONFLICT: 1
  Total evidence rate: 99.4%
```

**Step3-GATE 결과**:
- ✅ 10개 보험사 모두 처리 완료
- ✅ UNKNOWN = 0 유지 (모든 보험사)
- ✅ 문서 탐색 성공률 100%

### Step4 Compare Model (전체 비교)

**Before (STEP NEXT-69)**:
```
Total rows: 245
Insurers: kb, meritz, samsung, hanwha, heungkuk, hyundai  (6개)
Anchored: 76 (31.0%)
Conflicts: 60
```

**After (STEP NEXT-70)**:
```
Total rows: 367
Insurers: samsung, hanwha, heungkuk, hyundai, kb, meritz, db, lotte  (8개 = 10 variants)
Anchored: 139 (37.9%)
Unanchored: 228 (62.1%)
Conflicts: 112 coverages (121 slot-level conflicts)
Unknown rate: 0.0%

Warnings:
  - CONFLICT detected in 112 coverages (121 slot-level conflicts) (문서 불일치)
  - 228 coverages without coverage_code (정렬 제한)
```

**개선 사항**:
- ✅ +122 rows (245 → 367)
- ✅ +4 insurers (6 → 10 variants / 8 base insurers)
- ✅ +63 anchored (76 → 139)
- ✅ Anchored rate: 31.0% → 37.9% (+6.9%p)
- ✅ Conflict reporting: coverage-level + slot-level 분리 명시

---

## Anchor Rate 분석

**목표**: ≥ 60% anchored

**달성**: 37.9% anchored

**분석**:

1. **Unanchored coverage 특성** (예시 10개):
```
보험료 납입면제대상Ⅱ
암 진단비(유사암 제외)
유사암 진단비(기타피부암)(1년50%)
유사암 진단비(갑상선암)(1년50%)
유사암 진단비(대장점막내암)(1년50%)
유사암 진단비(제자리암)(1년50%)
유사암 진단비(경계성종양)(1년50%)
신재진단암(기타피부암 및 갑상선암 포함) 진단비(1년주기,5회한)
뇌출혈 진단비
뇌졸중 진단비(1년50%)
```

→ 담보명 자체에 숫자 코드가 없음 (일부 보험사의 명명 관습)

2. **Anchored coverage 특성** (예시):
```
1. 일반상해사망(기본)
2. 일반상해후유장해
3. 보험료납입면제대상보장
5. 일반상해후유장해
206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)
280  표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)
```

→ 숫자 코드 명시 (신정원 통일코드 또는 보험사 자체 코드)

3. **Conclusion**:
- 37.9% anchored는 **데이터 특성**이지 버그 아님
- 일부 보험사는 coverage_code 없이 서술형 담보명만 사용
- 60% 목표 달성을 위해서는:
  - Step2-b canonical mapping 정보 활용 필요 (현재 Step3는 Step1 직접 사용)
  - 또는 canonical_code → coverage_code 매핑 추가

**현재 아키텍처**:
```
Step1 (raw) → Step3 (evidence) → Step4 (compare)
                ↑ coverage_name_raw에서 code 추출
```

**대안 아키텍처** (향후 개선):
```
Step1 → Step2-b (canonical) → Step3 → Step4
                  ↑ canonical_code 포함
```

---

## 성공 기준 검증

| 기준 | 목표 | 달성 | 비고 |
|------|------|------|------|
| 모든 보험사가 비교 테이블에 올라감 | 10 variants | ✅ 10 variants | db_over41/under40, lotte_female/male 복구 |
| code 있는 담보는 확실히 묶임 | anchored=true | ✅ | regex 개선으로 double-space separator 지원 |
| 충돌은 이유를 바로 설명 가능 | 명확한 구분 | ✅ | coverage-level (112) + slot-level (121) 분리 표시 |
| UNKNOWN = 0 | 0% | ✅ | 모든 보험사 0% 달성 |

---

## 산출물

### Code Changes

1. **pipeline/step3_evidence_resolver/document_reader.py**
   - `VARIANT_TO_BASE_INSURER` mapping 추가
   - `_select_variant_pdf()` 메서드 추가
   - Discovery logging 추가

2. **pipeline/step4_compare_model/model.py**
   - `extract_coverage_code()` regex 개선: `r'^(\d+)(?:\.|[\s]{2,})'`
   - `extract_coverage_title()` regex 개선

3. **pipeline/step4_compare_model/builder.py**
   - `_has_conflict()` docstring 강화
   - `_generate_warnings()` slot-level conflict count 추가

### Data Files

**Step3 Output** (10 insurers):
```
data/scope_v3/samsung_step3_evidence_enriched_v1_gated.jsonl        (32 coverages)
data/scope_v3/hanwha_step3_evidence_enriched_v1_gated.jsonl        (33 coverages)
data/scope_v3/heungkuk_step3_evidence_enriched_v1_gated.jsonl      (36 coverages)
data/scope_v3/hyundai_step3_evidence_enriched_v1_gated.jsonl       (47 coverages)
data/scope_v3/kb_step3_evidence_enriched_v1_gated.jsonl            (60 coverages)
data/scope_v3/meritz_step3_evidence_enriched_v1_gated.jsonl        (37 coverages)
data/scope_v3/db_over41_step3_evidence_enriched_v1_gated.jsonl     (31 coverages) ✅
data/scope_v3/db_under40_step3_evidence_enriched_v1_gated.jsonl    (31 coverages) ✅
data/scope_v3/lotte_female_step3_evidence_enriched_v1_gated.jsonl  (30 coverages) ✅
data/scope_v3/lotte_male_step3_evidence_enriched_v1_gated.jsonl    (30 coverages) ✅
```

**Step4 Output**:
```
data/compare_v1/compare_rows_v1.jsonl     (367 rows)
data/compare_v1/compare_tables_v1.jsonl   (1 table, 8 base insurers)
```

---

## 절대 규칙 준수

- ✅ LLM 금지
- ✅ 값 추론/보정 금지
- ✅ Step1~2 의미 변경 금지
- ✅ Evidence-first
- ✅ Same input → Same output (deterministic)

---

## 다음 단계 제안

1. **Step3 Input 변경**:
   - 현재: Step1 raw → Step3
   - 제안: Step2-b canonical → Step3
   - 이유: canonical_code, mapping_method 정보 활용 가능

2. **Anchor Policy Enhancement**:
   - `canonical_code` 존재 시 → `anchored=true`
   - `coverage_code` 없어도 canonical mapping 성공 시 anchor 가능

3. **Conflict 상세 분석**:
   - Meritz 34 slot conflicts 원인 분석
   - Document type별 conflict 패턴 파악

---

**End of STEP NEXT-70**
