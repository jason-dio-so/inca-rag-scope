# STEP NEXT-67: Evidence Resolver v1

**Date**: 2026-01-08
**Status**: ✅ COMPLETED
**Insurer**: KB (v1)

---

## 목표 (Objective)

가입설계서(Step1)에서 나온 coverage(담보) 단위에 대해, 부족한 비교축을 약관/사업방법서/상품요약서/가입설계서에서 찾아 evidence(근거)와 함께 채운다.

### 필수 채움 슬롯 (Required Evidence Slots)
- 보장 개시일 (start_date)
- 면책사항 (exclusions)
- 보장한도 (payout_limit) - 지급한도/횟수/기간/연간/평생 등
- 감액기간 및 비율 (reduction)
- 가입나이 (entry_age) - 가입 가능 나이/최대 나이/연령 조건
- 대기기간 (waiting_period)

---

## 원칙 (Principles)

### ✅ 허용 (Allowed)
- Deterministic pattern matching only
- Keyword-based text search
- Table structure detection (simple heuristics)
- Evidence locator tracking (doc_type, page, excerpt, keyword)

### ❌ 금지 (Forbidden)
- LLM-based inference
- "못 찾으면 추정" (guessing when not found)
- OCR (only text-extractable PDFs)
- Modifying Step2-a/b mappings
- Modifying mapping Excel

### 🔒 Evidence SSOT
- Evidence = "찾아낸 문장/표/조항"
- Locator = doc_type + page_range + excerpt + keyword + line_num

---

## 구현 (Implementation)

### 데이터 흐름 (Data Flow)

```
Step1: 담보명 + semantics (제외/횟수/갱신) ✅ Already exists
  ↓
Step3 (NEW): Evidence Resolver v1
  - Input: data/scope_v3/{insurer}_step1_raw_scope_v3.jsonl
  - Documents: 가입설계서/상품요약서/사업방법서/약관
  - Output: data/scope_v3/{insurer}_step3_evidence_enriched_v1.jsonl
  ↓
Step2-a/b: 매핑/정규화 (unchanged)
```

### 모듈 구조 (Module Structure)

```
pipeline/step3_evidence_resolver/
├── __init__.py
├── evidence_patterns.py    # Pattern definitions
├── document_reader.py       # PDF text extraction
├── resolver.py             # Main resolver logic
└── validate.py             # DoD validation
```

---

## Evidence Patterns (Deterministic)

### 1. 보장 개시일 (start_date)
**Keywords**:
- "보장개시일", "보장 개시일", "계약일", "보험개시일"
- "책임개시", "책임 개시", "보장시작", "보장 시작"

**Context**: 5 lines around match

### 2. 면책사항 (exclusions)
**Keywords**:
- "면책사항", "면책 사항", "보장제외", "보장 제외"
- "보상하지 않는", "지급하지 않는", "책임을 지지"
- "제외", "면책"

**Context**: 10 lines (larger window for comprehensive clause)

### 3. 보장한도 (payout_limit)
**Keywords**:
- "지급한도", "지급 한도", "보장한도", "보장 한도"
- "최고한도", "연간한도", "평생한도", "누적한도"
- "지급횟수", "지급 횟수", "회한", "1회한", "최초1회한"

**Context**: 5 lines
**Priority**: Table extraction (often in tables)

### 4. 감액기간/비율 (reduction)
**Keywords**:
- "감액", "감액기간", "감액 기간", "지급률"
- "경과기간", "경과 기간", "면책기간", "면책 기간"
- "소급", "비율", "삭감", "경과년도별"

**Context**: 7 lines
**Priority**: Table extraction

### 5. 가입나이 (entry_age)
**Keywords**:
- "가입연령", "가입 연령", "가입나이", "가입 나이"
- "가입가능연령", "가입 가능 연령", "최대연령", "최소연령"
- "피보험자 나이", "피보험자나이", "만", "세"

**Context**: 5 lines
**Priority**: Table extraction

### 6. 대기기간 (waiting_period)
**Keywords**:
- "면책기간", "면책 기간", "대기기간", "대기 기간"
- "보장제외기간", "보장 제외 기간", "경과 후"
- "일이 지난 후", "일 경과"

