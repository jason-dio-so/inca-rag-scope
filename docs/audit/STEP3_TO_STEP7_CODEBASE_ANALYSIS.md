# Pipeline Step3-Step7 Codebase Analysis Report

**Generated**: 2026-01-01
**Scope**: Evidence extraction, search, and card building pipeline
**Status**: Active production code

---

## Executive Summary

**Pipeline Purpose**: Extract evidence from insurance documents (약관/사업방법서/상품요약서), match to coverage names, and build standardized coverage cards for comparison.

**Design Philosophy**:
- ✅ **NO LLM** - Deterministic pattern matching only
- ✅ **NO OCR** - PDF text extraction only
- ✅ **NO Embedding/Vector DB** - String search only
- ✅ **Independent doc-type search** - 약관/사업방법서/상품요약서 searched separately

**Architecture**: Linear pipeline with explicit input/output contracts and validation gates.

---

## Pipeline Overview

```
Step3: Extract Text      → data/evidence_text/{insurer}/{doc_type}/*.page.jsonl
    ↓
Step4: Search Evidence   → data/evidence_pack/{insurer}_evidence_pack.jsonl
    ↓
Step5: Build Cards       → data/compare/{insurer}_coverage_cards.jsonl (SSOT)
    ↓
Step7: Enrich Amounts    → data/compare/{insurer}_coverage_cards.jsonl (enriched)
```

**Note**: Step6 does not exist (skipped in numbering).

---

## Step 3: PDF Text Extraction

### Purpose
Extract page-by-page text from PDF evidence documents (약관, 사업방법서, 상품요약서).

### File
`pipeline/step3_extract_text/extract_pdf_text.py` (151 lines)

### Input
```
data/evidence_sources/{insurer}_manifest.csv
  - Columns: doc_type, file_path
  - Example: 약관, data/sources/insurers/hyundai/약관/현대_약관.pdf
```

### Output
```
data/evidence_text/{insurer}/{doc_type}/{basename}.page.jsonl
  - Format: {"page": 1, "text": "..."}
  - One JSON object per line (JSONL)
  - 1-based page numbering
```

### Implementation Details

**Core Logic** (`PDFTextExtractor` class):
```python
def extract_pdf_to_jsonl(pdf_path, doc_type, insurer):
    doc = pymupdf.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")  # NO OCR, text layer only
        page_data = {"page": page_num + 1, "text": text.strip()}
        # Write to JSONL
```

**Technology**: PyMuPDF (fitz) for PDF text extraction.

**Guarantees**:
- ✅ NO OCR (text layer only)
- ✅ NO preprocessing (raw text preserved)
- ✅ Per-page granularity
- ✅ UTF-8 encoding

**Error Handling**: Failed PDFs logged but don't halt pipeline.

### CLI Usage
```bash
python -m pipeline.step3_extract_text.extract_pdf_text --insurer hyundai
```

### Output Statistics
```
Total: N files processed
Success: N files
Failed: N files
```

---

## Step 4: Evidence Search

### Purpose
Search evidence documents for coverage name mentions using deterministic string matching.

### File
`pipeline/step4_evidence_search/search_evidence.py` (807 lines)

### Input
```
1. data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl  (SSOT)
2. data/evidence_text/{insurer}/**/*.page.jsonl
```

### Output
```
data/evidence_pack/{insurer}_evidence_pack.jsonl
  - First line: Meta record (scope_content_hash, created_at)
  - Following lines: Evidence records (one per coverage)
```

### Core Components

#### 1. EvidenceSearcher Class

**Normalization** (for matching):
```python
def _normalize(text: str) -> str:
    # Remove whitespace
    text = re.sub(r'\s+', '', text)
    # Keep only Korean, English, digits, parentheses
    text = re.sub(r'[^가-힣a-zA-Z0-9()]', '', text)
    return text.lower()
```

**Doc-Type Priority**:
```python
DOC_TYPE_PRIORITY = {
    '약관': 1,           # Highest priority
    '사업방법서': 2,
    '상품요약서': 3      # Lowest priority
}
```

#### 2. Query Expansion (Insurer-Specific)

**Hyundai Variants** (max 4):
```python
def _generate_hyundai_query_variants(coverage_name):
    variants = [coverage_name]

    # Rule (a): Remove suffix (담보, 특약, 보장, 보장특약)
    for suffix in ['보장특약', '담보', '특약', '보장']:
        if coverage_name.endswith(suffix):
            variants.append(coverage_name[:-len(suffix)])
            break

    # Rule (b): 진단비 <-> 진단
    if '진단비' in coverage_name:
        variants.append(coverage_name.replace('진단비', '진단'))
    elif '진단' in coverage_name:
        variants.append(coverage_name.replace('진단', '진단비'))

    # Rule (c): Whitespace cleanup
    cleaned = re.sub(r'\s+', ' ', coverage_name).strip()
    if cleaned != coverage_name:
        variants.append(cleaned)

    return variants[:4]  # Max 4 variants
```

