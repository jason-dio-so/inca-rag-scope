#!/usr/bin/env python3
"""
Integration Tests for Amount API
STEP NEXT-11: Amount API Integration & Presentation Lock

Tests:
1. Amount repository read operations
2. Amount query handler
3. Status-based responses
4. Audit lineage tracking
5. Presentation rules compliance
"""

import pytest
import uuid
from datetime import datetime
from apps.api.dto import (
    AmountDTO,
    AmountEvidenceDTO,
    AmountAuditDTO,
    AmountQueryRequest,
    AmountPresentationRules,
    validate_amount_dto
)


# ============================================================================
# DTO Validation Tests
# ============================================================================

class TestAmountDTOValidation:
    """Test AmountDTO validation rules"""

    def test_confirmed_requires_value_text(self):
        """CONFIRMED status must have value_text"""
        # Valid CONFIRMED
        amount = AmountDTO(
            status="CONFIRMED",
            value_text="1천만원",
            evidence=AmountEvidenceDTO(status="found", source="가입설계서 p.4", snippet="...")
        )
        validate_amount_dto(amount)  # Should not raise

        # Invalid CONFIRMED (no value_text)
        with pytest.raises(ValueError, match="CONFIRMED status requires value_text"):
            invalid = AmountDTO(
                status="CONFIRMED",
                value_text=None
            )
            validate_amount_dto(invalid)

    def test_confirmed_cannot_have_fixed_text(self):
        """CONFIRMED cannot use fixed status text"""
        forbidden_texts = ["확인 불가", "해당 담보 없음"]

        for text in forbidden_texts:
            with pytest.raises(ValueError, match="cannot have fixed text"):
                invalid = AmountDTO(
                    status="CONFIRMED",
                    value_text=text
                )
                validate_amount_dto(invalid)

    def test_unconfirmed_no_value_text(self):
        """UNCONFIRMED should not have actual value_text"""
        # Valid UNCONFIRMED
        amount = AmountDTO(
            status="UNCONFIRMED",
            value_text=None
        )
        validate_amount_dto(amount)  # Should not raise

        # Invalid UNCONFIRMED (has value_text)
        with pytest.raises(ValueError, match="should not have actual value_text"):
            invalid = AmountDTO(
                status="UNCONFIRMED",
                value_text="1천만원"
            )
            validate_amount_dto(invalid)

    def test_not_available_no_value_text(self):
        """NOT_AVAILABLE should not have actual value_text"""
        # Valid NOT_AVAILABLE
        amount = AmountDTO(
            status="NOT_AVAILABLE",
            value_text=None
        )
        validate_amount_dto(amount)  # Should not raise


# ============================================================================
# Presentation Rules Tests
# ============================================================================

class TestAmountPresentationRules:
    """Test presentation rules compliance"""

    def test_confirmed_display_text(self):
        """CONFIRMED shows value_text"""
        display = AmountPresentationRules.get_display_text("CONFIRMED", "3천만원")
        assert display == "3천만원"

    def test_unconfirmed_display_text(self):
        """UNCONFIRMED shows type-aware text (deprecated, use presentation_utils)"""
        display = AmountPresentationRules.get_display_text("UNCONFIRMED")
        assert display == "(Type-aware)"  # Now deprecated, use presentation_utils

    def test_not_available_display_text(self):
        """NOT_AVAILABLE shows fixed text"""
        display = AmountPresentationRules.get_display_text("NOT_AVAILABLE")
        assert display == "해당 담보 없음"

    def test_confirmed_style(self):
        """CONFIRMED has normal style"""
        style = AmountPresentationRules.get_style("CONFIRMED")
        assert style["style"] == "normal"
        assert style["color"] == "inherit"

    def test_unconfirmed_style(self):
        """UNCONFIRMED has muted style"""
        style = AmountPresentationRules.get_style("UNCONFIRMED")
        assert style["style"] == "muted"
        assert style["color"] == "#666666"

    def test_not_available_style(self):
        """NOT_AVAILABLE has disabled style"""
        style = AmountPresentationRules.get_style("NOT_AVAILABLE")
        assert style["style"] == "disabled"
        assert style["color"] == "#999999"


# ============================================================================
# Status Semantics Tests
# ============================================================================

class TestAmountStatusSemantics:
    """Test status field semantics"""

    def test_confirmed_semantics(self):
        """CONFIRMED = amount explicitly stated + evidence exists"""
        amount = AmountDTO(
            status="CONFIRMED",
            value_text="1천만원",
            source_doc_type="가입설계서",
            evidence=AmountEvidenceDTO(
                status="found",
                source="가입설계서 p.4",
                snippet="5. 상해사망\n1천만원"
            )
        )

        # Semantics check
        assert amount.status == "CONFIRMED"
        assert amount.value_text is not None
        assert amount.evidence is not None
        assert amount.evidence.status == "found"

    def test_unconfirmed_semantics(self):
        """UNCONFIRMED = coverage exists but amount not stated"""
        amount = AmountDTO(
            status="UNCONFIRMED",
            value_text=None,
            evidence=None
        )

        # Semantics check
        assert amount.status == "UNCONFIRMED"
        assert amount.value_text is None
        # Note: Coverage exists in DB (coverage_instance), just no amount

    def test_not_available_semantics(self):
        """NOT_AVAILABLE = coverage itself doesn't exist"""
        amount = AmountDTO(
            status="NOT_AVAILABLE",
            value_text=None,
            evidence=None
        )

        # Semantics check
        assert amount.status == "NOT_AVAILABLE"
        assert amount.value_text is None
        # Note: Coverage doesn't exist in DB (no coverage_instance)


