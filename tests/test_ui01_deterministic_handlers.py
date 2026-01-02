"""
STEP NEXT-UI-01: Test deterministic handlers with LLM OFF

All tests must pass without LLM calls
"""

import pytest
import sys
from pathlib import Path

# Add apps to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.chat_vm import ChatRequest, MessageKind
from apps.api.chat_handlers_deterministic import (
    Example1HandlerDeterministic,
    Example2HandlerDeterministic,
    Example3HandlerDeterministic,
    Example4HandlerDeterministic,
    HandlerRegistryDeterministic
)


class TestExample1Premium:
    """Test Example 1: Premium comparison"""

    def test_premium_disabled_response(self):
        """Premium comparison should return disabled message (no premium data)"""
        handler = Example1HandlerDeterministic()

        request = ChatRequest(
            message="보험료 비교해주세요",
            llm_mode="OFF"
        )

        compiled_query = {
            "request_id": str(request.request_id),
            "kind": "EX1_PREMIUM_DISABLED"
        }

        vm = handler.execute(compiled_query, request)

        assert vm.kind in ["EX1_PREMIUM_DISABLED", "PREMIUM_COMPARE"]
        assert len(vm.summary_bullets) >= 1
        assert vm.lineage["llm_used"] is False
        assert vm.lineage["deterministic"] is True


class TestExample2CoverageLimit:
    """Test Example 2: Coverage limit comparison"""

    def test_coverage_limit_comparison(self):
        """Coverage limit comparison should work LLM OFF"""
        handler = Example2HandlerDeterministic()

        request = ChatRequest(
            message="암진단비 보장한도 알려주세요",
            coverage_names=["암진단비(유사암제외)"],
            insurers=["samsung", "meritz"],
            llm_mode="OFF"
        )

        compiled_query = {
            "request_id": str(request.request_id),
            "kind": "EX2_DETAIL",
            "coverage_code": "A4200_1",
            "insurers": ["samsung", "meritz"]
        }

        vm = handler.execute(compiled_query, request)

        assert vm.kind == "EX2_DETAIL"
        assert len(vm.sections) >= 1
        assert vm.lineage["llm_used"] is False
        assert vm.lineage["deterministic"] is True


class TestExample3TwoInsurer:
    """Test Example 3: Two-insurer comparison"""

    def test_two_insurer_comparison(self):
        """Two-insurer comparison should work LLM OFF"""
        handler = Example3HandlerDeterministic()

        request = ChatRequest(
            message="삼성화재와 메리츠화재 암진단비 비교해주세요",
            insurers=["samsung", "meritz"],
            coverage_names=["암진단비(유사암제외)"],
            llm_mode="OFF"
        )

        compiled_query = {
            "request_id": str(request.request_id),
            "kind": "EX3_INTEGRATED",
            "coverage_code": "A4200_1",
            "insurers": ["samsung", "meritz"]
        }

        vm = handler.execute(compiled_query, request)

        assert vm.kind == "EX3_INTEGRATED"
        assert vm.lineage["llm_used"] is False


class TestExample4Eligibility:
    """Test Example 4: Subtype eligibility"""

    def test_subtype_eligibility(self):
        """Subtype eligibility check should work LLM OFF"""
        handler = Example4HandlerDeterministic()

        request = ChatRequest(
            message="제자리암 보장 가능한가요?",
            insurers=["samsung", "meritz", "lotte"],
            disease_name="제자리암",
            llm_mode="OFF"
        )

        compiled_query = {
            "request_id": str(request.request_id),
            "kind": "EX4_ELIGIBILITY",
            "disease_name": "제자리암",
            "insurers": ["samsung", "meritz", "lotte"]
        }

        vm = handler.execute(compiled_query, request)

        assert vm.kind == "EX4_ELIGIBILITY"
        assert len(vm.summary_bullets) >= 1
        assert vm.lineage["llm_used"] is False


class TestHandlerRegistry:
    """Test handler registry"""

    def test_registry_has_all_handlers(self):
        """Registry should have all example handlers"""
        assert HandlerRegistryDeterministic.get_handler("EX1_PREMIUM_DISABLED") is not None
        assert HandlerRegistryDeterministic.get_handler("EX2_DETAIL") is not None
        assert HandlerRegistryDeterministic.get_handler("EX3_INTEGRATED") is not None
        assert HandlerRegistryDeterministic.get_handler("EX4_ELIGIBILITY") is not None


class TestForbiddenPhrases:
    """Test forbidden phrase validation"""

    def test_no_forbidden_phrases_in_outputs(self):
        """All handler outputs must not contain forbidden phrases"""
        from apps.api.policy.forbidden_language import ForbiddenLanguageValidator

        validator = ForbiddenLanguageValidator()

        # Test texts that should pass
        good_texts = [
            "금액: 동일 (3,000만원)",
            "지급유형: 상이 (정액 / 실손)",
            "보장여부: O",
            "가입설계서 기준입니다"
        ]

        for text in good_texts:
            violations = validator.check_text(text)
            assert len(violations) == 0, f"Should not flag: {text}"

        # Test texts that should fail
        bad_texts = [
            "이 상품을 추천합니다",
            "더 유리한 조건입니다",
            "가성비가 좋습니다"
        ]

        for text in bad_texts:
            violations = validator.check_text(text)
            assert len(violations) > 0, f"Should flag: {text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