**Hanwha Variants** (max 6):
```python
def _generate_hanwha_query_variants(coverage_name):
    # Rules (a)-(c): Same as Hyundai

    # Rule (d): 암 용어 브릿지
    # 4대유사암 ↔ 유사암(4대) ↔ 유사암
    if '유사암(4대)' in coverage_name:
        variants.append(coverage_name.replace('유사암(4대)', '4대유사암'))
        variants.append(coverage_name.replace('유사암(4대)', '유사암'))

    # 통합암(4대유사암제외) variants
    # 표적항암 ↔ 표적
    # 재진단암 ↔ 재진단
    # etc. (see lines 122-186)

    # Rule (e): Top-6 suffix variants
    # 치료비 ↔ 치료
    # 입원일당 ↔ 입원
    # 수술비 ↔ 수술
    # etc. (see lines 151-186)

    # Rule (f): Bracket normalization (fallback)
    if '(' in coverage_name:
        no_bracket = re.sub(r'\([^)]*\)', '', coverage_name)
        variants.append(no_bracket)

    return variants[:6]  # Max 6 variants
```

**Other Insurers**: No expansion (use raw + canonical only).

#### 3. Fallback Strategies

**STEP 4-λ: Token-AND Search** (Hanwha only):
```python
def _fallback_token_and_search(coverage_name, doc_type, pages):
    # Extract core tokens (2+ chars, exclude: 비, 형, 담보, etc.)
    core_tokens = _extract_core_tokens(coverage_name)

    # Require >= 2 tokens
    if len(core_tokens) < 2:
        return []

    # Find lines where >= 2 tokens co-occur
    for page in pages:
        for line in page.text.split('\n'):
            token_count = sum(1 for token in core_tokens if token in line)
            if token_count >= 2:
                # Extract snippet with context
                snippet = extract_context(line, context_lines=2)
                evidences.append(snippet)

    return evidences
```

**STEP 6-δ: KB 사업방법서 정의 Hit** (KB A4200_1 only):
```python
def _kb_bm_a4200_1_definition_hit(pages):
    # Score-based snippet selection
    # Required tokens: 암진단비 + 유사암 + 제외 (ALL required)

    best_score = 0
    for page in pages:
        for line in page.text.split('\n'):
            score = 0
            if '암진단비' in line: score += 1
            if '유사암' in line: score += 1
            if '제외' in line or '유사암제외' in line: score += 1
            if '보험금' in line or '지급' in line: score += 1

            if score < 3:  # Threshold
                continue

            if score > best_score:
                best_score = score
                snippet = extract_context(line, context_lines=4)

    return snippet if best_score >= 3 else None
```

#### 4. Search Execution

**Main Search Logic**:
```python
def search_coverage_evidence(
    coverage_name_raw,
    coverage_name_canonical=None,
    mapping_status="matched",
    coverage_code=None
):
    # Determine keywords
    if mapping_status == "matched" and coverage_name_canonical:
        keywords = [coverage_name_canonical, coverage_name_raw]
    else:
        keywords = [coverage_name_raw]

    # Expand keywords (insurer-specific)
    if self.insurer == 'hyundai':
        keywords = expand_hyundai_variants(keywords)
    elif self.insurer == 'hanwha':
        keywords = expand_hanwha_variants(keywords)

    # Initialize hit counters (REQUIRED for 3 doc types)
    hits_by_doc_type = {
        '약관': 0,
        '사업방법서': 0,
        '상품요약서': 0
    }

    # Search each doc_type independently (ENFORCED)
    for doc_type in ['약관', '사업방법서', '상품요약서']:
        pages = self.text_data[doc_type]
        doc_type_evidences = []

        for page in pages:
            if len(doc_type_evidences) >= max_evidences_per_type:
                break

            for keyword in keywords:
                snippets = _extract_snippet(page.text, keyword, context_lines=2)
                for snippet in snippets:
                    doc_type_evidences.append({
                        'doc_type': doc_type,
                        'file_path': page.file_path,
                        'page': page.page,
                        'snippet': snippet[:500],  # Max 500 chars
                        'match_keyword': keyword
                    })

        # Update hit count
        hits_by_doc_type[doc_type] = len(doc_type_evidences)
        all_evidences.extend(doc_type_evidences)

    # Fallback: Token-AND (Hanwha only, if all failed)
    if self.insurer == 'hanwha' and len(all_evidences) == 0:
        fallback_evidences = _fallback_token_and_search(...)
        all_evidences.extend(fallback_evidences)
        flags.append('fallback_token_and')

    # Fallback: KB BM Definition Hit (KB A4200_1 only, if BM failed)
    if self.insurer == 'kb' and coverage_code == 'A4200_1':
        if hits_by_doc_type['사업방법서'] == 0:
            hit = _kb_bm_a4200_1_definition_hit(pages)
            if hit:
                all_evidences.append(hit)
                hits_by_doc_type['사업방법서'] = 1
                flags.append('kb_bm_definition_hit')

    # Generate flags
    flags = []
    if hits_by_doc_type['약관'] >= 1 and \
       hits_by_doc_type['사업방법서'] == 0 and \
       hits_by_doc_type['상품요약서'] == 0:
        flags.append('policy_only')

    return {
        'evidences': all_evidences,
        'hits_by_doc_type': hits_by_doc_type,
        'flags': flags
    }
```

#### 5. Evidence Pack Generation

