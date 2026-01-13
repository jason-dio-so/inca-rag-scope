"""
Q8 SSOT Loader - Load surgery repeat payment policy from JSONL

FROZEN: Read-only loader for q8_surgery_repeat_policy_v1.jsonl
"""

import json
from pathlib import Path
from typing import List, Optional

from .model import SurgeryRepeatPolicy


def load_q8_surgery_repeat_policy(
    insurers_filter: Optional[List[str]] = None
) -> List[SurgeryRepeatPolicy]:
    """
    Load Q8 surgery repeat payment policy from SSOT.

    Args:
        insurers_filter: Optional list of insurer keys to filter

    Returns:
        List of SurgeryRepeatPolicy objects
    """
    # SSOT path (relative to project root)
    # __file__ = .../apps/api/overlays/q8/loader.py
    # parent x5 = project root
    ssot_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "compare_v1" / "q8_surgery_repeat_policy_v1.jsonl"

    if not ssot_path.exists():
        raise FileNotFoundError(f"Q8 SSOT not found: {ssot_path}")

    policies = []

    with open(ssot_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            data = json.loads(line)
            insurer_key = data.get('insurer_key', '')

            # Apply filter if specified
            if insurers_filter and insurer_key not in insurers_filter:
                continue

            policy = SurgeryRepeatPolicy(
                insurer_key=insurer_key,
                repeat_payment_policy=data.get('repeat_payment_policy', 'UNKNOWN'),
                display_text=data.get('display_text', '확인 불가 (근거 없음)'),
                evidence_refs=data.get('evidence_refs', [])
            )

            policies.append(policy)

    return policies
