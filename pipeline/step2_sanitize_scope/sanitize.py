#!/usr/bin/env python3
"""
STEP NEXT-59: Step2 Sanitization Logic (Premium Waiver Tagging)
================================================================

Deterministic pattern-based sanitization of raw Step1 extraction.

Rules (ANY match → DROP):
    1. Fragment patterns (parentheses-only, trailing markers)
    2. Sentence-like noise (conditions, explanations)
    3. Duplicate variants (keep first occurrence only)

STEP NEXT-59: Premium Waiver items are KEPT + TAGGED (NOT dropped)
    - KEEP: 납입면제 items are core comparison axis
    - TAG: coverage_kind="premium_waiver", coverage_axis=["waiver"]

Constitutional enforcement:
    - NO LLM / NO inference
    - Pattern matching only
    - Audit trail required
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


# DROP patterns (ANY match → DROP row)
DROP_PATTERNS = [
    # Category 1: Fragment Detection (STEP NEXT-52: Added broken fragments)
    (r'^\)\(', 'BROKEN_PREFIX'),  # Starts with )(
    (r'^신형\)담보$', 'BROKEN_SUFFIX'),  # Exactly "신형)담보"
    (r'^\)\(갱신형\)담보', 'BROKEN_RENEWAL'),  # Starts with )(갱신형)담보
    (r'^\([^)]+\)$', 'PARENTHESES_ONLY'),
    (r'(인|한)\s*경우$', 'TRAILING_CLAUSE_CASE'),
    (r'일\s*때$', 'TRAILING_CLAUSE_WHEN'),
    (r'시$', 'TRAILING_CLAUSE_TIME'),
    (r'(으로|로)\s*진단확정된', 'CONDITION_FRAGMENT'),

    # Category 1b: STEP NEXT-60-H Broken Fragment Rules (General, NOT Hyundai-specific)
    (r'^\(?갱신형\)?담보$', 'BROKEN_RENEWAL_담보'),  # (갱신형)담보, 갱신형담보
    (r'^담보명$', 'COLUMN_HEADER_담보명'),  # Table header remnant
    (r'^\d+\.?\d*$', 'STANDALONE_NUMBER'),  # Pure numbers (5, 91.5, etc.)
    (r'^[가-힣](\s+[가-힣])+(\s+[가-힣\(%)]*)*$', 'FRAGMENTED_HANGUL'),  # "남 자", "보 험 가 격 지 수 (%)"
    (r'^갱신차수$', 'ADMIN_FIELD_갱신차수'),  # Administrative field
    (r'^\)담보$', 'BROKEN_CLOSING_담보'),  # Just ")담보"
    (r'^[료초][\d회한]*[(\)]', 'BROKEN_FRAGMENT_료초'),  # "료(연간...", "초1회한)" - fragments
    (r'^\d+회한[(\)]', 'BROKEN_FRAGMENT_회한'),  # "1회한)(갱신형)..." - fragments

    # Category 2: Sentence-like Noise
    (r'지급\s*(조건|사유|내용)', 'PAYMENT_EXPLANATION'),
    (r'보장\s*(개시일|내용)', 'COVERAGE_EXPLANATION'),
    (r'이후에$', 'SENTENCE_MARKER'),
    (r'경우$', 'SENTENCE_ENDING'),

    # Category 3: Administrative Non-Coverage
    # STEP NEXT-59: REMOVED PREMIUM_WAIVER_TARGET (now tagged, not dropped)
    # (r'납입면제.*대상', 'PREMIUM_WAIVER_TARGET'),  # DISABLED - premium waiver is core coverage
    # (r'대상\s*(담보|보장)', 'META_ENTRY'),  # DISABLED - too broad, affects premium waiver
]

# NORMALIZATION patterns (STEP NEXT-52: Transform but don't drop)
NORMALIZATION_PATTERNS = [
    # STEP NEXT-60-H: Remove embedded newlines (PDF table extraction artifact)
    # "표적항암약물허가치료(갱신형\n)담보" → "표적항암약물허가치료(갱신형)담보"
    (r'\n', '', 'EMBEDDED_NEWLINE'),

    # STEP NEXT-59C: Numeric prefix with punctuation (DB/Hyundai/KB pattern)
    # MUST be first to catch "1.", "2)", "3-" before other patterns
    # "1. 상해사망" → "상해사망"
    # "3) 질병사망" → "질병사망"
    # "4- 후유장해" → "후유장해"
    (r'^\s*\d+\s*[.)]\s*', '', 'NUMERIC_PREFIX_DOT_PAREN'),
    (r'^\s*\d+\s*[-–—]\s*', '', 'NUMERIC_PREFIX_DASH'),

    # STEP NEXT-55: Leading markers removal
    # ". 상해사망" → "상해사망"
    # "• 질병사망" → "질병사망"
    (r'^\s*[·•]+\s*', '', 'LEADING_BULLET_MARKER'),
    (r'^\s*\.+\s*', '', 'LEADING_DOT_MARKER'),
    (r'^\s*\(\d+\)\s*', '', 'LEADING_PAREN_NUMBER'),
    (r'^\s*\d+\)\s*', '', 'LEADING_NUMBER_PAREN'),
    (r'^\s*[A-Za-z]\.\s*', '', 'LEADING_ALPHA_DOT'),

    # Leading number prefix (Meritz, Lotte pattern)
    # "155 뇌졸중진단비" → "뇌졸중진단비"
    (r'^\s*\d+\s+', '', 'LEADING_NUMBER_PREFIX'),

    # Sub-item marker (Hanwha pattern)
    # "- 4대유사암진단비" → "4대유사암진단비"
    (r'^\s*-\s+', '', 'SUB_ITEM_MARKER'),
]

# Coverage keywords (used for long-text detection)
COVERAGE_KEYWORDS = [
    '진단비', '수술비', '입원비', '통원비', '치료비',
    '사망', '후유장해', '골절', '화상', '암',
    '뇌', '심장', '간', '신장', '폐'
]


def detect_premium_waiver(coverage_name_raw: str, coverage_name_normalized: str) -> Tuple[bool, List[str]]:
    """
    Detect premium waiver coverage items (STEP NEXT-59).

    Premium waiver items are CORE coverage (NOT administrative noise).
    Detection is deterministic keyword matching (NO LLM).

    Args:
        coverage_name_raw: Raw coverage name
        coverage_name_normalized: Normalized coverage name

    Returns:
        (is_premium_waiver, matched_rules)
    """
    # Detection keywords (OR logic)
    WAIVER_KEYWORDS = [
        '납입면제',
        '보험료납입면제',
        '보험료 납입면제',
    ]

    matched_rules = []

    # Check both raw and normalized names
    for text in [coverage_name_raw, coverage_name_normalized]:
        for keyword in WAIVER_KEYWORDS:
            if keyword in text:
                matched_rules.append(f"WAIVER_KEYWORD_{keyword}")
                break

    is_waiver = len(matched_rules) > 0
    return is_waiver, matched_rules


def normalize_coverage_name(coverage_name_raw: str) -> Tuple[str, List[str]]:
    """
    Normalize coverage name (remove prefixes/markers but preserve meaning).

    STEP NEXT-52: Apply deterministic transformations.

    Args:
        coverage_name_raw: Raw coverage name from Step1

    Returns:
        (normalized_name, applied_transformations)
    """
    normalized = coverage_name_raw
    transformations = []

    for pattern, replacement, transform_name in NORMALIZATION_PATTERNS:
        if re.search(pattern, normalized):
            normalized = re.sub(pattern, replacement, normalized)
            transformations.append(transform_name)

    return normalized.strip(), transformations


def should_drop_entry(coverage_name_raw: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if entry should be dropped.

    Args:
        coverage_name_raw: Coverage name from Step1 extraction

    Returns:
        (should_drop, drop_reason)
    """
    # Rule 1: Check DROP patterns
    for pattern, reason in DROP_PATTERNS:
        if re.search(pattern, coverage_name_raw):
            return True, reason

    # Rule 2: Long text without coverage keywords (likely noise)
    if len(coverage_name_raw) > 40:
        has_keyword = any(kw in coverage_name_raw for kw in COVERAGE_KEYWORDS)
        if not has_keyword:
            return True, 'LONG_TEXT_NO_KEYWORDS'

    # Rule 3: Empty or whitespace-only
    if not coverage_name_raw.strip():
        return True, 'EMPTY_TEXT'

    return False, None