**STEP NEXT-31-P3: Content-Hash Lock**:
```python
def create_evidence_pack(scope_mapped_csv, ...):
    # Calculate scope content hash
    scope_content_hash = calculate_scope_content_hash(scope_mapped_csv)

    # Write meta record (FIRST LINE)
    meta_record = {
        'record_type': 'meta',
        'insurer': insurer,
        'scope_file': scope_mapped_csv.name,
        'scope_content_hash': scope_content_hash,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'schema_version': 'v1'
    }
    f.write(json.dumps(meta_record, ensure_ascii=False) + '\n')

    # Write evidence records
    for item in evidence_pack:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
```

### Constitutional Gates

**STEP NEXT-31-P1: Input Gate** (Hard fail if violated):
```python
# Step4 MUST use sanitized scope CSV
if not scope_mapped_csv.name.endswith('.sanitized.csv'):
    raise RuntimeError(
        "[STEP NEXT-31-P1 GATE] Step4 MUST use sanitized scope CSV."
    )
```

### CLI Usage
```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer hyundai
```

### Output Structure
```jsonl
{"record_type": "meta", "insurer": "hyundai", "scope_content_hash": "abc123...", ...}
{"insurer": "hyundai", "coverage_name_raw": "암진단비", "evidences": [...], "hits_by_doc_type": {...}, "flags": [...]}
{"insurer": "hyundai", "coverage_name_raw": "뇌졸중진단비", ...}
...
```

### Output Statistics
```
Total coverages: N
Matched: N
Unmapped: N
With evidence: N
Without evidence: N
```

---

## Step 5: Build Coverage Cards

### Purpose
Join scope data + evidence pack → standardized coverage cards (SSOT for comparison).

### File
`pipeline/step5_build_cards/build_cards.py` (386 lines)

### Input
```
1. data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl  (SSOT)
2. data/evidence_pack/{insurer}_evidence_pack.jsonl
```

### Output
```
data/compare/{insurer}_coverage_cards.jsonl  (SSOT for downstream)
```

### Core Components

#### 1. Evidence Diversity Selection

**STEP 6-ε.2: Doc-Type Diversity + Dedup + Priority**:
```python
def _select_diverse_evidences(evidences, max_count=3):
    """
    Select up to 3 evidences with doc-type diversity.

    Rules:
    1. Dedup by (doc_type, file_path, page, snippet)
    2. Fallback detection: 'fallback_' in keyword OR keyword.startswith('token_and(')
    3. Sort priority:
       a. Non-fallback > fallback
       b. 약관 > 사업방법서 > 상품요약서
       c. page (ascending)
       d. file_path (ascending)
       e. snippet (ascending)
    4. 1st pass: Select 1 from each doc_type (약관, 사업방법서, 상품요약서)
    5. 2nd pass: Fill remaining slots from pool
    """

    # Dedup
    unique_evidences = []
    seen_keys = set()
    for ev in evidences:
        key = (ev.doc_type, ev.file_path, ev.page, ev.snippet)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_evidences.append(ev)

    # Group by doc_type
    by_doc_type = {}
    for ev in unique_evidences:
        if ev.doc_type not in by_doc_type:
            by_doc_type[ev.doc_type] = []
        by_doc_type[ev.doc_type].append(ev)

    # Sort within each doc_type
    for doc_type in by_doc_type:
        by_doc_type[doc_type].sort(key=sort_key)

    # 1st pass: Select 1 from each doc_type
    selected = []
    for doc_type in ['약관', '사업방법서', '상품요약서']:
        if doc_type in by_doc_type and len(selected) < max_count:
            selected.append(by_doc_type[doc_type][0])

    # 2nd pass: Fill up to max_count
    if len(selected) < max_count:
        remaining = [ev for ev in unique_evidences if id(ev) not in selected_set]
        remaining.sort(key=sort_key)
        for ev in remaining:
            if len(selected) >= max_count:
                break
            selected.append(ev)

    return selected[:max_count]
```

#### 2. Card Generation

