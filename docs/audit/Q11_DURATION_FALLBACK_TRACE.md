# Q11 Duration Fallback & Phase-1 Insurer Coverage

**Date**: 2026-01-14
**Task**: STEP DEMO-Q11-EVIDENCE-TRUST-02
**Status**: ✅ COMPLETE

---

## Problem Statement

### Issue A: Heungkuk Duration UNKNOWN

Q11 endpoint returned `heungkuk.duration_limit_days.status = "UNKNOWN"` and `value = null` despite evidence text containing:
- "암직접치료입원비(요양병원제외)(1일-180일)"
- "※ 180일 한도"

**Root Cause**: Duration value was null in core model, but duration text patterns existed in `daily_benefit_amount_won.evidences`.

### Issue B: Missing Insurers

Q11 returned only 7 items instead of Phase-1 8 insurers. Lotte was completely missing because it doesn't have coverage A6200 in proposal documents.

### Issue C: DB Duplicate

DB appeared twice in items (db_over41 and db_under40 both have A6200).

---

## Solution Applied

### A) Evidence-Based Duration Fallback

**Implementation**: `apps/api/server.py:1106-1140, 1288-1325`

#### Extraction Function

```python
def extract_duration_from_evidence_text(text: str) -> Optional[int]:
    """
    STEP DEMO-Q11-EVIDENCE-TRUST-02: Extract duration limit from evidence text

    Patterns supported:
    - "1일-180일" (hyphen range)
    - "1~180일" (tilde range)
    - "180일 한도"
    - "1일이상180일한도"
    - "최대180일"
    """
    patterns = [
        r'(\d+)\s*일\s*한도',  # "180일한도", "90일 한도"
        r'1\s*일?\s*-\s*(\d+)\s*일',  # "1일-180일", "1-180일" (hyphen)
        r'1\s*~\s*(\d+)\s*일',  # "1~180일" (tilde)
        r'1\s*일\s*이상\s*(\d+)\s*일\s*한도',  # "1일이상180일한도"
        r'최대\s*(\d+)\s*일',  # "최대180일"
    ]
    # ... regex matching logic
```

#### Fallback Source Priority

When `duration_limit_days.value` is null, extract from evidence sources in priority order:

1. **Source 1**: `duration_limit_days.evidences` (highest priority)
2. **Source 2**: `item.evidence` (global evidence)
3. **Source 3**: `daily_benefit_amount_won.evidences` (fallback)

#### Application Logic

```python
# After building each item (line 1288)
if item['duration_limit_days']['value'] is None:
    duration_extracted = None
    matched_evidence = None

    # Try each source in priority order
    for ev in days_evidences:
        excerpt = ev.get('excerpt', '')
        extracted = extract_duration_from_evidence_text(excerpt)
        if extracted:
            duration_extracted = extracted
            matched_evidence = ev
            break

    # Apply if found
    if duration_extracted and matched_evidence:
        item['duration_limit_days']['status'] = 'FOUND'
        item['duration_limit_days']['value'] = duration_extracted
        item['duration_limit_days']['evidences'] = [matched_evidence]
```

**Key Principles**:
- ✅ Evidence-first: Only extract from actual evidence text
- ✅ No inference: Regex-based pattern matching only
- ✅ Fact-only: No LLM, no estimation
- ✅ Single evidence: Attach only the matched evidence (not all 3)

---

### B) Phase-1 8 Insurers Always Visible

**Implementation**: `apps/api/server.py:1345-1386`

#### Deduplication

Before adding placeholders, deduplicate by `insurer_key` (e.g., db_over41 → db, db_under40 → db):

```python
# Priority: FOUND status > evidence exists > higher benefit value
items_by_insurer = {}
for item in items:
    key = item['insurer_key']
    if key not in items_by_insurer:
        items_by_insurer[key] = item
    else:
        # Compare and keep higher priority item
        # ...
```

#### Placeholder Items

For insurers missing from items (e.g., lotte):

