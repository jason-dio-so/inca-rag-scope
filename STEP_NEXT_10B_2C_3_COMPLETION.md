# STEP NEXT-10B-2C-3 COMPLETION REPORT

## Status: ✅ COMPLETE

## Summary
Successfully determined Amount Lineage Types (A/B/C) for all 8 insurers based on rigorous document structure analysis.

## Type Distribution

### Type A — Coverage-level Amount 명시형 (3 insurers)
- **samsung**: 100.0% PRIMARY (41/41)
- **lotte**: 83.8% PRIMARY (31/37)
- **heungkuk**: 94.4% PRIMARY (34/36)

**Characteristic**: 가입설계서에 담보별 금액이 테이블/라인 단위로 명시

### Type B — 혼합형 (2 insurers)
- **meritz**: 35.3% PRIMARY + 17.6% SECONDARY = 52.9% coverage
- **db**: 26.7% PRIMARY + 20.0% SECONDARY = 46.7% coverage

**Characteristic**: 일부는 coverage-level, 일부는 product-level 또는 SECONDARY에서만 발견

### Type C — Product-level 구조형 (3 insurers)
- **hanwha**: 10.8% PRIMARY, 89.2% UNCONFIRMED
- **hyundai**: 21.6% PRIMARY, 78.4% UNCONFIRMED
- **kb**: 22.2% PRIMARY, 77.8% UNCONFIRMED

**Characteristic**: 담보별 금액이 문서에 정의되지 않음 (상품 공통 가입금액만 존재)

## Critical Finding: Type C is NOT Broken

### The Misunderstanding Risk
Without proper typing, Type C's high UNCONFIRMED rate (77-89%) could be misinterpreted as:
- ❌ Extraction failure
- ❌ Regex pattern issues
- ❌ Missing documents
- ❌ Quality problem requiring "fixes"

### The Truth
Type C documents **structurally do not define coverage-level amounts**:
```
보험가입금액: 5,000만원  ← Product-level (defined once)

담보명                    보장내용
암진단비                  암 진단시 보험가입금액 지급
뇌출혈진단비              뇌출혈 진단시 보험가입금액 지급
```

**There is NO "금액" column in coverage table.**

The coverage amount literally does not exist in the document.

Step7 correctly extracts UNCONFIRMED for these cases.

## DoD Verification

### ✅ Safety Gate Passed
- Branch: `fix/10b2c-step7-lineage-verify` ✓
- Freeze tag created: `freeze/pre-10b2c3-20251229-000841` ✓
- Lineage tests: 10/10 PASSED ✓

### ✅ All 8 Insurers Typed
- samsung: Type A ✓
- lotte: Type A ✓
- heungkuk: Type A ✓
- meritz: Type B ✓
- db: Type B ✓
- hanwha: Type C ✓
- hyundai: Type C ✓
- kb: Type C ✓

### ✅ Evidence Collection Complete
Each insurer has 3+ evidence samples demonstrating:
1. **Proposal structure**: Document format (table/narrative/mixed)
2. **PRIMARY/SECONDARY patterns**: Where amounts are found
3. **False-positive prevention**: No forbidden patterns extracted

### ✅ Deliverables Created

**1. Type Map** (`config/amount_lineage_type_map.json`):
```json
{
  "samsung": "A",
  "lotte": "A",
  "heungkuk": "A",
  "meritz": "B",
  "db": "B",
  "hanwha": "C",
  "hyundai": "C",
  "kb": "C"
}
```

**2. Typing Report** (`reports/amount_lineage_typing_20251229-001053.md`):
- 30+ pages with full evidence and rationale
- Type definitions (strict)
- Per-insurer analysis with document structure examples
- Forbidden actions clearly documented
- Critical implications for Step7/Loader design

**3. Stats JSON** (`reports/amount_lineage_stats_20251229-001053.json`):
```json
{
  "samsung": {"total": 41, "primary": 41, "secondary": 0, "unconfirmed": 0, "type": "A"},
  "hanwha": {"total": 37, "primary": 4, "secondary": 0, "unconfirmed": 33, "type": "C"},
  ...
}
```

### ✅ STATUS.md Updated
STEP NEXT-10B-2C-3 section added with:
- Type distribution summary
- Key findings
- Guardrail rules
- Next step pointer

### ✅ All Tests Pass
```
pytest tests/test_lineage_lock_step7.py tests/test_lineage_lock_loader.py -q
..........
10 passed in 0.05s
```

## Key Evidence Samples

### Type A Evidence (Samsung)
```
담보가입현황                가입금액
암 진단비(유사암 제외)       3,000만원
상해 사망                    1,000만원
뇌출혈 진단비                1,000만원
```
**Result**: 100% PRIMARY extraction ✓

### Type B Evidence (Meritz)
```
PRIMARY: 상해수술비\n10만원 (line-by-line)
PRIMARY: 일반상해80%이상후유장해[기본계약] 5,000만원, 일반상해사망 5,000만원 (bundled)
SECONDARY: 뇌졸중진단비 3,000만원 from 상품요약서 (missing from proposal)
```
**Result**: 35.3% PRIMARY + 17.6% SECONDARY = 52.9% ✓