**Main Build Logic**:
```python
def build_coverage_cards(scope_mapped_csv, evidence_pack_jsonl, insurer):
    # Load scope data
    scope_data = {}  # coverage_name_raw -> {code, canonical, status}
    with open(scope_mapped_csv) as f:
        for row in csv.DictReader(f):
            if scope_gate.is_in_scope(row['coverage_name_raw']):
                scope_data[row['coverage_name_raw']] = {
                    'coverage_code': row['coverage_code'],
                    'coverage_name_canonical': row['coverage_name_canonical'],
                    'mapping_status': row['mapping_status']
                }

    # Load evidence pack
    evidence_data = {}  # coverage_name_raw -> {evidences, hits, flags}
    with open(evidence_pack_jsonl) as f:
        for line in f:
            item = json.loads(line)

            # Validate meta record (FIRST LINE)
            if not first_record_processed:
                first_record_processed = True
                if item['record_type'] != 'meta':
                    raise RuntimeError("Evidence pack missing meta record")

                # Validate scope_content_hash
                current_hash = calculate_scope_content_hash(scope_mapped_csv)
                if item['scope_content_hash'] != current_hash:
                    raise RuntimeError(
                        "Scope content hash mismatch - stale evidence_pack"
                    )
                continue  # Skip meta, process evidence records only

            # Process evidence records
            if scope_gate.is_in_scope(item['coverage_name_raw']):
                evidence_data[item['coverage_name_raw']] = {
                    'evidences': item['evidences'],
                    'hits_by_doc_type': item['hits_by_doc_type'],
                    'flags': item['flags']
                }

    # Join-rate gate (HARD GATE: >= 95%)
    join_rate = len(scope_data ∩ evidence_data) / len(scope_data)
    if join_rate < 0.95:
        raise RuntimeError(
            f"Join rate {join_rate:.2%} below 95% threshold - "
            f"stale or mismatched evidence_pack"
        )

    # Build cards
    cards = []
    for coverage_name_raw, scope_info in scope_data.items():
        # Get evidence data
        ev_data = evidence_data.get(coverage_name_raw, {
            'evidences': [],
            'hits_by_doc_type': {},
            'flags': []
        })

        # Determine evidence_status
        evidence_status = 'found' if ev_data['evidences'] else 'not_found'

        # Select diverse evidences (max 3)
        selected_evidences = _select_diverse_evidences(
            ev_data['evidences'],
            max_count=3
        )

        # Create card
        card = CoverageCard(
            insurer=insurer,
            coverage_name_raw=coverage_name_raw,
            coverage_code=scope_info['coverage_code'] or None,
            coverage_name_canonical=scope_info['coverage_name_canonical'] or None,
            mapping_status=scope_info['mapping_status'],
            evidence_status=evidence_status,
            evidences=selected_evidences,
            hits_by_doc_type=ev_data['hits_by_doc_type'],
            flags=ev_data['flags']
        )
        cards.append(card)

    # Sort cards
    cards.sort(key=lambda c: c.sort_key())

    # Write JSONL
    with open(output_cards_jsonl, 'w') as f:
        for card in cards:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + '\n')

    return stats
```

#### 3. Coverage Card Schema

**CoverageCard** (from `core/compare_types.py`):
```python
{
    "insurer": "hyundai",
    "coverage_name_raw": "암진단비(유사암제외)",
    "coverage_code": "A1100",
    "coverage_name_canonical": "암진단비",
    "mapping_status": "mapped",
    "evidence_status": "found",
    "evidences": [
        {
            "doc_type": "약관",
            "file_path": "data/evidence_text/hyundai/약관/현대_약관.page.jsonl",
            "page": 15,
            "snippet": "제5조(보험금의 지급사유) 암진단비...",
            "match_keyword": "암진단비"
        },
        {
            "doc_type": "사업방법서",
            "file_path": "...",
            "page": 23,
            "snippet": "...",
            "match_keyword": "암진단비"
        },
        {
            "doc_type": "상품요약서",
            "file_path": "...",
            "page": 3,
            "snippet": "...",
            "match_keyword": "암진단비"
        }
    ],
    "hits_by_doc_type": {
        "약관": 2,
        "사업방법서": 1,
        "상품요약서": 1
    },
    "flags": []
}
```

### Constitutional Gates

**STEP NEXT-31-P3: Content-Hash Gate** (Hard fail if violated):
```python
# Validate meta record exists
if item.get('record_type') != 'meta':
    raise RuntimeError("Evidence pack missing meta record")

# Validate scope_content_hash matches
if pack_scope_hash != current_scope_hash:
    raise RuntimeError("Scope content hash mismatch - stale evidence_pack")
```

**STEP NEXT-31-P1: Join-Rate Gate** (Hard fail if < 95%):
```python
if join_rate < 0.95:
    raise RuntimeError(
        f"Join rate {join_rate:.2%} below 95% threshold"
    )
```

### CLI Usage
```bash
python -m pipeline.step5_build_cards.build_cards --insurer hyundai
```

### Output Statistics
```
Total coverages: N
Matched: N
Unmapped: N
Evidence found: N
Evidence not found: N
```

---

## Step 7: Amount Extraction & Enrichment

### Purpose
Extract coverage amounts from proposal PDFs and enrich coverage_cards with `amount` field.

### File
`pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` (491 lines)

### Input
```
1. data/evidence_text/{insurer}/가입설계서/*.page.jsonl
2. data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl  (for matching)
3. data/compare/{insurer}_coverage_cards.jsonl  (to enrich)
```

### Output
```
data/compare/{insurer}_coverage_cards.jsonl  (enriched with amount field)
```

### Core Components

#### 1. Coverage Name Normalization

**STEP NEXT-18B + NEXT-19: Matching-Specific Normalization**:
```python
def normalize_coverage_name_for_matching(raw_name):
    """
    Normalization for matching proposal → coverage_code.

    Rules:
    1. Remove line number prefix: ^\d{2,}\s+ OR ^\d{1,2}\.\s+
       - "251 암진단비" → "암진단비"
       - "1. 상해사망" → "상해사망"
       - BUT keep "4대유사암" (content number, not line number)

    2. Extract from base contract: 기본계약(담보명) → 담보명
       - "기본계약(암진단비)" → "암진단비"

    3. Remove whitespace

    4. Remove separators (·, -, _, bullets)
    """
    # 1. Line number prefix removal
    normalized = re.sub(r'^(\d{2,}\s+|\d{1,2}\.\s+)', '', raw_name)

    # 2. Base contract extraction
    base_contract_match = re.search(r'^기본계약\(([^)]+)\)', normalized)
    if base_contract_match:
        normalized = base_contract_match.group(1)

    # 3. Whitespace removal
    normalized = re.sub(r'\s+', '', normalized)

    # 4. Separator removal
    normalized = re.sub(r'[·\-_\u2022\u2023\u25E6\u2043\u2219]', '', normalized)

    return normalized.strip()
```

