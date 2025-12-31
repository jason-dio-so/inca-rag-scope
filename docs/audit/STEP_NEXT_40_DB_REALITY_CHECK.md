# STEP NEXT-40: DB Reality Check (READ-ONLY)

**Date**: 2025-12-31
**Purpose**: Verify PostgreSQL database contains SSOT data for customer delivery
**Mode**: Read-only inspection (NO modifications)

---

## Executive Summary

**DB Status**: **⚠️ EMPTY_DB** (Populated but unusable)

**Customer Screen Feasibility**: **NO**

**Critical Issue**: All amount_fact rows have NULL value_text (285/285 rows)

**Blocking Fact**: API queries filter for `status = 'CONFIRMED'` but all DB rows are `status = 'UNCONFIRMED'` with NULL values

---

## 1. DB Connection Verification

### 1.1 PostgreSQL Process Check

**Command**: `lsof -i :5432`

**Result**:
```
COMMAND    PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
com.docke 3491 cheollee  181u  IPv6 0xa9b912a1f464b507      0t0  TCP *:postgresql (LISTEN)
```

**Status**: ✅ PostgreSQL running (via docker, PID 3491)

**Port**: 5432 (listening)

### 1.2 Database Connection Info (from server.py:64-67)

```python
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
)
```

**Connection string used for verification**:
- Host: localhost
- Port: 5432
- Database: inca_rag_scope
- User: inca_admin

**Connection test**: ✅ SUCCESS (able to query)

---

## 2. Table Existence & Row Counts

### 2.1 Core Fact Tables

| Table | Row Count | Status |
|-------|-----------|--------|
| coverage_canonical | 48 | ✅ Populated |
| coverage_instance | 297 | ✅ Populated |
| evidence_ref | 747 | ✅ Populated |
| amount_fact | 285 | ⚠️ **Populated but UNUSABLE** |

**All tables exist**: ✅ YES

**Data loaded**: ✅ YES (from 2025-12-30 15:29:52)

**Problem**: Data is unusable for customer delivery (details below)

### 2.2 Load Timestamp

**Query**:
```sql
SELECT MIN(created_at) as earliest_load, MAX(created_at) as latest_load
FROM amount_fact;
```

**Result**:
```
earliest_load         | latest_load
----------------------+----------------------
2025-12-30 15:29:52   | 2025-12-30 15:29:53
```

**Load date**: 2025-12-30 (1 day old)

**Load duration**: ~1 second (fast bulk insert)

**Interpretation**: Data was loaded via `step9_loader.py` on Dec 30th

---

## 3. SSOT Presence Verification

### 3.1 Insurer Distribution

**Query**:
```sql
SELECT i.insurer_name_kr, COUNT(*) as amount_count
FROM insurer i
LEFT JOIN coverage_instance ci ON i.insurer_id = ci.insurer_id
LEFT JOIN amount_fact af ON ci.instance_id = af.coverage_instance_id
WHERE af.coverage_instance_id IS NOT NULL
GROUP BY i.insurer_name_kr
ORDER BY i.insurer_name_kr;
```

**Result**:
| Insurer | Amount Count |
|---------|--------------|
| 삼성화재 | 40 |
| 한화생명 | 37 |
| 현대해상 | 36 |
| 흥국생명 | 36 |
| 메리츠화재 | 34 |
| 롯데손해보험 | 37 |
| DB손해보험 | 29 |
| KB손해보험 | 36 |

**Total insurers**: 8
**Total amount facts**: 285 (40+37+36+36+34+37+29+36)

**Coverage**: All major insurers present (Samsung, Hanwha, Meritz, KB, DB, Lotte, Hyundai, Heungkuk)

**Status**: ✅ SSOT data loaded for all 8 insurers

### 3.2 Coverage Distribution

**Query**:
```sql
SELECT cc.coverage_code, cc.coverage_name_canonical, COUNT(DISTINCT ci.insurer_id) as insurer_count
FROM coverage_canonical cc
LEFT JOIN coverage_instance ci ON cc.coverage_code = ci.coverage_code
GROUP BY cc.coverage_code, cc.coverage_name_canonical
ORDER BY insurer_count DESC LIMIT 10;
```

**Top 10 coverages by insurer count**:
| Coverage Code | Coverage Name | Insurer Count |
|---------------|---------------|---------------|
| A4103 | 뇌졸중진단비 | 8 |
| A3300_1 | 상해후유장해(3-100%) | 8 |
| A4200_1 | 암진단비(유사암제외) | 8 |
| A5300 | 상해수술비 | 7 |
| A1100 | 질병사망 | 7 |
| A4105 | 허혈성심장질환진단비 | 7 |
| A1300 | 상해사망 | 7 |
| A5100 | 질병수술비 | 7 |
| A4102 | 뇌출혈진단비 | 7 |
| A9617_1 | 항암방사선약물치료비(최초1회한) | 7 |

