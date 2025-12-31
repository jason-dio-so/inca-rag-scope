# PIPELINE ALIGNMENT AUDIT — 가입설계서 담보 추출 중심 구조 재검토

**Date**: 2025-12-30
**Purpose**: 현재 pipeline이 "가입설계서에서 담보 추출 → canonical 정합 → 이후 처리" 목표와 구조적으로 일치하는지 전면 재검토
**Scope**: 구조 분석 (코드 수정 ❌, 단건 버그 수정 ❌, 임시 패치 금지)

---

## 🎯 Executive Summary

### 핵심 발견
1. **담보 정의 주체 분산**: 담보의 "존재"와 "정체성"이 3개 step에 분산 (Step0/Step1 추출, Step2 매핑, Step5 카드 생성)
2. **Proposal 명칭 vs Canonical 명칭 간극**: Step2 mapping은 **exact/normalized 일치**만 지원, alias layer 없음
3. **Hanwha/Heungkuk 구조적 한계**: 가입설계서 명칭 ≠ mapping 자료 명칭 → **구조적으로 매칭 불가능**

### 현재 구조로 가능한 것
- ✅ 가입설계서 테이블에서 담보명 추출 (table-based filtering 정착)
- ✅ Mapping 자료에 등록된 alias와 exact/normalized 매칭
- ✅ Matched 담보에 대한 evidence 검색 + amount 추출

### 현재 구조로 불가능한 것
- ❌ Mapping 자료에 없는 proposal 명칭 자동 해석
- ❌ "4대유사암" ↔ "유사암(8대)" 같은 semantic equivalence 추론
- ❌ Fuzzy matching (의도적 금지 by SSOT contract)

---

## 1️⃣ Pipeline Step-by-Step Analysis

### **STEP 0: Scope Filter** (coverage_candidate_filter.py)

#### Input
- `data/evidence_text/{insurer}/가입설계서/*.page.jsonl` (PDF 텍스트 추출 결과)

#### Output
- `data/scope/{insurer}_scope.csv` (filtered coverage candidates)

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **YES** - 무엇이 담보인지 / 무엇이 아닌지 결정 |
| Business Logic 포함? | **YES** - EXCLUSION_PATTERNS (condition sentences, explanations) |
| 회사별 포맷 차이 책임? | **NO** - 패턴은 범용, 회사 특화 로직 없음 |

#### Logic Summary
```python
# Hard Rules (lines 53-74)
EXCLUSION_PATTERNS = [
    (r'(으로|로)\s*진단확정된\s*경우', 'CONDITION_SENTENCE'),  # 조건문
    (r'(인|한)\s*경우$', 'CONDITION_SENTENCE'),
    (r'시$', 'CONDITION_SENTENCE'),
    (r'다\.$', 'SENTENCE_ENDING'),                          # 문장 종결
    (r'보장개시일\s*이후', 'EXPLANATION_PHRASE'),           # 설명문
    (r'납입면제대상', 'PREMIUM_WAIVER'),                    # 비담보
]

# Source validation (lines 100-102)
if candidate.source_type == 'paragraph':  # NOT table
    return FilterResult(candidate, False, 'NON_TABLE_SOURCE')
```

#### Key Insight
- **담보 "존재" 1차 판정**: table row에서 나왔고, condition/explanation 패턴 미포함 → 담보 후보
- **정체성 판정은 안 함**: 이름만 추출, 어떤 담보인지는 Step2에 위임

---

### **STEP 1-sanitize: Sanitize Scope** (step1_sanitize_scope/run.py)

#### Input
- `data/scope/{insurer}_scope_mapped.csv` (mapping 후 결과)

#### Output
- `data/scope/{insurer}_scope_mapped.sanitized.csv` (정제된 scope)
- `data/scope/{insurer}_scope_filtered_out.jsonl` (제거 audit trail)

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **YES** - 추가 condition sentence 제거 |
| Business Logic 포함? | **YES** - DROP_PATTERNS (step0과 유사하지만 더 강화) |
| 회사별 포맷 차이 책임? | **NO** - 범용 패턴 적용 |

