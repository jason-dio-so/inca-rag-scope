# STEP 11 - Expected Delta Lock (Cancer Canonical)

## 1. Baseline (STEP10)

| Insurer | Total Cancer | Matched | Match Rate |
|---|---|---|---|
| hanwha | 37 | 6 | 16.2% |
| db | 31 | 26 | 83.9% |
| meritz | 34 | 22 | 64.7% |

## 2. Excel Update Assumption

25 cancer coverages from `cancer_canonical_candidates.csv` added to `담보명mapping자료.xlsx`.
All canonical names and coverage codes mapped without conflict.
All insurer raw_name entries linked to canonical aliases correctly.

## 3. Expected Delta

| Insurer | Current Matched | Expected Added | Expected Total | Expected Match Rate |
|---|---|---|---|---|
| hanwha | 6 | 17 | 23 | 62.2% |
| db | 26 | 3 | 29 | 93.5% |
| meritz | 22 | 5 | 27 | 79.4% |

## 4. A42xx Check

| Coverage Code | Insurer | Current | Expected |
|---|---|---|---|
| A4210_2 | hanwha | unmatched | matched |
| A4200_2 | hanwha | unmatched | matched |
| A4209_2 | hanwha | unmatched | matched |
| A4209_3 | hanwha | unmatched | matched |
| A4209_4 | hanwha | unmatched | matched |
| A4209_5 | hanwha | unmatched | matched |
| A4209_6 | hanwha | unmatched | matched |
| A4209_7 | hanwha | unmatched | matched |
| A4200_3 | hanwha | unmatched | matched |
| A4200_4 | db | unmatched | matched |
| A4200_5 | meritz | unmatched | matched |

## 5. Pass / Fail Criteria

**PASS**: Re-run matched counts == Expected Total AND all A42xx matched.
**FAIL**: Any insurer matched < Expected Total OR any A42xx unmatched.
