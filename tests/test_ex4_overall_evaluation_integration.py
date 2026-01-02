#!/usr/bin/env python3
"""
Integration Test: EX4_ELIGIBILITY Overall Evaluation End-to-End

STEP NEXT-79-FE: Verify overall evaluation flows from composer → handler → API

TEST SCENARIOS:
1. EX4 response always contains overall_evaluation section
2. Decision logic (RECOMMEND/NOT_RECOMMEND/NEUTRAL) works correctly
3. Response structure is compatible with frontend types
4. Other intents (EX2/EX3) do not have overall_evaluation
"""

import pytest
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer
from apps.api.chat_handlers_deterministic import Example4HandlerDeterministic
from apps.api.chat_vm import ChatRequest


class TestEX4OverallEvaluationIntegration:
    """Integration tests for EX4 overall evaluation"""

    def test_ex4_response_has_overall_evaluation_section(self):
        """Test that EX4 response always contains overall_evaluation section"""
        # Arrange
        handler = Example4HandlerDeterministic()
        compiled_query = {
            "insurers": ["samsung", "meritz", "hanwha"],
            "disease_name": "제자리암"
        }
        request = ChatRequest(message="제자리암 보장 가능한가요?")

        # Act
        vm = handler.execute(compiled_query, request)

        # Assert
        assert vm.kind == "EX4_ELIGIBILITY"
        assert vm.sections is not None

        # Find overall_evaluation section
        overall_eval_section = None
        for section in vm.sections:
            # Check if section is OverallEvaluationSection (Pydantic model)
            if hasattr(section, 'kind') and section.kind == "overall_evaluation":
                overall_eval_section = section
                break

        assert overall_eval_section is not None, "overall_evaluation section must exist"
        assert hasattr(overall_eval_section, "overall_evaluation")

    def test_ex4_decision_structure_matches_frontend_types(self):
        """Test that decision structure matches frontend TypeScript types"""
        # Arrange
        insurers = ["samsung", "meritz"]
        subtype_keyword = "제자리암"
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.12"
            },
            {
                "insurer": "meritz",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.15"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert - Check structure matches TypeScript OverallEvaluationSection
        sections = response["sections"]
        overall_eval_section = next(
            s for s in sections if s.get("kind") == "overall_evaluation"
        )

        # Check required fields (matching types.ts)
        assert "kind" in overall_eval_section
        assert overall_eval_section["kind"] == "overall_evaluation"
        assert "title" in overall_eval_section
        assert "overall_evaluation" in overall_eval_section

        overall_eval = overall_eval_section["overall_evaluation"]
        assert "decision" in overall_eval
        assert "summary" in overall_eval
        assert "reasons" in overall_eval
        assert "notes" in overall_eval

        # Check reasons structure
        assert isinstance(overall_eval["reasons"], list)
        if len(overall_eval["reasons"]) > 0:
            reason = overall_eval["reasons"][0]
            assert "type" in reason
            assert "description" in reason
            assert "refs" in reason
            assert isinstance(reason["refs"], list)

    def test_ex4_recommend_scenario(self):
        """Test RECOMMEND decision scenario"""
        # Arrange - O majority
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.12"
            },
            {
                "insurer": "meritz",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.15"
            },
            {
                "insurer": "hanwha",
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "약관 p.18"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz", "hanwha"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        # Assert
        overall_eval_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = overall_eval_section["overall_evaluation"]["decision"]
        assert decision == "RECOMMEND"

    def test_ex4_not_recommend_scenario(self):
        """Test NOT_RECOMMEND decision scenario"""
        # Arrange - X majority
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "약관 p.12"
            },
            {
                "insurer": "meritz",
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "약관 p.15"
            },
            {
                "insurer": "hanwha",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.18"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz", "hanwha"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        # Assert
        overall_eval_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = overall_eval_section["overall_evaluation"]["decision"]
        assert decision == "NOT_RECOMMEND"

    def test_ex4_neutral_scenario(self):
        """Test NEUTRAL decision scenario"""
        # Arrange - Mixed statuses
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "△",
                "evidence_type": "감액",
                "evidence_snippet": "제자리암: 50% 감액",
                "evidence_ref": "약관 p.12"
            },
            {
                "insurer": "meritz",
                "status": "Unknown",
                "evidence_type": None,
                "evidence_snippet": None,
                "evidence_ref": None
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        # Assert
        overall_eval_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = overall_eval_section["overall_evaluation"]["decision"]
        assert decision == "NEUTRAL"

    def test_ex4_section_order_preserved(self):
        """Test that section order is preserved (matrix → evaluation → notes)"""
        # Arrange
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.12"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=["samsung"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        # Assert - Check section order
        sections = response["sections"]
        assert len(sections) == 3

        # Expected order: matrix → evaluation → notes
        assert sections[0]["kind"] == "comparison_table"
        assert sections[1]["kind"] == "overall_evaluation"
        assert sections[2]["kind"] == "common_notes"

    def test_ex4_no_llm_usage(self):
        """Test that overall evaluation is deterministic (NO LLM)"""
        # Arrange
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장 가능",
                "evidence_ref": "약관 p.12"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=["samsung"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        # Assert - Check lineage
        assert response["lineage"]["llm_used"] is False
        assert response["lineage"]["deterministic"] is True