#### 2. Amount Extraction Patterns

**Amount Pattern Matching**:
```python
def extract_amount_from_line(line_text):
    """
    Extract amount from line text.

    Supported patterns (priority order):
    1. N천만원, N백만원, N십만원 (e.g., 3천만원, 5백만원)
    2. N,NNN만원, NNNN만원 (e.g., 3,000만원, 1000만원)
    3. NNN,NNN원 (e.g., 100,000원)
    4. N만원 (lowest priority)
    """
    # Pattern 1: N천만원, N백만원, N십만원
    pattern1 = re.search(r'(\d+[천백십]만?원)', line_text)
    if pattern1:
        return pattern1.group(1)

    # Pattern 2: N,NNN만원, NNNN만원
    pattern2 = re.search(r'(\d{1,3}(?:,\d{3})*만?원)', line_text)
    if pattern2:
        return pattern2.group(1)

    # Pattern 3: NNN,NNN원
    pattern3 = re.search(r'(\d{1,3}(?:,\d{3})+원)', line_text)
    if pattern3:
        return pattern3.group(1)

    # Pattern 4: N만원
    pattern4 = re.search(r'(\d+만?원)', line_text)
    if pattern4:
        return pattern4.group(1)

    return None
```

#### 3. Multi-Line Amount Fragment Merging

**STEP NEXT-19: Handle PDF Table Cell Line Breaks**:
```python
def merge_amount_fragments(lines, start_idx):
    """
    Merge multi-line amount fragments (PDF table cell wrapping).

    Pattern: "N," (line 1) + "NNN만원" (line 2) → "N,NNN만원"

    Example:
      Line i:   "1,"
      Line i+1: "000만원"
      Merged:   "1,000만원"

    Returns:
        (merged_amount or None, lines_consumed)
    """
    first_line = lines[start_idx].strip()

    # Only merge "N," pattern (trailing comma)
    comma_match = re.fullmatch(r'(\d+),', first_line)
    if comma_match and start_idx + 1 < len(lines):
        next_line = lines[start_idx + 1].strip()

        # Check for "NNN만원" or "NNN원" (exactly 3 digits)
        unit_match = re.fullmatch(r'(\d{3})(만?원)', next_line)
        if unit_match:
            # Merge
            merged = f"{comma_match.group(1)},{unit_match.group(1)}{unit_match.group(2)}"
            return merged, 2  # Consumed 2 lines

    return None, 0  # No merge
```

#### 4. Proposal Amount Pair Extraction

**Main Extraction Logic**:
```python
def extract_proposal_amount_pairs(proposal_page_jsonl):
    """
    Extract (coverage_name, amount) pairs from proposal PDF.

    Strategy:
    1. Filter pages with table keywords (가입금액, 보장금액, etc.)
    2. Parse line-by-line
    3. Check for multi-line amount fragments FIRST
    4. Extract single-line (coverage + amount)
    5. Extract multi-line (coverage on line N, amount on line N+1)
    """
    pairs = []

    with open(proposal_page_jsonl) as f:
        for page_data in json.loads(f):
            text = page_data['text']
            page_num = page_data['page']

            # Filter: table pages only
            if not any(kw in text for kw in ['가입금액', '보장금액', '담보가입현황']):
                continue

            lines = text.split('\n')
            i = 0

            while i < len(lines):
                line_text = lines[i].strip()

                # Skip header lines
                if any(hdr in line_text for hdr in ['담보가입현황', '가입금액']):
                    i += 1
                    continue

                # Check multi-line amount fragments FIRST
                merged_amount, consumed = merge_amount_fragments(lines, i)
                if merged_amount:
                    # Lookback for coverage name (1-3 lines before)
                    coverage_candidate = None
                    for lookback in range(1, 4):
                        if i - lookback >= 0:
                            prev_line = lines[i - lookback].strip()
                            # Skip numeric-only lines (row numbers)
                            if re.fullmatch(r'\d+', prev_line):
                                continue
                            # Check Korean text
                            if re.search(r'[가-힣]', prev_line) and len(prev_line) >= 3:
                                coverage_candidate = prev_line
                                break

                    if coverage_candidate:
                        pairs.append(ProposalAmountPair(
                            coverage_name_raw=coverage_candidate,
                            amount_text=merged_amount,
                            page_num=page_num,
                            line_text=f"{coverage_candidate} / {merged_amount}"
                        ))

                    i += consumed
                    continue

                # Skip short lines
                if len(line_text) < 3:
                    i += 1
                    continue

                # Single-line: coverage + amount
                amount = extract_amount_from_line(line_text)
                if amount:
                    # Remove amount to extract coverage name
                    coverage_candidate = re.sub(r'\d{1,3}(?:,\d{3})*만?원', '', line_text)
                    coverage_candidate = re.sub(r'\d+[천백십]만?원', '', coverage_candidate)
                    coverage_candidate = re.sub(r'\d+', '', coverage_candidate).strip()

                    # Validate: Korean text + min length
                    if re.search(r'[가-힣]', coverage_candidate) and len(coverage_candidate) >= 3:
                        pairs.append(ProposalAmountPair(
                            coverage_name_raw=coverage_candidate,
                            amount_text=amount,
                            page_num=page_num,
                            line_text=line_text
                        ))
                    i += 1
                else:
                    # Multi-line: coverage (line N) + amount (line N+1)
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        next_amount = extract_amount_from_line(next_line)

                        if next_amount:
                            # Skip numeric-only lines
                            if re.match(r'^[\d,\s]+$', line_text):
                                i += 1
                                continue

                            # Validate coverage name
                            if re.search(r'[가-힣]', line_text) and len(line_text) >= 3:
                                pairs.append(ProposalAmountPair(
                                    coverage_name_raw=line_text,
                                    amount_text=next_amount,
                                    page_num=page_num,
                                    line_text=f"{line_text} / {next_line}"
                                ))
                                i += 2  # Skip both lines
                                continue

                    i += 1

    return pairs
```