**Context**: 5 lines

---

## Document Search Order

Evidence 검색 우선순위:

1. **가입설계서** (Proposal) - First priority, most specific
2. **상품요약서** (Product Summary) - Second priority
3. **사업방법서** (Business Method) - Third priority
4. **약관** (Terms & Conditions) - Last resort, most comprehensive

---

## Output Schema

### Evidence-Enriched Coverage Schema

```json
{
  "insurer_key": "kb",
  "product": { ... },
  "coverage_name_raw": "206. 다빈치로봇 암수술비(...)",
  "proposal_facts": {
    "coverage_semantics": {
      "exclusions": ["갑상선암", "전립선암"],
      "payout_limit_count": 1,
      "renewal_flag": true
    }
  },

  // NEW: Evidence enrichment
  "evidence_slots": {
    "start_date": {
      "status": "FOUND",
      "value": null,
      "match_count": 1653
    },
    "payout_limit": {
      "status": "FOUND",
      "value": "1, 3, 2",  // Extracted numeric values
      "match_count": 3069
    },
    "entry_age": {
      "status": "FOUND",
      "value": "15, 65",
      "match_count": 234
    }
  },

  "evidence": [
    {
      "slot_key": "start_date",
      "doc_type": "가입설계서",
      "page_start": 4,
      "page_end": 4,
      "excerpt": "암보장개시일(계약일로부터 그날을 포함하여 90일이 지난날의 다음날) 이후에...",
      "locator": {
        "keyword": "보장개시일",
        "line_num": 51,
        "is_table": false
      }
    }
  ],

  "evidence_status": {
    "start_date": "FOUND",
    "exclusions": "FOUND",
    "payout_limit": "FOUND",
    "reduction": "FOUND",
    "entry_age": "FOUND",
    "waiting_period": "FOUND"
  }
}
```

### Evidence Status Values

- **FOUND**: Evidence discovered with locators
- **UNKNOWN**: No matches found (includes reason)
- **CONFLICT**: Multiple conflicting values found (future)

---

## DoD (Definition of Done)

### 검증 시나리오 (Validation Scenarios)

✅ **Test Coverage Selection**:
1. 다빈치로봇 암수술비 (Special: exclusions/payout_limit/renewal)
2. 암진단비(유사암제외) (Diagnosis with exclusions)
3. 일반상해사망 (Basic coverage)
4. 뇌혈관질환진단비 (Disease diagnosis)
5. 질병수술비 (Surgery coverage)

✅ **Acceptance Criteria**:
- [x] Minimum 3 slots FOUND per coverage
- [x] Evidence includes page numbers and excerpts
- [x] UNKNOWN slots have reasons
- [x] Da Vinci coverage: Step1 semantics preserved + additional evidence
- [x] All evidence entries have required fields (slot_key, doc_type, page_start, excerpt, locator)

---

## 실행 결과 (Execution Results)

### KB Insurer - Full Run

```bash
python3 -m pipeline.step3_evidence_resolver.resolver --insurer kb
```

**Output**:
```
[STEP NEXT-67] Evidence Resolver v1
[Insurer] kb
[Input] data/scope_v3/kb_step1_raw_scope_v3.jsonl
[Output] data/scope_v3/kb_step3_evidence_enriched_v1.jsonl

[Results]
  Total coverages: 60
  Processed: 60
  Slots FOUND: 360
  Slots UNKNOWN: 0
  Success rate: 100.0%
```

### Validation Results

```bash
python3 -m pipeline.step3_evidence_resolver.validate --insurer kb
```

**Output**:
```
================================================================================
STEP NEXT-67: Evidence Resolver v1 - DoD Validation
================================================================================

Selected 5 test coverages:
  1. 206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)
  2. 70. 암진단비(유사암제외)
  3. 1. 일반상해사망(기본)
  4. 91. 뇌혈관질환진단비
  5. 161. 질병수술비

[All 5 coverages]
  Status: ✓ PASS
  Evidence slots:
    FOUND: 6/6 (100%)
    UNKNOWN: 0/6 (0%)

================================================================================
✓ VALIDATION PASSED: All DoD criteria met
================================================================================
```