```python
PHASE1_INSURERS = ['kb', 'samsung', 'hyundai', 'db', 'meritz', 'hanwha', 'heungkuk', 'lotte']

missing_insurers = [ins for ins in PHASE1_INSURERS if ins not in present_insurers]

for insurer_key in missing_insurers:
    placeholder_item = {
        "insurer_key": insurer_key,
        "coverage_code": "A6200",
        "coverage_name": "암직접치료입원비",
        "product_full_name": {
            "value": product_meta.get('product_name_display', '상품명 확인 불가'),
            "evidence": product_meta.get('evidence', {})
        },
        "duration_limit_days": {"status": "UNKNOWN", "value": None, "evidences": []},
        "daily_benefit_amount_won": {"status": "UNKNOWN", "value": None, "evidences": []},
        "evidence": None,
        "badge": "NOT_IN_PROPOSAL",
        "note": "가입설계서에 미포함"
    }
    items.append(placeholder_item)
```

---

## Verification Results

### A-4: Heungkuk Duration Check

```bash
curl -s http://127.0.0.1:8000/q11 | jq '.items[] | select(.insurer_key=="heungkuk") | {duration_limit_days, daily_benefit_amount_won}'
```

**Output**:
```json
{
  "duration_limit_days": {
    "status": "FOUND",
    "value": 180,
    "evidences": [
      {
        "doc_type": "가입설계서",
        "page": 12,
        "excerpt": "...(1일-180일)...2만원...",
        "source_slot": "daily_benefit_amount_won"
      }
    ]
  }
}
```

**Verification**:
- ✅ `status` == "FOUND"
- ✅ `value` == 180
- ✅ `evidences.length` == 1
- ✅ excerpt contains "1일-180일"

### B-3: Phase-1 8 Insurers Check

```bash
curl -s http://127.0.0.1:8000/q11 | jq '.items | length'
# Output: 8

curl -s http://127.0.0.1:8000/q11 | jq '.items[].insurer_key' -r | sort
# Output:
# db
# hanwha
# heungkuk
# hyundai
# kb
# lotte
# meritz
# samsung
```

**Verification**:
- ✅ `length` == 8
- ✅ All Phase-1 insurers present
- ✅ `lotte` included
- ✅ `hanwha` included (moved from references to items with badge)

### Complete Q11 Response

```bash
curl -s http://127.0.0.1:8000/q11 | jq '.items[] | {insurer_key, duration: .duration_limit_days.value, benefit: .daily_benefit_amount_won.value, badge}'
```

| Insurer | Duration | Benefit | Badge |
|---------|----------|---------|-------|
| hyundai | 180 | 100,000 | - |
| heungkuk | **180** | 20,000 | - |
| kb | 180 | 10,000 | - |
| samsung | 30 | 100,000 | - |
| db | null | 3,000,000 | - |
| meritz | null | 140,000 | - |
| hanwha | null | null | **NOT_IN_PROPOSAL** |
| lotte | null | null | **NOT_IN_PROPOSAL** |

---

## Before / After Comparison

### Before (STEP DEMO-Q11-BACKEND-FIX-02 Analysis)

**Q11 Response**:
```json
{
  "items": [
    // 7 items only (lotte missing)
    {
      "insurer_key": "db",  // Duplicate 1
      ...
    },
    {
      "insurer_key": "db",  // Duplicate 2
      ...
    },
    {
      "insurer_key": "heungkuk",
      "duration_limit_days": {
        "status": "UNKNOWN",  // ❌ WRONG
        "value": null,        // ❌ WRONG
        "evidences": []       // ❌ EMPTY
      }
    }
  ],
  "references": [
    {"insurer_key": "hanwha", ...}  // In references, not items
  ]
}
```

**Issues**:
- ❌ Heungkuk duration UNKNOWN (despite evidence containing "1일-180일")
- ❌ Only 7 insurers in items
- ❌ Lotte completely missing
- ❌ DB duplicate (2 items)
- ❌ Hanwha in references, not items

### After (STEP DEMO-Q11-EVIDENCE-TRUST-02)

**Q11 Response**:
```json
{
  "items": [
    // 8 items (Phase-1 complete)
    {
      "insurer_key": "heungkuk",
      "duration_limit_days": {
        "status": "FOUND",      // ✅ FIXED
        "value": 180,           // ✅ EXTRACTED FROM EVIDENCE
        "evidences": [{         // ✅ MATCHED EVIDENCE ATTACHED
          "doc_type": "가입설계서",
          "page": 12,
          "excerpt": "...(1일-180일)...",
          "source_slot": "daily_benefit_amount_won"
        }]
      }
    },
    {
      "insurer_key": "lotte",   // ✅ ADDED
      "duration_limit_days": {"status": "UNKNOWN", "value": null, "evidences": []},
      "badge": "NOT_IN_PROPOSAL",
      "note": "가입설계서에 미포함"
    },
    {
      "insurer_key": "hanwha",  // ✅ MOVED FROM REFERENCES
      "duration_limit_days": {"status": "UNKNOWN", "value": null, "evidences": []},
      "badge": "NOT_IN_PROPOSAL",
      "note": "가입설계서에 미포함"
    }
    // Only 1 DB item (deduplication applied)
  ],
  "references": []  // Empty (all moved to items)
}
```

