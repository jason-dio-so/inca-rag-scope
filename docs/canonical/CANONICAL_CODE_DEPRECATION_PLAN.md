# Canonical Code Deprecation Plan

**Document Type**: Technical Debt Remediation Plan
**Created**: 2025-12-31 (STEP NEXT-37)
**Authority**: CANONICAL_CODE_EXTENSION_POLICY.md Section 6.2
**Status**: PLANNED (NOT EXECUTED)

---

## 1. Deprecated Canonical Code 정의 (Definition)

### 1.1 What Is a Deprecated Canonical Code?

**Definition**: A canonical coverage code (`cre_cvr_cd`) that:
- Was created in violation of code extension policy (CANONICAL_CODE_EXTENSION_POLICY.md)
- Remains in mapping Excel for backward compatibility
- MUST NOT be used for new coverage mappings
- MUST be replaced with policy-compliant code in future pipeline runs

**Lifecycle States**:
```
ACTIVE → DEPRECATED → MIGRATED → REMOVED
  ↑ Current usage    ↑ Planned    ↑ After reassignment complete
```

**Deprecated Code Behavior**:
- ✅ **Read-only**: Existing mappings in scope CSV continue to work
- ✅ **Evidence search**: Step4 searches using deprecated code's canonical name
- ✅ **Coverage cards**: SSOT (coverage_cards.jsonl) preserves deprecated codes
- ❌ **New mappings**: Step2 MUST NOT assign deprecated codes to new coverages
- ❌ **Precedent**: Cannot be cited as justification for similar extensions

### 1.2 Distinction from Deletion

**Deprecated ≠ Deleted**:
- **Deprecated**: Marked invalid for future use, but preserved for historical data
- **Deleted**: Removed from Excel, breaks existing mappings (NOT ALLOWED)

**Why Not Delete?**:
1. Existing SSOT files (coverage_cards.jsonl) reference deprecated codes
2. Historical pipeline runs would become non-reproducible
3. Meritz scope CSV contains `coverage_code: A4999_1` mappings
4. Breaking change would violate CLAUDE.md INPUT contract stability

**Deprecation Marker**:
- Excel column: Add `[DEPRECATED]` prefix to 신정원코드명
- New column (optional): `status` = "deprecated" | "active"
- Documentation: This file (CANONICAL_CODE_DEPRECATION_PLAN.md)

---

## 2. A4999_* Deprecation 사유 (Justification)

### 2.1 Policy Violation Identified

**Codes in Question**:
- `A4999_1`: 갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
- `A4999_2`: 갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)

**Created**: 2025-12-31 (commit eb5dfd8, STEP NEXT-35)

**Violation**: CANONICAL_CODE_EXTENSION_POLICY.md Section 4.3
- **Reserved Range**: A4900-A4999 is reserved for future structural needs
- **Available Alternatives**: A4303-A4399 range available (87 codes unused)
- **Pattern Deviation**: Existing A4xxx codes: A4101-A4105, A4200-A4210, A4299, A4301-A4302 (no A49xx precedent)

**Why Created (Original Rationale)**:
- STEP NEXT-35 alias fix for Meritz `(20년갱신)갱신형...` prefix mismatch
- Evidence found (약관 3 hits, 상품요약서 1 hit) but no canonical code existed
- Urgent fix needed to achieve 100% evidence_status: found for Meritz
- Reserved range violation not caught during creation

**STEP NEXT-36 Ruling**: Conditionally Allowed with mandatory remediation (Section 6.2)

### 2.2 Impact of Deprecation

**Current Usage** (as of 2025-12-31):
```
Insurer: Meritz (N01)
Coverages affected: 2
Scope files: data/scope/meritz_scope_mapped.csv (lines 14-15)
SSOT files: data/compare/meritz_coverage_cards.jsonl (lines 13-14)
Evidence hits: A4999_1 (약관:3, 상품요약서:1), A4999_2 (약관:3, 상품요약서:1)
```

