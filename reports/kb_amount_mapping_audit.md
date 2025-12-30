# KB Amount Mapping Audit

**STEP**: NEXT-10B-2E-2
**Date**: 2025-12-29
**Purpose**: 가입설계서 담보명 → 매핑 테이블 경유 여부 검증

---

## Summary Statistics

- **Total coverages in proposal with amounts**: 21
- **Found in scope_mapped.csv**: 17 (81.0%)
- **Mapping status 'matched'**: 12 (57.1%)
- **Mapping status 'unmatched'**: 5 (23.8%)
- **Not in scope_mapped**: 4 (19.0%)

---

## Detailed Mapping Results

| No | Coverage Name (Raw from Proposal) | Amount | Coverage Code | Canonical Name | Mapping Status | In Scope |
|----|----------------------------------|--------|---------------|----------------|----------------|----------|
| 1  | 일반상해사망(기본) | 1천만원 | A1300 | 상해사망 | ✅ matched | YES |
| 2  | 일반상해후유장해(20~100%)(기본) | 1천만원 | - | - | ❌ unmatched | YES |
| 3  | 보험료납입면제대상보장(8대기본) | 10만원 | - | - | ❌ unmatched | YES |
| 4  | 일반상해후유장해(3%~100%) | 1천만원 | A3300_1 | 상해후유장해(3-100%) | ✅ matched | YES |
| 5  | 질병사망 | 1천만원 | A1100 | 질병사망 | ✅ matched | YES |
| 6  | 암진단비(유사암제외) | 3천만원 | A4200_1 | 암진단비(유사암제외) | ✅ matched | YES |
| 7  | 10대고액치료비암진단비 | 1천만원 | - | - | ❌ NOT_IN_SCOPE | NO |
| 8  | 뇌혈관질환수술비 | 5백만원 | A5104_1 | 뇌혈관질환수술비 | ✅ matched | YES |
| 9  | 허혈성심장질환수술비 | 5백만원 | A5107_1 | 허혈성심장질환수술비 | ✅ matched | YES |
| 10 | 상해수술비 | 10만원 | A5300 | 상해수술비 | ✅ matched | YES |
| 11 | 항암방사선치료비 | 3백만원 | A9617_1 | 항암방사선치료비 | ✅ matched | YES |
| 12 | 항암약물치료비 | 3백만원 | A9617_1 | 항암약물치료비 | ✅ matched | YES |
| 13 | 표적항암약물허가치료비(3대특정암)(최초1회한)Ⅱ(갱신형) | 1천만원 | - | - | ❌ unmatched | YES |
| 14 | 표적항암약물허가치료비(림프종·백혈병 관련암)(최초1회한)Ⅱ(갱신형) | 1천만원 | - | - | ❌ NOT_IN_SCOPE | NO |
| 15 | 특정항암호르몬약물허가치료비(최초1회한)Ⅱ(갱신형) | 50만원 | - | - | ❌ unmatched | YES |
| 16 | 카티(CAR-T)항암약물허가치료비(연간1회한)(갱신형) | 1천만원 | - | - | ❌ unmatched | YES |
| 17 | 혈전용해치료비Ⅱ(최초1회한)(특정심장질환) 보장 | 2백만원 | - | - | ❌ NOT_IN_SCOPE | NO |
| 18 | 혈전용해치료비Ⅱ(최초1회한)(뇌졸중) 보장 | 2백만원 | - | - | ❌ NOT_IN_SCOPE | NO |
| 19 | 질병입원일당(1일이상) | 1만원 | A6100_1 | 질병입원일당(1일이상) | ✅ matched | YES |
| 20 | 상해입원일당(1일이상)Ⅱ | 1만원 | A6300_1 | 상해입원일당(1일이상) | ✅ matched | YES |
| 21 | 암직접치료입원일당(요양제외,1일이상180일한도) | 2만원 | A6200 | 암직접치료입원일당(요양제외, 1일 이상, 180일 한도) | ✅ matched | YES |

---

## Analysis by Category

### Category 1: ✅ MATCHED (12 coverages)

**Definition**: Found in scope_mapped.csv AND mapping_status = 'matched'

These coverages:
- ✅ Are in scope (canonical mapping exists)
- ✅ Have coverage_code assigned (e.g., A1300, A4200_1)
- ✅ Step7 SHOULD be able to extract amount using canonical name

**List**:
1. 일반상해사망(기본) → A1300 상해사망
2. 일반상해후유장해(3%~100%) → A3300_1 상해후유장해(3-100%)
3. 질병사망 → A1100 질병사망
4. 암진단비(유사암제외) → A4200_1 암진단비(유사암제외)
5. 뇌혈관질환수술비 → A5104_1 뇌혈관질환수술비
6. 허혈성심장질환수술비 → A5107_1 허혈성심장질환수술비
7. 상해수술비 → A5300 상해수술비
8. 항암방사선치료비 → A9617_1 항암방사선치료비
9. 항암약물치료비 → A9617_1 항암약물치료비
10. 질병입원일당(1일이상) → A6100_1 질병입원일당(1일이상)
11. 상해입원일당(1일이상)Ⅱ → A6300_1 상해입원일당(1일이상)
12. 암직접치료입원일당(요양제외,1일이상180일한도) → A6200 암직접치료입원일당

---