**Fixed**:
- ✅ Heungkuk duration = 180 (extracted from evidence)
- ✅ 8 Phase-1 insurers in items
- ✅ Lotte included with badge
- ✅ Hanwha moved to items with badge
- ✅ DB deduplicated (only 1 item)

---

## Files Changed

1. **`apps/api/server.py`**
   - Lines 1106-1140: Added `extract_duration_from_evidence_text()` function
   - Lines 1155: Updated docstring (evidence-based fallback)
   - Lines 1288-1325: Evidence-based fallback extraction logic
   - Lines 1345-1373: Deduplication by insurer_key
   - Lines 1375-1386: Phase-1 insurer placeholder items

---

## Constitutional Compliance

- ✅ **Evidence-first**: Duration extracted from actual evidence text, not inference
- ✅ **No inference**: Regex-based pattern matching only
- ✅ **Fact-only**: No LLM, no estimation, no scoring
- ✅ **Single evidence**: Only the matched evidence attached (not all 3)
- ✅ **UNKNOWN transparency**: Lotte/Hanwha show badge="NOT_IN_PROPOSAL" + note
- ✅ **Minimal change**: Backend-only fix, no pipeline regeneration required

---

## Testing Notes

### Pattern Extraction Tests

```python
# Test cases verified
assert extract_duration_from_evidence_text("암직접치료입원비(1일-180일)") == 180  # ✓ Hyphen
assert extract_duration_from_evidence_text("1~180일") == 180  # ✓ Tilde
assert extract_duration_from_evidence_text("180일 한도") == 180  # ✓ Limit
assert extract_duration_from_evidence_text("1일이상180일한도") == 180  # ✓ KB style
assert extract_duration_from_evidence_text("최대90일") == 90  # ✓ Max
```

### Edge Cases

| Case | Duration Evidence | Result |
|------|-------------------|--------|
| Heungkuk | In benefit evidences (fallback) | ✅ Extracted 180 |
| KB | In duration evidences (direct) | ✅ Extracted 180 |
| Hyundai | In duration evidences | ✅ Extracted 180 |
| Samsung | In duration evidences | ✅ Extracted 30 |
| DB | No match | ✅ Remains null |
| Meritz | No match | ✅ Remains null |
| Lotte | No evidence (not in proposal) | ✅ Badge + note |
| Hanwha | No evidence (not in proposal) | ✅ Badge + note |

---

## Known Limitations

### Current Implementation

- ✅ Extracts duration from evidence fallback sources
- ✅ All Phase-1 8 insurers always visible
- ✅ Placeholder items for missing insurers
- ✅ Deduplication by insurer_key

### NOT Implemented

- ❌ Duration fallback for other Q endpoints (Q5/Q7/Q8)
- ❌ Multi-pattern extraction (e.g., "1~90일" + "최대180일" → pick higher)
- ❌ Warning if evidence source is fallback (currently silent, only `source_slot` added)

**Rationale**: Q11 is highest priority for demo. Other Q endpoints can adopt the same pattern if needed.

---

## Sign-Off

**Backend Implementation**: ✅ COMPLETE
**Duration Fallback**: ✅ WORKING (heungkuk 180 extracted)
**Phase-1 Coverage**: ✅ WORKING (8 insurers visible)
**Deduplication**: ✅ WORKING (DB no longer duplicate)
**Evidence Relevance**: ✅ MAINTAINED (slot-level top-1 filtering in frontend)

**DoD Checklist**:
- [✅] Heungkuk duration = 180 with evidence
- [✅] Q11 returns 8 items (Phase-1)
- [✅] Lotte included with badge
- [✅] Hanwha included with badge
- [✅] DB deduplicated
- [✅] Evidence-based extraction (no inference)
- [✅] Curl verification commands pass

**Next Action**: Manual UI testing to verify demo trust and evidence relevance display.

---

**END OF TRACE DOCUMENT**
