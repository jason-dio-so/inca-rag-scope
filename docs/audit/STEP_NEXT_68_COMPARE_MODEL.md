# STEP NEXT-68: Coverage Comparison Model

**Date**: 2026-01-08
**Status**: ✅ COMPLETED
**Insurer**: KB (v1)

---

## 목표 (Objective)

Step3 GATED 출력 (FOUND/FOUND_GLOBAL/CONFLICT/UNKNOWN)을 입력으로 받아,
보험사/상품/variant/담보 단위 비교 테이블(Compare ViewModel)을 생성한다.

**핵심 원칙**: Evidence-first, NO LLM, NO inference.

---

## 입출력 (Input/Output SSOT)

### INPUT

**SSOT**: `data/scope_v3/{insurer}_step3_evidence_enriched_v1_gated.jsonl`

**필수 필드**:
- `insurer_key`, `product.product_key`, `variant.variant_key`
- `coverage_name_raw` / `coverage_normalized`
- `coverage_code` (optional)
- `proposal_facts.coverage_semantics` (optional)
- `evidence_slots`, `evidence_status`, `evidence`

### OUTPUT

**SSOT**:
1. `data/compare_v1/compare_rows_v1.jsonl` (row-per-coverage-per-insurer)
2. `data/compare_v1/compare_tables_v1.jsonl` (query-ready table bundles)

---

## 핵심 모델 (Schema)

### 1. 비교 슬롯 (Comparison Slots)

각 coverage row는 아래 6개 슬롯을 **반드시** 가진다:

| Slot | 의미 | 출처 |
|------|------|------|
| `start_date` | 보장개시일 | Step3 evidence |
| `exclusions` | 면책사항 | Step3 evidence |
| `payout_limit` | 지급한도/횟수 | Step3 evidence |
| `reduction` | 감액기간/비율 | Step3 evidence |
| `entry_age` | 가입나이 | Step3 evidence |
| `waiting_period` | 면책기간/대기기간 | Step3 evidence |

**Optional**:
- `renewal_condition`: 갱신형 여부/주기 (from Step1 semantics)

### 2. SlotValue 구조

```json
{
  "status": "FOUND | FOUND_GLOBAL | CONFLICT | UNKNOWN",
  "value": "정규화된 값 (optional)",
  "evidences": [
    {
      "doc_type": "가입설계서",
      "page": 6,
      "excerpt": "...",
      "locator": {...},
      "gate_status": "FOUND"
    }
  ],
  "notes": "gate failure reason or conflict summary"
}
```

**CONSTRAINT**: `value` must be derived from `evidences` (no inference).

### 3. CompareRow Schema

```json
{
  "identity": {
    "insurer_key": "kb",
    "product_key": "kb__KB닥터플러스건강보험...",
    "variant_key": "default",
    "coverage_code": "206",
    "coverage_title": "다빈치로봇 암수술비",
    "coverage_name_raw": "206. 다빈치로봇 암수술비(...)"
  },
  "semantics": {
    "exclusions": ["갑상선암", "전립선암"],
    "payout_limit_count": 1,
    "renewal_flag": true
  },
  "slots": {
    "start_date": { SlotValue },
    "exclusions": { SlotValue },
    "payout_limit": { SlotValue },
    "reduction": { SlotValue },
    "entry_age": { SlotValue },
    "waiting_period": { SlotValue }
  },
  "renewal_condition": "갱신형 (10년갱신)",
  "meta": {
    "slot_status_summary": {"FOUND": 4, "FOUND_GLOBAL": 2},
    "has_conflict": false,
    "unanchored": false
  }
}
```

### 4. CompareTable Schema

```json
{
  "table_id": "compare_kb",
  "insurers": ["kb"],
  "product_keys": ["kb__KB닥터플러스건강보험..."],
  "variant_keys": ["default"],
  "coverage_rows": [ CompareRow, ... ],
  "table_warnings": [
    "CONFLICT detected in 10 coverages (문서 불일치)",
    "21 coverages without coverage_code (정렬 제한)"
  ],
  "meta": {
    "total_rows": 60,
    "conflict_count": 10,
    "unknown_rate": 0.0
  }
}
```