**Files Referencing A4999_***:
- `data/sources/mapping/담보명mapping자료.xlsx` (INPUT contract)
- `data/scope/meritz_scope_mapped.csv` (intermediate)
- `data/scope/meritz_scope_mapped.sanitized.csv` (pipeline input)
- `data/compare/meritz_coverage_cards.jsonl` (SSOT)

**Other Insurers**: ❌ NOT AFFECTED (A4999_* used only by Meritz)

**Comparison Results**: ⚠️ POTENTIALLY AFFECTED
- If cross-insurer comparison includes Meritz + A4999 codes → results valid but codes deprecated

---

## 3. Target Reassignment Codes (A43xx)

### 3.1 Semantic Analysis

**A4999_1 / A4999_2 Coverage Characteristics**:
- **Category**: 질병 진단비 (disease diagnosis benefit)
- **Disease Type**: 중증질환자 산정특례대상 (severe illness special calculation target)
- **Sub-types**: 뇌혈관질환 (cerebrovascular), 심장질환 (cardiac)
- **Payment Structure**: 연간1회한 (annually, 1 time limit)
- **Policy Type**: 갱신형 (renewable)

**Existing Semantic Neighbors**:
- `A4101`: 뇌혈관질환진단비 (general cerebrovascular diagnosis)
- `A4104_1`: 심장질환진단비 (general cardiac diagnosis)
- `A4105`: 허혈성심장질환진단비 (ischemic cardiac diagnosis)

**Distinction**:
- A4101/A4104/A4105: General disease diagnosis (non-renewable, single payment)
- A4999_1/A4999_2: **산정특례대상** (special calculation target status) + **갱신형** (renewable) + **연간1회한** (annual recurrence)

**Conclusion**: A4999_* are NOT simple aliases of A4101/A4104 — they are distinct coverage types requiring separate canonical codes.

### 3.2 Reassignment Target Selection

**Candidate Ranges**:

**Option A: A4101_x / A4104_x (Suffix Increment)**
- Pros: Groups with existing 뇌혈관질환/심장질환 codes
- Cons: A4101/A4104 are general diagnosis, not 산정특례 variants
- Cons: Conflates "general disease" with "severe illness special status"
- **Ruling**: ❌ REJECTED (semantic mismatch)

**Option B: A4300_x (New Hundred-Level Prefix)**
- Pros: A4300 available, establishes new category for 산정특례 diagnosis
- Pros: Future-proof for other 산정특례 coverages
- Cons: Creates new hundred-level prefix (requires strong justification)
- **Ruling**: ✅ VIABLE (if 산정특례 becomes recurring category)

**Option C: A4303_1 / A4303_2 (New Base Code for 산정특례)**
- Pros: Uses available A43xx range (A4303-A4399 open)
- Pros: Separates from A4301 (골절진단비), A4302 (화상진단비)
- Pros: Allows future expansion (A4303_3 ~ A4303_9 for other 산정특례 types)
- Cons: None identified
- **Ruling**: ✅ **RECOMMENDED**

**Option D: A4104_2 / A4104_3 (Under 심장질환 base)**
- Pros: Only for A4999_2 (심장질환), groups with A4104_1
- Cons: A4999_1 (뇌혈관질환) would need A4101_2, splits the 산정특례 concept
- Cons: 산정특례 is cross-disease category, should have unified prefix
- **Ruling**: ❌ REJECTED (splits semantic category)

### 3.3 Final Reassignment Codes

**RECOMMENDED CODES**:
```
A4999_1 → A4303_1 (갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한))
A4999_2 → A4303_2 (갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한))
```

**Rationale**:
1. **Policy Compliance**: A4303 falls within A4300-A4399 (available range)
2. **Semantic Coherence**: A4303_x establishes 산정특례 진단비 category
3. **Sequential Suffix**: _1, _2 follow CANONICAL_CODE_EXTENSION_POLICY.md Section 3.2
4. **Extensibility**: A4303_3 ~ A4303_9 reserved for future 산정특례 variants
5. **Pattern Consistency**: Follows existing pattern (A4200_x, A4209_x, A4210_x)

