#!/usr/bin/env python3
"""
STEP NEXT-18D: Coverage Candidate Filter (Pipeline Entry Point)
================================================================

Purpose:
    Filter out non-coverage text (condition sentences, explanations)
    from scope generation pipeline.

    This is the ROOT CAUSE FIX for UNCONFIRMED proliferation.

Rules (Hard Assertions):
    1. Coverage candidates MUST come from table rows (보장명/가입금액/보험료)
    2. Condition sentences (문장형) are NOT coverages
    3. ANY match with exclusion patterns → DROP

Exclusion Patterns (ANY match → DROP):
    - Sentences ending with: ~인 경우, ~시, ~때, ~한하여, ~다.
    - Condition patterns: ~으로 진단확정된 경우
    - Source: paragraph (not table)

Usage:
    python -m pipeline.step0_scope_filter.coverage_candidate_filter --insurer kb
"""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CoverageCandidate:
    """Coverage candidate from proposal"""
    text: str
    source_type: str  # table | paragraph
    page_num: int
    line_text: str


@dataclass
class FilterResult:
    """Filter decision"""
    candidate: CoverageCandidate
    is_valid: bool
    filter_reason: Optional[str] = None


# Exclusion patterns (ANY match → DROP)
EXCLUSION_PATTERNS = [
    # Condition sentences
    (r'(으로|로)\s*진단확정된\s*경우', 'CONDITION_SENTENCE'),
    (r'(인|한)\s*경우$', 'CONDITION_SENTENCE'),
    (r'시$', 'CONDITION_SENTENCE'),
    (r'때$', 'CONDITION_SENTENCE'),
    (r'한하여', 'CONDITION_SENTENCE'),

    # Sentence ending
    (r'다\.$', 'SENTENCE_ENDING'),
    (r'습니다\.$', 'SENTENCE_ENDING'),

    # Explanation phrases
    (r'보장개시일\s*이후', 'EXPLANATION_PHRASE'),
    (r'계약일로부터', 'EXPLANATION_PHRASE'),
    (r'피보험자', 'EXPLANATION_PHRASE'),

    # Non-coverage markers
    (r'납입면제대상', 'PREMIUM_WAIVER'),
    (r'대상보장', 'NON_COVERAGE'),
    (r'대상담보', 'NON_COVERAGE'),
]


def is_valid_coverage_candidate(candidate: CoverageCandidate) -> FilterResult:
    """
    Determine if candidate is a valid coverage.

    Hard Rules:
        1. Source must be 'table' (not paragraph)
        2. Must NOT match any exclusion pattern
        3. Must contain Korean characters
        4. Must be at least 2 characters

    Returns:
        FilterResult with is_valid flag and reason if filtered
    """
    text = candidate.text.strip()

    # Rule 1: Must have Korean characters
    if not re.search(r'[가-힣]', text):
        return FilterResult(candidate, False, 'NO_KOREAN')

    # Rule 2: Minimum length
    if len(text) < 2:
        return FilterResult(candidate, False, 'TOO_SHORT')

    # Rule 3: Source must be table (not paragraph)
    if candidate.source_type == 'paragraph':
        return FilterResult(candidate, False, 'PARAGRAPH_SOURCE')

    # Rule 4: Check exclusion patterns
    for pattern, reason in EXCLUSION_PATTERNS:
        if re.search(pattern, text):
            return FilterResult(candidate, False, reason)

    # Valid coverage candidate
    return FilterResult(candidate, True, None)


def extract_coverage_candidates_from_proposal(
    proposal_page_jsonl: Path
) -> List[CoverageCandidate]:
    """
    Extract coverage candidates from proposal PDF.

    Args:
        proposal_page_jsonl: Proposal page.jsonl file

    Returns:
        List of CoverageCandidate objects
    """
    candidates = []

    if not proposal_page_jsonl.exists():
        return candidates

    with open(proposal_page_jsonl, 'r', encoding='utf-8') as f:
        for line_idx, line in enumerate(f):
            if not line.strip():
                continue

            try:
                page_data = json.loads(line)
                page_num = page_data.get('page', line_idx + 1)
                text = page_data.get('text', '')

                # Filter for table-like pages (has keywords: 담보, 가입금액, 보험료)
                table_keywords = ['담보', '보장', '가입금액', '보험가입금액', '보험료']
                is_table_page = any(kw in text for kw in table_keywords)

                if not is_table_page:
                    continue

                # Parse lines
                lines = text.split('\n')
                for line_text in lines:
                    line_text = line_text.strip()

                    # Skip empty, short, or header lines
                    if len(line_text) < 2:
                        continue
                    if any(hdr in line_text for hdr in ['담보가입현황', '가입금액', '보험료', '납입기간', '피보험자']):
                        continue

                    # Heuristic: If line has Korean + numbers/amounts, it's likely a table row
                    has_korean = bool(re.search(r'[가-힣]', line_text))
                    has_amount = bool(re.search(r'\d{1,3}(?:,\d{3})*\s*만?원|\d+[천백십]만?원', line_text))

                    if has_korean:
                        # Determine source type based on structure
                        # Table rows typically have: name + amount + number patterns
                        # Paragraphs are longer with sentence endings
                        source_type = 'table' if has_amount else 'paragraph'

                        candidates.append(CoverageCandidate(
                            text=line_text,
                            source_type=source_type,
                            page_num=page_num,
                            line_text=line_text
                        ))

            except json.JSONDecodeError:
                continue

    return candidates


