#!/usr/bin/env python3
"""
Amount Read API Handler
STEP NEXT-11: Amount API Integration & Presentation Lock

PURPOSE:
    Read-only API handler for amount_fact table queries

IMMUTABLE RULES:
1. READ-ONLY: No writes to amount_fact
2. NO inference, NO calculation, NO recommendations
3. Status-based presentation (CONFIRMED | UNCONFIRMED | NOT_AVAILABLE)
4. Audit lineage tracking (audit_run_id + freeze_tag)
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import psycopg2
import psycopg2.extras

from apps.api.dto import (
    AmountDTO,
    AmountEvidenceDTO,
    AmountAuditDTO,
    CoverageWithAmountDTO,
    AmountQueryRequest,
    AmountQueryResponseDTO,
    validate_amount_dto
)

logger = logging.getLogger(__name__)


# ============================================================================
# Amount Repository (Read-Only)
# ============================================================================

class AmountRepository:
    """
    Read-only repository for amount_fact table

    CRITICAL: This class ONLY reads from DB, NEVER writes
    """

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def get_amount_by_code(
        self,
        insurer_key: str,
        coverage_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get amount for coverage by canonical code

        Args:
            insurer_key: Insurer key (e.g., "samsung")
            coverage_code: Canonical coverage code (e.g., "A1300")

        Returns:
            {
                "status": "CONFIRMED",
                "value_text": "1천만원",
                "source_doc_type": "가입설계서",
                "evidence_id": uuid,
                "instance_id": uuid
            }
            or None
        """
        # Get insurer_id
        insurer_kr = self._get_insurer_kr(insurer_key)
        if not insurer_kr:
            return None

        self.cursor.execute(
            """
            SELECT
                af.status,
                af.value_text,
                af.source_doc_type,
                af.source_priority,
                af.evidence_id,
                ci.instance_id,
                ci.coverage_name_raw
            FROM amount_fact af
            JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
            JOIN insurer i ON ci.insurer_id = i.insurer_id
            WHERE i.insurer_name_kr = %s
              AND ci.coverage_code = %s
            LIMIT 1
            """,
            (insurer_kr, coverage_code)
        )
        result = self.cursor.fetchone()

        if not result:
            # Check if coverage exists but no amount_fact
            if self._coverage_exists(insurer_kr, coverage_code):
                # Coverage exists but amount not recorded → UNCONFIRMED
                return {
                    "status": "UNCONFIRMED",
                    "value_text": None,
                    "source_doc_type": None,
                    "evidence_id": None,
                    "instance_id": None
                }
            else:
                # Coverage itself doesn't exist → NOT_AVAILABLE
                return {
                    "status": "NOT_AVAILABLE",
                    "value_text": None,
                    "source_doc_type": None,
                    "evidence_id": None,
                    "instance_id": None
                }

        return {
            "status": result['status'],
            "value_text": result['value_text'],
            "source_doc_type": result['source_doc_type'],
            "source_priority": result.get('source_priority'),
            "evidence_id": result['evidence_id'],
            "instance_id": result['instance_id']
        }

    def get_amount_by_raw_name(
        self,
        insurer_key: str,
        coverage_name_raw: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get amount for coverage by raw name (from proposal)

        Args:
            insurer_key: Insurer key (e.g., "samsung")
            coverage_name_raw: Raw coverage name from proposal

        Returns:
            Same as get_amount_by_code
        """
        insurer_kr = self._get_insurer_kr(insurer_key)
        if not insurer_kr:
            return None

        self.cursor.execute(
            """
            SELECT
                af.status,
                af.value_text,
                af.source_doc_type,
                af.source_priority,
                af.evidence_id,
                ci.instance_id,
                ci.coverage_code
            FROM amount_fact af
            JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
            JOIN insurer i ON ci.insurer_id = i.insurer_id
            WHERE i.insurer_name_kr = %s
              AND ci.coverage_name_raw = %s
            LIMIT 1
            """,
            (insurer_kr, coverage_name_raw)
        )
        result = self.cursor.fetchone()

        if not result:
            return {
                "status": "NOT_AVAILABLE",
                "value_text": None,
                "source_doc_type": None,
                "evidence_id": None,
                "instance_id": None
            }

        return {
            "status": result['status'],
            "value_text": result['value_text'],
            "source_doc_type": result['source_doc_type'],
            "source_priority": result.get('source_priority'),
            "evidence_id": result['evidence_id'],
            "instance_id": result['instance_id'],
            "coverage_code": result.get('coverage_code')
        }

    def get_evidence(
        self,
        instance_id: Optional[str],
        max_rank: int = 3
    ) -> Optional[AmountEvidenceDTO]:
        """
        Get evidence snippet for amount

        Args:
            instance_id: Coverage instance UUID
            max_rank: Max rank to search (default 3)

        Returns:
            AmountEvidenceDTO or None
        """
        if not instance_id:
            return AmountEvidenceDTO(status="not_found")

        for rank in range(1, max_rank + 1):
            self.cursor.execute(
                """
                SELECT er.snippet, er.doc_type, er.page
                FROM evidence_ref er
                WHERE er.coverage_instance_id = %s AND er.rank = %s
                LIMIT 1
                """,
                (instance_id, rank)
            )
            result = self.cursor.fetchone()

            if not result:
                continue

            snippet = result['snippet']
            if not snippet or len(snippet.strip()) < 10:
                continue

            # Normalize snippet
            import re
            normalized_snippet = re.sub(r'\s+', ' ', snippet.strip())[:400]

            return AmountEvidenceDTO(
                status="found",
                source=f"{result['doc_type']} p.{result['page']}",
                snippet=normalized_snippet
            )

        return AmountEvidenceDTO(status="not_found")

    def get_latest_audit_metadata(self) -> Optional[AmountAuditDTO]:
        """
        Get latest audit run metadata from audit_runs table

        Returns:
            AmountAuditDTO with audit_run_id, freeze_tag, git_commit
        """
        self.cursor.execute(
            """
            SELECT
                audit_run_id,
                freeze_tag,
                git_commit
            FROM audit_runs
            WHERE audit_name = 'step7_amount_gt_audit'
              AND audit_status = 'PASS'
            ORDER BY generated_at DESC
            LIMIT 1
            """
        )
        result = self.cursor.fetchone()

        if not result:
            return None

        return AmountAuditDTO(
            audit_run_id=result['audit_run_id'],
            freeze_tag=result['freeze_tag'],
            git_commit=result['git_commit']
        )

    def _coverage_exists(self, insurer_kr: str, coverage_code: str) -> bool:
        """Check if coverage_instance exists"""
        self.cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM coverage_instance ci
            JOIN insurer i ON ci.insurer_id = i.insurer_id
            WHERE i.insurer_name_kr = %s AND ci.coverage_code = %s
            """,
            (insurer_kr, coverage_code)
        )
        result = self.cursor.fetchone()
        return result['count'] > 0

    def _get_insurer_kr(self, insurer_key: str) -> Optional[str]:
        """Convert insurer key to Korean name"""
        insurer_map = {
            'samsung': '삼성화재',
            'hanwha': '한화생명',
            'meritz': '메리츠화재',
            'db': 'DB손해보험',
            'kb': 'KB손해보험',
            'lotte': '롯데손해보험',
            'hyundai': '현대해상',
            'heungkuk': '흥국생명'
        }
        return insurer_map.get(insurer_key.lower())