#### Logic Summary
```python
# DROP patterns (lines 34-55)
DROP_PATTERNS = [
    (r'(으로|로)\s*진단확정된\s*경우', 'CONDITION_DIAGNOSIS'),
    (r'(인|한)\s*경우$', 'CONDITION_CASE'),
    (r'일\s*때$', 'CONDITION_WHEN'),
    (r'지급\s*(조건|사유|내용)', 'PAYMENT_EXPLANATION'),
    (r'납입면제.*대상', 'PREMIUM_WAIVER'),
]

# Sentence-like unmatched filtering (lines 76-84)
if mapping_status == 'unmatched' or not coverage_code:
    if any(marker in coverage_name_raw for marker in ['~', '으로', '는', '는지']):
        if len(coverage_name_raw) > 20 and no_coverage_keywords:
            return True, 'SENTENCE_LIKE_UNMATCHED'
```

#### Key Insight
- **중복 필터링 (Step0 후 추가)**: mapping 후 unmatched 중 문장형 추가 제거
- **Mapping status 정규화**: `.strip().lower()` 적용 (SSOT 준비)

---

### **STEP 2: Canonical Mapping** (step2_canonical_mapping/map_to_canonical.py)

#### Input
- `data/scope/{insurer}_scope.csv` (추출된 담보 목록)
- `data/sources/mapping/담보명mapping자료.xlsx` (INPUT contract - 단일 출처)

#### Output
- `data/scope/{insurer}_scope_mapped.csv` (coverage_code + mapping_status 추가)

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **YES** - 담보의 정체성(canonical code) 확정 |
| Business Logic 포함? | **YES** - 4-tier matching dictionary |
| 회사별 포맷 차이 책임? | **PARTIAL** - Excel alias 의존 |

#### Logic Summary
```python
# 4-tier matching (lines 77-108)
# Tier 1: Exact match on canonical name
mapping_dict[coverage_name_canonical] = {..., 'match_type': 'exact'}

# Tier 2: Normalized match on canonical name
normalized_canonical = _normalize(coverage_name_canonical)
mapping_dict[normalized_canonical] = {..., 'match_type': 'normalized'}

# Tier 3: Exact match on insurer alias (from Excel)
mapping_dict[coverage_name_insurer] = {..., 'match_type': 'alias'}

# Tier 4: Normalized match on insurer alias
normalized_insurer = _normalize(coverage_name_insurer)
mapping_dict[normalized_insurer] = {..., 'match_type': 'normalized_alias'}

# Normalization (lines 26-40)
def _normalize(text):
    text = re.sub(r'\s+', '', text)              # 공백 제거
    text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)  # 특수문자 제거
    return text.lower()
```

#### Key Insight
- **담보 정체성 확정**: coverage_code 부여 = canonical로 매핑 성공
- **Alias 의존성**: 보험사별 명칭은 **Excel 파일에 수동 등록된 것만** 인식
- **No fallback beyond Excel**: 엑셀에 없으면 → `unmatched` (Step2에서 판단 종료)

---

### **STEP 3: Extract Text** (step3_extract_text/extract_pdf_text.py)

#### Input
- `data/evidence_sources/{insurer}_manifest.csv` (PDF 목록)

#### Output
- `data/evidence_text/{insurer}/{doc_type}/{basename}.page.jsonl`

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **NO** - 단순 텍스트 추출 |
| Business Logic 포함? | **NO** - PyMuPDF 래퍼 |
| 회사별 포맷 차이 책임? | **NO** |

#### Logic Summary
```python
# Simple extraction (lines 48-61)
doc = fitz.open(pdf_path)
for page_num, page in enumerate(doc, start=1):
    text = page.get_text("text")
    page_jsonl.write(json.dumps({"page": page_num, "text": text.strip()}))
```

#### Key Insight
- **Infrastructure layer**: 판단/해석 없음, raw text만 추출

---

### **STEP 4: Evidence Search** (step4_evidence_search/search_evidence.py)

#### Input
- `data/scope/{insurer}_scope_mapped.csv` (mapped coverages)
- `data/evidence_text/{insurer}/**/*.page.jsonl` (extracted text)

