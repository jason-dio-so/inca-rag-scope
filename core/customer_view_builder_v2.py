"""
STEP NEXT-66: Customer View Builder v2 (Vector-Enhanced)

Extract customer-understandable fields using vector search + deterministic rules.

Constitutional Rules:
- NO LLM usage
- Vector search for candidate retrieval
- Deterministic rule filters for extraction
- Evidence traceability (chunk_id/doc_type/page)
- Evidence priority: 사업방법서 > 상품요약서 > 약관 (for benefit_description)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from core.vector_search_file import search_chunks, ChunkHit


@dataclass
class EvidenceRef:
    """Evidence reference for traceability"""
    doc_type: str
    page: int
    chunk_id: Optional[str] = None
    file_path: Optional[str] = None
    snippet_preview: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "doc_type": self.doc_type,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "snippet_preview": self.snippet_preview
        }


class QueryVariantGenerator:
    """
    Generate query variants for vector search (deterministic).

    Rules:
    - Canonical name (as-is)
    - Remove parentheses and modifiers
    - Extract key disease/condition terms
    """

    # Common modifiers to remove
    MODIFIERS = [
        r'\(.*?\)',  # Parentheses
        r'유사암\s*제외',
        r'특정.*?제외',
        r'\d+일\s*면책',
        r'\d+년\s*납',
        r'갱신형',
    ]

    # Disease/condition keywords
    DISEASE_KEYWORDS = [
        '암', '유사암', '제자리암', '경계성종양', '소액암',
        '뇌출혈', '뇌졸중', '뇌혈관질환', '심근경색', '허혈성심장질환',
        '치매', '수술', '입원', '통원'
    ]

    @classmethod
    def generate(cls, coverage_name: str) -> List[str]:
        """
        Generate query variants from coverage name.

        Args:
            coverage_name: Canonical coverage name

        Returns:
            List of query strings (ordered by priority)
        """
        variants = []

        # 1. Original (canonical)
        variants.append(coverage_name)

        # 2. Remove modifiers
        cleaned = coverage_name
        for mod in cls.MODIFIERS:
            cleaned = re.sub(mod, '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if cleaned and cleaned != coverage_name:
            variants.append(cleaned)

        # 3. Extract disease keywords
        for kw in cls.DISEASE_KEYWORDS:
            if kw in coverage_name:
                variants.append(kw)

        # Deduplicate while preserving order
        seen = set()
        unique_variants = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                unique_variants.append(v)

        return unique_variants


class BenefitDescriptionExtractor:
    """
    Extract benefit description from vector search results.

    Uses evidence priority: 사업방법서 > 상품요약서 > 약관
    """

    DOC_TYPE_PRIORITY = ['사업방법서', '상품요약서', '약관']

    # Min score threshold (cosine similarity)
    MIN_SCORE = 0.3

    # Description indicators (Korean insurance docs)
    DESCRIPTION_INDICATORS = [
        '지급', '보장', '진단확정', '수술', '입원', '치료',
        '받은', '경우', '때', '다음'
    ]

    # Noise patterns (section numbers, table fragments)
    NOISE_PATTERNS = [
        r'^제?\d+조\s*[-.]?\s*\d*',  # 제4조, 4-1
        r'^\d+[-\.]\d+',  # Section numbers
        r'^표\s*\d+',  # Table markers
    ]

    @classmethod
    def extract(cls, hits: List[ChunkHit]) -> Tuple[str, List[EvidenceRef], str]:
        """
        Extract benefit description from search hits.

        Args:
            hits: Vector search results (ChunkHit objects)

        Returns:
            (description, evidence_refs, extraction_notes)
        """
        # Filter low-score hits
        high_score_hits = [h for h in hits if h.score >= cls.MIN_SCORE]

        if not high_score_hits:
            return "명시 없음", [], "No high-confidence vector matches"

        # Try each doc_type in priority order
        for doc_type in cls.DOC_TYPE_PRIORITY:
            doc_hits = [h for h in high_score_hits if h.doc_type == doc_type]

            for hit in doc_hits:
                # Check if text is a valid description
                if cls._is_valid_description(hit.text):
                    # Extract 2-4 sentences
                    sentences = cls._extract_sentences(hit.text, max_sentences=4)

                    if sentences:
                        description = ' '.join(sentences)
                        ref = EvidenceRef(
                            doc_type=hit.doc_type,
                            page=hit.page,
                            chunk_id=hit.chunk_id,
                            file_path=hit.file_path,
                            snippet_preview=hit.text[:100]
                        )
                        notes = f"Vector search: {doc_type} p.{hit.page} (score={hit.score:.3f})"
                        return description, [ref], notes

        # No valid description found
        return "명시 없음", [], "Vector hits did not contain descriptive text"

    @classmethod
    def _is_valid_description(cls, text: str) -> bool:
        """Check if text is a valid benefit description"""
        # Must contain description indicators
        if not any(ind in text for ind in cls.DESCRIPTION_INDICATORS):
            return False

        # Must not be noise (section numbers, etc.)
        for pattern in cls.NOISE_PATTERNS:
            if re.match(pattern, text.strip()):
                return False

        # Must be long enough
        if len(text) < 30:
            return False

        return True

    @classmethod
    def _extract_sentences(cls, text: str, max_sentences: int = 4) -> List[str]:
        """Extract up to max_sentences from text"""
        sentence_endings = r'[.。!?]\s+'
        sentences = re.split(sentence_endings, text)

        valid = []
        for sent in sentences[:max_sentences]:
            sent = sent.strip()
            if sent and len(sent) > 15:
                valid.append(sent)

        return valid[:max_sentences]


class PaymentTypeLimitExtractor:
    """
    Extract payment_type and limit_conditions from vector search results.

    Deterministic pattern matching.
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
    def extract_payment_type(cls, hits: List[ChunkHit]) -> Tuple[Optional[str], List[EvidenceRef], str]:
        """Extract payment type from hits"""
        for hit in hits:
            for pattern, payment_type in cls.PAYMENT_TYPE_PATTERNS:
                if re.search(pattern, hit.text):
                    ref = EvidenceRef(
                        doc_type=hit.doc_type,
                        page=hit.page,
                        chunk_id=hit.chunk_id,
                        file_path=hit.file_path,
                        snippet_preview=hit.text[:100]
                    )
                    notes = f"Pattern '{pattern}' in {hit.doc_type} p.{hit.page}"
                    return payment_type, [ref], notes

        return None, [], "No payment type pattern matched"

    @classmethod
    def extract_limit_conditions(cls, hits: List[ChunkHit]) -> Tuple[List[str], List[EvidenceRef], str]:
        """Extract limit conditions from hits"""
        conditions = []
        refs = []
        notes_parts = []

        for hit in hits:
            for pattern, limit_type in cls.LIMIT_PATTERNS:
                match = re.search(pattern, hit.text)
                if match:
                    count = match.group(1) if match.groups() else None

                    # Build condition string
                    if limit_type == 'count_first':
                        cond = f"최초 {count}회"
                    elif limit_type == 'count_annual':
                        cond = f"연 {count}회"
                    elif limit_type == 'count_lifetime':
                        cond = f"보험기간 중 {count}회"
                    elif limit_type in ['count_limit', 'count_simple']:
                        cond = f"{count}회 한도"
                    elif limit_type == 'days_limit':
                        cond = f"{count}일 한도"
                    else:
                        continue

                    if cond not in conditions:
                        conditions.append(cond)
                        ref = EvidenceRef(
                            doc_type=hit.doc_type,
                            page=hit.page,
                            chunk_id=hit.chunk_id,
                            file_path=hit.file_path,
                            snippet_preview=hit.text[:100]
                        )
                        refs.append(ref)
                        notes_parts.append(f"{limit_type} in {hit.doc_type} p.{hit.page}")
                    break  # One limit per hit

        if conditions:
            return conditions, refs, "; ".join(notes_parts)
        else:
            return [], [], "No limit conditions found"