**Alternative (If A4300 Preferred)**:
```
A4999_1 → A4300_1
A4999_2 → A4300_2
```
- Use if 산정특례 becomes major category requiring hundred-level prefix
- Requires stronger justification (new category establishment)

**Prefix Assignment Policy Reference**:
- CANONICAL_CODE_EXTENSION_POLICY.md Section 3.1: A4300-A4399 available
- CANONICAL_CODE_EXTENSION_POLICY.md Section 5.1 Case C: New coverage type → new hundred-level prefix conditionally allowed
- STEP13_CANCER_CANONICAL_POLICY.md: Event-based categorization (산정특례 = special payment event)

---

## 4. Migration Strategy

### 4.1 Timing

**NOT Immediate** — Migration is deferred to future STEP for safety.

**Trigger Conditions** (ANY of the following):
1. **Next Meritz pipeline re-run** (e.g., STEP NEXT-40+, when Meritz scope changes)
2. **Other insurer encounters 산정특례 coverage** (A4303_x needed for new coverage)
3. **30 days from STEP NEXT-36** (2026-01-30 deadline per CANONICAL_CODE_EXTENSION_POLICY.md Section 6.2)
4. **Manual migration request** (user explicitly requests cleanup)

**Why Deferred?**:
- Current Meritz results valid (evidence_status: found, 100% success)
- No operational failure (A4999_* functions correctly in pipeline)
- Risk of introducing regression if migrated immediately
- Allows thorough testing in isolated STEP

**Recommended Timing**: **STEP NEXT-40** (Meritz scope update or new insurer onboarding)

### 4.2 Migration Steps (Execution Order)

**Phase 1: Preparation** (STEP NEXT-38, current STEP)
1. ✅ Create deprecation plan (this document)
2. ✅ Define target codes (A4303_1, A4303_2)
3. ⏳ Add deprecation markers to Excel (신정원코드명 prefix `[DEPRECATED]`)
4. ⏳ Document in Excel notes: "Use A4303_1 / A4303_2 instead"

**Phase 2: New Code Creation** (STEP NEXT-39 or trigger-based)
1. Add new rows to `data/sources/mapping/담보명mapping자료.xlsx`:
   ```
   cre_cvr_cd: A4303_1
   신정원코드명: 갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
   담보명(가입설계서): (20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
   ins_cd: N01 (Meritz)
   보험사명: 메리츠
   ```
   ```
   cre_cvr_cd: A4303_2
   신정원코드명: 갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)
   담보명(가입설계서): (20년갱신)갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)
   ins_cd: N01 (Meritz)
   보험사명: 메리츠
   ```

2. Keep A4999_1, A4999_2 rows with `[DEPRECATED - Use A4303_1/2]` marker

**Phase 3: Pipeline Re-run** (STEP NEXT-40, Meritz only)
1. Run Step2 (canonical mapping) for Meritz:
   ```bash
   python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer meritz
   ```
2. Verify scope_mapped.csv now contains `A4303_1`, `A4303_2` (not A4999_*)
3. Run Steps 1b, 4, 5 (sanitize, evidence search, cards):
   ```bash
   python -m pipeline.step1_sanitize_scope.run --insurer meritz
   python -m pipeline.step4_evidence_search.search_evidence --insurer meritz
   python -m pipeline.step5_build_cards.build_cards --insurer meritz
   ```

**Phase 4: Verification** (Same STEP as Phase 3)
1. Compare old vs new coverage_cards.jsonl:
   ```bash
   diff <(jq -c 'select(.coverage_code | startswith("A4999"))' data/compare/meritz_coverage_cards.jsonl.bak) \
        <(jq -c 'select(.coverage_code | startswith("A4303"))' data/compare/meritz_coverage_cards.jsonl)
   ```