**Most common coverage**: 뇌졸중진단비, 상해후유장해, 암진단비 (8/8 insurers)

**Canonical codes**: ✅ Present (A4103, A4200_1, etc. match STEP 9.1 schema)

**Status**: ✅ SSOT canonical codes loaded

---

## 4. Critical Data Quality Issue

### 4.1 Amount Fact Status Distribution

**Query**:
```sql
SELECT af.status, COUNT(*) as count
FROM amount_fact af
GROUP BY af.status;
```

**Result**:
```
status      | count
------------+-------
UNCONFIRMED | 285
```

**Problem**: All 285 rows are UNCONFIRMED, **ZERO rows are CONFIRMED**

**API requirement** (server.py:458):
```python
AND af.status = 'CONFIRMED'
```

**Impact**: API will return **ZERO amount_fact rows** because query filters for CONFIRMED only

### 4.2 Value Text Verification

**Query**:
```sql
SELECT COUNT(*) as null_count
FROM amount_fact
WHERE value_text IS NULL OR value_text = '';
```

**Result**:
```
null_count
-----------
285
```

**Problem**: **ALL 285 rows have NULL value_text**

**Expected** (from STEP NEXT-39-α analysis, loader comment line 11):
```
amount_fact (from coverage_cards.jsonl)
```

**Sample data** (5 rows):
```
coverage_code | insurer_id | value_text | status
--------------+------------+------------+-------------
A4209_6       | c795...    | (NULL)     | UNCONFIRMED
A9617_1       | 0b36...    | (NULL)     | UNCONFIRMED
A6300_1       | 70ea...    | (NULL)     | UNCONFIRMED
A6300_1       | 0b36...    | (NULL)     | UNCONFIRMED
A4209_2       | c795...    | (NULL)     | UNCONFIRMED
```

**API expectation** (server.py:440-479):
```python
def _get_fact_value(self, insurer_id: str, coverage_code: str) -> Optional[Dict[str, Any]]:
    """
    Get fact-based value from amount_fact (FACT-FIRST)

    Returns:
        {
            "value_text": "3000만원",  # <-- EXPECTS THIS
            "evidence_id": uuid,
            "source_doc_type": "가입설계서"
        }
        or None
    """
```

**Reality**: value_text is NULL → API returns None → "확인 불가" for all coverages

---

## 5. Evidence Data Quality

### 5.1 Evidence Ref Sample

**Query**:
```sql
SELECT er.snippet, er.doc_type, er.page, er.rank
FROM evidence_ref er
WHERE er.snippet IS NOT NULL AND LENGTH(er.snippet) > 10
LIMIT 5;
```

**Sample snippets**:
1. "종속 특별약관\n85\n  1. 보험료 납입면제대상Ⅱ 특별약관..." (목차)
2. "보장 제외\n암\n- 보험료 납입면제대상Ⅱ\n가입후 90일간..." (혼합)
3. "가입금액 한도\n기타\n- 보험료 납입면제대상Ⅱ..." (목차)
4. "4-1. 질병 관련 특별약관\n167\n..." (목차)
5. Similar table of contents patterns

**Issue**: Evidence snippets contain low-quality text (목차, 페이지 번호 나열)

**API has forbidden pattern filter** (server.py:72-78):
```python
FORBIDDEN_SNIPPET_PATTERNS = [
    r"(목차|특약관|특별약관|민원사례|안내|예시|FAQ)",  # 목차/안내문
    r"(\n?\s*\d{2,4}\s*){3,}",  # 숫자 반복 과다 (페이지 번호 나열)
    r"제\s*\d+\s*(장|절|조)\s*[\.:]?\s*$",  # 조항 번호만
    r"^[\d\s\-\.]+$",  # 숫자/기호만
]
```

**Likely outcome**: Most evidence will be rejected by API quality filter

---

## 6. Why Loader Must NOT Be Re-Run Now

### 6.1 Current State Analysis

**DB State**: Populated (2025-12-30 15:29:52)

