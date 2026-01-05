"""
STEP NEXT-138: Single-Insurer Explanation Guard (CRITICAL REGRESSION FIX)

PROBLEM:
"삼성화재 암진단비 설명해줘" → EXAM2 비교 화면 노출 (삼성+메리츠)
This is a regression.

ROOT RULES:
1. IF insurer_count == 1 AND intent in ["설명", "알려줘", "설명해줘"]
   → FORCE EX2_DETAIL (single-insurer detail view)
   → EXAM3_COMPARE HARD BLOCK (ignore multi-insurer context)

2. EXAM3 entry requires BOTH:
   - insurer_count >= 2
   - explicit compare signal ("비교", "차이", "다른", "vs")

3. When a new query explicitly mentions insurers:
   → CLEAR previous conversation insurers (NO carry-over)

TESTS:
- T1: "삼성화재 암진단비 설명해줘" → EX1_DETAIL detected, single insurer
- T2: "삼성화재와 메리츠화재 암진단비 비교해줘" → EX3 detected, 2 insurers
- T3: After EX3, "삼성화재 수술비 설명해줘" → context reset, single insurer
- T4: "설명해줘" (no insurer) → clarification required
- T5: "암진단비 비교해줘" (no insurer) → clarification required
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_single_insurer_explanation_detection():
    """T1: '삼성화재 암진단비 설명해줘' → EX1_DETAIL, single insurer"""
    from apps.web.lib.clarificationUtils import deriveClarificationState

    message = "삼성화재 암진단비 설명해줘"

    result = deriveClarificationState({
        "requestPayload": {
            "message": message,
            "insurers": [],
            "coverage_names": []
        },
        "lastResponseVm": None,
        "lastUserText": message,
        "conversationContext": {
            "lockedInsurers": None,
            "lockedCoverageNames": None
        }
    })

    # Should detect EX1_DETAIL (explanation intent)
    assert result["examType"] == "EX1_DETAIL", f"Expected EX1_DETAIL, got {result['examType']}"

    # Should resolve single insurer from message
    assert result["resolvedSlots"]["insurers"] == ["samsung"], \
        f"Expected ['samsung'], got {result['resolvedSlots']['insurers']}"

    # Should resolve coverage from message
    assert result["resolvedSlots"]["coverage"] == ["암진단비"], \
        f"Expected ['암진단비'], got {result['resolvedSlots']['coverage']}"

    # Should NOT show clarification (all slots resolved)
    assert result["showClarification"] == False, \
        f"Expected showClarification=False, got {result['showClarification']}"


def test_multi_insurer_comparison_detection():
    """T2: '삼성화재와 메리츠화재 암진단비 비교해줘' → EX3, 2 insurers"""
    from apps.web.lib.clarificationUtils import deriveClarificationState

    message = "삼성화재와 메리츠화재 암진단비 비교해줘"

    result = deriveClarificationState({
        "requestPayload": {
            "message": message,
            "insurers": [],
            "coverage_names": []
        },
        "lastResponseVm": None,
        "lastUserText": message,
        "conversationContext": {
            "lockedInsurers": None,
            "lockedCoverageNames": None
        }
    })

    # Should detect EX3 (comparison intent)
    assert result["examType"] == "EX3", f"Expected EX3, got {result['examType']}"

    # Should resolve 2 insurers from message
    assert len(result["resolvedSlots"]["insurers"]) == 2, \
        f"Expected 2 insurers, got {len(result['resolvedSlots']['insurers'])}"
    assert set(result["resolvedSlots"]["insurers"]) == {"samsung", "meritz"}, \
        f"Expected samsung+meritz, got {result['resolvedSlots']['insurers']}"

    # Should resolve coverage from message
    assert result["resolvedSlots"]["coverage"] == ["암진단비"], \
        f"Expected ['암진단비'], got {result['resolvedSlots']['coverage']}"

    # Should NOT show clarification (all slots resolved)
    assert result["showClarification"] == False, \
        f"Expected showClarification=False, got {result['showClarification']}"


def test_context_reset_on_explicit_insurer():
    """T3: After EX3, '삼성화재 수술비 설명해줘' → context reset, single insurer"""
    from apps.web.lib.clarificationUtils import deriveClarificationState

    message = "삼성화재 수술비 설명해줘"

    result = deriveClarificationState({
        "requestPayload": {
            "message": message,
            "insurers": [],
            "coverage_names": []
        },
        "lastResponseVm": None,
        "lastUserText": message,
        "conversationContext": {
            "lockedInsurers": ["samsung", "meritz"],  # Previous EX3 context
            "lockedCoverageNames": ["암진단비"]
        }
    })

    # Should detect EX1_DETAIL (explanation intent overrides comparison context)
    assert result["examType"] == "EX1_DETAIL", f"Expected EX1_DETAIL, got {result['examType']}"

    # CRITICAL: Should use explicitly mentioned insurer (samsung), NOT locked context (samsung+meritz)
    assert result["resolvedSlots"]["insurers"] == ["samsung"], \
        f"Expected ['samsung'] (context reset), got {result['resolvedSlots']['insurers']}"

    # Should resolve NEW coverage from message
    assert result["resolvedSlots"]["coverage"] == ["수술비"], \
        f"Expected ['수술비'], got {result['resolvedSlots']['coverage']}"

    # Should NOT show clarification
    assert result["showClarification"] == False, \
        f"Expected showClarification=False, got {result['showClarification']}"


def test_explanation_without_insurer_requires_clarification():
    """T4: '설명해줘' (no insurer) → clarification required"""
    from apps.web.lib.clarificationUtils import deriveClarificationState

    message = "설명해줘"

    result = deriveClarificationState({
        "requestPayload": {
            "message": message,
            "insurers": [],
            "coverage_names": []
        },
        "lastResponseVm": None,
        "lastUserText": message,
        "conversationContext": {
            "lockedInsurers": None,
            "lockedCoverageNames": None
        }
    })

    # Should detect EX1_DETAIL
    assert result["examType"] == "EX1_DETAIL", f"Expected EX1_DETAIL, got {result['examType']}"

    # Should show clarification (missing insurers + coverage)
    assert result["showClarification"] == True, \
        f"Expected showClarification=True, got {result['showClarification']}"
    assert result["missingSlots"]["insurers"] == True
    assert result["missingSlots"]["coverage"] == True


def test_comparison_without_insurer_requires_clarification():
    """T5: '암진단비 비교해줘' (no insurer) → clarification required"""
    from apps.web.lib.clarificationUtils import deriveClarificationState

    message = "암진단비 비교해줘"

    result = deriveClarificationState({
        "requestPayload": {
            "message": message,
            "insurers": [],
            "coverage_names": []
        },
        "lastResponseVm": None,
        "lastUserText": message,
        "conversationContext": {
            "lockedInsurers": None,
            "lockedCoverageNames": None
        }
    })

    # Should detect EX3 (comparison intent)
    assert result["examType"] == "EX3", f"Expected EX3, got {result['examType']}"

    # Should show clarification (missing insurers, coverage resolved)
    assert result["showClarification"] == True, \
        f"Expected showClarification=True, got {result['showClarification']}"
    assert result["missingSlots"]["insurers"] == True
    assert result["missingSlots"]["coverage"] == False  # Coverage resolved from message


def test_single_insurer_blocks_exam3():
    """T6: Single insurer + explanation MUST NOT route to EX3_COMPARE"""
    from apps.web.lib.clarificationUtils import deriveClarificationState

    message = "삼성화재 암진단비 설명해줘"

    result = deriveClarificationState({
        "requestPayload": {
            "message": message,
            "insurers": ["samsung"],
            "coverage_names": ["암진단비"]
        },
        "lastResponseVm": None,
        "lastUserText": message,
        "conversationContext": {
            "lockedInsurers": None,
            "lockedCoverageNames": None
        }
    })

    # CRITICAL: Must be EX1_DETAIL, NOT EX3
    assert result["examType"] == "EX1_DETAIL", \
        f"Single insurer + explanation MUST route to EX1_DETAIL, got {result['examType']}"

    # Single insurer MUST be preserved
    assert len(result["resolvedSlots"]["insurers"]) == 1, \
        f"Expected 1 insurer, got {len(result['resolvedSlots']['insurers'])}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
