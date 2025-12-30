# Amount Read API Contract

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**Frozen Commit**: `c6fad903c4782c9b78c44563f0f47bf13f9f3417`

---

## 🎯 Purpose

This document defines the **immutable contract** for amount_fact API integration.

**CRITICAL**: This API is **READ-ONLY**. No writes, no inference, no recommendations.

---

## 📋 Contract Principles

### P1. Read-Only Principle
- API **ONLY reads** from `amount_fact` table
- **NO writes**, NO updates, NO deletes
- **NO** Step7 pipeline re-execution
- **NO** fallback inference or calculation

### P2. Status Preservation Principle
- `status` field values are **LOCKED**:
  - `CONFIRMED` - Amount explicitly stated + evidence exists
  - `UNCONFIRMED` - Coverage exists but amount not stated
  - `NOT_AVAILABLE` - Coverage does not exist

- Status is **NEVER changed** by API
- Status semantics are **IMMUTABLE**

### P3. Fact-First Principle
- `value_text` comes **ONLY** from `amount_fact.value_text`
- **NEVER** extracted from snippets
- **NEVER** inferred or calculated
- **NEVER** filled with defaults

### P4. Audit Lineage Principle
- All responses **MUST** include `audit` metadata:
  - `audit_run_id` (from `audit_runs` table)
  - `freeze_tag` (e.g., `freeze/pre-10b2g2-*`)
  - `git_commit` (frozen commit hash)

---

## 📊 Data Source

### Primary Table: `amount_fact`

```sql
TABLE amount_fact (
    coverage_instance_id UUID PRIMARY KEY,  -- FK to coverage_instance
    evidence_id UUID,                      -- FK to evidence_ref (optional)
    status TEXT,                           -- CONFIRMED | UNCONFIRMED
    value_text TEXT,                       -- e.g., "1천만원" (CONFIRMED only)
    source_doc_type TEXT,                  -- e.g., "가입설계서"
    source_priority TEXT,                  -- e.g., "PRIMARY"
    notes JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

### Join Path

```
amount_fact
  → coverage_instance (coverage_instance_id)
    → coverage_canonical (coverage_code)
    → insurer (insurer_id)
  → evidence_ref (evidence_id) [OPTIONAL]
  → audit_runs (via audit_name = 'step7_amount_gt_audit')
```

---

## 🔌 API Endpoints

### 1. Amount Query Endpoint (Proposed)

**Endpoint**: `GET /api/v1/amount`

**Purpose**: Query amount for single coverage

**Request**:
```json
{
  "insurer": "samsung",
  "coverage_code": "A1300",  // Canonical code (preferred)
  "coverage_name_raw": null,  // Or raw name from proposal
  "include_audit": true,
  "include_evidence": true
}
```

**Response**:
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-29T10:30:00Z",
  "coverage": {
    "coverage_code": "A1300",
    "coverage_name": "상해사망",
    "amount": {
      "status": "CONFIRMED",
      "value_text": "1천만원",
      "source_doc_type": "가입설계서",
      "source_priority": "PRIMARY",
      "evidence": {
        "status": "found",
        "source": "가입설계서 p.4",
        "snippet": "5. 상해사망\n1천만원"
      },
      "notes": []
    },
    "audit": {
      "audit_run_id": "f2e58b52-f22d-4d66-8850-df464954c9b8",
      "freeze_tag": "freeze/pre-10b2g2-20251229-024400",
      "git_commit": "c6fad903c4782c9b78c44563f0f47bf13f9f3417"
    }
  },
  "audit": {
    "audit_run_id": "f2e58b52-f22d-4d66-8850-df464954c9b8",
    "freeze_tag": "freeze/pre-10b2g2-20251229-024400",
    "git_commit": "c6fad903c4782c9b78c44563f0f47bf13f9f3417"
  }
}
```

---

### 2. Compare API Integration (Existing)

**Endpoint**: `POST /compare`

**Integration Point**: `ProductSummaryHandler._get_fact_value()`

