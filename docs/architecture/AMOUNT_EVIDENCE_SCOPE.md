# Amount Evidence Scope Definition

**Purpose**: Define what constitutes VALID vs INVALID amount evidence for coverage_cards.jsonl enrichment.

**Context**: STEP NEXT-19 introduced multiline fragment merge. This document clarifies the **scope of application**.

---

## VALID Evidence (Proof-Grade)

Amount evidence is VALID **if and only if ALL 3 conditions are met**:

### 1. Document Type = 가입설계서 (Proposal)

```python
# Code reference: extract_and_enrich_amounts.py:211-212
proposal_page_jsonl = Path(f"data/evidence_text/{insurer}/가입설계서/{insurer}_가입설계서_*.page.jsonl")
```

**Reasoning**: Proposals are the ONLY authoritative source for "가입금액" (coverage amount).

**Counter-examples** (INVALID):
- 약관 (policy terms) — contains 보험금 지급액 (claim amounts), not 가입금액
- 사업방법서 (business methods) — no amount data
- 상품요약서 (product summary) — no amount data

### 2. Semantic Context = 가입금액 Column

**VALID contexts** (code ref: `extract_and_enrich_amounts.py:222`):
```python
if any(kw in text for kw in ['가입금액', '보험가입금액', '보장금액', '담보가입현황', '담보별 보장내용']):
```

**INVALID contexts** (excluded by code at line 232):
- 보험료 (premium)
- 납입기간 (payment period)
- 해약환급금 (surrender value)
- 책임준비금 (reserve)
- 담보코드 (coverage code)
- 페이지 번호 (page number)
- 보험나이 (insurance age)

### 3. Coverage Association = Mapped to coverage_code

**Validation path** (code ref: `extract_and_enrich_amounts.py:354-366`):

```python
# Step 1: Extract (coverage_name_raw, amount_text) from proposal
pair = ProposalAmountPair(coverage_name_raw="뇌졸중진단비", amount_text="1,000만원")

# Step 2: Match to coverage_code via scope_mapped.csv
coverage_map[normalize("뇌졸중진단비")] = ("A4103", "뇌졸중진단비")

# Step 3: Link to coverage_card
code_to_amount["A4103"] = ("1,000만원", page_num, snippet)
```

**INVALID**: Amount extracted but NO matching coverage_code in scope_mapped.csv

---

## VALID Evidence Examples (Real Data)

### Example 1: Hanwha — 상해후유장해(3-100%)

**Source**: `data/evidence_text/hanwha/가입설계서/한화_가입설계서_2511.page.jsonl`, page 3

**Raw text** (multiline fragment):
```
상해후유장해(3-100%)    1,
000만원    500원    100세만기 / 20년납
```

**Extracted**:
- coverage_name_raw: `"상해후유장해(3-100%)"`
- amount_text: `"1,000만원"` (merged from `"1,"` + `"000만원"`)
- page_num: 3
- snippet: `"상해후유장해(3-100%) / 1,000만원"`

**Mapped to**:
- coverage_code: `A3300_1`
- coverage_name_canonical: `"상해후유장해(3-100%)"`

**Result in coverage_card**:
```json
{
  "insurer": "hanwha",
  "coverage_code": "A3300_1",
  "amount": {
    "status": "CONFIRMED",
    "value_text": "1,000만원",
    "source_doc_type": "가입설계서",
    "source_priority": "proposal_table",
    "evidence_ref": {
      "page_num": 3,
      "snippet": "상해후유장해(3-100%) / 1,000만원"
    }
  }
}
```

✅ **ALL 3 CONDITIONS MET**: Document type (proposal) + Semantic context (가입금액) + Coverage association (A3300_1)

### Example 2: Hanwha — 뇌졸중진단비

**Source**: Same file, page 3

**Raw text**:
```
251 뇌졸중진단비    1,
000만원    7,450원    100세만기 / 20년납
```

**Extracted**:
- coverage_name_raw: `"뇌졸중진단비"` (number prefix "251" removed)
- amount_text: `"1,000만원"` (merged)
- page_num: 3
- snippet: `"251 뇌졸중진단비 / 1,000만원"`

**Mapped to**: `A4103`

✅ **VALID** — Same reasoning as Example 1

---

## INVALID Evidence Examples (Counter-Cases)

### Counter-Example 1: Premium Amount (보험료)

**Source**: Same file, page 3

**Raw text**:
```
뇌졸중진단비    1,000만원    7,
450원    100세만기
```

**Fragment detected**: `"7,"` + `"450원"`

❌ **INVALID** — Semantic context is "보험료" (premium), NOT "가입금액"

**Code behavior**: Skipped at line 232 (header filter) OR not extracted because lookback finds premium context

### Counter-Example 2: Page Number Fragment

**Source**: Proposal page footer

**Raw text**:
```
확인필-제2025-상품지원-기타(안내,교육)01389E-전사(25.03.31~ 26.
03.30)
```

**Fragment detected**: `"26."` + potential merge

❌ **INVALID** — No Korean coverage name in lookback (line 249: `re.search(r'[가-힣]', prev_line)`)

**Code behavior**: Skipped at line 253 (no coverage_candidate)

### Counter-Example 3: Policy Term Amount (약관)

**Source**: `data/evidence_text/hanwha/약관/한화_약관.page.jsonl`

**Raw text**:
```
뇌졸중으로 진단확정된 경우 보험가입금액 지급
1,
000만원
```

❌ **INVALID** — Document type is NOT 가입설계서

**Code behavior**: Never scanned (only `*_가입설계서_*.page.jsonl` files are processed)

---

## Scope Summary

| Category | Count | VALID? | Reason |
|---|---|---|---|
| Proposal table amounts | ~30-40/insurer | ✅ | All 3 conditions met |
| Premium amounts | N/A | ❌ | Semantic context wrong |
| Policy term amounts | N/A | ❌ | Document type wrong |
| Page numbers | N/A | ❌ | No coverage association |
| Header/footer text | N/A | ❌ | Filtered at line 232 |

**STEP NEXT-19 Merge Scope**: Applied ONLY to proposal table amounts (VALID category).

**Non-Merge Amounts**: Single-line amounts (e.g., `"3천만원"`) are also VALID if all 3 conditions met.

---

## Verification Checklist

Before marking an amount as "CONFIRMED" in coverage_card:

- [ ] `source_doc_type == "가입설계서"`
- [ ] Amount appears in table context (not header/footer/premium)
- [ ] `coverage_code` exists in scope_mapped.csv
- [ ] `evidence_ref.snippet` shows coverage_name + amount pair

If ANY condition fails → `status: "UNCONFIRMED"` with empty `value_text`.