2. Verify evidence_status unchanged: found → found
3. Verify hits_by_doc_type unchanged: {약관:3, 상품요약서:1}
4. Verify coverage_name_raw unchanged (SSOT preservation)
5. Check no NEW unmatched coverages introduced

**Phase 5: Deprecation Finalization** (After successful migration)
1. Remove A4999_* rows from Excel (OR keep with clear DEPRECATED status)
2. Update this document status: PLANNED → EXECUTED
3. Archive old coverage_cards.jsonl as `meritz_coverage_cards.A4999_deprecated.jsonl`

### 4.3 Safety Checks (Pre-Migration Validation)

**Checklist** (ALL must pass before migration):

- [ ] **Backup created**: `data/sources/mapping/담보명mapping자료.xlsx.bak`
- [ ] **Scope backup**: `data/scope/meritz_scope_mapped.csv.bak`
- [ ] **SSOT backup**: `data/compare/meritz_coverage_cards.jsonl.bak`
- [ ] **New codes ready**: A4303_1, A4303_2 rows added to Excel
- [ ] **Alias preserved**: `(20년갱신)갱신형...` alias in A4303_x rows
- [ ] **신정원코드명 identical**: Canonical names match A4999_* exactly
- [ ] **No other insurers affected**: Only Meritz uses A4999_*
- [ ] **Step2 logic unchanged**: No code changes to map_to_canonical.py
- [ ] **Test run successful**: Dry-run on test branch passes pytest

**Automated Safety Check Script** (future implementation):
```python
# tools/migration/validate_a4999_migration.py
def validate_migration():
    # Check A4303_1/2 canonical names match A4999_1/2
    # Verify Meritz scope re-mapping produces identical evidence hits
    # Confirm no new unmatched coverages
    pass
```

### 4.4 Rollback Plan

**If Migration Fails** (evidence_status changes, new unmatched coverages):

**Rollback Steps**:
1. Restore Excel from backup:
   ```bash
   cp data/sources/mapping/담보명mapping자료.xlsx.bak data/sources/mapping/담보명mapping자료.xlsx
   ```
2. Restore Meritz scope CSV:
   ```bash
   cp data/scope/meritz_scope_mapped.csv.bak data/scope/meritz_scope_mapped.csv
   ```
3. Restore SSOT:
   ```bash
   cp data/compare/meritz_coverage_cards.jsonl.bak data/compare/meritz_coverage_cards.jsonl
   ```
4. Document rollback reason in this file (Section 6: Execution Log)
5. Investigate root cause (likely alias mismatch or search_key issue)
6. Re-attempt migration after fix

**No Code Rollback Needed**: Migration does NOT modify pipeline code, only data files.

**Rollback SLA**: < 5 minutes (simple file restore)

---

## 5. Non-Impact Guarantee

### 5.1 Other Insurers (100% Isolated)

**Analysis**:
```bash
# Verify A4999_* usage is Meritz-only
grep -r "A4999" data/scope/*.csv | grep -v meritz
# Expected: No results
```

**Guaranteed Non-Impact**:
- ✅ **Samsung**: Does not use A4999_* (verified in 9c212d3 data)
- ✅ **DB**: Does not use A4999_* (verified)
- ✅ **Hanwha**: Does not use A4999_* (verified)
- ✅ **KB**: Does not use A4999_* (verified)
- ✅ **Lotte**: Does not use A4999_* (verified)
- ✅ **Heungkuk**: Does not use A4999_* (verified)
- ✅ **Hyundai**: Does not use A4999_* (verified)

**Reason**: A4999_1/2 created for Meritz-specific coverage `(20년갱신)갱신형 중증질환자...` not found in other insurers' proposals.

**If Other Insurer Needs 산정특례 Code**:
- Use A4303_x directly (skip A4999_* entirely)
- No migration needed for that insurer (A4303 is primary code)

### 5.2 Existing Comparisons