#### Output
- `data/evidence_pack/{insurer}_evidence_pack.jsonl` (evidence per coverage)

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **YES** - 어떤 텍스트가 담보 evidence인지 결정 |
| Business Logic 포함? | **YES** - Query variants, fallback patterns |
| 회사별 포맷 차이 책임? | **YES** - Hyundai/Hanwha 특화 variants |

#### Logic Summary
```python
# Hyundai variants (lines 57-95)
def _generate_hyundai_query_variants(coverage_name):
    variants = [coverage_name]
    # Rule (a): 끝 suffix 제거 - 담보, 특약, 보장
    # Rule (b): 진단비 ↔ 진단 변환
    return variants[:4]

# Hanwha variants (lines 97-213)
def _generate_hanwha_query_variants(coverage_name):
    variants = [coverage_name]
    # Rule (a): suffix 제거
    # Rule (b): 진단비 ↔ 진단 변환
    # Rule (c): 암 용어 브릿지 - 4대유사암 ↔ 유사암(4대) ↔ 유사암
    # Rule (d): Top-6 suffix variants (치료비 ↔ 치료, 입원일당 ↔ 입원, ...)
    return variants[:6]

# Doc-type independent search (lines 492-540)
for doc_type in ['약관', '사업방법서', '상품요약서']:
    evidences = search_in_doc_type(coverage_name, doc_type)
    hits_by_doc_type[doc_type] = len(evidences)

# Fallback: token-AND search (lines 371-429)
if phrase_search_fails:
    tokens = extract_core_tokens(coverage_name)  # 2+ Korean chars
    find_lines_with_at_least_2_tokens()
```

#### Key Insight
- **Evidence 발견 책임**: Mapping 성공 여부와 무관하게 약관/사업방법서/상품요약서에서 텍스트 증거 검색
- **회사별 heuristic 집중지**: Hyundai/Hanwha variant 생성 로직 존재
- **Proposal 명칭 사용 안 함**: `coverage_name_canonical` 또는 `coverage_name_raw`로 검색 (proposal 명칭 직접 사용 없음)

---

### **STEP 5: Build Cards** (step5_build_cards/build_cards.py)

#### Input
- Resolved scope CSV (3-tier fallback: sanitized → mapped → original)
- `data/evidence_pack/{insurer}_evidence_pack.jsonl`

#### Output
- **`data/compare/{insurer}_coverage_cards.jsonl`** ← **Coverage SSOT**

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **YES** - SSOT 생성 (최종 담보 목록 확정) |
| Business Logic 포함? | **YES** - Evidence diversity selection (Rule 6-ε.2) |
| 회사별 포맷 차이 책임? | **NO** - 범용 로직 |

#### Logic Summary
```python
# Coverage card structure (core/compare_types.py:43-67)
@dataclass
class CoverageCard:
    insurer: str
    coverage_name_raw: str            # Proposal 담보명
    coverage_code: Optional[str]      # Canonical code (matched만)
    coverage_name_canonical: Optional[str]
    mapping_status: str               # "matched" | "unmatched"
    evidence_status: str              # "found" | "not_found"
    evidences: List[Evidence]
    hits_by_doc_type: dict
    flags: List[str]

# Evidence diversity selection (lines 26-128)
def _select_diverse_evidences(evidences, max_count=3):
    # Dedup by (doc_type, file_path, page, snippet)
    # Fallback detection: 'fallback_' in keyword OR keyword.startswith('token_and(')
    # Priority: non-fallback > 약관 > 사업방법서 > 상품요약서 > page asc
    # Diversity pass: 1 per doc_type, then fill-up to max 3
```

#### Key Insight
- **SSOT 생성 지점**: 이 단계에서 coverage 목록이 확정됨
- **Mapping status 보존**: `unmatched` 담보도 카드에 포함 (증거가 있으면 evidence_status=found)
- **Proposal 명칭 유지**: `coverage_name_raw`는 가입설계서 원본 명칭 그대로 저장

---

### **STEP 7: Amount Extraction** (step7_amount_extraction/extract_and_enrich_amounts.py)

#### Input
- `data/compare/{insurer}_coverage_cards.jsonl`
- `data/evidence_text/{insurer}/가입설계서/*.page.jsonl`