---

## Coverage Identity & Comparison Key

### Coverage Code Extraction

```python
# "206. 다빈치로봇 암수술비(...)" -> "206"
# "1. 일반상해사망(기본)" -> "1"
coverage_code = extract_coverage_code(coverage_name_raw)
```

### Coverage Title Extraction

```python
# "206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
# -> "다빈치로봇 암수술비"
coverage_title = extract_coverage_title(coverage_name_raw)
```

### Comparison Key

**우선순위**: `coverage_code` > `coverage_title`

```python
def get_comparison_key(coverage):
    if coverage.code:
        return f"code:{coverage.code}"
    return f"title:{coverage.title}"
```

### Anchoring (정렬 기준)

- **Anchored** (coverage_code 존재): 테이블 상단, code 순 정렬
- **Unanchored** (coverage_code 없음): 테이블 하단, title 순 정렬

---

## 비교 테이블 생성 규칙

### 1. Single-Insurer Table

**Input**: `data/scope_v3/kb_step3_evidence_enriched_v1_gated.jsonl`

**Process**:
1. Load all coverages
2. Build CompareRow for each coverage
3. Sort by comparison_key (anchored first, then by code/title)
4. Bundle into CompareTable

### 2. Multi-Insurer Table (Future)

**Input**: Multiple Step3 gated files (e.g., KB + Meritz)

**Process**:
1. Load coverages from all insurers
2. Build CompareRow for each
3. **Group by comparison_key** (coverage_code match)
4. For unmatched coverages, create separate rows
5. Sort and bundle into CompareTable

**Alignment**:
- Same `coverage_code` → same row group
- No `coverage_code` → separate unanchored section

---

## 구현 (Implementation)

### 모듈 구조

```
pipeline/step4_compare_model/
├── __init__.py
├── model.py          # Dataclasses (CompareRow, CompareTable, SlotValue, etc.)
├── builder.py        # Row/table builders
└── run.py            # CLI entry point
```

### 모델 정의 (model.py)

**Dataclasses**:
- `EvidenceReference`: Single evidence entry
- `SlotValue`: Slot value with status + evidences
- `CoverageIdentity`: Coverage identity (insurer/product/variant/code/title)
- `CoverageSemantics`: Step1 semantics (optional)
- `CompareRow`: Single coverage comparison row
- `CompareTable`: Multi-coverage comparison table

**Utilities**:
- `extract_coverage_code(coverage_name_raw)`: Extract code from name
- `extract_coverage_title(coverage_name_raw)`: Extract clean title
- `normalize_coverage_title(title)`: Normalize for comparison

### 빌더 로직 (builder.py)

**CompareRowBuilder**:
- `build_row(step3_coverage)`: Step3 coverage → CompareRow
- `_build_identity()`: Extract identity fields
- `_build_semantics()`: Extract semantics from Step1
- `_build_slots()`: Build all 6 slots with evidences
- `_build_renewal_condition()`: Extract renewal info
- `_calculate_status_summary()`: Count slot statuses
- `_has_conflict()`: Check for CONFLICT status

**CompareTableBuilder**:
- `build_table(rows)`: Build CompareTable from rows
- `_sort_rows_for_comparison()`: Sort by anchoring + code/title
- `_calculate_unknown_rate()`: Calculate UNKNOWN percentage
- `_generate_warnings()`: Generate quality warnings

**CompareBuilder** (High-level):
- `build_from_step3_files(files, output_dir)`: End-to-end builder
- Loads Step3 gated files
- Builds rows and tables
- Writes to `compare_rows_v1.jsonl` and `compare_tables_v1.jsonl`

### CLI (run.py)

```bash
# Single insurer
python -m pipeline.step4_compare_model.run --insurers kb

# Multiple insurers (future)
python -m pipeline.step4_compare_model.run --insurers kb meritz
```

**Output**:
- `data/compare_v1/compare_rows_v1.jsonl`
- `data/compare_v1/compare_tables_v1.jsonl`

---

## 실행 결과 (Execution Results)

### KB Single-Insurer Test

```bash
python3 -m pipeline.step4_compare_model.run --insurers kb
```