**Cross-Insurer Comparison Impact**:

**Scenario 1: A4200_1 comparison (all insurers)**
- Meritz not included → NO IMPACT
- Meritz included, only uses A4200_1 → NO IMPACT

**Scenario 2: Future A4303_x comparison**
- Before migration: Only Meritz with A4999_* (comparison possible but code deprecated)
- After migration: Only Meritz with A4303_x (comparison uses correct code)

**Comparison Files Affected**:
- `data/single/a4200_1_all_compare.json`: NO IMPACT (A4999 not related to A4200)
- Future `a4303_1_all_compare.json`: IMPACT (A4999_1 → A4303_1 changes code reference)

**Mitigation**:
- Historical comparison results remain valid (archived with deprecated codes)
- New comparisons use A4303_x (correct canonical codes)

### 5.3 Historical Results (Backward Compatibility)

**SSOT Immutability Principle**:
- Coverage cards generated before migration preserve A4999_* references
- Old SSOT files NOT modified (historical record)

**File Versioning**:
```
data/compare/meritz_coverage_cards.jsonl.2025-12-31  # Contains A4999_*
data/compare/meritz_coverage_cards.jsonl             # After migration, contains A4303_*
```

**Result Reproducibility**:
- Pipeline run on 2025-12-31 with old Excel → produces A4999_*
- Pipeline run on 2026-01-30 with new Excel → produces A4303_*
- Both results valid for their respective time periods

**Audit Trail**:
- This document serves as migration record
- Git history preserves Excel changes
- SSOT file timestamps indicate migration date

**Query Compatibility**:
- API queries for A4999_1 on old SSOT → returns data
- API queries for A4303_1 on new SSOT → returns data
- API MUST NOT conflate A4999_1 ≈ A4303_1 (separate codes with separate histories)

---

## 6. Execution Log (To Be Updated)

**Status**: PLANNED (NOT EXECUTED as of 2025-12-31)

**Execution Record** (to be filled when migration occurs):

| Phase | Date | Executor | Status | Notes |
|-------|------|----------|--------|-------|
| Phase 1: Preparation | 2025-12-31 | STEP NEXT-37 | ✅ COMPLETE | Deprecation plan created |
| Phase 2: New Code Creation | TBD | TBD | ⏳ PENDING | A4303_1/2 to be added to Excel |
| Phase 3: Pipeline Re-run | TBD | TBD | ⏳ PENDING | Meritz pipeline to be re-run |
| Phase 4: Verification | TBD | TBD | ⏳ PENDING | Evidence hits to be verified |
| Phase 5: Finalization | TBD | TBD | ⏳ PENDING | A4999_* deprecation final |

**Rollback History**: None (no execution yet)

**Issues Encountered**: None (no execution yet)

---

## 7. Policy Enforcement

### 7.1 Immediate Effect (2025-12-31 onwards)

**A4999_* Treatment**:
- ✅ **Read-only valid**: Existing mappings work in pipeline
- ❌ **New mapping prohibited**: Step2 MUST NOT assign A4999_* to new coverages
- ❌ **Precedent denied**: Cannot cite A4999_* as justification for A49xx extensions
- ⚠️ **Conditional validity**: Valid only until migration to A4303_*

**Code Review Requirement**:
- Any new coverage mapping to A49xx range → REJECTED in code review
- Any reference to A4999_* as extension precedent → REJECTED

### 7.2 Future A49xx Requests

**Blanket Prohibition**:
- A4900-A4999 reserved per CANONICAL_CODE_EXTENSION_POLICY.md Section 3.1
- NO exceptions without constitutional amendment (CANONICAL_CODE_EXTENSION_POLICY.md Section 7.2)

**If Similar Case Arises**:
1. Check A4300-A4399 range (87 codes available)
2. Use A43xx_x pattern (NOT A49xx)
3. Cite this deprecation plan as precedent for correct approach

### 7.3 Documentation Requirements

