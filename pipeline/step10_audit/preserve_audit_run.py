#!/usr/bin/env python3
"""
Preserve Audit Run Metadata
============================

Purpose:
    Store Step7 amount audit run metadata in DB for compliance + lineage.
    Links git commit, freeze tag, and audit reports for永久 reference.

Usage:
    python -m pipeline.step10_audit.preserve_audit_run \
        --db-url "postgresql://..." \
        --audit-name "step7_amount_gt_audit" \
        --report-json "reports/step7_gt_audit_all_20251229-025007.json" \
        --report-md "reports/step7_gt_audit_all_20251229-025007.md" \
        --git-commit "c6fad903c4782c9b78c44563f0f47bf13f9f3417" \
        --freeze-tag "freeze/pre-10b2g2-20251229-024400"
"""

import argparse
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_git_commit() -> str:
    """Get current git commit hash"""
    result = subprocess.run(
        ['git', 'log', '-1', '--format=%H'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def get_latest_freeze_tag() -> str:
    """Get latest freeze tag matching 'freeze/pre-10b2g2-*'"""
    result = subprocess.run(
        ['git', 'tag', '--list', 'freeze/pre-10b2g2-*', '--sort=-version:refname'],
        capture_output=True,
        text=True,
        check=True
    )
    tags = result.stdout.strip().split('\n')
    return tags[0] if tags and tags[0] else None


def parse_audit_report(json_path: Path) -> dict:
    """
    Parse audit report JSON to extract summary stats.

    Expected structure (array of insurer results):
    [
      {
        "insurer": "samsung",
        "gt_pairs": 59,
        "verdict_counts": { "OK_MATCH": 33, ... }
      },
      ...
    ]
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Audit report is an array of insurer results
    if not isinstance(data, list):
        raise ValueError("Unexpected audit format (expected array)")

    insurers = [item.get('insurer') for item in data if 'insurer' in item]
    total_rows = sum(item.get('gt_pairs', 0) for item in data)

    # Check for MISMATCH_VALUE errors across all insurers
    mismatch_value = 0
    mismatch_type = 0

    for item in data:
        verdict_counts = item.get('verdict_counts', {})
        if 'MISMATCH_VALUE' in verdict_counts:
            mismatch_value += verdict_counts['MISMATCH_VALUE']
        if 'MISMATCH_TYPE' in verdict_counts:
            mismatch_type += verdict_counts['MISMATCH_TYPE']

    return {
        'total_rows_audited': total_rows,
        'mismatch_value_count': mismatch_value,
        'mismatch_type_count': mismatch_type,
        'insurers': insurers,
        'audit_status': 'PASS' if (mismatch_value == 0 and mismatch_type == 0) else 'FAIL'
    }


def preserve_audit_run(
    db_url: str,
    audit_name: str,
    report_json_path: str,
    report_md_path: str,
    git_commit: str = None,
    freeze_tag: str = None
):
    """
    Preserve audit run metadata in DB.

    Args:
        db_url: PostgreSQL connection URL
        audit_name: Audit name (e.g., 'step7_amount_gt_audit')
        report_json_path: Path to audit report JSON
        report_md_path: Path to audit report markdown
        git_commit: Git commit hash (auto-detected if None)
        freeze_tag: Git freeze tag (auto-detected if None)
    """
    logger.info("=== Preserving Audit Run Metadata ===")

    # Auto-detect git metadata
    if git_commit is None:
        git_commit = get_git_commit()
        logger.info(f"Auto-detected git commit: {git_commit}")

    if freeze_tag is None:
        freeze_tag = get_latest_freeze_tag()
        logger.info(f"Auto-detected freeze tag: {freeze_tag}")

    # Parse audit report
    json_path = Path(report_json_path)
    md_path = Path(report_md_path)

    if not json_path.exists():
        raise FileNotFoundError(f"Audit report JSON not found: {json_path}")
    if not md_path.exists():
        raise FileNotFoundError(f"Audit report MD not found: {md_path}")

    audit_stats = parse_audit_report(json_path)

    logger.info(f"Audit stats: {audit_stats}")

    # Insert into DB
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute("""
            INSERT INTO audit_runs (
                audit_name,
                git_commit,
                freeze_tag,
                report_json_path,
                report_md_path,
                total_insurers,
                total_rows_audited,
                mismatch_value_count,
                mismatch_type_count,
                audit_status,
                insurers,
                generated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (git_commit, audit_name) DO UPDATE SET
                freeze_tag = EXCLUDED.freeze_tag,
                report_json_path = EXCLUDED.report_json_path,
                report_md_path = EXCLUDED.report_md_path,
                total_rows_audited = EXCLUDED.total_rows_audited,
                mismatch_value_count = EXCLUDED.mismatch_value_count,
                mismatch_type_count = EXCLUDED.mismatch_type_count,
                audit_status = EXCLUDED.audit_status,
                insurers = EXCLUDED.insurers,
                created_at = CURRENT_TIMESTAMP
            RETURNING audit_run_id
        """, (
            audit_name,
            git_commit,
            freeze_tag,
            str(json_path),
            str(md_path),
            len(audit_stats['insurers']),
            audit_stats['total_rows_audited'],
            audit_stats['mismatch_value_count'],
            audit_stats['mismatch_type_count'],
            audit_stats['audit_status'],
            audit_stats['insurers'],
            datetime.now()
        ))

        result = cursor.fetchone()
        audit_run_id = result['audit_run_id']

        conn.commit()

        logger.info(f"✅ Audit run preserved: {audit_run_id}")
        logger.info(f"   Audit: {audit_name}")
        logger.info(f"   Commit: {git_commit}")
        logger.info(f"   Tag: {freeze_tag}")
        logger.info(f"   Status: {audit_stats['audit_status']}")
        logger.info(f"   Insurers: {', '.join(audit_stats['insurers'])}")

    except Exception as e:
        logger.error(f"Error preserving audit run: {e}", exc_info=True)
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Preserve audit run metadata in DB')
    parser.add_argument(
        '--db-url',
        default='postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope',
        help='PostgreSQL connection URL'
    )
    parser.add_argument(
        '--audit-name',
        default='step7_amount_gt_audit',
        help='Audit name'
    )
    parser.add_argument(
        '--report-json',
        required=True,
        help='Path to audit report JSON'
    )
    parser.add_argument(
        '--report-md',
        required=True,
        help='Path to audit report markdown'
    )
    parser.add_argument(
        '--git-commit',
        help='Git commit hash (auto-detected if not provided)'
    )
    parser.add_argument(
        '--freeze-tag',
        help='Git freeze tag (auto-detected if not provided)'
    )

    args = parser.parse_args()

    preserve_audit_run(
        db_url=args.db_url,
        audit_name=args.audit_name,
        report_json_path=args.report_json,
        report_md_path=args.report_md,
        git_commit=args.git_commit,
        freeze_tag=args.freeze_tag
    )


if __name__ == '__main__':
    main()
