"""
STEP NEXT-63: Deterministic Text Templates (NO LLM)

Constitutional Rules:
- NO inference, NO recommendation, NO comparison judgment
- ONLY fact-based output from evidence
- ALL outputs must be deterministically reproducible
"""

from typing import Dict, List, Optional, Any


class DeterministicTemplates:
    """Fixed sentence templates for rendering comparisons (NO LLM)"""

    # ===== EXAMPLE 1: Premium Comparison =====

    @staticmethod
    def premium_table_row(insurer: str, monthly: str, total: str,
                         monthly_ref: str, total_ref: str) -> Dict[str, Any]:
        """Single row for premium comparison table"""
        return {
            "insurer": insurer,
            "monthly_premium": monthly,
            "total_premium": total,
            "monthly_evidence": monthly_ref,
            "total_evidence": total_ref
        }

    @staticmethod
    def premium_not_available(reason: str) -> Dict[str, str]:
        return {
            "status": "NotAvailable",
            "reason": reason
        }

    # ===== EXAMPLE 2: Coverage Limit Comparison =====

    @staticmethod
    def coverage_limit_row(insurer: str, amount: Optional[str],
                          payment_type: Optional[str],
                          limit: Optional[str],
                          conditions: Optional[str],
                          evidence_refs: List[str]) -> Dict[str, Any]:
        """Single row for coverage limit table"""
        return {
            "insurer": insurer,
            "amount": amount or "명시 없음",
            "payment_type": payment_type or "명시 없음",
            "limit": limit or "명시 없음",
            "conditions": conditions or "명시 없음",
            "evidence_refs": evidence_refs
        }

    # ===== EXAMPLE 3: Two-Insurer Comparison =====

    @staticmethod
    def comparison_summary_amount(amounts: List[str]) -> str:
        """Deterministic amount comparison summary"""
        unique_amounts = set(amounts)
        if len(unique_amounts) == 1:
            return f"금액: 동일 ({amounts[0]})"
        else:
            sorted_amounts = sorted(amounts)
            return f"금액: 상이 ({' / '.join(sorted_amounts)})"

    @staticmethod
    def comparison_summary_payment_type(types: List[str]) -> str:
        """Deterministic payment type comparison"""
        unique_types = set(types)
        if len(unique_types) == 1:
            return f"지급유형: 동일 ({types[0]})"
        else:
            return f"지급유형: 상이 ({' / '.join(sorted(types))})"

    @staticmethod
    def comparison_summary_conditions(conditions: List[str]) -> str:
        """Deterministic condition comparison"""
        if all(c == conditions[0] for c in conditions):
            return f"조건: 동일"
        else:
            return f"조건: 차이 있음 (세부 내용은 증거 참조)"

    # ===== EXAMPLE 4: Subtype Eligibility =====

    @staticmethod
    def eligibility_status(has_evidence: bool, is_excluded: bool,
                          is_reduced: bool) -> str:
        """Determine O/X/Unknown status"""
        if not has_evidence:
            return "Unknown"
        if is_excluded:
            return "X"
        if is_reduced:
            return "△"  # Partial coverage
        return "O"

    @staticmethod
    def eligibility_row(insurer: str, status: str,
                       evidence_type: Optional[str],
                       evidence_snippet: Optional[str],
                       evidence_ref: Optional[str]) -> Dict[str, Any]:
        """Single row for subtype eligibility"""
        return {
            "insurer": insurer,
            "status": status,
            "evidence_type": evidence_type or "판단근거 없음",
            "evidence_snippet": evidence_snippet or "",
            "evidence_ref": evidence_ref or ""
        }

    # ===== Forbidden Phrases (for validation) =====

    FORBIDDEN_PHRASES = [
        "추천", "권장", "유리", "불리", "좋", "나쁨",
        "우수", "열등", "최선", "최악", "선호",
        "~해야", "~하세요", "~하는 것이 좋습니다",
        "종합 판단", "결론적으로", "~로 보임", "~으로 추정"
    ]

    @classmethod
    def validate_no_forbidden_phrases(cls, text: str) -> bool:
        """Check if text contains forbidden inference phrases"""
        text_lower = text.lower()
        for phrase in cls.FORBIDDEN_PHRASES:
            if phrase in text_lower:
                return False
        return True
