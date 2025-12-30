# Step7 Amount Extraction - Multi-Insurer Audit Report

## Execution Summary
- Date: 2025-12-28
- Insurers processed: 8
- All executions: SUCCESS ✅

## Distribution Statistics

| Insurer | Total | PRIMARY | SECONDARY | UNCONFIRMED | Coverage % |
|---------|-------|---------|-----------|-------------|------------|
| samsung  |    41 |      41 |         0 |           0 |     100.0% |
| meritz   |    34 |      12 |         6 |          16 |      52.9% |
| db       |    30 |       8 |         6 |          16 |      46.7% |
| hanwha   |    37 |       4 |         0 |          33 |      10.8% |
| hyundai  |    37 |       8 |         0 |          29 |      21.6% |
| kb       |    45 |      10 |         0 |          35 |      22.2% |
| lotte    |    37 |      31 |         0 |           6 |      83.8% |
| heungkuk |    36 |      34 |         0 |           2 |      94.4% |

## Verification Results

### Amount Field Presence
✅ PASS: All 8 insurers have amount fields in all coverage cards

### Forbidden Pattern Check
✅ PASS: 0 violations detected across all insurers

### PRIMARY > 0 Check
✅ PASS: All insurers have at least 1 PRIMARY extraction

### Schema Consistency
✅ PASS: All amount objects follow the same schema:
- status: CONFIRMED | UNCONFIRMED
- value_text: amount only (no metadata)
- source_doc_type: 가입설계서 | 사업방법서 | 상품요약서 | 약관
- source_priority: PRIMARY | SECONDARY
- evidence_ref: {doc_type, source, snippet}

## Overall Result

**✅ STEP NEXT-10B-2C-2B: PASS**

All verification checks passed:
- 8/8 insurers executed successfully
- 297 total coverage cards processed
- 148 PRIMARY extractions (가입설계서)
- 12 SECONDARY extractions (사업방법서/상품요약서/약관)
- 137 UNCONFIRMED (expected - not all coverages have amounts in all docs)
- 0 forbidden pattern violations
- 100% schema consistency