def filter_coverage_candidates(
    candidates: List[CoverageCandidate]
) -> Tuple[List[CoverageCandidate], List[FilterResult]]:
    """
    Filter coverage candidates.

    Returns:
        (valid_candidates, filtered_out_results)
    """
    valid = []
    filtered_out = []

    for candidate in candidates:
        result = is_valid_coverage_candidate(candidate)

        if result.is_valid:
            valid.append(candidate)
        else:
            filtered_out.append(result)

    return valid, filtered_out


def extract_coverage_name_from_candidate(candidate_text: str) -> str:
    """
    Extract clean coverage name from candidate text.

    Remove amounts, numbers, dates, etc. to get just the coverage name.

    Args:
        candidate_text: Raw candidate text

    Returns:
        Clean coverage name
    """
    # Remove amounts
    text = re.sub(r'\d{1,3}(?:,\d{3})*\s*만?원', '', candidate_text)
    text = re.sub(r'\d+[천백십]만?원', '', text)

    # Remove pure numbers
    text = re.sub(r'\d+', '', text)

    # Remove special chars (but keep parentheses for coverage name parts)
    text = re.sub(r'[/\|]', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def generate_scope_csv(
    insurer: str,
    valid_candidates: List[CoverageCandidate],
    output_csv: Path
):
    """
    Generate scope.csv from valid candidates.

    Args:
        insurer: Insurer name
        valid_candidates: Filtered valid coverage candidates
        output_csv: Output scope.csv path
    """
    rows = []

    # Deduplicate by coverage name
    seen_names = set()

    for candidate in valid_candidates:
        coverage_name = extract_coverage_name_from_candidate(candidate.text)

        # Skip duplicates
        if coverage_name in seen_names:
            continue

        seen_names.add(coverage_name)

        rows.append({
            'coverage_name_raw': coverage_name,
            'insurer': insurer,
            'source_page': candidate.page_num
        })

    # Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['coverage_name_raw', 'insurer', 'source_page'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated scope.csv: {len(rows)} coverages")


def save_filtered_out_report(
    filtered_out: List[FilterResult],
    output_jsonl: Path
):
    """
    Save filtered-out candidates for audit.

    Args:
        filtered_out: List of filtered out results
        output_jsonl: Output JSONL path
    """
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for result in filtered_out:
            entry = {
                'text': result.candidate.text,
                'source_type': result.candidate.source_type,
                'page': result.candidate.page_num,
                'filter_reason': result.filter_reason
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"Filtered out: {len(filtered_out)} candidates")


def main():
    parser = argparse.ArgumentParser(description='Filter coverage candidates from proposal')
    parser.add_argument('--insurer', type=str, required=True, help='Insurer name')
    args = parser.parse_args()

    insurer = args.insurer
    project_root = Path(__file__).resolve().parents[2]

    print(f"[Step0 Coverage Candidate Filter]")
    print(f"Insurer: {insurer}\n")

    # Paths
    proposal_dir = project_root / 'data' / 'evidence_text' / insurer / '가입설계서'
    output_scope_csv = project_root / 'data' / 'scope' / f'{insurer}_scope.csv'
    output_filtered_jsonl = project_root / 'data' / 'scope' / f'{insurer}_filtered_out.jsonl'

    # Step 1: Extract candidates
    print("[1/4] Extracting coverage candidates from proposal...")
    proposal_files = list(proposal_dir.glob('*.page.jsonl')) if proposal_dir.exists() else []

    if not proposal_files:
        print(f"[ERROR] No proposal files found")
        return

    all_candidates = []
    for pfile in proposal_files:
        candidates = extract_coverage_candidates_from_proposal(pfile)
        all_candidates.extend(candidates)

    print(f"  Extracted: {len(all_candidates)} candidates")

    # Step 2: Filter candidates
    print("\n[2/4] Filtering out non-coverage candidates...")
    valid, filtered_out = filter_coverage_candidates(all_candidates)
    print(f"  Valid: {len(valid)}")
    print(f"  Filtered out: {len(filtered_out)}")

    # Step 3: Generate scope.csv
    print("\n[3/4] Generating scope.csv...")
    generate_scope_csv(insurer, valid, output_scope_csv)
    print(f"  Output: {output_scope_csv}")

    # Step 4: Save filtered-out report
    print("\n[4/4] Saving filtered-out report...")
    save_filtered_out_report(filtered_out, output_filtered_jsonl)
    print(f"  Output: {output_filtered_jsonl}")

    print(f"\n✓ Step0 complete for {insurer}")


if __name__ == '__main__':
    main()
