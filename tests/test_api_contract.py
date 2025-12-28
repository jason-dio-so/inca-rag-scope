"""
Test API Contract - Request/Response Schema Validation
STEP NEXT-9
"""

import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

# Paths
DOCS_DIR = Path(__file__).parent.parent / "docs" / "api"
SCHEMA_DIR = DOCS_DIR / "schema"
FIXTURES_DIR = Path(__file__).parent.parent / "apps" / "mock-api" / "fixtures"

# Load schemas
with open(SCHEMA_DIR / "compare_request.schema.json") as f:
    REQUEST_SCHEMA = json.load(f)

with open(SCHEMA_DIR / "compare_response_view_model.schema.json") as f:
    RESPONSE_SCHEMA = json.load(f)

# Example requests (matching EXAMPLE_TO_REQUEST in index.html)
EXAMPLE_REQUESTS = {
    "example1": {
        "intent": "PREMIUM_REFERENCE",
        "insurers": ["SAMSUNG", "HANWHA", "MERITZ", "DB"],
        "products": [
            {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
            {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"},
            {"insurer": "MERITZ", "product_name": "메리츠화재 무배당 암보험"},
            {"insurer": "DB", "product_name": "DB손해보험 무배당 암보험"}
        ],
        "target_coverages": [],
        "options": {"premium_reference_only": True, "include_notes": False, "include_evidence": False}
    },
    "example2": {
        "intent": "COVERAGE_CONDITION_DIFF",
        "insurers": ["SAMSUNG", "HANWHA"],
        "products": [
            {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
            {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
        ],
        "target_coverages": [{"coverage_code": "A4210", "coverage_name_raw": "암 직접치료 입원일당"}]
    },
    "example3": {
        "intent": "PRODUCT_SUMMARY",
        "insurers": ["SAMSUNG", "HANWHA"],
        "products": [
            {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
            {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
        ],
        "target_coverages": [
            {"coverage_code": "A4200_1"},
            {"coverage_code": "A4210"},
            {"coverage_code": "A5200"},
            {"coverage_code": "A5100"},
            {"coverage_code": "A6100_1"},
            {"coverage_code": "A6300_1"},
            {"coverage_code": "A9617_1"},
            {"coverage_code": "A9640_1"},
            {"coverage_code": "A4102"}
        ]
    },
    "example4": {
        "intent": "COVERAGE_AVAILABILITY",
        "insurers": ["SAMSUNG", "HANWHA"],
        "products": [
            {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
            {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
        ],
        "target_coverages": [
            {"coverage_name_raw": "제자리암"},
            {"coverage_name_raw": "경계성종양"}
        ]
    }
}

# Fixtures mapping
EXAMPLE_FIXTURES = {
    "example1": "example1_premium.json",
    "example2": "example2_coverage_compare.json",
    "example3": "example3_product_summary.json",
    "example4": "example4_ox.json"
}


class TestRequestSchemaValidation:
    """Test that all example requests pass schema validation"""

    @pytest.mark.parametrize("example_name", ["example1", "example2", "example3", "example4"])
    def test_request_schema_validation(self, example_name):
        """Each example request must pass schema validation"""
        request = EXAMPLE_REQUESTS[example_name]
        validate(instance=request, schema=REQUEST_SCHEMA)  # Will raise if invalid

    def test_required_fields_enforced(self):
        """Schema enforces required fields"""
        invalid_request = {"intent": "PRODUCT_SUMMARY"}  # Missing insurers, products
        with pytest.raises(ValidationError):
            validate(instance=invalid_request, schema=REQUEST_SCHEMA)

    def test_intent_enum_enforced(self):
        """Schema enforces intent enum"""
        invalid_request = {
            "intent": "INVALID_INTENT",
            "insurers": ["SAMSUNG"],
            "products": [{"insurer": "SAMSUNG", "product_name": "test"}]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_request, schema=REQUEST_SCHEMA)


class TestResponseSchemaValidation:
    """Test that all fixture responses pass schema validation"""

    @pytest.mark.parametrize("example_name", ["example1", "example2", "example3", "example4"])
    def test_response_schema_validation(self, example_name):
        """Each fixture response must pass schema validation"""
        fixture_file = EXAMPLE_FIXTURES[example_name]
        fixture_path = FIXTURES_DIR / fixture_file

        with open(fixture_path, "r", encoding="utf-8") as f:
            response = json.load(f)

        validate(instance=response, schema=RESPONSE_SCHEMA)  # Will raise if invalid

    def test_five_block_structure_enforced(self):
        """Response must have 5 required blocks"""
        invalid_response = {"meta": {}, "query_summary": {}}  # Missing 3 blocks
        with pytest.raises(ValidationError):
            validate(instance=invalid_response, schema=RESPONSE_SCHEMA)


class TestContractConsistency:
    """Test consistency between request and response"""

    def test_example3_has_9_coverages(self):
        """Example 3 request has 9 coverages, response should match"""
        request = EXAMPLE_REQUESTS["example3"]
        assert len(request["target_coverages"]) == 9

        fixture_path = FIXTURES_DIR / "example3_product_summary.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response = json.load(f)

        # Response should have 9 rows in comparison
        assert len(response["comparison"]["rows"]) == 9

    def test_premium_notice_in_example1_only(self):
        """premium_notice should be true in example1, false in others"""
        for example_name in ["example1", "example2", "example3", "example4"]:
            fixture_path = FIXTURES_DIR / EXAMPLE_FIXTURES[example_name]
            with open(fixture_path, "r", encoding="utf-8") as f:
                response = json.load(f)

            premium_notice = response["query_summary"]["premium_notice"]
            if example_name == "example1":
                assert premium_notice is True, "Example 1 must have premium_notice=true"
            else:
                assert premium_notice is False, f"{example_name} must have premium_notice=false"


class TestForbiddenPhrases:
    """Test that responses contain no forbidden phrases"""

    FORBIDDEN = ["추천", "권유", "유리", "불리", "더 좋", "가입하세요", "선택하세요"]

    @pytest.mark.parametrize("example_name", ["example1", "example2", "example3", "example4"])
    def test_no_forbidden_phrases_in_response(self, example_name):
        """No forbidden phrases in any response"""
        fixture_path = FIXTURES_DIR / EXAMPLE_FIXTURES[example_name]
        with open(fixture_path, "r", encoding="utf-8") as f:
            response_text = f.read()

        found_forbidden = []
        for phrase in self.FORBIDDEN:
            if phrase in response_text:
                found_forbidden.append(phrase)

        assert len(found_forbidden) == 0, f"Found forbidden phrases in {example_name}: {found_forbidden}"


class TestEvidenceRules:
    """Test evidence-based rules"""

    @pytest.mark.parametrize("example_name", ["example2", "example3", "example4"])
    def test_all_values_have_evidence(self, example_name):
        """All comparison values must have evidence object"""
        fixture_path = FIXTURES_DIR / EXAMPLE_FIXTURES[example_name]
        with open(fixture_path, "r", encoding="utf-8") as f:
            response = json.load(f)

        rows = response["comparison"]["rows"]
        for row in rows:
            for insurer, value_obj in row["values"].items():
                assert "evidence" in value_obj, f"Missing evidence in {example_name} row for {insurer}"
                assert "status" in value_obj["evidence"], f"Missing evidence.status in {example_name}"

    def test_notes_have_evidence_refs(self):
        """All notes must have evidence_refs (example 3)"""
        fixture_path = FIXTURES_DIR / "example3_product_summary.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            response = json.load(f)

        notes = response["notes"]
        for note in notes:
            assert "evidence_refs" in note, f"Note missing evidence_refs: {note['title']}"
            assert len(note["evidence_refs"]) > 0, f"Note has empty evidence_refs: {note['title']}"
