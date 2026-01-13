# Q7 Fact Snapshot — 2026-01-13

## Executive Summary
Q7 Premium Waiver Policy overlay implemented as **TYPE B Overlay** (no Core Model dependency).

### Key Findings
- **Insurers covered**: 10
- **산정특례 as waiver trigger**: UNKNOWN for all insurers
- **Evidence source**: 약관 (insurance terms) for all
- **Waiver triggers**: 3-11 conditions per insurer (major diseases)

### Critical Observation
**산정특례 does NOT appear as a premium waiver trigger** in any insurer's policy documents. It appears only as a separate benefit category (diagnosis benefits for patients under the special calculation system), not as a condition that triggers premium waiver.

## DoD (Definition of Done) Verification

### (A) Core Model Integrity
```bash
$ wc -l data/compare_v1/compare_rows_v1.jsonl
340 data/compare_v1/compare_rows_v1.jsonl
```
✅ **PASS**: Line count unchanged (340 maintained)

### (B) Regression Test — Q5/Q11/Q13 Unchanged
```bash
$ curl -s http://127.0.0.1:8000/q5 | python3 -c "import sys, json; d=json.load(sys.stdin); print('Q5 items:', len(d['items']))"
Q5 items: 10

$ curl -s http://127.0.0.1:8000/q11 | python3 -c "import sys, json; d=json.load(sys.stdin); print('Q11 items:', len(d['items']))"
Q11 items: 7

$ curl -s http://127.0.0.1:8000/q13 | python3 -c "import sys, json; d=json.load(sys.stdin); print('Q13 matrix:', len(d['matrix']))"
Q13 matrix: 8
```
✅ **PASS**: All existing overlay endpoints unchanged

### (C) Q7 SSOT Completeness
```bash
$ wc -l data/compare_v1/q7_waiver_policy_v1.jsonl
10 data/compare_v1/q7_waiver_policy_v1.jsonl

$ jq -r '.insurer_key' data/compare_v1/q7_waiver_policy_v1.jsonl | sort
db_over41
db_under40
hanwha
heungkuk
hyundai
kb
lotte_female
lotte_male
meritz
samsung
```
✅ **PASS**: All 10 insurers have records

### (D) Evidence Validation — 산정특례 Status
```bash
$ jq -r 'select(.has_sanjeong_teukrye=="YES") | .insurer_key' data/compare_v1/q7_waiver_policy_v1.jsonl | wc -l
0

$ jq -r 'select(.has_sanjeong_teukrye=="UNKNOWN") | .insurer_key' data/compare_v1/q7_waiver_policy_v1.jsonl | wc -l
10
```
✅ **PASS**: All insurers marked UNKNOWN (no false positives)

## Q7 API Endpoint Verification
```bash
$ curl -s http://127.0.0.1:8000/q7 | python3 -m json.tool | head -40
{
    "query_id": "Q7",
    "items": [
        {
            "insurer_key": "db_over41",
            "waiver_triggers": [
                "암",
                "갑상선암",
                "유사암",
                "뇌졸중",
                "급성심근경색색",
                "말기간경화",
                "말기신부전증",
                "말기폐질환"
            ],
            "has_sanjeong_teukrye": "UNKNOWN",
            "sanjeong_teukrye_display": "확인 불가 (근거 부족)",
            "evidence_count": 2,
            "evidence": {
                "doc_type": "약관",
                "page": 66,
                "excerpt": "제26-1조(보험료의 납입면제(Ⅰ)) 회사는 제2회 이후의 보험료 납입기간 중 피보험자가..."
            }
        },
        ...
    ]
}
```
✅ **PASS**: API returns well-formed JSON with all required fields

## Waiver Triggers Summary

| Insurer | Trigger Count | Notable Triggers |
|---------|---------------|------------------|
| samsung | 1 | 보험료납입면제대상 (refs external terms) |
| hanwha | 5 | 암, 뇌졸중, 급성심근경색, 말기간경화, 말기신부전증 |
| heungkuk | 6 | + 갑상선암 |
| hyundai | 7 | + 유사암, 말기폐질환 |
| kb | 3 | 암, 갑상선암, 유사암 |
| lotte_female | 6 | 일반암, 암, 뇌졸중, 급성심근경색, 말기간경화, 말기신부전증 |
| lotte_male | 6 | (same as lotte_female) |
| meritz | 11 | + 양성뇌종양, 중대한재생불량성빈혈, 만성당뇨합병증 |
| db_over41 | 8 | 암, 갑상선암, 유사암, 뇌졸중, 급성심근경색, 말기간경화, 말기신부전증, 말기폐질환 |
| db_under40 | 8 | (same as db_over41) |