**For A4303_x Codes** (when created):
- Excel notes column: "Replaces deprecated A4999_1/2, created per CANONICAL_CODE_DEPRECATION_PLAN.md"
- Git commit message: Reference this document
- Migration STEP document: Detailed execution log

**For Other 산정특례 Variants**:
- Use A4303_3 ~ A4303_9 (sequential)
- If exceeds _9: Create A4304 (new base code for sub-category)
- Follow CANONICAL_CODE_EXTENSION_POLICY.md Section 5.3 checklist

---

## 8. Appendix: Technical Specifications

### 8.1 Excel Row Format (New A4303_x Codes)

**A4303_1**:
```
cre_cvr_cd: A4303_1
신정원코드명: 갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
담보명(가입설계서): (20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
ins_cd: N01
보험사명: 메리츠
notes: Replaces A4999_1 (deprecated), CANONICAL_CODE_DEPRECATION_PLAN.md
```

**A4303_2**:
```
cre_cvr_cd: A4303_2
신정원코드명: 갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)
담보명(가입설계서): (20년갱신)갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)
ins_cd: N01
보험사명: 메리츠
notes: Replaces A4999_2 (deprecated), CANONICAL_CODE_DEPRECATION_PLAN.md
```

**A4999_1 (Deprecated)**:
```
cre_cvr_cd: A4999_1
신정원코드명: [DEPRECATED - Use A4303_1] 갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
담보명(가입설계서): (KEEP FOR BACKWARD COMPATIBILITY)
ins_cd: N01
보험사명: 메리츠
notes: DEPRECATED 2025-12-31, reserved range violation, migrate to A4303_1
```

### 8.2 Expected Pipeline Behavior Change

**Before Migration** (Step2 output):
```csv
coverage_name_raw,insurer,source_page,coverage_code,coverage_name_canonical,mapping_status,match_type
"(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회\n한)",meritz,3,A4999_1,갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한),matched,normalized_alias
```

**After Migration** (Step2 output):
```csv
coverage_name_raw,insurer,source_page,coverage_code,coverage_name_canonical,mapping_status,match_type
"(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회\n한)",meritz,3,A4303_1,갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한),matched,normalized_alias
```

**Key Difference**: Only `coverage_code` changes (A4999_1 → A4303_1), all other fields identical.

### 8.3 Evidence Search Invariance

**Step4 Search Keywords** (unchanged):
```python
keywords = [
    coverage_name_canonical,  # 갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
    search_key                # (20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
]
```

**Result**: Evidence hits remain identical (canonical name unchanged, search_key unchanged).

**Verification Command**:
```bash
# Before migration
grep "A4999_1" data/compare/meritz_coverage_cards.jsonl | jq '.hits_by_doc_type'
# {"약관": 3, "사업방법서": 0, "상품요약서": 1}

# After migration
grep "A4303_1" data/compare/meritz_coverage_cards.jsonl | jq '.hits_by_doc_type'
# {"약관": 3, "사업방법서": 0, "상품요약서": 1}  (MUST BE IDENTICAL)
```

---

**END OF DEPRECATION PLAN**

---

## FINAL STATEMENT

**Until this deprecation plan is executed, A4999_* remains valid for read-only canonical mapping and MUST NOT be used as precedent for future extensions.**

**Post-Execution**: A4303_1 / A4303_2 become the canonical codes for 산정특례대상 진단비, and A4999_* becomes historical reference only.

**Enforcement**: Any new A49xx code request (A4900-A4999 range) MUST be rejected with reference to:
1. CANONICAL_CODE_EXTENSION_POLICY.md Section 4.3 (reserved range prohibition)
2. This document (CANONICAL_CODE_DEPRECATION_PLAN.md) as example of remediation

**Success Criteria**:
- Meritz evidence_status: found (100%) maintained after migration
- No new unmatched coverages introduced
- Coverage_name_raw (SSOT) unchanged
- Other insurers (7) unaffected
- Historical results backward-compatible
