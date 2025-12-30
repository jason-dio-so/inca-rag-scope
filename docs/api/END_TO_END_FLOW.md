# End-to-End Flow Documentation

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-13

---

## 🎯 Purpose

This document defines the **complete data flow** from user request to UI display.

**CRITICAL**: This is a **flow documentation**, NOT an implementation guide.
- All components are LOCKED (read-only)
- NO modifications allowed at any layer
- Flow is deterministic (NO LLM, NO inference)

---

## 📊 System Architecture (Complete Stack)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER BROWSER                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. User Input                                        │  │
│  │     - Select insurers (e.g., 삼성화재, KB손해보험)     │  │
│  │     - Select products (e.g., 다이렉트 암보험)          │  │
│  │     - Select coverages (e.g., 암진단비)               │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  2. API Request (POST /compare)                       │  │
│  │     - Frontend sends JSON request                     │  │
│  │     - Request follows AMOUNT_READ_CONTRACT            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ▼ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                    API SERVER (FastAPI)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  3. Request Validation                                │  │
│  │     - Validate product exists                         │  │
│  │     - Validate coverage code/name                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  4. Database Query (READ-ONLY)                        │  │
│  │     - Query amount_fact table                         │  │
│  │     - Join coverage_instance, evidence_ref            │  │
│  │     - Get audit_runs metadata                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  5. AmountDTO Construction                            │  │
│  │     - status: CONFIRMED | UNCONFIRMED | NOT_AVAILABLE │  │
│  │     - value_text: from amount_fact.value_text         │  │
│  │     - evidence: from evidence_ref (optional)          │  │
│  │     - audit: from audit_runs                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  6. Explanation Generation (Template-Based)           │  │
│  │     - CONFIRMED → "{insurer}의 ... {value_text}..."   │  │
│  │     - UNCONFIRMED → "금액이 명시되어 있지 않습니다"    │  │
│  │     - NOT_AVAILABLE → "해당 담보가 존재하지 않습니다"  │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  7. Response Serialization                            │  │
│  │     - Build CompareResponse JSON                      │  │
│  │     - Include audit metadata                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ▼ JSON
┌─────────────────────────────────────────────────────────────┐
│                    USER BROWSER                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  8. Response Parsing                                  │  │
│  │     - Parse JSON response                             │  │
│  │     - Extract coverage comparisons                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  9. UI Rendering (Presentation Rules)                │  │
│  │     - Display value_text as-is (NO parsing)           │  │
│  │     - Apply status-based styling                      │  │
│  │     - NO forbidden words                              │  │
│  │     - NO comparisons (parallel display only)          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Flow (Step-by-Step)

### STEP 1: User Input (Frontend)

**User Actions**:
1. Select insurers: `["삼성화재", "KB손해보험"]`
2. Select products: `["다이렉트 암보험", "KB 암보험"]`
3. Select coverages: `["암진단비 (A4200_1)"]`
4. Click "비교하기" button

**Frontend Processing**:
- Construct API request payload
- NO client-side validation (API will validate)
- NO pre-fetching or caching

**Output**: API request object

---

### STEP 2: API Request (Frontend → API)

**HTTP Request**:

```http
POST /compare HTTP/1.1
Host: api.inca-rag-scope.example.com
Content-Type: application/json

{
  "products": [
    {
      "insurer": "삼성화재",
      "product_name": "다이렉트 암보험"
    },
    {
      "insurer": "KB손해보험",
      "product_name": "KB 암보험"
    }
  ],
  "target_coverages": [
    {
      "coverage_code": "A4200_1"
    }
  ],
  "options": {
    "include_notes": true,
    "include_evidence": true
  }
}
```

**Network Layer**:
- Protocol: HTTPS (production)
- Method: POST
- Headers: `Content-Type: application/json`
- Body: JSON request

---

### STEP 3: Request Validation (API Server)

**Validation Steps**:

1. **Product Validation**:
   ```sql
   SELECT product_id
   FROM product
   WHERE product_name = '다이렉트 암보험'
     AND insurer_id = (SELECT insurer_id FROM insurer WHERE insurer_name_kr = '삼성화재');
   ```

   - If NOT EXISTS → Return error `404 Product Not Found`

2. **Coverage Validation**:
   ```sql
   SELECT coverage_code, coverage_name
   FROM coverage_canonical
   WHERE coverage_code = 'A4200_1';
   ```

   - If NOT EXISTS → Return error `404 Coverage Not Found`

