"""
Q8 Overlay Model - Surgery Repeat Payment Policy

FROZEN: No further expansion allowed.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SurgeryRepeatEvidence:
    """Evidence reference for surgery repeat payment policy"""
    doc_type: str
    page: int
    excerpt: str


@dataclass
class SurgeryRepeatPolicy:
    """
    Contract-level surgery repeat payment policy.

    ENUM:
    - PER_EVENT: 매회 / 회당 / 수술 1회당
    - ANNUAL_LIMIT: 연간 1회 / 연 1회한 / 1년 1회
    - UNKNOWN: 근거 부족
    """
    insurer_key: str
    repeat_payment_policy: str
    display_text: str
    evidence_refs: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insurer_key": self.insurer_key,
            "repeat_payment_policy": self.repeat_payment_policy,
            "display_text": self.display_text,
            "evidence_refs": self.evidence_refs
        }


# Policy display mapping (UI only)
POLICY_DISPLAY = {
    "PER_EVENT": "매회 지급",
    "ANNUAL_LIMIT": "연간 1회한",
    "UNKNOWN": "확인 불가 (근거 없음)"
}
