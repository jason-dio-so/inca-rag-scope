"""
STEP NEXT-63: Test Suite for LLM OFF Examples

Constitutional Rules:
- ZERO LLM calls allowed
- All outputs must be deterministic
- NO forbidden phrases (추천, 유리, etc.)
- All evidence references must exist

Test Coverage:
- Example 1: Premium comparison (Top-4)
- Example 2: Coverage limit comparison
- Example 3: Two-insurer comparison
- Example 4: Subtype eligibility
"""

import pytest
import json
import subprocess
from pathlib import Path
import sys

# Add pipeline directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline" / "step8_render_deterministic"))

from templates import DeterministicTemplates


class TestExample1PremiumCompare:
    """Test Example 1: Premium Comparison"""

    def test_premium_compare_top4(self):
        """Test premium comparison returns Top-4 with evidence refs"""
        from example1_premium_compare import PremiumComparer

        comparer = PremiumComparer()
        insurers = ["samsung", "meritz", "hanwha", "lotte", "kb", "hyundai"]

        result = comparer.compare_top4(insurers)

        assert result["status"] in ["success", "not_available"]

        if result["status"] == "success":
            assert len(result["rows"]) == 4
            for row in result["rows"]:
                assert "insurer" in row
                assert "monthly_premium" in row
                assert "total_premium" in row
                assert "monthly_evidence" in row
                assert "total_evidence" in row

    def test_no_forbidden_phrases(self):
        """Ensure no forbidden phrases in output"""
        from example1_premium_compare import PremiumComparer

        comparer = PremiumComparer()
        result = comparer.compare_top4(["samsung", "meritz", "hanwha", "lotte"])

        result_str = json.dumps(result, ensure_ascii=False)
        assert DeterministicTemplates.validate_no_forbidden_phrases(result_str)


class TestExample2CoverageLimit:
    """Test Example 2: Coverage Limit Comparison"""

    def test_coverage_limit_extraction(self):
        """Test coverage limit extraction with evidence refs"""
        from example2_coverage_limit import CoverageLimitComparer

        comparer = CoverageLimitComparer()
        insurers = ["samsung", "meritz"]
        coverage_code = "A4200_1"  # 암진단비(유사암제외)

        result = comparer.compare_coverage_limits(insurers, coverage_code)

        assert result["coverage_code"] == coverage_code
        assert len(result["rows"]) == len(insurers)

        for row in result["rows"]:
            assert "insurer" in row
            assert "amount" in row
            assert "payment_type" in row
            assert "evidence_refs" in row
            assert isinstance(row["evidence_refs"], list)

    def test_amount_parsing_deterministic(self):
        """Ensure amount parsing is deterministic (no LLM)"""
        from example2_coverage_limit import CoverageLimitComparer

        comparer = CoverageLimitComparer()

        # Mock evidence
        evidences = [
            {"snippet": "암 진단시 3,000만원을 지급합니다", "page": 10, "doc_type": "약관"}
        ]

        amount = comparer.extract_amount(evidences)
        assert amount == "3,000만원"


class TestExample3TwoInsurerCompare:
    """Test Example 3: Two-Insurer Comparison"""

    def test_two_insurer_comparison(self):
        """Test two-insurer comparison with gates"""
        from example3_two_insurer_compare import TwoInsurerComparer

        comparer = TwoInsurerComparer()
        result = comparer.compare_two_insurers("samsung", "meritz", "A4200_1")

        assert "status" in result

        if result["status"] == "success":
            assert "comparison_table" in result
            assert "summary" in result
            assert "gates" in result

            # Gate checks
            assert result["gates"]["join_rate"] == 1.0
            assert result["gates"]["evidence_fill_rate"] >= 0.8

            # Summary must be 3 lines
            assert len(result["summary"]) == 3

    def test_summary_templates_deterministic(self):
        """Ensure summary templates are deterministic"""
        templates = DeterministicTemplates()

        # Same amounts
        summary1 = templates.comparison_summary_amount(["3,000만원", "3,000만원"])
        assert "동일" in summary1

        # Different amounts
        summary2 = templates.comparison_summary_amount(["3,000만원", "5,000만원"])
        assert "상이" in summary2


