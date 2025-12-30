"""
STEP NEXT-17B/17C: Step7 Miss Candidates Regression Test

Tracks known miss candidates (UNCONFIRMED with PDF evidence) as XFAIL.
When Step7 extraction is improved, these tests should transition to PASS.

TRIAGE RESULTS (STEP NEXT-17C):
- 15/57 candidates triaged (hyundai: 5, kb: 5, lotte: 5)
- TRUE_MISS_TABLE: 3 confirmed (hyundai: 1, kb: 2, lotte: 0)
- FALSE_POSITIVE: 10 (amount belongs to different coverage)
- NAME_MISMATCH: 2 (coverage name normalization issues)

CONFIRMED TARGETS FOR STEP7 FIX:
1. hyundai/상해사망 - Page 2 - Issue: parenthesized name "기본계약(상해사망)"
2. kb/뇌혈관질환수술비 - Page 3 - Issue: number prefix "209 뇌혈관질환수술비"
3. kb/허혈성심장질환수술비 - Page 3 - Issue: number prefix "213 허혈성심장질환수술비"

See: docs/audit/STEP7_MISS_TRIAGE_STEP17C.md
     docs/audit/STEP7_MISS_TARGETS.md
"""

import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
COMPARE_DIR = PROJECT_ROOT / "data" / "compare"
MISS_CANDIDATES_REPORT = PROJECT_ROOT / "docs" / "audit" / "STEP7_MISS_CANDIDATES.md"


def load_coverage_cards(insurer: str):
    """Load coverage cards for a given insurer."""
    path = COMPARE_DIR / f"{insurer}_coverage_cards.jsonl"
    if not path.exists():
        return []

    cards = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cards.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return cards


def parse_miss_candidates():
    """
    Parse STEP7_MISS_CANDIDATES.md to extract candidate list.
    Returns: [(insurer, coverage_canonical, status), ...]
    """
    if not MISS_CANDIDATES_REPORT.exists():
        return []

    candidates = []
    current_insurer = None
    current_coverage = None
    current_status = None

    with open(MISS_CANDIDATES_REPORT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- **Insurer**:"):
                current_insurer = line.split(":", 1)[1].strip()
            elif line.startswith("- **Coverage**:"):
                current_coverage = line.split(":", 1)[1].strip()
            elif line.startswith("- **Status**:"):
                current_status = line.split(":", 1)[1].strip()
            elif line.startswith("- **Label**: MISS_CANDIDATE"):
                if current_insurer and current_coverage and current_status:
                    candidates.append((current_insurer, current_coverage, current_status))
                current_insurer = None
                current_coverage = None
                current_status = None

    return candidates


# Load miss candidates at module level
MISS_CANDIDATES = parse_miss_candidates()


class TestStep7MissCandidatesRegression:
    """
    Regression tests for Step7 miss candidates.

    Each candidate is tracked as an XFAIL test. When Step7 extraction is improved,
    these tests should start passing (status changes from UNCONFIRMED to CONFIRMED).
    """

    @pytest.mark.parametrize("insurer,coverage_canonical,expected_status", MISS_CANDIDATES)
    @pytest.mark.xfail(reason="Known Step7 miss candidate - awaiting Step7 extraction improvement", strict=False)
    def test_miss_candidate_should_be_confirmed(self, insurer, coverage_canonical, expected_status):
        """
        Test that a known miss candidate eventually gets CONFIRMED status.

        This test is XFAIL by default, meaning we expect it to fail (status == UNCONFIRMED).
        When Step7 extraction is fixed, this test will pass (status == CONFIRMED),
        which will be reported as an unexpected pass (XPASS), signaling improvement.
        """
        cards = load_coverage_cards(insurer)

        # Find the card for this coverage
        matching_card = None
        for card in cards:
            if card.get("coverage_name_canonical") == coverage_canonical:
                matching_card = card
                break

        assert matching_card is not None, \
            f"Coverage '{coverage_canonical}' not found in {insurer}_coverage_cards.jsonl"

        actual_status = matching_card.get("amount", {}).get("status")

        # This assertion SHOULD fail now (UNCONFIRMED), but pass after Step7 fix (CONFIRMED)
        assert actual_status == "CONFIRMED", \
            f"{insurer}/{coverage_canonical}: Expected CONFIRMED, got {actual_status}"

    def test_miss_candidates_report_exists(self):
        """Sanity check: miss candidates report should exist."""
        assert MISS_CANDIDATES_REPORT.exists(), \
            "STEP7_MISS_CANDIDATES.md not found - run audit script first"

    def test_miss_candidates_not_empty(self):
        """Sanity check: we should have at least some miss candidates."""
        assert len(MISS_CANDIDATES) > 0, \
            "No miss candidates found - this may indicate detection logic failure"

    def test_miss_candidates_structure_valid(self):
        """Sanity check: all candidates have required fields."""
        for insurer, coverage, status in MISS_CANDIDATES:
            assert insurer, "Missing insurer in candidate"
            assert coverage, "Missing coverage in candidate"
            assert status == "UNCONFIRMED", f"Candidate should have UNCONFIRMED status, got {status}"

    def test_miss_candidates_coverage_exists_in_cards(self):
        """Verify all miss candidates actually exist in coverage_cards.jsonl."""
        for insurer, coverage_canonical, _ in MISS_CANDIDATES:
            cards = load_coverage_cards(insurer)
            found = any(
                card.get("coverage_name_canonical") == coverage_canonical
                for card in cards
            )
            assert found, \
                f"Miss candidate {insurer}/{coverage_canonical} not found in coverage_cards.jsonl"


class TestStep7MissDetectionSmoke:
    """Smoke tests for miss detection logic (non-regression)."""

    def test_unconfirmed_status_exists_in_dataset(self):
        """Verify UNCONFIRMED status appears in at least one insurer (otherwise miss detection is moot)."""
        insurers = ["samsung", "meritz", "db", "hanwha", "hyundai", "kb", "heungkuk", "lotte"]
        total_unconfirmed = 0

        for insurer in insurers:
            cards = load_coverage_cards(insurer)
            unconfirmed_count = sum(
                1 for card in cards
                if card.get("amount", {}).get("status") == "UNCONFIRMED"
            )
            total_unconfirmed += unconfirmed_count

        assert total_unconfirmed > 0, \
            "No UNCONFIRMED amounts found across all insurers - miss detection cannot function"

    def test_miss_candidates_are_subset_of_unconfirmed(self):
        """Miss candidates should be a subset of all UNCONFIRMED cases."""
        all_unconfirmed = set()

        insurers = ["samsung", "meritz", "db", "hanwha", "hyundai", "kb", "heungkuk", "lotte"]
        for insurer in insurers:
            cards = load_coverage_cards(insurer)
            for card in cards:
                if card.get("amount", {}).get("status") == "UNCONFIRMED":
                    coverage = card.get("coverage_name_canonical")
                    if coverage:
                        all_unconfirmed.add((insurer, coverage))

        miss_set = set((ins, cov) for ins, cov, _ in MISS_CANDIDATES)

        # Miss candidates should be subset (or equal)
        assert miss_set.issubset(all_unconfirmed), \
            f"Miss candidates contain items not in UNCONFIRMED set: {miss_set - all_unconfirmed}"
