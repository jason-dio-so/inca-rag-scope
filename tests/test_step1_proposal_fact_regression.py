"""
STEP NEXT-44-β: Step1 Proposal Fact Regression Tests

Tests to prevent KB/Hyundai coverage name contamination from recurring.

Hard Gates:
1. KB: coverage_name_raw must not contain amount-only patterns
2. Hyundai: coverage_name_raw must not contain row number patterns
3. All insurers: coverage_name_raw must be valid (len >= 3, not number-only)
4. All records: evidences array must have length >= 1
"""

import json
import re
from pathlib import Path

import pytest

# STEP NEXT-44-β: Rejection patterns (from contract)
REJECT_PATTERNS = [
    r'^\d+\.?$',              # "10.", "11."
    r'^\d+\)$',               # "10)", "11)"
    r'^\d+(,\d{3})*(원|만원)?$',  # "3,000원", "3,000만원"
    r'^\d+만(원)?$',          # "10만", "10만원"
    r'^\d+[천백십](만)?원?$',  # "1천만원", "5백만원", "10만원"
    r'^[천백십만억]+원?$',    # "천원", "만원", "억원"
]


def load_step1_jsonl(insurer: str) -> list:
    """Load Step1 JSONL for given insurer"""
    base_dir = Path(__file__).parent.parent / "data" / "scope"
    jsonl_path = base_dir / f"{insurer}_step1_raw_scope.jsonl"

    if not jsonl_path.exists():
        pytest.skip(f"JSONL not found: {jsonl_path}")

    records = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def check_rejected_pattern(name: str) -> str:
    """Check if name matches any rejected pattern, return pattern if matched"""
    for pattern in REJECT_PATTERNS:
        if re.match(pattern, name.strip()):
            return pattern
    return None


