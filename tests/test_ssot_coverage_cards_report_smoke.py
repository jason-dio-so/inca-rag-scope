"""
STEP NEXT-18X-SSOT: Coverage Cards Report Smoke Test

SSOT Validation: data/compare/*_coverage_cards.jsonl only
Replaces legacy report-based tests (reports/*.md removed)

Validates:
- All insurers have coverage_cards.jsonl
- Each card has required fields (insurer, coverage_name_raw, mapping_status, evidence_status, amount.status)
- mapping_status values are normalized (matched|unmatched)
- amount.status values are valid (CONFIRMED|UNCONFIRMED|NOT_AVAILABLE)
- At least 1 matched coverage per insurer (minimal sanity)
"""

import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COMPARE_DIR = PROJECT_ROOT / "data" / "compare"

EXPECTED_INSURERS = ["samsung", "meritz", "db", "hanwha", "hyundai", "kb", "heungkuk", "lotte"]
VALID_MAPPING_STATUSES = {"matched", "unmatched"}
VALID_AMOUNT_STATUSES = {"CONFIRMED", "UNCONFIRMED", "NOT_AVAILABLE"}


def get_coverage_cards_files():
    """Get all coverage_cards.jsonl files."""
    return list(COMPARE_DIR.glob("*_coverage_cards.jsonl"))


def parse_jsonl(file_path: Path):
    """Parse JSONL file and return list of records."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                pytest.fail(f"{file_path.name} line {line_num}: JSON decode error: {e}")
    return records


class TestSSOTCoverageCardsReportSmoke:
    """SSOT-based smoke tests for coverage_cards.jsonl files."""

    def test_all_insurers_have_cards(self):
        """All expected insurers have coverage_cards.jsonl files."""
        files = get_coverage_cards_files()
        found_insurers = set()

        for file_path in files:
            insurer = file_path.stem.replace("_coverage_cards", "")
            found_insurers.add(insurer)

        missing = set(EXPECTED_INSURERS) - found_insurers
        assert not missing, f"Missing coverage_cards for insurers: {missing}"

    def test_cards_parseable_and_not_empty(self):
        """All coverage_cards.jsonl files are valid JSON and not empty."""
        files = get_coverage_cards_files()
        assert len(files) > 0, "No coverage_cards.jsonl files found"

        for file_path in files:
            records = parse_jsonl(file_path)
            assert len(records) > 0, f"{file_path.name} is empty"

    def test_required_fields_present(self):
        """All cards have required fields."""
        files = get_coverage_cards_files()
        required_fields = ["insurer", "coverage_name_raw", "mapping_status", "evidence_status"]

        for file_path in files:
            records = parse_jsonl(file_path)
            for i, record in enumerate(records):
                for field in required_fields:
                    assert field in record, \
                        f"{file_path.name} record {i}: missing required field '{field}'"

                # amount.status is nested
                assert "amount" in record, \
                    f"{file_path.name} record {i}: missing 'amount' field"
                assert "status" in record["amount"], \
                    f"{file_path.name} record {i}: missing 'amount.status' field"

    def test_mapping_status_normalized(self):
        """mapping_status values are normalized (matched|unmatched)."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            for i, record in enumerate(records):
                mapping_status = record.get("mapping_status", "").strip().lower()
                assert mapping_status in VALID_MAPPING_STATUSES, \
                    f"{file_path.name} record {i}: invalid mapping_status '{mapping_status}', expected {VALID_MAPPING_STATUSES}"

    def test_amount_status_valid(self):
        """amount.status values are valid (CONFIRMED|UNCONFIRMED|NOT_AVAILABLE)."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            for i, record in enumerate(records):
                amount_status = record.get("amount", {}).get("status")
                assert amount_status in VALID_AMOUNT_STATUSES, \
                    f"{file_path.name} record {i}: invalid amount.status '{amount_status}', expected {VALID_AMOUNT_STATUSES}"

    def test_at_least_one_matched_coverage_per_insurer(self):
        """Each insurer has at least 1 matched coverage (minimal sanity)."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            matched_count = sum(
                1 for r in records
                if r.get("mapping_status", "").strip().lower() == "matched"
            )

            # Sanity check: at least 1 matched coverage per insurer
            # This catches catastrophic mapping failures
            assert matched_count > 0, \
                f"{file_path.name}: 0 matched coverages out of {len(records)} total (possible mapping failure)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
