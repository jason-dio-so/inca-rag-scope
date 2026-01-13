# Q11 Fact Snapshot

**Document Type:** Fact Record (Raw Outputs)
**Date:** 2026-01-13
**Status:** IMMUTABLE
**Phase:** STEP NEXT-Q11-FREEZE-γ

---

## Purpose

Record raw evidence from Step3 and compare_tables_v1 to establish the factual foundation for Q11 (A6200) UNKNOWN status.

**Core Finding:** Step3 evidence_pack is empty (length=0) for all A6200 records, meaning Step3 found NO coverage-level evidence in 4 documents (가입설계서/상품요약서/사업방법서/약관).

---

## Command 1: Step3 Evidence Pack Status for A6200

**Command:**
```bash
python3 gather_q11_facts.py
```

**Output:**
```
================================================================================
Q11 FACT GATHERING - Step3 Evidence Pack Status for A6200
================================================================================

==== heungkuk ====
{"coverage_code": "A6200", "coverage_name_raw": "암직접치료입원비(요양병원제외)(1일-180일)", "evidence_pack_len": 0, "slots": {"duration_limit_days": {"status": null, "value": null}, "daily_benefit_amount_won": {"status": null, "value": null}}}

==== hyundai ====
{"coverage_code": "A6200", "coverage_name_raw": "29. 암직접치료입원일당(1-180일,요양병원제외)담보", "evidence_pack_len": 0, "slots": {"duration_limit_days": {"status": null, "value": null}, "daily_benefit_amount_won": {"status": null, "value": null}}}

==== meritz ====
{"coverage_code": "A6200", "coverage_name_raw": "암직접치료입원일당(Ⅱ)(요양병원제외, 1일이상)", "evidence_pack_len": 0, "slots": {"duration_limit_days": {"status": null, "value": null}, "daily_benefit_amount_won": {"status": null, "value": null}}}

==== db_over41 ====
{"coverage_code": "A6200", "coverage_name_raw": "18. 암직접치료입원일당Ⅱ(요양병원제외)(1일이상180일한도)", "evidence_pack_len": 0, "slots": {"duration_limit_days": {"status": null, "value": null}, "daily_benefit_amount_won": {"status": null, "value": null}}}

==== db_under40 ====
{"coverage_code": "A6200", "coverage_name_raw": "18. 암직접치료입원일당Ⅱ(요양병원제외)(1일이상180일한도)", "evidence_pack_len": 0, "slots": {"duration_limit_days": {"status": null, "value": null}, "daily_benefit_amount_won": {"status": null, "value": null}}}

================================================================================
CONCLUSION
================================================================================
A6200에 대해 (heungkuk/hyundai/meritz/db)의 Step3 evidence_pack이 빈 배열(len=0)임을 확인했다.
이는 Step3에서 4개 문서(가입설계서/상품요약서/사업방법서/약관)를 검색했으나
A6200 coverage-level evidence를 찾지 못했음을 의미한다.
```

---

## Command 2: A6200 Rows in compare_tables_v1.jsonl

**Command:**
```bash
jq -r '.coverage_rows[] | select(.identity.coverage_code=="A6200") | .identity.insurer_key' \
  data/compare_v1/compare_tables_v1.jsonl | sort | uniq -c
```

**Output:**
```
   2 db
   1 heungkuk
   1 hyundai
   1 kb
   1 meritz
   1 samsung
```

**Analysis:**
- Total: 7 rows (6 insurers)
- db appears 2x (db_over41, db_under40 variants)
- kb and samsung have A6200 rows WITH values (KB: 10,000/180일, Samsung: 100,000/30일)
- heungkuk, hyundai, meritz, db have A6200 rows but Step3 evidence_pack was empty

---

## Command 3: Available Step3 Gated Files

**Command:**
```bash
ls -1 data/scope_v3/*_step3_evidence_enriched_v1_gated.jsonl | xargs -I {} basename {}
```