### Category 2: ❌ IN_SCOPE but UNMATCHED (5 coverages)

**Definition**: Found in scope_mapped.csv BUT mapping_status = 'unmatched'

These coverages:
- ✅ Are listed in scope_mapped.csv
- ❌ Have NO coverage_code (mapping failed)
- ❌ Have NO canonical name
- ❌ Step7 CANNOT extract amount (no mapping = no canonical name to search)

**List**:
1. 일반상해후유장해(20~100%)(기본) - 1천만원
2. 보험료납입면제대상보장(8대기본) - 10만원
3. 표적항암약물허가치료비(3대특정암)(최초1회한)Ⅱ(갱신형) - 1천만원
4. 특정항암호르몬약물허가치료비(최초1회한)Ⅱ(갱신형) - 50만원
5. 카티(CAR-T)항암약물허가치료비(연간1회한)(갱신형) - 1천만원

**Total amount locked**: 1천만원 + 10만원 + 1천만원 + 50만원 + 1천만원 = ~3,060만원 equivalent

---

### Category 3: ❌ NOT_IN_SCOPE (4 coverages)

**Definition**: NOT found in scope_mapped.csv at all

These coverages:
- ❌ Not in scope_mapped.csv
- ❌ Likely out of canonical scope (not in 담보명mapping자료.xlsx)
- ❌ Step7 CANNOT extract amount (not in scope = not processed)

**List**:
1. 10대고액치료비암진단비 - 1천만원
2. 표적항암약물허가치료비(림프종·백혈병 관련암)(최초1회한)Ⅱ(갱신형) - 1천만원
3. 혈전용해치료비Ⅱ(최초1회한)(특정심장질환) 보장 - 2백만원
4. 혈전용해치료비Ⅱ(최초1회한)(뇌졸중) 보장 - 2백만원

**Note**: These are legitimately OUT OF SCOPE per canonical mapping rules.

---

## Key Findings

### Finding 1: Mapping Table IS Used

✅ **YES** - Step7 relies on scope_mapped.csv to determine which coverages to process

**Evidence**:
- 12 coverages have `mapping_status = 'matched'` with valid coverage_code
- 5 coverages are IN scope_mapped but have `mapping_status = 'unmatched'` (no code assigned)
- 4 coverages are NOT in scope_mapped at all

**Conclusion**: Step7 DOES NOT bypass the mapping table.

---

### Finding 2: Mapping Failures Block Amount Extraction

❌ **CRITICAL** - Even if amount exists in proposal, unmatched coverages cannot be extracted

**Evidence**:
- Category 2 (5 coverages) have amounts in proposal (1천만원, 10만원, etc.)
- But these have `mapping_status = 'unmatched'` (no canonical name, no coverage_code)
- Step7 cannot extract without canonical name to search against

**Implication**: Type C classification is partially due to mapping failures, NOT document structure.

---

### Finding 3: KB is NOT a Pure Type C Insurer

**Observation**:
- KB proposal has **담보별 금액이 명시되어 있음** (line-by-line amounts)
- This is a **Type A characteristic** (coverage-level 명시형)
- Yet KB was classified as Type C (77.8% UNCONFIRMED)

**Root Cause Analysis**:
- Category 1 (matched): 12 coverages → Step7 CAN extract → CONFIRMED expected
- Category 2 (unmatched): 5 coverages → Step7 CANNOT extract (mapping failure) → UNCONFIRMED
- Category 3 (not in scope): 4 coverages → Out of scope → UNCONFIRMED (legitimate)

**Expected vs Actual**:
- Expected CONFIRMED: 12/21 = 57.1% (if Step7 works correctly)
- Actual CONFIRMED (from previous audit): 10/45 = 22.2%

**Question for STEP 3**:
- Why is actual CONFIRMED (22.2%) lower than expected (57.1%)?
- Are there pattern recognition failures beyond mapping?

---

## STOP Condition Check

### ❌ Potential Issue Detected

**Issue**: 5 coverages with valid amounts are UNMATCHED in scope_mapped.csv

**Examples**:
- `일반상해후유장해(20~100%)(기본)` - 1천만원 available, but NO canonical mapping
- `표적항암약물허가치료비(3대특정암)...` - 1천만원 available, but NO canonical mapping

**Implication**:
- These are NOT Type C issues (document structure)
- These are mapping table incompleteness issues
- Fixing these requires updating canonical mapping Excel (MANUAL WORK, not code)

**Is this a STOP?**: NO - this is expected behavior per Scope Gate rules.
- Scope Gate: "mapping 파일에 없는 담보는 처리 금지"
- These coverages are in scope_mapped but unmatched = mapping table needs manual update

---

## Next Step (STEP 3)

**Compare with Step7 actual output**:
- Load `data/compare/kb_coverage_cards.jsonl`
- Check which of the 12 MATCHED coverages actually have amounts extracted
- Identify any pattern recognition failures beyond mapping

**Questions to answer**:
- Do all 12 MATCHED coverages have amounts in coverage_cards.jsonl?
- If not, why? (pattern recognition issue vs document structure issue)
- Is KB truly Type C, or is it misclassified?

---

**Report Generated**: 2025-12-29 01:40:00 KST
**Mapping Data**: `/tmp/kb_mapping_audit_results.json`
**Status**: ✅ COMPLETE