# ============================================================================
# Audit Lineage Tests
# ============================================================================

class TestAmountAuditLineage:
    """Test audit metadata tracking"""

    def test_audit_dto_structure(self):
        """Audit DTO has required fields"""
        audit = AmountAuditDTO(
            audit_run_id=uuid.uuid4(),
            freeze_tag="freeze/pre-10b2g2-20251229-024400",
            git_commit="c6fad903c4782c9b78c44563f0f47bf13f9f3417"
        )

        assert audit.audit_run_id is not None
        assert audit.freeze_tag.startswith("freeze/")
        assert len(audit.git_commit) == 40  # Git SHA-1 length

    def test_audit_dto_immutable(self):
        """Audit DTO is frozen (immutable)"""
        audit = AmountAuditDTO(
            audit_run_id=uuid.uuid4(),
            freeze_tag="freeze/test",
            git_commit="abc123"
        )

        # Pydantic frozen=True prevents modification
        with pytest.raises(Exception):  # ValidationError or AttributeError
            audit.freeze_tag = "modified"


# ============================================================================
# Response Schema Tests
# ============================================================================

class TestResponseSchemaCompliance:
    """Test response schema compliance"""

    def test_amount_dto_schema(self):
        """AmountDTO has locked schema"""
        amount = AmountDTO(
            status="CONFIRMED",
            value_text="1천만원",
            source_doc_type="가입설계서",
            source_priority="PRIMARY",
            evidence=AmountEvidenceDTO(status="found", source="p.4", snippet="..."),
            notes=[]
        )

        # Check schema fields
        assert hasattr(amount, 'status')
        assert hasattr(amount, 'value_text')
        assert hasattr(amount, 'source_doc_type')
        assert hasattr(amount, 'source_priority')
        assert hasattr(amount, 'evidence')
        assert hasattr(amount, 'notes')

        # Check types
        assert amount.status in ["CONFIRMED", "UNCONFIRMED", "NOT_AVAILABLE"]
        assert isinstance(amount.notes, list)

    def test_evidence_dto_schema(self):
        """AmountEvidenceDTO has locked schema"""
        evidence = AmountEvidenceDTO(
            status="found",
            source="가입설계서 p.4",
            snippet="5. 상해사망\n1천만원"
        )

        # Check schema fields
        assert hasattr(evidence, 'status')
        assert hasattr(evidence, 'source')
        assert hasattr(evidence, 'snippet')

        # Check types
        assert evidence.status in ["found", "not_found"]
        assert isinstance(evidence.source, str)


# ============================================================================
# Forbidden Operations Tests
# ============================================================================

class TestForbiddenOperations:
    """Test that forbidden operations are prevented"""

    def test_no_amount_calculation(self):
        """Test that numeric calculations are not supported"""
        amounts = [
            AmountDTO(status="CONFIRMED", value_text="1천만원"),
            AmountDTO(status="CONFIRMED", value_text="2천만원"),
            AmountDTO(status="CONFIRMED", value_text="3천만원")
        ]

        # value_text is text only, no numeric field
        for amount in amounts:
            assert not hasattr(amount, 'amount_numeric')
            assert not hasattr(amount, 'amount_float')

    def test_no_status_mutation(self):
        """Test that status cannot be changed after creation"""
        amount = AmountDTO(
            status="UNCONFIRMED",
            value_text=None
        )

        # Pydantic frozen=True prevents modification
        with pytest.raises(Exception):
            amount.status = "CONFIRMED"

    def test_no_comparison_fields(self):
        """Test that comparison fields are not present"""
        amount = AmountDTO(
            status="CONFIRMED",
            value_text="1천만원"
        )

        # Forbidden fields
        assert not hasattr(amount, 'rank')
        assert not hasattr(amount, 'is_best')
        assert not hasattr(amount, 'is_worst')
        assert not hasattr(amount, 'comparison_score')


# ============================================================================
# Integration Test (Mock DB)
# ============================================================================

class TestAmountRepositoryIntegration:
    """Integration tests for AmountRepository (requires DB)"""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires live database")
    def test_get_amount_by_code(self):
        """Test amount retrieval by canonical code"""
        # This would test actual DB queries
        # Skipped for unit test suite
        pass

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires live database")
    def test_get_evidence(self):
        """Test evidence retrieval"""
        # This would test actual evidence_ref queries
        # Skipped for unit test suite
        pass

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires live database")
    def test_get_audit_metadata(self):
        """Test audit metadata retrieval"""
        # This would test audit_runs table query
        # Skipped for unit test suite
        pass


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