**Output:**
```
db_over41_step3_evidence_enriched_v1_gated.jsonl
db_under40_step3_evidence_enriched_v1_gated.jsonl
hanwha_step3_evidence_enriched_v1_gated.jsonl
heungkuk_step3_evidence_enriched_v1_gated.jsonl
hyundai_step3_evidence_enriched_v1_gated.jsonl
kb_step3_evidence_enriched_v1_gated.jsonl
lotte_female_step3_evidence_enriched_v1_gated.jsonl
lotte_male_step3_evidence_enriched_v1_gated.jsonl
meritz_step3_evidence_enriched_v1_gated.jsonl
SAMSUNG_step3_evidence_enriched_v1_gated.jsonl
```

---

## Fact Summary

### Step3 Evidence Pack Status (A6200)

| Insurer | evidence_pack_len | duration status | daily status | coverage_name_raw contains period |
|---------|-------------------|-----------------|--------------|----------------------------------|
| heungkuk | 0 | null | null | YES (1일-180일) |
| hyundai | 0 | null | null | YES (1-180일) |
| meritz | 0 | null | null | NO (1일이상 only) |
| db_over41 | 0 | null | null | YES (1일이상180일한도) |
| db_under40 | 0 | null | null | YES (1일이상180일한도) |
| kb | (not checked) | (varies) | (varies) | YES (1일이상180일한도) |
| samsung | (not checked) | (varies) | (varies) | YES (1-180일) |

### Key Observation

**Heungkuk/Hyundai/DB coverage_name_raw contains period information (e.g., "1일-180일", "180일한도") BUT Step3 evidence_pack is empty.**

This means:
1. Step3 pattern matching did NOT extract coverage-level evidence from 4 documents
2. compare_tables_v1 shows these insurers have A6200 rows (with/without values)
3. If compare_tables_v1 has FOUND values for duration/daily, they came from **non-Step3 sources**:
   - Possible source: proposal_facts.coverage_amount_text
   - Possible source: coverage_name_raw parsing (NOT evidence-based)
   - Possible source: Step4 inference/backfill (VIOLATION of evidence-first)

---

## Evidence-First Principle Violation Detection

### compare_tables_v1 Analysis (from previous verification)

**From `q11_unknown_verification.py` output:**

| Insurer | compare_tables daily | compare_tables duration | Step3 evidence_pack |
|---------|---------------------|------------------------|---------------------|
| heungkuk | FOUND (20,000) | FOUND (null) | EMPTY (len=0) |
| hyundai | FOUND (100,000) | FOUND (null) | EMPTY (len=0) |
| meritz | FOUND (140,000) | FOUND (null) | EMPTY (len=0) |
| db | UNKNOWN (after decontamination) | FOUND (null) | EMPTY (len=0) |

**Conclusion:** compare_tables_v1 has FOUND status for daily_benefit even though Step3 evidence_pack is empty. This indicates values were backfilled from non-evidence sources (likely proposal_facts or coverage_name_raw).

---

## Compliance Check

### Evidence-First Principle (from SYSTEM_CONSTITUTION.md)

**Rule:** "근거 없으면 UNKNOWN. Evidence-First 원칙 엄수."

**Status for A6200:**
- Step3 evidence_pack = EMPTY (len=0)
- Expected: All slots should be UNKNOWN
- Actual: Some insurers have FOUND status in compare_tables_v1
- **Verdict:** VIOLATION (values backfilled without evidence)

---

## Conclusion

**A6200에 대해 (heungkuk/hyundai/meritz/db)의 Step3 evidence_pack이 빈 배열(len=0)임을 raw output으로 확인했다.**

This fact establishes:
1. Step3 found NO coverage-level evidence in 4 documents for A6200
2. Any FOUND values in compare_tables_v1 came from non-Step3 sources
3. Evidence-First principle requires: evidence_pack empty → slot status UNKNOWN
4. Q11 slots (duration_limit_days, daily_benefit_amount_won) must NOT be backfilled from other sources

---

**Related Documentation:**
- Policy: `docs/policy/Q11_COVERAGE_CODE_LOCK.md`
- Freeze Declaration: `docs/policy/Q11_FREEZE_DECLARATION.md`
- Decontamination Report: `docs/audit/Q11_DECONTAMINATION_REPORT_2026-01-13.md`