class TestExample4SubtypeEligibility:
    """Test Example 4: Subtype Eligibility"""

    def test_subtype_eligibility_checking(self):
        """Test subtype eligibility (제자리암)"""
        from example4_subtype_eligibility import SubtypeEligibilityChecker

        checker = SubtypeEligibilityChecker()
        insurers = ["samsung", "meritz", "lotte"]
        subtype = "제자리암"

        result = checker.check_subtype_eligibility(insurers, subtype)

        assert result["subtype_keyword"] == subtype
        assert len(result["rows"]) == len(insurers)

        for row in result["rows"]:
            assert "insurer" in row
            assert "status" in row
            assert row["status"] in ["O", "X", "△", "Unknown"]

            # If not Unknown, must have evidence
            if row["status"] != "Unknown":
                assert row["evidence_type"] is not None
                assert row["evidence_ref"] is not None

    def test_eligibility_status_logic(self):
        """Test O/X/Unknown logic is deterministic"""
        from example4_subtype_eligibility import SubtypeEligibilityChecker

        checker = SubtypeEligibilityChecker()

        # No evidence → Unknown
        status1 = checker.determine_eligibility_status({
            "has_evidence": False,
            "evidence_type": None
        })
        assert status1 == "Unknown"

        # 면책 → X
        status2 = checker.determine_eligibility_status({
            "has_evidence": True,
            "evidence_type": "면책"
        })
        assert status2 == "X"

        # 감액 → △
        status3 = checker.determine_eligibility_status({
            "has_evidence": True,
            "evidence_type": "감액"
        })
        assert status3 == "△"

        # 정의 → O
        status4 = checker.determine_eligibility_status({
            "has_evidence": True,
            "evidence_type": "정의"
        })
        assert status4 == "O"


class TestDeterministicConstraints:
    """Test constitutional constraints (NO LLM, NO inference)"""

    def test_no_llm_imports(self):
        """Ensure no LLM libraries are imported"""
        import ast

        forbidden_imports = ["openai", "anthropic", "langchain", "transformers"]

        for example_file in [
            "example1_premium_compare.py",
            "example2_coverage_limit.py",
            "example3_two_insurer_compare.py",
            "example4_subtype_eligibility.py"
        ]:
            file_path = Path(__file__).parent.parent / "pipeline" / "step8_render_deterministic" / example_file
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in forbidden_imports, \
                            f"Forbidden import {alias.name} in {example_file}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module and any(lib in node.module for lib in forbidden_imports):
                        raise AssertionError(f"Forbidden import from {node.module} in {example_file}")

    def test_forbidden_phrases_validation(self):
        """Test forbidden phrase detection"""
        templates = DeterministicTemplates()

        # Should pass
        assert templates.validate_no_forbidden_phrases("금액: 동일 (3,000만원)")
        assert templates.validate_no_forbidden_phrases("지급유형: 상이 (정액 / 실손)")

        # Should fail
        assert not templates.validate_no_forbidden_phrases("이 상품을 추천합니다")
        assert not templates.validate_no_forbidden_phrases("더 유리한 조건")
        assert not templates.validate_no_forbidden_phrases("종합 판단하면 좋습니다")


def test_all_examples_executable():
    """Integration test: All examples are executable"""
    examples = [
        "example1_premium_compare.py",
        "example2_coverage_limit.py",
        "example3_two_insurer_compare.py",
        "example4_subtype_eligibility.py"
    ]

    for example in examples:
        example_path = Path(__file__).parent.parent / "pipeline" / "step8_render_deterministic" / example
        assert example_path.exists(), f"{example} not found"

        # Check if file is valid Python
        with open(example_path, 'r', encoding='utf-8') as f:
            compile(f.read(), example_path, 'exec')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
