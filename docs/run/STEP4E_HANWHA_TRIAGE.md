# STEP 4-ε Hanwha Evidence Failure Triage

Generated: 2025-12-27

## Input Files Status

| file | lines | status |
|------|-------|--------|
| data/scope/hanwha_scope.csv | 38 | EXISTS |
| data/scope/hanwha_scope_mapped.csv | 38 | EXISTS |
| data/evidence_sources/hanwha_manifest.csv | 4 | EXISTS |
| data/evidence_pack/hanwha_evidence_pack.jsonl | 37 | EXISTS |
| data/evidence_text/hanwha/*.page.jsonl | 3 files | EXISTS |

## Manifest ↔ PDF Verification

| doc_type | pdf_path | exists |
|----------|----------|--------|
| 약관 | data/sources/insurers/hanwha/약관/한화_약관.pdf | YES |
| 사업방법서 | data/sources/insurers/hanwha/사업방법서/한화_사업방법서.pdf | YES |
| 상품요약서 | data/sources/insurers/hanwha/상품요약서/한화_상품요약서.pdf | YES |

## Text Extraction Quality

| doc_type | pages | total_chars | 암 | 진단 | 지급 | 보험금 |
|----------|-------|-------------|-----|------|------|--------|
| 약관 | 1065 | 1,621,573 | 6873 | 3493 | 6853 | 3902 |
| 사업방법서 | 341 | 479,390 | 2793 | 1002 | 716 | 361 |
| 상품요약서 | 96 | 144,476 | 2435 | 861 | 596 | 59 |

**Conclusion**: Text extraction is successful. Keywords present in all doc types.

## Failed Cases Analysis

Total evidence_pack entries: 37
- Success (evidences > 0): 9
- Failed (evidences = 0): 28
  - Matched but failed: 17
  - Unmatched (expected): 11

### Sample 5 Failed Cases (Matched)

| # | coverage_name_raw | coverage_code | canonical | search_keywords |
|---|-------------------|---------------|-----------|-----------------|
| 1 | 유사암(8대) 진단비 | A4210_2 | 유사암(8대)진단비 | ['유사암(8대)진단비', '유사암(8대) 진단비'] |
| 2 | 암 진단비(유사암 제외) | A4200_1 | 암진단비(유사암제외) | ['암진단비(유사암제외)', '암 진단비(유사암 제외)'] |
| 3 | 암(4대특정암 제외) 진단비 | A4200_2 | 암(4대특정암제외)진단비 | ['암(4대특정암제외)진단비', '암(4대특정암 제외) 진단비'] |
| 4 | 4대특정암 진단비 | A4209_2 | 4대특정암진단비 | ['4대특정암진단비', '4대특정암 진단비'] |
| 5 | 4대특정암 진단비(제자리암) | A4209_3 | 4대특정암진단비(제자리암) | ['4대특정암진단비(제자리암)', '4대특정암 진단비(제자리암)'] |

### Normalized Keyword Match Test

| search_keyword (normalized) | 약관 | 사업방법서 | 상품요약서 |
|-----------------------------|------|-----------|-----------|
| 유사암(8대)진단비 | 0 | 0 | 0 |
| 암진단비(유사암제외) | 0 | 0 | 0 |
| 4대특정암진단비 | 0 | 0 | 0 |

### Actual Patterns in Hanwha Text

Sample cancer coverage names found in hanwha 약관:
- `4대유사암제외)진단비`
- `전이암진단비`
- `통합암(4대유사암제외)진단비`
- `통합전이암진단비`
- `특정유사암진단후`

**KEY FINDING**: hanwha uses different terminology:
- Search: `유사암(8대)진단비` → Actual: `4대유사암진단비` or `4대유사암제외)진단비`
- Search: `4대특정암진단비` → Not found (may use `특정암` or other variants)

## Root Cause Classification

| category | condition | evidence |
|----------|-----------|----------|
| **B** | text_present_keyword_mismatch | Search keywords: `유사암(8대)진단비`, `4대특정암진단비`, `암진단비(유사암제외)` normalized to 0 matches. Actual patterns in text: `4대유사암`, `통합암(4대유사암제외)`, `특정유사암`. Text extraction OK (1065 pages, 1.6M chars in 약관, keywords '암':6873, '진단':3493). 17/28 failed cases are matched coverages. **Diagnosis**: hanwha-specific terminology mismatch in canonical mapping or search query generation. |

## Conclusion

**Root Cause**: **B (text_present_keyword_mismatch)**

Evidence summary:
- PDFs exist: 3/3
- Text extracted: 1502 pages, 2.2M chars
- Keywords present: 암(12101), 진단(5356)
- Search keywords: 0 matches (normalized)
- Actual patterns: different terminology (4대유사암, 통합암, etc.)

**Next Step**: Requires query variant generation for hanwha (similar to hyundai) OR canonical mapping review in `담보명mapping자료.xlsx` to match hanwha's actual terminology.