**Output**:
```
[STEP NEXT-68] Coverage Comparison Model Builder
[Insurers] kb
[Input Dir] data/scope_v3
[Output Dir] data/compare_v1

Found: kb_step3_evidence_enriched_v1_gated.jsonl

[Results]
  Rows file: data/compare_v1/compare_rows_v1.jsonl
  Tables file: data/compare_v1/compare_tables_v1.jsonl

[Stats]
  Total rows: 60
  Insurers: kb
  Total coverages in table: 60
  Conflicts: 10
  Unknown rate: 0.0%

[Warnings]
  - CONFLICT detected in 10 coverages (문서 불일치)
  - 21 coverages without coverage_code (정렬 제한)
```

✅ **DoD 달성**: 60 coverages → 60 rows

---

## 샘플 검증 (Sample Verification)

### 1. 일반상해사망 (Basic Coverage)

**Identity**:
- Code: `1`
- Title: `일반상해사망`

**Slot Status**: All 6 slots = FOUND

**Key Slots (with evidence)**:
- `exclusions`: FOUND (3 evidences)
  - 가입설계서 p4 [FOUND]
- `payout_limit`: FOUND (3 evidences)
  - 가입설계서 p4 [FOUND]
- `reduction`: FOUND (3 evidences)
  - 약관 p105 [FOUND]

✅ **검증**: Evidence links present

---

### 2. 암진단비(유사암제외)

**Identity**:
- Code: `70`
- Title: `암진단비`

**Slot Status**: All 6 slots = FOUND

**Key Slots (with evidence)**:
- `exclusions`: FOUND (3 evidences)
  - 가입설계서 p4 [FOUND]
- `payout_limit`: FOUND (3 evidences)
  - 가입설계서 p4 [FOUND]
- `reduction`: FOUND (3 evidences)
  - 가입설계서 p4 [FOUND]

✅ **검증**: Evidence links present

---

### 3. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)

**Identity**:
- Code: `206`
- Title: `다빈치로봇 암수술비`

**Slot Status**:
- FOUND: 4 slots
- FOUND_GLOBAL: 2 slots (entry_age, waiting_period)

**Semantics (preserved from Step1)**:
```json
{
  "exclusions": ["갑상선암", "전립선암"],
  "payout_limit_count": 1,
  "renewal_flag": true
}
```

**Key Slots (with evidence)**:
- `exclusions`: FOUND (3 evidences)
  - 가입설계서 p6 [FOUND]
- `payout_limit`: FOUND (3 evidences)
  - 약관 p6 [FOUND]
- `reduction`: FOUND (3 evidences)
  - 약관 p30 [FOUND]

✅ **검증**: Evidence links present + Step1 semantics preserved

---

## 절대 준수 사항 (Constitution)

### ✅ 허용 (Allowed)

- Deterministic pattern matching
- Evidence reference extraction
- Status propagation from Step3 gates
- Coverage code/title normalization
- Comparison key generation

### ❌ 금지 (Forbidden)

- ❌ LLM usage: 없음
- ❌ Vector search: 없음
- ❌ Inference: 없음
- ❌ Evidence 없이 value 생성: 없음
- ❌ Slot status 재해석: 없음 (Step3 gate 결과 그대로 사용)
- ❌ Step1~Step3 수정: 없음
- ❌ "추천/종합의견" 생성: 없음 (NEXT-69)
- ❌ 보험료 포함: 없음 (요구사항 제외)

---

## Definition of Done (DoD)

### ✅ KB 단독 검증

- [x] Input: 60 coverages (Step3 gated)
- [x] Output: 60 rows (compare_rows_v1.jsonl)
- [x] 각 row는 6 슬롯 모두 존재
- [x] 샘플 3개 담보 검증:
  - [x] 다빈치로봇 암수술비: evidence links 존재
  - [x] 암진단비: evidence links 존재
  - [x] 일반상해사망: evidence links 존재
- [x] CONFLICT 10건이 table_warnings에 노출됨

### 🔄 Multi-Insurer (미완료, 차기 작업)

- [ ] KB + Meritz Step3 gated files 준비 필요
- [ ] coverage_code 기준 정렬/정합 검증
- [ ] FOUND_GLOBAL이 "공통 규정"으로 표시됨

