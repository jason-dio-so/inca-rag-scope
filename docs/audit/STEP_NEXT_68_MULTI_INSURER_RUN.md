# STEP NEXT-68: Multi-Insurer Comparison Validation

**Date**: 2026-01-08
**Status**: ✅ COMPLETED
**Insurers**: 6 (KB, SAMSUNG, Hanwha, Heungkuk, Hyundai, Meritz)

---

## 목표 (Objective)

Step3 gated output from multiple insurers → unified comparison table.

---

## 실행 결과 (Execution Results)

### Command

```bash
python3 -m pipeline.step4_compare_model.run \
  --insurers kb SAMSUNG hanwha heungkuk hyundai meritz
```

### Output

```
[STEP NEXT-68] Coverage Comparison Model Builder
[Insurers] kb, SAMSUNG, hanwha, heungkuk, hyundai, meritz

Found: kb_step3_evidence_enriched_v1_gated.jsonl
Found: SAMSUNG_step3_evidence_enriched_v1_gated.jsonl
Found: hanwha_step3_evidence_enriched_v1_gated.jsonl
Found: heungkuk_step3_evidence_enriched_v1_gated.jsonl
Found: hyundai_step3_evidence_enriched_v1_gated.jsonl
Found: meritz_step3_evidence_enriched_v1_gated.jsonl

[Results]
  Rows file: data/compare_v1/compare_rows_v1.jsonl
  Tables file: data/compare_v1/compare_tables_v1.jsonl

[Stats]
  Total rows: 245
  Insurers: kb, samsung, hanwha, heungkuk, hyundai, meritz
  Total coverages in table: 245
  Conflicts: 72
  Unknown rate: 0.0%

[Warnings]
  - CONFLICT detected in 72 coverages (문서 불일치)
  - 169 coverages without coverage_code (정렬 제한)
```

### Summary Stats

| Metric | Value | Notes |
|--------|-------|-------|
| Total rows | 245 | Sum of all insurer coverages |
| Insurers | 6 | kb, samsung, hanwha, heungkuk, hyundai, meritz |
| Conflicts | 72 (29.4%) | Coverages with at least 1 CONFLICT slot |
| Unknown rate | 0.0% | No UNKNOWN slots |
| Anchored | 76 (31.0%) | Coverages with coverage_code |
| Unanchored | 169 (69.0%) | No coverage_code (정렬 제한) |

---

## Conflict Analysis

### Top 10 CONFLICT Samples

| # | Insurer | Coverage | Conflict Slots | Example Conflict |
|---|---------|----------|----------------|------------------|
| 1 | hyundai | 상해입원일당 | 2 (reduction, entry_age) | reduction: 가입설계서 vs 상품요약서 값 불일치 |
| 2 | hyundai | 뇌출혈진단담보 | 2 (payout_limit, reduction) | payout_limit: 가입설계서/사업방법서/약관 값 상이 |
| 3 | hyundai | 뇌졸중진단담보 | 2 (reduction, entry_age) | reduction: 상품요약서 vs 약관 |
| 4 | hyundai | 담보명 | 2 (entry_age, waiting_period) | entry_age: 사업방법서 vs 약관 |
| 5 | meritz | 5대고액치료비암진단비 | 2 (payout_limit, entry_age) | payout_limit: 가입설계서 vs 약관 |
| 6 | meritz | 뇌졸중진단비 | 2 (reduction, entry_age) | reduction: 상품요약서 vs 가입설계서 |
| 7 | meritz | 허혈성심장질환진단비 | 2 (reduction, entry_age) | reduction: 상품요약서 vs 가입설계서 |
| 8 | kb | 일반상해후유장해 | 1 (entry_age) | entry_age: 가입설계서/사업방법서/약관 값 상이 |
| 9 | kb | 질병사망 | 1 (entry_age) | entry_age: 가입설계서 vs 사업방법서 |
| 10 | kb | 뇌혈관질환진단비 | 1 (payout_limit) | payout_limit: 가입설계서 vs 약관 |

