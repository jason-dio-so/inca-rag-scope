"""
Surgery Repeat Payment Policy Resolver - Q8

Resolves contract-level surgery repeat payment policy for 질병수술비(1~5종).
Evidence-based, deterministic keyword matching only.

ENUM:
- PER_EVENT: 매회 / 회당 / 수술 1회당
- ANNUAL_LIMIT: 연간 1회 / 연 1회한 / 1년 1회
- UNKNOWN: 근거 없음

Document priority: 약관 > 사업방법서 > 상품요약서 > 가입설계서

IMPORTANT:
- Do NOT interpret based on surgery name (e.g., 대장용종)
- Only extract explicitly stated repeat payment conditions
- If conflicting clauses exist, choose more restrictive + record all evidence
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import re

from .document_reader import DocumentSet


@dataclass
class RepeatPolicyEvidence:
    """Evidence for repeat payment policy determination"""
    doc_type: str
    page: int
    excerpt: str
    pattern_matched: str


class SurgeryRepeatPolicyResolver:
    """
    Resolves contract-level surgery repeat payment policy.

    RULE: Evidence-based only. No inference, no estimation, no correction.
    """

    # Document priority order (higher priority first)
    DOC_PRIORITY = ["약관", "사업방법서", "상품요약서", "가입설계서"]

    def __init__(self, document_set: DocumentSet):
        self.document_set = document_set

    def resolve_repeat_payment_policy(self) -> tuple[str, List[RepeatPolicyEvidence]]:
        """
        Resolve repeat payment policy for surgery coverage.

        Returns:
            (policy_value, evidences)
            policy_value: PER_EVENT | ANNUAL_LIMIT | UNKNOWN
            evidences: List of evidence references
        """
        # Search documents in priority order
        for doc_type in self.DOC_PRIORITY:
            doc = self.document_set.get_document(doc_type)
            if not doc:
                continue

            policy, evidences = self._extract_policy_from_document(doc)
            if policy != "UNKNOWN":
                return policy, evidences

        # No evidence found
        return "UNKNOWN", []

    def _extract_policy_from_document(
        self, doc
    ) -> tuple[str, List[RepeatPolicyEvidence]]:
        """
        Extract repeat payment policy from a single document.

        Returns:
            (policy_value, evidences)
        """
        doc.load_text()
        page_count = doc.get_page_count()

        all_evidences = []

        for page_num in range(1, page_count + 1):
            page_text = doc.get_page_text(page_num)

            # Skip if page doesn't mention surgery at all
            if not self._is_surgery_related_page(page_text):
                continue

            # Split into lines for analysis
            lines = page_text.split('\n')

            for i, line in enumerate(lines):
                # Check for repeat payment patterns
                policy, excerpt, pattern = self._match_repeat_pattern(line, lines, i)

                if policy != "UNKNOWN":
                    evidence = RepeatPolicyEvidence(
                        doc_type=doc.doc_type,
                        page=page_num,
                        excerpt=excerpt,
                        pattern_matched=pattern
                    )
                    all_evidences.append(evidence)

        # Determine final policy from all evidences
        if all_evidences:
            return self._consolidate_evidences(all_evidences)

        return "UNKNOWN", []

    def _is_surgery_related_page(self, text: str) -> bool:
        """Check if page mentions disease surgery coverage (질병수술비)"""
        # Must mention 질병수술비 specifically
        return "질병수술비" in text

    def _match_repeat_pattern(
        self, line: str, lines: List[str], line_idx: int
    ) -> tuple[str, str, str]:
        """
        Match repeat payment pattern in a line.

        Returns:
            (policy_value, excerpt, pattern_name)
        """
        # Get broader context (up to 5 lines before and after)
        context_start = max(0, line_idx - 5)
        context_end = min(len(lines), line_idx + 6)
        context_lines = lines[context_start:context_end]
        context = ' '.join(context_lines)

        # Must mention 질병수술비 in the context
        if "질병수술비" not in context:
            return "UNKNOWN", "", ""

        # Get excerpt context (current line + next 2)
        excerpt_lines = lines[line_idx:line_idx + 3]
        excerpt = ' '.join(excerpt_lines)

        # Pattern 1: PER_EVENT (매회 / 회당 / 수술 1회당)
        if self._contains_per_event_pattern(line):
            return "PER_EVENT", excerpt[:300], "매회지급"

        # Pattern 2: ANNUAL_LIMIT (연간 1회 / 연 1회한 / 1년 1회)
        if self._contains_annual_limit_pattern(line):
            return "ANNUAL_LIMIT", excerpt[:300], "연간1회한"

        return "UNKNOWN", "", ""

    def _contains_per_event_pattern(self, text: str) -> bool:
        """Check for per-event payment pattern"""
        # Strong indicators: must have payment context AND frequency term
        has_payment_context = any(keyword in text for keyword in ['지급', '보험금'])

        per_event_patterns = [
            r'매\s*회',  # 매회
            r'회\s*당',  # 회당
            r'수술\s*1\s*회\s*당',  # 수술 1회당
            r'1\s*회\s*당',  # 1회당
        ]

        if has_payment_context:
            for pattern in per_event_patterns:
                if re.search(pattern, text):
                    return True

        return False

    def _contains_annual_limit_pattern(self, text: str) -> bool:
        """Check for annual limit pattern"""
        # Strong indicators: frequency term with limit context
        annual_patterns = [
            r'연간\s*1\s*회',  # 연간 1회
            r'연\s*1\s*회한',  # 연 1회한
            r'1\s*년\s*1\s*회',  # 1년 1회
            r'연\s*1\s*회\s*한',  # 연 1회 한 (spaced)
        ]

        for pattern in annual_patterns:
            if re.search(pattern, text):
                # Make sure it's in a payment/limit context, not just a coverage name
                if any(keyword in text for keyword in ['지급', '한도', '한함']):
                    return True

        return False

    def _consolidate_evidences(
        self, evidences: List[RepeatPolicyEvidence]
    ) -> tuple[str, List[RepeatPolicyEvidence]]:
        """
        Consolidate multiple evidences into single policy.

        Priority order: ANNUAL_LIMIT > PER_EVENT (more restrictive wins)

        Returns:
            (policy_value, filtered_evidences)
        """
        # Count by policy type
        policy_counts = {}
        for ev in evidences:
            policy = self._evidence_to_policy(ev.pattern_matched)
            policy_counts[policy] = policy_counts.get(policy, 0) + 1

        # Determine final policy (most restrictive wins)
        if "ANNUAL_LIMIT" in policy_counts:
            final_policy = "ANNUAL_LIMIT"
        elif "PER_EVENT" in policy_counts:
            final_policy = "PER_EVENT"
        else:
            return "UNKNOWN", []

        # Filter evidences matching final policy
        filtered = [
            ev for ev in evidences
            if self._evidence_to_policy(ev.pattern_matched) == final_policy
        ]

        return final_policy, filtered

    def _evidence_to_policy(self, pattern: str) -> str:
        """Map pattern name to policy value"""
        if "매회지급" in pattern:
            return "PER_EVENT"
        elif "연간1회한" in pattern:
            return "ANNUAL_LIMIT"
        return "UNKNOWN"


def resolve_surgery_repeat_policy(insurer_key: str) -> Dict[str, Any]:
    """
    Standalone function to resolve surgery repeat payment policy for an insurer.

    Args:
        insurer_key: Insurer identifier

    Returns:
        {
            "insurer_key": str,
            "repeat_payment_policy": str,  # PER_EVENT | ANNUAL_LIMIT | UNKNOWN
            "display_text": str,  # 매회 지급 | 연간 1회한 | 확인 불가 (근거 없음)
            "evidence_refs": [
                {
                    "doc_type": str,
                    "page": int,
                    "excerpt": str
                }
            ]
        }
    """
    from pathlib import Path

    # Load document set
    project_root = Path(__file__).parent.parent.parent
    sources_dir = project_root / "data" / "sources" / "insurers"
    document_set = DocumentSet(insurer_key, sources_dir)

    # Resolve policy
    resolver = SurgeryRepeatPolicyResolver(document_set)
    policy, evidences = resolver.resolve_repeat_payment_policy()

    # Map policy to display text
    display_map = {
        "PER_EVENT": "매회 지급",
        "ANNUAL_LIMIT": "연간 1회한",
        "UNKNOWN": "확인 불가 (근거 없음)"
    }

    # Format result
    result = {
        "insurer_key": insurer_key,
        "repeat_payment_policy": policy,
        "display_text": display_map[policy],
        "evidence_refs": [
            {
                "doc_type": ev.doc_type,
                "page": ev.page,
                "excerpt": ev.excerpt
            }
            for ev in evidences
        ]
    }

    return result
