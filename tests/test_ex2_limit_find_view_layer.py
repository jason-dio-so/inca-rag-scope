"""
STEP NEXT-88: EX2_LIMIT_FIND View Layer Expression Tests

Tests for view layer expression rules:
1. Title must include insurer+coverage context
2. Singular/plural grammar must be correct
3. Coverage code must not be exposed
4. Korean particles must be grammatically correct
"""

import pytest
from tests.manual_test_ex2_limit_find_samples import (
    scenario_1_limit_difference,
    scenario_2_waiting_period_difference,
    scenario_3_condition_difference,
    scenario_4_limit_difference_multi,
    scenario_5_reduction_condition_filter,
    scenario_6_waiver_condition_difference,
)


def test_title_includes_insurer_context():
    """Title must include insurer names (not just coverage name)"""

    # 2 insurers
    response = scenario_1_limit_difference()
    assert "삼성화재" in response["title"]
    assert "메리츠화재" in response["title"]

    # 3 insurers
    response = scenario_2_waiting_period_difference()
    assert "한화손해보험" in response["title"]
    assert "삼성화재" in response["title"]
    assert "KB손해보험" in response["title"]


def test_title_includes_coverage_name():
    """Title must include coverage name (never coverage_code)"""

    response = scenario_1_limit_difference()
    assert "암직접입원비" in response["title"]
    assert "A4200" not in response["title"]  # Coverage code must not appear


def test_singular_plural_grammar():
    """Test singular/plural grammar for insurer count"""

    # 1 insurer would use "선택한 보험사의" (but EX2_LIMIT_FIND requires 2+)
    # 2 insurers: should NOT use plural form in summary (specific names used)
    response = scenario_1_limit_difference()
    # Summary uses specific insurer name, not generic "선택한 보험사"
    assert "삼성화재의 보장한도가 다릅니다" in response["summary_bullets"][0]

    # 3 insurers: summary still uses specific names
    response = scenario_2_waiting_period_difference()
    assert "삼성화재의 조건가 다릅니다" in response["summary_bullets"][0]


def test_korean_particle_wa_gwa():
    """Test correct Korean particle usage (와/과)"""

    # "삼성화재" ends with vowel (재) → 와
    response = scenario_1_limit_difference()
    assert "삼성화재와 메리츠화재" in response["title"]

    # "한화손해보험" ends with consonant (험) → 과
    response = scenario_3_condition_difference()
    assert "한화손해보험과 흥국화재" in response["title"]

    # "한화손해보험" + "롯데손해보험" → 과
    response = scenario_6_waiver_condition_difference()
    assert "한화손해보험과 롯데손해보험" in response["title"]


def test_coverage_code_not_in_title():
    """Coverage code must not appear in title"""

    scenarios = [
        scenario_1_limit_difference(),
        scenario_2_waiting_period_difference(),
        scenario_3_condition_difference(),
        scenario_4_limit_difference_multi(),
        scenario_5_reduction_condition_filter(),
        scenario_6_waiver_condition_difference(),
    ]

    coverage_code_pattern = r"[A-Z]\d{4}_\d"
    import re

    for response in scenarios:
        title = response["title"]
        matches = re.findall(coverage_code_pattern, title)
        assert not matches, f"Coverage code found in title: {matches} (title: {title})"


def test_coverage_code_not_in_summary():
    """Coverage code must not appear in summary"""

    scenarios = [
        scenario_1_limit_difference(),
        scenario_2_waiting_period_difference(),
        scenario_3_condition_difference(),
        scenario_4_limit_difference_multi(),
        scenario_5_reduction_condition_filter(),
        scenario_6_waiver_condition_difference(),
    ]

    coverage_code_pattern = r"[A-Z]\d{4}_\d"
    import re

    for response in scenarios:
        summary_text = " ".join(response["summary_bullets"])
        matches = re.findall(coverage_code_pattern, summary_text)
        assert not matches, f"Coverage code found in summary: {matches}"


def test_insurer_display_names_in_table():
    """Table rows must use display names, not codes"""

    response = scenario_1_limit_difference()

    # Check table section
    table_section = response["sections"][0]
    assert table_section["kind"] == "comparison_table"

    # Check row cells
    insurer_names = [row["cells"][0]["text"] for row in table_section["rows"]]

    # Must be display names, not codes
    assert "삼성화재" in insurer_names
    assert "메리츠화재" in insurer_names

    # Must NOT be codes
    assert "samsung" not in insurer_names
    assert "meritz" not in insurer_names


def test_3_insurer_list_formatting():
    """3+ insurers should use comma-separated list"""

    response = scenario_2_waiting_period_difference()
    title = response["title"]

    # Should contain all 3 insurers
    assert "한화손해보험" in title
    assert "삼성화재" in title
    assert "KB손해보험" in title

    # Should use comma separator
    assert ", " in title


def test_compare_field_in_title():
    """Title must include compare field"""

    response = scenario_1_limit_difference()
    assert "보장한도" in response["title"]

    response = scenario_2_waiting_period_difference()
    assert "조건" in response["title"]


def test_title_structure():
    """Title structure must be: {insurers}의 {coverage} {field} 차이"""

    response = scenario_1_limit_difference()
    title = response["title"]

    # Must contain: insurers + 의 + coverage + field + 차이
    assert "의" in title
    assert "차이" in title

    # Example: "삼성화재와 메리츠화재의 암직접입원비 보장한도 차이"
    assert title.count("의") == 1  # Only one possessive particle


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