3. **Request Schema Validation**:
   - Pydantic model validation
   - Required fields present
   - Field types correct

**Output**: Validated request or error response

---

### STEP 4: Database Query (API Server → PostgreSQL)

**Query Path**: `amount_fact` ← `coverage_instance` ← `coverage_canonical`

**SQL Query** (simplified):

```sql
SELECT
    af.status,
    af.value_text,
    af.source_doc_type,
    af.evidence_id,
    ci.coverage_code,
    cc.coverage_name,
    i.insurer_name_kr
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
JOIN coverage_canonical cc ON ci.coverage_code = cc.coverage_code
JOIN product p ON ci.product_id = p.product_id
JOIN insurer i ON p.insurer_id = i.insurer_id
WHERE ci.coverage_code = 'A4200_1'
  AND i.insurer_name_kr = '삼성화재'
  AND p.product_name = '다이렉트 암보험';
```

**Possible Results**:

| Scenario | amount_fact Row | Status | value_text |
|----------|----------------|--------|------------|
| **Amount found** | EXISTS | CONFIRMED | "3천만원" |
| **Coverage exists, no amount** | EXISTS | UNCONFIRMED | NULL |
| **Coverage doesn't exist** | NOT EXISTS | NOT_AVAILABLE | NULL |

**Audit Metadata Query**:

```sql
SELECT audit_run_id, freeze_tag, git_commit
FROM audit_runs
WHERE audit_name = 'step7_amount_gt_audit'
  AND audit_status = 'PASS'
ORDER BY generated_at DESC
LIMIT 1;
```

**Output**: Database rows (amount_fact + audit_runs)

---

### STEP 5: AmountDTO Construction (API Server)

**Logic**:

```python
def build_amount_dto(amount_fact_row, evidence_row, audit_row):
    if amount_fact_row is None:
        # Coverage doesn't exist
        return AmountDTO(
            status="NOT_AVAILABLE",
            value_text=None,
            evidence=None
        )

    if amount_fact_row['status'] == 'CONFIRMED':
        # Amount explicitly stated
        return AmountDTO(
            status="CONFIRMED",
            value_text=amount_fact_row['value_text'],  # e.g., "3천만원"
            source_doc_type=amount_fact_row['source_doc_type'],
            evidence=AmountEvidenceDTO(
                status="found",
                source=evidence_row['source'],
                snippet=evidence_row['snippet']
            )
        )

    else:
        # Coverage exists but amount not stated
        return AmountDTO(
            status="UNCONFIRMED",
            value_text=None,
            evidence=None
        )
```

**CRITICAL RULES**:
- `value_text` comes **ONLY** from `amount_fact.value_text` (NOT from snippet)
- Status semantics are **IMMUTABLE**
- NO inference or calculation

**Output**: AmountDTO object

---

### STEP 6: Explanation Generation (API Server)

**Template Selection**:

```python
def generate_explanation(insurer, coverage_name, amount_dto):
    if amount_dto.status == "CONFIRMED":
        return f"{insurer}의 {coverage_name}는 가입설계서에 {amount_dto.value_text}으로 명시되어 있습니다."

    elif amount_dto.status == "UNCONFIRMED":
        return f"{insurer}의 {coverage_name}는 가입설계서에 금액이 명시되어 있지 않습니다."

    elif amount_dto.status == "NOT_AVAILABLE":
        return f"{insurer}에는 해당 담보가 존재하지 않습니다."
```

**Example Outputs**:

| Status | Explanation |
|--------|-------------|
| CONFIRMED | "삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다." |
| UNCONFIRMED | "KB손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다." |
| NOT_AVAILABLE | "현대해상에는 해당 담보가 존재하지 않습니다." |

**CRITICAL RULES**:
- Templates are **LOCKED** (no LLM)
- NO comparative language (더/보다/유리/불리)
- Explanations are **parallel** (not cross-referenced)

**Output**: InsurerExplanationDTO object

---

### STEP 7: Response Serialization (API Server)

**Response Structure**:

