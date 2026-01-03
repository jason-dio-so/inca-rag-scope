#!/usr/bin/env python3
"""
STEP NEXT-112: EX3_COMPARE Comparison-First UX Lock (Contract Tests)

Tests the structural redesign of EX3_COMPARE bubble_markdown:
1. 구조적 차이 요약 (structural difference summary - NOT abstract)
2. 보장 기준 비교 (side-by-side comparison table - comparison-first)
3. 해석 보조 (neutral interpretation guide - NOT judgment)

Constitutional Rules:
- ❌ NO abstract/evasive summary ("일부 보험사는...")
- ❌ NO card-based layout (vertical separation)
- ❌ NO recommendations / superiority judgments
- ✅ Structural difference explicitly stated (HOW coverage is defined)
- ✅ Side-by-side table (same row = direct comparison)
- ✅ Neutral interpretation (structural implications ONLY)
"""

import pytest
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


class TestEX3ComparisonFirstStructure:
    """Test STEP NEXT-112: Comparison-first structure (NOT card-based)"""

    def test_no_abstract_evasive_summary(self):
        """
        ❌ FORBIDDEN: "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
        ✅ REQUIRED: Explicit structural comparison with insurer names
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "보험기간 중 1회",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ❌ FORBIDDEN: Abstract/evasive summary
        assert "일부 보험사는" not in bubble, "Abstract summary '일부 보험사는...' is FORBIDDEN"
        assert "일부는" not in bubble, "Evasive pattern '일부는...' is FORBIDDEN"

        # ✅ REQUIRED: Explicit insurer names in structural comparison
        assert "삼성화재" in bubble, "Insurer name (삼성화재) MUST be in structural summary"
        assert "메리츠화재" in bubble, "Insurer name (메리츠화재) MUST be in structural summary"

        # ✅ REQUIRED: Structural difference explicitly stated
        assert "구조적 차이 요약" in bubble, "Section '구조적 차이 요약' is REQUIRED"
        assert ("보장이 정의됩니다" in bubble or "보장이 정의되고" in bubble), \
            "Structural definition statement is REQUIRED"

    def test_side_by_side_comparison_table_exists(self):
        """
        ✅ REQUIRED: Side-by-side comparison table (NOT vertical cards)
        Table format: | 비교 항목 | Insurer1 | Insurer2 |
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "보험기간 중 1회",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ✅ REQUIRED: Comparison table section
        assert "보장 기준 비교" in bubble, "Section '보장 기준 비교' is REQUIRED"

        # ✅ REQUIRED: Markdown table format (| ... | ... |)
        assert "| 비교 항목 |" in bubble, "Table header '| 비교 항목 |' is REQUIRED"
        assert "|----------|" in bubble or "| --- |" in bubble, "Table separator is REQUIRED"

        # ✅ REQUIRED: Insurer names in table columns
        assert "| 비교 항목 | 삼성화재 | 메리츠화재 |" in bubble, \
            "Table columns MUST have insurer display names (NOT codes)"

    def test_same_row_comparison_not_vertical_cards(self):
        """
        ✅ REQUIRED: Comparison values on SAME ROW (cognitive load reduction)
        ❌ FORBIDDEN: Vertical card separation (requires mental comparison)
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "보험기간 중 1회",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ✅ REQUIRED: Table row with "보장 정의 기준" comparison
        assert "| 보장 정의 기준 |" in bubble, "Row '보장 정의 기준' is REQUIRED"

        # ✅ REQUIRED: At least one row with side-by-side values
        # Check that table has multiple cells per row (format: | item | val1 | val2 |)
        table_lines = [line for line in bubble.split("\n") if line.startswith("|")]
        data_rows = [line for line in table_lines if "---" not in line and "비교 항목" not in line]

        assert len(data_rows) >= 1, "At least 1 comparison row is REQUIRED"

        # ✅ Each data row should have 3+ cells (item, insurer1, insurer2)
        for row in data_rows:
            cell_count = row.count("|") - 1  # Subtract 1 for trailing |
            assert cell_count >= 3, f"Row MUST have 3+ cells (item + 2 insurers), got {cell_count}: {row}"

    def test_no_recommendation_or_superiority_judgment(self):
        """
        ❌ FORBIDDEN: Recommendations, superiority judgments, "더 유리"
        ✅ REQUIRED: Neutral interpretation ONLY (structural implications)
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "보험기간 중 1회",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ❌ FORBIDDEN: Recommendation keywords
        forbidden = ["추천", "권장", "유리", "불리", "좋습니다", "나쁩니다", "선택하세요"]
        for word in forbidden:
            assert word not in bubble, f"Recommendation keyword '{word}' is FORBIDDEN in bubble_markdown"

        # ✅ REQUIRED: Neutral interpretation section
        assert "해석 보조" in bubble, "Section '해석 보조' is REQUIRED"