class TestStep1ProposalFactRegression:
    """Regression tests for Step1 proposal fact extraction"""

    def test_kb_no_amount_patterns_in_coverage_names(self):
        """
        KB Hard Gate: coverage_name_raw must NOT be amount-only

        Regression: Before fix, KB had "1천만원", "10만원" as coverage names
        """
        records = load_step1_jsonl('kb')

        # Check first 20 (as per contract)
        sample_count = min(20, len(records))
        rejected = []

        for i in range(sample_count):
            name = records[i].get('coverage_name_raw', '')
            pattern = check_rejected_pattern(name)
            if pattern:
                rejected.append((name, pattern))

        assert len(rejected) == 0, (
            f"KB regression: Found {len(rejected)} rejected patterns in top 20:\n"
            + "\n".join(f"  - '{name}' matches {pattern}" for name, pattern in rejected)
        )

    def test_hyundai_no_row_numbers_in_coverage_names(self):
        """
        Hyundai Hard Gate: coverage_name_raw must NOT be row numbers like "10."

        Regression: Before fix, Hyundai had "10.", "11." as coverage names
        """
        records = load_step1_jsonl('hyundai')

        # Check first 20 (as per contract)
        sample_count = min(20, len(records))
        rejected = []

        for i in range(sample_count):
            name = records[i].get('coverage_name_raw', '')
            # Specifically check row number patterns
            if re.match(r'^\d+\.?$', name.strip()):
                rejected.append(name)

        assert len(rejected) == 0, (
            f"Hyundai regression: Found {len(rejected)} row number patterns in top 20:\n"
            + "\n".join(f"  - '{name}'" for name in rejected)
        )

    @pytest.mark.parametrize("insurer", [
        'samsung', 'meritz', 'kb', 'db', 'hanwha', 'heungkuk', 'hyundai', 'lotte'
    ])
    def test_all_insurers_no_rejected_patterns(self, insurer):
        """
        All insurers: coverage_name_raw must not match ANY rejected pattern

        Hard Gate: 0 rejected patterns across all 8 insurers
        """
        records = load_step1_jsonl(insurer)

        # Check ALL records (not just top 20)
        rejected = []
        for record in records:
            name = record.get('coverage_name_raw', '')
            pattern = check_rejected_pattern(name)
            if pattern:
                rejected.append((name, pattern))

        assert len(rejected) == 0, (
            f"{insurer} has {len(rejected)} rejected patterns:\n"
            + "\n".join(f"  - '{name}' matches {pattern}" for name, pattern in rejected[:5])
        )

    @pytest.mark.parametrize("insurer", [
        'samsung', 'meritz', 'kb', 'db', 'hanwha', 'heungkuk', 'hyundai', 'lotte'
    ])
    def test_all_insurers_evidences_required(self, insurer):
        """
        All insurers: Every record must have at least 1 evidence

        Hard Gate: evidences array length >= 1
        """
        records = load_step1_jsonl(insurer)

        missing_evidence = []
        for i, record in enumerate(records):
            evidences = record.get('proposal_facts', {}).get('evidences', [])
            if not isinstance(evidences, list) or len(evidences) == 0:
                coverage_name = record.get('coverage_name_raw', 'UNKNOWN')
                missing_evidence.append((i, coverage_name))

        assert len(missing_evidence) == 0, (
            f"{insurer} has {len(missing_evidence)} records without evidences:\n"
            + "\n".join(f"  - [{i}] {name}" for i, name in missing_evidence[:5])
        )

    @pytest.mark.parametrize("insurer", [
        'samsung', 'meritz', 'kb', 'db', 'hanwha', 'heungkuk', 'hyundai', 'lotte'
    ])
    def test_all_insurers_coverage_name_valid(self, insurer):
        """
        All insurers: coverage_name_raw must be valid (len >= 3, not empty)
        """
        records = load_step1_jsonl(insurer)

        invalid_names = []
        for i, record in enumerate(records):
            name = record.get('coverage_name_raw', '')
            if len(name) < 3:
                invalid_names.append((i, name))

        assert len(invalid_names) == 0, (
            f"{insurer} has {len(invalid_names)} invalid coverage names:\n"
            + "\n".join(f"  - [{i}] '{name}' (len={len(name)})" for i, name in invalid_names[:5])
        )

    @pytest.mark.parametrize("insurer", [
        'samsung', 'meritz', 'kb', 'db', 'hanwha', 'heungkuk', 'hyundai', 'lotte'
    ])
    def test_all_insurers_schema_compliance(self, insurer):
        """
        All insurers: JSONL records must conform to STEP NEXT-44-β contract schema
        """
        records = load_step1_jsonl(insurer)

        schema_violations = []
        for i, record in enumerate(records):
            # Check required fields
            if 'insurer' not in record:
                schema_violations.append((i, 'missing insurer'))
            if 'coverage_name_raw' not in record:
                schema_violations.append((i, 'missing coverage_name_raw'))
            if 'proposal_facts' not in record:
                schema_violations.append((i, 'missing proposal_facts'))

            # Check proposal_facts structure
            pf = record.get('proposal_facts', {})
            if 'evidences' not in pf:
                schema_violations.append((i, 'missing proposal_facts.evidences'))
            elif not isinstance(pf['evidences'], list):
                schema_violations.append((i, 'proposal_facts.evidences is not array'))

            # Check evidence structure
            for ev_idx, ev in enumerate(pf.get('evidences', [])):
                if not isinstance(ev, dict):
                    schema_violations.append((i, f'evidence[{ev_idx}] is not object'))
                elif 'doc_type' not in ev:
                    schema_violations.append((i, f'evidence[{ev_idx}] missing doc_type'))
                elif 'page' not in ev:
                    schema_violations.append((i, f'evidence[{ev_idx}] missing page'))
                elif 'snippet' not in ev:
                    schema_violations.append((i, f'evidence[{ev_idx}] missing snippet'))

        assert len(schema_violations) == 0, (
            f"{insurer} has {len(schema_violations)} schema violations:\n"
            + "\n".join(f"  - [{i}] {msg}" for i, msg in schema_violations[:10])
        )


class TestStep1ProposalFactQuality:
    """Quality checks for Step1 proposal facts (soft metrics, not hard gates)"""

    @pytest.mark.parametrize("insurer", [
        'samsung', 'meritz', 'kb', 'db', 'hanwha', 'heungkuk', 'hyundai', 'lotte'
    ])
    def test_coverage_amount_fill_rate(self, insurer):
        """
        Soft metric: coverage_amount_text fill rate should be > 70%

        Note: This is NOT a hard gate, just a quality indicator
        """
        records = load_step1_jsonl(insurer)

        filled_count = sum(
            1 for r in records
            if r.get('proposal_facts', {}).get('coverage_amount_text')
        )
        fill_rate = filled_count / len(records) if records else 0

        # Log for visibility (not a hard assertion)
        print(f"\n{insurer} coverage_amount fill rate: {fill_rate:.1%} ({filled_count}/{len(records)})")

        # Soft assertion: warn if < 70% but don't fail
        if fill_rate < 0.7:
            pytest.skip(f"{insurer} coverage_amount fill rate {fill_rate:.1%} < 70% (may be PDF structure issue)")