#### 5. Matching to Coverage Code

**Proposal → Coverage Code Matching**:
```python
def match_proposal_to_coverage_code(pairs, scope_mapped_csv):
    """
    Match proposal pairs to coverage_code.

    Strategy:
    1. Load scope_mapped.csv: coverage_name_raw → coverage_code
    2. Normalize both proposal names and scope names
    3. Match normalized names
    4. Return coverage_code → (amount, page, line)
    """
    # Load scope map
    coverage_map = {}  # normalized_name → (coverage_code, raw_name)
    with open(scope_mapped_csv) as f:
        for row in csv.DictReader(f):
            if row['mapping_status'] == 'matched':
                norm = normalize_coverage_name_for_matching(row['coverage_name_raw'])
                coverage_map[norm] = (row['coverage_code'], row['coverage_name_raw'])

    # Match proposal pairs
    code_to_amount = {}  # coverage_code → (amount, page, line)
    for pair in pairs:
        norm = normalize_coverage_name_for_matching(pair.coverage_name_raw)

        if norm in coverage_map:
            code, raw_name = coverage_map[norm]
            # First match only (avoid duplicates)
            if code not in code_to_amount:
                code_to_amount[code] = (pair.amount_text, pair.page_num, pair.line_text)

    return code_to_amount
```

#### 6. Coverage Cards Enrichment

**Amount Field Addition**:
```python
def enrich_coverage_cards_with_amounts(
    coverage_cards_jsonl,
    code_to_amount,
    output_jsonl
):
    """
    Add 'amount' field to coverage_cards.jsonl.

    Amount Schema:
    {
        "status": "CONFIRMED" | "UNCONFIRMED",
        "value_text": "3천만원" or None,
        "source_doc_type": "가입설계서" or None,
        "source_priority": "proposal_table" or None,
        "evidence_ref": {
            "page_num": 3,
            "snippet": "암진단비 / 3천만원"
        } or None,
        "notes": []
    }
    """
    enriched_cards = []
    stats = {'total': 0, 'confirmed': 0, 'unconfirmed': 0}

    with open(coverage_cards_jsonl) as f:
        for line in f:
            card = json.loads(line)
            stats['total'] += 1

            coverage_code = card.get('coverage_code')

            # Add amount field
            if coverage_code and coverage_code in code_to_amount:
                amount_text, page_num, line_text = code_to_amount[coverage_code]

                card['amount'] = {
                    'status': 'CONFIRMED',
                    'value_text': amount_text,
                    'source_doc_type': '가입설계서',
                    'source_priority': 'proposal_table',
                    'evidence_ref': {
                        'page_num': page_num,
                        'snippet': line_text[:200]
                    },
                    'notes': []
                }
                stats['confirmed'] += 1
            else:
                # Amount not found → UNCONFIRMED
                card['amount'] = {
                    'status': 'UNCONFIRMED',
                    'value_text': None,
                    'source_doc_type': None,
                    'source_priority': None,
                    'evidence_ref': None,
                    'notes': []
                }
                stats['unconfirmed'] += 1

            enriched_cards.append(card)

    # Write enriched cards (OVERWRITE original)
    with open(output_jsonl, 'w') as f:
        for card in enriched_cards:
            f.write(json.dumps(card, ensure_ascii=False) + '\n')

    return stats
```

### CLI Usage
```bash
python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer hyundai
```

