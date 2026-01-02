"""
STEP NEXT-65R: Customer View Builder

Extract customer-understandable benefit descriptions from existing evidence.

Constitutional Rules:
- NO LLM usage
- NO new extraction pipelines
- NO Step1/Step2 modification
- Uses existing coverage_cards.evidences only
- All outputs must be evidence-traceable

Evidence Priority:
1. 사업방법서
2. 상품요약서
3. 약관
(가입설계서 summary table is for amounts only, NOT benefit descriptions)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EvidenceRef:
    """Evidence reference for traceability"""
    doc_type: str
    page: int
    file_path: Optional[str] = None
    snippet_preview: Optional[str] = None  # First 100 chars

    def to_dict(self) -> dict:
        return {
            "doc_type": self.doc_type,
            "page": self.page,
            "file_path": self.file_path,
            "snippet_preview": self.snippet_preview
        }


class BenefitDescriptionExtractor:
    """
    Extract benefit descriptions from evidence snippets.

    Rules (deterministic):
    - Extract description sentences from evidence
    - Remove structural artifacts (조문 번호, PDF markers, table fragments)
    - Length: 2-4 sentences
    - Style: explanatory (ends with "~을 보장합니다" or similar)
    - NO summarization / inference / recommendations
    """

    # Structural noise to remove
    NOISE_PATTERNS = [
        r'^제?\d+조\s*[-.]?\s*\d*\.?\s*',  # 제4조, 4-1, 4.1
        r'^\d+[-\.]\d+[-\.]?\d*\s*',       # 4-1-13, 6.1.2
        r'^\s*\d+\s*$',                     # Standalone page numbers
        r'^\s*표\s*\d+',                    # 표1, 표2
        r'^\s*\[.*?\]\s*',                  # [갱신형], [특약]
        r'^\s*·\s*',                        # Bullet points at start
        r'^\s*-\s*',                        # Dash bullets
        r'^\s*\d+\)\s*',                    # 1), 2)
    ]

    # Exclusion keywords (structural, not benefit descriptions)
    FORBIDDEN_KEYWORDS = [
        '목차', '페이지', '특별약관', '보통약관', '상품요약서',
        '가입설계서', '사업방법서', '약관', '담보명', '보험료',
        '선택', '계약'  # Table headers in business method docs
    ]

    @classmethod
    def extract(cls, evidences: List[Dict[str, Any]], doc_type_priority: List[str]) -> Tuple[str, List[EvidenceRef], str]:
        """
        Extract benefit description from evidences.

        Args:
            evidences: List of evidence dicts (from CoverageCard.evidences)
            doc_type_priority: Priority order (e.g., ['사업방법서', '상품요약서', '약관'])

        Returns:
            Tuple of (benefit_description, evidence_refs, extraction_notes)
        """
        # Filter by doc_type priority
        for doc_type in doc_type_priority:
            doc_evidences = [e for e in evidences if e.get('doc_type') == doc_type]
            if doc_evidences:
                # Try to extract from this doc_type
                description, refs, notes = cls._extract_from_evidences(doc_evidences, doc_type)
                if description:
                    return description, refs, notes

        # Fallback: no valid description found
        # NOTE: Most evidence snippets are TOC/lists, not descriptive text
        # This is expected per STEP NEXT-65R constraints (NO proposal DETAIL extraction)
        return "명시 없음", [], "Evidence snippets contain TOC/lists, not descriptive benefit text"

    @classmethod
    def _extract_from_evidences(cls, evidences: List[Dict[str, Any]], doc_type: str) -> Tuple[str, List[EvidenceRef], str]:
        """Extract description from evidences of a single doc_type"""
        for ev in evidences:
            snippet = ev.get('snippet', '')
            if not snippet:
                continue

            # Clean snippet
            cleaned = cls._clean_snippet(snippet)
            if not cleaned:
                continue

            # Check if this is a valid description (not just structural noise)
            if cls._is_valid_description(cleaned):
                # Extract 2-4 sentences
                sentences = cls._extract_sentences(cleaned, max_sentences=4)
                if sentences:
                    description = ' '.join(sentences)
                    ref = EvidenceRef(
                        doc_type=doc_type,
                        page=ev.get('page', 0),
                        file_path=ev.get('file_path'),
                        snippet_preview=snippet[:100]
                    )
                    notes = f"Extracted from {doc_type} p.{ev.get('page', 0)}"
                    return description, [ref], notes

        # No valid description found in this doc_type
        return "", [], ""

    @classmethod
    def _clean_snippet(cls, snippet: str) -> str:
        """Remove structural noise from snippet"""
        lines = snippet.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove noise patterns
            for pattern in cls.NOISE_PATTERNS:
                line = re.sub(pattern, '', line)

            # Remove forbidden keywords
            if any(kw in line for kw in cls.FORBIDDEN_KEYWORDS):
                continue

            # Keep non-empty lines
            line = line.strip()
            if line and len(line) > 10:  # Minimum length threshold
                cleaned_lines.append(line)

        return ' '.join(cleaned_lines)

    @classmethod
    def _is_valid_description(cls, text: str) -> bool:
        """Check if text is a valid benefit description"""
        # Must contain benefit-related keywords
        benefit_keywords = ['지급', '보장', '진단확정', '수술', '입원', '치료', '지원', '받은']
        if not any(kw in text for kw in benefit_keywords):
            return False

        # Must not be too short (likely a title/header)
        if len(text) < 20:
            return False

        # Filter out bullet lists (too many coverage names listed)
        # If text has more than 3 coverage name patterns, it's likely a TOC
        coverage_patterns = [
            r'진단비', r'수술비', r'입원', r'통원', r'치료비'
        ]
        pattern_count = sum(1 for p in coverage_patterns if len(re.findall(p, text)) > 2)
        if pattern_count >= 2:
            return False

        return True

    @classmethod
    def _extract_sentences(cls, text: str, max_sentences: int = 4) -> List[str]:
        """Extract up to max_sentences from text"""
        # Split by common sentence endings
        sentence_endings = r'[.。!?]\s+'
        sentences = re.split(sentence_endings, text)

        # Filter and clean
        valid_sentences = []
        for sent in sentences[:max_sentences]:
            sent = sent.strip()
            if sent and len(sent) > 15:  # Minimum sentence length
                valid_sentences.append(sent)

        return valid_sentences[:max_sentences]


class PaymentTypeLimitExtractor:
    """
    Extract payment_type and limit_conditions from evidence.

    Uses existing normalize_fields.py logic (deterministic pattern matching).
    """

    PAYMENT_TYPE_PATTERNS = [
        (r'일시금.*지급', 'lump_sum'),
        (r'보험가입금액.*지급', 'lump_sum'),
        (r'정액.*지급', 'lump_sum'),
        (r'진단.*일시금', 'lump_sum'),
        (r'입원.*일당', 'per_day'),
        (r'입원.*일수당', 'per_day'),
        (r'일당.*지급', 'per_day'),
        (r'수술.*건당', 'per_event'),
        (r'수술.*회당', 'per_event'),
        (r'건당.*지급', 'per_event'),
    ]

    LIMIT_PATTERNS = [
        (r'최초\s*(\d+)\s*회', 'count_first'),
        (r'연간?\s*(\d+)\s*회', 'count_annual'),
        (r'평생\s*(\d+)\s*회', 'count_lifetime'),
        (r'보험기간\s*중\s*(\d+)\s*회', 'count_lifetime'),
        (r'(\d+)\s*회\s*한', 'count_limit'),
        (r'(\d+)\s*회', 'count_simple'),
        (r'(\d+)\s*일\s*한도', 'days_limit'),
    ]

    @classmethod
    def extract_payment_type(cls, evidences: List[Dict[str, Any]]) -> Tuple[Optional[str], List[EvidenceRef], str]:
        """
        Extract payment type from evidences.

        Returns:
            Tuple of (payment_type, evidence_refs, extraction_notes)
        """
        for ev in evidences:
            snippet = ev.get('snippet', '')
            if not snippet:
                continue

            for pattern, payment_type in cls.PAYMENT_TYPE_PATTERNS:
                if re.search(pattern, snippet):
                    ref = EvidenceRef(
                        doc_type=ev.get('doc_type', ''),
                        page=ev.get('page', 0),
                        file_path=ev.get('file_path'),
                        snippet_preview=snippet[:100]
                    )
                    notes = f"Pattern matched: {pattern} in {ev.get('doc_type')} p.{ev.get('page', 0)}"
                    return payment_type, [ref], notes

        # Not found
        return None, [], "No payment type pattern matched in evidence"

    @classmethod
    def extract_limit_conditions(cls, evidences: List[Dict[str, Any]]) -> Tuple[List[str], List[EvidenceRef], str]:
        """
        Extract limit conditions from evidences.

        Returns:
            Tuple of (limit_conditions, evidence_refs, extraction_notes)
        """
        conditions = []
        refs = []
        notes_parts = []

        for ev in evidences:
            snippet = ev.get('snippet', '')
            if not snippet:
                continue

            for pattern, limit_type in cls.LIMIT_PATTERNS:
                match = re.search(pattern, snippet)
                if match:
                    count = match.group(1) if match.groups() else None

                    # Build condition string
                    if limit_type == 'count_first':
                        conditions.append(f"최초 {count}회")
                    elif limit_type == 'count_annual':
                        conditions.append(f"연 {count}회")
                    elif limit_type == 'count_lifetime':
                        conditions.append(f"보험기간 중 {count}회")
                    elif limit_type in ['count_limit', 'count_simple']:
                        conditions.append(f"{count}회 한도")
                    elif limit_type == 'days_limit':
                        conditions.append(f"{count}일 한도")

                    ref = EvidenceRef(
                        doc_type=ev.get('doc_type', ''),
                        page=ev.get('page', 0),
                        file_path=ev.get('file_path'),
                        snippet_preview=snippet[:100]
                    )
                    refs.append(ref)
                    notes_parts.append(f"{limit_type} matched in {ev.get('doc_type')} p.{ev.get('page', 0)}")
                    break  # One limit per evidence

        if conditions:
            notes = "; ".join(notes_parts)
            return conditions, refs, notes
        else:
            return [], [], "No limit conditions found in evidence"


class ExclusionNotesExtractor:
    """
    Extract exclusion/restriction notes from evidence.

    Deterministic keyword matching (NO inference).
    """

    EXCLUSION_KEYWORDS = {
        '유사암 제외': '유사암 제외',
        '유사암제외': '유사암 제외',
        '면책': '면책 조건',
        '감액': '감액 조건',
        '대기기간': '대기기간',
        '90일': '90일 대기기간',
        '갱신형': '갱신형',
        '제외': '보장 제외 조건',
    }

    @classmethod
    def extract(cls, evidences: List[Dict[str, Any]]) -> Tuple[List[str], List[EvidenceRef], str]:
        """
        Extract exclusion notes from evidences.

        Returns:
            Tuple of (exclusion_notes, evidence_refs, extraction_notes)
        """
        exclusions = []
        refs = []
        notes_parts = []

        for ev in evidences:
            snippet = ev.get('snippet', '')
            if not snippet:
                continue

            for keyword, note in cls.EXCLUSION_KEYWORDS.items():
                if keyword in snippet:
                    if note not in exclusions:
                        exclusions.append(note)
                        ref = EvidenceRef(
                            doc_type=ev.get('doc_type', ''),
                            page=ev.get('page', 0),
                            file_path=ev.get('file_path'),
                            snippet_preview=snippet[:100]
                        )
                        refs.append(ref)
                        notes_parts.append(f"'{keyword}' found in {ev.get('doc_type')} p.{ev.get('page', 0)}")

        if exclusions:
            notes = "; ".join(notes_parts)
            return exclusions, refs, notes
        else:
            return [], [], "No exclusion keywords found in evidence"


def build_customer_view(
    evidences: List[Dict[str, Any]],
    proposal_detail_facts: Optional[Dict[str, Any]] = None,
    insurer: Optional[str] = None,
    coverage_name_raw: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build customer_view from coverage card evidences.

    STEP NEXT-67D: Priority #1 is proposal DETAIL (보장/보상내용)
    KB NEXT PATCH: Handle "명시 없음" for coverages without benefit descriptions

    Args:
        evidences: List of Evidence dicts from CoverageCard
        proposal_detail_facts: Optional proposal DETAIL facts (from Step1)
        insurer: Insurer code (for KB-specific handling)
        coverage_name_raw: Coverage name (for KB-specific detection)

    Returns:
        CustomerView dict with:
        - benefit_description
        - payment_type
        - limit_conditions
        - exclusion_notes
        - evidence_refs
        - extraction_notes
    """
    # Evidence priority (STEP NEXT-65R + 67D)
    doc_type_priority = ['사업방법서', '상품요약서', '약관']
    policy_evidences = [e for e in evidences if e.get('doc_type') in doc_type_priority]

    # STEP NEXT-67D: Priority #1 - Proposal DETAIL table (보장/보상내용)
    if proposal_detail_facts and proposal_detail_facts.get('benefit_description_text'):
        description = proposal_detail_facts['benefit_description_text']
        desc_refs = [
            EvidenceRef(
                doc_type="가입설계서",
                page=proposal_detail_facts.get('detail_page', 0),
                snippet_preview=description[:100]
            )
        ]
        desc_notes = f"Proposal DETAIL table p.{proposal_detail_facts.get('detail_page', 0)}"
    else:
        # KB NEXT PATCH: Check if this is KB p.2-3 coverage (no description column)
        # KB p.2-3 coverages have NO proposal_detail_facts at all
        # This is NOT an extraction failure, but source document constraint
        if insurer == 'kb' and proposal_detail_facts is None:
            # Check if this is from summary table pages (p.2-3)
            # Summary table has coverage name only, no description column
            summary_evidences = [
                e for e in evidences
                if e.get('doc_type') == '가입설계서' and e.get('page', 0) in [2, 3]
            ]
            if summary_evidences:
                # Explicitly mark as "명시 없음" (not extraction failure)
                description = "명시 없음"
                desc_refs = []
                desc_notes = "KB 가입설계서 p.2–3 해당 담보는 보장내용 설명 컬럼이 없어 '명시 없음' 처리"
            else:
                # Fallback: Extract from policy/business/summary evidences
                description, desc_refs, desc_notes = BenefitDescriptionExtractor.extract(
                    policy_evidences, doc_type_priority
                )
        else:
            # Fallback: Extract from policy/business/summary evidences
            description, desc_refs, desc_notes = BenefitDescriptionExtractor.extract(
                policy_evidences, doc_type_priority
            )

    # Extract payment type
    payment_type, payment_refs, payment_notes = PaymentTypeLimitExtractor.extract_payment_type(
        policy_evidences
    )

    # Extract limit conditions
    limit_conditions, limit_refs, limit_notes = PaymentTypeLimitExtractor.extract_limit_conditions(
        policy_evidences
    )

    # Extract exclusion notes
    exclusion_notes, excl_refs, excl_notes = ExclusionNotesExtractor.extract(
        policy_evidences
    )

    # Aggregate evidence refs
    all_refs = desc_refs + payment_refs + limit_refs + excl_refs
    # Deduplicate by (doc_type, page)
    seen = set()
    unique_refs = []
    for ref in all_refs:
        key = (ref.doc_type, ref.page)
        if key not in seen:
            seen.add(key)
            unique_refs.append(ref)

    # Aggregate extraction notes
    extraction_notes = " | ".join(filter(None, [desc_notes, payment_notes, limit_notes, excl_notes]))

    return {
        'benefit_description': description,
        'payment_type': payment_type,
        'limit_conditions': limit_conditions,
        'exclusion_notes': exclusion_notes,
        'evidence_refs': [ref.to_dict() for ref in unique_refs],
        'extraction_notes': extraction_notes
    }