### Conflict Distribution by Insurer

| Insurer | Coverages with Conflicts | Conflict Rate | Most Common Conflict Slots |
|---------|--------------------------|---------------|---------------------------|
| **Meritz** | 31 | 83.8% | reduction, entry_age |
| **Hyundai** | 12 | 25.5% | reduction, entry_age, payout_limit |
| **Heungkuk** | 11 | 30.6% | reduction, entry_age |
| **KB** | 10 | 16.7% | entry_age, payout_limit |
| **Hanwha** | 5 | 15.2% | reduction, payout_limit |
| **SAMSUNG** | 3 | 9.4% | entry_age |

### Conflict Insights

1. **Most Conflict-Prone Insurer**: Meritz (83.8% conflict rate)
   - Document inconsistencies across 가입설계서/상품요약서/약관
   - Requires manual review

2. **Most Conflict-Prone Slots**:
   - `reduction` (감액기간/비율): Часто 문서별 상이
   - `entry_age` (가입나이): 문서 간 값 차이
   - `payout_limit` (지급한도): 복수 문서에서 다른 값 추출

3. **Least Conflict-Prone Slots**:
   - `start_date` (보장개시일): 일관성 높음
   - `exclusions` (면책사항): 대체로 일치
   - `waiting_period`: 상대적으로 충돌 적음

---

## Anchoring Analysis

### Coverage Code Distribution

| Category | Count | Percentage | Notes |
|----------|-------|------------|-------|
| **Anchored** (code 있음) | 76 | 31.0% | 코드 기준 정렬 가능 |
| **Unanchored** (code 없음) | 169 | 69.0% | Title 기준 정렬 (제한적) |

### Implications

- **Cross-insurer alignment**: Only 31% can be aligned by coverage_code
- **69% unanchored**: Requires title-based matching (less reliable)
- **Future work**: Implement fuzzy matching for unanchored coverages

---

## DoD Verification

### ✅ 모든 조건 충족

- [x] compare_rows_v1.jsonl: 245 rows (insurer별 합계 일치)
- [x] compare_tables_v1.jsonl: 1 table (6 insurers)
- [x] Anchored 비율 리포트: 31.0% (76/245)
- [x] Top 10 CONFLICT 샘플 출력: ✅
- [x] Evidence links 포함: ✅ (모든 row에 evidences[] 존재)

---

## 산출물 (Deliverables)

### Data Files

- ✅ `data/compare_v1/compare_rows_v1.jsonl` (245 rows)
- ✅ `data/compare_v1/compare_tables_v1.jsonl` (1 table)

### Documentation

- ✅ `docs/audit/STEP_NEXT_68_MULTI_INSURER_RUN.md` (this file)
- ✅ `docs/audit/STEP_NEXT_69_ALL_INSURERS_STEP3_GATE.md`

---

## 결론 (Conclusion)

**Multi-Insurer Comparison 검증 완료**: 6 insurers, 245 coverages successfully compared.

### Key Achievements

1. ✅ **245 rows generated**: All insurer coverages included
2. ✅ **Evidence-first**: All slot values linked to Step3 evidences
3. ✅ **Conflict detection**: 72 coverages flagged for manual review
4. ✅ **Anchoring analysis**: 31% anchored, 69% unanchored
5. ✅ **Deterministic**: No LLM, no inference

### Known Limitations

1. **Low anchoring rate** (31%): Limits cross-insurer alignment
2. **High Meritz conflicts** (83.8%): Document quality issue
3. **Unanchored coverages**: Cannot reliably match across insurers

### Recommendations

1. **Meritz review**: Manual verification of 31 conflict coverages
2. **Fuzzy matching**: Implement for unanchored coverage alignment
3. **Document standardization**: Work with insurers to improve consistency

---

**End of STEP NEXT-68 Multi-Insurer Validation**
