#!/usr/bin/env python3
"""
STEP NEXT-72: Auto-Triage Unanchored Backlog (NO LLM)

Deterministically classify 62 unanchored coverage items into:
- LIKELY_ALIAS: Can be mapped to existing coverage_code
- LIKELY_INTENTIONAL: Headers/metadata that should stay unmapped
- LIKELY_NEW_CANONICAL: New coverage requiring canonical code creation
- NEEDS_HUMAN: Requires manual review

NO LLM / NO INFERENCE - purely deterministic rules.
"""

import pandas as pd
import re
from typing import List, Tuple, Dict, Set
from pathlib import Path


# ============================================================================
# Normalization (deterministic)
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Deterministic normalization for matching:
    - Remove spaces
    - Remove special characters (except Korean/alphanumeric)
    - Lowercase
    - Remove parentheses content
    - Remove numeric prefixes
    """
    if pd.isna(text):
        return ""

    # Remove numeric prefixes like "10. ", "206. "
    text = re.sub(r'^\d+\.\s*', '', str(text))

    # Remove content in parentheses
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Remove special characters except Korean and alphanumeric
    text = re.sub(r'[^\w가-힣]', '', text)

    # Lowercase
    text = text.lower()

    return text.strip()


def tokenize(text: str) -> Set[str]:
    """Simple tokenization: split on common boundaries"""
    normalized = normalize_text(text)
    # Split on transitions between hangul and alphanumeric
    tokens = set()
    current = []

    for char in normalized:
        if char.isalnum() or '\uac00' <= char <= '\ud7a3':  # Korean syllables
            current.append(char)
        elif current:
            tokens.add(''.join(current))
            current = []

    if current:
        tokens.add(''.join(current))

    return tokens


# ============================================================================
# Rule-based classification
# ============================================================================

# A) LIKELY_INTENTIONAL keywords (headers/metadata)
INTENTIONAL_KEYWORDS = {
    # Headers/column names
    '담보명', '보장명', '가입금액', '보험료', '납입기간', '보험기간',
    '기준', '합계', '계', '구분', '담보', '보장',

    # Metadata/explanatory text
    '예시', '대표계약', '기본계약', '보험료비교', '자동갱신특약',
    '갱신차수', '남자', '여자', '세', '만기', '월납', '년납',

    # Numeric/symbolic only patterns handled separately
}

# B) LIKELY_ALIAS keywords (core coverage concepts)
ALIAS_KEYWORDS = {
    # Disease/injury core concepts
    '사망', '후유장해', '진단비', '수술비', '입원일당', '치료비',
    '암', '뇌', '심장', '혈관', '골절', '화상', '배상',
    '질병', '상해', '간병', '장해', '장애',

    # Cancer types
    '갑상선암', '전립선암', '유사암', '일반암',

    # Heart/brain
    '뇌경색', '뇌출혈', '심근경색', '허혈성', '심혈관',

    # Body parts
    '치아', '골절', '척추', '관절',
}

# C) LIKELY_NEW_CANONICAL keywords (very specific/new treatments)
NEW_CANONICAL_KEYWORDS = {
    'cart', 'car-t', '카티',
    '표적항암', '다빈치', '로봇수술', '혈전용해',
    '대동맥판막협착증', '심근병증', '부정맥',
    '항암약물', '호르몬약물', '허가치료',
    'i49', 'i63', 'i21',
}


def is_likely_intentional(coverage_name: str) -> Tuple[bool, List[str]]:
    """Check if coverage name is likely intentional unmapped (header/metadata)"""
    reasons = []

    if pd.isna(coverage_name) or not coverage_name.strip():
        reasons.append("EMPTY")
        return True, reasons

    text = str(coverage_name).strip()
    normalized = normalize_text(text)

    # Check for purely numeric or symbolic
    if re.match(r'^[\d\.\,\s]+$', text):
        reasons.append("NUMERIC_ONLY")
        return True, reasons

    if re.match(r'^[\(\)\[\]\-\s]+$', text):
        reasons.append("SYMBOLIC_ONLY")
        return True, reasons

    # Check for very short (likely fragment)
    if len(normalized) <= 3:
        reasons.append("TOO_SHORT")
        return True, reasons

    # Check for intentional keywords
    for keyword in INTENTIONAL_KEYWORDS:
        if keyword in text:
            reasons.append(f"INTENTIONAL_KEYWORD:{keyword}")

    # Check for "보험료 비교", "대표계약 기준" patterns
    if '보험료' in text and '비교' in text:
        reasons.append("PREMIUM_COMPARISON")
        return True, reasons

    if '기준' in text and ('대표계약' in text or '계약' in text):
        reasons.append("CONTRACT_REFERENCE")
        return True, reasons

    # Check if it contains "자동갱신특약" (renewal notice)
    if '자동갱신' in text and '특약' in text:
        reasons.append("AUTO_RENEWAL_NOTICE")
        return True, reasons

    # If multiple intentional keywords found
    if len(reasons) >= 2:
        return True, reasons

    return len(reasons) > 0, reasons


def is_likely_new_canonical(coverage_name: str) -> Tuple[bool, List[str]]:
    """Check if coverage name likely requires new canonical code"""
    reasons = []
    normalized = normalize_text(coverage_name)
    lower_text = str(coverage_name).lower()

    # Check for new treatment keywords
    for keyword in NEW_CANONICAL_KEYWORDS:
        if keyword in lower_text or keyword in normalized:
            reasons.append(f"NEW_TREATMENT:{keyword}")

    return len(reasons) > 0, reasons


def has_alias_keywords(coverage_name: str) -> Tuple[bool, List[str]]:
    """Check if coverage name has core insurance coverage keywords"""
    reasons = []
    normalized = normalize_text(coverage_name)

    for keyword in ALIAS_KEYWORDS:
        if keyword in coverage_name or keyword in normalized:
            reasons.append(f"ALIAS_KEYWORD:{keyword}")

    return len(reasons) > 0, reasons


# ============================================================================
# Candidate code matching (deterministic)
# ============================================================================

def compute_token_overlap(query: str, target: str) -> float:
    """Compute token overlap score (Jaccard similarity)"""
    query_tokens = tokenize(query)
    target_tokens = tokenize(target)

    if not query_tokens or not target_tokens:
        return 0.0

    intersection = query_tokens & target_tokens
    union = query_tokens | target_tokens

    return len(intersection) / len(union) if union else 0.0


def compute_contains_score(query: str, target: str) -> float:
    """Check if query is contained in target or vice versa"""
    query_norm = normalize_text(query)
    target_norm = normalize_text(target)

    if not query_norm or not target_norm:
        return 0.0

    if query_norm in target_norm:
        return 0.8
    if target_norm in query_norm:
        return 0.7

    return 0.0


def compute_prefix_score(query: str, target: str) -> float:
    """Check for prefix match"""
    query_norm = normalize_text(query)
    target_norm = normalize_text(target)

    if not query_norm or not target_norm:
        return 0.0

    min_len = min(len(query_norm), len(target_norm))
    if min_len < 3:
        return 0.0

    # Check first N characters
    for n in range(min_len, 2, -1):
        if query_norm[:n] == target_norm[:n]:
            return 0.5 * (n / min_len)

    return 0.0


def find_candidate_codes(coverage_name: str, excel_df: pd.DataFrame, insurer_key: str, top_n: int = 5) -> List[Dict]:
    """
    Find candidate coverage codes from Excel using deterministic matching.

    Returns list of dicts:
    {
        'cre_cvr_cd': code,
        'coverage_name': 신정원코드명 or 담보명,
        'similarity_score': float,
        'match_type': str
    }
    """
    candidates = []

    # Map insurer_key to ins_cd
    insurer_map = {
        'samsung': 'N08',
        'hanwha': 'N02',
        'heungkuk': 'N05',
        'hyundai': 'N06',
        'kb': 'N07',
        'meritz': 'N01',
        'db': 'N09',
        'lotte': 'N03',
    }

    ins_cd = insurer_map.get(insurer_key)

    # Search both 신정원코드명 (canonical) and 담보명(가입설계서) (alias)
    for idx, row in excel_df.iterrows():
        # Skip if different insurer (but still search across all for fallback)
        row_ins_cd = row.get('ins_cd', '')

        canonical_name = row.get('신정원코드명', '')
        alias_name = row.get('담보명(가입설계서)', '')
        code = row.get('cre_cvr_cd', '')

        if pd.isna(code) or not code:
            continue

        # Score against canonical name
        for target_name, name_type in [(canonical_name, 'canonical'), (alias_name, 'alias')]:
            if pd.isna(target_name) or not target_name:
                continue

            # Compute multiple scores
            token_score = compute_token_overlap(coverage_name, str(target_name))
            contains_score = compute_contains_score(coverage_name, str(target_name))
            prefix_score = compute_prefix_score(coverage_name, str(target_name))

            # Overall score (weighted)
            overall_score = max(token_score, contains_score, prefix_score)

            # Boost if same insurer
            if row_ins_cd == ins_cd:
                overall_score *= 1.2

            if overall_score > 0.1:  # Minimum threshold
                candidates.append({
                    'cre_cvr_cd': code,
                    'coverage_name': str(target_name),
                    'similarity_score': round(overall_score, 3),
                    'match_type': name_type,
                    'insurer_match': row_ins_cd == ins_cd
                })

    # Sort by score descending
    candidates.sort(key=lambda x: (x['insurer_match'], x['similarity_score']), reverse=True)

    return candidates[:top_n]


# ============================================================================
# Auto-bucket assignment
# ============================================================================

def assign_bucket_and_priority(row: pd.Series, candidate_codes: List[Dict]) -> Tuple[str, str, List[str], str]:
    """
    Assign auto_bucket, priority, reasons, and candidate summary.

    Returns: (bucket, priority, reasons, candidate_summary)
    """
    coverage_name = row['coverage_name_normalized']
    reasons = []

    # Check LIKELY_INTENTIONAL first (highest confidence)
    is_intentional, intentional_reasons = is_likely_intentional(coverage_name)
    if is_intentional:
        reasons.extend(intentional_reasons)
        return 'LIKELY_INTENTIONAL', 'P0', reasons, ''

    # Check for NEW_CANONICAL indicators
    is_new, new_reasons = is_likely_new_canonical(coverage_name)

    # Check for ALIAS indicators
    has_alias, alias_reasons = has_alias_keywords(coverage_name)

    # Decision logic
    if candidate_codes:
        best_score = candidate_codes[0]['similarity_score']
        best_insurer_match = candidate_codes[0]['insurer_match']

        # Strong match → LIKELY_ALIAS
        if best_score >= 0.7 and best_insurer_match:
            reasons.extend(alias_reasons)
            reasons.append(f"STRONG_MATCH:score={best_score}")
            return 'LIKELY_ALIAS', 'P0', reasons, format_candidates(candidate_codes)

        # Medium match + alias keywords → LIKELY_ALIAS
        if best_score >= 0.5 and has_alias:
            reasons.extend(alias_reasons)
            reasons.append(f"MEDIUM_MATCH:score={best_score}")
            return 'LIKELY_ALIAS', 'P1', reasons, format_candidates(candidate_codes)

        # Low match + new treatment keywords → LIKELY_NEW_CANONICAL
        if best_score < 0.5 and is_new:
            reasons.extend(new_reasons)
            reasons.append(f"LOW_MATCH:score={best_score}")
            return 'LIKELY_NEW_CANONICAL', 'P1', reasons, format_candidates(candidate_codes)

        # Ambiguous
        reasons.extend(alias_reasons if has_alias else new_reasons)
        reasons.append(f"AMBIGUOUS:score={best_score}")
        return 'NEEDS_HUMAN', 'P2', reasons, format_candidates(candidate_codes)

    else:
        # No candidates found
        if is_new:
            reasons.extend(new_reasons)
            reasons.append("NO_CANDIDATES")
            return 'LIKELY_NEW_CANONICAL', 'P1', reasons, ''

        if has_alias:
            reasons.extend(alias_reasons)
            reasons.append("NO_CANDIDATES")
            return 'NEEDS_HUMAN', 'P2', reasons, ''

        # No candidates, no strong signals
        reasons.append("NO_CANDIDATES_NO_SIGNALS")
        return 'NEEDS_HUMAN', 'P2', reasons, ''


def format_candidates(candidates: List[Dict]) -> str:
    """Format candidate codes for CSV output"""
    if not candidates:
        return ''

    parts = []
    for c in candidates[:5]:  # Max 5
        parts.append(f"{c['cre_cvr_cd']}:{c['coverage_name']}:{c['similarity_score']}")

    return ' | '.join(parts)


# ============================================================================
# Main
# ============================================================================

def main():
    # Paths
    backlog_v1_path = Path('docs/audit/unanchored_backlog_v1.csv')
    excel_path = Path('data/sources/mapping/담보명mapping자료.xlsx')
    output_path = Path('docs/audit/unanchored_backlog_v2.csv')

    print("=" * 80)
    print("STEP NEXT-72: Auto-Triage Unanchored Backlog")
    print("=" * 80)

    # Load inputs
    print(f"\n[1/4] Loading backlog v1: {backlog_v1_path}")
    backlog_df = pd.read_csv(backlog_v1_path)
    print(f"  Total items: {len(backlog_df)}")

    print(f"\n[2/4] Loading Excel mapping: {excel_path}")
    excel_df = pd.read_excel(excel_path)
    print(f"  Total mapping rows: {len(excel_df)}")
    print(f"  Unique codes: {excel_df['cre_cvr_cd'].nunique()}")

    # Process each row
    print(f"\n[3/4] Processing each item...")
    results = []

    for idx, row in backlog_df.iterrows():
        coverage_name = row['coverage_name_normalized']
        insurer_key = row['insurer_key']

        # Find candidate codes
        candidates = find_candidate_codes(coverage_name, excel_df, insurer_key, top_n=5)

        # Assign bucket and priority
        bucket, priority, reasons, candidate_summary = assign_bucket_and_priority(row, candidates)

        # Build output row
        result = row.to_dict()
        result['auto_bucket'] = bucket
        result['auto_reason'] = ', '.join(reasons[:5])  # Limit reason length
        result['candidate_codes'] = candidate_summary
        result['priority'] = priority

        # Extract top candidate for convenience
        if candidates:
            result['top_candidate_code'] = candidates[0]['cre_cvr_cd']
            result['top_candidate_name'] = candidates[0]['coverage_name']
            result['top_candidate_score'] = candidates[0]['similarity_score']
        else:
            result['top_candidate_code'] = ''
            result['top_candidate_name'] = ''
            result['top_candidate_score'] = 0.0

        results.append(result)

        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(backlog_df)} items...")

    # Convert to DataFrame
    result_df = pd.DataFrame(results)

    # Sort by priority, then bucket
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
    result_df['priority_rank'] = result_df['priority'].map(priority_order)
    result_df = result_df.sort_values(['priority_rank', 'auto_bucket', 'insurer_key'])
    result_df = result_df.drop(columns=['priority_rank'])

    # Save
    print(f"\n[4/4] Saving v2: {output_path}")
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')

    # Statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\nBy bucket:")
    for bucket in ['LIKELY_INTENTIONAL', 'LIKELY_ALIAS', 'LIKELY_NEW_CANONICAL', 'NEEDS_HUMAN']:
        count = len(result_df[result_df['auto_bucket'] == bucket])
        pct = 100 * count / len(result_df) if len(result_df) > 0 else 0
        print(f"  {bucket:25s}: {count:3d} ({pct:5.1f}%)")

    print("\nBy priority:")
    for priority in ['P0', 'P1', 'P2']:
        count = len(result_df[result_df['priority'] == priority])
        pct = 100 * count / len(result_df) if len(result_df) > 0 else 0
        print(f"  {priority:5s}: {count:3d} ({pct:5.1f}%)")

    # Candidate coverage
    with_candidates = len(result_df[result_df['candidate_codes'] != ''])
    pct_with = 100 * with_candidates / len(result_df) if len(result_df) > 0 else 0
    print(f"\nItems with candidate codes: {with_candidates}/{len(result_df)} ({pct_with:.1f}%)")

    print(f"\n✅ Output written to: {output_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()