class ExclusionNotesExtractor:
    """
    Extract exclusion/restriction notes from vector search results.

    Deterministic keyword matching.
    """

    EXCLUSION_KEYWORDS = {
        '유사암 제외': '유사암 제외',
        '유사암제외': '유사암 제외',
        '소액암': '소액암',
        '제자리암': '제자리암',
        '경계성종양': '경계성종양',
        '특정암': '특정암',
        '면책': '면책 조건',
        '감액': '감액 조건',
        '대기기간': '대기기간',
        '90일': '90일 대기기간',
        '갱신형': '갱신형',
    }

    @classmethod
    def extract(cls, hits: List[ChunkHit]) -> Tuple[List[str], List[EvidenceRef], str]:
        """Extract exclusion notes from hits"""
        exclusions = []
        refs = []
        notes_parts = []

        for hit in hits:
            for keyword, note in cls.EXCLUSION_KEYWORDS.items():
                if keyword in hit.text and note not in exclusions:
                    exclusions.append(note)
                    ref = EvidenceRef(
                        doc_type=hit.doc_type,
                        page=hit.page,
                        chunk_id=hit.chunk_id,
                        file_path=hit.file_path,
                        snippet_preview=hit.text[:100]
                    )
                    refs.append(ref)
                    notes_parts.append(f"'{keyword}' in {hit.doc_type} p.{hit.page}")

        if exclusions:
            return exclusions, refs, "; ".join(notes_parts)
        else:
            return [], [], "No exclusion keywords found"