#### Output
- **`data/compare/{insurer}_coverage_cards.jsonl`** (enriched with `amount` field)

#### Decision Points
| 질문 | 답변 |
|------|------|
| 판단을 내리는가? | **YES** - 금액 확정 (CONFIRMED/UNCONFIRMED) |
| Business Logic 포함? | **YES** - Normalization + amount pattern extraction |
| 회사별 포맷 차이 책임? | **YES** - Multi-line merging (Hanwha/Heungkuk) |

#### Logic Summary
```python
# Coverage name normalization for matching (lines 59-94)
def normalize_coverage_name_for_matching(raw_name):
    # 1. Remove line number prefixes: ^\d{2,}\s+ OR ^\d{1,2}\.\s+
    normalized = re.sub(r'^(\d{2,}\s+|\d{1,2}\.\s+)', '', raw_name)

    # 2. Extract from base contract: 기본계약(담보명) → 담보명
    base_contract_match = re.search(r'^기본계약\(([^)]+)\)', normalized)
    if base_contract_match:
        normalized = base_contract_match.group(1)

    # 3. Remove whitespace/special chars
    normalized = re.sub(r'\s+', '', normalized)
    normalized = re.sub(r'[·\-_...]', '', normalized)

    return normalized.strip()

# Multi-line amount merging (lines 162-192 STEP NEXT-19)
def merge_amount_fragments(lines, start_idx):
    # Pattern: "1," + "000만원" → "1,000만원"
    comma_match = re.fullmatch(r'(\d+),', first_line)
    if comma_match and next_line_matches_NNN만원:
        merged = f"{comma_match.group(1)},{unit_match.group(1)}{unit_match.group(2)}"
        return merged, 2  # consumed 2 lines

# Matching to coverage_code (lines 322-366)
def match_proposal_to_coverage_code(pairs, scope_mapped_csv):
    # Normalize both proposal and scope names
    # Match normalized names → coverage_code
    # First match only (no duplicates)
```

#### Key Insight
- **Proposal 담보명 직접 사용**: 가입설계서에서 추출한 `(담보명, 금액)` 페어의 담보명을 **normalize 후 scope_mapped.csv와 매칭**
- **Matching 지점 2회 발생**:
  1. Step2: `coverage_name_raw` (가입설계서) → canonical code
  2. Step7: proposal 페어 담보명 → scope `coverage_name_raw` → canonical code
- **Step7 matching은 Step2와 독립적**: Step2 실패해도 Step7에서 재시도 (정규화 규칙 다름)

---

## 2️⃣ 담보 추출 관점 핵심 질문 답변

### Q1: "담보의 존재"는 어느 step에서 확정되는가?

**Answer**: **Step0 + Step5 조합**

1. **Step0 (1차 존재 판정)**: 가입설계서 table row에서 추출, condition sentence 아님 → 담보 후보
2. **Step1-sanitize (2차 정제)**: mapping 후 unmatched 중 문장형 추가 제거
3. **Step5 (최종 확정)**: Coverage card SSOT 생성 = 담보 존재 확정 (matched든 unmatched든)

**문제점**:
- Step0-1-5가 "존재" 판정을 분산 수행
- Step5는 이미 Step2 mapping 결과를 받은 상태 → **unmatched는 Step5에서 제거 불가** (SSOT에 포함됨)

---

### Q2: "담보의 정체성(어떤 담보인가)"은 어느 step에서 확정되는가?

**Answer**: **Step2 (Canonical Mapping)** 단독

- **Step2 성공 (matched)**: coverage_code 부여 → canonical 정체성 확정
- **Step2 실패 (unmatched)**: 정체성 미확정 → 이후 모든 step에서 `coverage_code=None` 유지

**문제점**:
- Step2 이후 **재판정 기회 없음** (Step7 amount matching은 별도 로직, canonical code 재부여 안 함)
- Unmatched 담보는 영구적으로 정체성 없이 흐름

---

### Q3: "Canonical code로의 귀속"은 어느 step에서 확정되는가?

**Answer**: **Step2 (Canonical Mapping) 단독**

