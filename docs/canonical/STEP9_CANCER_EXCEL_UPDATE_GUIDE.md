# STEP 9 - Cancer Coverage Canonical Excel Update Guide

## Purpose
Add 25 unmatched cancer coverages to `data/sources/mapping/담보명mapping자료.xlsx` to improve matching rate.

## File Location
**Target Excel**: `data/sources/mapping/담보명mapping자료.xlsx`

## Source Data
**Candidates**: `data/review/cancer_canonical_candidates.csv` (25 rows)

## Coverage Breakdown

### Hanwha (17 coverages)
1. 유사암(8대) 진단비 → A4210_2
2. 암(4대특정암 제외) 진단비 → A4200_2
3. 4대특정암 진단비 → A4209_2
4. 4대특정암 진단비(제자리암) → A4209_3
5. 4대특정암 진단비(기타피부암) → A4209_4
6. 4대특정암 진단비(갑상선암) → A4209_5
7. 4대특정암 진단비(경계성종양) → A4209_6
8. 암(4대특정암 제외) 치료비(1회한) → A9600_1
9. 4대특정암 치료비(1회한) → A9600_2
10. 표적항암약물허가치료비(Ⅰ)(1회한)(갱신형) → A9619_2
11. 키트루다(CAR-T)면역항암치료비(1회한)(갱신형) → A9620_1
12. 암(특정암 제외) 입원일당 → A6200_2
13. 특정암 진단비 → A4209_7
14. 암(4대특정암 제외) 수술비(1회한) → A5200_2
15. 4대특정암 수술비(1회한) → A5200_3
16. 표적항암면역치료비(Ⅰ)(1회한)(갱신형) → A9621_1
17. 신재진단암(기타피부암 제외) 진단비(1회한)(갱신형) → A4200_3

### DB (3 coverages)
1. 계속받는암진단비(유사암,대장점막내암및전립선암제외) → A4200_4
2. 다빈치로봇암수술비(연간1회한,특정암) → A5200_4
3. 다빈치로봇암수술비(연간1회한,특정암제외) → A5200_5

### Meritz (5 coverages)
1. 재진단암진단비(1년대기형) → A4200_5
2. 암직접치료입원일당(Ⅱ)(요양병원제외, 1일이상) → A6200_3
3. (10년갱신)갱신형다빈치로봇암수술비(암(특정암제외)) → A5200_6
4. (10년갱신)갱신형다빈치로봇암수술비(특정암) → A5200_7
5. (10년갱신)갱신형표적항암약물허가치료비Ⅱ → A9619_3

## Why Add to Excel
These coverages exist in insurer scope files but are not registered in the canonical mapping Excel, causing unmatched status and evidence search failure.

## Excel Row Mapping Example

| coverage_code | coverage_name_canonical | samsung | meritz | db | hanwha | 기타 |
|---|---|---|---|---|---|---|
| A4210_2 | 유사암(8대)진단비 | | | | 유사암(8대) 진단비 | |
| A4200_2 | 암(4대특정암제외)진단비 | | | | 암(4대특정암 제외) 진단비 | |
| A4209_2 | 4대특정암진단비 | | | | 4대특정암 진단비 | |
| A4200_4 | 계속받는암진단비(유사암대장점막내암전립선암제외) | | | 계속받는암진단비(유사암,대장점막내암및전립선암제외) | | |
| A4200_5 | 재진단암진단비(1년대기형) | | 재진단암진단비(1년대기형) | | | |

**Note**: Fill insurer columns with exact raw coverage names from scope files. Leave other insurers blank if coverage does not exist.

## Column Mapping
- `coverage_code`: Use suggested codes from candidates CSV
- `coverage_name_canonical`: Normalized name (spaces/special chars removed)
- `{insurer}` columns: Exact raw coverage name from scope CSV
- `기타`: Leave blank unless needed

## Manual Steps
1. Open `data/sources/mapping/담보명mapping자료.xlsx`
2. Add 25 new rows at the end of the sheet
3. For each row in `cancer_canonical_candidates.csv`:
   - Copy `suggested_coverage_code` to `coverage_code` column
   - Copy `suggested_canonical_name` to `coverage_name_canonical` column
   - Copy `raw_coverage_name` to the corresponding `{insurer}` column
4. Save Excel file
5. Proceed to STEP9_REEVAL_COMMANDS.md
