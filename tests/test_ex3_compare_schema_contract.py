#!/usr/bin/env python3
"""
Contract Test for EX3_COMPARE Schema

STEP NEXT-77: Validate EX3_COMPARE response against SSOT schema

SSOT: docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md

VALIDATION:
1. Response has kind="EX3_COMPARE"
2. title and summary_bullets are present
3. All refs use PD: or EV: prefix
4. NO raw_text, benefit_description_text in response body
5. KPI section (if present) has refs
6. Table rows have meta.proposal_detail_ref or meta.evidence_refs
7. Forbidden phrase validation passes
"""

import pytest
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


class TestEX3CompareSchemaContract:
    """Contract tests for EX3_COMPARE schema"""

    @pytest.fixture
    def mock_comparison_data(self):
        """Mock comparison data (Step8 output format)"""
        return {
            "samsung": {
                "amount": "3000만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"],
                "kpi_summary": {
                    "payment_type": "정액형",
                    "limit_summary": None,
                    "kpi_evidence_refs": ["EV:samsung:A4200_1:03"],
                    "extraction_notes": ""
                },
                "kpi_condition": {
                    "waiting_period": "90일",
                    "reduction_condition": None,
                    "exclusion_condition": "유사암 제외",
                    "renewal_condition": None,
                    "condition_evidence_refs": ["EV:samsung:A4200_1:04"],
                    "extraction_notes": ""
                }
            },
            "meritz": {
                "amount": "5000만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "정액형",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": ["EV:meritz:A4200_1:01"],
                "kpi_summary": {
                    "payment_type": "정액형",
                    "limit_summary": "1회당 5천만원 한도",
                    "kpi_evidence_refs": ["EV:meritz:A4200_1:02"],
                    "extraction_notes": ""
                },
                "kpi_condition": {
                    "waiting_period": "90일",
                    "reduction_condition": "1년 50%",
                    "exclusion_condition": None,
                    "renewal_condition": None,
                    "condition_evidence_refs": [],
                    "extraction_notes": ""
                }
            }
        }

    def test_compose_returns_ex3_compare_kind(self, mock_comparison_data):
        """Test: Response has kind="EX3_COMPARE" """
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        assert result["kind"] == "EX3_COMPARE"

    def test_compose_has_required_top_level_fields(self, mock_comparison_data):
        """Test: Response has title, summary_bullets, sections"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        assert "title" in result
        assert "summary_bullets" in result
        assert "sections" in result
        assert isinstance(result["summary_bullets"], list)
        assert len(result["summary_bullets"]) > 0

    def test_compose_sections_have_correct_kinds(self, mock_comparison_data):
        """Test: Sections have valid kinds (kpi_summary, comparison_table, common_notes)"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        sections = result["sections"]
        assert len(sections) > 0

        # Extract section kinds
        section_kinds = [s["kind"] for s in sections]

        # Check expected kinds
        assert "comparison_table" in section_kinds  # Required
        assert "common_notes" in section_kinds      # Required

        # KPI section is optional (depends on data)
        # If present, validate it
        for section in sections:
            if section["kind"] == "kpi_summary":
                assert "kpi" in section
                assert "payment_type" in section["kpi"]
                assert "refs" in section["kpi"]

    def test_table_section_has_rows_with_meta(self, mock_comparison_data):
        """Test: Table rows have meta with refs (proposal_detail_ref, evidence_refs)"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        # Find comparison_table section
        table_section = None
        for section in result["sections"]:
            if section["kind"] == "comparison_table":
                table_section = section
                break

        assert table_section is not None
        assert "rows" in table_section
        assert len(table_section["rows"]) > 0

        # Check first row has meta
        first_row = table_section["rows"][0]
        assert "meta" in first_row
        assert first_row["meta"] is not None

        # Check meta has refs
        meta = first_row["meta"]
        assert "proposal_detail_ref" in meta or "evidence_refs" in meta

    def test_all_refs_use_correct_prefix(self, mock_comparison_data):
        """Test: All refs use PD: or EV: prefix"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        # Collect all refs from response
        all_refs = []

        # Extract refs from sections
        for section in result["sections"]:
            if section["kind"] == "kpi_summary":
                kpi_refs = section["kpi"]["refs"]
                all_refs.extend(kpi_refs.get("kpi_evidence_refs", []))
                all_refs.extend(kpi_refs.get("condition_evidence_refs", []))

            elif section["kind"] == "comparison_table":
                for row in section["rows"]:
                    if row.get("meta"):
                        meta = row["meta"]
                        if meta.get("proposal_detail_ref"):
                            all_refs.append(meta["proposal_detail_ref"])
                        if meta.get("evidence_refs"):
                            all_refs.extend(meta["evidence_refs"])

        # Validate all refs have PD: or EV: prefix
        for ref in all_refs:
            assert ref.startswith("PD:") or ref.startswith("EV:"), f"Invalid ref prefix: {ref}"

    def test_no_raw_text_in_response_body(self, mock_comparison_data):
        """Test: NO raw_text, benefit_description_text in response body"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        # Serialize to JSON string
        import json
        result_json = json.dumps(result)

        # Check for forbidden field names
        assert "raw_text" not in result_json, "raw_text should not be in response body"
        assert "benefit_description_text" not in result_json, "benefit_description_text should not be in response body"

    def test_kpi_section_has_refs_if_present(self, mock_comparison_data):
        """Test: KPI section (if present) has refs"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        # Find kpi_summary section
        kpi_section = None
        for section in result["sections"]:
            if section["kind"] == "kpi_summary":
                kpi_section = section
                break

        if kpi_section:
            # Validate refs exist
            assert "kpi" in kpi_section
            assert "refs" in kpi_section["kpi"]
            refs = kpi_section["kpi"]["refs"]

            # Check that at least one ref type exists
            has_refs = (
                len(refs.get("kpi_evidence_refs", [])) > 0 or
                len(refs.get("condition_evidence_refs", [])) > 0
            )
            assert has_refs, "KPI section should have at least one ref type with values"

    def test_payment_type_unknown_handling(self):
        """Test: payment_type UNKNOWN is preserved (not converted to '표현 없음' in composer)"""
        # Create data with UNKNOWN payment_type
        comparison_data = {
            "samsung": {
                "amount": "3000만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "UNKNOWN",  # Edge case
                "proposal_detail_ref": "PD:samsung:A4200_1",
                "evidence_refs": [],
                "kpi_summary": {
                    "payment_type": "UNKNOWN",
                    "limit_summary": None,
                    "kpi_evidence_refs": [],
                    "extraction_notes": ""
                }
            },
            "meritz": {
                "amount": "5000만원",
                "premium": "명시 없음",
                "period": "20년납/80세만기",
                "payment_type": "UNKNOWN",
                "proposal_detail_ref": "PD:meritz:A4200_1",
                "evidence_refs": [],
                "kpi_summary": {
                    "payment_type": "UNKNOWN",
                    "limit_summary": None,
                    "kpi_evidence_refs": [],
                    "extraction_notes": ""
                }
            }
        }

        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비"
        )

        # Find KPI section
        kpi_section = None
        for section in result["sections"]:
            if section["kind"] == "kpi_summary":
                kpi_section = section
                break

        if kpi_section:
            # payment_type should remain "UNKNOWN" in response (UI will convert to "표현 없음")
            assert kpi_section["kpi"]["payment_type"] == "UNKNOWN"

        # Find comparison_table section and check payment_type row
        table_section = None
        for section in result["sections"]:
            if section["kind"] == "comparison_table":
                table_section = section
                break

        assert table_section is not None

        # Find "지급유형" row
        payment_type_row = None
        for row in table_section["rows"]:
            if row["cells"][0]["text"] == "지급유형":
                payment_type_row = row
                break

        assert payment_type_row is not None
        # Cells should display "표현 없음" (converted by composer for table display)
        assert payment_type_row["cells"][1]["text"] == "표현 없음"
        assert payment_type_row["cells"][2]["text"] == "표현 없음"

    def test_lineage_metadata_present(self, mock_comparison_data):
        """Test: Response has lineage metadata with deterministic flag"""
        result = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=mock_comparison_data,
            coverage_name="암진단비(유사암 제외)"
        )

        assert "lineage" in result
        lineage = result["lineage"]

        assert "handler" in lineage
        assert lineage["handler"] == "EX3CompareComposer"
        assert "llm_used" in lineage
        assert lineage["llm_used"] is False
        assert "deterministic" in lineage
        assert lineage["deterministic"] is True