- Mapping 자료 Excel의 4-tier dictionary lookup 결과가 전부
- Tier 1-4 모두 실패 → `unmatched` (이후 변경 불가)

**문제점**:
- Excel 파일에 alias 등록 안 되어 있으면 **구조적으로 매칭 불가**
- Step4 evidence search / Step7 amount extraction은 canonical code 재부여 권한 없음

---

### Q4: Scope mismatch / 명칭 불일치는 어느 문제인가?

**Answer**: **Mapping 문제 + Alias 정책 문제**

| 케이스 | 원인 | 책임 step | 해결 가능성 |
|--------|------|-----------|-------------|
| Hanwha "4대유사암" (proposal) vs "유사암(8대)" (scope) | Excel alias 미등록 | Step2 | ❌ 구조적 불가 (Excel 수동 추가 필요) |
| Heungkuk "담보명 A" (proposal) vs "담보명 B" (scope) | Excel alias 미등록 | Step2 | ❌ 구조적 불가 (Excel 수동 추가 필요) |
| Hyundai "암진단비보장" → "암진단비" | Step4 variant 생성 지원 | Step4 | ✅ 가능 (evidence만, code 부여는 안 됨) |

**구조적 한계**:
- Step2는 **proposal 명칭을 직접 보지 않음** (Step0/1이 추출한 `coverage_name_raw`만 사용)
- Proposal PDF에서 추출한 담보명이 Excel alias와 다르면 → **Step2에서 unmatched 확정**
- Step7 amount extraction은 proposal 담보명 사용하지만 **canonical code 부여 권한 없음**

---

### Q5: 현재 구조에서 Hanwha/Heungkuk 케이스는 원천적으로 해결 가능한가?

**Answer**: **❌ 구조적으로 불가능 (현재 pipeline 구조 내에서)**

**이유**:
1. **Step0-1 추출**: 가입설계서에서 "4대유사암" 추출 성공
2. **Step2 mapping**: Excel에 "4대유사암" alias 없음 → `unmatched`
3. **Step4 evidence**: Hanwha variant 생성으로 "유사암(4대)" 검색 → 증거 발견 (evidence_status=found)
4. **Step5 cards**: `mapping_status=unmatched`, `evidence_status=found` 카드 생성 (SSOT 확정)
5. **Step7 amount**: 가입설계서 "4대유사암" 금액 추출 성공, 하지만 **scope에 "4대유사암" 없음** → `coverage_code=None` → 매칭 실패

**Mismatch 발생 지점**:
- Proposal 담보명 ("4대유사암") ≠ Scope 담보명 ("유사암(8대)") ≠ Canonical 담보명 ("유사암진단비(4대유사암제외)")
- **3개 명칭 불일치, but alias layer 없음**

**현재 구조의 해결책**:
1. ✅ Excel 파일에 "4대유사암" → A3300_4 alias 수동 추가 (Step2 mapping 성공)
2. ❌ 코드로 자동 추론 (fuzzy matching 금지 by SSOT contract)

---

## 3️⃣ Step Alignment Evaluation

| Step | 역할 명확성 | 평가 | 비고 |
|------|-------------|------|------|
| **Step0: Scope Filter** | ✅ 명확 | 담보 후보 1차 필터링 (table row, 비문장) | 역할 적절 |
| **Step1-sanitize: Sanitize Scope** | ⚠️ 모호 | Mapping 후 unmatched 추가 정제 → **순서 역전** (sanitize가 mapping 전에 와야 함) | **구조 재정의 필요** |
| **Step2: Canonical Mapping** | ✅ 명확 | Coverage 정체성 확정 (coverage_code 부여) | 역할 적절, but **alias 확장 필요** |
| **Step3: Extract Text** | ✅ 명확 | Infrastructure (텍스트 추출) | 역할 적절 |
| **Step4: Evidence Search** | ❌ 책임 과다 | Evidence 검색 + **회사별 variant heuristic** | **Variant 생성은 Step2 이전에 와야 함** |
| **Step5: Build Cards** | ✅ 명확 | SSOT 생성 (담보 목록 확정) | 역할 적절 |
| **Step7: Amount Extraction** | ⚠️ 중복 매칭 | Proposal 담보명 → scope 매칭 → **Step2와 독립적 매칭** | **중복 로직, 통합 필요** |

