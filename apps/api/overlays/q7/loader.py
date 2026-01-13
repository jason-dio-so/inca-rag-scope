"""
Q7 SSOT Loader - Load waiver policy from JSONL

FROZEN: Read-only loader for q7_waiver_policy_v1.jsonl
"""

import json
from pathlib import Path
from typing import List, Optional

from .model import ContractWaiverPolicy


def load_q7_waiver_policy(
    insurers_filter: Optional[List[str]] = None
) -> List[ContractWaiverPolicy]:
    """
    Load Q7 waiver policy from SSOT.

    Args:
        insurers_filter: Optional list of insurer keys to filter

    Returns:
        List of ContractWaiverPolicy objects
    """
    # SSOT path (relative to project root)
    # __file__ = .../apps/api/overlays/q7/loader.py
    # parent x5 = project root
    ssot_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "compare_v1" / "q7_waiver_policy_v1.jsonl"

    if not ssot_path.exists():
        raise FileNotFoundError(f"Q7 SSOT not found: {ssot_path}")

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

            policy = ContractWaiverPolicy(
                insurer_key=insurer_key,
                waiver_triggers=data.get('waiver_triggers', []),
                has_sanjeong_teukrye=data.get('has_sanjeong_teukrye', 'UNKNOWN'),
                evidence_refs=data.get('evidence_refs', [])
            )

            policies.append(policy)

    return policies