### Output Statistics
```
Total cards: N
CONFIRMED: N (XX.X%)
UNCONFIRMED: N (XX.X%)
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│ INPUT: PDF Documents + Scope Definition                             │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: Extract Text                                                 │
│                                                                      │
│ Input:  data/evidence_sources/{insurer}_manifest.csv                │
│ Output: data/evidence_text/{insurer}/{doc_type}/*.page.jsonl        │
│                                                                      │
│ Tech:   PyMuPDF text extraction (NO OCR)                            │
│ Format: {"page": 1, "text": "..."}                                  │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: Search Evidence                                             │
│                                                                      │
│ Input:  data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl      │
│         data/evidence_text/{insurer}/**/*.page.jsonl                 │
│ Output: data/evidence_pack/{insurer}_evidence_pack.jsonl            │
│                                                                      │
│ Logic:  - Deterministic string matching (NO LLM)                    │
│         - Query expansion (insurer-specific variants)               │
│         - Independent doc-type search (약관/사업방법서/상품요약서)     │
│         - Fallback strategies (Token-AND, KB BM definition)         │
│         - Content-hash lock (STEP NEXT-31-P3)                       │
│                                                                      │
│ Format: Line 1: {"record_type": "meta", "scope_content_hash": ...}  │
│         Line 2+: {"coverage_name_raw": ..., "evidences": [...]}     │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 5: Build Coverage Cards                                        │
│                                                                      │
│ Input:  data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl      │
│         data/evidence_pack/{insurer}_evidence_pack.jsonl            │
│ Output: data/compare/{insurer}_coverage_cards.jsonl (SSOT)          │
│                                                                      │
│ Logic:  - Validate content-hash (scope integrity)                   │
│         - Join-rate gate (>= 95%)                                   │
│         - Evidence diversity selection (max 3, doc-type diversity)  │
│         - Generate standardized cards                               │
│                                                                      │
│ Format: {"insurer": ..., "coverage_name_raw": ...,                  │
│          "evidences": [...], "hits_by_doc_type": {...}}             │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 7: Enrich Amounts                                              │
│                                                                      │
│ Input:  data/evidence_text/{insurer}/가입설계서/*.page.jsonl         │
│         data/compare/{insurer}_coverage_cards.jsonl                  │
│ Output: data/compare/{insurer}_coverage_cards.jsonl (enriched)      │
│                                                                      │
│ Logic:  - Extract (coverage, amount) pairs from proposal tables     │
│         - Normalize coverage names for matching                     │
│         - Match to coverage_code                                    │
│         - Add 'amount' field (CONFIRMED / UNCONFIRMED)              │
│                                                                      │
│ Format: {..., "amount": {"status": "CONFIRMED", "value_text": ...}} │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Coverage Cards (SSOT for Downstream)                        │
│                                                                      │
│ File:   data/compare/{insurer}_coverage_cards.jsonl                 │
│ Schema: CoverageCard with evidence + amount fields                  │
│ Usage:  - API layer (compare, query, explain)                       │
│         - Chat UI                                                   │
│         - Audit/reporting tools                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Constitutional Rules Summary

### Deterministic-Only Enforcement
- ✅ NO LLM - All string matching is deterministic
- ✅ NO OCR - PDF text layer extraction only
- ✅ NO Embedding/Vector DB - Pattern matching only
- ✅ NO Inference - Rules-based logic only

### Independent Doc-Type Search (Hard Requirement)
- ✅ 약관, 사업방법서, 상품요약서 searched **independently**
- ✅ `hits_by_doc_type` field **required** (Step4 output)
- ✅ Evidence diversity selection enforces doc-type diversity (Step5)

### Content-Hash Lock (STEP NEXT-31-P3)
- ✅ Evidence pack **MUST** include meta record (first line)
- ✅ `scope_content_hash` **MUST** match current scope file
- ✅ Validation failure → RuntimeError (hard gate)

### Join-Rate Gate (STEP NEXT-31-P1)
- ✅ Scope rows ↔ Evidence pack rows join rate **MUST** be >= 95%
- ✅ Validation failure → RuntimeError (hard gate)
- ✅ Prevents stale/mismatched evidence_pack usage

### SSOT Paths (STEP NEXT-52-HK)
- ✅ Step3+ **MUST** use `data/scope_v3/` (NOT `data/scope/`)
- ✅ Coverage cards: `data/compare/{insurer}_coverage_cards.jsonl` (SSOT)
- ✅ No legacy path access allowed

---

## Insurer-Specific Logic

### Hyundai
- **Query Variants**: Max 4 (suffix removal, 진단비↔진단, whitespace cleanup)
- **Fallback**: None (standard search only)

### Hanwha
- **Query Variants**: Max 6 (Hyundai rules + 암 용어 브릿지 + 6 suffix variants + bracket normalization)
  - 4대유사암 ↔ 유사암(4대) ↔ 유사암
  - 통합암(4대유사암제외) variants
  - 치료비↔치료, 입원일당↔입원, 수술비↔수술, etc.
- **Fallback**: Token-AND search (if all phrase/variant searches fail)

### KB
- **Query Variants**: Standard (raw + canonical only)
- **Fallback**: 사업방법서 정의 Hit (A4200_1 only, if 사업방법서 search fails)
  - Requires: 암진단비 + 유사암 + 제외 (all 3)
  - Scoring: 보험금/지급 keywords add bonus points
  - Threshold: score >= 3

### Other Insurers (DB, Heungkuk, Lotte, Meritz, Samsung)
- **Query Variants**: Standard (raw + canonical only)
- **Fallback**: None (standard search only)

---

## Testing & Validation

### Unit Tests
- `tests/test_evidence_search.py` - Evidence search logic
- `tests/test_build_cards.py` - Card building logic
- `tests/test_amount_extraction.py` - Amount extraction logic

### Integration Tests
- `tests/test_step_next_18x_fix_regression.py` - End-to-end pipeline validation

### Manual Validation
```bash
# Run full pipeline for single insurer
INSURER=hyundai

# Step3: Extract text
python -m pipeline.step3_extract_text.extract_pdf_text --insurer $INSURER

# Step4: Search evidence
python -m pipeline.step4_evidence_search.search_evidence --insurer $INSURER

# Step5: Build cards
python -m pipeline.step5_build_cards.build_cards --insurer $INSURER

# Step7: Enrich amounts
python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer $INSURER