---

### 세부 평가

#### ❌ **Step4: Evidence Search — 역할 과다**

**문제**:
- Evidence 검색 (본업)
- + Query variant 생성 (Hyundai/Hanwha 특화)
- + Fallback pattern (token-AND search)

**이 step에 있으면 안 되는 로직**:
```python
# step4_evidence_search/search_evidence.py:57-213
def _generate_hyundai_query_variants(coverage_name):
    # 진단비 ↔ 진단 변환
    # suffix 제거 (담보, 특약, 보장)

def _generate_hanwha_query_variants(coverage_name):
    # 4대유사암 ↔ 유사암(4대) ↔ 유사암 브릿지
    # 6개 suffix variants
```

**왜 문제인가**:
- **Variant 생성 = alias 정의 로직** → Step2 이전에 와야 함
- Step4는 **이미 mapping 실패한 담보에 대해 보상 시도** (fallback) → 구조적으로 늦음

**올바른 위치**:
- Step2 이전에 **Alias Expansion Layer** 추가
- Proposal 명칭 → variant 생성 → mapping 시도 (4-tier + variant tier)

---

#### ⚠️ **Step1-sanitize — 순서 역전**

**문제**:
- 현재: Step2 mapping **후** sanitize (mapping 결과를 보고 unmatched 정제)
- 올바른 순서: sanitize **먼저** (condition sentence 제거), mapping **나중**

**증거**:
```python
# step1_sanitize_scope/run.py:76-84
if mapping_status == 'unmatched' or not coverage_code:
    if sentence_like_pattern:
        return True, 'SENTENCE_LIKE_UNMATCHED'
```

→ `mapping_status`를 보고 판단 = **mapping 후 실행되어야 한다는 의미**

**문제점**:
- Sanitize가 mapping 결과에 의존 → **circular dependency risk**
- Step2 실패 시 sanitize 기회 상실 (이미 unmatched로 확정)

---

#### ⚠️ **Step7: Amount Extraction — 중복 매칭**

**문제**:
- Step2: `coverage_name_raw` (scope) → canonical code
- Step7: proposal 담보명 → scope `coverage_name_raw` → canonical code (간접)

**증거**:
```python
# step7_amount_extraction/extract_and_enrich_amounts.py:322-366
def match_proposal_to_coverage_code(pairs, scope_mapped_csv):
    # Load scope_mapped.csv: coverage_name_raw -> coverage_code
    coverage_map[norm_name] = (code, raw_name)

    # Match proposal pairs to coverage_code
    for pair in pairs:
        norm = normalize_coverage_name_for_matching(pair.coverage_name_raw)
        if norm in coverage_map:
            code = coverage_map[norm]
```

**문제점**:
- **Normalization 규칙 중복**: Step2 `_normalize()` vs Step7 `normalize_coverage_name_for_matching()`
- Step7 성공해도 **coverage_code 재부여 안 함** (amount 필드만 추가)
- Step2 실패 + Step7 성공 시 **UNCONFIRMED로 남음** (구조적 손실)

---

## 4️⃣ 구조적 결론 및 재정의 필요 사항

### 지금 구조로 충분한 것

1. ✅ **가입설계서 table 추출**: Step0 scope filter 정착 (table-based filtering)
2. ✅ **Canonical mapping 계약**: Excel 기반 4-tier matching (exact/normalized/alias/normalized_alias)
3. ✅ **SSOT 생성**: Step5 coverage cards (matched + unmatched 모두 포함)
4. ✅ **Evidence 검색**: 3개 doc type 독립 검색 + hits_by_doc_type 기록
5. ✅ **Amount 추출**: Type A/B proposal table parsing + multi-line merging

---

### 지금 구조로 불가능한 것 (구조적 한계)

1. ❌ **Proposal 명칭 ≠ Scope 명칭 자동 해석**
   - 예: "4대유사암" (proposal) → "유사암(8대)" (scope) 매칭
   - 현재: Excel alias 수동 등록 필수
   - 한계: Excel 없으면 영구 `unmatched`

