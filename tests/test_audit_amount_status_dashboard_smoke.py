"""
STEP NEXT-17B: Amount Status Dashboard Smoke Test

Validates that all coverage_cards.jsonl files are parseable and contain valid amount status values.
"""

import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
COMPARE_DIR = PROJECT_ROOT / "data" / "compare"

EXPECTED_INSURERS = ["samsung", "meritz", "db", "hanwha", "hyundai", "kb", "heungkuk", "lotte"]
VALID_STATUSES = {"CONFIRMED", "UNCONFIRMED", "NOT_AVAILABLE"}


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


class TestAmountStatusDashboardSmoke:
    """Smoke tests for amount status dashboard data integrity."""

    def test_all_expected_insurers_present(self):
        """Verify all expected insurers have coverage_cards.jsonl files."""
        files = get_coverage_cards_files()
        found_insurers = set()

        for file_path in files:
            insurer = file_path.stem.replace("_coverage_cards", "")
            found_insurers.add(insurer)

        missing = set(EXPECTED_INSURERS) - found_insurers
        assert not missing, f"Missing coverage_cards for insurers: {missing}"

    def test_coverage_cards_parseable(self):
        """Verify all coverage_cards.jsonl files are valid JSON."""
        files = get_coverage_cards_files()
        assert len(files) > 0, "No coverage_cards.jsonl files found"

        for file_path in files:
            records = parse_jsonl(file_path)
            assert len(records) > 0, f"{file_path.name} is empty"

    def test_amount_status_field_exists(self):
        """Verify all cards have amount.status field."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            for i, record in enumerate(records):
                assert "amount" in record, \
                    f"{file_path.name} record {i}: missing 'amount' field"
                assert "status" in record["amount"], \
                    f"{file_path.name} record {i}: missing 'amount.status' field"

    def test_amount_status_values_valid(self):
        """Verify all amount.status values are in valid set."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            for i, record in enumerate(records):
                status = record.get("amount", {}).get("status")
                assert status in VALID_STATUSES, \
                    f"{file_path.name} record {i}: invalid status '{status}', expected one of {VALID_STATUSES}"

    def test_amount_status_distribution_reasonable(self):
        """Verify each insurer has at least some CONFIRMED amounts (sanity check)."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            confirmed_count = sum(
                1 for r in records
                if r.get("amount", {}).get("status") == "CONFIRMED"
            )
            total_count = len(records)

            # Sanity check: at least 1 CONFIRMED per insurer (may need adjustment)
            # This catches catastrophic extraction failures
            assert confirmed_count > 0, \
                f"{file_path.name}: 0 CONFIRMED amounts out of {total_count} total (possible extraction failure)"

    def test_coverage_name_canonical_exists(self):
        """Verify all cards have coverage_name_canonical field (needed for miss detection)."""
        files = get_coverage_cards_files()

        for file_path in files:
            records = parse_jsonl(file_path)
            for i, record in enumerate(records):
                assert "coverage_name_canonical" in record, \
                    f"{file_path.name} record {i}: missing 'coverage_name_canonical' field"

                # Allow null canonical name for unmatched coverages (out of scope)
                if record.get("mapping_status") == "unmatched":
                    continue

                assert record["coverage_name_canonical"], \
                    f"{file_path.name} record {i}: empty 'coverage_name_canonical' for matched coverage"
