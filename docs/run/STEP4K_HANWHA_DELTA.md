# STEP 4-κ – Hanwha Evidence Search Rule Application

## Summary

Applied Top-6 suffix variant rules (including Top-3) to Hanwha evidence search.

## Before vs After

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total rows | 37 | 37 | 0 |
| Nonempty | 13 | 13 | 0 |
| Empty | 24 | 24 | 0 |
| Matched | 23 | 23 | 0 |
| Unmatched | 14 | 14 | 0 |

## Rules Applied

Hanwha-specific query variant rules (Top-6 including Top-3):

1. 치료비 ↔ 치료 (TOP-3 #1)
2. 입원일당 ↔ 입원
3. 수술비 ↔ 수술 (TOP-3 #2)
4. 항암치료 ↔ 항암 (TOP-3 #3)
5. 표적항암 ↔ 표적
6. 재진단암 ↔ 재진단

## Note

Rules were already in place prior to STEP4-κ. No code changes made.
DoD target (nonempty≥18) not met. Current implementation at 13/37.