2. ❌ **Semantic equivalence 추론**
   - 예: "암진단비" ↔ "암 진단" ↔ "암진단금" 동치 판정
   - 현재: normalized matching만 (공백/특수문자 제거)
   - 한계: 형태소 변형 / 유의어 미지원

3. ❌ **Variant 생성 타이밍 문제**
   - 현재: Step4에서 variant 생성 (mapping 후)
   - 문제: Step2 실패 → Step4 variant 무용지물
   - 한계: Variant로 evidence 찾아도 `coverage_code=None` 유지

4. ❌ **Step2-Step7 mapping 로직 분산**
   - 현재: Step2 (scope → canonical), Step7 (proposal → scope → canonical)
   - 문제: 정규화 규칙 중복, Step7 성공해도 code 재부여 안 함
   - 한계: Step2 실패 시 Step7 성공이 SSOT에 반영 안 됨

---

### 재정의가 필요한 Step

#### 1. **Step1-sanitize → Step1.5로 이동 (mapping 전으로)**

**현재**:
```
Step0 (filter) → Step1-extract (legacy) → Step2 (mapping) → Step1-sanitize (cleanup) → Step5 (cards)
```

**제안**:
```
Step0 (filter) → Step1-sanitize (cleanup FIRST) → Step2 (mapping) → Step5 (cards)
```

**이유**:
- Sanitize는 **mapping 독립적** (condition sentence 제거)
- Mapping 전에 정제해야 Step2 성공률 향상

---

#### 2. **Step2 이전에 Alias Expansion Layer 추가**

**현재**:
```
Step0 (extract) → Step2 (mapping with Excel only)
                ↓
            unmatched → Step4 (variant 생성, 하지만 code 재부여 안 함)
```

**제안**:
```
Step0 (extract) → Step1.5 (Alias Expansion: Hyundai/Hanwha variants)
                → Step2 (mapping with Excel + expanded aliases)
                → Step4 (evidence search only, NO variant logic)
```

**Alias Expansion Layer 역할**:
- Input: `coverage_name_raw` (proposal 명칭)
- Output: `[original, variant1, variant2, ...]` (최대 6개)
- Logic: Hyundai/Hanwha rules (현재 Step4 variant 생성 로직 이동)
- Step2는 **모든 variant에 대해 mapping 시도** (first match wins)

**효과**:
- Hanwha "4대유사암" → variant "유사암(4대)" 생성 → Step2 mapping 성공 (Excel에 등록되어 있다면)
- Step4는 pure evidence search만 담당 (역할 명확화)

---

#### 3. **Step7 Amount Matching을 Step2.5로 통합**

**현재**:
```
Step2 (scope → canonical) ... (여러 step) ... Step7 (proposal → scope → canonical)
```

**제안**:
```
Step2 (scope → canonical)
  ↓
Step2.5 (Proposal Amount Pre-matching: proposal 담보명 → scope 매칭 시도)
  ↓
  if matched:
    update coverage_code (Step2 실패 건 복구)
  ↓
Step5 (cards with corrected mapping_status)
  ↓
Step7 (amount enrichment only, NO matching)
```

**Step2.5 역할**:
- Input: `data/evidence_text/{insurer}/가입설계서/*.page.jsonl`
- Output: `data/scope/{insurer}_proposal_aliases.csv` (proposal 담보명 → scope 담보명 매핑)
- Logic:
  1. Proposal에서 (담보명, 금액) 페어 추출
  2. Normalize proposal 담보명
  3. Scope `coverage_name_raw`와 매칭 시도
  4. 매칭 성공 시 `proposal_name → scope_name → coverage_code` 경로 기록
  5. Step2 실패 건 중 Step2.5 성공 건 → `mapping_status=matched` 업데이트

**효과**:
- Step2-Step7 중복 로직 제거
- Proposal 명칭 기반 매칭 결과가 **SSOT 생성 전에 반영**
- Step7은 pure amount enrichment (matching 책임 제거)

---

## 5️⃣ 다음 단계 후보 (NEXT STEP Candidates)

### **Option A: STEP NEXT-22 — Alias Expansion Layer 신설** (추천 ⭐)