**SSOT State** (from git status):
- Modified: data/compare/*.jsonl (not committed)
- Modified: data/scope/*.csv (not committed)
- Modified: data/evidence_pack/*.jsonl (not committed)

**Problem**: DB was loaded from SSOT state on Dec 30th, but SSOT has changed since then (git shows modifications)

### 6.2 Risks of Re-Running Loader

**If we run loader now**:

1. **SSOT Drift Risk**
   - Current DB = Dec 30th SSOT snapshot
   - Current disk = Dec 31st SSOT (modified, not committed)
   - Reload = overwrite with newer, unverified SSOT

2. **Quality Gate Bypass Risk**
   - STEP 32-35 quality gates were applied to Dec 30th data
   - Dec 31st modifications may not have passed quality gates
   - Loader has no built-in quality validation

3. **Status Field Mismatch**
   - Current DB: All UNCONFIRMED (intentional loader output?)
   - Loader code (line 627): `INSERT INTO amount_fact`
   - Unknown: Does loader set status=CONFIRMED or UNCONFIRMED?
   - Re-run may replicate same UNCONFIRMED issue

4. **Value_text Population**
   - Current DB: All NULL value_text
   - Unknown: Does loader extract value_text from coverage_cards.jsonl?
   - Need to audit loader code before re-run

5. **Audit Trail Loss**
   - Current DB represents Dec 30th verified state
   - Reload = lose ability to compare Dec 30th vs Dec 31st
   - No rollback mechanism exists

### 6.3 Required Investigation Before Any Loader Action

**Must answer**:
1. Why are all amount_fact.status = UNCONFIRMED? (Expected or bug?)
2. Why are all amount_fact.value_text = NULL? (Loader bug or missing source data?)
3. What changed in SSOT between Dec 30th and Dec 31st? (git diff)
4. Is current DB state intended or corrupted?

**Evidence needed**:
- Loader code audit (step9_loader.py lines 627-700)
- coverage_cards.jsonl structure verification
- Git diff of SSOT files (Dec 30 vs Dec 31)

---

## 7. Customer Screen Feasibility Judgment

### 7.1 Technical Feasibility

**Question**: Can API serve customer screens with current DB?

**Answer**: **NO**

**Reason**: API query (server.py:458) filters `status = 'CONFIRMED'`, but DB has **ZERO CONFIRMED rows**

**SQL that will execute**:
```sql
SELECT af.value_text, af.evidence_id, af.source_doc_type, af.status, ci.instance_id
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
WHERE ci.insurer_id = %s AND ci.coverage_code = %s
  AND af.status = 'CONFIRMED'  -- <-- Will return 0 rows
LIMIT 1
```

**Result**: 0 rows returned → API returns `{"value_text": "확인 불가"}`

### 7.2 Expected Customer Experience

**If we start API with current DB**:

**Request**: "Compare 삼성화재 vs 한화생명 암 진단비"

**Expected Response** (5-block):
```json
{
  "meta": { "query_id": "...", "intent": "PRODUCT_SUMMARY" },
  "query_summary": { "targets": ["SAMSUNG", "HANWHA"], ... },
  "comparison": {
    "rows": [
      {
        "coverage_code": "A4200_1",
        "coverage_name": "암진단비(유사암제외)",
        "values": {
          "SAMSUNG": {
            "value_text": "확인 불가",  // <-- No CONFIRMED amount_fact
            "evidence": {"status": "not_found"}  // <-- Or low-quality evidence rejected
          },
          "HANWHA": {
            "value_text": "확인 불가",
            "evidence": {"status": "not_found"}
          }
        }
      }
    ]
  },
  "notes": [],
  "limitations": [...]
}
```

**Customer sees**: "확인 불가" for all coverages across all insurers

**Customer reaction**: "Why is everything unavailable? This system is useless."

---

## 8. SSOT vs DB Alignment Status

### 8.1 Schema Alignment

| Component | SSOT (Disk) | DB (PostgreSQL) | Aligned |
|-----------|-------------|-----------------|---------|
| coverage_canonical | 담보명mapping자료.xlsx | coverage_canonical (48 rows) | ✅ YES |
| coverage_instance | scope_mapped.sanitized.csv | coverage_instance (297 rows) | ✅ YES |
| evidence_ref | evidence_pack.jsonl | evidence_ref (747 rows) | ✅ YES |
| amount_fact | coverage_cards.jsonl | amount_fact (285 rows) | ⚠️ PARTIAL |

**Partial alignment reason**: Row counts match (~285), but **value_text extraction failed**

### 8.2 Data Freshness

**SSOT Last Modified** (from git status):
```
M data/compare/kb_coverage_cards.jsonl
M data/compare/meritz_coverage_cards.jsonl
M data/compare/samsung_coverage_cards.jsonl
```

**DB Last Loaded**: 2025-12-30 15:29:52

**Time gap**: ~19 hours (Dec 30 15:29 → Dec 31 10:00+)

**Git commits since DB load**:
- 54ef5a3 (STEP NEXT-35): Dec 31
- eb5dfd8 (STEP NEXT-35): Dec 31
- 31d32e4 (STEP NEXT-34-ε): Dec 31
- 25dfa9c (STEP NEXT-34-ε): Dec 31

**SSOT has evolved**: Quality gates + alias restoration applied after DB load

---

## 9. Root Cause Hypothesis

### 9.1 Loader Code Analysis Needed

**Hypothesis 1**: Loader extracts coverage_instance and evidence correctly, but **fails to extract value_text from coverage_cards.jsonl**

**Evidence**:
- coverage_instance: 297 rows (correct)
- evidence_ref: 747 rows (correct)
- amount_fact: 285 rows (row count correct, **values missing**)

**Possible causes**:
1. coverage_cards.jsonl has no `amount` field (check JSONL structure)
2. Loader code has bug in value_text extraction (check line 627-700)
3. Loader intentionally sets value_text=NULL for initial load (check loader comments)

### 9.2 Status Field Mystery

**Hypothesis 2**: Loader sets status='UNCONFIRMED' by default, expecting **post-load validation step**

**Evidence**:
- All 285 rows: status='UNCONFIRMED'
- Loader commit message (6a9849f): "Load amount_fact from coverage_cards.jsonl (CONFIRMED when evidence exists)"
- Contradiction: Comment says "CONFIRMED when evidence exists", but all are UNCONFIRMED

**Possible causes**:
1. Loader code doesn't implement "CONFIRMED when evidence exists" logic yet
2. Loader sets UNCONFIRMED as placeholder, expects separate UPDATE step
3. Evidence linking failed → all marked UNCONFIRMED

### 9.3 Evidence Quality Issue

**Hypothesis 3**: Evidence was loaded but contains low-quality snippets (목차, 페이지 번호)

**Evidence**:
- Sample snippets show table of contents, page numbers, headers
- API has forbidden pattern filter (server.py:72-78)
- These snippets will be rejected by API

**Possible causes**:
1. Evidence extraction (STEP 4) captured wrong text regions
2. Quality filter (STEP 32) was applied to disk files but not to DB load
3. Loader loaded raw evidence_pack.jsonl without quality filtering

---

## 10. Next Steps (Dependencies Only, No Actions)

### 10.1 Immediate Investigation Required

**Before ANY loader action**:
1. **Audit loader code** (apps/loader/step9_loader.py:627-700)
   - How is value_text extracted?
   - How is status determined?
   - What validation occurs?

2. **Verify SSOT structure** (data/compare/samsung_coverage_cards.jsonl)
   - Does `amount` field exist?
   - What is the field name for value_text?
   - Sample 5 rows

3. **Git diff audit** (Dec 30 → Dec 31)
   - What changed in coverage_cards.jsonl?
   - Were quality gates applied after DB load?
   - Is current SSOT safer or riskier?

### 10.2 Decision Tree

**IF** loader has value_text bug:
→ Fix loader code → Re-run with current SSOT → Verify results

**IF** SSOT structure changed:
→ Audit SSOT changes → Determine if safe to reload → If safe, re-run loader

**IF** status='CONFIRMED' logic missing:
→ Implement status validation logic → Re-run loader OR run UPDATE query

**IF** evidence quality is the issue:
→ Re-run STEP 4 (evidence search) with quality filter → Reload evidence_ref

### 10.3 Do NOT Proceed To

❌ STEP NEXT-41 (UI real data connection) — DB is unusable
❌ STEP NEXT-41-β (Controlled loader run) — Root cause unknown
❌ Any loader execution — Investigation incomplete
❌ Any DB schema changes — Not the problem
❌ docker restart — Won't fix data issue

---

## 11. Conclusion

### 11.1 DB Status Classification

**Status**: **⚠️ EMPTY_DB** (Populated but Unusable)

**Definition**: Database exists, tables exist, rows exist, **but data is not fit for customer delivery**

**NOT**: ✅ READY (would require CONFIRMED status + non-NULL value_text)
**NOT**: ❌ NO_DB (PostgreSQL is running and accessible)

### 11.2 Customer Screen Feasibility

**Feasibility**: **NO**

**Reason**: API will return "확인 불가" for all coverages because:
1. All amount_fact.status = 'UNCONFIRMED' (API filters for 'CONFIRMED')
2. All amount_fact.value_text = NULL (API expects "3000만원" etc.)
3. Evidence snippets likely rejected by quality filter (목차/페이지번호)

**Customer impact**: Empty comparison table, no usable information

### 11.3 Why Loader Must Wait

**Blocker**: Unknown root cause of value_text=NULL and status=UNCONFIRMED

**Required**: Loader code audit + SSOT structure verification + git diff analysis

**Risk**: Re-running loader without investigation may replicate same issue or introduce new corruption

**Policy**: Read-only investigation first, loader execution only after root cause identified

---

**Audit completed**: 2025-12-31
**Mode**: Read-only (NO modifications made)
**DB accessed**: inca_rag_scope @ localhost:5432
**Queries executed**: 10 (all SELECT, 0 INSERT/UPDATE/DELETE)
**Tables verified**: 4 (coverage_canonical, coverage_instance, evidence_ref, amount_fact)
**Row counts**: 48 + 297 + 747 + 285 = 1,377 total rows
**Critical findings**: 285/285 amount_fact rows unusable (NULL value_text + UNCONFIRMED status)