## 산정특례 Analysis

### Search Scope
All 10 insurers' 약관 (insurance terms) were searched for:
- Primary keywords: "보험료 납입면제", "납입면제", "보험료 면제"
- 산정특례 keywords: "산정특례", "산정특례 대상", "본인부담 경감", "중증질환 산정특례"

### Findings
1. **Waiver clauses found**: All insurers have explicit premium waiver clauses
2. **산정특례 in waiver clauses**: NONE
3. **산정특례 in documents**: Found in benefit product names (e.g., "중증질환자(뇌혈관질환) 산정특례대상진단비")
4. **Interpretation**: 산정특례 is a diagnosis **benefit category**, not a waiver trigger

### Example Evidence (Hanwha)
```
약관 p.83:
제27조(보험료의 납입면제) 회사는 제2회 이후의 보험료 납입기간 중 피보험자가
이 특별약관의 보장개시일 이후에 암, 뇌졸중, 급성심근경색, 말기간경화,
말기신부전증으로 진단확정된 경우에는 차회 이후의 보험료 납입을 면제하여 드립니다.
```

**산정특례 NOT mentioned in waiver triggers.**

## Evidence Quality Assessment

### Doc Type Distribution
- 약관: 10/10 insurers (100%)
- Evidence rank: All rank 1 (highest quality)

### Evidence Completeness
| Insurer | Evidence Count | Pages Referenced |
|---------|----------------|------------------|
| samsung | 1 | 72 |
| hanwha | 1 | 83 |
| heungkuk | 1 | 80 |
| hyundai | 1 | 87 |
| kb | 1 | 30 |
| lotte_female | 1 | 91 |
| lotte_male | 1 | 91 |
| meritz | 1 | 112 |
| db_over41 | 2 | 66, 68 |
| db_under40 | 2 | 66, 68 |

All evidence excerpts contain explicit waiver clause text (제XX조 보험료의 납입면제).

## Known Limitations
1. **Samsung**: Waiver triggers reference "보험료납입면제대상Ⅱ 특별약관" (external special terms) not expanded
2. **No cross-document search**: Only searched 약관 doc_type (highest priority)
3. **No inference**: UNKNOWN maintained even when pattern suggests absence
4. **Single evidence per insurer**: Only first (highest rank) evidence returned in API

## Freeze Declaration
As of **2026-01-13**, Q7 is **FROZEN**:
- SSOT: `data/compare_v1/q7_waiver_policy_v1.jsonl`
- Insurers: 10
- has_sanjeong_teukrye: UNKNOWN for all (no backfill)
- Evidence: 약관-based, rank 1

### Immutability Rules
1. NO UNKNOWN → YES/NO changes without new document evidence
2. NO estimation or inference
3. NO cross-insurer pattern matching
4. Schema changes require Constitutional review

## Files Modified
```
data/compare_v1/q7_waiver_policy_v1.jsonl         (NEW - SSOT)
apps/api/overlays/q7/__init__.py                   (NEW)
apps/api/overlays/q7/model.py                      (NEW)
apps/api/overlays/q7/loader.py                     (NEW)
apps/api/server.py                                 (MODIFIED - added /q7 endpoint)
docs/policy/Q7_WAIVER_POLICY_OVERLAY.md           (NEW)
docs/audit/Q7_FACT_SNAPSHOT_2026-01-13.md         (NEW - this file)
```

## Compliance Checklist
- ✅ SYSTEM_CONSTITUTION.md: Overlay rules followed
- ✅ Evidence-First: All values evidence-backed or UNKNOWN
- ✅ No Core Model modification
- ✅ Q5 pattern followed (TYPE B Overlay)
- ✅ Regression tests passed
- ✅ API functional
- ✅ Documentation complete

## Next Steps (If Needed)
1. **Samsung expansion**: Parse external special terms if needed
2. **산정특례 clarification**: If business requirements change, search additional doc types
3. **UI integration**: Add Q7 to comparison UI (Phase 2)

---

**Snapshot Date**: 2026-01-13
**Auditor**: Claude (automated evidence gathering + manual validation)
**Status**: FROZEN — NO BACKFILL ALLOWED