**목표**: Proposal 명칭 variant 생성을 Step2 이전으로 이동, mapping 성공률 향상

**변경**:
1. `pipeline/step1.5_alias_expansion/` 생성
   - Input: `{insurer}_scope.csv` (raw proposal 명칭)
   - Output: `{insurer}_scope_expanded.csv` (original + variants)
   - Logic: Hyundai/Hanwha variant rules (Step4에서 이동)
2. Step2 mapping 입력을 `scope_expanded.csv`로 변경
3. Step4 variant 생성 로직 제거 (pure evidence search만 유지)

**효과**:
- Hanwha "4대유사암" → "유사암(4대)" variant 생성 → Step2 mapping 성공 가능
- **단, Excel alias 등록 필수** (variant 생성만으로는 불충분, Excel에 "유사암(4대)" alias 있어야 함)

**한계**:
- Excel alias 의존 여전 (자동 추론 아님)
- Variant 폭발 위험 (Hanwha 6개 × 30 coverages = 180 variants)

---

### **Option B: STEP NEXT-23 — Proposal-Scope Alias Registry 구축**

**목표**: Proposal 담보명 ↔ Scope 담보명 매핑 테이블 생성 (Excel과 독립)

**변경**:
1. `data/sources/mapping/proposal_scope_aliases.json` 생성
   ```json
   {
     "hanwha": {
       "4대유사암": "유사암(8대)",
       "통합암(4대유사암제외)": "유사암진단비(4대유사암제외)"
     },
     "heungkuk": {
       "담보A": "담보B"
     }
   }
   ```
2. Step2 이전에 alias registry 기반 proposal → scope 명칭 변환
3. 변환된 scope 명칭으로 Step2 mapping 시도

**효과**:
- Proposal-Scope mismatch 해결 (보험사별 alias 수동 관리)
- Excel 파일 변경 없이 alias 추가 가능

**한계**:
- 여전히 수동 등록 필요 (자동 추론 아님)
- 2개 mapping 파일 관리 (Excel + JSON)

---

### **Option C: STEP NEXT-24 — Sanitize-Mapping 순서 재정의** (Quick Win)

**목표**: Step1-sanitize를 Step2 이전으로 이동 (순서 정상화)

**변경**:
1. `step1_sanitize_scope/run.py` input을 `{insurer}_scope.csv`로 변경 (현재는 `_mapped.csv`)
2. Sanitize 로직에서 `mapping_status` 의존 제거
3. Pipeline 순서: Step0 → Step1-sanitize → Step2 → Step5

**효과**:
- Condition sentence 제거가 mapping 전에 수행 → Step2 성공률 향상
- Circular dependency 제거

**한계**:
- Hanwha/Heungkuk alias 문제 미해결 (순서 변경만으로는 불충분)

---

## 📋 Final Recommendations

### 우선순위 1: **STEP NEXT-24 (Sanitize 순서 정상화)** ← Quick Win
- 구조적 순서 역전 해결
- 변경 범위 작음 (Step1 input 변경만)
- 즉시 효과 (mapping 성공률 소폭 향상)

### 우선순위 2: **STEP NEXT-22 (Alias Expansion Layer)** ← Structural Fix
- Variant 생성을 Step2 이전으로 이동
- Step4 역할 명확화 (evidence search only)
- Hanwha/Heungkuk 일부 케이스 해결 가능 (Excel alias 등록 병행 필요)

### 우선순위 3: **STEP NEXT-23 (Proposal-Scope Alias Registry)** ← Long-term
- Proposal-Scope mismatch 근본 해결
- Excel 독립적 alias 관리
- 장기 운영 관점에서 필요 (단, 수동 관리 부담 증가)

---

## 🚫 금지 사항 Checklist

- ✅ 금액 추출 로직 수정 안 함
- ✅ Fuzzy matching 제안 안 함
- ✅ 단기 KPI 개선 패치 안 함
- ✅ inca-rag-demo 참조 안 함
- ✅ 코드 변경 안 함 (분석 only)

---

**Document Version**: 1.0
**Completion Date**: 2025-12-30
**Next Action**: STEP NEXT-24 (Sanitize 순서 정상화) 착수 검토