def deduplicate_variants(entries: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Remove duplicate variants (keep first occurrence only).

    STEP NEXT-52: Enhanced to use normalized names for deduplication.
    STEP NEXT-70: Enhanced to merge proposal_detail_facts when encountering duplicates.

    Handles:
        - DB: under40 vs over41
        - Lotte: male vs female
        - Prefix variations: "155 뇌졸중진단비" vs "뇌졸중진단비"
        - KB: Merge DETAIL from variant signatures (pages 5-6) into summary (pages 2-3)

    Args:
        entries: List of sanitized entries

    Returns:
        (kept_entries, dropped_duplicates)
    """
    seen_normalized_names = {}  # normalized_name → first occurrence
    kept = []
    dropped = []

    for entry in entries:
        coverage_name_raw = entry['coverage_name_raw']

        # Use normalized name for dedup key
        # STEP NEXT-52: normalization_applied field already added in main sanitize loop
        normalized_name = entry.get('coverage_name_normalized', coverage_name_raw)

        if normalized_name in seen_normalized_names:
            # STEP NEXT-70: Merge proposal_detail_facts if current entry has it but first doesn't
            first_entry = seen_normalized_names[normalized_name]
            current_has_detail = entry.get('proposal_detail_facts') is not None
            first_has_detail = first_entry.get('proposal_detail_facts') is not None

            if current_has_detail and not first_has_detail:
                # Current entry has DETAIL but first doesn't - merge it
                first_entry['proposal_detail_facts'] = entry['proposal_detail_facts']

            # Duplicate variant - drop current entry
            dropped.append({
                **entry,
                'sanitized': False,
                'drop_reason': 'DUPLICATE_VARIANT',
                'duplicate_of': first_entry['coverage_name_raw']
            })
        else:
            seen_normalized_names[normalized_name] = entry
            kept.append(entry)

    return kept, dropped


def sanitize_step1_output(
    input_jsonl: Path,
    output_jsonl: Path,
    dropped_jsonl: Path
) -> Dict:
    """
    Sanitize Step1 raw extraction output.

    Args:
        input_jsonl: Input Step1 raw scope JSONL
        output_jsonl: Output sanitized JSONL
        dropped_jsonl: Dropped entries audit trail

    Returns:
        Statistics dict
    """
    if not input_jsonl.exists():
        return {'error': 'FILE_NOT_FOUND'}

    # Read input
    entries = []
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            o = json.loads(line)

            # --- STEP NEXT-XX: Step1 raw compatibility fix ---
            # Some Step1 raw outputs (e.g. SAMSUNG) do not provide `coverage_name`
            # Step2 sanitize assumes `coverage_name` is the primary key
            if not o.get("coverage_name"):
                raw = (o.get("coverage_name_raw") or "").strip()
                o["coverage_name"] = raw if raw else None
            # ------------------------------------------------

            entries.append(o)
    # Sanitize
    kept_entries = []
    dropped_entries = []
    normalization_stats = {
        'applied_count': 0,  # Rows where normalization was applied
        'not_applied_count': 0  # Rows where no normalization was needed
    }

    for entry in entries:
        coverage_name_raw = entry.get('coverage_name_raw', '')

        # Apply normalization FIRST (needed for waiver detection)
        normalized_name, transformations = normalize_coverage_name(coverage_name_raw)

        # STEP NEXT-59: Detect premium waiver items (BEFORE drop check)
        is_premium_waiver, waiver_rules = detect_premium_waiver(coverage_name_raw, normalized_name)

        # Check if should drop (fragments, noise, etc.)
        should_drop, drop_reason = should_drop_entry(coverage_name_raw)

        # STEP NEXT-59: Premium waiver items NEVER dropped (override drop decision)
        if is_premium_waiver:
            should_drop = False
            drop_reason = None

        if should_drop:
            dropped_entries.append({
                **entry,
                'sanitized': False,
                'drop_reason': drop_reason
            })
        else:
            # STEP NEXT-59C: Track normalization execution
            if transformations:
                normalization_stats['applied_count'] += 1
            else:
                normalization_stats['not_applied_count'] += 1

            # Check if normalization resulted in empty string
            if not normalized_name:
                dropped_entries.append({
                    **entry,
                    'sanitized': False,
                    'drop_reason': 'NORMALIZED_TO_EMPTY',
                    'normalization_applied': transformations
                })
                continue

            # Build kept entry with normalization metadata
            kept_entry = {
                **entry,
                'coverage_name_normalized': normalized_name,
                'normalization_applied': transformations,
                'sanitized': True,
                'drop_reason': None
            }

            # STEP NEXT-59: Add premium waiver tags if detected
            if is_premium_waiver:
                kept_entry['coverage_kind'] = 'premium_waiver'
                kept_entry['coverage_axis'] = ['waiver']
                kept_entry['waiver_detected'] = True
                kept_entry['waiver_rule_hits'] = waiver_rules

            kept_entries.append(kept_entry)

    # Deduplicate variants
    kept_entries, variant_duplicates = deduplicate_variants(kept_entries)
    dropped_entries.extend(variant_duplicates)

    # Write sanitized output
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for entry in kept_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # Write dropped entries audit trail
    dropped_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(dropped_jsonl, 'w', encoding='utf-8') as f:
        for entry in dropped_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # Statistics
    drop_reason_counts = {}
    for entry in dropped_entries:
        reason = entry['drop_reason']
        drop_reason_counts[reason] = drop_reason_counts.get(reason, 0) + 1

    # STEP NEXT-59C: Include normalization execution stats
    return {
        'input_total': len(entries),
        'kept': len(kept_entries),
        'dropped': len(dropped_entries),
        'drop_reason_counts': drop_reason_counts,
        'dropped_entries': dropped_entries,
        'normalization_applied_rows': normalization_stats['applied_count'],
        'normalization_not_applied_rows': normalization_stats['not_applied_count'],
        'normalization_rate': normalization_stats['applied_count'] / (normalization_stats['applied_count'] + normalization_stats['not_applied_count']) if (normalization_stats['applied_count'] + normalization_stats['not_applied_count']) > 0 else 0.0
    }


def verify_sanitized_output(jsonl_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify sanitized output has no contamination.

    Hard-coded failure patterns (should NEVER appear in sanitized output):
        - 진단확정된 경우
        - 인 경우
        - 일 때
        - Parentheses-only

    Args:
        jsonl_path: Path to sanitized JSONL

    Returns:
        (is_clean, violations)
    """
    if not jsonl_path.exists():
        return False, ['FILE_NOT_FOUND']

    violations = []

    FAILURE_PATTERNS = [
        r'진단확정된\s*경우',
        r'(인|한)\s*경우$',
        r'일\s*때$',
        r'^\([^)]+\)$'
    ]

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            entry = json.loads(line)
            coverage_name = entry.get('coverage_name_raw', '')

            for pattern in FAILURE_PATTERNS:
                if re.search(pattern, coverage_name):
                    violations.append(f"Line {line_num}: {coverage_name}")
                    break

    return len(violations) == 0, violations