# ============================================================================
# Amount Query Handler
# ============================================================================

class AmountQueryHandler:
    """
    Handler for amount query API

    READ-ONLY: This handler ONLY reads from amount_fact table
    """

    def __init__(self, conn):
        self.conn = conn
        self.repo = AmountRepository(conn)

    def handle_query(
        self,
        request: AmountQueryRequest
    ) -> AmountQueryResponseDTO:
        """
        Handle amount query request

        Args:
            request: AmountQueryRequest

        Returns:
            AmountQueryResponseDTO with amount data + audit metadata
        """
        # Get amount data
        if request.coverage_code:
            amount_data = self.repo.get_amount_by_code(
                request.insurer,
                request.coverage_code
            )
        elif request.coverage_name_raw:
            amount_data = self.repo.get_amount_by_raw_name(
                request.insurer,
                request.coverage_name_raw
            )
        else:
            raise ValueError("Either coverage_code or coverage_name_raw required")

        if not amount_data:
            amount_data = {
                "status": "NOT_AVAILABLE",
                "value_text": None,
                "source_doc_type": None,
                "evidence_id": None,
                "instance_id": None
            }

        # Build AmountDTO
        amount_dto = self._build_amount_dto(
            amount_data,
            include_evidence=request.include_evidence
        )

        # Validate DTO
        validate_amount_dto(amount_dto)

        # Get coverage canonical name
        coverage_code = amount_data.get('coverage_code') or request.coverage_code
        coverage_name = self._get_canonical_name(coverage_code) if coverage_code else "확인 불가"

        # Get audit metadata
        audit_dto = None
        if request.include_audit:
            audit_dto = self.repo.get_latest_audit_metadata()

        # Build response
        return AmountQueryResponseDTO(
            query_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            coverage=CoverageWithAmountDTO(
                coverage_code=coverage_code or "",
                coverage_name=coverage_name,
                amount=amount_dto,
                audit=audit_dto
            ),
            audit=audit_dto
        )

    def _build_amount_dto(
        self,
        amount_data: Dict[str, Any],
        include_evidence: bool = True
    ) -> AmountDTO:
        """Build AmountDTO from DB data"""
        status = amount_data.get('status', 'NOT_AVAILABLE')
        value_text = amount_data.get('value_text')
        source_doc_type = amount_data.get('source_doc_type')
        source_priority = amount_data.get('source_priority')
        instance_id = amount_data.get('instance_id')

        # Get evidence if requested
        evidence = None
        if include_evidence and instance_id:
            evidence = self.repo.get_evidence(instance_id)

        return AmountDTO(
            status=status,
            value_text=value_text,
            source_doc_type=source_doc_type,
            source_priority=source_priority,
            evidence=evidence,
            notes=[]
        )

    def _get_canonical_name(self, coverage_code: str) -> str:
        """Get canonical name for coverage code"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT coverage_name_canonical FROM coverage_canonical WHERE coverage_code = %s",
            (coverage_code,)
        )
        result = cursor.fetchone()
        return result['coverage_name_canonical'] if result else "확인 불가"
