#!/usr/bin/env python3
"""
STEP NEXT-50: DB Mapping Smoke Test

Gate: Verify DB mapping is not 0% (regression prevention)

This test ensures that the DB insurer code mapping (N13, not N11)
is correctly configured and DB coverages can be mapped.
"""

import json
import pytest
from pathlib import Path

from pipeline.step2_canonical_mapping.canonical_mapper import (
    CanonicalMapper,
    INSURER_CODE_MAP
)


def test_db_insurer_code_is_n13():
    """Gate 1: DB insurer code must be N13 (not N11)"""
    assert INSURER_CODE_MAP['db'] == 'N13', \
        "DB insurer code must be N13 (was N11 in bug)"


def test_db_canonical_mapping_exists():
    """Gate 2: Excel must contain DB (N13) mappings"""
    project_root = Path(__file__).resolve().parents[1]
    mapping_excel = project_root / 'data' / 'sources' / 'mapping' / '담보명mapping자료.xlsx'

    mapper = CanonicalMapper(mapping_excel)

    # Check DB mappings exist
    assert 'db' in mapper.insurer_mappings, "DB not found in insurer mappings"

    db_exact_map = mapper.insurer_mappings['db']['exact']
    db_normalized_map = mapper.insurer_mappings['db']['normalized']

    # Should have mappings
    assert len(db_exact_map) > 0, "DB has no exact mappings"
    assert len(db_normalized_map) > 0, "DB has no normalized mappings"


def test_db_key_coverages_mapping():
    """Gate 3: Key DB coverages must map correctly"""
    project_root = Path(__file__).resolve().parents[1]
    mapping_excel = project_root / 'data' / 'sources' / 'mapping' / '담보명mapping자료.xlsx'

    mapper = CanonicalMapper(mapping_excel)

    # Test key coverages (must exist in Excel)
    test_cases = [
        ('db', '상해사망', 'A1300', '상해사망'),
        ('db', '질병사망', 'A1100', '질병사망'),
        ('db', '상해후유장해(3-100%)', 'A3300_1', '상해후유장해(3-100%)'),
    ]

    for insurer, coverage_name, expected_code, expected_canonical in test_cases:
        code, canonical, method, confidence, evidence = mapper.map_coverage(
            insurer, coverage_name
        )

        assert code == expected_code, \
            f"Expected {coverage_name} → {expected_code}, got {code}"
        assert canonical == expected_canonical, \
            f"Expected canonical name {expected_canonical}, got {canonical}"
        assert method in ['exact', 'normalized'], \
            f"Expected exact/normalized mapping, got {method}"
        assert confidence > 0.0, \
            f"Expected confidence > 0, got {confidence}"


def test_db_mapping_rate_not_zero():
    """
    Gate 4: DB mapping rate must be > 0%

    Regression test for STEP NEXT-50 bug where DB had 0% mapping
    due to incorrect insurer code (N11 vs N13).
    """
    project_root = Path(__file__).resolve().parents[1]

    # Check if scope_v3 output exists
    db_canonical = project_root / 'data' / 'scope' / 'db_step2_canonical_scope_v1.jsonl'

    if not db_canonical.exists():
        pytest.skip("DB canonical scope not generated yet")

    # Count mapped vs unmapped
    total = 0
    mapped = 0

    with open(db_canonical, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            entry = json.loads(line)
            total += 1

            if entry.get('mapping_method') != 'unmapped':
                mapped += 1

    # Gate: Must have some mappings
    assert total > 0, "DB canonical scope is empty"
    assert mapped > 0, "DB has 0% mapping (regression bug)"

    mapping_rate = mapped / total * 100
    assert mapping_rate > 50.0, \
        f"DB mapping rate too low: {mapping_rate:.1f}% (expected > 50%)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