```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-29T10:30:00Z",
  "request": {
    "products": [
      {"insurer": "삼성화재", "product_name": "다이렉트 암보험"},
      {"insurer": "KB손해보험", "product_name": "KB 암보험"}
    ],
    "target_coverages": [
      {"coverage_code": "A4200_1"}
    ]
  },
  "results": [
    {
      "coverage_code": "A4200_1",
      "coverage_name": "암진단비",
      "values": {
        "삼성화재": {
          "value_text": "3천만원",
          "evidence": {
            "status": "found",
            "source": "가입설계서 p.4",
            "snippet": "암진단비: 3천만원"
          }
        },
        "KB손해보험": {
          "value_text": null,
          "evidence": {
            "status": "not_found"
          }
        }
      }
    }
  ],
  "audit": {
    "audit_run_id": "f2e58b52-f22d-4d66-8850-df464954c9b8",
    "freeze_tag": "freeze/pre-10b2g2-20251229-024400",
    "git_commit": "c6fad903c4782c9b78c44563f0f47bf13f9f3417"
  }
}
```

**Serialization**:
- Pydantic models → JSON
- UTF-8 encoding
- Pretty print (development) or compact (production)

**Output**: HTTP response with JSON body

---

### STEP 8: Response Parsing (Frontend)

**JavaScript Parsing**:

```javascript
fetch('/compare', {
  method: 'POST',
  body: JSON.stringify(request)
})
.then(res => res.json())
.then(data => {
  // data.results: array of coverage comparisons
  // data.audit: audit metadata
  displayResults(data.results);
});
```

**Validation** (Optional):

```javascript
function validateResponse(data) {
  if (!data.results || !Array.isArray(data.results)) {
    throw new Error("Invalid response structure");
  }

  data.results.forEach(coverage => {
    if (!coverage.coverage_code || !coverage.values) {
      throw new Error("Missing required fields");
    }
  });

  return true;
}
```

**Output**: Parsed JavaScript object

---

### STEP 9: UI Rendering (Frontend)

**Display Logic**:

```javascript
function renderCoverage(coverage) {
  const table = document.createElement('table');

  // Header
  const header = table.insertRow();
  header.insertCell().textContent = "보험사";
  header.insertCell().textContent = "금액";
  header.insertCell().textContent = "출처";

  // Rows (one per insurer)
  Object.entries(coverage.values).forEach(([insurer, data]) => {
    const row = table.insertRow();

    // Insurer
    row.insertCell().textContent = insurer;

    // Amount (status-based display)
    const amountCell = row.insertCell();
    const displayValue = data.value_text || "금액 명시 없음";
    amountCell.textContent = displayValue;

    // Apply styling based on value_text presence
    if (data.value_text) {
      amountCell.className = "amount-confirmed";
    } else {
      amountCell.className = "amount-unconfirmed";
      amountCell.style.fontStyle = "italic";
      amountCell.style.color = "#666666";
    }

    // Evidence source
    const sourceCell = row.insertCell();
    if (data.evidence?.status === "found") {
      sourceCell.textContent = data.evidence.source;
    } else {
      sourceCell.textContent = "-";
    }
  });

  return table;
}
```

**Styling** (CSS):

```css
.amount-confirmed {
  font-weight: normal;
  color: inherit;
}

.amount-unconfirmed {
  font-style: italic;
  color: #666666;
}

/* ❌ FORBIDDEN: Comparison coloring */
/* .amount-highest { color: green; } */
/* .amount-lowest { color: red; } */
```

**Output**: Rendered HTML table

---

## 🔒 Lock Points (Critical Checkpoints)

### Lock Point 1: Database (amount_fact)

**Status**: 🔒 LOCKED (STEP NEXT-10B-FINAL)

**Rules**:
- ✅ READ-ONLY access
- ❌ NO writes or updates
- ❌ NO recalculation
- ❌ NO schema changes

**Verification**:
```sql
SELECT COUNT(*) FROM amount_fact;
-- Expected: 297 (LOCKED)
```

---

### Lock Point 2: API (AmountDTO)

**Status**: 🔒 LOCKED (STEP NEXT-11)

**Rules**:
- ✅ Status values: CONFIRMED | UNCONFIRMED | NOT_AVAILABLE
- ✅ value_text from amount_fact.value_text ONLY
- ❌ NO status semantics changes
- ❌ NO inference from snippets

**Verification**:
```python
# DTO contract validation
assert amount_dto.status in ["CONFIRMED", "UNCONFIRMED", "NOT_AVAILABLE"]
if amount_dto.status == "CONFIRMED":
    assert amount_dto.value_text is not None
```

---

### Lock Point 3: Explanation (Templates)

**Status**: 🔒 LOCKED (STEP NEXT-12)

**Rules**:
- ✅ Template-based generation ONLY
- ✅ Forbidden words enforced (25+ patterns)
- ❌ NO LLM calls
- ❌ NO comparative language

