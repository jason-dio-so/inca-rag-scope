"""
Q7 Overlay Model - Contract-Level Premium Waiver Policy

FROZEN: No further expansion allowed.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class WaiverPolicyEvidence:
    """Evidence reference for waiver policy"""
    doc_type: str
    page: int
    excerpt: str
    locator: str = None


@dataclass
class ContractWaiverPolicy:
    """
    Contract-level premium waiver policy.

    has_sanjeong_teukrye ENUM:
    - YES: 산정특례 explicitly mentioned as waiver trigger
    - NO: Document explicitly states 산정특례 is NOT a waiver trigger
    - UNKNOWN: 근거 부족 (no evidence either way)
    """
    insurer_key: str
    waiver_triggers: List[str]
    has_sanjeong_teukrye: str  # YES, NO, UNKNOWN
    evidence_refs: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insurer_key": self.insurer_key,
            "waiver_triggers": self.waiver_triggers,
            "has_sanjeong_teukrye": self.has_sanjeong_teukrye,
            "evidence_refs": self.evidence_refs
        }


# Status display mapping (UI only)
SANJEONG_TEUKRYE_DISPLAY = {
    "YES": "산정특례가 납입면제 사유로 명시됨",
    "NO": "산정특례가 납입면제 사유가 아님",
    "UNKNOWN": "확인 불가 (근거 부족)"
}