class TestEX3StructuralDifferenceSummary:
    """Test structural difference summary (NOT abstract)"""

    def test_structural_difference_when_different_basis(self):
        """
        ✅ REQUIRED (Different Basis):
        "메리츠화재는 정액 지급 방식으로 보장이 정의되고,
         삼성화재는 지급 한도 기준으로 보장이 정의됩니다."
        """
        insurers = ["meritz", "samsung"]
        comparison_data = {
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
            "samsung": {
                "amount": "명시 없음",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ✅ REQUIRED: Different basis → explicit statement with both insurers
        assert "메리츠화재는" in bubble, "Insurer1 name (메리츠화재) MUST be in summary"
        assert "삼성화재는" in bubble or "삼성화재" in bubble, \
            "Insurer2 name (삼성화재) MUST be in summary"

        # ✅ REQUIRED: Structural definition keywords
        assert "정의되고" in bubble or "정의됩니다" in bubble, \
            "Structural definition verb is REQUIRED"

        # ✅ REQUIRED: Mention both "정액 지급" and "한도" for this case
        assert "정액 지급" in bubble, "'정액 지급' keyword is REQUIRED for amount-based"
        assert "한도" in bubble, "'한도' keyword is REQUIRED for limit-based"

    def test_structural_summary_when_same_basis(self):
        """
        ✅ REQUIRED (Same Basis):
        "삼성화재와 메리츠화재는 모두 정액 지급 방식으로 보장이 정의됩니다."
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
            "meritz": {
                "amount": "5천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ✅ REQUIRED: Same basis → "모두" pattern
        assert "모두" in bubble, "'모두' keyword is REQUIRED when basis is the same"
        assert "정액 지급 방식" in bubble, "'정액 지급 방식' keyword is REQUIRED"
        assert "정의됩니다" in bubble, "Structural definition statement is REQUIRED"


class TestEX3InterpretationGuide:
    """Test interpretation guide (neutral, NOT judgment)"""

    def test_interpretation_guide_exists(self):
        """
        ✅ REQUIRED: "해석 보조" section with neutral interpretation
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "보험기간 중 1회",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ✅ REQUIRED: Section exists
        assert "## 해석 보조" in bubble, "Section '해석 보조' is REQUIRED"

        # ✅ REQUIRED: Interpretation guide has content (not empty)
        lines_after_interpretation = bubble.split("## 해석 보조")[1].strip()
        assert len(lines_after_interpretation) > 50, \
            "Interpretation guide MUST have substantive content (>50 chars)"

    def test_interpretation_guide_is_neutral(self):
        """
        ✅ REQUIRED: Interpretation explains structural implications
        ❌ FORBIDDEN: "더 좋다", "선택하세요", "추천"
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "보험기간 중 1회",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]
        interpretation_section = bubble.split("## 해석 보조")[1] if "## 해석 보조" in bubble else ""

        # ❌ FORBIDDEN: Judgment keywords in interpretation
        forbidden = ["더 좋", "선택하세요", "추천", "권장", "유리합니다"]
        for word in forbidden:
            assert word not in interpretation_section, \
                f"Judgment keyword '{word}' is FORBIDDEN in interpretation guide"

        # ✅ REQUIRED: Neutral keywords (structural implications)
        # At least one of these patterns should appear
        neutral_keywords = [
            "지급액이 명확",
            "조건 확인이 중요",
            "지급 조건",
            "확인하시기 바랍니다",
            "달라질 수 있습니다"
        ]
        has_neutral = any(kw in interpretation_section for kw in neutral_keywords)
        assert has_neutral, \
            "Interpretation guide MUST contain neutral structural implications (NOT judgments)"

    def test_interpretation_guide_contextual_to_structure(self):
        """
        ✅ REQUIRED: Interpretation adapts to structure types
        - Mixed (amount vs. limit) → explain both
        - Both amount-based → explain amount-based
        - Both limit-based → explain limit-based
        """
        # Case 1: Mixed (amount vs. limit)
        insurers = ["meritz", "samsung"]
        comparison_data_mixed = {
            "meritz": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
            "samsung": {
                "amount": "명시 없음",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": "보험기간 중 1회"},
            },
        }

        response_mixed = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data_mixed,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_mixed = response_mixed["bubble_markdown"]
        interpretation_mixed = bubble_mixed.split("## 해석 보조")[1] if "## 해석 보조" in bubble_mixed else ""

        # ✅ Mixed → should explain BOTH amount and limit
        assert "정액 지급" in interpretation_mixed or "지급액이 명확" in interpretation_mixed, \
            "Mixed case MUST explain amount-based structure"
        assert "한도" in interpretation_mixed or "지급 조건" in interpretation_mixed, \
            "Mixed case MUST explain limit-based structure"


class TestEX3RegressionProtection:
    """Regression tests for existing contract (schema, refs, no code exposure)"""

    def test_no_coverage_code_exposure(self):
        """
        ❌ FORBIDDEN: coverage_code (A4200_1) in bubble_markdown
        ✅ ALLOWED: coverage_code in refs (PD:samsung:A4200_1)
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
            "meritz": {
                "amount": "5천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ❌ FORBIDDEN: coverage_code pattern in bubble_markdown
        # Pattern: 4+ uppercase letters followed by underscore and digits
        import re
        code_pattern = r'\b[A-Z]{4,}_\d+'
        matches = re.findall(code_pattern, bubble)

        assert len(matches) == 0, \
            f"Coverage codes MUST NOT appear in bubble_markdown. Found: {matches}"

    def test_no_insurer_code_exposure(self):
        """
        ❌ FORBIDDEN: insurer codes (samsung, meritz, kb) in bubble_markdown
        ✅ REQUIRED: display names (삼성화재, 메리츠화재, KB손해보험)
        ✅ ALLOWED: insurer codes in refs (PD:samsung:, EV:meritz:)
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
            "meritz": {
                "amount": "5천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]

        # ❌ FORBIDDEN: lowercase insurer codes (NOT in refs)
        # Filter out refs (PD:, EV:) before checking
        bubble_no_refs = bubble
        for prefix in ["PD:", "EV:"]:
            # Remove ref patterns: PD:samsung:A4200_1, EV:meritz:A4200_1:01
            import re
            bubble_no_refs = re.sub(rf'{prefix}\w+:\w+(?::\d+)?', '', bubble_no_refs)

        insurer_codes = ["samsung", "meritz", "kb", "hanwha", "hyundai", "lotte", "db", "heungkuk"]
        for code in insurer_codes:
            assert code not in bubble_no_refs.lower(), \
                f"Insurer code '{code}' MUST NOT appear in bubble_markdown (outside refs)"

    def test_response_kind_is_ex3_compare(self):
        """
        ✅ REQUIRED: response["kind"] == "EX3_COMPARE"
        """
        insurers = ["samsung", "meritz"]
        comparison_data = {
            "samsung": {
                "amount": "3천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
            "meritz": {
                "amount": "5천만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {"payment_type": "정액형", "limit_summary": None},
            },
        }

        response = EX3CompareComposer.compose(
            insurers=insurers,
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        assert response["kind"] == "EX3_COMPARE", \
            "Response kind MUST be 'EX3_COMPARE'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
