"""
STEP NEXT-73R: Store Loader (In-Memory Cache)

data/detail/*_proposal_detail_store.jsonl
data/detail/*_evidence_store.jsonl

메모리 캐싱 구조:
- proposal_detail_ref -> record
- evidence_ref -> record
"""

import json
from pathlib import Path
from typing import Dict, Optional

# Global cache
_proposal_detail_cache: Dict[str, dict] = {}
_evidence_cache: Dict[str, dict] = {}


def init_store_cache(base_dir: Optional[Path] = None) -> None:
    """
    Store JSONL을 메모리에 로딩

    Args:
        base_dir: 프로젝트 루트 (None이면 auto-detect)
    """
    global _proposal_detail_cache, _evidence_cache

    if base_dir is None:
        # Auto-detect project root
        base_dir = Path(__file__).parent.parent.parent

    detail_dir = base_dir / "data" / "detail"

    if not detail_dir.exists():
        print(f"[WARN] Store detail directory not found: {detail_dir}")
        return

    # Load all proposal_detail_store.jsonl files
    proposal_files = list(detail_dir.glob("*_proposal_detail_store.jsonl"))
    print(f"[DEBUG] Loading proposal detail stores from: {detail_dir.absolute()}")
    for file_path in proposal_files:
        print(f"[DEBUG]   - {file_path.absolute()}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                ref = record.get('proposal_detail_ref')
                if ref:
                    _proposal_detail_cache[ref] = record

    # Load all evidence_store.jsonl files
    evidence_files = list(detail_dir.glob("*_evidence_store.jsonl"))
    print(f"[DEBUG] Loading evidence stores from: {detail_dir.absolute()}")
    for file_path in evidence_files:
        print(f"[DEBUG]   - {file_path.absolute()}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                ref = record.get('evidence_ref')
                if ref:
                    _evidence_cache[ref] = record

    print(f"[STEP NEXT-73R] Store cache initialized:")
    print(f"  - Proposal details: {len(_proposal_detail_cache)} records")
    print(f"  - Evidence: {len(_evidence_cache)} records")


def get_proposal_detail(ref: str) -> Optional[dict]:
    """
    Proposal detail ref로 조회

    Args:
        ref: proposal_detail_ref (예: PD:samsung:A4200_1)

    Returns:
        dict or None
    """
    return _proposal_detail_cache.get(ref)


def get_evidence(ref: str) -> Optional[dict]:
    """
    Evidence ref로 조회

    Args:
        ref: evidence_ref (예: EV:samsung:A4200_1:01)

    Returns:
        dict or None
    """
    return _evidence_cache.get(ref)


def batch_get_evidence(refs: list[str]) -> dict[str, dict]:
    """
    Evidence refs 배치 조회

    Args:
        refs: evidence_ref 목록

    Returns:
        {ref: record} (존재하는 것만)
    """
    result = {}
    for ref in refs:
        record = _evidence_cache.get(ref)
        if record:
            result[ref] = record
    return result


def get_cache_stats() -> dict:
    """캐시 통계"""
    return {
        'proposal_detail_count': len(_proposal_detail_cache),
        'evidence_count': len(_evidence_cache)
    }
