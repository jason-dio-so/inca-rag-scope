# Q7: Premium Waiver Policy Overlay

## SSOT Location
`data/compare_v1/q7_waiver_policy_v1.jsonl`

## Type Classification
**TYPE B Overlay** (Contract-level policy, NO Core Model dependency)

## Constitutional Compliance
- ✅ Core Slot 불변: Q7 does NOT modify Core slots
- ✅ Overlay only: Q7 is pure overlay, no Core Model writes
- ✅ Evidence-First: All values backed by document evidence or marked UNKNOWN
- ✅ UNKNOWN allowed: Document limitations accepted, no estimation

## Schema

```json
{
  "insurer_key": "string",
  "waiver_triggers": ["string"],
  "has_sanjeong_teukrye": "YES|NO|UNKNOWN",
  "evidence_refs": [
    {
      "doc_type": "string",
      "page": "number",
      "excerpt": "string",
      "locator": "string (optional)"
    }
  ]
}
```

## Field Definitions

### waiver_triggers
List of conditions that trigger premium waiver (보험료 납입면제 사유).

**Examples:**
- 암 (Cancer)
- 뇌졸중 (Stroke)
- 급성심근경색 (Acute Myocardial Infarction)
- 말기간경화 (End-stage liver cirrhosis)
- 말기신부전증 (End-stage renal failure)

### has_sanjeong_teukrye
Indicates whether "산정특례" (special calculation exemption for severe illness patients) is explicitly mentioned as a waiver trigger.

**Values:**
- `YES`: 산정특례 explicitly listed as waiver trigger in policy documents
- `NO`: Document explicitly states 산정특례 is NOT a waiver trigger
- `UNKNOWN`: No evidence either way (keyword not found in waiver clauses)

**CRITICAL FINDING (2026-01-13):**
- All 10 insurers: `UNKNOWN`
- Reason: 산정특례 appears only as benefit product category (diagnosis benefits), NOT as premium waiver trigger
- Evidence: Waiver clauses list specific diseases but do NOT mention 산정특례

## Evidence Priority
1. 약관 (Insurance Terms)
2. 사업방법서 (Business Method Manual)
3. 상품요약서 (Product Summary)
4. 가입설계서 (Proposal)

## API Endpoint
`GET /q7?insurers={comma_separated_list}`

**Example:**
```bash
curl http://localhost:8000/q7?insurers=samsung,hanwha
```

## Freeze Declaration
This overlay is **FROZEN** as of 2026-01-13.

### Scope Lock
- Insurers: 10 (samsung, hanwha, heungkuk, hyundai, kb, lotte_female, lotte_male, meritz, db_over41, db_under40)
- Coverage: Premium waiver triggers only
- 산정특례 status: UNKNOWN for all insurers (no backfill allowed)

### Immutability Rules
1. NO backfill of UNKNOWN → YES/NO without new document evidence
2. NO inference or estimation
3. Schema changes require Constitutional review
4. Evidence addition allowed ONLY with explicit document reference

## Business Rules
1. waiver_triggers는 약관에 명시된 질병/상태만 포함
2. has_sanjeong_teukrye는 "산정특례" keyword 기준으로만 판단
3. 추정/보완/유추 금지 (Evidence-First)
4. UNKNOWN은 정상 상태 (document limitation)

## Known Limitations
1. Samsung: Waiver triggers reference external special terms ("보험료납입면제대상Ⅱ"), not expanded
2. Evidence depth: Only first evidence ref returned in API (full list in SSOT)
3. No cross-insurer comparison logic (API returns raw facts only)

## Related Documents
- SYSTEM_CONSTITUTION.md: Overlay rules
- docs/audit/Q7_FACT_SNAPSHOT_2026-01-13.md: Evidence audit
- Q5_WAITING_PERIOD_DECISION.md: Pattern reference (TYPE B Overlay)

## Changelog
- 2026-01-13: Initial Q7 overlay implementation
  - 10 insurers
  - Evidence-backed waiver triggers
  - 산정특례 status: UNKNOWN for all
  - FROZEN