**Flow**:
```python
# 1. Get amount from amount_fact
fact_data = self._get_fact_value(insurer_id, coverage_code)

# 2. Check status
if fact_data and fact_data.get('value_text'):
    # CONFIRMED - use value_text
    value_text = fact_data['value_text']
else:
    # UNCONFIRMED or NOT_AVAILABLE - show status
    value_text = "확인 불가"

# 3. Get evidence (optional)
evidence = self._build_evidence_from_fact(fact_data)

# 4. Build response row
{
    "coverage_code": "A1300",
    "coverage_name": "상해사망",
    "values": {
        "SAMSUNG": {
            "value_text": "1천만원",
            "evidence": {
                "status": "found",
                "source": "가입설계서 p.4",
                "snippet": "..."
            }
        }
    }
}
```

**Existing Implementation**: `apps/api/server.py:440-479`

---

## 📝 Response Schema (Locked)

### AmountDTO

```typescript
interface AmountDTO {
  status: "CONFIRMED" | "UNCONFIRMED" | "NOT_AVAILABLE";  // LOCKED
  value_text: string | null;  // From amount_fact.value_text ONLY
  source_doc_type: string | null;  // e.g., "가입설계서"
  source_priority: string | null;  // e.g., "PRIMARY"
  evidence: AmountEvidenceDTO | null;
  notes: string[];  // Reserved for future use
}
```

### AmountEvidenceDTO

```typescript
interface AmountEvidenceDTO {
  status: "found" | "not_found";
  source: string | null;  // e.g., "가입설계서 p.4"
  snippet: string | null;  // Max 400 chars, normalized
}
```

### AmountAuditDTO

```typescript
interface AmountAuditDTO {
  audit_run_id: UUID;
  freeze_tag: string;  // e.g., "freeze/pre-10b2g2-20251229-024400"
  git_commit: string;  // e.g., "c6fad903c4782c9b78c44563f0f47bf13f9f3417"
}
```

---

## 🚦 Status Handling Rules

### CONFIRMED

**Database State**:
```sql
amount_fact.status = 'CONFIRMED'
amount_fact.value_text IS NOT NULL  -- e.g., "1천만원"
amount_fact.evidence_id IS NOT NULL  -- Required
```

**API Response**:
```json
{
  "status": "CONFIRMED",
  "value_text": "1천만원",
  "evidence": {
    "status": "found",
    "source": "가입설계서 p.4",
    "snippet": "..."
  }
}
```

**Presentation** (UI):
- Display `value_text` as-is
- Normal text style
- Evidence tooltip available

---

### UNCONFIRMED

**Database State**:
```sql
amount_fact.status = 'UNCONFIRMED'
amount_fact.value_text IS NULL  -- No amount stated
coverage_instance EXISTS  -- Coverage exists
```

**API Response**:
```json
{
  "status": "UNCONFIRMED",
  "value_text": null,
  "evidence": null
}
```

**Presentation** (UI):
- Display: **"금액 명시 없음"** (fixed text)
- Style: Muted/gray
- Tooltip: "문서상 금액이 명시되지 않았습니다"

---

### NOT_AVAILABLE

**Database State**:
```sql
coverage_instance NOT EXISTS  -- Coverage doesn't exist for this insurer
-- OR
amount_fact NOT EXISTS AND coverage_instance NOT EXISTS
```

**API Response**:
```json
{
  "status": "NOT_AVAILABLE",
  "value_text": null,
  "evidence": null
}
```

**Presentation** (UI):
- Display: **"해당 담보 없음"** (fixed text)
- Style: Disabled/strikethrough
- Tooltip: "해당 보험사/상품에 이 담보가 없습니다"

---

## ❌ Forbidden Operations

### API Layer
- ❌ Writing to `amount_fact` table
- ❌ Updating `status` or `value_text`
- ❌ Inferring amounts from snippets
- ❌ Calculating amounts from formulas
- ❌ Providing fallback/default values
- ❌ Running Step7 pipeline from API
- ❌ Changing audit metadata

