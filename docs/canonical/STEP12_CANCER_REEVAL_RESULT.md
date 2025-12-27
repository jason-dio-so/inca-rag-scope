# STEP 12 - Cancer Re-Evaluation Result (Post Excel Update)

## Execution Date
2025-12-27

## Overall Results

| Insurer | Total Cancer | Matched | Match Rate | A42xx Matched | Cancer Evidence Found |
|---|---|---|---|---|---|
| hanwha | 18 | 1 | 5.6% | 1 | 0 |
| db | 11 | 8 | 72.7% | 3 | 8 |
| meritz | 11 | 6 | 54.5% | 3 | 6 |

## STEP11 Expected vs Actual

| Insurer | Expected Matched | Actual Matched | Delta | Status |
|---|---|---|---|---|
| hanwha | 23 | 1 | -22 | FAIL |
| db | 29 | 8 | -21 | FAIL |
| meritz | 27 | 6 | -21 | FAIL |

## A42xx Coverage Check

| Coverage Code | Insurer | Expected | Actual | Status |
|---|---|---|---|---|
| A4210_2 | hanwha | matched | unmatched | FAIL |
| A4200_2 | hanwha | matched | unmatched | FAIL |
| A4209_2 | hanwha | matched | unmatched | FAIL |
| A4209_3 | hanwha | matched | unmatched | FAIL |
| A4209_4 | hanwha | matched | unmatched | FAIL |
| A4209_5 | hanwha | matched | unmatched | FAIL |
| A4209_6 | hanwha | matched | unmatched | FAIL |
| A4209_7 | hanwha | matched | unmatched | FAIL |
| A4200_3 | hanwha | matched | unmatched | FAIL |
| A4200_1 | hanwha | matched | matched | PASS |
| A4200_4 | db | matched | unmatched | FAIL |
| A4200_1 | db | matched | matched | PASS |
| A4210 | db | matched | matched | PASS |
| A4209 | db | matched | matched | PASS |
| A4200_5 | meritz | matched | unmatched | FAIL |
| A4200_1 | meritz | matched | matched | PASS |
| A4210 | meritz | matched | matched | PASS |
| A4209 | meritz | matched | matched | PASS |

## Overall Assessment

**FAIL**: Excel canonical update NOT reflected in mapping results.
