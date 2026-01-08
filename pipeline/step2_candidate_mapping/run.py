#!/usr/bin/env python3
"""
STEP NEXT-57: Step2-c Candidate Mapping Runner

Generates candidate coverage_code suggestions for unmapped items.

Usage:
    python -m pipeline.step2_candidate_mapping.run --insurer kb
    python -m pipeline.step2_candidate_mapping.run  # Process all insurers

Constitutional enforcement:
- Candidates do NOT change Step2-b mapping results
- This is a separate report (Step2-c output)
- NO LLM usage
"""

import argparse
import logging
from pathlib import Path
import sys

from pipeline.step2_candidate_mapping.candidate_mapper import generate_candidate_report


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# SSOT paths (STEP NEXT-52-HK enforced)
SCOPE_V3_DIR = Path(__file__).parent.parent.parent / 'data' / 'scope_v3'
MAPPING_EXCEL_PATH = Path(__file__).parent.parent.parent / 'data' / 'sources' / 'mapping' / '담보명mapping자료.xlsx'


# Known insurers (from INSURER_CODE_MAP)
KNOWN_INSURERS = [
    'meritz', 'hanwha', 'lotte_female', 'lotte_male',
    'heungkuk', 'samsung', 'hyundai', 'kb',
    'db_over41', 'db_under40'
]


def run_candidate_mapping(insurer: str, min_confidence: float = 0.5):
    """
    Run candidate mapping for single insurer.

    Args:
        insurer: Insurer name
        min_confidence: Minimum confidence threshold
    """
    logger.info(f"Running candidate mapping for: {insurer}")

    # Input: Step2-b mapping report
    mapping_report_path = SCOPE_V3_DIR / f'{insurer}_step2_mapping_report.jsonl'
    if not mapping_report_path.exists():
        logger.warning(f"Mapping report not found: {mapping_report_path}")
        return

    # Output: Step2-c candidate report
    candidate_report_path = SCOPE_V3_DIR / f'{insurer}_step2_candidate_report_v1.jsonl'

    # Generate candidates
    stats = generate_candidate_report(
        mapping_report_jsonl=mapping_report_path,
        output_jsonl=candidate_report_path,
        mapping_excel_path=MAPPING_EXCEL_PATH,
        min_confidence=min_confidence
    )

    if 'error' in stats:
        logger.error(f"{insurer}: {stats['error']}")
        return

    logger.info(f"{insurer}: {stats['candidate_generated']}/{stats['total_unmapped']} "
                f"candidates generated ({stats['candidate_rate']:.1%})")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='STEP NEXT-57: Generate candidate mappings for unmapped coverages'
    )
    parser.add_argument(
        '--insurer',
        type=str,
        help='Specific insurer to process (default: all)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.5,
        help='Minimum confidence threshold (0-1, default: 0.5)'
    )

    args = parser.parse_args()

    # SSOT enforcement (STEP NEXT-52-HK)
    if not SCOPE_V3_DIR.exists():
        logger.error(f"SSOT path not found: {SCOPE_V3_DIR}")
        sys.exit(2)

    if not MAPPING_EXCEL_PATH.exists():
        logger.error(f"Mapping Excel not found: {MAPPING_EXCEL_PATH}")
        sys.exit(2)

    logger.info("="*70)
    logger.info("STEP 2-c CANDIDATE MAPPING (LEVEL 1 - Deterministic)")
    logger.info("="*70)

    # Process insurers
    if args.insurer:
        insurers = [args.insurer]
    else:
        # Process all known insurers
        insurers = KNOWN_INSURERS

    total_stats = {
        'processed': 0,
        'total_unmapped': 0,
        'total_candidates': 0
    }

    for insurer in insurers:
        stats = run_candidate_mapping(insurer, min_confidence=args.min_confidence)
        if stats:
            total_stats['processed'] += 1
            total_stats['total_unmapped'] += stats['total_unmapped']
            total_stats['total_candidates'] += stats['candidate_generated']

    logger.info("="*70)
    logger.info("STEP 2-c CANDIDATE MAPPING SUMMARY")
    logger.info("="*70)
    logger.info(f"Processed: {total_stats['processed']} insurer(s)")
    logger.info(f"Total unmapped: {total_stats['total_unmapped']}")
    logger.info(f"Total candidates: {total_stats['total_candidates']} "
                f"({total_stats['total_candidates']/total_stats['total_unmapped']*100 if total_stats['total_unmapped'] else 0:.1f}%)")
    logger.info("")
    logger.info("✅ Candidate reports: data/scope_v3/*_step2_candidate_report_v1.jsonl")
    logger.info("🔒 SSOT path: " + str(SCOPE_V3_DIR))
    logger.info("⚠️  Candidates are suggestions only (NOT confirmed mappings)")
    logger.info("")


if __name__ == '__main__':
    main()