### Response
- ❌ Returning amounts NOT in `amount_fact.value_text`
- ❌ Changing status values (e.g., UNCONFIRMED → CONFIRMED)
- ❌ Omitting audit metadata
- ❌ Adding computed fields (e.g., `amount_numeric`, `comparison_rank`)

### Presentation
- ❌ Sorting by amount value
- ❌ Color coding for "better/worse"
- ❌ Highlighting max/min values
- ❌ Calculating averages
- ❌ Recommendations based on amount
- ❌ Visualizing comparisons (charts/graphs)

---

## 🔍 Query Patterns

### By Canonical Code (Preferred)

```sql
SELECT
    af.status,
    af.value_text,
    af.source_doc_type,
    af.evidence_id,
    ci.instance_id
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
JOIN insurer i ON ci.insurer_id = i.insurer_id
WHERE i.insurer_name_kr = '삼성화재'
  AND ci.coverage_code = 'A1300'
LIMIT 1;
```

### By Raw Name (Fallback)

```sql
SELECT
    af.status,
    af.value_text,
    af.source_doc_type,
    af.evidence_id,
    ci.instance_id,
    ci.coverage_code
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
JOIN insurer i ON ci.insurer_id = i.insurer_id
WHERE i.insurer_name_kr = '삼성화재'
  AND ci.coverage_name_raw = '상해사망'
LIMIT 1;
```

### Get Audit Metadata

```sql
SELECT
    audit_run_id,
    freeze_tag,
    git_commit
FROM audit_runs
WHERE audit_name = 'step7_amount_gt_audit'
  AND audit_status = 'PASS'
ORDER BY generated_at DESC
LIMIT 1;
```

---

## 🧪 Validation

### Request Validation
```python
# Rule 1: Either coverage_code or coverage_name_raw required
if not (request.coverage_code or request.coverage_name_raw):
    raise ValueError("Either coverage_code or coverage_name_raw required")

# Rule 2: Insurer must be valid
if request.insurer.lower() not in VALID_INSURERS:
    raise ValueError(f"Invalid insurer: {request.insurer}")
```

### Response Validation
```python
# Rule 1: CONFIRMED requires value_text
if amount.status == "CONFIRMED":
    assert amount.value_text is not None
    assert amount.value_text not in ["확인 불가", "금액 명시 없음"]

# Rule 2: UNCONFIRMED/NOT_AVAILABLE should not have value_text
if amount.status in ["UNCONFIRMED", "NOT_AVAILABLE"]:
    assert amount.value_text is None

# Rule 3: Evidence required for CONFIRMED
if amount.status == "CONFIRMED":
    if not amount.evidence or amount.evidence.status != "found":
        logger.warning(f"CONFIRMED without evidence: {amount.value_text}")

# Rule 4: Audit metadata required
assert response.audit is not None
assert response.audit.audit_run_id is not None
```

---

## 📚 Implementation References

| Component | File | Lines |
|-----------|------|-------|
| DTO Definitions | `apps/api/dto.py` | 1-385 |
| Amount Repository | `apps/api/amount_handler.py` | 30-245 |
| Query Handler | `apps/api/amount_handler.py` | 250-385 |
| Compare Integration | `apps/api/server.py` | 440-607 |
| Presentation Rules | `apps/api/dto.py` | 250-325 |

---

## 🔒 Contract Lock

**This contract is LOCKED as of STEP NEXT-11.**

Any changes to:
- Response schema
- Status values
- Query behavior
- Presentation rules

Require **version bump** and **new audit run**.

**Enforcement**:
- Schema changes → API version increment
- Status changes → Contract violation (rejected)
- New amount sources → Step7 v2 (new pipeline)

---

## 📞 Support

**Questions**: Refer to `docs/ui/AMOUNT_PRESENTATION_RULES.md` for UI guidelines
**Issues**: Check `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md` for lock policy

**Lock Owner**: Pipeline Team
**Last Updated**: 2025-12-29