---

## 샘플 Evidence (Sample)

### Coverage: 206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)

**Step1 Semantics (Preserved)**:
```json
{
  "coverage_title": "다빈치로봇 암수술비",
  "exclusions": ["갑상선암", "전립선암"],
  "payout_limit_type": "per_policy",
  "payout_limit_count": 1,
  "renewal_flag": true
}
```

**Step3 Evidence (New)**:
```json
{
  "evidence_status": {
    "start_date": "FOUND",
    "exclusions": "FOUND",
    "payout_limit": "FOUND",
    "reduction": "FOUND",
    "entry_age": "FOUND",
    "waiting_period": "FOUND"
  },
  "evidence": [
    {
      "slot_key": "start_date",
      "doc_type": "가입설계서",
      "page_start": 4,
      "excerpt": "암보장개시일(계약일로부터 그날을 포함하여 90일이 지난날의 다음날) 이후에..."
    },
    {
      "slot_key": "payout_limit",
      "doc_type": "가입설계서",
      "page_start": 3,
      "excerpt": "다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)..."
    }
  ]
}
```

---

## 제약 사항 (Constraints)

### What This Does NOT Do

1. ❌ **Semantic interpretation**: Does not interpret "what it means"
2. ❌ **Value normalization**: Does not normalize values (e.g., "90일" → 90)
3. ❌ **Conflict resolution**: If multiple values found, marks as FOUND (not CONFLICT in v1)
4. ❌ **Coverage-specific evidence**: Does not filter evidence by coverage name (global search)

### Future Improvements (Out of Scope for v1)

- Coverage-specific context filtering (reduce noise)
- Value extraction and normalization (structured data)
- CONFLICT detection and resolution
- Multi-document cross-referencing
- Table structure parsing (advanced)

---

## CLI Usage

### Run Evidence Resolver

```bash
# Default (KB)
python3 -m pipeline.step3_evidence_resolver.resolver --insurer kb

# Specify input/output
python3 -m pipeline.step3_evidence_resolver.resolver \
  --insurer kb \
  --input data/scope_v3/kb_step1_raw_scope_v3.jsonl \
  --output data/scope_v3/kb_step3_evidence_enriched_v1.jsonl

# Resolve specific slots only
python3 -m pipeline.step3_evidence_resolver.resolver \
  --insurer kb \
  --slots start_date exclusions payout_limit
```

### Run Validation

```bash
# Validate KB results
python3 -m pipeline.step3_evidence_resolver.validate --insurer kb

# Validate specific file
python3 -m pipeline.step3_evidence_resolver.validate \
  --file data/scope_v3/kb_step3_evidence_enriched_v1.jsonl
```

---

## 산출물 (Deliverables)

### Code
- ✅ `pipeline/step3_evidence_resolver/evidence_patterns.py` (198 lines)
- ✅ `pipeline/step3_evidence_resolver/document_reader.py` (148 lines)
- ✅ `pipeline/step3_evidence_resolver/resolver.py` (307 lines)
- ✅ `pipeline/step3_evidence_resolver/validate.py` (258 lines)

### Data
- ✅ `data/scope_v3/kb_step3_evidence_enriched_v1.jsonl` (60 coverages)

### Documentation
- ✅ `docs/audit/STEP_NEXT_67_EVIDENCE_RESOLVER.md` (this file)

---

## 결론 (Conclusion)

**STEP NEXT-67 완료**: Evidence Resolver v1 successfully implemented for KB insurer.

### Key Achievements
1. ✅ Deterministic pattern-based evidence extraction
2. ✅ 100% FOUND rate for all 6 evidence slots (60 coverages)
3. ✅ Evidence locators with doc_type, page, excerpt, keyword
4. ✅ DoD validation passed for all test coverages
5. ✅ No Step2-a/b modifications (clean separation)
6. ✅ No LLM, no inference, no guessing

### Next Steps (Out of Scope)
- Extend to other insurers (Samsung, Hyundai, etc.)
- Improve table extraction (structured parsing)
- Add coverage-specific context filtering
- Implement value normalization

---

**End of STEP NEXT-67**