**Verification**:
```python
# Template validation
for pattern in FORBIDDEN_PATTERNS:
    assert pattern not in explanation.explanation
```

---

### Lock Point 4: UI (Presentation)

**Status**: 🔒 LOCKED (STEP NEXT-13)

**Rules**:
- ✅ Display value_text as-is (NO parsing)
- ✅ Status-based styling ONLY
- ❌ NO color coding for comparison
- ❌ NO sorting by amount
- ❌ NO calculations (average, total)

**Verification**:
```javascript
// UI contract test
const displayedText = element.textContent;
assert(displayedText === apiResponse.value_text || displayedText === "금액 명시 없음");
```

---

## 📊 Data Lineage (Full Trace)

### From Excel to UI

```
Excel (담보명mapping자료.xlsx)
  ↓ STEP 1: load_scope
CSV (data/scope/{insurer}_scope.csv)
  ↓ STEP 2-3: pdf_extract + search
Evidence (data/evidence_pack/{insurer}_pack.jsonl)
  ↓ STEP 4-6: evidence + validation + report
Database (coverage_instance, evidence_ref)
  ↓ STEP 7: Amount Pipeline (LOCKED)
Database (amount_fact, audit_runs)
  ↓ STEP 11: Amount API (LOCKED)
AmountDTO (Python object)
  ↓ STEP 12: Explanation Layer (LOCKED)
InsurerExplanationDTO (Python object)
  ↓ API Response
JSON (HTTP response)
  ↓ Frontend Parsing
JavaScript Object
  ↓ UI Rendering (LOCKED)
HTML (User Browser)
```

**CRITICAL**: Each arrow represents a **LOCKED transformation** (NO modifications allowed).

---

## 🚨 Common Flow Violations (FORBIDDEN)

### Violation 1: Client-Side Amount Parsing

```javascript
// ❌ WRONG
const amountValue = parseInt(data.value_text.replace(/[^0-9]/g, ''));
const average = amounts.reduce((a, b) => a + b) / amounts.length;
```

**Why**: Amount inference is FORBIDDEN (breaks FACT-FIRST principle)

**Correct**:
```javascript
// ✅ CORRECT
const displayValue = data.value_text || "금액 명시 없음";
// Display as-is, NO parsing
```

---

### Violation 2: Database Direct Update

```sql
-- ❌ WRONG
UPDATE amount_fact
SET value_text = '5천만원'
WHERE coverage_instance_id = '...';
```

**Why**: amount_fact is READ-ONLY (LOCKED in STEP NEXT-10B-FINAL)

**Correct**:
```sql
-- ✅ CORRECT (if update needed)
-- Re-run entire Step7 pipeline (requires audit approval)
python -m pipeline.step7_amount_integration.run_all_insurers
```

---

### Violation 3: UI Comparison Language

```html
<!-- ❌ WRONG -->
<div>삼성화재가 KB손해보험보다 더 유리합니다</div>
<div>가장 높은 금액: 3천만원</div>
```

**Why**: Forbidden words (더/보다/유리/가장)

**Correct**:
```html
<!-- ✅ CORRECT -->
<div>삼성화재: 3천만원</div>
<div>KB손해보험: 금액 명시 없음</div>
```

---

## 📞 Support & References

| Layer | Document | Contact |
|-------|----------|---------|
| **Database** | `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md` | DBA Team |
| **API** | `docs/api/AMOUNT_READ_CONTRACT.md` | Backend Team |
| **Explanation** | `docs/ui/COMPARISON_EXPLANATION_RULES.md` | API Team |
| **UI** | `docs/ui/FRONTEND_INTEGRATION_GUIDE.md` | Frontend Team |
| **Deployment** | `docs/deploy/PRODUCTION_DEPLOYMENT.md` | DevOps Team |

---

## 🎯 End-to-End Verification Checklist

- ✅ User input → API request (valid JSON)
- ✅ API request → Database query (READ-ONLY)
- ✅ Database query → amount_fact row (297 rows total)
- ✅ amount_fact → AmountDTO (status contract)
- ✅ AmountDTO → Explanation (template-based)
- ✅ Explanation → JSON response (no forbidden words)
- ✅ JSON response → UI parsing (no errors)
- ✅ UI parsing → HTML render (presentation rules)
- ✅ HTML render → User display (fact-first)

---

**Lock Owner**: All Teams (Full Stack)
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