# Verify output
jq -r '.coverage_name_raw' data/compare/${INSURER}_coverage_cards.jsonl | head
```

---

## Performance Characteristics

### Step3 (Text Extraction)
- **Speed**: ~1-2 seconds per PDF (depends on page count)
- **Bottleneck**: PyMuPDF I/O
- **Scalability**: Linear with page count

### Step4 (Evidence Search)
- **Speed**: ~5-10 seconds per insurer (depends on text corpus size)
- **Bottleneck**: String matching across all pages
- **Scalability**: O(pages × keywords × doc_types)
- **Optimization**: Query variant expansion limited (max 4-6 per insurer)

### Step5 (Build Cards)
- **Speed**: < 1 second per insurer
- **Bottleneck**: JSON I/O + join operation
- **Scalability**: Linear with scope size

### Step7 (Amount Extraction)
- **Speed**: ~2-5 seconds per insurer
- **Bottleneck**: Line-by-line parsing of proposal PDF
- **Scalability**: Linear with proposal page count

---

## Known Limitations

### 1. PDF Text Layer Dependency
- **Issue**: Requires text layer in PDF (no OCR)
- **Impact**: Scanned PDFs without text layer will fail
- **Mitigation**: Ensure all PDF sources have embedded text

### 2. String Matching Brittleness
- **Issue**: Exact/normalized string matching sensitive to typos
- **Impact**: Legitimate coverages may be missed if name varies
- **Mitigation**: Query variant expansion (insurer-specific)

### 3. Multi-Line Fragment Detection
- **Issue**: PDF table cell wrapping can split amount across lines
- **Impact**: Amount extraction may fail for wrapped cells
- **Mitigation**: `merge_amount_fragments()` handles common patterns (STEP NEXT-19)

### 4. Evidence Snippet Context Limit
- **Issue**: Snippet truncated to 500 chars
- **Impact**: Long clauses may be cut off
- **Mitigation**: Adjustable via `max_snippet_length` parameter

### 5. Insurer-Specific Logic Maintenance
- **Issue**: Query variants and fallbacks hard-coded per insurer
- **Impact**: Adding new insurer requires code changes
- **Mitigation**: Centralized in Step4 `EvidenceSearcher` class

---

## Future Improvement Opportunities

### 1. Evidence Search
- [ ] Fuzzy matching (edit distance) for typo tolerance
- [ ] Regex pattern library for complex coverage names
- [ ] Configurable query variant rules (external YAML)

### 2. Amount Extraction
- [ ] Handle decimal amounts (e.g., "1.5천만원")
- [ ] Extract amount ranges (e.g., "1천만원 ~ 5천만원")
- [ ] Multi-currency support (currently KRW only)

### 3. Performance
- [ ] Parallel processing (multi-threading for Step4 search)
- [ ] Incremental updates (avoid full re-run if scope unchanged)
- [ ] Caching layer for text extraction

### 4. Quality Assurance
- [ ] Evidence snippet quality scoring
- [ ] Automatic false-positive detection
- [ ] Coverage name disambiguation (when multiple matches)

---

## Change Log

### STEP NEXT-60-H (2026-01-01)
- Added broken fragment cleanup to Step2-a (upstream of Step3)
- No direct changes to Step3-7

### STEP NEXT-59C (2026-01-01)
- Enhanced Step2 normalization patterns (upstream)

### STEP NEXT-52-HK (2026-01-01)
- Enforced SSOT paths (`data/scope_v3/` only)
- Added path validation in Step4

### STEP NEXT-31-P3 (2025-12-31)
- Added content-hash lock to evidence pack (Step4 output)
- Added content-hash validation in Step5

### STEP NEXT-31-P1 (2025-12-31)
- Added join-rate gate (95% threshold) to Step5

### STEP NEXT-19 (2025-12-30)
- Added multi-line amount fragment merging (Step7)
- Fixed line number prefix removal (Step7)

### STEP NEXT-18B (2025-12-30)
- Enhanced coverage name normalization for matching (Step7)
- Added base contract extraction ("기본계약(담보명)")

### STEP 6-ε.2 (2025-12-29)
- Implemented evidence diversity selection (Step5)
- Added deduplication + fallback priority

### STEP 6-δ (2025-12-29)
- Added KB 사업방법서 정의 Hit fallback (Step4, KB only)

### STEP 4-λ (2025-12-28)
- Added Token-AND fallback search (Step4, Hanwha only)

---

## Glossary

| Term | Definition |
|------|------------|
| **Coverage Card** | Standardized data structure containing coverage name, code, evidence, and metadata |
| **Evidence** | Text snippet from insurance document mentioning coverage |
| **Doc-Type** | Document type (약관, 사업방법서, 상품요약서) |
| **Hits by Doc-Type** | Count of evidence snippets found in each doc-type |
| **Query Variant** | Alternative coverage name form for search (e.g., "진단비" vs "진단") |
| **Fallback** | Alternative search strategy when primary search fails |
| **Content-Hash** | SHA-256 hash of scope file content (for integrity check) |
| **Join-Rate** | Percentage of scope rows successfully joined with evidence |
| **SSOT** | Single Source of Truth (canonical data file) |
| **Canonical** | Standardized coverage name (from 신정원 mapping) |

---

**END OF REPORT**