def build_customer_view_v2(
    axis: str,
    coverage_code: str,
    coverage_name: str,
    index_dir: str = "data/vector_index/v1"
) -> Dict[str, Any]:
    """
    Build customer_view using vector search (v2).

    Args:
        axis: Insurance axis (e.g., "samsung")
        coverage_code: Coverage code (e.g., "A4200_1")
        coverage_name: Canonical coverage name
        index_dir: Vector index directory

    Returns:
        CustomerView dict with:
        - benefit_description
        - payment_type
        - limit_conditions
        - exclusion_notes
        - evidence_refs
        - extraction_notes
    """
    # Check if index exists
    index_path = Path(index_dir) / f"{axis}__chunks.jsonl"
    if not index_path.exists():
        # Fallback: return empty customer_view
        return {
            'benefit_description': '명시 없음',
            'payment_type': None,
            'limit_conditions': [],
            'exclusion_notes': [],
            'evidence_refs': [],
            'extraction_notes': f"Vector index not found: {index_path}"
        }

    # Generate query variants
    query_variants = QueryVariantGenerator.generate(coverage_name)

    # Search with primary query (canonical name)
    primary_query = query_variants[0]

    # Search in priority order: 사업방법서 > 상품요약서 > 약관
    doc_types = ['사업방법서', '상품요약서', '약관']

    try:
        hits = search_chunks(
            axis=axis,
            query=primary_query,
            doc_types=doc_types,
            top_k=20,  # Get more candidates
            index_dir=index_dir
        )
    except Exception as e:
        # Index not ready
        return {
            'benefit_description': '명시 없음',
            'payment_type': None,
            'limit_conditions': [],
            'exclusion_notes': [],
            'evidence_refs': [],
            'extraction_notes': f"Vector search failed: {e}"
        }

    # Extract fields from hits
    description, desc_refs, desc_notes = BenefitDescriptionExtractor.extract(hits)
    payment_type, payment_refs, payment_notes = PaymentTypeLimitExtractor.extract_payment_type(hits)
    limit_conditions, limit_refs, limit_notes = PaymentTypeLimitExtractor.extract_limit_conditions(hits)
    exclusion_notes, excl_refs, excl_notes = ExclusionNotesExtractor.extract(hits)

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
