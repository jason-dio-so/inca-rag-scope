#!/usr/bin/env python3
"""
Mock Amount Blocker Test
STEP NEXT-17-KB: Verification Gate

PURPOSE:
Ensure chat handlers do NOT use hardcoded mock amounts that invalidate E2E tests.

RATIONALE:
Mock amounts in handlers (e.g., text="1천만원") make all E2E verification meaningless.
This test FAILS if such mocks are detected, forcing proper integration with
AmountRepository/Step11 before any KB regression verification can be considered valid.

CRITICAL RULE:
If this test fails, ALL E2E test results are INVALID and must be ignored.
"""

import re
from pathlib import Path


def test_no_mock_amounts_in_chat_handlers():
    """
    BLOCKER: Fail if chat_handlers.py contains hardcoded mock amounts

    PATTERNS THAT SHOULD FAIL:
    - text="1천만원"  # Mock
    - text="3천만원"  # Mock
    - text="...만원"  # Mock (any hardcoded amount)
    - snippet="...: 1천만원"  # Mock

    ALLOWED:
    - Comments containing "Mock" are documented warnings (OK)
    - Actual integration with AmountRepository (future work)

    ENFORCEMENT:
    This test must PASS before any KB E2E results can be considered valid.
    """

    handler_file = Path("apps/api/chat_handlers.py")

    if not handler_file.exists():
        raise FileNotFoundError(f"Handler file not found: {handler_file}")

    content = handler_file.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Pattern: text="...만원" or snippet="...: ...만원"
    mock_patterns = [
        r'text\s*=\s*"[^"]*만원"',  # text="1천만원"
        r'snippet\s*=\s*"[^"]*:\s*[^"]*만원"',  # snippet="...: 1천만원"
    ]

    violations = []

    for i, line in enumerate(lines, 1):
        # Skip comment-only lines (documentation of mock status is OK)
        if line.strip().startswith('#'):
            continue

        for pattern in mock_patterns:
            if re.search(pattern, line):
                violations.append({
                    'line': i,
                    'text': line.strip(),
                    'pattern': pattern
                })

    # Build failure message
    if violations:
        msg_lines = [
            "\n" + "="*80,
            "CRITICAL: Mock amounts detected in chat_handlers.py",
            "="*80,
            "",
            "Mock amounts invalidate ALL E2E verification tests.",
            "Remove hardcoded amounts and integrate with AmountRepository.",
            "",
            "Violations found:",
            ""
        ]

        for v in violations:
            msg_lines.append(f"  Line {v['line']:4d}: {v['text']}")
            msg_lines.append(f"             Pattern: {v['pattern']}")
            msg_lines.append("")

        msg_lines.extend([
            "ACTION REQUIRED:",
            "1. Remove hardcoded text=\"...만원\" from handler code",
            "2. Integrate with AmountRepository to get real amounts",
            "3. Re-run this test to confirm fix",
            "",
            "IMPACT:",
            "- All KB E2E test results are INVALID until this is fixed",
            "- Type C verification cannot proceed",
            "- Amount display testing is meaningless",
            "="*80,
            ""
        ])

        raise AssertionError("\n".join(msg_lines))


def test_mock_comments_are_documented():
    """
    INFO: Document locations of "Mock" comments

    This test does NOT fail - it just lists where mock comments appear
    for awareness and future cleanup tracking.
    """

    handler_file = Path("apps/api/chat_handlers.py")
    content = handler_file.read_text(encoding='utf-8')
    lines = content.split('\n')

    mock_comment_lines = []

    for i, line in enumerate(lines, 1):
        if '# Mock' in line or 'Mock data' in line or 'Mock explanation' in line:
            mock_comment_lines.append((i, line.strip()))

    # Just print for awareness (not a failure)
    if mock_comment_lines:
        print(f"\nFound {len(mock_comment_lines)} mock-related comments:")
        for line_no, text in mock_comment_lines[:10]:  # Show first 10
            print(f"  Line {line_no:4d}: {text[:80]}")

        if len(mock_comment_lines) > 10:
            print(f"  ... and {len(mock_comment_lines) - 10} more")
