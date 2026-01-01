# Run Summary: 2025-12-31T181145Z

**Generated**: 2025-12-31T181145Z

---

## Pipeline Execution Counts

| Insurer  | Step1 Raw | Step2-a Sanitized | Step2-b Total | Step2-b Mapped | Step2-b Unmapped | Mapping Rate |
|----------|-----------|-------------------|---------------|----------------|------------------|-------------|
| samsung  |         8 |                61 |            61 |             52 |                9 | 85.2%       |
| hyundai  |        37 |                34 |            34 |             23 |               11 | 67.6%       |
| lotte    |        30 |                64 |            64 |             21 |               43 | 32.8%       |
| db       |        31 |                48 |            48 |              0 |               48 | 0.0%        |
| kb       |        50 |                36 |            36 |             24 |               12 | 66.7%       |
| meritz   |        36 |                36 |            36 |              6 |               30 | 16.7%       |
| hanwha   |        33 |                34 |            34 |             27 |                7 | 79.4%       |
| heungkuk |        36 |                22 |            22 |             20 |                2 | 90.9%       |
| **TOTAL** | **    261** | **            335** | **        335** | **         173** | **           162** | **51.6%    ** |

---

## Output Files

- `db_step1_raw_scope_v3.jsonl`
- `db_step2_canonical_scope_v1.jsonl`
- `db_step2_dropped.jsonl`
- `db_step2_mapping_report.jsonl`
- `db_step2_sanitized_scope_v1.jsonl`
- `hanwha_step1_raw_scope_v3.jsonl`
- `hanwha_step2_canonical_scope_v1.jsonl`
- `hanwha_step2_dropped.jsonl`
- `hanwha_step2_mapping_report.jsonl`
- `hanwha_step2_sanitized_scope_v1.jsonl`
- `heungkuk_step1_raw_scope_v3.jsonl`
- `heungkuk_step2_canonical_scope_v1.jsonl`
- `heungkuk_step2_dropped.jsonl`
- `heungkuk_step2_mapping_report.jsonl`
- `heungkuk_step2_sanitized_scope_v1.jsonl`
- `hyundai_step1_raw_scope_v3.jsonl`
- `hyundai_step2_canonical_scope_v1.jsonl`
- `hyundai_step2_dropped.jsonl`
- `hyundai_step2_mapping_report.jsonl`
- `hyundai_step2_sanitized_scope_v1.jsonl`
- `kb_step1_raw_scope_v3.jsonl`
- `kb_step2_canonical_scope_v1.jsonl`
- `kb_step2_dropped.jsonl`
- `kb_step2_mapping_report.jsonl`
- `kb_step2_sanitized_scope_v1.jsonl`
- `lotte_step1_raw_scope_v3.jsonl`
- `lotte_step2_canonical_scope_v1.jsonl`
- `lotte_step2_dropped.jsonl`
- `lotte_step2_mapping_report.jsonl`
- `lotte_step2_sanitized_scope_v1.jsonl`
- `meritz_step1_raw_scope_v3.jsonl`
- `meritz_step2_canonical_scope_v1.jsonl`
- `meritz_step2_dropped.jsonl`
- `meritz_step2_mapping_report.jsonl`
- `meritz_step2_sanitized_scope_v1.jsonl`
- `samsung_step1_raw_scope_v3.jsonl`
- `samsung_step2_canonical_scope_v1.jsonl`
- `samsung_step2_dropped.jsonl`
- `samsung_step2_mapping_report.jsonl`
- `samsung_step2_sanitized_scope_v1.jsonl`

---

## Pipeline Stages

**Step1**: Raw scope extraction (v3)
**Step2-a**: Sanitization (fragment/noise removal)
**Step2-b**: Canonical mapping (신정원 통일코드)
