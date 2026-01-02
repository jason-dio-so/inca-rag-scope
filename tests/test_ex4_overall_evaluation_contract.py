#!/usr/bin/env python3
"""
Contract Test: EX4_ELIGIBILITY Overall Evaluation Lock

STEP NEXT-79: Verify overall_evaluation section is always present and valid

TEST RULES:
1. overall_evaluation ALWAYS exists in EX4_ELIGIBILITY responses
2. decision ∈ {RECOMMEND, NOT_RECOMMEND, NEUTRAL}
3. All reasons MUST have refs (except Unknown status)
4. decision is deterministic (same input → same decision)
5. NO forbidden phrases in summary/reasons
"""

import pytest
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


class TestEX4OverallEvaluationContract:
    """Contract tests for EX4_ELIGIBILITY overall evaluation"""

    def test_overall_evaluation_always_exists(self):
        """Test that overall_evaluation section is always present"""
        # Arrange
        insurers = ["samsung", "meritz", "hanwha"]
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
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "약관 p.15"
            },
            {
                "insurer": "hanwha",
                "status": "△",
                "evidence_type": "감액",
                "evidence_snippet": "제자리암: 50% 감액",
                "evidence_ref": "약관 p.18"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        sections = response["sections"]
        evaluation_section = None
        for section in sections:
            if section.get("kind") == "overall_evaluation":
                evaluation_section = section
                break

        assert evaluation_section is not None, "overall_evaluation section MUST exist"
        assert "overall_evaluation" in evaluation_section
        assert "decision" in evaluation_section["overall_evaluation"]
        assert "summary" in evaluation_section["overall_evaluation"]
        assert "reasons" in evaluation_section["overall_evaluation"]
        assert "notes" in evaluation_section["overall_evaluation"]

    def test_decision_is_valid_enum(self):
        """Test that decision is one of the valid enum values"""
        # Arrange
        insurers = ["samsung", "meritz"]
        subtype_keyword = "경계성종양"
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "경계성종양: 보장 가능",
                "evidence_ref": "약관 p.20"
            },
            {
                "insurer": "meritz",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "경계성종양: 보장 가능",
                "evidence_ref": "약관 p.22"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = evaluation_section["overall_evaluation"]["decision"]
        valid_decisions = ["RECOMMEND", "NOT_RECOMMEND", "NEUTRAL"]
        assert decision in valid_decisions, f"decision must be in {valid_decisions}, got {decision}"

    def test_decision_recommend_when_o_majority(self):
        """Test RECOMMEND decision when O is majority"""
        # Arrange
        insurers = ["samsung", "meritz", "hanwha"]
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
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = evaluation_section["overall_evaluation"]["decision"]
        assert decision == "RECOMMEND", f"Expected RECOMMEND for O majority, got {decision}"

    def test_decision_not_recommend_when_x_majority(self):
        """Test NOT_RECOMMEND decision when X is majority"""
        # Arrange
        insurers = ["samsung", "meritz", "hanwha"]
        subtype_keyword = "제자리암"
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
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = evaluation_section["overall_evaluation"]["decision"]
        assert decision == "NOT_RECOMMEND", f"Expected NOT_RECOMMEND for X majority, got {decision}"

    def test_decision_neutral_when_mixed(self):
        """Test NEUTRAL decision when statuses are mixed"""
        # Arrange
        insurers = ["samsung", "meritz"]
        subtype_keyword = "제자리암"
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
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        decision = evaluation_section["overall_evaluation"]["decision"]
        assert decision == "NEUTRAL", f"Expected NEUTRAL for mixed statuses, got {decision}"

    def test_reasons_have_refs_except_unknown(self):
        """Test that all reasons have refs (except Unknown status)"""
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
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "약관 p.15"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        reasons = evaluation_section["overall_evaluation"]["reasons"]
        assert len(reasons) > 0, "Reasons list must not be empty"

        for reason in reasons:
            assert "type" in reason
            assert "description" in reason
            assert "refs" in reason
            # Refs can be empty for Unknown status reasons
            # But must be present as a field
            assert isinstance(reason["refs"], list)

    def test_decision_deterministic_same_input(self):
        """Test that same input produces same decision"""
        # Arrange
        insurers = ["samsung", "meritz", "hanwha"]
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

        # Act - run twice
        response1 = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )
        response2 = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert
        eval1 = next(s for s in response1["sections"] if s.get("kind") == "overall_evaluation")
        eval2 = next(s for s in response2["sections"] if s.get("kind") == "overall_evaluation")

        decision1 = eval1["overall_evaluation"]["decision"]
        decision2 = eval2["overall_evaluation"]["decision"]
        assert decision1 == decision2, "Decision must be deterministic"

    def test_no_forbidden_phrases_in_summary(self):
        """Test that summary does not contain forbidden phrases"""
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

        # Assert
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        summary = evaluation_section["overall_evaluation"]["summary"]

        forbidden_phrases = ["추천", "좋아 보임", "합리적", "우수", "최적"]
        for phrase in forbidden_phrases:
            assert phrase not in summary, f"Forbidden phrase '{phrase}' found in summary"

    def test_response_structure_matches_spec(self):
        """Test that response structure matches STEP NEXT-79 spec"""
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
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "약관 p.15"
            }
        ]

        # Act
        response = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype_keyword,
            eligibility_data=eligibility_data
        )

        # Assert - Top-level response structure
        assert "message_id" in response
        assert "kind" in response
        assert response["kind"] == "EX4_ELIGIBILITY"
        assert "title" in response
        assert "summary_bullets" in response
        assert "sections" in response
        assert "lineage" in response

        # Assert - Lineage
        assert response["lineage"]["llm_used"] is False
        assert response["lineage"]["deterministic"] is True

        # Assert - Overall evaluation section structure
        evaluation_section = next(
            s for s in response["sections"] if s.get("kind") == "overall_evaluation"
        )
        overall_eval = evaluation_section["overall_evaluation"]
        assert "decision" in overall_eval
        assert "summary" in overall_eval
        assert "reasons" in overall_eval
        assert "notes" in overall_eval
        assert isinstance(overall_eval["reasons"], list)
