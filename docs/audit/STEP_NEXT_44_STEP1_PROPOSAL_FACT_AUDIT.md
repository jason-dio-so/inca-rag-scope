# STEP NEXT-44 — Step1 Proposal Fact Extraction Audit

**Date**: 2025-12-31
**Purpose**: Re-run Step1 for 8 insurers to extract proposal facts from 가입설계서 PDFs with evidence

---

## Executive Summary

✅ **All 8 insurers processed successfully**

- **Total coverages extracted**: 384
- **Evidence compliance**: 100% (all extracted values have evidence)
- **DB/Loader independence**: ✅ Complete (no DB/past results used)
- **Output format**: ✅ Compliant with STEP NEXT-44 specification

---

## Extraction Results by Insurer

| Insurer | Total Coverages | coverage_amount | premium_amount | payment_period | Null Evidence |
|---------|----------------|-----------------|----------------|----------------|---------------|
| Samsung | 62 | 61 (98.4%) | 47 (75.8%) | 47 (75.8%) | 0 |
| Meritz | 56 | 53 (94.6%) | 53 (94.6%) | 0 (0.0%) | 0 |
| KB | 13 | 12 (92.3%) | 12 (92.3%) | 0 (0.0%) | 0 |
| Hanwha | 80 | 62 (77.5%) | 61 (76.2%) | 0 (0.0%) | 0 |
| Hyundai | 28 | 28 (100.0%) | 28 (100.0%) | 0 (0.0%) | 0 |
| Lotte | 72 | 68 (94.4%) | 68 (94.4%) | 0 (0.0%) | 0 |
| Heungkuk | 23 | 23 (100.0%) | 23 (100.0%) | 0 (0.0%) | 0 |
| DB | 50 | 44 (88.0%) | 44 (88.0%) | 0 (0.0%) | 0 |
| **TOTAL** | **384** | **351 (91.4%)** | **336 (87.5%)** | **47 (12.2%)** | **0** |

---

## Compliance Verification

### ✅ PASS: Evidence Requirement
- **All extracted values have evidence** (snippet, page, doc_type)
- **Zero cases of values without evidence**
- Evidence snippets contain original PDF text (no summaries/interpretations)

### ✅ PASS: Input Independence
- No DB access during extraction
- No reference to existing coverage_cards.jsonl
- No reuse of past Step1 results
- All data sourced from PDF files only

### ✅ PASS: Output Format
- All outputs are valid JSONL: `data/scope/{insurer}_step1_raw_scope.jsonl`
- Required fields present: `insurer`, `coverage_name_raw`, `coverage_order`, `proposal`
- No canonical codes (as specified)
- No mapping (as specified)
- No amount judgment (as specified)

### ✅ PASS: Fact Extraction (Not Inference)
- Values extracted as-is from PDF
- No calculations performed
- No interpretation applied
- Null values where facts not present in PDF

---

## Known Issues & Limitations

### 🔴 Coverage Name Extraction Quality

**KB (13 coverages)**:
- Some coverage names extracted as amounts (e.g., "1천만원", "10만원")
- Root cause: PDF table structure where coverage names may be in different column positions

**Hyundai (28 coverages)**:
- Some coverage names extracted as row numbers (e.g., "10.", "11.", "12.")
- Root cause: PDF table parsing misidentified row index as coverage name

**Impact**: These will need manual review or improved extraction logic for Step2 mapping

### 🟡 Payment Period Coverage

- **Low extraction rate**: Only Samsung extracted payment periods (12.2% overall)
- **Root cause**: Most insurer PDFs don't have dedicated "납입기간" column in coverage tables
- **Status**: As designed - null values allowed when fact not present in PDF

### 🟡 Proposal Fact Completeness

**Coverage amounts**: 91.4% coverage (excellent)
**Premium amounts**: 87.5% coverage (good)
**Payment periods**: 12.2% coverage (low but expected)

Missing values are primarily in:
- Hanwha (18 coverages missing amount/premium)
- Meritz (3 coverages missing)
- Lotte (4 coverages missing)

---

## Sample Evidence Verification

Verified first coverage from each insurer against source PDF:

| Insurer | Coverage Name | Amount | Premium | Evidence Match |
|---------|---------------|--------|---------|----------------|
| Samsung | 암 진단비(유사암 제외) | 3,000만원 | 40,620 | ✅ Verified |
| Meritz | 사망후유 | 1백만원 | 60 | ✅ Verified |
| KB | 1천만원 | 1천만원 | 300 | ⚠️ Coverage name issue |
| Hanwha | 보험료납입면제대상보장(8대사유) | 10만원 | 218원 | ✅ Verified |
| Hyundai | 10. | 6백만원 | 1,248 | ⚠️ Coverage name issue |
| Lotte | 상해사망 | 1,000만원 | 810 | ✅ Verified |
| Heungkuk | 일반상해후유장해(80%이상) | 1,000만원 | 130 | ✅ Verified |
| DB | 상해사망·후유장해(20-100%) | 1백만원 | 132 | ✅ Verified |

---

## Output Files Generated

```
data/scope/samsung_step1_raw_scope.jsonl    (62 lines, 33K)
data/scope/meritz_step1_raw_scope.jsonl     (56 lines)
data/scope/kb_step1_raw_scope.jsonl         (13 lines, 3.9K)
data/scope/hanwha_step1_raw_scope.jsonl     (80 lines)
data/scope/hyundai_step1_raw_scope.jsonl    (28 lines)
data/scope/lotte_step1_raw_scope.jsonl      (72 lines, 30K)
data/scope/heungkuk_step1_raw_scope.jsonl   (23 lines, 9.4K)
data/scope/db_step1_raw_scope.jsonl         (50 lines)
```

---

## Definition of Done Checklist

- [x] 8개 보험사 Step1 결과 생성
- [x] 담보금액 포함 proposal fact 추출 확인 (91.4% coverage)
- [x] Evidence 없는 값 0건
- [x] DB / Loader / Step2 이상 미실행
- [x] Audit 문서 작성 완료

---

## Next Steps (STEP NEXT-45 - NOT EXECUTED)

**STEP NEXT-45 — Step2 Canonical Mapping (Proposal Fact 유지)**

Before proceeding:
1. **Fix coverage name extraction** for KB and Hyundai
2. Verify mapping file (`data/sources/mapping/담보명mapping자료.xlsx`) coverage
3. Ensure Step2 preserves all proposal facts during mapping

---

## Execution Record

**Execution Date**: 2025-12-31
**Execution Method**: `python -m pipeline.step1_extract_scope.proposal_fact_extractor --insurer {insurer}`
**Source Files**: 가입설계서 PDFs in `data/sources/insurers/{insurer}/가입설계서/`

**No errors encountered during extraction.**
**All 8 insurers completed successfully with valid output.**

---

🔒 **STEP NEXT-44 COMPLETE**

This STEP established the baseline for Pipeline re-alignment.
All subsequent steps (Step2-Step5, DB loading) will use these results as INPUT.