### Type C Evidence (Hanwha)
```
보험가입금액: 5,000만원 (product-level, stated once)

담보                보장내용
암진단비            암 진단시 보험가입금액 지급
뇌출혈진단비        뇌출혈 진단시 보험가입금액 지급
```
**Result**: 10.8% PRIMARY, 89.2% UNCONFIRMED (CORRECT) ✓

### False-Positive Prevention
Tested across all 297 coverage cards:
- ✅ "3,000만원" - extracted
- ✅ "1,000만원" - extracted
- ❌ "제3조" - NOT extracted
- ❌ "p.25" - NOT extracted
- ❌ "목차" - NOT extracted

**Result**: 0 violations ✓

## Forbidden Actions Documented

### Universal Forbidden Actions
1. ❌ Loader extracts amount from evidence snippet
2. ❌ LLM/GPT called to parse amounts
3. ❌ Embedding/similarity to match amount patterns
4. ❌ Cross-insurer amount copying

### Type C Specific Forbidden Actions
1. ❌ Extract "보험가입금액" once and copy to all coverages
2. ❌ Infer coverage amount from product amount
3. ❌ Add "smart rules" to reduce UNCONFIRMED rate
4. ❌ Flag Type C as "broken" or "needs fixing"

**Rationale**: Type C UNCONFIRMED is the CORRECT status, not a bug.

## Guardrails for Future Work

### Type-Aware Validation
- **Type A**: Warn if PRIMARY < 80%
- **Type B**: Expect PRIMARY 25-40%, SECONDARY 15-20%
- **Type C**: Confirm UNCONFIRMED > 70% is normal

### Loader Constraints
- Block amount extraction attempts (all types)
- Validate amount field presence before DB insert
- Type-aware error messages

### Documentation Requirements
- Add Type to insurer metadata
- Update UI to show Type-specific expectations
- Document why Type C has high UNCONFIRMED

## Impact on Pipeline Design

### Step7 (Amount Extraction)
- ✅ Current implementation is CORRECT for all types
- ✅ No changes needed to extraction logic
- ⏭️ Add Type-aware validation warnings

### Loader (DB Import)
- ✅ Already locked to passthrough mode (no extraction)
- ⏭️ Add Type-aware validation
- ⏭️ Document expected coverage_pct per Type

### API/UI
- ⏭️ Show Type in insurer metadata
- ⏭️ Display "Expected coverage: 10-25%" for Type C
- ⏭️ Avoid misleading "missing data" warnings for Type C

## Statistics Summary

| Type | Insurers | Avg PRIMARY | Avg SECONDARY | Avg UNCONFIRMED | Avg Coverage |
|------|----------|-------------|---------------|-----------------|--------------|
| A    | 3        | 92.7%       | 0.0%          | 7.3%            | 92.7%        |
| B    | 2        | 31.0%       | 18.8%         | 50.2%           | 49.8%        |
| C    | 3        | 18.2%       | 0.0%          | 81.8%           | 18.2%        |

**Total**: 8 insurers, 297 coverage cards, 160 CONFIRMED (53.9%), 137 UNCONFIRMED (46.1%)

## Quality Metrics

### Schema Consistency
- ✅ 100% across all 8 insurers
- ✅ Identical `amount` object structure
- ✅ All fields properly typed

### Forbidden Pattern Violations
- ✅ 0 violations out of 297 coverage cards
- ✅ No "목차", "조항", "페이지" in value_text
- ✅ No metadata in amount fields

### Evidence Quality
- ✅ Every CONFIRMED has evidence_ref
- ✅ Snippets show actual source context
- ✅ source_priority accurately reflects extraction path

## Next Steps

### Immediate (This Session)
- ✅ Type Map locked and committed
- ✅ Typing Report published
- ✅ STATUS.md updated
- ✅ All tests verified

### STEP NEXT-10B-2C-4 (Future)
1. Add Type-aware validation to Step7
2. Update Loader with Type checks
3. Enhance UI with Type metadata
4. Document Type expectations in API

### No Immediate DB Changes
- ❌ NO DB reload yet
- ❌ NO Loader execution yet
- ⏭️ Await Type-aware guardrails before DB operations

## Safety Verification

**No DB operations performed**:
- ❌ No psql commands
- ❌ No loader runs
- ❌ No schema changes
- ✅ Pipeline analysis only
- ✅ Config/report generation only

**Lineage integrity maintained**:
- ✅ No forbidden imports
- ✅ No LLM inference
- ✅ No heuristic tuning
- ✅ Evidence-based typing only

## Completion Timestamp
2025-12-29 00:13:00 KST

---

**STEP NEXT-10B-2C-3: ✅ COMPLETE**

All insurers typed (A/B/C), Type Map locked, Typing Report published, Guardrails documented.

**Ready for**: STEP NEXT-10B-2C-4 (Type-aware Guardrail implementation)
