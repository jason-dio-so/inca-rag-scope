"""
Evidence Extraction Patterns (Deterministic Only)

STEP NEXT-67: Define keyword/regex patterns for extracting evidence slots.
NO LLM. NO INFERENCE. Pattern matching only.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EvidencePattern:
    """Pattern for extracting a specific evidence slot"""
    slot_key: str
    keywords: List[str]  # Keywords to search for
    context_lines: int = 3  # How many lines around match to capture
    table_priority: bool = False  # Prioritize table extraction


# Evidence slot patterns (Korean insurance documents)
EVIDENCE_PATTERNS = {
    "start_date": EvidencePattern(
        slot_key="start_date",
        keywords=[
            "보장개시일", "보장 개시일", "계약일", "보험개시일",
            "책임개시", "책임 개시", "보장시작", "보장 시작"
        ],
        context_lines=5,
        table_priority=False
    ),

    "exclusions": EvidencePattern(
        slot_key="exclusions",
        keywords=[
            "면책사항", "면책 사항", "보장제외", "보장 제외",
            "보상하지 않는", "지급하지 않는", "책임을 지지",
            "제외", "면책"
        ],
        context_lines=10,
        table_priority=False
    ),

    "payout_limit": EvidencePattern(
        slot_key="payout_limit",
        keywords=[
            "지급한도", "지급 한도", "보장한도", "보장 한도",
            "최고한도", "연간한도", "평생한도", "누적한도",
            "지급횟수", "지급 횟수", "회한", "1회한", "최초1회한"
        ],
        context_lines=5,
        table_priority=True  # Often in tables
    ),

    "reduction": EvidencePattern(
        slot_key="reduction",
        keywords=[
            "감액", "감액기간", "감액 기간", "지급률",
            "경과기간", "경과 기간", "면책기간", "면책 기간",
            "소급", "비율", "삭감", "경과년도별"
        ],
        context_lines=7,
        table_priority=True  # Often in tables
    ),

    "entry_age": EvidencePattern(
        slot_key="entry_age",
        keywords=[
            "가입연령", "가입 연령", "가입나이", "가입 나이",
            "가입가능연령", "가입 가능 연령", "최대연령", "최소연령",
            "피보험자 나이", "피보험자나이", "만", "세"
        ],
        context_lines=5,
        table_priority=True
    ),

    "waiting_period": EvidencePattern(
        slot_key="waiting_period",
        keywords=[
            "면책기간", "면책 기간", "대기기간", "대기 기간",
            "보장제외기간", "보장 제외 기간", "경과 후",
            "일이 지난 후", "일 경과"
        ],
        context_lines=5,
        table_priority=False
    ),

    # STEP NEXT-76-A: Extended slots for customer questions 1-5, 8
    "underwriting_condition": EvidencePattern(
        slot_key="underwriting_condition",
        keywords=[
            "유병자", "고혈압", "당뇨", "당뇨병", "인수 가능", "가입 가능",
            "건강고지", "특별조건", "할증", "인수 조건", "가입 제한",
            "질환자", "건강상태", "병력", "과거 질환"
        ],
        context_lines=10,
        table_priority=False
    ),

    "mandatory_dependency": EvidencePattern(
        slot_key="mandatory_dependency",
        keywords=[
            "주계약 필수", "주계약필수", "필수 가입", "필수가입",
            "최소 가입금액", "최소가입금액", "동시 가입", "동시가입",
            "의무 가입", "의무가입", "단독가입", "단독 가입",
            "특약만", "특약 단독"
        ],
        context_lines=7,
        table_priority=False
    ),

    "payout_frequency": EvidencePattern(
        slot_key="payout_frequency",
        keywords=[
            "1회한", "1회 한", "최초 1회한", "최초1회한",
            "연간", "연 1회", "매년", "평생", "생애",
            "재발", "재진단", "반복지급", "반복 지급",
            "회수 제한", "회수제한", "지급회수", "지급 회수",
            "경과기간", "경과 기간"
        ],
        context_lines=7,
        table_priority=True  # Often in payout condition tables
    ),

    "industry_aggregate_limit": EvidencePattern(
        slot_key="industry_aggregate_limit",
        keywords=[
            "업계 누적", "업계누적", "타사 가입", "타사가입",
            "합산", "총 한도", "총한도", "전체 한도",
            "다른 보험사", "타 보험사", "전체 보험",
            "누적한도", "누적 한도", "통산한도", "통산 한도"
        ],
        context_lines=10,
        table_priority=False
    ),

    # STEP NEXT-80: benefit_day_range for 암직접입원비 coverage day range
    "benefit_day_range": EvidencePattern(
        slot_key="benefit_day_range",
        keywords=[
            "입원일당", "입원 일당", "입원일수", "입원 일수",
            "1일부터", "최대", "120일", "180일", "365일",
            "일당", "보장일수", "보장 일수", "지급일수", "지급 일수"
        ],
        context_lines=7,
        table_priority=True  # Often in benefit tables
    ),

    # STEP NEXT-81: subtype_coverage_map for 제자리암/경계성종양 coverage
    "subtype_coverage_map": EvidencePattern(
        slot_key="subtype_coverage_map",
        keywords=[
            "제자리암", "상피내암", "CIS", "Carcinoma in situ",
            "경계성종양", "경계성신생물", "borderline tumor",
            "포함", "보장", "지급", "진단", "수술", "치료",
            "제외", "보장제외", "지급하지 않는", "지급 제외"
        ],
        context_lines=10,
        table_priority=False
    ),
}


class PatternMatcher:
    """Deterministic pattern-based text matcher"""

    def __init__(self):
        self.patterns = EVIDENCE_PATTERNS

    def find_candidates(
        self,
        text: str,
        pattern: EvidencePattern,
        page_num: int
    ) -> List[Dict]:
        """
        Find text candidates matching a pattern.

        Returns list of matches with context.
        """
        lines = text.split('\n')
        candidates = []

        for i, line in enumerate(lines):
            # Check if any keyword matches (case-insensitive)
            for keyword in pattern.keywords:
                if keyword in line:
                    # Extract context window
                    start_idx = max(0, i - pattern.context_lines)
                    end_idx = min(len(lines), i + pattern.context_lines + 1)
                    context = '\n'.join(lines[start_idx:end_idx])

                    candidates.append({
                        "slot_key": pattern.slot_key,
                        "keyword": keyword,
                        "line_num": i + 1,
                        "line_text": line.strip(),
                        "context": context.strip(),
                        "page": page_num
                    })
                    break  # One match per line

        return candidates

    def extract_table_candidates(
        self,
        text: str,
        pattern: EvidencePattern,
        page_num: int
    ) -> List[Dict]:
        """
        Extract candidates from table-like structures.

        Uses simple heuristics:
        - Lines with multiple whitespace gaps (columns)
        - Lines with | or │ separators
        - Consecutive lines with similar structure
        """
        lines = text.split('\n')
        table_candidates = []

        # Detect table-like lines
        for i, line in enumerate(lines):
            # Check if this looks like a table row
            is_table_line = (
                line.count('│') >= 2 or
                line.count('|') >= 2 or
                len(re.findall(r'\s{2,}', line)) >= 2
            )

            if not is_table_line:
                continue

            # Check if any keyword matches
            for keyword in pattern.keywords:
                if keyword in line:
                    # Extract surrounding table context
                    start_idx = max(0, i - 3)
                    end_idx = min(len(lines), i + 3)
                    context = '\n'.join(lines[start_idx:end_idx])

                    table_candidates.append({
                        "slot_key": pattern.slot_key,
                        "keyword": keyword,
                        "line_num": i + 1,
                        "line_text": line.strip(),
                        "context": context.strip(),
                        "page": page_num,
                        "is_table": True
                    })
                    break

        return table_candidates

    def extract_numeric_values(self, text: str) -> List[str]:
        """
        Extract numeric values from text (ages, limits, percentages).

        Examples:
        - "만 15세 ~ 65세" -> ["15", "65"]
        - "연간 5회" -> ["5"]
        - "50%" -> ["50"]
        """
        # Age patterns
        age_pattern = r'만\s*(\d+)\s*세'
        ages = re.findall(age_pattern, text)

        # Count patterns
        count_pattern = r'(\d+)\s*회'
        counts = re.findall(count_pattern, text)

        # Percentage patterns
        pct_pattern = r'(\d+)\s*%'
        pcts = re.findall(pct_pattern, text)

        # General numbers
        num_pattern = r'\d+'
        nums = re.findall(num_pattern, text)

        return list(set(ages + counts + pcts + nums))


def create_evidence_entry(
    candidate: Dict,
    doc_type: str,
    excerpt_max_len: int = 200
) -> Dict:
    """
    Create an evidence entry from a candidate match.

    Args:
        candidate: Match result from PatternMatcher
        doc_type: Document type (가입설계서, 약관, etc.)
        excerpt_max_len: Maximum excerpt length

    Returns:
        Evidence entry dict
    """
    excerpt = candidate["context"]
    if len(excerpt) > excerpt_max_len:
        excerpt = excerpt[:excerpt_max_len] + "..."

    return {
        "slot_key": candidate["slot_key"],
        "doc_type": doc_type,
        "page_start": candidate["page"],
        "page_end": candidate["page"],
        "excerpt": excerpt,
        "locator": {
            "keyword": candidate["keyword"],
            "line_num": candidate.get("line_num"),
            "is_table": candidate.get("is_table", False)
        }
    }