**Note**: Meritz는 Step3 gated file 미생성. Step2 미완료로 인해 Step3 실행 불가.
Multi-insurer comparison은 Meritz Step3 완료 후 테스트 가능.

---

## CLI Usage

### Single Insurer

```bash
python3 -m pipeline.step4_compare_model.run --insurers kb
```

### Multiple Insurers (when ready)

```bash
python3 -m pipeline.step4_compare_model.run --insurers kb meritz
```

### Custom Paths

```bash
python3 -m pipeline.step4_compare_model.run \
  --insurers kb \
  --input-dir data/scope_v3 \
  --output-dir data/compare_v1
```

---

## 산출물 (Deliverables)

### Code

- ✅ `pipeline/step4_compare_model/__init__.py`
- ✅ `pipeline/step4_compare_model/model.py` (231 lines)
- ✅ `pipeline/step4_compare_model/builder.py` (303 lines)
- ✅ `pipeline/step4_compare_model/run.py` (89 lines)

**Total**: ~623 lines

### Data

- ✅ `data/compare_v1/compare_rows_v1.jsonl` (60 rows)
- ✅ `data/compare_v1/compare_tables_v1.jsonl` (1 table)

### Documentation

- ✅ `docs/audit/STEP_NEXT_68_COMPARE_MODEL.md` (this file)

---

## 제약 사항 (Constraints)

### What This Does

1. ✅ Convert Step3 gated output → comparison rows
2. ✅ Extract evidence references to slots
3. ✅ Preserve Step1 semantics (optional)
4. ✅ Generate comparison tables with quality warnings
5. ✅ Sort by coverage_code (anchored first)

### What This Does NOT Do

1. ❌ **Normalize values**: Values are passed through as-is from Step3
2. ❌ **Infer missing data**: No LLM, no inference
3. ❌ **Recommend products**: Comparison only (NEXT-69)
4. ❌ **Include pricing**: Out of scope
5. ❌ **Cross-reference mappings**: Uses Step3 output only

---

## 다음 단계 (Next Steps)

### STEP NEXT-69 (Out of Scope)

- Comparison UI/API layer
- Coverage recommendation engine
- Pricing integration
- User query handling

### 개선 사항 (Future Improvements)

1. **Value normalization**:
   - Parse "90일" → `{"value": 90, "unit": "days"}`
   - Parse "1천만원" → `{"value": 10000000, "unit": "KRW"}`

2. **Coverage alignment**:
   - Fuzzy matching for coverage titles (when code missing)
   - Cross-insurer coverage mapping

3. **Evidence quality scoring**:
   - Confidence scores for evidences
   - FOUND vs FOUND_GLOBAL weighting

4. **Table filtering**:
   - Filter by slot status (e.g., only FOUND)
   - Filter by coverage type

---

## 결론 (Conclusion)

**STEP NEXT-68 완료**: Coverage Comparison Model successfully implemented and validated.

### Key Achievements

1. ✅ **Evidence-first comparison**: All values linked to Step3 evidences
2. ✅ **Deterministic only**: No LLM, no inference, no guessing
3. ✅ **60 coverages → 60 rows**: KB single-insurer test passed
4. ✅ **6 slots per row**: start_date, exclusions, payout_limit, reduction, entry_age, waiting_period
5. ✅ **Sample verification**: da Vinci, 암진단비, 상해사망 all have evidence links
6. ✅ **Quality warnings**: CONFLICT detection and table warnings

### Coverage Rate (KB)

| Metric | Value |
|--------|-------|
| Total rows | 60 |
| Conflicts | 10 (16.7%) |
| Unknown rate | 0.0% |
| Anchored (with code) | 39 (65%) |
| Unanchored (no code) | 21 (35%) |

### Model Quality

- **Evidence integrity**: ✅ All slot values have evidence references
- **Status preservation**: ✅ FOUND/FOUND_GLOBAL/CONFLICT from Step3 gates
- **Semantics preservation**: ✅ Step1 semantics (exclusions, payout_limit, renewal) preserved
- **Determinism**: ✅ Same input → same output

---

**End of STEP NEXT-68**
